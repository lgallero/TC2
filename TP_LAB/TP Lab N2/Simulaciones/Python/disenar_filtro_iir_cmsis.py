#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diseño y exportación de filtros IIR para CMSIS-DSP.

Plantilla A (por defecto):
    Chebyshev tipo I pasabajos, fp=100 Hz, fsb=300 Hz,
    pérdida máxima=1 dB y atenuación mínima=60 dB.

Plantilla B:
    Notch de segundo orden, f0=50 Hz y BW @ -3 dB=1 Hz.

SciPy almacena cada SOS como [b0, b1, b2, a0, a1, a2] y usa
realimentación con signo negativo. CMSIS-DSP DF1 espera
[b0, b1, b2, -a1, -a2]. Este programa realiza y verifica esa conversión.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy import optimize, signal


@dataclass(frozen=True)
class Diseno:
    nombre: str
    descripcion: str
    sos: np.ndarray


def disenar_plantilla_a(
    fs_hz: float,
    fp_hz: float,
    fstop_hz: float,
    gpass_db: float,
    gstop_db: float,
) -> Diseno:
    """Diseña el Chebyshev I pasabajos de orden mínimo con iirdesign."""
    if not 0.0 < fp_hz < fstop_hz < fs_hz / 2.0:
        raise ValueError("Se requiere 0 < fp < fstop < fs/2 para la plantilla A.")

    sos = signal.iirdesign(
        wp=fp_hz,
        ws=fstop_hz,
        gpass=gpass_db,
        gstop=gstop_db,
        analog=False,
        ftype="cheby1",
        output="sos",
        fs=fs_hz,
    )
    descripcion = (
        f"Chebyshev I pasabajos: fp={fp_hz:g} Hz, fstop={fstop_hz:g} Hz, "
        f"Amax={gpass_db:g} dB, Amin={gstop_db:g} dB"
    )
    return Diseno("A", descripcion, np.asarray(sos, dtype=np.float64))


def disenar_plantilla_b(fs_hz: float, f0_hz: float, bw_hz: float) -> Diseno:
    """Diseña el notch a partir de Q=f0/BW mediante scipy.signal.iirnotch."""
    if not 0.0 < f0_hz < fs_hz / 2.0:
        raise ValueError("Se requiere 0 < f0 < fs/2 para la plantilla B.")
    if not 0.0 < bw_hz < 2.0 * f0_hz:
        raise ValueError("El ancho de banda del notch debe ser positivo y menor que 2*f0.")

    q = f0_hz / bw_hz
    b, a = signal.iirnotch(w0=f0_hz, Q=q, fs=fs_hz)
    sos = signal.tf2sos(b, a)
    descripcion = f"Notch: f0={f0_hz:g} Hz, BW@-3dB={bw_hz:g} Hz, Q={q:g}"
    return Diseno("B", descripcion, np.asarray(sos, dtype=np.float64))


def normalizar_sos(sos: np.ndarray) -> np.ndarray:
    """Normaliza a0=1 en todas las secciones."""
    sos = np.asarray(sos, dtype=np.float64).copy()
    if sos.ndim != 2 or sos.shape[1] != 6:
        raise ValueError("El arreglo SOS debe tener forma (cantidad_secciones, 6).")
    if np.any(np.isclose(sos[:, 3], 0.0)):
        raise ValueError("Se encontró una sección SOS con a0=0.")

    sos[:, :3] /= sos[:, 3, None]
    sos[:, 4:] /= sos[:, 3, None]
    sos[:, 3] = 1.0
    return sos


def sos_a_cmsis_df1(sos: np.ndarray) -> np.ndarray:
    """Convierte SOS de SciPy a [b0,b1,b2,-a1,-a2] de CMSIS-DSP DF1."""
    sos_n = normalizar_sos(sos)
    cmsis = sos_n[:, [0, 1, 2, 4, 5]].copy()
    cmsis[:, 3:] *= -1.0
    return cmsis.astype(np.float32)


