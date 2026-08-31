#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FIR pasabajos configurable con la misma plantilla del IIR Chebyshev.

Compara ventanas por método directo, grafica módulo/fase/retardo y polos/ceros,
y agrega al Excel consolidado el diseño elegido para ``arm_fir_f32``.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy import signal as sig

from filtros_cmsis_utils import (
    exportar_fir_cmsis,
    graficar_polos_ceros_fir,
    graficar_respuestas,
    imprimir_coeficientes_fir,
    imprimir_rutas,
    magnitud_db,
    respuesta_ba,
)


#%% ===========================================================================
# CONFIGURACIÓN: editar solamente esta sección para cambiar el diseño
# =============================================================================

FS_HZ = 1000.0
F_PASS_HZ = 100.0
F_STOP_HZ = 300.0
PERDIDA_MAX_DB = 1.0
ATENUACION_MIN_DB = 60.0

# El corte se ubica en el centro de la transición si se deja en None.
F_CORTE_HZ = None
CANT_COEF = 81

VENTANAS = {
    "blackmanharris": "blackmanharris",
    "hamming": "hamming",
    "kaiser_beta_14": ("kaiser", 14.0),
}
VENTANA_A_EXPORTAR = "kaiser_beta_14"

PUNTOS_GRAFICO = 32768
LIMITE_X_HZ = (0.0, FS_HZ / 2.0)
PISO_GRAFICO_DB = -(ATENUACION_MIN_DB + 30.0)
MOSTRAR_GRAFICOS = True
GUARDAR_GRAFICOS = True
MOSTRAR_COEFICIENTES_TERMINAL = True
# Se imprimen varios taps por renglón para no saturar la terminal.
COEFICIENTES_POR_LINEA_TERMINAL = 8

DIGITOS_SIGNIFICATIVOS_C = 17
CARPETA_SALIDA = Path(__file__).resolve().parent / "resultados" / "fir_pasabajos"


#%% ===========================================================================
# FUNCIONES DE DISEÑO Y PLANTILLA
# =============================================================================

def obtener_f_corte() -> float:
    if F_CORTE_HZ is None:
        return 0.5 * (F_PASS_HZ + F_STOP_HZ)
    return float(F_CORTE_HZ)


def validar_configuracion() -> None:
    if FS_HZ <= 0.0:
        raise ValueError("FS_HZ debe ser positiva.")
    if not 0.0 < F_PASS_HZ < F_STOP_HZ < FS_HZ / 2.0:
        raise ValueError("Se requiere 0 < F_PASS_HZ < F_STOP_HZ < FS_HZ/2.")
    if not F_PASS_HZ < obtener_f_corte() < F_STOP_HZ:
        raise ValueError("F_CORTE_HZ debe quedar dentro de la banda de transición.")
    if CANT_COEF < 3:
        raise ValueError("CANT_COEF debe ser al menos 3.")
    if PERDIDA_MAX_DB <= 0.0 or ATENUACION_MIN_DB <= 0.0:
        raise ValueError("Las atenuaciones de plantilla deben ser positivas.")
    if VENTANA_A_EXPORTAR not in VENTANAS:
        raise ValueError("VENTANA_A_EXPORTAR no aparece en VENTANAS.")
    if PUNTOS_GRAFICO < 32:
        raise ValueError("PUNTOS_GRAFICO debe ser al menos 32.")


def disenar_fir_pasabajos(ventana: object) -> np.ndarray:
    return sig.firwin(
        numtaps=CANT_COEF,
        cutoff=obtener_f_corte(),
        window=ventana,
        pass_zero="lowpass",
        scale=True,
        fs=FS_HZ,
    )


def dibujar_plantilla_pasabajos(ax: plt.Axes) -> None:
    nyquist = FS_HZ / 2.0
    ax.hlines(
        -PERDIDA_MAX_DB,
        0.0,
        F_PASS_HZ,
        colors="tab:green",
        linestyles="--",
        label=f"pérdida máxima: {PERDIDA_MAX_DB:g} dB",
    )
    ax.hlines(
        -ATENUACION_MIN_DB,
        F_STOP_HZ,
        nyquist,
        colors="tab:red",
        linestyles="--",
        label=f"atenuación mínima: {ATENUACION_MIN_DB:g} dB",
    )
    ax.axvline(F_PASS_HZ, color="tab:green", ls=":", lw=1.0)
    ax.axvline(F_STOP_HZ, color="tab:red", ls=":", lw=1.0)
    ax.axvspan(F_PASS_HZ, F_STOP_HZ, color="0.5", alpha=0.08, label="transición")
    ax.fill_between(
        [0.0, F_PASS_HZ],
        [PISO_GRAFICO_DB, PISO_GRAFICO_DB],
        [-PERDIDA_MAX_DB, -PERDIDA_MAX_DB],
        color="tab:red",
        alpha=0.06,
    )
    ax.fill_between(
        [F_STOP_HZ, nyquist],
        [-ATENUACION_MIN_DB, -ATENUACION_MIN_DB],
        [5.0, 5.0],
        color="tab:red",
        alpha=0.06,
    )


