from pathlib import Path
from datetime import datetime
import shutil
import nbformat

base = Path(r'D:\UTN\4to\TC2\TC2 - Lucas\TC2\Trabajo_semanal_9')
p = base/'trabajo_semanal_9.ipynb'
backup = base/'tmp'/('respaldo_presentacion_'+datetime.now().strftime('%Y%m%d_%H%M%S'))
backup.mkdir(parents=True)
shutil.copy2(p, backup/p.name)
nb = nbformat.read(p, as_version=4)
original = list(nb.cells)

imports = r'''import sympy as sp
import numpy as np
import matplotlib.pyplot as plt
from IPython.display import IFrame
from pytc2.general import s, print_latex, a_equal_b_latex_s
from pytc2.remociones import remover_polo_dc, remover_polo_infinito, remover_polo_jw
from pytc2.cuadripolos import TabcdZ_s, TabcdY_s

%matplotlib inline
sp.init_printing()
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11, 'figure.dpi': 100})

Q = s**3+2*s**2+2*s+1
P = s*(s**2+sp.Rational(1,16))
f = np.logspace(-4, 3, 7001)

def mostrar(nombre, expresion):
    print_latex(a_equal_b_latex_s(nombre, sp.factor(expresion)))

def verificar_cero(expresion):
    assert sp.cancel(expresion) == 0

def componentes(lista):
    for nombre, valor, unidad in lista:
        print(f'{nombre}: {sp.sstr(valor)} = {float(valor):.10g} {unidad}')

def matriz_pi(ya, zt, yc):
    yb = 1/zt
    Y = sp.Matrix([[ya+yb, -yb], [-yb, yc+yb]])
    return Y.inv().applyfunc(sp.factor)

def evaluar(funcion):
    return np.asarray(sp.lambdify(s, funcion, 'numpy')(2j*np.pi*f), dtype=complex)

def graficar_transferencia(numero, funcion, omega_cero):
    h = evaluar(funcion)
    fz = float(omega_cero)/(2*np.pi)
    fig, ax = plt.subplots(2, 1, figsize=(11, 6), sharex=True, constrained_layout=True)
    ax[0].semilogx(f, 20*np.log10(np.maximum(abs(h), 1e-16)), color='black')
    ax[1].semilogx(f, np.degrees(np.unwrap(np.angle(h))), color='tab:blue')
    ax[0].set_title(f'Ejercicio {numero} - Transferencia en Python')
    ax[0].set_ylabel('Módulo (dB)' if numero == 1 else 'Módulo (dB ref. 1 Ω)')
    ax[1].set_ylabel('Fase (°)')
    ax[1].set_xlabel('Frecuencia (Hz)')
    for eje in ax:
        eje.grid(True, which='both', alpha=.3)
        eje.axvline(fz, color='gray', ls=':', lw=1)
    plt.show()

def graficar_parametros(numero, excitacion, transferencia):
    nombre = 'Z_{22}' if numero == 2 else 'Z_{11}'
    fig, ax = plt.subplots(2, 1, figsize=(11, 6), sharex=True, constrained_layout=True)
    for eje, funcion, etiqueta, color in [
        (ax[0], transferencia, 'Z_{21}', 'red'),
        (ax[1], excitacion, nombre, 'blue')
    ]:
        eje.semilogx(f, 20*np.log10(np.maximum(abs(evaluar(funcion)), 1e-16)), color=color)
        eje.set_ylabel('$'+etiqueta+'$ (dB ref. 1 Ω)')
        eje.grid(True, which='both', alpha=.3)
    ax[0].set_title(f'Ejercicio {numero} - Parámetros del cuadripolo en Python')
    ax[1].set_xlabel('Frecuencia (Hz)')
    plt.show()'''
nb.cells[2].source = imports


def imagen(nombre, descripcion, ancho):
    return f'<div align="center">\n    <img src="./Imagenes/{nombre}" alt="{descripcion}" width="{ancho}" style="max-width:100%; height:auto;" />\n</div>'


def cursores(n, parametro):
    return ('<div align="center">\n'
            f'    <img src="./Imagenes/Ej{n} Simulacion PoloCero Z21.png" alt="Lecturas de los cursores para Z21 del ejercicio {n}" width="290" />\n'
            f'    <img src="./Imagenes/Ej{n} Simulacion PoloCero {parametro}.png" alt="Lecturas de los cursores para {parametro} del ejercicio {n}" width="290" />\n'
            '</div>')

