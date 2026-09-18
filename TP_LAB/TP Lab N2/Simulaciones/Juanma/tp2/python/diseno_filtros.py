"""
TPL2 - Teoria de los Circuitos II
Pre-Lab: diseno de los filtros digitales IIR (Filtro A: Chebyshev pasabajos,
Filtro B: Notch) y conversion de los coeficientes al formato que espera
arm_biquad_cascade_df1_f32 (CMSIS-DSP).

Requiere: numpy, scipy, matplotlib
"""
import numpy as np
from scipy import signal
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# Frecuencia de muestreo del sistema (ADC/DAC). Coincide con SAMPLE_RATE
# definido en app/inc/filter.h. Cambiarla aca y en filter.h si hace falta.
# ---------------------------------------------------------------------------
FS_SAMPLING = 1000.0  # Hz

# ---------------------------------------------------------------------------
# Filtro A - Plantilla: Chebyshev pasabajos
#   fp = 100 Hz, fs = 300 Hz, alpha_max = 1 dB, alpha_min = 60 dB
# (fp/fs son bordes de banda pasante/atenuada, NO la frecuencia de muestreo)
# ---------------------------------------------------------------------------
A_WP = 100.0
A_WS = 300.0
A_GPASS = 1.0
A_GSTOP = 60.0

# ---------------------------------------------------------------------------
# Filtro B - Plantilla: Notch
#   fnotch = 50 Hz, BW@3dB = 1 Hz
# ---------------------------------------------------------------------------
B_FNOTCH = 50.0
B_BW3DB = 1.0


def cmsis_sos_from_scipy_sos(sos):
    """Convierte SOS de scipy [b0,b1,b2,a0,a1,a2] (a0=1) al orden que espera
    arm_biquad_cascade_df1_f32: {b0,b1,b2,a1,a2} por seccion, con a1,a2
    NEGADOS respecto de la convencion estandar de scipy.

    scipy:  H(z) = (b0 + b1 z^-1 + b2 z^-2) / (1 + a1 z^-1 + a2 z^-2)
            y[n] = b0 x[n] + b1 x[n-1] + b2 x[n-2] - a1 y[n-1] - a2 y[n-2]

    CMSIS:  y[n] = b0 x[n] + b1 x[n-1] + b2 x[n-2] + a1 y[n-1] + a2 y[n-2]
            (ver AN "arm_biquad_cascade_df1_f32": los coeficientes a deben
            negarse respecto de la forma directa estandar)
    """
    coeffs = []
    for section in sos:
        b0, b1, b2, a0, a1, a2 = section
        assert abs(a0 - 1.0) < 1e-9, "scipy siempre normaliza a0=1 en sos"
        coeffs.extend([b0, b1, b2, -a1, -a2])
    return np.array(coeffs, dtype=np.float32)


def emit_c_array(name, cmsis_coeffs, sos_count):
    vals = ", ".join(f"{v:.10e}f" for v in cmsis_coeffs)
    print(f"#define {name.upper()}_SOS_NUM {sos_count}")
    print(f"float32_t {name}[{name.upper()}_SOS_NUM * 5] = {{ {vals} }};")
    print()


def design_filter_a():
    order, wn = signal.cheb1ord(A_WP, A_WS, A_GPASS, A_GSTOP, fs=FS_SAMPLING)
    sos = signal.iirdesign(A_WP, A_WS, A_GPASS, A_GSTOP, fs=FS_SAMPLING,
                            ftype='cheby1', output='sos')
    print(f"Filtro A (Chebyshev LPF): orden={order}, wn={wn:.3f} Hz, "
          f"secciones biquad={sos.shape[0]}")
    return sos


def design_filter_b():
    Q = B_FNOTCH / B_BW3DB
    b, a = signal.iirnotch(B_FNOTCH, Q, fs=FS_SAMPLING)
    sos = signal.tf2sos(b, a)
    print(f"Filtro B (Notch): fnotch={B_FNOTCH} Hz, Q={Q:.1f}, "
          f"secciones biquad={sos.shape[0]}")
    return sos


def plot_response(sos, fs, title, marks, fname):
    w, h = signal.sosfreqz(sos, worN=8192, fs=fs)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.semilogx(w, 20 * np.log10(np.maximum(np.abs(h), 1e-12)))
    for label, freq in marks:
        ax.axvline(freq, color='gray', linestyle='--', linewidth=0.8)
        ax.annotate(label, (freq, ax.get_ylim()[0] + 5), rotation=90,
                    fontsize=8, va='bottom')
    ax.set_title(title)
    ax.set_xlabel("Frecuencia [Hz]")
    ax.set_ylabel("Magnitud [dB]")
    ax.set_xlim(1, fs / 2)
    ax.grid(True, which='both', alpha=0.3)
    fig.tight_layout()
    fig.savefig(fname, dpi=150)
    print(f"  -> grafico guardado en {fname}")


def main():
    print(f"Frecuencia de muestreo (fs del sistema): {FS_SAMPLING} Hz\n")

    sos_a = design_filter_a()
    cmsis_a = cmsis_sos_from_scipy_sos(sos_a)
    emit_c_array("float_iir_taps_A", cmsis_a, sos_a.shape[0])
    plot_response(sos_a, FS_SAMPLING, "Filtro A - Chebyshev pasabajos",
                  [("fp=100Hz", 100), ("fs=300Hz", 300)],
                  "python/filtro_A_respuesta.png")

    print()

    sos_b = design_filter_b()
    cmsis_b = cmsis_sos_from_scipy_sos(sos_b)
    emit_c_array("float_iir_taps_B", cmsis_b, sos_b.shape[0])
    plot_response(sos_b, FS_SAMPLING, "Filtro B - Notch 50 Hz",
                  [("fnotch=50Hz", 50)],
                  "python/filtro_B_respuesta.png")


if __name__ == "__main__":
    main()
