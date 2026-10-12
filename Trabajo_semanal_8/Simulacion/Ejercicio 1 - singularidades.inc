.options meascplxfmt=cartesian
.param h=4.4775908783877
* Referencias con entrada de impedancia infinita y salidas independientes.
Epolo1 polo_real 0 in 0 Laplace=1/(s+1)
Epolo2 polos_complejos 0 in 0 Laplace=25/(s*s+h*s+25)
Ecero base_ceros 0 in 0 Laplace=1/(s*s+s+1)

* Frecuencia de quiebre del polo real: modulo normalizado -3.0103 dB.
.meas AC f_polo_real WHEN mag(V(polo_real))=0.707106781186548 FALL=1
.meas AC s_polo_real PARAM -2*pi*f_polo_real

* Frecuencias naturales de los pares complejos: parte real nula del factor.
* Son omega0/(2*pi), no las partes imaginarias de las raices ni picos de Z.
.meas AC f0_polos WHEN re(V(polos_complejos))=0 FALL=1
.meas AC f0_ceros WHEN re(V(in)/V(base_ceros))=0 FALL=1
.meas AC omega0_polos PARAM 2*pi*f0_polos
.meas AC omega0_ceros PARAM 2*pi*f0_ceros

* Reconstruccion teorica con entrada AC 1.
.meas AC error_Z MAX mag(V(in)/(-I(V1))-V(polo_real)*V(polos_complejos)/(25*V(base_ceros)))
.meas AC Z_baja FIND mag(V(in)/(-I(V1))) AT=0.001
.meas AC Z_alta FIND mag(V(in)/(-I(V1))) AT=100
.meas AC M_baja_1 FIND db(mag(V(in)/(-I(V1)))) AT=0.001
.meas AC M_baja_2 FIND db(mag(V(in)/(-I(V1)))) AT=0.01
.meas AC pendiente_baja PARAM M_baja_2-M_baja_1
.meas AC M_alta_1 FIND db(mag(V(in)/(-I(V1)))) AT=10
.meas AC M_alta_2 FIND db(mag(V(in)/(-I(V1)))) AT=100
.meas AC pendiente_alta PARAM M_alta_2-M_alta_1