lt = {}
lt[1] = r'''### <ins>Simulación en LTspice</ins>

Se simula el circuito con $R_g=1\;\Omega$ y la salida abierta. La transferencia se mide como `V(V2)/V(Vg)`.

'''+imagen('Ej1 Simulacion Circuito.png', 'Circuito simulado del ejercicio 1', 760)+r'''

#### Módulo y fase de la transferencia

'''+imagen('Ej1 Simulacion Modulo y Fase.png', 'Módulo y fase de la transferencia del ejercicio 1 en LTspice', 1100)+r'''

#### Parámetros del cuadripolo

Las curvas siguientes corresponden a $Z_{21}$ y $Z_{11}$ del cuadripolo LC, sin incluir $R_g$.

'''+imagen('Ej1 Simulacion Z21 Z11.png', 'Z21 y Z11 del ejercicio 1 en LTspice', 1100)+r'''

Los cursores ubican el cero de $Z_{21}$ cerca de $0{,}0398\;\mathrm{Hz}$, el polo común cerca de $0{,}1125\;\mathrm{Hz}$ y el cero de $Z_{11}$ cerca de $0{,}2251\;\mathrm{Hz}$.

'''+cursores(1, 'Z11')
lt[2] = r'''### <ins>Simulación en LTspice</ins>

Se aplica una corriente AC unitaria a la entrada y se conecta $R_L=1\;\Omega$ en la salida. La transimpedancia se mide como `V(V2)/I(I1)`.

'''+imagen('Ej2 Simulacion Circuito.png', 'Circuito simulado del ejercicio 2', 900)+r'''

#### Módulo y fase de la transimpedancia

'''+imagen('Ej2 Simulacion Modulo y Fase.png', 'Módulo y fase de la transimpedancia del ejercicio 2 en LTspice', 1100)+r'''

#### Parámetros del cuadripolo

Se presentan $Z_{21}$ y $Z_{22}$ del cuadripolo LC sin la resistencia de carga.

'''+imagen('Ej2 Simulacion Z21 Z22.png', 'Z21 y Z22 del ejercicio 2 en LTspice', 1100)+r'''

Los cursores muestran el cero de $Z_{22}$ cerca de $0{,}1125\;\mathrm{Hz}$, el polo común cerca de $0{,}2251\;\mathrm{Hz}$ y el cero de $Z_{21}$ cerca de $0{,}4775\;\mathrm{Hz}$.

'''+cursores(2, 'Z22')
lt[3] = r'''### <ins>Simulación en LTspice</ins>

Se simula el generador de corriente con $R_g=1\;\Omega$ en paralelo. La salida se toma sobre $L_{3B}$ y se mide `V(V2)/I(Ig)`.

'''+imagen('Ej3 Simulacion Circuito.png', 'Circuito simulado del ejercicio 3', 950)+r'''

#### Módulo y fase de la transimpedancia

'''+imagen('Ej3 Simulacion Modulo y Fase.png', 'Módulo y fase de la transimpedancia del ejercicio 3 en LTspice', 1100)+r'''

La lectura a $1\;\mathrm{kHz}$ confirma el nivel de $-6\;\mathrm{dB}$ en la meseta de alta frecuencia.

'''+imagen('Ej3 Simulacion Modulo Alta Frec.png', 'Lectura de menos 6 dB a alta frecuencia en el ejercicio 3', 300)+r'''

#### Parámetros del cuadripolo

Se presentan $Z_{21}$ y $Z_{11}$ del cuadripolo LC sin $R_g$, manteniendo los dos inductores del divisor de salida.

'''+imagen('Ej3 Simulacion Z21 Z11.png', 'Z21 y Z11 del ejercicio 3 en LTspice', 1100)+r'''

Los cursores ubican el cero de $Z_{21}$ cerca de $0{,}0398\;\mathrm{Hz}$, el polo común cerca de $0{,}1125\;\mathrm{Hz}$ y el cero de $Z_{11}$ cerca de $0{,}2251\;\mathrm{Hz}$.

'''+cursores(3, 'Z11')