def cmsis_df1_a_sos(cmsis: np.ndarray) -> np.ndarray:
    """Reconstruye SOS de SciPy desde coeficientes CMSIS; útil para verificar."""
    cmsis = np.asarray(cmsis, dtype=np.float32)
    if cmsis.ndim != 2 or cmsis.shape[1] != 5:
        raise ValueError("El arreglo CMSIS debe tener forma (cantidad_secciones, 5).")

    sos = np.empty((cmsis.shape[0], 6), dtype=np.float64)
    sos[:, :3] = cmsis[:, :3]
    sos[:, 3] = 1.0
    sos[:, 4:] = -cmsis[:, 3:]
    return sos


def respuesta_en_frecuencia(
    sos: np.ndarray, fs_hz: float, wor_n: int | np.ndarray = 65536
) -> tuple[np.ndarray, np.ndarray]:
    """Compatibilidad con versiones nuevas y anteriores de SciPy."""
    if hasattr(signal, "freqz_sos"):
        return signal.freqz_sos(sos, worN=wor_n, fs=fs_hz)
    return signal.sosfreqz(sos, worN=wor_n, fs=fs_hz)


def simular_cmsis_df1_f32(cmsis: np.ndarray, x: np.ndarray) -> np.ndarray:
    """Referencia en Python de la ecuación usada por arm_biquad_cascade_df1_f32."""
    coeffs = np.asarray(cmsis, dtype=np.float32)
    state = np.zeros((coeffs.shape[0], 4), dtype=np.float32)
    salida = np.empty(np.asarray(x).size, dtype=np.float32)

    for n, muestra in enumerate(np.asarray(x, dtype=np.float32)):
        entrada_etapa = np.float32(muestra)
        for etapa, (b0, b1, b2, a1, a2) in enumerate(coeffs):
            x1, x2, y1, y2 = state[etapa]
            y = np.float32(
                np.float32(b0 * entrada_etapa)
                + np.float32(b1 * x1)
                + np.float32(b2 * x2)
                + np.float32(a1 * y1)
                + np.float32(a2 * y2)
            )
            state[etapa] = (entrada_etapa, x1, y, y1)
            entrada_etapa = y
        salida[n] = entrada_etapa
    return salida


def verificar_conversion(sos_f32: np.ndarray, cmsis: np.ndarray) -> float:
    """Compara SciPy SOS contra una simulación DF1 con los mismos float32."""
    impulso = np.zeros(4096, dtype=np.float32)
    impulso[0] = 1.0
    y_scipy = signal.sosfilt(sos_f32.astype(np.float32), impulso)
    y_cmsis = simular_cmsis_df1_f32(cmsis, impulso)
    error_max = float(np.max(np.abs(y_scipy - y_cmsis)))
    if error_max > 1.0e-5:
        raise RuntimeError(
            f"La conversión SciPy/CMSIS no superó la verificación: error={error_max:.3e}"
        )
    return error_max


def medir_plantilla_a(
    sos: np.ndarray,
    fs_hz: float,
    fp_hz: float,
    fstop_hz: float,
    gpass_db: float,
    gstop_db: float,
) -> dict[str, float]:
    f, h = respuesta_en_frecuencia(sos, fs_hz)
    mag_db = 20.0 * np.log10(np.maximum(np.abs(h), np.finfo(float).tiny))
    perdida_max = float(-np.min(mag_db[f <= fp_hz]))
    atenuacion_min = float(-np.max(mag_db[f >= fstop_hz]))
    if perdida_max > gpass_db + 0.02 or atenuacion_min < gstop_db - 0.02:
        raise RuntimeError("Los coeficientes float32 no cumplen la plantilla A.")
    return {"perdida_max_db": perdida_max, "atenuacion_min_db": atenuacion_min}


