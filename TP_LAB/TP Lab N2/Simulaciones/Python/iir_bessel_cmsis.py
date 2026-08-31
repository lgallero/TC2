#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IIR Bessel configurable a partir de una plantilla de retardo y atenuación.

La configuración inicial reproduce la plantilla E del TP: retardo constante de
80 us, desvío máximo del 5 % hasta 3 kHz y atenuación máxima de 1 dB a 2 kHz.
El orden mínimo se busca usando los coeficientes float32 que utilizará CMSIS.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import ScalarFormatter
from scipy import signal as sig

from filtros_cmsis_utils import (
    cmsis_df1_a_sos,
    exportar_sos_cmsis,
    fase_y_retardo,
    graficar_polos_ceros_sos,
    imprimir_coeficientes_iir,
    imprimir_configuracion_stm32,
    imprimir_rutas,
    magnitud_db,
    respuesta_sos,
    sos_scipy_a_cmsis_df1,
    verificar_conversion_cmsis,
    verificar_estabilidad_sos,
)


#%% ===========================================================================
# CONFIGURACIÓN: editar solamente esta sección para cambiar la plantilla
# =============================================================================

# Se usan 40 kHz porque es una frecuencia ya prevista en filter.h y permite
# cumplir simultáneamente las condiciones de retardo y atenuación.
FS_HZ = 40000.0

RETARDO_OBJETIVO_US = 80.0
F_LIMITE_RETARDO_HZ = 3000.0
DESVIO_RETARDO_MAX_PORC = 5.0

F_ATENUACION_HZ = 2000.0
ATENUACION_MAX_DB = 1.0

# None busca automáticamente el menor orden que cumple la plantilla. También
# puede escribirse un entero para comprobar un orden elegido manualmente.
ORDEN_MANUAL = None
ORDEN_MINIMO = 1
ORDEN_MAXIMO = 12

PUNTOS_EVALUACION = 65536
PUNTOS_GRAFICO = 65536
LIMITE_X_HZ = (0.0, 6000.0)
PISO_GRAFICO_DB = -40.0
MOSTRAR_GRAFICOS = True
GUARDAR_GRAFICOS = True
MOSTRAR_COEFICIENTES_TERMINAL = True

DIGITOS_SIGNIFICATIVOS_C = 17
CARPETA_SALIDA = Path(__file__).resolve().parent / "resultados" / "iir_bessel"


#%% ===========================================================================
# DISEÑO Y COMPROBACIÓN DE LA PLANTILLA
# =============================================================================

def validar_configuracion() -> None:
    if FS_HZ <= 2.0 * max(F_LIMITE_RETARDO_HZ, F_ATENUACION_HZ):
        raise ValueError("FS_HZ debe ser mayor que el doble de la frecuencia más alta.")
    if RETARDO_OBJETIVO_US <= 0.0:
        raise ValueError("RETARDO_OBJETIVO_US debe ser positivo.")
    if not 0.0 < DESVIO_RETARDO_MAX_PORC < 100.0:
        raise ValueError("DESVIO_RETARDO_MAX_PORC debe estar entre 0 y 100.")
    if ATENUACION_MAX_DB <= 0.0:
        raise ValueError("ATENUACION_MAX_DB debe ser positiva.")
    if PUNTOS_EVALUACION < 1024 or PUNTOS_GRAFICO < 1024:
        raise ValueError("Use al menos 1024 puntos para evaluar y graficar.")
    if ORDEN_MINIMO < 1 or ORDEN_MAXIMO < ORDEN_MINIMO:
        raise ValueError("El intervalo de órdenes configurado no es válido.")


def disenar_bessel(orden: int) -> np.ndarray:
    """Diseña el Bessel analógico con retardo DC exacto y lo digitaliza."""
    retardo_s = RETARDO_OBJETIVO_US * 1.0e-6
    ceros, polos, ganancia = sig.besselap(orden, norm="delay")
    ceros, polos, ganancia = sig.lp2lp_zpk(
        ceros,
        polos,
        ganancia,
        wo=1.0 / retardo_s,
    )
    ceros_z, polos_z, ganancia_z = sig.bilinear_zpk(
        ceros,
        polos,
        ganancia,
        fs=FS_HZ,
    )
    return sig.zpk2sos(ceros_z, polos_z, ganancia_z, pairing="nearest")


