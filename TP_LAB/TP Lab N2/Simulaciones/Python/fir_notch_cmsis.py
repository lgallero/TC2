#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diseño configurable de un FIR notch y exportación para arm_fir_f32.

La plantilla B del TP es, por defecto, un notch en 50 Hz con ancho de banda
de 1 Hz medido a -3 dB. Se comparan varias ventanas como en el ejemplo de la
cátedra y se exporta solamente el diseño elegido en ``VENTANA_A_EXPORTAR``.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy import optimize
from scipy import signal as sig

from filtros_cmsis_utils import (
    exportar_fir_cmsis,
    graficar_polos_ceros_fir,
    graficar_respuestas,
    imprimir_coeficientes_fir,
    imprimir_configuracion_stm32,
    imprimir_rutas,
    medir_notch,
    respuesta_ba,
)


#%% ===========================================================================
# CONFIGURACIÓN: editar solamente esta sección para cambiar el diseño
# =============================================================================

FS_HZ = 1000.0
F_NOTCH_HZ = 50.0
BW_3DB_HZ = 1.0

# Un notch de 1 Hz a fs=1 kHz exige un FIR largo. Debe ser IMPAR porque la
# banda de paso llega hasta Nyquist; un FIR simétrico de longitud par (tipo II)
# está obligado a tener un cero en Nyquist.
CANT_COEF = 4001

# firwin define sus cortes a -6 dB. Si esta opción está activa, el programa
# corrige automáticamente el ancho interno hasta obtener el BW solicitado a
# -3 dB. Después impone matemáticamente un cero exacto en F_NOTCH_HZ.
AJUSTAR_BW_AUTOMATICAMENTE = True
BW_INTERNO_HZ = BW_3DB_HZ
PUNTOS_AJUSTE_BW = 20001
RANGO_BW_INTERNO = (0.01 * BW_3DB_HZ, 2.5 * BW_3DB_HZ)

# Se pueden agregar o quitar ventanas. El valor es exactamente el argumento
# ``window`` aceptado por scipy.signal.firwin.
VENTANAS = {
    "blackmanharris": "blackmanharris",
    "hamming": "hamming",
    "kaiser_beta_14": ("kaiser", 14.0),
}
VENTANA_A_EXPORTAR = "kaiser_beta_14"

# Cantidad de puntos del análisis/gráfico. Para un notch angosto conviene usar
# una grilla grande; este número no modifica el filtro, sólo su evaluación.
PUNTOS_GRAFICO = 131072
LIMITE_X_HZ = (0.0, 100.0)
ZOOM_X_HZ = (45.0, 55.0)
PISO_GRAFICO_DB = -160.0
MOSTRAR_GRAFICOS = True
GUARDAR_GRAFICOS = True
MOSTRAR_COEFICIENTES_TERMINAL = True

# arm_fir_f32 usa float32. Nueve cifras significativas ya garantizan el
# round-trip exacto; se muestran 17 para conservar todos los decimales visibles.
DIGITOS_SIGNIFICATIVOS_C = 17
CARPETA_SALIDA = Path(__file__).resolve().parent / "resultados" / "fir_notch"


#%% ===========================================================================
# FUNCIONES DE DISEÑO Y PLANTILLA
# =============================================================================

def validar_configuracion() -> None:
    nyquist = FS_HZ / 2.0
    if FS_HZ <= 0.0:
        raise ValueError("FS_HZ debe ser positiva.")
    if not 0.0 < F_NOTCH_HZ < nyquist:
        raise ValueError("F_NOTCH_HZ debe estar entre 0 y Nyquist.")
    if not 0.0 < BW_3DB_HZ < 2.0 * min(F_NOTCH_HZ, nyquist - F_NOTCH_HZ):
        raise ValueError("BW_3DB_HZ no cabe alrededor de la frecuencia del notch.")
    if CANT_COEF < 3 or CANT_COEF % 2 == 0:
        raise ValueError(
            "CANT_COEF debe ser impar. Un FIR tipo II tiene un cero forzado en Nyquist."
        )
    if PUNTOS_GRAFICO < 32:
        raise ValueError("PUNTOS_GRAFICO debe ser al menos 32.")
    if VENTANA_A_EXPORTAR not in VENTANAS:
        raise ValueError("VENTANA_A_EXPORTAR no aparece en el diccionario VENTANAS.")
    if PUNTOS_AJUSTE_BW < 1001:
        raise ValueError("PUNTOS_AJUSTE_BW debe ser al menos 1001.")
    if not 0.0 < RANGO_BW_INTERNO[0] < RANGO_BW_INTERNO[1]:
        raise ValueError("RANGO_BW_INTERNO debe contener dos anchos positivos crecientes.")


