# Medidor L/C por impedancia compleja

Programa para el circuito de la propuesta de Medidas Electronicas II. Lee un
UNI-T UTD2202CEX+ por USBTMC/SCPI, toma `Vpp` de la tension sobre la carga y de
la salida del acondicionador de corriente, mide la fase entre ambas y calcula el
modelo serie del componente.

El equipo figura a veces como **UTD2202CEX+ARG** en Argentina; la familia que
aparece en la documentacion del fabricante es **UTD2000CEX+**.

## Conexion de las señales

La configuracion predeterminada supone el circuito dibujado en la propuesta:

- CH1: `Z_OUT`, es decir, tension sobre la carga desconocida respecto de GND.
- CH2: `I_OUT`, salida del amplificador diferencial respecto de GND.
- R patron: resistencia serie entre la salida del generador y `Z_OUT`.
- Ganancia: modulo de la ganancia diferencial (5 para R2/R3 = R5/R4 = 5).

Conviene cargar el valor **medido** de la resistencia patron y de la ganancia,
no solamente los nominales. La resistencia debe ser de baja inductancia y
adecuada para la potencia aplicada.

Las masas de las dos puntas del osciloscopio estan unidas internamente a tierra.
Conectarlas unicamente al GND comun del circuito; no conectar una masa a cada
extremo de la resistencia patron.

En el circuito del PDF:

```text
V_I_OUT = G * (V_Z_OUT - V_entrada) = -G * V_Rpatron
```

Por eso CH2 representa la corriente con 180 grados de inversion. El programa
suma 180 grados a la fase leida de forma predeterminada. Si se invirtieron las
entradas del operacional, se activo la inversion del canal o se usa otro
acondicionador, ajustar `--correccion-fase`.

## Ecuaciones implementadas

Con señales senoidales, `Vrms = Vpp/(2*sqrt(2))`. Como aparece el mismo factor
en numerador y denominador:

```text
I_R,pp  = V_I_OUT,pp / (R_patron * G)
I_R,rms = I_R,pp / (2*sqrt(2))
|Z_par| = R_patron * G * V_X,pp / V_I_OUT,pp
phi_par = wrap(signo * phi_scope + correccion_fase)
Z_par   = |Z_par| * (cos(phi_par) + j*sin(phi_par))
```

La rama R4+R5 del esquema carga `Z_OUT` con 20 kohm + 100 kohm = 120 kohm.
Para no confundir esa corriente con la del componente se aplica, por defecto:

```text
Y_DUT = 1/Z_par - 1/120000
Z_DUT = 1/Y_DUT = ESR + j*X
```

Se puede ignorar esta correccion con `--r-entrada-paralela inf`, o cargar el
valor real si se cambiaron R4/R5.

Para `X < 0`:

```text
C = 1/(2*pi*f*|X|)
D = ESR/|X|
```

Para `X > 0`:

```text
L = X/(2*pi*f)
Q = X/ESR
```

El valor absoluto en las ecuaciones del capacitor es importante: la reactancia
capacitiva es negativa, pero C y D son magnitudes positivas. Una resistencia
serie negativa se considera un error de polaridad, orden de canales o
correccion de fase y no se oculta con un valor absoluto.

## Comandos SCPI usados

El manual de programacion oficial de la familia UTD2000CEX+ documenta los
siguientes comandos (la terminacion es LF, `\n`):

```text
*IDN?
:MEASure:VPP? CHANnel1
:MEASure:VPP? CHANnel2
:MEASure:PHASe? CHANnel1,CHANnel2
:MEASure:FREQuency? CHANnel1
```

