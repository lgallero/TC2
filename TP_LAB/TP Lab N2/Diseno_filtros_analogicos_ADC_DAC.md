# Filtros analogicos de entrada y salida del ADC/DAC

## 1. Datos del sistema

- Placa: NUCLEO-F446RE (STM32F446RE).
- Entrada: `ADC1_IN0`, pin `PA0` (`A0` en el conector Arduino).
- Salida: `DAC_OUT1`, pin `PA4` (`A2` en el conector Arduino).
- Resolucion: 12 bits.
- Frecuencia de muestreo: `f_s = 1000 Hz`.
- Plantilla A: Chebyshev pasabajos con banda de paso hasta `100 Hz` y rechazo desde
  `300 Hz`.
- Plantilla B: notch centrado en `50 Hz`, con ancho de banda de `1 Hz`.
- Frecuencia de Nyquist: `f_N = f_s/2 = 500 Hz`.

El objetivo de estas redes analogicas no es implementar ninguna de las dos plantillas, sino
limitar las componentes fuera de la banda de muestreo sin ocultar el comportamiento del
filtro digital. Por eso se adopta una frecuencia de corte igual, aproximadamente, a Nyquist:
`f_c ~= 500 Hz`.

Con esta eleccion, la red analogica es practicamente transparente alrededor del notch de
`50 Hz` y en la banda de paso del Chebyshev hasta `100 Hz`.

## 2. Celda de primer orden elegida

Los dos filtros usan la misma red RC pasabajos:

- `R = 6.8 kohm`
- `C = 47 nF`

La funcion transferencia es

```text
             1
H(s) = ---------------
       1 + s R C
```

y su frecuencia de corte resulta

```text
f_c = 1/(2*pi*R*C)
    = 1/(2*pi*6.8 kohm*47 nF)
    = 497.98 Hz
```

La constante de tiempo es `tau = R*C = 319.6 us` y la pendiente asintotica por encima de
`f_c` es `-20 dB/decada`.

## 3. Filtro de entrada (anti-alias)

Conectar la red inmediatamente antes del ADC:

```text
 Vin filtrada                PA0 / A0 / ADC1_IN0
 desde la fuente ---- R1 -----------o
                       6.8 kohm      |
                                     | C1 = 47 nF
                                     |
                                    AGND
```

El capacitor debe quedar fisicamente cerca del pin `PA0` y su retorno debe ir a masa
analogica con una conexion corta.

La red deja pasar el nivel continuo de polarizacion. Para una senal bipolar generada en el
laboratorio, aplicar al ADC una senal centrada en `1.65 V`; como margen practico, no superar
aproximadamente `3.0 Vpp` para mantener la entrada dentro de `0 a 3.3 V`.

## 4. Filtro de salida (reconstruccion)

Conectar la segunda red despues del DAC:

```text
 PA4 / A2 / DAC_OUT1                       Vout filtrada
 --------------------- R2 ----------------------o
                        6.8 kohm                 |
                                                 | C2 = 47 nF
                                                 |
                                                AGND
```

Medir `Vout filtrada` con una entrada de alta impedancia (osciloscopio en `1 Mohm` o
`10 Mohm`). No usar terminacion de `50 ohm`: produciria una atenuacion muy grande. Si la
salida debe alimentar una carga baja, agregar despues del RC un amplificador operacional
seguidor apto para alimentacion de 3.3 V.

La resistencia serie aisla al buffer interno del DAC del capacitor de `47 nF`. A alta
frecuencia el DAC ve aproximadamente `6.8 kohm`, por encima de la carga resistiva minima de
`5 kohm` indicada para el buffer habilitado.

## 5. Respuesta esperada de cada filtro

| Frecuencia | Modulo | Atenuacion |
|---:|---:|---:|
| 50 Hz | 0.995 | -0.04 dB |
| 100 Hz | 0.981 | -0.17 dB |
| 300 Hz | 0.857 | -1.34 dB |
| 498 Hz | 0.707 | -3.01 dB |
| 500 Hz | 0.705 | -3.03 dB |
| 900 Hz | 0.484 | -6.30 dB |
| 1000 Hz | 0.446 | -7.01 dB |

Como los filtros de entrada y salida aparecen en cascada durante una medicion completa, la
perdida analogica total es aproximadamente `-0.09 dB` a `50 Hz` y `-0.34 dB` a `100 Hz`.
Por lo tanto, su efecto sobre el notch y sobre la banda de paso del Chebyshev es pequeno.

Para analizar con precision el notch en frecuencias cercanas a Nyquist, se debe descontar de
la medicion la respuesta conocida de estas redes RC, ya que cada una alcanza `-3 dB` cerca
de `500 Hz`.

## 6. Ajuste recomendado del ADC

El proyecto tiene configurado el tiempo minimo de adquisicion (`3 ciclos`). Debido a que la
frecuencia de muestreo es solamente `1 kHz`, conviene cambiarlo a
`ADC_SAMPLETIME_84CYCLES`. Con el reloj ADC actual de `21 MHz`, esto corresponde a `4 us`
de adquisicion y no compromete el periodo de muestreo de `1 ms`.

Este cambio debe realizarse tanto en STM32CubeMX como en el codigo generado, para que una
regeneracion del proyecto no lo revierta.

## 7. Limitacion de primer orden

Una celda de primer orden solamente cae `20 dB/decada`. Por eso este circuito es correcto
como filtro analogico sencillo exigido por el trabajo, pero la atenuacion de componentes por
encima de Nyquist es limitada. El rechazo de `60 dB` de la plantilla A corresponde al filtro
digital, no a estas redes analogicas.

## 8. Lista de materiales

- 2 resistencias de `6.8 kohm`, preferentemente de 1 %.
- 2 capacitores de `47 nF`, preferentemente de pelicula o ceramicos X7R.
- Cables cortos y masa comun entre generador, placa y osciloscopio.

## Referencias

- STMicroelectronics, *STM32F446xC/E datasheet*, DS10693.
- STMicroelectronics, *How to optimize the ADC accuracy in the STM32 MCUs*, AN2834.
- STMicroelectronics, *STM32 Nucleo-64 boards*, UM1724.