def medir_plantilla(sos: np.ndarray) -> dict[str, float]:
    """Mide atenuación y peor desvío de retardo en la banda especificada."""
    ff = np.linspace(0.0, F_LIMITE_RETARDO_HZ, PUNTOS_EVALUACION)
    if hasattr(sig, "freqz_sos"):
        _, hh = sig.freqz_sos(sos, worN=ff, fs=FS_HZ)
    else:
        _, hh = sig.sosfreqz(sos, worN=ff, fs=FS_HZ)

    omega = 2.0 * np.pi * ff / FS_HZ
    fase = np.unwrap(np.angle(hh))
    retardo_muestras = -np.gradient(fase, omega)
    retardo_us = retardo_muestras / FS_HZ * 1.0e6
    desvio_porc = 100.0 * np.abs(
        retardo_us - RETARDO_OBJETIVO_US
    ) / RETARDO_OBJETIVO_US

    _, h_atenuacion = sig.sosfreqz(
        sos,
        worN=np.asarray([F_ATENUACION_HZ]),
        fs=FS_HZ,
    )
    atenuacion_db = -float(magnitud_db(h_atenuacion)[0])
    indice_peor = int(np.argmax(desvio_porc))
    return {
        "atenuacion_en_f_db": atenuacion_db,
        "retardo_dc_us": float(retardo_us[0]),
        "retardo_min_hasta_f_us": float(np.min(retardo_us)),
        "retardo_max_hasta_f_us": float(np.max(retardo_us)),
        "desvio_max_retardo_porc": float(desvio_porc[indice_peor]),
        "frecuencia_peor_desvio_hz": float(ff[indice_peor]),
    }


def cumple_plantilla(metricas: dict[str, float]) -> bool:
    return (
        metricas["atenuacion_en_f_db"] <= ATENUACION_MAX_DB
        and metricas["desvio_max_retardo_porc"] <= DESVIO_RETARDO_MAX_PORC
    )


def seleccionar_diseno() -> tuple[int, np.ndarray, dict[str, float]]:
    if ORDEN_MANUAL is None:
        ordenes = range(ORDEN_MINIMO, ORDEN_MAXIMO + 1)
    else:
        if not isinstance(ORDEN_MANUAL, int) or ORDEN_MANUAL < 1:
            raise ValueError("ORDEN_MANUAL debe ser None o un entero positivo.")
        ordenes = (ORDEN_MANUAL,)

    resultados = []
    for orden in ordenes:
        sos_diseno = disenar_bessel(orden)
        cmsis = sos_scipy_a_cmsis_df1(sos_diseno)
        sos_arm = cmsis_df1_a_sos(cmsis)
        metricas = medir_plantilla(sos_arm)
        resultados.append((orden, metricas))
        if cumple_plantilla(metricas):
            return orden, sos_diseno, metricas

    detalle = "; ".join(
        f"N={orden}: A={m['atenuacion_en_f_db']:.4g} dB, "
        f"desvío={m['desvio_max_retardo_porc']:.4g} %"
        for orden, m in resultados
    )
    raise RuntimeError(
        "Ningún orden evaluado cumple la plantilla con los coeficientes float32. "
        + detalle
    )


#%% ===========================================================================
# GRÁFICOS
# =============================================================================

def graficar_respuesta_bessel(
    ff: np.ndarray,
    hh: np.ndarray,
    titulo: str,
    ruta_png: Path | None,
) -> plt.Figure:
    fase_grados, retardo_muestras = fase_y_retardo(ff, hh, FS_HZ)
    retardo_us = retardo_muestras / FS_HZ * 1.0e6
    limite_inferior = RETARDO_OBJETIVO_US * (1.0 - DESVIO_RETARDO_MAX_PORC / 100.0)
    limite_superior = RETARDO_OBJETIVO_US * (1.0 + DESVIO_RETARDO_MAX_PORC / 100.0)

    fig, (ax_mag, ax_fase, ax_retardo) = plt.subplots(
        3,
        1,
        figsize=(11, 10),
        sharex=True,
    )
    ax_mag.plot(ff, magnitud_db(hh), label="IIR Bessel — ARM float32")
    ax_mag.fill_between(
        [0.0, F_ATENUACION_HZ],
        [-ATENUACION_MAX_DB, -ATENUACION_MAX_DB],
        [2.0, 2.0],
        color="tab:green",
        alpha=0.15,
        label=f"Plantilla: pérdida ≤ {ATENUACION_MAX_DB:g} dB",
    )
    ax_mag.axhline(-ATENUACION_MAX_DB, color="tab:red", linestyle="--")
    ax_mag.axvline(F_ATENUACION_HZ, color="tab:red", linestyle=":")
    ax_mag.set_ylim(PISO_GRAFICO_DB, 2.0)
    ax_mag.set_ylabel("Módulo [dB]")
    ax_mag.set_title(titulo)

    ax_fase.plot(ff, fase_grados, label="Fase")
    ax_fase.set_ylabel("Fase [grados]")

    ax_retardo.plot(ff, retardo_us, label="Retardo de grupo")
    ax_retardo.fill_between(
        [0.0, F_LIMITE_RETARDO_HZ],
        [limite_inferior, limite_inferior],
        [limite_superior, limite_superior],
        color="tab:green",
        alpha=0.15,
        label=f"Plantilla: {RETARDO_OBJETIVO_US:g} us ± {DESVIO_RETARDO_MAX_PORC:g} %",
    )
    ax_retardo.axhline(RETARDO_OBJETIVO_US, color="black", linestyle="--")
    ax_retardo.axhline(limite_inferior, color="tab:red", linestyle="--")
    ax_retardo.axhline(limite_superior, color="tab:red", linestyle="--")
    ax_retardo.axvline(F_LIMITE_RETARDO_HZ, color="tab:red", linestyle=":")
    ax_retardo.set_ylabel("Retardo [us]")
    ax_retardo.set_xlabel("Frecuencia [Hz]")
    ax_retardo.yaxis.set_major_formatter(ScalarFormatter(useOffset=False))

    for eje in (ax_mag, ax_fase, ax_retardo):
        eje.set_xlim(*LIMITE_X_HZ)
        eje.grid(True, which="both", alpha=0.4)
        eje.legend(loc="best")

    mascara_visible = (
        (ff >= LIMITE_X_HZ[0])
        & (ff <= LIMITE_X_HZ[1])
        & np.isfinite(retardo_us)
    )
    if np.any(mascara_visible):
        minimo = min(limite_inferior, float(np.min(retardo_us[mascara_visible])))
        maximo = max(limite_superior, float(np.max(retardo_us[mascara_visible])))
        margen = max(2.0, 0.08 * (maximo - minimo))
        ax_retardo.set_ylim(max(0.0, minimo - margen), maximo + margen)

    fig.tight_layout()
    if ruta_png is not None:
        ruta_png.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(ruta_png, dpi=180, bbox_inches="tight")
    return fig