Fuentes: [pagina oficial del UTD2000CEX+](https://instruments.uni-trend.com/cate/68.html)
y [manual oficial de programacion](https://unitrend.oss-cn-hongkong.aliyuncs.com/uploads/attach/20250624/171101e2d93f099015b2851407068.pdf).

El orden de la consulta de fase es siempre carga primero y corriente despues.
Si una comprobacion con un capacitor conocido da signo inductivo, usar
`--invertir-signo-fase`. Si una resistencia conocida no queda cerca de 0 grados,
ajustar `--correccion-fase` hasta compensar el error fijo del acondicionador.

Para calibrar la fase a una frecuencia de trabajo, reemplazar temporalmente el
DUT por una resistencia conocida de modulo parecido. Si la fase cruda medida es
`phi_R`, usar aproximadamente:

```text
correccion_fase = -signo_fase * phi_R     (normalizada modulo 360 grados)
```

Por ejemplo, una lectura cruda de -179.4 grados requiere +179.4 grados. Repetir
esta calibracion cuando cambie mucho la frecuencia: el operacional, las puntas
y el osciloscopio agregan retardo. Este punto es especialmente importante para
Q alto o D bajo, porque cerca de +/-90 grados un error pequeño de fase produce
un error grande en la ESR.

## Instalacion en Linux (Ubuntu/Debian)

1. Instalar Python, soporte USB y herramientas de diagnostico:

   ```bash
   sudo apt update
   sudo apt install -y python3 python3-venv python3-pip libusb-1.0-0 usbutils
   ```

2. En la carpeta del proyecto, crear el entorno e instalar el programa y el
   backend USB de PyVISA:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install --upgrade pip
   python -m pip install -e '.[usb]'
   pyvisa-info
   ```

   PyVISA-py requiere PyUSB y una implementacion libusb para recursos USB. La
   documentacion del proyecto tambien advierte que en Linux hay que dar permiso
   tanto al dispositivo USB como a `/dev/usbtmcN`:
   [instalacion de PyVISA-py](https://github.com/pyvisa/pyvisa-py/blob/main/docs/source/installation.rst).

3. Conectar el puerto **USB Device** trasero del osciloscopio al PC y verificar:

   ```bash
   lsusb
   ls -l /dev/usbtmc*
   ```

4. Crear una regla udev especifica. Primero copiar de `lsusb` los cuatro digitos
   hexadecimales de VID y PID. Luego crear `/etc/udev/rules.d/99-unit-utd.rules`
   con `VID_REAL` y `PID_REAL` reemplazados por esos valores:

   ```udev
   SUBSYSTEM=="usb", ATTR{idVendor}=="VID_REAL", ATTR{idProduct}=="PID_REAL", MODE="0660", GROUP="plugdev", TAG+="uaccess"
   SUBSYSTEM=="usbmisc", KERNEL=="usbtmc*", MODE="0660", GROUP="plugdev", TAG+="uaccess"
   ```

   Aplicar los permisos y volver a conectar el cable:

   ```bash
   sudo usermod -aG plugdev "$USER"
   sudo udevadm control --reload-rules
   sudo udevadm trigger
   ```

   Cerrar sesion y volver a entrar si se agrego el usuario al grupo `plugdev`.
   Es preferible una regla con VID/PID real a dar permiso `0666` a todos los USB.

5. Descubrir el instrumento:

   ```bash
   medidor-lc descubrir
   ```

El programa intenta primero `/dev/usbtmcN` (driver USBTMC del kernel) y despues
recursos VISA mediante el backend puro de Python `@py`. Tambien se puede indicar
el recurso de manera explicita, por ejemplo `/dev/usbtmc0` o una direccion VISA
como `USB0::0x1234::0x5678::SERIE::INSTR`.

Si `lsusb` ve el equipo pero no existe `/dev/usbtmcN` ni aparece en PyVISA,
examinar la interfaz con:

```bash
lsusb -v -d VID:PID | grep -E 'bInterface(Class|SubClass|Protocol)'
```

USBTMC debe indicar clase `254` (`0xfe`) y subclase `3`. Si la unidad/firmware
expone una interfaz propietaria en lugar de USBTMC, estos comandos SCPI no se
pueden transportar con PyVISA: sera necesario el SDK de UNI-T o actualizar el
firmware compatible. No conviene instalar a ciegas el software antiguo para
Windows en Linux.

## Preparacion del osciloscopio

- Usar una senoide estable, sin recorte y sin continua innecesaria.
- Configurar correctamente 1X/10X en cada punta y en el menu del canal.
- Mostrar ambos canales con varias divisiones de amplitud y al menos 2 a 5
  periodos en pantalla.
- Disparar de CH1 para obtener una forma estable.
- Evitar que `I_OUT` sature contra la alimentacion del operacional.
- Para reducir ruido, el programa toma cinco juegos de lecturas y usa medianas.

## Uso

Medir con R patron de 10 ohm y ganancia 5:

```bash
medidor-lc medir --r-patron 10 --ganancia 5
```

Usar un recurso determinado y una frecuencia cargada manualmente:

```bash
medidor-lc medir \
  --resource /dev/usbtmc0 \
  --r-patron 10 \
  --ganancia 5 \
  --frecuencia 1000
```

Si la topologia no tiene la rama paralela R4+R5:

```bash
medidor-lc medir --r-patron 10 --ganancia 5 --r-entrada-paralela inf
```

Probar solamente las cuentas con valores cargados a mano:

```bash
medidor-lc calcular \
  --r-patron 10 \
  --ganancia 5 \
  --vpp-carga 3.18335 \
  --vpp-corriente 1 \
  --fase-cruda 90.72 \
  --frecuencia 1000 \
  --r-entrada-paralela inf
```

Agregar `--json` a `medir` o `calcular` para integrar la salida con otro
programa. Ver todas las opciones con `medidor-lc medir --help`.

## Verificacion local

Las pruebas sintetizan las lecturas esperables para un capacitor, un inductor y
la correccion de la rama paralela:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

La comunicacion fisica no puede verificarse sin conectar el osciloscopio; el
subcomando `descubrir` y `*IDN?` son la primera comprobacion en el equipo real.
