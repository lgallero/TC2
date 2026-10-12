.options meascplxfmt=cartesian
* Referencias de Bode: entradas de impedancia infinita, salidas independientes.
* Los filtros de los ceros se invierten solamente en el visor de ondas.
Epolo1 polo_1 0 in 0 Laplace=1/(s+1)
Epolo3 polo_3 0 in 0 Laplace=3/(s+3)
Ecero2 base_cero_2 0 in 0 Laplace=2/(s+2)
Ecero4 base_cero_4 0 in 0 Laplace=4/(s+4)

* Frecuencias de quiebre de las referencias normalizadas.
.meas AC f_polo_1 WHEN mag(V(polo_1))=0.707106781186548 FALL=1
.meas AC f_cero_2 WHEN mag(V(in)/V(base_cero_2))=1.414213562373095 RISE=1
.meas AC f_polo_3 WHEN mag(V(polo_3))=0.707106781186548 FALL=1
.meas AC f_cero_4 WHEN mag(V(in)/V(base_cero_4))=1.414213562373095 RISE=1
.meas AC s_polo_1 PARAM -2*pi*f_polo_1
.meas AC s_cero_2 PARAM -2*pi*f_cero_2
.meas AC s_polo_3 PARAM -2*pi*f_polo_3
.meas AC s_cero_4 PARAM -2*pi*f_cero_4

* Contraste del dipolo real con la impedancia teorica (entrada AC 1).
.meas AC error_Z MAX mag(V(in)/(-I(V1))-(8/3)*V(polo_1)*V(polo_3)/(V(base_cero_2)*V(base_cero_4)))
.meas AC Z_baja FIND mag(V(in)/(-I(V1))) AT=0.001
.meas AC Z_alta FIND mag(V(in)/(-I(V1))) AT=100