#%% ===========================================================================
# PROGRAMA PRINCIPAL
# =============================================================================

def main() -> None:
    validar_configuracion()
    CARPETA_SALIDA.mkdir(parents=True, exist_ok=True)

    orden, sos_diseno, _ = seleccionar_diseno()
    descripcion = (
        f"IIR Bessel: retardo={RETARDO_OBJETIVO_US:g} us, "
        f"desvío<={DESVIO_RETARDO_MAX_PORC:g}% hasta {F_LIMITE_RETARDO_HZ:g} Hz, "
        f"atenuación<={ATENUACION_MAX_DB:g} dB a {F_ATENUACION_HZ:g} Hz, "
        f"orden={orden}"
    )
    rutas, cmsis, sos_arm = exportar_sos_cmsis(
        CARPETA_SALIDA,
        "iir_bessel",
        sos_diseno,
        FS_HZ,
        descripcion,
        DIGITOS_SIGNIFICATIVOS_C,
    )

    error_conversion = verificar_conversion_cmsis(sos_arm, cmsis)
    radio_max = verificar_estabilidad_sos(sos_arm)
    metricas = medir_plantilla(sos_arm)
    if not cumple_plantilla(metricas):
        raise RuntimeError("El diseño dejó de cumplir la plantilla después de exportarlo.")

    ff, hh = respuesta_sos(sos_arm, FS_HZ, PUNTOS_GRAFICO)
    ruta_respuesta = (
        CARPETA_SALIDA / "iir_bessel_respuesta.png" if GUARDAR_GRAFICOS else None
    )
    ruta_pz = (
        CARPETA_SALIDA / "iir_bessel_polos_ceros.png" if GUARDAR_GRAFICOS else None
    )
    graficar_respuesta_bessel(ff, hh, descripcion, ruta_respuesta)
    graficar_polos_ceros_sos(
        sos_arm,
        titulo=f"IIR Bessel — polos y ceros — orden={orden}",
        ruta_png=ruta_pz,
        mostrar=False,
    )

    print("\nDISEÑO IIR BESSEL")
    print(descripcion)
    print(f"Frecuencia de muestreo: {FS_HZ:g} Hz")
    print(f"Orden mínimo obtenido: {orden}")
    print(f"Cantidad de etapas SOS: {cmsis.shape[0]}")
    print(f"Radio máximo de polos después de float32: {radio_max:.12g}")
    print(f"Error SciPy/CMSIS DF1 simulado: {error_conversion:.3e}")
    print("\nCOMPROBACIÓN DE LA PLANTILLA CON COEFICIENTES ARM FLOAT32")
    print(
        f"Atenuación a {F_ATENUACION_HZ:g} Hz: "
        f"{metricas['atenuacion_en_f_db']:.12g} dB "
        f"(máximo {ATENUACION_MAX_DB:g} dB)"
    )
    print(
        f"Retardo en DC: {metricas['retardo_dc_us']:.12g} us "
        f"(objetivo {RETARDO_OBJETIVO_US:g} us)"
    )
    print(
        f"Retardo mínimo/máximo hasta {F_LIMITE_RETARDO_HZ:g} Hz: "
        f"{metricas['retardo_min_hasta_f_us']:.12g} / "
        f"{metricas['retardo_max_hasta_f_us']:.12g} us"
    )
    print(
        f"Desvío máximo: {metricas['desvio_max_retardo_porc']:.12g} % "
        f"(máximo permitido {DESVIO_RETARDO_MAX_PORC:g} %)"
    )
    print(f"Resultado: {'CUMPLE' if cumple_plantilla(metricas) else 'NO CUMPLE'}")

    if MOSTRAR_COEFICIENTES_TERMINAL:
        imprimir_coeficientes_iir(sos_diseno, cmsis, DIGITOS_SIGNIFICATIVOS_C)

    print("\nEXCEL CONSOLIDADO Y GRÁFICOS")
    imprimir_rutas(rutas)
    if ruta_respuesta is not None:
        print(f"gráfico: {ruta_respuesta.resolve()}")
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
