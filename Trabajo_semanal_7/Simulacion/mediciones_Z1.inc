* Mediciones: modulo en dB, fase en grados, frecuencias en Hz.
* Pendientes calculadas entre puntos separados una decada.
.options plotwinsize=0 numdgt=15 measdgt=10 meascplxfmt=cartesian
.meas AC db_baja_a FIND 20*log10(mag(V(in)/(-I(V1)))) AT=0.001
.meas AC db_baja_b FIND 20*log10(mag(V(in)/(-I(V1)))) AT=0.01
.meas AC db_alta_a FIND 20*log10(mag(V(in)/(-I(V1)))) AT=10
.meas AC db_alta_b FIND 20*log10(mag(V(in)/(-I(V1)))) AT=100
.meas AC pendiente_baja_db_dec PARAM db_baja_b-db_baja_a
.meas AC pendiente_alta_db_dec PARAM db_alta_b-db_alta_a
.meas AC fase_tramo1_grados FIND 180/pi*ph(V(in)/(-I(V1))) AT=0.1
.meas AC modulo_tramo1_db FIND 20*log10(mag(V(in)/(-I(V1)))) AT=0.1
.meas AC fase_tramo2_grados FIND 180/pi*ph(V(in)/(-I(V1))) AT=0.18
.meas AC modulo_tramo2_db FIND 20*log10(mag(V(in)/(-I(V1)))) AT=0.18
.meas AC fase_tramo3_grados FIND 180/pi*ph(V(in)/(-I(V1))) AT=0.25
.meas AC modulo_tramo3_db FIND 20*log10(mag(V(in)/(-I(V1)))) AT=0.25
.meas AC fase_tramo4_grados FIND 180/pi*ph(V(in)/(-I(V1))) AT=0.4
.meas AC modulo_tramo4_db FIND 20*log10(mag(V(in)/(-I(V1)))) AT=0.4
.meas AC f_cero1_teorica_hz PARAM 1/(2*pi)
.meas AC f_polo1_teorica_hz PARAM sqrt(2)/(2*pi)
.meas AC f_cero2_teorica_hz PARAM sqrt(3)/(2*pi)
.meas AC f_cambio1_medida_hz WHEN im(V(in)/(-I(V1)))=0 CROSS=1
.meas AC f_cambio2_medida_hz WHEN im(V(in)/(-I(V1)))=0 CROSS=2
.meas AC f_cambio3_medida_hz WHEN im(V(in)/(-I(V1)))=0 CROSS=3
