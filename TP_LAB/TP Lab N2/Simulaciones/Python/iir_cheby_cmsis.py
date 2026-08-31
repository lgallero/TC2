#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diseño configurable de un IIR Chebyshev y exportación CMSIS-DSP DF1.

La configuración inicial reproduce la plantilla A del TP: pasabajos,
fp=100 Hz, fstop=300 Hz, pérdida máxima=1 dB y atenuación mínima=60 dB.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy import signal as sig

from filtros_cmsis_utils import (
    exportar_sos_cmsis,
    graficar_polos_ceros_sos,
    graficar_respuestas,
    imprimir_coeficientes_iir,
    imprimir_configuracion_stm32,
    imprimir_rutas,
    magnitud_db,
    respuesta_sos,
    verificar_conversion_cmsis,
    verificar_estabilidad_sos,
)


#%% ===========================================================================
# CONFIGURACIÓN: editar solamente esta sección para cambiar el diseño
# =============================================================================

FS_HZ = 1000.0
F_PASS_HZ = 100.0
F_STOP_HZ = 300.0
PERDIDA_MAX_DB = 1.0
ATENUACION_MIN_DB = 60.0

# 1: ripple en banda de paso; 2: ripple en banda de rechazo.
TIPO_CHEBYSHEV = 1

PUNTOS_GRAFICO = 32768
LIMITE_X_HZ = (0.0, FS_HZ / 2.0)
PISO_GRAFICO_DB = -(ATENUACION_MIN_DB + 30.0)
MOSTRAR_GRAFICOS = True
GUARDAR_GRAFICOS = True
MOSTRAR_COEFICIENTES_TERMINAL = True

# El cálculo se realiza en float64 y el header contiene los números float32 que
# procesará arm_biquad_cascade_df1_f32. Nueve cifras ya bastan para conservar
# exactamente un float32; se muestran 17 para conservar todos los decimales.
DIGITOS_SIGNIFICATIVOS_C = 17
CARPETA_SALIDA = Path(__file__).resolve().parent / "resultados" / "iir_cheby"


#%% ===========================================================================
# FUNCIONES DE DISEÑO Y PLANTILLA
# =============================================================================

def validar_configuracion() -> None:
    if FS_HZ <= 0.0:
        raise ValueError("FS_HZ debe ser positiva.")
    if not 0.0 < F_PASS_HZ < F_STOP_HZ < FS_HZ / 2.0:
        raise ValueError("Se requiere 0 < F_PASS_HZ < F_STOP_HZ < FS_HZ/2.")
    if PERDIDA_MAX_DB <= 0.0 or ATENUACION_MIN_DB <= 0.0:
        raise ValueError("Las atenuaciones de la plantilla deben ser positivas.")
    if TIPO_CHEBYSHEV not in (1, 2):
        raise ValueError("TIPO_CHEBYSHEV debe valer 1 o 2.")
    if PUNTOS_GRAFICO < 32:
        raise ValueError("PUNTOS_GRAFICO debe ser al menos 32.")


def disenar_iir_cheby() -> np.ndarray:
    return sig.iirdesign(
        wp=F_PASS_HZ,
        ws=F_STOP_HZ,
        gpass=PERDIDA_MAX_DB,
        gstop=ATENUACION_MIN_DB,
        analog=False,
        ftype=f"cheby{TIPO_CHEBYSHEV}",
        output="sos",
        fs=FS_HZ,
    )


def dibujar_plantilla_cheby(ax: plt.Axes) -> None:
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

    # Regiones prohibidas de la plantilla.
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
    perdida = float(-np.min(mag[ff <= F_PASS_HZ]))
    atenuacion = float(-np.max(mag[ff >= F_STOP_HZ]))
    return {
        "perdida_max_banda_paso_db": perdida,
        "atenuacion_min_banda_stop_db": atenuacion,
    }


#%% ===========================================================================
# PROGRAMA PRINCIPAL
# =============================================================================