def medir_plantilla_b(
    sos: np.ndarray, fs_hz: float, f0_hz: float, bw_objetivo_hz: float
) -> dict[str, float]:
    def nivel_menos_3db(f_hz: float) -> float:
        _, h = respuesta_en_frecuencia(sos, fs_hz, np.asarray([f_hz]))
        return float(np.abs(h[0]) ** 2 - 0.5)

    margen = min(max(10.0 * bw_objetivo_hz, 1.0), 0.99 * f0_hz)
    f_izq = optimize.brentq(nivel_menos_3db, f0_hz - margen, f0_hz)
    f_der = optimize.brentq(
        nivel_menos_3db, f0_hz, min(f0_hz + margen, 0.999 * fs_hz / 2.0)
    )
    _, h0 = respuesta_en_frecuencia(sos, fs_hz, np.asarray([f0_hz]))
    bw_medido = float(f_der - f_izq)
    if not np.isclose(bw_medido, bw_objetivo_hz, rtol=2.0e-4, atol=2.0e-4):
        raise RuntimeError("Los coeficientes float32 no conservan el BW del notch.")
    return {
        "f_3db_izq_hz": float(f_izq),
        "f_3db_der_hz": float(f_der),
        "bw_3db_hz": bw_medido,
        "notch_db": float(20.0 * np.log10(max(abs(h0[0]), np.finfo(float).tiny))),
    }


def escribir_header(
    ruta: Path, diseno: Diseno, fs_hz: float, cmsis: np.ndarray
) -> None:
    guard = f"COEFICIENTES_IIR_{diseno.nombre}_H"
    valores = cmsis.ravel()
    filas = []
    for etapa, fila in enumerate(cmsis, start=1):
        numeros = ", ".join(f"{float(v):+.9e}f" for v in fila)
        filas.append(f"    {numeros},  /* etapa {etapa}: b0, b1, b2, a1, a2 */")

    contenido = f"""/* Archivo generado por disenar_filtro_iir_cmsis.py.
 * {diseno.descripcion}
 * Frecuencia de muestreo usada en el diseño: {fs_hz:g} Hz
 * Orden CMSIS-DSP DF1 por etapa: {{b0, b1, b2, a1, a2}}
 */
#ifndef {guard}
#define {guard}

#include "arm_math.h"

#define IIR_NUM_STAGES ({cmsis.shape[0]}U)
#define IIR_NUM_COEFFS ({valores.size}U)
#define IIR_STATE_LENGTH (4U * IIR_NUM_STAGES)

static const float32_t iir_coeffs[IIR_NUM_COEFFS] = {{
{chr(10).join(filas)}
}};

#endif /* {guard} */
"""
    ruta.write_text(contenido, encoding="utf-8")


def graficar(
    ruta: Path,
    diseno: Diseno,
    sos: np.ndarray,
    fs_hz: float,
    args: argparse.Namespace,
) -> None:
    f, h = respuesta_en_frecuencia(sos, fs_hz)
    mag_db = 20.0 * np.log10(np.maximum(np.abs(h), 1.0e-8))
    fase_deg = np.unwrap(np.angle(h)) * 180.0 / np.pi

    fig, (ax_mag, ax_fase) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    ax_mag.plot(f, mag_db, color="tab:blue", lw=1.6)
    ax_fase.plot(f, fase_deg, color="tab:orange", lw=1.2)

    if diseno.nombre == "A":
        ax_mag.axvline(args.fp, color="tab:green", ls="--", label=f"fp={args.fp:g} Hz")
        ax_mag.axvline(
            args.fstop, color="tab:red", ls="--", label=f"fstop={args.fstop:g} Hz"
        )
        ax_mag.axhline(-args.gpass, color="tab:green", ls=":")
        ax_mag.axhline(-args.gstop, color="tab:red", ls=":")
        ax_mag.set_ylim(-(args.gstop + 25.0), 3.0)
    else:
        ax_mag.axvline(args.f0, color="tab:red", ls="--", label=f"f0={args.f0:g} Hz")
        ax_mag.axhline(-3.0, color="tab:green", ls=":", label="-3 dB")
        zoom = max(5.0 * args.bw, 5.0)
        ax_mag.set_xlim(max(0.0, args.f0 - zoom), min(fs_hz / 2.0, args.f0 + zoom))
        ax_mag.set_ylim(-100.0, 3.0)

    ax_mag.set_title(f"Plantilla {diseno.nombre} — {diseno.descripcion} — fs={fs_hz:g} Hz")
    ax_mag.set_ylabel("Módulo [dB]")
    ax_fase.set_ylabel("Fase [grados]")
    ax_fase.set_xlabel("Frecuencia [Hz]")
    for ax in (ax_mag, ax_fase):
        ax.grid(True, which="both", alpha=0.35)
    ax_mag.legend(loc="best")
    fig.tight_layout()
    fig.savefig(ruta, dpi=160)
    plt.close(fig)