def medir_plantilla(ff: np.ndarray, hh: np.ndarray) -> dict[str, float]:
    mag = magnitud_db(hh)
    return {
        "perdida_max_banda_paso_db": float(-np.min(mag[ff <= F_PASS_HZ])),
        "atenuacion_min_banda_stop_db": float(-np.max(mag[ff >= F_STOP_HZ])),
    }


#%% ===========================================================================
# PROGRAMA PRINCIPAL
# =============================================================================

def main() -> None:
    validar_configuracion()
    CARPETA_SALIDA.mkdir(parents=True, exist_ok=True)

    filtros: dict[str, np.ndarray] = {}
    respuestas: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    metricas: dict[str, dict[str, float]] = {}
    for nombre, ventana in VENTANAS.items():
        bb = disenar_fir_pasabajos(ventana)
        bb_arm = bb.astype(np.float32).astype(np.float64)
        ff, hh = respuesta_ba(bb_arm, 1.0, FS_HZ, PUNTOS_GRAFICO)
        filtros[nombre] = bb
        respuestas[nombre] = (ff, hh)
        metricas[nombre] = medir_plantilla(ff, hh)

    seleccion = filtros[VENTANA_A_EXPORTAR]
    descripcion = (
        f"FIR pasabajos: fp={F_PASS_HZ:g} Hz, fstop={F_STOP_HZ:g} Hz, "
        f"Amax={PERDIDA_MAX_DB:g} dB, Amin={ATENUACION_MIN_DB:g} dB, "
        f"taps={CANT_COEF}, ventana={VENTANA_A_EXPORTAR}"
    )
    rutas = exportar_fir_cmsis(
        CARPETA_SALIDA,
        "fir_pasabajos",
        seleccion,
        FS_HZ,
        descripcion,
        DIGITOS_SIGNIFICATIVOS_C,
    )

    tolerancia_db = 0.03
    seleccion_metricas = metricas[VENTANA_A_EXPORTAR]
    if seleccion_metricas["perdida_max_banda_paso_db"] > PERDIDA_MAX_DB + tolerancia_db:
        raise RuntimeError("El FIR float32 no cumple la pérdida de banda de paso.")
    if seleccion_metricas["atenuacion_min_banda_stop_db"] < ATENUACION_MIN_DB - tolerancia_db:
        raise RuntimeError("El FIR float32 no cumple la atenuación de rechazo.")

    ruta_respuesta = (
        CARPETA_SALIDA / "fir_pasabajos_respuesta.png" if GUARDAR_GRAFICOS else None
    )
    ruta_pz = (
        CARPETA_SALIDA / "fir_pasabajos_polos_ceros.png" if GUARDAR_GRAFICOS else None
    )
    graficar_respuestas(
        respuestas,
        FS_HZ,
        titulo=descripcion,
        dibujar_plantilla=dibujar_plantilla_pasabajos,
        puntos_xlim=LIMITE_X_HZ,
        modulo_ylim=(PISO_GRAFICO_DB, 5.0),
        ruta_png=ruta_respuesta,
        mostrar=False,
    )
    graficar_polos_ceros_fir(
        seleccion.astype(np.float32),
        titulo=(
            f"FIR pasabajos — polos y ceros — taps={CANT_COEF} — "
            f"ventana={VENTANA_A_EXPORTAR}"
        ),
        ruta_png=ruta_pz,
        mostrar=False,
    )

    print("\nDISEÑO FIR PASABAJOS CON PLANTILLA CHEBYSHEV")
    print(descripcion)
    for nombre, valores in metricas.items():
        print(f"\n{nombre}:")
        for clave, valor in valores.items():
            print(f"  {clave}: {valor:.12g}")

    if MOSTRAR_COEFICIENTES_TERMINAL:
        imprimir_coeficientes_fir(
            seleccion,
            DIGITOS_SIGNIFICATIVOS_C,
            COEFICIENTES_POR_LINEA_TERMINAL,
        )

    print("\nEXCEL CONSOLIDADO Y GRÁFICOS")
    imprimir_rutas(rutas)
    if ruta_respuesta is not None:
        print(f"gráfico: {ruta_respuesta.resolve()}")
        print(f"polos y ceros: {ruta_pz.resolve()}")

    if MOSTRAR_GRAFICOS:
        plt.show()


if __name__ == "__main__":
    main()