def forzar_cero_en_f0(bb: np.ndarray) -> np.ndarray:
    """Proyecta un FIR simétrico para imponer H(exp(j*w0))=0 exactamente."""
    bb = np.asarray(bb, dtype=np.float64)
    centro = (bb.size - 1) / 2.0
    nn = np.arange(bb.size, dtype=np.float64)
    base_coseno = np.cos(2.0 * np.pi * F_NOTCH_HZ / FS_HZ * (nn - centro))
    correccion = np.dot(bb, base_coseno) / np.dot(base_coseno, base_coseno)
    bb = bb - correccion * base_coseno
    return bb / np.sum(bb)


def disenar_fir_notch(ventana: object, bw_interno_hz: float) -> np.ndarray:
    """Diseña por ventana un bandstop y fuerza el cero en la frecuencia central."""
    f_izq = F_NOTCH_HZ - bw_interno_hz / 2.0
    f_der = F_NOTCH_HZ + bw_interno_hz / 2.0
    bb = sig.firwin(
        numtaps=CANT_COEF,
        cutoff=[f_izq, f_der],
        pass_zero="bandstop",
        window=ventana,
        fs=FS_HZ,
        scale=True,
    )
    return forzar_cero_en_f0(bb)


def medir_bw_rapido(bb: np.ndarray) -> float:
    margen = max(5.0 * BW_3DB_HZ, 5.0)
    ff = np.linspace(
        max(0.0, F_NOTCH_HZ - margen),
        min(FS_HZ / 2.0, F_NOTCH_HZ + margen),
        PUNTOS_AJUSTE_BW,
    )
    _, hh = sig.freqz(bb, 1.0, worN=ff, fs=FS_HZ)
    return float(medir_notch(ff, hh, F_NOTCH_HZ)["bw_3db_hz"])


def calcular_bw_interno(ventana: object) -> float:
    if not AJUSTAR_BW_AUTOMATICAMENTE:
        return BW_INTERNO_HZ

    def error_bw(bw_interno: float) -> float:
        bb = disenar_fir_notch(ventana, bw_interno)
        return medir_bw_rapido(bb) - BW_3DB_HZ

    bw_min, bw_max = RANGO_BW_INTERNO
    error_min = error_bw(bw_min)
    error_max = error_bw(bw_max)
    if not error_min < 0.0 < error_max:
        raise RuntimeError(
            "No se pudo ajustar el BW. Aumente CANT_COEF o amplíe RANGO_BW_INTERNO."
        )
    return float(optimize.brentq(error_bw, bw_min, bw_max, xtol=1.0e-9, rtol=1.0e-9))


def dibujar_plantilla_notch(ax: plt.Axes) -> None:
    f_izq = F_NOTCH_HZ - BW_3DB_HZ / 2.0
    f_der = F_NOTCH_HZ + BW_3DB_HZ / 2.0
    xx = [0.0, f_izq, F_NOTCH_HZ, f_der, FS_HZ / 2.0]
    yy = [0.0, -3.0, PISO_GRAFICO_DB, -3.0, 0.0]
    ax.plot(xx, yy, "k--", lw=1.3, label="plantilla solicitada")
    ax.axvline(F_NOTCH_HZ, color="tab:red", ls=":", lw=1.0)
    ax.axhline(-3.0, color="0.35", ls=":", lw=1.0, label="nivel -3 dB")


#%% ===========================================================================
# PROGRAMA PRINCIPAL
# =============================================================================