def main() -> None:
    validar_configuracion()
    CARPETA_SALIDA.mkdir(parents=True, exist_ok=True)

    sos_diseno = disenar_iir_cheby()
    descripcion = (
        f"Chebyshev {TIPO_CHEBYSHEV} pasabajos: fp={F_PASS_HZ:g} Hz, "
        f"fstop={F_STOP_HZ:g} Hz, Amax={PERDIDA_MAX_DB:g} dB, "
        f"Amin={ATENUACION_MIN_DB:g} dB"
    )
    rutas, cmsis, sos_arm = exportar_sos_cmsis(
        CARPETA_SALIDA,
        "iir_cheby",
        sos_diseno,
        FS_HZ,
        descripcion,
        DIGITOS_SIGNIFICATIVOS_C,
    )

    error_conversion = verificar_conversion_cmsis(sos_arm, cmsis)
    radio_max = verificar_estabilidad_sos(sos_arm)
    ff, hh = respuesta_sos(sos_arm, FS_HZ, PUNTOS_GRAFICO)
    metricas = medir_plantilla(ff, hh)

    tolerancia_db = 0.03
    if metricas["perdida_max_banda_paso_db"] > PERDIDA_MAX_DB + tolerancia_db:
        raise RuntimeError("El filtro float32 no cumple la pérdida de banda de paso.")
    if metricas["atenuacion_min_banda_stop_db"] < ATENUACION_MIN_DB - tolerancia_db:
        raise RuntimeError("El filtro float32 no cumple la atenuación de banda de rechazo.")

    respuestas = {f"Chebyshev {TIPO_CHEBYSHEV} — ARM float32": (ff, hh)}
    ruta_png = CARPETA_SALIDA / "iir_cheby_respuesta.png" if GUARDAR_GRAFICOS else None
    ruta_pz = CARPETA_SALIDA / "iir_cheby_polos_ceros.png" if GUARDAR_GRAFICOS else None
    titulo = f"{descripcion} — fs={FS_HZ:g} Hz"
    graficar_respuestas(
        respuestas,
        FS_HZ,
        titulo,
        dibujar_plantilla_cheby,
        puntos_xlim=LIMITE_X_HZ,
        modulo_ylim=(PISO_GRAFICO_DB, 5.0),
        ruta_png=ruta_png,
        mostrar=False,
    )
    graficar_polos_ceros_sos(
        sos_arm,
        titulo=f"IIR Chebyshev {TIPO_CHEBYSHEV} — polos y ceros",
        ruta_png=ruta_pz,
        mostrar=False,
    )

    _, polos, _ = sig.sos2zpk(sos_arm)
    print("\nDISEÑO IIR CHEBYSHEV")
    print(descripcion)
    print(f"Orden del filtro: {len(polos)}")
    print(f"Cantidad de etapas biquad: {cmsis.shape[0]}")
    print(f"Radio máximo de polos después de float32: {radio_max:.12g}")
    print(f"Error SciPy/CMSIS DF1 simulado: {error_conversion:.3e}")
    for clave, valor in metricas.items():
        print(f"{clave}: {valor:.12g}")

    if MOSTRAR_COEFICIENTES_TERMINAL:
        imprimir_coeficientes_iir(
            sos_diseno,
            cmsis,
            DIGITOS_SIGNIFICATIVOS_C,
        )

    print("\nEXCEL CONSOLIDADO Y GRÁFICOS")
    imprimir_rutas(rutas)
    if ruta_png is not None:
        print(f"gráfico: {ruta_png.resolve()}")
        print(f"polos y ceros: {ruta_pz.resolve()}")

    imprimir_configuracion_stm32(
        "IIR",
        FS_HZ,
        cantidad_coeficientes=cmsis.size,
        cantidad_sos=cmsis.shape[0],
    )

    if MOSTRAR_GRAFICOS:
        plt.show()


if __name__ == "__main__":
    main()
