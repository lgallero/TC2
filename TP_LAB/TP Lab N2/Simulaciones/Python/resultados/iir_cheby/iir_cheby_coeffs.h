/* Generado automáticamente para arm_biquad_cascade_df1_f32.
 * Chebyshev 1 pasabajos: fp=100 Hz, fstop=300 Hz, Amax=1 dB, Amin=60 dB
 * fs de diseño: 1000 Hz
 * Orden: b0, b1, b2, -a1, -a2 por cada etapa.
 */
#ifndef IIR_CHEBY_COEFFS_H
#define IIR_CHEBY_COEFFS_H

#include "arm_math.h"

#define IIR_CHEBY_NUM_STAGES (2U)
#define IIR_CHEBY_NUM_COEFFS (5U * IIR_CHEBY_NUM_STAGES)
#define IIR_CHEBY_STATE_LENGTH (4U * IIR_CHEBY_NUM_STAGES)

static const float32_t iir_cheby_coeffs[IIR_CHEBY_NUM_COEFFS] = {
    +1.83555041440e-03f, +3.67110082880e-03f, +1.83555041440e-03f, +1.55478513241e+00f, -6.49295449257e-01f,  /* etapa 1: b0,b1,b2,-a1,-a2 */
    +1.00000000000e+00f, +2.00000000000e+00f, +1.00000000000e+00f, +1.49955451488e+00f, -8.48218679428e-01f,  /* etapa 2: b0,b1,b2,-a1,-a2 */
};

#endif /* IIR_CHEBY_COEFFS_H */