def main() -> None:
    validar_configuracion()
    CARPETA_SALIDA.mkdir(parents=True, exist_ok=True)

    filtros: dict[str, np.ndarray] = {}
    respuestas: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    anchos_internos: dict[str, float] = {}

    for nombre, ventana in VENTANAS.items():
        bw_interno = calcular_bw_interno(ventana)
        bb = disenar_fir_notch(ventana, bw_interno)
        # Se grafica lo que realmente procesará ARM después de cuantizar a f32.
        bb_arm = bb.astype(np.float32).astype(np.float64)
        ff, hh = respuesta_ba(bb_arm, 1.0, FS_HZ, PUNTOS_GRAFICO)
        filtros[nombre] = bb
        respuestas[nombre] = (ff, hh)
        anchos_internos[nombre] = bw_interno

    descripcion = (
        f"FIR notch: f0={F_NOTCH_HZ:g} Hz, BW@-3dB={BW_3DB_HZ:g} Hz, "
        f"taps={CANT_COEF}, ventana={VENTANA_A_EXPORTAR}"
    )
    rutas = exportar_fir_cmsis(
        CARPETA_SALIDA,
        "fir_notch",
        filtros[VENTANA_A_EXPORTAR],
        FS_HZ,
        descripcion,
        DIGITOS_SIGNIFICATIVOS_C,
    )

    ruta_general = CARPETA_SALIDA / "fir_notch_respuesta.png" if GUARDAR_GRAFICOS else None
    ruta_zoom = CARPETA_SALIDA / "fir_notch_zoom.png" if GUARDAR_GRAFICOS else None
    ruta_pz = CARPETA_SALIDA / "fir_notch_polos_ceros.png" if GUARDAR_GRAFICOS else None
    titulo = (
        f"FIR notch por métodos directos — f0={F_NOTCH_HZ:g} Hz — "
        f"BW@-3dB={BW_3DB_HZ:g} Hz — taps={CANT_COEF}"
    )
    graficar_respuestas(
        respuestas,
        FS_HZ,
        titulo,
        dibujar_plantilla_notch,
        puntos_xlim=LIMITE_X_HZ,
        modulo_ylim=(PISO_GRAFICO_DB, 5.0),
        ruta_png=ruta_general,
        mostrar=False,
    )
    angulo_notch = 2.0 * np.pi * F_NOTCH_HZ / FS_HZ
    ceros_notch = [np.exp(1j * angulo_notch), np.exp(-1j * angulo_notch)]
    graficar_polos_ceros_fir(
        filtros[VENTANA_A_EXPORTAR].astype(np.float32),
        titulo=(
            f"FIR notch — polos y ceros relevantes — "
            f"f0={F_NOTCH_HZ:g} Hz — taps={CANT_COEF}"
        ),
        ruta_png=ruta_pz,
        mostrar=False,
        ceros_relevantes=ceros_notch,
    )
    graficar_respuestas(
        respuestas,
        FS_HZ,
        titulo + " — detalle",
        dibujar_plantilla_notch,
        puntos_xlim=ZOOM_X_HZ,
        modulo_ylim=(PISO_GRAFICO_DB, 5.0),
        ruta_png=ruta_zoom,
        mostrar=False,
    )

    print("\nMÉTRICAS OBTENIDAS")
    for nombre, (ff, hh) in respuestas.items():
        metricas = medir_notch(ff, hh, F_NOTCH_HZ)
        _, h0 = sig.freqz(
            filtros[nombre].astype(np.float32),
            1.0,
            worN=np.asarray([F_NOTCH_HZ]),
            fs=FS_HZ,
        )
        print(f"\n{nombre}:")
        print(f"  bw_interno_firwin_hz: {anchos_internos[nombre]:.12g}")
        for clave, valor in metricas.items():
            print(f"  {clave}: {valor:.12g}")
        profundidad_exacta = 20.0 * np.log10(max(abs(h0[0]), np.finfo(float).tiny))
        print(f"  profundidad_exacta_en_f0_db: {profundidad_exacta:.12g}")

    if MOSTRAR_COEFICIENTES_TERMINAL:
        imprimir_coeficientes_fir(
            filtros[VENTANA_A_EXPORTAR],
            DIGITOS_SIGNIFICATIVOS_C,
        )

    print("\nEXCEL CONSOLIDADO Y GRÁFICOS")
    imprimir_rutas(rutas)
    if ruta_general is not None:
        print(f"gráfico: {ruta_general.resolve()}")
        print(f"zoom: {ruta_zoom.resolve()}")
        print(f"polos y ceros: {ruta_pz.resolve()}")

    imprimir_configuracion_stm32(
        "FIR",
        FS_HZ,
        cantidad_coeficientes=filtros[VENTANA_A_EXPORTAR].size,
    )

    if MOSTRAR_GRAFICOS:
        plt.show()


if __name__ == "__main__":
    main()
