from pathlib import Path
import math
import nbformat as nbf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Circle
from matplotlib.path import Path as MplPath
from matplotlib.transforms import Bbox

BASE = Path(__file__).resolve().parents[1]
IM = BASE/'Imagenes'


def mapa(numero):
    """Mapa en el estilo de TS8: ejes apilados, RP/RT y movimiento de ceros."""
    es2 = numero == 2
    plt.rcParams.update({'font.family':'STIXGeneral', 'mathtext.fontset':'stix'})
    fig, ax = plt.subplots(figsize=(8.6, 10.0))
    ax.set(xlim=(-1.4, 13.15), ylim=(-15.4, .88)); ax.axis('off')
    ax.set_aspect('equal', adjustable='box')
    rojo, verde, cyan = '#f22342', '#009745', '#007a99'
    xinf = 11.25
    escala = 3 if es2 else 6
    pos = lambda w: escala*w
    yy = [-2.1*i for i in range(8)]
    etiquetas = [r'Z_{21}',r'Z_{22}' if es2 else r'Z_{11}',
                 r'1/Z_{22}' if es2 else r'1/Z_{11}',r'Y_2',r'Z_2',r'Z_4',r'Y_4',r'Y_6=0']
    a, b = 1/math.sqrt(2), math.sqrt(2)
    ceros = [[3], [a], [0,b], [0,3], [a], [], [0], []] if es2 else [[0,.25],[0,b],[a],[.25],[0,b],[0],[],[]]
    polos = [[0,b],[0,b],[a],[a],[0,3],[0],[],[]] if es2 else [[a],[a],[0,b],[0,b],[.25],[],[0],[]]
    cinf = [True,True,False,False,True,True,False,False] if es2 else [False,False,True,True,False,False,True,False]
    fmt = lambda w: r'\frac{1}{4}' if abs(w-.25)<1e-8 else (r'\frac{\sqrt{2}}{2}' if abs(w-a)<1e-8 else (r'\sqrt{2}' if abs(w-b)<1e-8 else '3'))
    def marca(x,y,cero,etiqueta=None,cancelado=False):
        if cero:
            ax.add_patch(Circle((x,y),.19,fill=False,edgecolor=verde,lw=1.8,ls='--' if cancelado else '-'))
        else:
            ax.plot([x-.13,x+.13],[y-.13,y+.13],color=rojo,lw=1.9)
            ax.plot([x-.13,x+.13],[y+.13,y-.13],color=rojo,lw=1.9)
        if etiqueta: ax.text(x,y-.37,'$'+etiqueta+'$',ha='center',va='top',fontsize=15)
    for i,y in enumerate(yy):
        ax.annotate('',xy=(12.2,y),xytext=(0,y),arrowprops={'arrowstyle':'->','lw':1.15,'color':'black'})
        ax.text(-.62,y,'$'+etiquetas[i]+'$',ha='right',va='center',fontsize=23)
        ax.text(12.4,y,r'$j\omega$',va='center',fontsize=18)
        ax.text(0,y-.37,'$0$',ha='center',va='top',fontsize=15)
        ax.text(xinf,y-.37,r'$\infty$',ha='center',va='top',fontsize=18)
        for x in [10.1,10.28]: ax.plot([x,x+.18],[y-.17,y+.17],color='gray',lw=1)
        for w in ceros[i]: marca(pos(w),y,True,fmt(w) if w else None)
        for w in polos[i]: marca(pos(w),y,False,fmt(w) if w else None)
        if i<7: marca(xinf,y,cinf[i])
    def rodear(x,y,t):
        ax.add_patch(Circle((x,y),.30,fill=False,edgecolor=cyan,lw=1.25))
        ax.text(x,y+.45,t,ha='center',va='bottom',fontsize=16,color=cyan,fontweight='bold')
    def mover(x1,i,x2,j):
        # Los cuatro puntos quedan dentro del espacio libre entre las filas.
        # La curva cúbica no puede cruzar el eje de llegada ni las etiquetas.
        inicio = (x1, yy[i]-1.15)
        fin = (x2, yy[j]+.32)
        distancia = abs(x2-x1)
        direccion = 1 if x2>x1 else -1
        # Salida horizontal con extremo redondeado y llegada diagonal suave.
        # La misma geometría se refleja para las remociones hacia la izquierda.
        control1 = (x1+direccion*min(.30*distancia,1.40), inicio[1])
        control2 = (x2-direccion*min(.20*distancia,.65), fin[1]+.16)
        estilo = '-|>,head_length=0.55,head_width=0.25'
        camino = MplPath([inicio, control1, control2, fin],
                         [MplPath.MOVETO, MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4])
        ax.add_patch(FancyArrowPatch(path=camino, arrowstyle=estilo,
                      mutation_scale=13,lw=2,color=verde,joinstyle='miter',capstyle='round'))
    def permanece(x,i,j):
        ax.annotate('',xy=(x,yy[j]+.27),xytext=(x,yy[i]-1.15),
                    arrowprops={'arrowstyle':'->','lw':.8,'color':rojo})
    rodear(xinf if es2 else 0,yy[2],'RP')
    mover(pos(b if es2 else a),2,pos(3 if es2 else .25),3)
    permanece(pos(a if es2 else b),2,3)
    permanece(xinf if es2 else 0,2,3)
    rodear(pos(3 if es2 else .25),yy[4],'RT')
    mover(pos(a if es2 else b),4,pos(3 if es2 else .25),5)
    marca(pos(3 if es2 else .25),yy[5],True,cancelado=True)
    permanece(0 if es2 else xinf,4,5)
    rodear(xinf if es2 else 0,yy[6],'RT')
    mover(0 if es2 else xinf,6,xinf if es2 else 0,7)
    marca(xinf if es2 else 0,yy[7],True,cancelado=True)
    ax.plot([-1.15,13.15],[(yy[0]+yy[1])/2]*2,color='#aaa',lw=.7,ls='--')
    fig.subplots_adjust(left=.03,right=.99,top=.99,bottom=.01)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    cajas = [artista.get_window_extent(renderer) for artista in
             list(ax.texts)+list(ax.lines)+list(ax.patches)]
    cajas = [c for c in cajas if all(math.isfinite(v) for v in c.extents)]
    recorte = Bbox.union(cajas).transformed(fig.dpi_scale_trans.inverted()).padded(.035)
    fig.savefig(IM/f'TS9_mapa_remociones_{numero}.png',dpi=180,facecolor='white',
                bbox_inches=recorte)
    plt.close(fig)