def crear_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Diseña la plantilla IIR A o B y exporta coeficientes CMSIS-DSP f32."
    )
    parser.add_argument("--filtro", choices=("A", "B", "a", "b"), default="A")
    parser.add_argument("--fs", type=float, default=1000.0, help="Frecuencia de muestreo [Hz].")
    parser.add_argument("--salida", type=Path, default=Path(__file__).with_name("resultados"))

    grupo_a = parser.add_argument_group("Plantilla A")
    grupo_a.add_argument("--fp", type=float, default=100.0, help="Fin de banda de paso [Hz].")
    grupo_a.add_argument("--fstop", type=float, default=300.0, help="Inicio de rechazo [Hz].")
    grupo_a.add_argument("--gpass", type=float, default=1.0, help="Pérdida máxima [dB].")
    grupo_a.add_argument("--gstop", type=float, default=60.0, help="Atenuación mínima [dB].")

    grupo_b = parser.add_argument_group("Plantilla B")
    grupo_b.add_argument("--f0", type=float, default=50.0, help="Frecuencia del notch [Hz].")
    grupo_b.add_argument("--bw", type=float, default=1.0, help="Ancho de banda @ -3 dB [Hz].")
    return parser


def main() -> None:
    args = crear_parser().parse_args()
    opcion = args.filtro.upper()
    if args.fs <= 0.0:
        raise ValueError("La frecuencia de muestreo debe ser positiva.")

    if opcion == "A":
        diseno = disenar_plantilla_a(args.fs, args.fp, args.fstop, args.gpass, args.gstop)
    else:
        diseno = disenar_plantilla_b(args.fs, args.f0, args.bw)

    sos = normalizar_sos(diseno.sos)
    cmsis = sos_a_cmsis_df1(sos)
    sos_f32 = cmsis_df1_a_sos(cmsis)
    error_conversion = verificar_conversion(sos_f32, cmsis)

    _, polos, _ = signal.sos2zpk(sos_f32)
    radio_max = float(np.max(np.abs(polos)))
    if radio_max >= 1.0:
        raise RuntimeError(f"El filtro cuantizado a float32 es inestable: |p|max={radio_max:.9f}")

    if opcion == "A":
        metricas = medir_plantilla_a(
            sos_f32, args.fs, args.fp, args.fstop, args.gpass, args.gstop
        )
    else:
        metricas = medir_plantilla_b(sos_f32, args.fs, args.f0, args.bw)

    args.salida.mkdir(parents=True, exist_ok=True)
    sufijo_fs = f"{args.fs:g}".replace(".", "p")
    ruta_h = args.salida / f"coeficientes_iir_{opcion}_fs_{sufijo_fs}Hz.h"
    ruta_png = args.salida / f"respuesta_iir_{opcion}_fs_{sufijo_fs}Hz.png"
    escribir_header(ruta_h, diseno, args.fs, cmsis)
    graficar(ruta_png, diseno, sos_f32, args.fs, args)

    print(f"\n{diseno.descripcion}")
    print(f"Frecuencia de muestreo: {args.fs:g} Hz")
    print(f"Cantidad de etapas biquad: {cmsis.shape[0]}")
    print(f"Orden del filtro: {len(polos)}")
    print(f"Radio máximo de los polos (float32): {radio_max:.9f}")
    print(f"Error máximo SciPy SOS vs. CMSIS DF1 simulado: {error_conversion:.3e}")
    for nombre, valor in metricas.items():
        print(f"{nombre}: {valor:.9g}")

    print("\nSOS de SciPy [b0, b1, b2, a0, a1, a2]:")
    print(np.array2string(sos, precision=12, suppress_small=False))
    print("\nCMSIS-DSP DF1 [b0, b1, b2, a1, a2] (float32):")
    print(np.array2string(cmsis, precision=12, suppress_small=False))
    print("\nVector plano para pCoeffs:")
    print(", ".join(f"{float(v):+.9e}f" for v in cmsis.ravel()))
    print(f"\nHeader generado: {ruta_h.resolve()}")
    print(f"Gráfico generado: {ruta_png.resolve()}")


if __name__ == "__main__":
    main()
