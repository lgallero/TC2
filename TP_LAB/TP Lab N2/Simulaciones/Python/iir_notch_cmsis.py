#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diseño configurable de un IIR notch y exportación CMSIS-DSP DF1.

La plantilla B se especifica mediante frecuencia central y ancho de banda a
-3 dB. SciPy usa ``Q=f0/BW`` y genera un único biquad de segundo orden.
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
    imprimir_rutas,
    medir_notch,
    respuesta_sos,
    verificar_conversion_cmsis,
    verificar_estabilidad_sos,
)


#%% ===========================================================================
# CONFIGURACIÓN: editar solamente esta sección para cambiar el diseño
# =============================================================================

FS_HZ = 1000.0
F_NOTCH_HZ = 50.0
BW_3DB_HZ = 1.0

# Si Q_MANUAL vale None se calcula Q=F_NOTCH_HZ/BW_3DB_HZ. Si se escribe un
# número, ese Q tiene prioridad y el ancho real pasa a ser F_NOTCH_HZ/Q_MANUAL.
Q_MANUAL = None

PUNTOS_GRAFICO = 131072
LIMITE_X_HZ = (0.0, 100.0)
ZOOM_X_HZ = (45.0, 55.0)
PISO_GRAFICO_DB = -160.0
MOSTRAR_GRAFICOS = True
GUARDAR_GRAFICOS = True
MOSTRAR_COEFICIENTES_TERMINAL = True

# Nueve cifras significativas ya garantizan el round-trip exacto de float32;
# se muestran 17 para conservar todos los decimales visibles en Excel y C.
DIGITOS_SIGNIFICATIVOS_C = 17
CARPETA_SALIDA = Path(__file__).resolve().parent / "resultados" / "iir_notch"


#%% ===========================================================================
# FUNCIONES DE DISEÑO Y PLANTILLA
# =============================================================================

def obtener_q() -> float:
    return F_NOTCH_HZ / BW_3DB_HZ if Q_MANUAL is None else float(Q_MANUAL)


def validar_configuracion() -> None:
    if FS_HZ <= 0.0:
        raise ValueError("FS_HZ debe ser positiva.")
    if not 0.0 < F_NOTCH_HZ < FS_HZ / 2.0:
        raise ValueError("F_NOTCH_HZ debe estar entre 0 y Nyquist.")
    if BW_3DB_HZ <= 0.0:
        raise ValueError("BW_3DB_HZ debe ser positivo.")
    if obtener_q() <= 0.0:
        raise ValueError("El factor de calidad Q debe ser positivo.")
    if PUNTOS_GRAFICO < 32:
        raise ValueError("PUNTOS_GRAFICO debe ser al menos 32.")


def disenar_iir_notch() -> np.ndarray:
    bb, aa = sig.iirnotch(w0=F_NOTCH_HZ, Q=obtener_q(), fs=FS_HZ)
    return sig.tf2sos(bb, aa)


def dibujar_plantilla_notch(ax: plt.Axes) -> None:
    bw_real = F_NOTCH_HZ / obtener_q()
    f_izq = F_NOTCH_HZ - bw_real / 2.0
    f_der = F_NOTCH_HZ + bw_real / 2.0
    ax.plot(
        [0.0, f_izq, F_NOTCH_HZ, f_der, FS_HZ / 2.0],
        [0.0, -3.0, PISO_GRAFICO_DB, -3.0, 0.0],
        "k--",
        lw=1.3,
        label="plantilla notch",
    )
    ax.axvline(F_NOTCH_HZ, color="tab:red", ls=":", lw=1.0)
    ax.axhline(-3.0, color="0.35", ls=":", lw=1.0, label="nivel -3 dB")


#%% ===========================================================================
# PROGRAMA PRINCIPAL
# =============================================================================

def main() -> None:
    validar_configuracion()
    CARPETA_SALIDA.mkdir(parents=True, exist_ok=True)

    q = obtener_q()
    bw_real = F_NOTCH_HZ / q
    sos_diseno = disenar_iir_notch()
    descripcion = (
        f"IIR notch: f0={F_NOTCH_HZ:g} Hz, BW@-3dB={bw_real:g} Hz, Q={q:g}"
    )
    rutas, cmsis, sos_arm = exportar_sos_cmsis(
        CARPETA_SALIDA,
        "iir_notch",
        sos_diseno,
        FS_HZ,
        descripcion,
        DIGITOS_SIGNIFICATIVOS_C,
    )

    error_conversion = verificar_conversion_cmsis(sos_arm, cmsis)
    radio_max = verificar_estabilidad_sos(sos_arm)
    ff, hh = respuesta_sos(sos_arm, FS_HZ, PUNTOS_GRAFICO)
    metricas = medir_notch(ff, hh, F_NOTCH_HZ)
    respuestas = {"IIR notch — coeficientes ARM float32": (ff, hh)}

    ruta_general = CARPETA_SALIDA / "iir_notch_respuesta.png" if GUARDAR_GRAFICOS else None
    ruta_zoom = CARPETA_SALIDA / "iir_notch_zoom.png" if GUARDAR_GRAFICOS else None
    ruta_pz = CARPETA_SALIDA / "iir_notch_polos_ceros.png" if GUARDAR_GRAFICOS else None
    titulo = f"IIR notch — f0={F_NOTCH_HZ:g} Hz — BW@-3dB={bw_real:g} Hz — Q={q:g}"
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
    graficar_polos_ceros_sos(
        sos_arm,
        titulo=f"IIR notch — polos y ceros — f0={F_NOTCH_HZ:g} Hz — Q={q:g}",
        ruta_png=ruta_pz,
        mostrar=False,
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

    print("\nDISEÑO IIR NOTCH")
    print(descripcion)
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
    if ruta_general is not None:
        print(f"gráfico: {ruta_general.resolve()}")
        print(f"zoom: {ruta_zoom.resolve()}")
        print(f"polos y ceros: {ruta_pz.resolve()}")

    if MOSTRAR_GRAFICOS:
        plt.show()


if __name__ == "__main__":
    main()