for i in (1,2,3): mapa(i)

cells=[]
def md(text): cells.append(nbf.v4.new_markdown_cell(text.strip()))
def code(text): cells.append(nbf.v4.new_code_cell(text.strip()))
def imagen(nombre, alt, ancho=900):
    return f'<div align="center">\n    <img src="./Imagenes/{nombre}" alt="{alt}" width="{ancho}" />\n</div>'

md(r'''
<div align="right">
    <img src="./Imagenes/logo_UTN.svg" alt="Logo de la UTN" width="150" />
</div>

#### Teoría de los Circuitos II
# Trabajo Semanal 9
#### Alumno: Lucas Gallero
#### Profesor: Mariano Llamedo Soria
#### Ayudante de TPs: David Moharos
----
''')
md(r'''
# Enunciado

Se pide sintetizar cuadripolos pasivos sin pérdidas que cumplan las siguientes transferencias simplemente cargadas:

### 1) Transferencia de tensión con generador real y salida abierta

$$T_1(s)=\frac{V_2}{V_g}=k\frac{s(s^2+1/16)}{s^3+2s^2+2s+1},\qquad I_2=0.$$

El generador de tensión tiene una resistencia serie $R_g$. Se pide hallar la red LC, sus componentes y el valor de $k$ que resulta de la síntesis.

### 2) Transimpedancia con carga en la salida

$$T_2(s)=\frac{V_2}{I_1}=k\frac{s^2+9}{s^3+2s^2+2s+1}.$$

La entrada se excita con un generador ideal de corriente y la salida se carga con $R_L$. Se pide hallar la red LC, sus componentes y el valor de $k$.

### 3) Transimpedancia con generador real y salida abierta

$$T_3(s)=\frac{V_2}{I_g}=k\frac{s(s^2+1/16)}{s^3+2s^2+2s+1},\qquad I_2=0.$$

El generador de corriente tiene una resistencia $R_g$ en paralelo. Se pide sintetizar la red y fijar $k$ para obtener $-6\;\mathrm{dB}$ en la banda de paso.

En los tres casos se verifican las transferencias y las funciones de excitación con PyTC2 y LTspice. Las corrientes de puerto se definen entrando al cuadripolo.
''')
code(r'''
from pathlib import Path
import sys
import sympy as sp
import numpy as np
import matplotlib.pyplot as plt
from IPython.display import display, Math, IFrame
from pytc2.general import s, print_latex, a_equal_b_latex_s
from pytc2.remociones import remover_polo_dc, remover_polo_infinito, remover_polo_jw
from pytc2.cuadripolos import TabcdZ_s, TabcdY_s

%matplotlib inline
sp.init_printing()
plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':11, 'figure.dpi':100})
BASE = Path.cwd()
sys.path.insert(0, str(BASE/'Simulaciones'))
from verificar_ts9 import cargar_ejercicio, cargar_parametros, verificar, verificar_parametros

Q = s**3+2*s**2+2*s+1
P = s*(s**2+sp.Rational(1,16))

def mostrar(nombre, expresion):
    print_latex(a_equal_b_latex_s(nombre, sp.factor(expresion)))

def verificar_cero(expresion):
    assert sp.cancel(expresion) == 0

def componentes(lista):
    for nombre, valor, unidad in lista:
        print(f'{nombre}: {sp.sstr(valor)} = {float(valor):.10g} {unidad}')

def matriz_pi(ya, zt, yc):
    yb = 1/zt
    Y = sp.Matrix([[ya+yb,-yb],[-yb,yc+yb]])
    return Y.inv().applyfunc(sp.factor)

def comparar_transferencia(numero, funcion):
    f, simulada, _ = cargar_ejercicio(numero)
    teorica = np.asarray(sp.lambdify(s, funcion, 'numpy')(2j*np.pi*f))
    resumen = verificar(numero)
    print(f'Puntos comparados: {resumen["puntos"]}')
    print(f'Error absoluto máximo: {resumen["error_absoluto_maximo"]:.3e}')
    print(f'Error relativo máximo fuera del nulo: {resumen["error_relativo_maximo_fuera_del_nulo"]:.3e}')
    print(f'Cero teórico: {resumen["frecuencia_cero_teorica_hz"]:.10g} Hz')
    print(f'Mínimo del barrido: {resumen["frecuencia_minimo_barrido_hz"]:.10g} Hz')
    print(f'Nivel a {f[-1]:g} Hz: {resumen["modulo_alta_db"]:.9f} dB')
    fig, ax = plt.subplots(2,1,figsize=(11,6),sharex=True,constrained_layout=True)
    for h, etiqueta, estilo in [(teorica,'Función teórica','-'),(simulada,'LTspice','--')]:
        ax[0].semilogx(f,20*np.log10(np.maximum(abs(h),1e-16)),estilo,label=etiqueta)
        ax[1].semilogx(f,np.angle(h,deg=True),estilo)
    ax[0].set_title(f'Ejercicio {numero} - Transferencia teórica y simulada')
    ax[0].set_ylabel('Módulo (dB)' if numero==1 else 'Módulo (dB ref. 1 Ω)')
    ax[1].set_ylabel('Fase principal (°)'); ax[1].set_xlabel('Frecuencia (Hz)')
    for a in ax:
        a.grid(True,which='both',alpha=.3)
        a.axvline(resumen['frecuencia_cero_teorica_hz'],color='gray',ls=':',lw=1)
    ax[0].legend(); plt.show()
    return resumen

def comparar_parametros(numero, excitacion, transferencia):
    f, exc_lt, trans_lt = cargar_parametros(numero)
    evaluacion = lambda h: np.asarray(sp.lambdify(s,h,'numpy')(2j*np.pi*f))
    nombre = 'Z22' if numero==2 else 'Z11'
    fig, ax = plt.subplots(2,1,figsize=(11,6),sharex=True,constrained_layout=True)
    for eje, fun, lt, etiqueta in [(ax[0],excitacion,exc_lt,nombre),(ax[1],transferencia,trans_lt,'Z21')]:
        eje.semilogx(f,20*np.log10(np.maximum(abs(evaluacion(fun)),1e-16)),label='Función teórica')
        eje.semilogx(f,20*np.log10(np.maximum(abs(lt),1e-16)),'--',label='LTspice')
        eje.set_ylabel(etiqueta+' (dB ref. 1 Ω)'); eje.grid(True,which='both',alpha=.3); eje.legend()
    ax[0].set_title(f'Ejercicio {numero} - Parámetros del cuadripolo sin la resistencia externa')
    ax[1].set_xlabel('Frecuencia (Hz)'); plt.show()
    resumen = verificar_parametros(numero)
    print('Error normalizado de excitación:', f'{resumen["error_normalizado_excitacion"]:.3e}')
    print('Error normalizado de transferencia:', f'{resumen["error_normalizado_parametro_transferencia"]:.3e}')
    return resumen
''')
md(r'''
---
# <ins>Resolución</ins>

## <ins>Criterio de síntesis y normalización</ins>

Se adopta $R_g=1\;\Omega$ en los ejercicios 1 y 3, y $R_L=1\;\Omega$ en el ejercicio 2. Los componentes se expresan para una norma de frecuencia $\Omega_0=1\;\mathrm{rad/s}$. Para otras normas: $L=R_0L_n/\Omega_0$ y $C=C_n/(R_0\Omega_0)$.

El denominador común se separa en parte par e impar:

$$Q(s)=M(s)+N(s),\qquad M(s)=2s^2+1,\qquad N(s)=s(s^2+2).$$

Se escribe la transferencia como $F_T/(1+F_E)$, eligiendo la división que deje un parámetro transferencia impar. Si el numerador prescrito es impar se divide por $M$; si es par, por $N$.

Los mapas muestran el semieje $j\omega$ positivo. Los puntos finitos no nulos tienen sus conjugados en el semieje negativo. Los círculos verdes son ceros y las cruces rojas, polos; RP y RT indican remoción parcial y total. Los círculos verdes discontinuos señalan cancelaciones, no ceros que permanezcan en el resto.
''')
md(r'''
## <ins>1. Transferencia de tensión con salida abierta</ins>

### <ins>Relación entre la transferencia y los parámetros Z</ins>

Con $I_2=0$:

$$V_1=Z_{11}I_1,\qquad V_2=Z_{21}I_1,\qquad V_g=(R_g+Z_{11})I_1.$$

$$\boxed{T_1=\frac{Z_{21}}{R_g+Z_{11}}}.$$

Para $R_g=1$, se divide por la parte par de $Q$:

$$T_1=\frac{\displaystyle k\frac{s(s^2+1/16)}{2s^2+1}}
{\displaystyle 1+\frac{s(s^2+2)}{2s^2+1}}.$$

$$\boxed{Z_{11}=\frac{s(s^2+2)}{2s^2+1}},\qquad
Z_{21}=k\frac{s(s^2+1/16)}{2s^2+1}.$$
''')
code(r'''
Rg1 = sp.Integer(1)
Z11_1 = s*(s**2+2)/(2*s**2+1)
Z21_base1 = P/(2*s**2+1)
mostrar('Z_{11}', Z11_1)
mostrar('Z_{21}/k', Z21_base1)
verificar_cero(Z21_base1/(1+Z11_1)-P/Q)
''')
md(r'''
### <ins>Primera remoción: inductor L1 en derivación</ins>

Se invierte la impedancia:

$$Y_{11}=\frac{2s^2+1}{s(s^2+2)}.$$

Para obtener el cero de transmisión en $\omega_z=1/4$, se remueve parcialmente el polo en el origen. El coeficiente se calcula evaluando en $s^2=-1/16$:

$$K_0=\left.sY_{11}\right|_{s^2=-1/16}
=\frac{1-2/16}{2-1/16}=\frac{14}{31}.$$

$$Y_{L_1}=\frac{K_0}{s}=\frac1{sL_1}
\quad\Longrightarrow\quad\boxed{L_1=\frac{31}{14}\;\mathrm H}.$$

$$Y_2=Y_{11}-\frac{14}{31s}
=\boxed{\frac{48}{31}\frac{s^2+1/16}{s(s^2+2)}}.$$
''')
code(r'''
Y11_1 = sp.cancel(1/Z11_1)
Y2_1, YL1_1 = remover_polo_dc(Y11_1, omega_zero=sp.Rational(1,4))
L1_1 = sp.cancel(1/(s*YL1_1))
Z2_1 = sp.cancel(1/Y2_1)
mostrar('Y_{L_1}', YL1_1)
mostrar('Y_2', Y2_1)
mostrar('Z_2', Z2_1)
verificar_cero(Y11_1-YL1_1-Y2_1)
verificar_cero(Y2_1.subs(s,sp.I/4))
''')
md(r'''
### <ins>Segunda remoción: tanque LC paralelo en serie</ins>

Al invertir $Y_2$ aparece el polo que se necesita remover:

$$Z_2=\frac{31}{48}\frac{s(s^2+2)}{s^2+1/16}.$$

Se extrae el término $Z_t=A_ts/(s^2+1/16)$, con

$$A_t=\left.\frac{s^2+1/16}{s}Z_2\right|_{s^2=-1/16}
=\frac{31}{48}\left(2-\frac1{16}\right)=\frac{961}{768}.$$

Un tanque LC paralelo tiene $Z_t=(1/C_2)s/[s^2+1/(L_2C_2)]$. Por comparación:

$$\boxed{C_2=\frac{768}{961}\;\mathrm F},\qquad
\boxed{L_2=\frac{961}{48}\;\mathrm H}.$$

### <ins>Tercera remoción: inductor de cierre</ins>

$$Z_4=Z_2-Z_t=\frac{31}{48}s,\qquad Y_4=\frac{48}{31s}.$$

La remoción total del polo en el origen de $Y_4$ deja $Y_6=0$:

$$\boxed{L_3=\frac{31}{48}\;\mathrm H}.$$

$L_3$ pertenece al cuadripolo y se conserva aunque la salida esté abierta.
''')
code(r'''
Z4_1, Zt_1, L2_1, C2_1 = remover_polo_jw(Z2_1, omega=sp.Rational(1,4), isImpedance=True)
Y4_1 = sp.cancel(1/Z4_1)
Y6_1, YL3_1 = remover_polo_dc(Y4_1)
L3_1 = sp.cancel(1/(s*YL3_1))
mostrar('Z_t', Zt_1)
mostrar('Z_4', Z4_1)
mostrar('Y_6', Y6_1)
componentes([('L1',L1_1,'H'),('L2',L2_1,'H'),('C2',C2_1,'F'),('L3',L3_1,'H')])
verificar_cero(Y6_1)
assert L2_1*C2_1 == 16
''')
md('### <ins>Mapa de remociones</ins>\n\n'+imagen('TS9_mapa_remociones_1.png','Mapa de remociones del ejercicio 1',750))
md(r'''
### <ins>Cálculo de k desde el circuito sintetizado</ins>

Con $I_2=0$, la corriente de la rama del tanque se obtiene por divisor de corriente. Así:

$$Z_{21,\mathrm{red}}=\frac{V_2}{I_1}
=\frac{(sL_1)(sL_3)}{sL_1+Z_t+sL_3}
=\frac{s(s^2+1/16)}{2s^2+1}.$$

Al compararlo con el parámetro prescrito se obtiene $\boxed{k_1=1}$.

También se comprueba a alta frecuencia: el capacitor puentea el tanque y las derivaciones inductivas presentan impedancia creciente; la corriente por $R_g$ tiende a cero y $V_2/V_g\to1$.
''')
code(r'''
Z21_red1 = sp.cancel((s*L1_1)*(s*L3_1)/(s*L1_1+Zt_1+s*L3_1))
k1 = sp.cancel(Z21_red1/Z21_base1)
Z_red1 = matriz_pi(1/(s*L1_1),Zt_1,1/(s*L3_1))
T1 = sp.cancel(Z_red1[1,0]/(Rg1+Z_red1[0,0]))
M1 = TabcdZ_s(Rg1)*TabcdY_s(1/(s*L1_1))*TabcdZ_s(Zt_1)*TabcdY_s(1/(s*L3_1))
mostrar('k_1', k1)
mostrar('T_1', T1)
verificar_cero(Z_red1[0,0]-Z11_1)
verificar_cero(Z_red1[1,0]-Z21_red1)
verificar_cero(T1-P/Q)
verificar_cero(1/M1[0,0]-T1)
assert all(x>0 for x in [L1_1,L2_1,C2_1,L3_1])
''')
md('### <ins>Circuito obtenido</ins>\n\n'+imagen('circuito_punto_1.png','Circuito LC del ejercicio 1',1000)+r'''

### <ins>Puntos de verificación</ins>

$$T_1(0)=0,\qquad T_1(j/4)=0,\qquad T_1(\infty)=1.$$

$Z_{11}$ tiene polos en $0{,}707107\;\mathrm{rad/s}$ e infinito, y ceros en el origen y $\sqrt2\;\mathrm{rad/s}$. $Z_{21}$ tiene los mismos polos, con ceros en el origen y $1/4\;\mathrm{rad/s}$. Los polos de la función de excitación pertenecen al cuadripolo sin la resistencia externa; no son los polos de la transferencia cargada.
''')
code(r'''
mostrar('T_1(0)', sp.limit(T1,s,0))
mostrar('T_1(j/4)', sp.simplify(T1.subs(s,sp.I/4)))
mostrar(r'T_1(\infty)', sp.limit(T1,s,sp.oo))
assert sp.limit(T1,s,0)==0 and sp.limit(T1,s,sp.oo)==1
''')
md(r'''
### <ins>Verificación en LTspice</ins>

El esquema [Ejercicio1.asc](Simulaciones/Ejercicio1.asc) usa $V_g=1$ en AC. Se mide `V(V2)/V(Vg)`; el archivo `.plt` deja esa traza preparada. El barrido va de $10^{-4}$ a $10^3\;\mathrm{Hz}$, con 1000 puntos por década. El cero está en $f_z=1/(8\pi)=0{,}039788736\;\mathrm{Hz}$.

LTspice no admite el lazo de inductores completamente ideales en el punto de operación. Se usa una resistencia serie de $1\;\mathrm{n}\Omega$ únicamente en $L_1$; los demás inductores tienen `Rser=0`. La síntesis simbólica se mantiene ideal. El error numérico medido permite comprobar el efecto de esta resistencia.

Un barrido logarítmico no necesariamente incluye la frecuencia exacta del cero: el mínimo de las muestras es finito, mientras que el nulo de la función ideal es exacto.
''')
code(r'''
resultado1 = comparar_transferencia(1,T1)
''')
md(r'''
Para verificar los parámetros se retira $R_g$ y se mantiene la salida abierta. En [Ejercicio1_parametros.cir](Simulaciones/Ejercicio1_parametros.cir), una corriente de prueba entra al puerto 1:

$$Z_{11}=V(\mathrm{pin})/I(\mathrm{Iprueba}),\qquad
Z_{21}=V(\mathrm{pout})/I(\mathrm{Iprueba}).$$
''')
code(r'''
parametros1 = comparar_parametros(1,Z11_1,Z21_red1)
''')
md(r'''
---
## <ins>2. Transimpedancia con carga en la salida</ins>

### <ins>Relación entre la transferencia y los parámetros Z</ins>

$$V_2=Z_{21}I_1+Z_{22}I_2,\qquad I_2=-V_2/R_L.$$

$$V_2\left(1+\frac{Z_{22}}{R_L}\right)=Z_{21}I_1
\quad\Longrightarrow\quad
\boxed{T_2=\frac{Z_{21}}{1+Z_{22}/R_L}}.$$

Con $R_L=1$ y numerador par, se divide por $N=s(s^2+2)$:

$$\boxed{Z_{22}=\frac{2s^2+1}{s(s^2+2)}},\qquad
Z_{21}=k\frac{s^2+9}{s(s^2+2)}.$$

La síntesis se realiza desde el puerto 2 hacia el puerto 1. La condición para medir $Z_{22}$ es $I_1=0$: la entrada queda abierta y $R_L$ se retira.
''')
code(r'''
RL2 = sp.Integer(1)
Z22_2 = (2*s**2+1)/(s*(s**2+2))
Z21_base2 = (s**2+9)/(s*(s**2+2))
mostrar('Z_{22}', Z22_2)
mostrar('Z_{21}/k', Z21_base2)
''')
md(r'''
### <ins>Primera remoción: capacitor C1 en la salida</ins>

$$Y_{22}=\frac{s(s^2+2)}{2s^2+1}.$$

Se remueve parcialmente el polo en infinito para crear un cero en $\omega_z=3$:

$$C_1=\left.\frac{Y_{22}}s\right|_{s^2=-9}
=\frac{-9+2}{2(-9)+1}=\boxed{\frac7{17}\;\mathrm F}.$$

$$Y_2=Y_{22}-\frac7{17}s
=\boxed{\frac{3s(s^2+9)}{17(2s^2+1)}}.$$

### <ins>Segunda remoción: tanque LC paralelo</ins>

$$Z_2=\frac1{Y_2}=\frac{17(2s^2+1)}{3s(s^2+9)}.$$

$$A_t=\left.\frac{s^2+9}{s}Z_2\right|_{s^2=-9}
=\left.\frac{17(2s^2+1)}{3s^2}\right|_{s^2=-9}=\frac{289}{27}.$$

$$Z_t=\frac{289}{27}\frac{s}{s^2+9},\qquad
\boxed{C_2=\frac{27}{289}\;\mathrm F},\qquad
\boxed{L_2=\frac{289}{243}\;\mathrm H}.$$

### <ins>Tercera remoción: capacitor de cierre en la entrada</ins>

$$Z_4=Z_2-Z_t=\frac{17}{27s},\qquad Y_4=\frac{27}{17}s.$$

La remoción total del polo en infinito de $Y_4$ deja $Y_6=0$ y da:

$$\boxed{C_3=\frac{27}{17}\;\mathrm F}.$$
''')
code(r'''
Y22_2 = sp.cancel(1/Z22_2)
Y2_2, YC1_2 = remover_polo_infinito(Y22_2,omega_zero=3)
C1_2 = sp.cancel(YC1_2/s)
Z2_2 = sp.cancel(1/Y2_2)
Z4_2, Zt_2, L2_2, C2_2 = remover_polo_jw(Z2_2,omega=3,isImpedance=True)
Y4_2 = sp.cancel(1/Z4_2)
Y6_2, YC3_2 = remover_polo_infinito(Y4_2)
C3_2 = sp.cancel(YC3_2/s)
for nombre,expresion in [('Y_2',Y2_2),('Z_2',Z2_2),('Z_t',Zt_2),('Z_4',Z4_2),('Y_6',Y6_2)]:
    mostrar(nombre,expresion)
componentes([('C1 (salida)',C1_2,'F'),('L2',L2_2,'H'),('C2',C2_2,'F'),('C3 (entrada)',C3_2,'F')])
verificar_cero(Y22_2-YC1_2-Y2_2)
verificar_cero(Z2_2-Zt_2-Z4_2)
verificar_cero(Y6_2)
assert L2_2*C2_2 == sp.Rational(1,9)
''')
md('### <ins>Mapa de remociones</ins>\n\n'+imagen('TS9_mapa_remociones_2.png','Mapa de remociones del ejercicio 2',750))
md(r'''
### <ins>Cálculo de k desde el circuito</ins>

Retirando $R_L$ y dejando la salida abierta:

$$Z_{21,\mathrm{red}}=\frac{Z_{C_3}Z_{C_1}}{Z_{C_3}+Z_t+Z_{C_1}}
=\frac{s^2+9}{9s(s^2+2)}.$$

La comparación con el parámetro prescrito da $\boxed{k_2=1/9}$.

Con la carga conectada, también se puede calcular en continua: los capacitores abren y el inductor une ambos puertos. Toda la corriente circula por $R_L=1$, por lo que $T_2(0)=1=9k_2$.
''')
code(r'''
ZCentrada2 = 1/(s*C3_2)
ZCsalida2 = 1/(s*C1_2)
Z21_red2 = sp.cancel(ZCentrada2*ZCsalida2/(ZCentrada2+Zt_2+ZCsalida2))
k2 = sp.cancel(Z21_red2/Z21_base2)
Z_red2 = matriz_pi(s*C3_2,Zt_2,s*C1_2)
T2 = sp.cancel(Z_red2[1,0]/(1+Z_red2[1,1]/RL2))
M2 = TabcdY_s(s*C3_2)*TabcdZ_s(Zt_2)*TabcdY_s(s*C1_2+1/RL2)
mostrar('k_2',k2)
mostrar('T_2',T2)
verificar_cero(Z_red2[1,1]-Z22_2)
verificar_cero(Z_red2[1,0]-Z21_red2)
verificar_cero(T2-(s**2+9)/(9*Q))
verificar_cero(1/M2[1,0]-T2)
assert all(x>0 for x in [C1_2,L2_2,C2_2,C3_2])
''')
md('### <ins>Circuito obtenido</ins>\n\n'+imagen('circuito_punto_2.png','Circuito LC del ejercicio 2',1100)+r'''

La numeración sigue el orden de extracción: $C_1=7/17$ queda en la salida y $C_3=27/17$ en la entrada. Esta ubicación es necesaria para conservar el $Z_{22}$ prescrito; intercambiarlos mantiene $Z_{21}$ por reciprocidad, pero modifica $Z_{22}$ y la transferencia cargada.

### <ins>Puntos de verificación</ins>

$$T_2(0)=1,\qquad T_2(j3)=0,\qquad T_2(\infty)=0.$$

$Z_{22}$ tiene polos en el origen y $\sqrt2\;\mathrm{rad/s}$, y ceros en $1/\sqrt2\;\mathrm{rad/s}$ e infinito. $Z_{21}$ conserva esos polos y tiene ceros en $3\;\mathrm{rad/s}$ e infinito.
''')
code(r'''
mostrar('T_2(0)',sp.limit(T2,s,0))
mostrar('T_2(j3)',sp.simplify(T2.subs(s,3*sp.I)))
mostrar(r'T_2(\infty)',sp.limit(T2,s,sp.oo))
assert sp.limit(T2,s,0)==1 and sp.limit(T2,s,sp.oo)==0
''')
md(r'''
### <ins>Verificación en LTspice</ins>

El esquema [Ejercicio2.asc](Simulaciones/Ejercicio2.asc) tiene el generador de corriente con amplitud AC unitaria y $R_L=1$. Se mide `V(V2)/I(I1)`. El inductor tiene `Rser=0`.

El cero de transmisión está en $f_z=3/(2\pi)=0{,}477464829\;\mathrm{Hz}$. En baja frecuencia la transimpedancia tiende a $1\;\Omega$, equivalente a $0\;\mathrm{dB}$ respecto de $1\;\Omega$. A alta frecuencia cae con pendiente asintótica de $-20\;\mathrm{dB/década}$.
''')
code(r'''
resultado2 = comparar_transferencia(2,T2)
''')
md(r'''
En [Ejercicio2_parametros.cir](Simulaciones/Ejercicio2_parametros.cir) se retira $R_L$ y se mantiene la entrada abierta. Se aplica una tensión de prueba en el puerto 2. La corriente que entra al cuadripolo es `-I(Vprueba)`:

$$Z_{22}=\frac{V(\mathrm{pout})}{-I(\mathrm{Vprueba})},\qquad
Z_{12}=\frac{V(\mathrm{pin})}{-I(\mathrm{Vprueba})}=Z_{21}.$$

La última igualdad corresponde a la reciprocidad de la red LC.
''')
code(r'''
parametros2 = comparar_parametros(2,Z22_2,Z21_red2)
''')
md(r'''
---
## <ins>3. Transimpedancia con generador real de corriente</ins>

### <ins>Relación entre la transferencia y los parámetros Z</ins>

Con la salida abierta, $Z_{11}$ es la impedancia conectada en paralelo con $R_g$. Por divisor de corriente:

$$I_1=I_g\frac{R_g}{R_g+Z_{11}},\qquad V_2=Z_{21}I_1.$$

$$\boxed{T_3=\frac{V_2}{I_g}=\frac{Z_{21}}{1+Z_{11}/R_g}}.$$

Para $R_g=1$ se obtienen las mismas funciones de excitación y transferencia base del ejercicio 1:

$$Z_{11}=\frac{s(s^2+2)}{2s^2+1},\qquad
Z_{21}=k\frac{s(s^2+1/16)}{2s^2+1}.$$

### <ins>Remociones y cierre equivalente</ins>

Se repite la remoción parcial de $14/(31s)$ de $Y_{11}$, la inversión y la remoción total del tanque en $\omega=1/4$. El resto es $Z_4=(31/48)s$:

$$L_1=\frac{31}{14},\qquad L_2=\frac{961}{48},\qquad
C_2=\frac{768}{961},\qquad L_{3,\mathrm{eq}}=\frac{31}{48}.$$
''')
code(r'''
Rg3 = sp.Integer(1)
Z11_3 = s*(s**2+2)/(2*s**2+1)
Y2_3, YL1_3 = remover_polo_dc(1/Z11_3,omega_zero=sp.Rational(1,4))
Z4_3, Zt_3, L2_3, C2_3 = remover_polo_jw(1/Y2_3,omega=sp.Rational(1,4),isImpedance=True)
L1_3 = sp.cancel(1/(s*YL1_3))
Leq3 = sp.cancel(Z4_3/s)
verificar_cero(Z11_3-Z11_1)
mostrar('L_{3,eq}',Leq3)
''')
md('### <ins>Mapa de remociones</ins>\n\n'+imagen('TS9_mapa_remociones_3.png','Mapa de remociones del ejercicio 3',750))
md(r'''
### <ins>Ajuste de k con un divisor inductivo de salida</ins>

Se divide el cierre en dos inductores independientes en serie, conservando la suma:

$$L_{3A}+L_{3B}=L_{3,\mathrm{eq}}=\frac{31}{48}.$$

Se llama $V_b$ a la tensión sobre el conjunto y se toma la salida $V_2$ sobre $L_{3B}$. Como $I_2=0$, la corriente es la misma en ambos:

$$\frac{V_2}{V_b}=\frac{sL_{3B}}{sL_{3A}+sL_{3B}}
=\frac{L_{3B}}{L_{3A}+L_{3B}}=\alpha.$$

El cierre conserva su impedancia total y, por lo tanto, no cambia $Z_{11}$.

Para obtener la transferencia hasta $V_b$, se plantea:

$$V_1=V_b\left(1+\frac{Z_t}{sL_{3,\mathrm{eq}}}\right)
=V_b\frac{s^2+2}{s^2+1/16}.$$

La corriente del generador es la suma de las corrientes por $R_g$, $L_1$ y la rama derecha:

$$I_g=V_1+\frac{14V_1}{31s}+\frac{48V_b}{31s}.$$

Reemplazando $V_1$ y agrupando:

$$I_g=V_b\frac{(31s+14)(s^2+2)+48(s^2+1/16)}{31s(s^2+1/16)}
=V_b\frac{Q(s)}{s(s^2+1/16)}.$$

$$\frac{V_b}{I_g}=\frac{s(s^2+1/16)}{Q(s)},\qquad
\boxed{\frac{V_2}{I_g}=\alpha\frac{s(s^2+1/16)}{Q(s)}}.$$

Por comparación, $k=\alpha$ para la normalización elegida.

### <ins>Condición de −6 dB y valores del cierre</ins>

Se toma la meseta de alta frecuencia como nivel de la banda de paso. La transimpedancia se expresa en dB respecto de $1\;\Omega$:

$$20\log_{10}\left(\frac{|T_3(j\omega)|}{1\;\Omega}\right)\longrightarrow-6\;\mathrm{dB}.$$

Como $T_3(\infty)=k$, en valores normalizados:

$$\boxed{k_3=10^{-6/20}\approx0{,}5011872336}.$$

Las dos condiciones del cierre permiten despejar los componentes:

$$k_3=\frac{L_{3B}}{L_{3A}+L_{3B}}=\frac{L_{3B}}{31/48}
\quad\Longrightarrow\quad
\boxed{L_{3B}=k_3\frac{31}{48}}.$$

$$\boxed{L_{3A}=\frac{31}{48}-L_{3B}=(1-k_3)\frac{31}{48}}.$$
''')
code(r'''
k3 = sp.Pow(10,-sp.Rational(3,10))
L3A = sp.simplify((1-k3)*Leq3)
L3B = sp.simplify(k3*Leq3)
componentes([('L1',L1_3,'H'),('L2',L2_3,'H'),('C2',C2_3,'F'),('L3A',L3A,'H'),('L3B',L3B,'H')])
mostrar('L_{3A}+L_{3B}',sp.simplify(L3A+L3B))
mostrar('k_3',k3)
print('Nivel de banda de paso:',20*np.log10(float(k3)),'dB ref. 1 Ω')
assert sp.simplify(L3A+L3B-Leq3)==0
assert sp.simplify(L3B/(L3A+L3B)-k3)==0
''')
md('### <ins>Circuito obtenido</ins>\n\n'+imagen('circuito_punto_3.png','Circuito del ejercicio 3 con divisor inductivo',1100)+r'''

En el dibujo, $\alpha=k_3$. Los valores son $L_{3A}\approx0{,}3221499116\;\mathrm H$ y $L_{3B}\approx0{,}3236834217\;\mathrm H$. Se conserva el valor exacto de $k_3$ en los cálculos y en los parámetros de LTspice.

### <ins>Verificación simbólica por parámetros ABCD</ins>

Se construye primero el cuadripolo LC sin $R_g$. Luego se agrega la resistencia de generador como admitancia en derivación. Con $I_2=0$, el parámetro $C$ de la cascada total cumple $I_g=C V_2$ y la transimpedancia es $1/C$.
''')
code(r'''
MLC3 = TabcdY_s(1/(s*L1_3))*TabcdZ_s(Zt_3+s*L3A)*TabcdY_s(1/(s*L3B))
Z11_red3 = sp.cancel(MLC3[0,0]/MLC3[1,0])
Z21_red3 = sp.cancel(1/MLC3[1,0])
M3 = TabcdY_s(1/Rg3)*MLC3
T3 = sp.cancel(1/M3[1,0])
verificar_cero(Z11_red3-Z11_3)
verificar_cero(Z21_red3-k3*P/(2*s**2+1))
verificar_cero(T3-k3*P/Q)
assert all(float(x)>0 for x in [L1_3,L2_3,C2_3,L3A,L3B])
mostrar('T_3(s)',T3)
mostrar('T_3(0)',sp.limit(T3,s,0))
mostrar('T_3(j/4)',sp.simplify(T3.subs(s,sp.I/4)))
mostrar(r'T_3(\infty)',sp.limit(T3,s,sp.oo))
''')
md(r'''
### <ins>Verificación en LTspice</ins>

En [Ejercicio3.asc](Simulaciones/Ejercicio3.asc) se mide `V(V2)/I(Ig)`. El generador tiene amplitud AC unitaria. La expresión de parámetros es:

```spice
.param K=10**(-6/20) La=(1-K)*31/48 Lb=K*31/48
```

Los inductores se cargan con `{La}` y `{Lb}`. $L_1$ usa `Rser=1n` para resolver el punto de operación; el tanque y los dos inductores del divisor tienen `Rser=0`.

Se verifican el nulo en $f_z=0{,}039788736\;\mathrm{Hz}$, el nivel de alta frecuencia de $-6\;\mathrm{dB}$ y la relación constante $V_2/V_b=k_3$.
''')
code(r'''
resultado3 = comparar_transferencia(3,T3)
f3, _, datos3 = cargar_ejercicio(3)
relacion3 = datos3['v(v2)']/datos3['v(vb)']
error_divisor = np.max(np.abs(relacion3-float(k3)))
print('Error máximo del divisor V2/Vb:',f'{error_divisor:.3e}')
assert error_divisor < 1e-8
assert abs(resultado3['modulo_alta_db']+6)<1e-5
''')
md(r'''
En [Ejercicio3_parametros.cir](Simulaciones/Ejercicio3_parametros.cir) se retira $R_g$ y se deja la salida abierta. La corriente de prueba verifica $Z_{11}$ y $Z_{21}$ del cuadripolo con el divisor incluido. La impedancia de entrada coincide con la del ejercicio 1 y el parámetro transferencia queda multiplicado por $k_3$.
''')
code(r'''
parametros3 = comparar_parametros(3,Z11_3,Z21_red3)
''')
md(r'''
---
## <ins>Archivos de simulación y resultados</ins>

Los esquemas `Ejercicio1.asc`, `Ejercicio2.asc` y `Ejercicio3.asc` conservan los dibujos preparados para cada circuito. Cada uno tiene su configuración `.plt`, el barrido AC y las mediciones de baja frecuencia, alta frecuencia y nulo de transmisión. Los archivos `EjercicioN_parametros.cir` verifican las condiciones de medición del cuadripolo sin la resistencia externa.

Para repetir las seis simulaciones y la comparación numérica se ejecuta, desde la carpeta del trabajo:

```python
import subprocess, sys
subprocess.run([sys.executable, 'Simulaciones/verificar_ts9.py', '--simular'], check=True)
```

Las celdas de este notebook leen los resultados `.raw` incluidos en `Simulaciones`; no vuelven a abrir LTspice al ejecutarse. El archivo `verificacion_resultados.json` guarda los errores y las frecuencias verificadas.

| Ejercicio | Escala de la transferencia | Nulo finito | Comportamiento de alta frecuencia |
|---|---|---|---|
| 1 | $k_1=1$ | $\omega=1/4$ | $T_1\to1$ |
| 2 | $k_2=1/9$ | $\omega=3$ | $T_2\to0$ |
| 3 | $k_3=10^{-6/20}$ | $\omega=1/4$ | $T_3\to k_3$, nivel $-6\;\mathrm{dB}$ |

## <ins>Referencias</ins>

- Mariano Llamedo Soria, [Síntesis de redes no disipativas simplemente cargadas](https://pytc2.readthedocs.io/en/latest/notebooks/ejnb_funciones_transf_simplemente_cargadas.html).
- Clases y Cosas de Mariano, [Síntesis de redes no disipativas, simplemente cargadas](https://youtu.be/PYGjVKhuDNQ).

---
# <ins>Resolución manuscrita</ins>

El desarrollo original se conserva en el documento siguiente. En el esquema del ejercicio 2 se corrigió la ubicación de los capacitores de los extremos de acuerdo con la síntesis desde el puerto de salida.
''')
code(r'''
IFrame('Imagenes/TS9.pdf',width=1000,height=700)
''')

nb = nbf.v4.new_notebook(cells=cells)
nb.metadata.update(kernelspec={'display_name':'Python 3 (ipykernel)','language':'python','name':'python3'},
                   language_info={'name':'python','version':'3.12.10','file_extension':'.py',
                                  'mimetype':'text/x-python','pygments_lexer':'ipython3','nbconvert_exporter':'python'})
nbf.validate(nb)
nbf.write(nb,BASE/'trabajo_semanal_9.ipynb')
print(f'Notebook creado: {len(cells)} celdas, {sum(c.cell_type=="code" for c in cells)} de código.')