conclusiones = {
1: r'''### <ins>Conclusión</ins>

Las curvas de Python y la simulación en LTspice muestran el nulo de transmisión en $\omega_z=1/4\;\mathrm{rad/s}$, equivalente a $f_z\approx0{,}03979\;\mathrm{Hz}$, y una transferencia que tiende a $1$ ($0\;\mathrm{dB}$) a alta frecuencia. Los polos y ceros observados en $Z_{11}$ y $Z_{21}$ coinciden con las funciones usadas en la síntesis. Se verifica así el circuito obtenido con $k_1=1$.''',
2: r'''### <ins>Conclusión</ins>

La simulación en LTspice reproduce la respuesta calculada en Python: la transimpedancia tiende a $1\;\Omega$ a baja frecuencia, se anula en $\omega_z=3\;\mathrm{rad/s}$ ($f_z\approx0{,}47746\;\mathrm{Hz}$) y cae a alta frecuencia con una pendiente asintótica de $-20\;\mathrm{dB/década}$. Las curvas de $Z_{22}$ y $Z_{21}$ también presentan los polos y ceros previstos. Estos resultados verifican la ubicación de los componentes y el valor $k_2=1/9$.''',
3: r'''### <ins>Conclusión</ins>

Las curvas de Python y LTspice conservan el nulo en $f_z\approx0{,}03979\;\mathrm{Hz}$ y alcanzan una meseta de $-6\;\mathrm{dB}$ a alta frecuencia, confirmada por la lectura del cursor. El divisor inductivo mantiene $Z_{11}$ y reduce $Z_{21}$ en $6\;\mathrm{dB}$ respecto del ejercicio 1, de acuerdo con $k_3=10^{-6/20}\approx0{,}501187$. La síntesis cumple la condición de nivel adoptada para la banda de paso.'''
}

bloques = {}
for n, indices in [(1,(15,16,17,18)), (2,(28,29,30,31)), (3,(39,40,41,42))]:
    h, t, l, z = (original[i] for i in indices)
    nombre = '$Z_{21}$ y $Z_{22}$' if n==2 else '$Z_{21}$ y $Z_{11}$'
    h.source = f'### <ins>Curvas en Python</ins>\n\nSe grafica el módulo y la fase de la transferencia obtenida, seguido de las curvas de {nombre} del cuadripolo LC. La frecuencia se expresa en Hz, con $f=\\omega/(2\\pi)$.'
    t.source = f'graficar_transferencia({n}, T{n}, '+('3)' if n==2 else 'sp.Rational(1,4))')
    exc = 'Z22_2' if n==2 else f'Z11_{n}'
    z.source = f'graficar_parametros({n}, {exc}, Z21_red{n})'
    l.source = lt[n]
    bloques[indices[0]] = [h,t,z,l,nbformat.v4.new_markdown_cell(conclusiones[n])]

nuevas=[]
i=0
while i<len(original):
    if i in bloques:
        nuevas.extend(bloques[i]); i+=4
    else:
        nuevas.append(original[i]); i+=1
nb.cells=nuevas
# Se conserva el desarrollo y se retira el apartado de archivos auxiliares.
referencias=next(c for c in nb.cells if c.get('id')=='2774e230')
referencias.source='## <ins>Referencias</ins>'+referencias.source.split('## <ins>Referencias</ins>',1)[1]
for c in nb.cells:
    if c.cell_type=='code':
        c.execution_count=None
        c.outputs=[]
nbformat.validate(nb)
nbformat.write(nb,p)

# Se retiran únicamente los archivos auxiliares creados para las pruebas .cir.
folder=base/'Simulaciones'
retirados=[]
for n in (1,2,3):
    for archivo in folder.glob(f'Ejercicio{n}_parametros.*'):
        if archivo.is_file():
            assert archivo.resolve().parent == folder.resolve()
            shutil.copy2(archivo,backup/archivo.name)
            archivo.unlink()
            retirados.append(archivo.name)
for nombre in ('verificar_ts9.py','verificacion_resultados.json'):
    archivo=folder/nombre
    if archivo.exists():
        shutil.copy2(archivo,backup/nombre)
        archivo.unlink()
        retirados.append(nombre)
cache=folder/'__pycache__'
if cache.exists():
    for archivo in cache.glob('verificar_ts9.*.pyc'):
        assert archivo.resolve().parent == cache.resolve()
        archivo.unlink()
print('Notebook actualizado:',len(nb.cells),'celdas')
print('Respaldo:',backup)
print('Auxiliares retirados:',', '.join(retirados))
