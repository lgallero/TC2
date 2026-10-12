from pathlib import Path
from io import BytesIO
import json
import shutil
import sys

import nbformat as nbf
import sympy as sp
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
import schemdraw
import schemdraw.elements as elm

sys.stdout.reconfigure(encoding='utf-8')
BASE = Path(__file__).resolve().parents[1]
IMG = BASE / 'Imagenes'
SIM = BASE / 'Simulacion'
IMG.mkdir(exist_ok=True)
SIM.mkdir(exist_ok=True)
source = Path(r'C:\Users\Lucas\AppData\Local\Temp\codex-clipboard-f317363d-d95f-406b-a086-0acc05abbcd1.png')
shutil.copy2(source, IMG / 'Enunciado_TS8.png')
im = Image.open(source)
im.crop((90, 207, 619, 358)).save(IMG / 'Enunciado1.png')
im.crop((132, 765, 573, 1005)).save(IMG / 'Enunciado2.png')

schemdraw.use('matplotlib')
schemdraw.config(color='black', bgcolor='white', fontsize=12)

def guardar_circuito(d, nombre):
    fig = d.draw(show=False).getfig()
    fig.savefig(IMG / nombre, dpi=170, bbox_inches='tight', pad_inches=.2, facecolor='white')
    plt.close(fig)

d = schemdraw.Drawing(unit=3)
d += elm.Dot().at((0, 0))
d += elm.Line().right().length(1.2)
d += elm.Capacitor().down().length(3)
d += elm.Line().left().length(1.2)
d += elm.Dot()
d += elm.Line().at((1.2, 0)).right().length(2.4)
d += elm.Resistor().down().length(3)
d += elm.Line().at((3.6, 0)).right().length(1)
d += elm.Resistor().right().length(3).label('$R_2=0{,}00603748\\,\\Omega$')
d += elm.Inductor().right().length(3).label('$L_1=1/24\\,\\mathrm{H}$')
d += elm.Capacitor().down().length(3)
d += elm.Line().at((10.6, 0)).right().length(2.8)
d += elm.Resistor().down().length(3)
d += elm.Line().left().length(12.2)
for pos,label in [((-.15,-1.5),'$C_1$\n$1\\,\\mathrm{F}$'),
                  ((5.1,-1.5),'$R_1$\n$0{,}223334\\,\\Omega$'),
                  ((9.1,-1.5),'$C_2$\n$27{,}39425\\,\\mathrm{F}$'),
                  ((15.0,-1.5),'$R_3$\n$0{,}0426897\\,\\Omega$')]:
    d += elm.Label().at(pos).label(label)
guardar_circuito(d, 'TS8_circuito_1.png')

d = schemdraw.Drawing(unit=3)
d += elm.Dot().at((0, 0))
d += elm.Resistor().right().length(3).label('$Z_1=3/8\\,\\Omega$')
d += elm.Dot()
d += elm.Resistor().down().length(2)
d += elm.Capacitor().down().length(2)
d += elm.Resistor().at((3, 0)).right().length(4).label('$Z_2=105/104\\,\\Omega$')
d += elm.Dot()
d += elm.Resistor().down().length(2)
d += elm.Capacitor().down().length(2)
d += elm.Resistor().at((7, 0)).right().length(4).label('$Z_3=50/39\\,\\Omega$')
d += elm.Line().down().length(4)
d += elm.Line().left().length(11)
d += elm.Dot()
for pos,label in [((1.5,-1),'$R_1$\n$35/32\\,\\Omega$'),
                  ((1.5,-3),'$C_1$\n$32/175\\,\\mathrm{F}$'),
                  ((8.7,-1),'$R_2$\n$350/507\\,\\Omega$'),
                  ((8.7,-3),'$C_2$\n$507/1400\\,\\mathrm{F}$')]:
    d += elm.Label().at(pos).label(label)
guardar_circuito(d, 'TS8_circuito_2.png')

# Mapa del manuscrito: el eje muestra sigma >= 0, donde s = -sigma.
rows = [
    ('Z', [1, 3], [2, 4], r'$8/3$', r'$1$'),
    ('Z_2', [1, 3], [sp.Rational(11,5), 5], r'$55/24$', r'$5/8$'),
    ('Y_2', [sp.Rational(11,5), 5], [1, 3], r'$24/55$', r'$8/5$'),
    ('Y_4', [sp.Rational(11,5)], [sp.Rational(7,5)], r'$24/55$', r'$24/35$'),
    ('Z_4', [sp.Rational(7,5)], [sp.Rational(11,5)], r'$55/24$', r'$35/24$'),
    ('Z_6', [sp.Rational(7,5)], [4], r'$50/39$', r'$35/78$'),
    ('Y_6', [4], [sp.Rational(7,5)], r'$39/50$', r'$78/35$'),
    ('Y_8', [], [], r'$39/50$', r'$39/50$'),
    ('Z_8', [], [], r'$50/39$', r'$50/39$'),
]
fig, axes = plt.subplots(9, 1, figsize=(9, 12.5), sharex=True)
fig.subplots_adjust(top=.9, bottom=.08, hspace=.8, left=.13, right=.9)
fig.suptitle('Ejercicio 2 - Mapa de remociones sucesivas', fontsize=16, y=.965)
fig.text(.13, .93, '× Polos    ○ Ceros    Flechas: desplazamiento de ceros', fontsize=11)
actions = {0:'RP de resistencia: cero en -5', 2:'RT de rama RC: polo en -5',
           4:'RP de resistencia: cero en -4', 6:'RT de rama RC: polo en -4'}
for i,(name, poles, zeros, dc, inf) in enumerate(rows):
    ax = axes[i]
    ax.axhline(0, color='#64748b', lw=1)
    ax.set_ylim(-.6,.85)
    ax.set_xlim(-.1,5.7)
    for p in poles:
        ax.plot(float(p),0,'x',ms=10,mew=2,color='#c2410c')
        ax.text(float(p),-.22,str(p),ha='center',va='top',fontsize=10)
    for z in zeros:
        ax.plot(float(z),0,'o',ms=10,mew=2,mfc='white',color='#047857')
        ax.text(float(z),-.22,str(z),ha='center',va='top',fontsize=10)
    ax.text(-.075,.4,'$'+name+'$',transform=ax.transAxes,fontsize=13,ha='right')
    ax.text(-.04,.98,'DC: '+dc,transform=ax.transAxes,fontsize=9)
    ax.text(1.01,.4,r'$\infty$:'+'\n'+inf,transform=ax.transAxes,fontsize=10)
    ax.set_yticks([])
    ax.spines[['top','left','right','bottom']].set_visible(False)
    if i<8:
        ax.tick_params(bottom=False,labelbottom=False)
    if i in actions:
        ax.text(.48,.73,actions[i],transform=ax.transAxes,fontsize=9,color='#334155')
    if i==1:
        for old,new in [(2,2.2),(4,5)]:
            ax.annotate('',(new,.19),(old,.65),arrowprops=dict(arrowstyle='->',color='#047857',connectionstyle='arc3,rad=.2'))
    if i==3:
        ax.annotate('',(1.4,.19),(1,.65),arrowprops=dict(arrowstyle='->',color='#047857'))
        ax.annotate('',(5,.19),(3,.65),arrowprops=dict(arrowstyle='->',color='#047857',connectionstyle='arc3,rad=.2'))
        ax.plot(5,0,'o',ms=18,mfc='none',mec='#64748b',ls='--')
        ax.text(5,-.38,'cancelación',ha='center',fontsize=8)
    if i==5:
        ax.annotate('',(4,.19),(2.2,.65),arrowprops=dict(arrowstyle='->',color='#047857',connectionstyle='arc3,rad=.2'))
    if i==7:
        ax.annotate('',(4,.19),(1.4,.65),arrowprops=dict(arrowstyle='->',color='#047857',connectionstyle='arc3,rad=.2'))
        ax.plot(4,0,'o',ms=18,mfc='none',mec='#64748b')
        ax.text(4,-.38,'cancelación',ha='center',fontsize=8)
axes[-1].set_xlabel(r'Semieje real negativo: $s=-\sigma$, con $\sigma\geq0$ ($\mathrm{s}^{-1}$)',fontsize=11)
fig.savefig(IMG/'TS8_mapa_remociones_2.png',dpi=150,facecolor='white')
plt.close(fig)

# Circuito preparado para ejecutar una simulación independiente del ejercicio 1.
h = -10*np.cos(np.deg2rad(116.6))
sigma = (25-h)/24
q = 1-sigma+sigma**2
values = {'C1':1, 'R1':1/h, 'R2':(1-sigma)/24, 'L1':1/24,
          'C2':24/q, 'R3':q/(24*sigma)}
lines = ['TS8 - Ejercicio 1 - K=1', 'V1 in 0 AC 1',
         f"C1 in 0 {values['C1']:.16g}",f"R1 in 0 {values['R1']:.16g}",
         f"R2 in n1 {values['R2']:.16g}",f"L1 n1 out {values['L1']:.16g} Rser=0",
         f"C2 out 0 {values['C2']:.16g}",f"R3 out 0 {values['R3']:.16g}",
         '.ac dec 1000 0.001 100',
         '.meas AC z_baja FIND mag(V(in)/(-I(V1))) AT=0.001',
         '.meas AC z_alta FIND mag(V(in)/(-I(V1))) AT=100',
         '* Impedancia de entrada: V(in)/(-I(V1))', '.end']
(SIM/'Ejercicio 1.cir').write_text('\n'.join(lines)+'\n',encoding='ascii')

nb = nbf.v4.new_notebook()
nb.metadata = {'kernelspec':{'display_name':'Python 3 (ipykernel)','language':'python','name':'python3'},
               'language_info':{'name':'python','version':'3.12.10','file_extension':'.py','mimetype':'text/x-python','pygments_lexer':'ipython3'}}
cells=[]
def md(t): cells.append(nbf.v4.new_markdown_cell(t.strip()))
def code(t): cells.append(nbf.v4.new_code_cell(t.strip()))
def picture(name,alt,width=700):
    return f'<div align="center">\n<img src="./Imagenes/{name}" alt="{alt}" width="{width}" style="max-width:100%; height:auto;" />\n</div>'

md('''<img src="./Imagenes/logo_UTN.svg" align="right" width="150" />

#### Teoría de los Circuitos II
# Trabajo Semanal 8
#### Alumno: Lucas Gallero
#### Profesor: Mariano Llamedo Soria
#### Ayudante de TPs: David Moharos
----''')
md(r'''# Enunciado

### 1) Síntesis de un dipolo RLC

Dada una función impedancia $Z(s)$, se sabe que la pulsación libre de amortiguamiento y el coeficiente de amortiguamiento asociados a sus ceros son $1\;\mathrm{rad/s}$ y $0{,}5\;\mathrm{s^{-1}}$. Posee polos en $s=-1$ y $s=5e^{j116{,}6^\circ}$.

Determine el valor de los componentes del siguiente dipolo, sabiendo que satisface la impedancia propuesta.

'''+picture('Enunciado1.png','Dipolo del ejercicio 1',550)+r'''

### 2) Síntesis de un dipolo RC con constantes de tiempo dadas

Encuentre los elementos del siguiente dipolo, caracterizado por:

$$R_1C_1=\frac15\;\mathrm{s},\qquad R_2C_2=\frac14\;\mathrm{s},$$

$$Z(s)=\frac{s^2+6s+8}{s^2+4s+3}.$$

'''+picture('Enunciado2.png','Dipolo del ejercicio 2',500)+r'''

En ambos ejercicios se pide verificar mediante simulación simbólica en Python con PyTC2 y simulación circuital en LTspice, utilizando cursores para verificar las singularidades.

[Enunciado original](Imagenes/Enunciado_TS8.png)''')
code('''import sympy as sp
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import re
from IPython.display import display, Math, Image, IFrame
from pytc2.general import s, print_latex, a_equal_b_latex_s
from pytc2.remociones import (
    remover_polo_infinito,
    remover_valor_en_infinito,
    remover_polo_sigma,
)

%matplotlib inline
sp.init_printing()
plt.rcParams.update({'font.size': 11, 'figure.dpi': 100})

def mostrar(nombre, expresion):
    # Los valores se calculan sin redondear; solo se abrevia su presentación.
    if any(max(abs(r.p),abs(r.q))>10**6 for r in expresion.atoms(sp.Rational)):
        num, den = sp.fraction(sp.cancel(expresion))
        escala = sp.Poly(den,s).LC()
        num = sp.N(num/escala,7)
        den = sp.N(den/escala,7)
        vista = num if den.equals(1) else sp.Mul(num,sp.Pow(den,-1,evaluate=False),evaluate=False)
        display(Math(nombre+r'\\approx '+sp.latex(vista)))
    else:
        print_latex(a_equal_b_latex_s(nombre, sp.factor(expresion)))

def tabla_componentes(componentes):
    for nombre, valor, unidad in componentes:
        exacto = f'{sp.sstr(valor)} = ' if all(abs(r.q)<10**6 for r in valor.atoms(sp.Rational)) else ''
        print(f'{nombre}: {exacto}{float(valor):.9g} {unidad}')

def verificar_cero(expresion):
    assert sp.cancel(expresion) == 0

def bode(funcion, titulo, limites=(1e-3, 1e2)):
    f = np.logspace(np.log10(limites[0]), np.log10(limites[1]), 3000)
    z = sp.lambdify(s, funcion, 'numpy')(2j*np.pi*f)
    fig, ax = plt.subplots(2, 1, figsize=(11, 6), sharex=True, constrained_layout=True)
    ax[0].semilogx(f, 20*np.log10(np.abs(z)))
    ax[0].set_ylabel('Módulo de Z (dB ref. 1 Ω)')
    ax[0].set_title(titulo)
    ax[1].semilogx(f, np.angle(z, deg=True))
    ax[1].set_ylabel('Fase de Z (°)')
    ax[1].set_xlabel('Frecuencia (Hz)')
    for eje in ax:
        eje.grid(True, which='both', alpha=.3)
    plt.show()
''')
md(r'''---
# <ins>Resolución</ins>

## <ins>1. Síntesis del dipolo RLC</ins>

Se sigue el orden del desarrollo manuscrito: capacitor en derivación, resistencia en derivación, inductancia serie, resistencia serie y paralelo RC final. Se conserva la numeración de los remanentes $Y_2$, $Y_4$, $Z_4$, $Z_6$ y $Z_8$.

El capacitor final se llama $C_2$, como en el enunciado; en el manuscrito aparece también identificado como $C_3$.

### <ins>Ceros, polos y función impedancia con K=1</ins>

Con $\omega_0=1$ y $\alpha=0{,}5$, los ceros son:

$$z_{1,2}=-\alpha\pm j\sqrt{\omega_0^2-\alpha^2}
=-\frac12\pm j\frac{\sqrt3}{2}.$$

Su polinomio es:

$$N(s)=s^2+2\alpha s+\omega_0^2=s^2+s+1.$$

El polo complejo se pasa a forma rectangular:

$$p_{2,3}=5\cos116{,}6^\circ\pm j\,5\sin116{,}6^\circ
\approx-2{,}238795\pm j\,4{,}470771.$$

Se incluye el conjugado porque el circuito tiene coeficientes reales. Junto con $p_1=-1$:

$$D(s)=(s+1)(s^2+hs+25),\qquad h=-10\cos116{,}6^\circ\approx4{,}477590878.$$

Los polos y ceros no fijan por sí solos la escala de impedancia. Se adopta **$K=1$**, igual que en el manuscrito:

$$\boxed{Z(s)=\frac{s^2+s+1}{(s+1)(s^2+hs+25)}}.$$

$$Z(s)\approx\frac{s^2+s+1}{s^3+5{,}477590878s^2+29{,}477590878s+25}.$$

En las remociones se conserva $h$ sin redondearlo a tres decimales. Esto evita acumular diferencias en los componentes.''')
code('''omega0 = sp.Integer(1)
alpha = sp.Rational(1, 2)
angulo = sp.Rational(583, 5)*sp.pi/180
h_angular = -10*sp.cos(angulo)
# Se conserva el coeficiente angular con 16 cifras y se opera con racionales.
h = sp.Rational(str(sp.N(h_angular, 16)))
Z_ej1 = (s**2+s+1)/((s+1)*(s**2+h*s+25))
mostrar('Z(s)', Z_ej1)
ceros_ej1 = [-alpha-sp.I*sp.sqrt(omega0**2-alpha**2),
             -alpha+sp.I*sp.sqrt(omega0**2-alpha**2)]
polos_ej1 = [sp.Integer(-1), 5*sp.exp(sp.I*angulo), 5*sp.exp(-sp.I*angulo)]
print('Ceros:', [complex(sp.N(z)) for z in ceros_ej1])
print('Polos:', [complex(sp.N(p)) for p in polos_ej1])
print('h =', float(h))
''')
md(r'''### <ins>Cómo se interpretan las remociones</ins>

Una remoción resta el aporte de un elemento de la función de entrada. Para elementos en paralelo se trabaja con admitancia; para elementos en serie, con impedancia.

| Elemento | Término removido | Función utilizada |
|---|---|---|
| Capacitor en derivación | $sC$ | $Y$ |
| Resistor en derivación | $1/R$ | $Y$ |
| Inductor serie | $sL$ | $Z$ |
| Resistor serie | $R$ | $Z$ |
| Paralelo RC en serie con el resto | $k/(s+\sigma)$ | $Z$ |

La red completa es RLC. Las primeras extracciones son remociones en infinito; el último paralelo se obtiene con una remoción Foster RC de polo real.

### <ins>Primera remoción: capacitor C1 en derivación</ins>

Se invierte la impedancia porque $C_1$ está en paralelo con la entrada:

$$Y(s)=\frac1{Z(s)}=\frac{s^3+(h+1)s^2+(h+25)s+25}{s^2+s+1}.$$

La remoción del polo en infinito da:

$$C_1=\lim_{s\to\infty}\frac{Y(s)}s=1\;\mathrm{F}.$$

Se resta $Y_{C_1}=s$:

$$\begin{aligned}
Y_2&=Y-s\\
&=\frac{s^3+(h+1)s^2+(h+25)s+25-s(s^2+s+1)}{s^2+s+1}\\
&=\boxed{\frac{hs^2+(h+24)s+25}{s^2+s+1}}.
\end{aligned}$$''')
code('''Y_ej1 = sp.cancel(1/Z_ej1)
Y2_ej1, Y_C1 = remover_polo_infinito(Y_ej1)
C1_ej1 = sp.simplify(Y_C1/s)
mostrar('Y_{C_1}(s)', Y_C1)
mostrar('Y_2(s)', Y2_ej1)
mostrar('C_1', C1_ej1)
verificar_cero(Y_ej1-Y_C1-Y2_ej1)
''')
md(r'''### <ins>Segunda remoción: resistencia R1 en derivación</ins>

Después de remover $C_1$, a alta frecuencia la inductancia abre la rama derecha. Queda la conductancia de $R_1$:

$$G_1=\frac1{R_1}=\lim_{s\to\infty}Y_2(s)=h.$$

$$\boxed{R_1=\frac1h\approx0{,}223334\;\Omega}.$$

Se remueve el valor constante:

$$\begin{aligned}
Y_4&=Y_2-h\\
&=\frac{hs^2+(h+24)s+25-h(s^2+s+1)}{s^2+s+1}\\
&=\boxed{\frac{24s+25-h}{s^2+s+1}}.
\end{aligned}$$

Solo queda la rama $R_2+L_1+(R_3\parallel C_2)$. Se invierte su admitancia para extraer los elementos serie:

$$\boxed{Z_4=\frac1{Y_4}=\frac{s^2+s+1}{24s+25-h}}.$$

Para simplificar las siguientes cuentas se define:

$$\sigma=\frac{25-h}{24}\approx0{,}855100380,
\qquad Z_4=\frac{s^2+s+1}{24(s+\sigma)}.$$''')
code('''Y4_ej1, G1_ej1 = remover_valor_en_infinito(Y2_ej1)
R1_ej1 = sp.simplify(1/G1_ej1)
Z4_ej1 = sp.cancel(1/Y4_ej1)
sigma_ej1 = sp.simplify((25-h)/24)
mostrar('G_1', G1_ej1)
mostrar('Y_4(s)', Y4_ej1)
mostrar('Z_4(s)', Z4_ej1)
tabla_componentes([('R1', R1_ej1, 'Ω')])
verificar_cero(Y2_ej1-G1_ej1-Y4_ej1)
''')
md(r'''### <ins>Tercera remoción: inductancia L1 serie</ins>

La remoción del polo en infinito de la impedancia permite extraer $sL_1$:

$$L_1=\lim_{s\to\infty}\frac{Z_4(s)}s
=\lim_{s\to\infty}\frac{s^2+s+1}{24s(s+\sigma)}
=\boxed{\frac1{24}\;\mathrm{H}}.$$

$$\begin{aligned}
Z_6&=Z_4-\frac{s}{24}\\
&=\frac{s^2+s+1-s(s+\sigma)}{24(s+\sigma)}\\
&=\boxed{\frac{(1-\sigma)s+1}{24(s+\sigma)}}.
\end{aligned}$$

### <ins>Cuarta remoción: resistencia R2 serie</ins>

A alta frecuencia el capacitor de salida cortocircuita su paralelo. Por lo tanto:

$$R_2=\lim_{s\to\infty}Z_6(s)
=\frac{1-\sigma}{24}
\approx\boxed{0{,}00603748\;\Omega}.$$

$$\begin{aligned}
Z_8&=Z_6-R_2\\
&=\frac{(1-\sigma)s+1-(1-\sigma)(s+\sigma)}{24(s+\sigma)}\\
&=\boxed{\frac{1-\sigma+\sigma^2}{24(s+\sigma)}}.
\end{aligned}$$

Los dos términos extraídos forman el bloque RL serie $Z_{RL}=R_2+sL_1$.''')
code('''Z6_ej1, Z_L1 = remover_polo_infinito(Z4_ej1)
L1_ej1 = sp.simplify(Z_L1/s)
Z8_ej1, R2_ej1 = remover_valor_en_infinito(Z6_ej1)
mostrar('Z_{L_1}(s)', Z_L1)
mostrar('Z_6(s)', Z6_ej1)
mostrar('Z_8(s)', Z8_ej1)
tabla_componentes([('L1', L1_ej1, 'H'), ('R2', R2_ej1, 'Ω')])
verificar_cero(Z4_ej1-Z_L1-Z6_ej1)
verificar_cero(Z6_ej1-R2_ej1-Z8_ej1)
''')
md(r'''### <ins>Quinta remoción: Foster RC del paralelo final</ins>

El remanente tiene un único polo real en $s=-\sigma$:

$$Z_8(s)=\frac{k_\sigma}{s+\sigma},\qquad
k_\sigma=\lim_{s\to-\sigma}(s+\sigma)Z_8(s)
=\frac{1-\sigma+\sigma^2}{24}\approx0{,}03650401166.$$

$k_\sigma$ es el residuo de esta remoción; no es la constante $K=1$ fijada al construir $Z(s)$.

La impedancia de un paralelo RC es:

$$Z_{R_3\parallel C_2}
=\frac1{sC_2+1/R_3}
=\frac{1/C_2}{s+1/(R_3C_2)}.$$

Comparando con la forma Foster:

$$\frac1{C_2}=k_\sigma,\qquad\frac1{R_3C_2}=\sigma.$$

$$\boxed{C_2=\frac1{k_\sigma}\approx27{,}39424941\;\mathrm{F}},
\qquad
\boxed{R_3=\frac{k_\sigma}{\sigma}\approx0{,}04268973856\;\Omega}.$$

Al remover todo el paralelo, $Z_{10}=Z_8-k_\sigma/(s+\sigma)=0$.

En PyTC2 se utiliza `isImpedance=True, isRC=True`: el término removido es una **impedancia RC** que se conecta en serie con el resto.''')
code('''Z10_ej1, Z_RC_final, R3_ej1, C2_ej1 = remover_polo_sigma(
    Z8_ej1, sigma=sigma_ej1, isImpedance=True, isRC=True
)
k_sigma_ej1 = sp.simplify((1-sigma_ej1+sigma_ej1**2)/24)
print('sigma =', float(sigma_ej1), 's^-1')
print('k_sigma =', float(k_sigma_ej1))
tabla_componentes([('R3', R3_ej1, 'Ω'), ('C2', C2_ej1, 'F')])
mostrar('Z_{10}(s)', Z10_ej1)
verificar_cero(Z10_ej1)
verificar_cero(Z_RC_final-1/(s*C2_ej1+1/R3_ej1))
''')
md(r'''### <ins>Componentes y circuito obtenido</ins>

| Componente | Valor | Conexión |
|---|---:|---|
| $C_1$ | $1\;\mathrm{F}$ | Derivación en la entrada |
| $R_1$ | $0{,}223334\;\Omega$ | Derivación en la entrada |
| $R_2$ | $0{,}00603748\;\Omega$ | Serie |
| $L_1$ | $1/24\;\mathrm{H}$ | Serie |
| $C_2$ | $27{,}39424941\;\mathrm{F}$ | Paralelo final |
| $R_3$ | $0{,}04268973856\;\Omega$ | Paralelo final |

'''+picture('TS8_circuito_1.png','Circuito obtenido para K igual a 1',1000)+r'''

### <ins>Reconstrucción y verificación simbólica</ins>

Se reconstruye desde el paralelo de salida hacia la entrada:

$$Z_{\mathrm{salida}}=\frac1{sC_2+1/R_3},\qquad
Z_{\mathrm{rama}}=R_2+sL_1+Z_{\mathrm{salida}}.$$

$$Y_{\mathrm{red}}=sC_1+\frac1{R_1}+\frac1{Z_{\mathrm{rama}}},
\qquad Z_{\mathrm{red}}=\frac1{Y_{\mathrm{red}}}.$$

La diferencia entre la función reconstruida y la propuesta debe ser idénticamente cero.''')
code('''Z_salida_ej1 = 1/(s*C2_ej1+1/R3_ej1)
Z_rama_ej1 = R2_ej1+s*L1_ej1+Z_salida_ej1
Z_red_ej1 = sp.cancel(1/(s*C1_ej1+1/R1_ej1+1/Z_rama_ej1))
diferencia_ej1 = sp.cancel(Z_red_ej1-Z_ej1)
mostrar('Z_{red}(s)-Z(s)', diferencia_ej1)
verificar_cero(diferencia_ej1)
assert all(float(x)>0 for x in [C1_ej1,R1_ej1,R2_ej1,L1_ej1,C2_ej1,R3_ej1])
''')
md(r'''### <ins>Comportamiento en baja y alta frecuencia</ins>

En DC, los capacitores quedan abiertos y la inductancia en cortocircuito:

$$Z(0)=R_1\parallel(R_2+R_3)=\frac1{25}=0{,}04\;\Omega.$$

A alta frecuencia, el capacitor de entrada domina:

$$Z(s)\sim\frac1{sC_1}=\frac1s.$$

El módulo tiende a $-20\;\mathrm{dB/década}$ y la fase a $-90^\circ$. En baja frecuencia el módulo tiende a $20\log_{10}(0{,}04)=-27{,}9588\;\mathrm{dB}$ y la fase a $0^\circ$.

Los ceros y polos complejos están en el semiplano izquierdo, fuera del eje $j\omega$. Por eso no producen nulos exactos ni divergencias en el barrido AC.''')
code('''Z_dc_ej1 = sp.simplify(R1_ej1*(R2_ej1+R3_ej1)/(R1_ej1+R2_ej1+R3_ej1))
mostrar('Z(0)', Z_dc_ej1)
assert Z_dc_ej1 == sp.Rational(1,25)
bode(Z_ej1, 'Ejercicio 1 - Impedancia teórica, K=1')
''')
md(r'''### <ins>Simulación en LTspice</ins>

El circuito para el barrido AC está en [Ejercicio 1.cir](Simulacion/Ejercicio%201.cir). La impedancia se obtiene con `V(in)/(-I(V1))`; el signo negativo toma la corriente que entra al dipolo. Se fija `Rser=0` en la inductancia para simular el componente ideal del enunciado.

**Verificación numérica del barrido**

Se compara la respuesta de LTspice con la función calculada. Las curvas de Python que aparecen en esta comparación usan datos del archivo `.raw`.

**Captura del circuito en LTspice**

<div style="height:80px"></div>

**Lecturas manuales de cursores**

| Zona | $f_1$ (Hz) | $f_2$ (Hz) | $M_1$ (dB) | $M_2$ (dB) | Pendiente (dB/década) |
|---|---|---|---|---|---|
| Baja frecuencia | | | | | |
| Alta frecuencia | | | | | |

$$m=\frac{M_2-M_1}{\log_{10}(f_2/f_1)}.$$

Los campos de lectura y la captura se dejan en blanco porque no se dispone de esas mediciones manuales.''')
code('''def leer_raw_ac(path):
    datos = Path(path).read_bytes()
    marca = 'Binary:\\n'.encode('utf-16-le')
    inicio = datos.index(marca)+len(marca)
    cabecera = datos[:inicio].decode('utf-16-le')
    if 'complex' not in cabecera or 'FastAccess' in cabecera:
        raise ValueError('Se requiere un archivo AC binario normal de LTspice.')
    nvars = int(re.search(r'No\\. Variables:\\s*(\\d+)', cabecera).group(1))
    npoints = int(re.search(r'No\\. Points:\\s*(\\d+)', cabecera).group(1))
    nombres = re.findall(r'^\\s*\\d+\\s+(\\S+)\\s+\\S+\\s*$', cabecera, re.M)
    matriz = np.frombuffer(datos, dtype='<c16', offset=inicio, count=npoints*nvars).reshape(npoints,nvars)
    return {nombre:matriz[:,i] for i,nombre in enumerate(nombres)}

def comparar_ltspice(path, funcion, titulo):
    datos = leer_raw_ac(path)
    f = np.real(datos['frequency'])
    z_lt = datos['V(in)']/(-datos['I(V1)'])
    z_teo = sp.lambdify(s,funcion,'numpy')(2j*np.pi*f)
    error = np.max(np.abs(z_lt-z_teo))
    error_rel = np.max(np.abs((z_lt-z_teo)/z_teo))
    print(f'Puntos comparados: {len(f)}')
    print(f'Error absoluto máximo: {error:.3e} Ω')
    print(f'Error relativo máximo: {error_rel:.3e}')
    print(f'Z a {f[0]:g} Hz: {abs(z_lt[0]):.9g} Ω')
    print(f'Z a {f[-1]:g} Hz: {abs(z_lt[-1]):.9g} Ω')
    assert error_rel < 1e-5
    fig,ax=plt.subplots(2,1,figsize=(11,6),sharex=True,constrained_layout=True)
    for z,label,style in [(z_teo,'Función teórica','-'),(z_lt,'LTspice','--')]:
        ax[0].semilogx(f,20*np.log10(np.abs(z)),style,label=label)
        ax[1].semilogx(f,np.angle(z,deg=True),style,label=label)
    ax[0].set_title(titulo)
    ax[0].set_ylabel('Módulo de Z (dB ref. 1 Ω)')
    ax[1].set_ylabel('Fase de Z (°)')
    ax[1].set_xlabel('Frecuencia (Hz)')
    for eje in ax:
        eje.grid(True,which='both',alpha=.3)
        eje.legend()
    plt.show()
    return error, error_rel

raw_ej1=Path('Simulacion/Ejercicio 1.raw')
if raw_ej1.exists():
    errores_ej1=comparar_ltspice(raw_ej1,Z_ej1,'Ejercicio 1 - Teoría y LTspice')
else:
    print('Barrido de LTspice pendiente. Ejecutar Simulacion/Ejercicio 1.cir.')
''')
md(r'''---
## <ins>2. Síntesis del dipolo RC con remociones parciales</ins>

$$Z(s)=\frac{s^2+6s+8}{s^2+4s+3}
=\frac{(s+2)(s+4)}{(s+1)(s+3)}.$$

Los polos son $-1$ y $-3$; los ceros son $-2$ y $-4$. Se intercalan sobre el eje real negativo, en el orden de una impedancia RC:

$$1\;(P)<2\;(C)<3\;(P)<4\;(C),\qquad s=-\sigma.$$

Los bloques $Z_1$, $Z_2$ y $Z_3$ se obtienen como resistencias. Las derivaciones son ramas RC **serie**.

### <ins>Qué fijan las constantes de tiempo</ins>

La admitancia de una rama RC serie es:

$$Y_{RC}(s)=\frac1{R+1/(sC)}
=\frac{(1/R)s}{s+1/(RC)}
=\frac{k s}{s+\sigma},$$

$$k=\frac1R,\qquad\sigma=\frac1{RC},\qquad C=\frac{k}{\sigma}.$$

Así, $R_1C_1=1/5$ exige un polo de admitancia en $s=-5$, y $R_2C_2=1/4$ exige otro en $s=-4$.

Para generar esos polos, primero se remueven parcialmente resistencias serie. Se elige el valor que haga cero al remanente de impedancia en la posición deseada; al invertirlo, ese cero se convierte en polo.''')
code('''Z_ej2 = (s**2+6*s+8)/(s**2+4*s+3)
mostrar('Z(s)', Z_ej2)
print('Polos:', sp.solve(sp.denom(Z_ej2),s))
print('Ceros:', sp.solve(sp.numer(Z_ej2),s))
''')
md(r'''### <ins>Primera remoción parcial: resistencia Z1</ins>

La primera derivación debe tener un polo en $-5$. Se requiere que $Z-Z_1$ tenga allí un cero:

$$[Z(s)-Z_1]_{s=-5}=0\quad\Longrightarrow\quad Z_1=Z(-5).$$

$$Z_1=\frac{(-5+2)(-5+4)}{(-5+1)(-5+3)}
=\frac{3}{8}\;\Omega.$$

Se llama remoción parcial porque no se extrae todo el valor en infinito: $Z(\infty)=1$, pero se remueve $3/8$.

$$\begin{aligned}
Z_2&=Z-\frac38\\
&=\frac{8(s^2+6s+8)-3(s^2+4s+3)}{8(s^2+4s+3)}\\
&=\frac{5s^2+36s+55}{8(s+1)(s+3)}\\
&=\boxed{\frac58\frac{(s+11/5)(s+5)}{(s+1)(s+3)}}.
\end{aligned}$$

Al invertir:

$$\boxed{Y_2=\frac85\frac{(s+1)(s+3)}{(s+11/5)(s+5)}}.$$

La remoción desplazó los ceros de $-2$ y $-4$ a $-11/5$ y $-5$.''')
code('''Z2_ej2, Z1_bloque = remover_valor_en_infinito(Z_ej2, sigma_zero=5)
Y2_ej2 = sp.cancel(1/Z2_ej2)
mostrar('Z_1', Z1_bloque)
mostrar('Z_2(s)', Z2_ej2)
mostrar('Y_2(s)', Y2_ej2)
assert Z1_bloque == sp.Rational(3,8)
verificar_cero(Z2_ej2.subs(s,-5))
''')
md(r'''### <ins>Segunda remoción: Foster RC de la primera rama serie</ins>

Como la rama está en derivación, se remueve su **admitancia**:

$$Y_{R_1+C_1}(s)=\frac{k_1s}{s+5}.$$

Su coeficiente se obtiene cancelando el polo:

$$\begin{aligned}
k_1&=\lim_{s\to-5}\frac{s+5}{s}Y_2(s)\\
&=\left.\frac85\frac{(s+1)(s+3)}{s(s+11/5)}\right|_{s=-5}\\
&=\frac85\frac{(-4)(-2)}{(-5)(-14/5)}
=\frac{32}{35}.
\end{aligned}$$

De $k_1=1/R_1$ y $C_1=k_1/5$:

$$\boxed{R_1=\frac{35}{32}\;\Omega},\qquad
\boxed{C_1=\frac{32}{175}\;\mathrm{F}}.$$

La constante de tiempo verifica:

$$R_1C_1=\frac{35}{32}\frac{32}{175}=\frac15\;\mathrm{s}.$$

Se resta la rama:

$$\begin{aligned}
Y_4&=Y_2-\frac{32}{35}\frac{s}{s+5}\\
&=\frac{\frac85(s+1)(s+3)-\frac{32}{35}s(s+11/5)}{(s+11/5)(s+5)}\\
&=\frac{\frac{24}{35}(s+7/5)(s+5)}{(s+11/5)(s+5)}\\
&=\boxed{\frac{24}{35}\frac{s+7/5}{s+11/5}}.
\end{aligned}$$

El factor $s+5$ se cancela: la remoción del polo es total. Se invierte para continuar con el siguiente bloque serie:

$$\boxed{Z_4=\frac{35}{24}\frac{s+11/5}{s+7/5}}.$$

En PyTC2: `isImpedance=False, isRC=True`, porque se remueve la admitancia de una rama RC serie.''')
code('''Y4_ej2, Y_RC1_ej2, R1_ej2, C1_ej2 = remover_polo_sigma(
    Y2_ej2, sigma=5, isImpedance=False, isRC=True
)
Z4_ej2 = sp.cancel(1/Y4_ej2)
mostrar('Y_{R_1+C_1}(s)', Y_RC1_ej2)
mostrar('Y_4(s)', Y4_ej2)
mostrar('Z_4(s)', Z4_ej2)
tabla_componentes([('R1',R1_ej2,'Ω'),('C1',C1_ej2,'F')])
assert R1_ej2*C1_ej2 == sp.Rational(1,5)
verificar_cero(Y_RC1_ej2-1/(R1_ej2+1/(s*C1_ej2)))
''')
md(r'''### <ins>Tercera remoción parcial: resistencia Z2</ins>

La segunda rama exige un polo de admitancia en $-4$. Se elige la resistencia serie que genere un cero de impedancia allí:

$$Z_2\text{ (bloque)}=Z_4(-4)
=\frac{35}{24}\frac{-4+11/5}{-4+7/5}
=\frac{35}{24}\frac9{13}
=\boxed{\frac{105}{104}\;\Omega}.$$

El bloque $Z_2$ del dibujo es una resistencia; no debe confundirse con el remanente $Z_2(s)$ del primer paso.

$$\begin{aligned}
Z_6&=Z_4-\frac{105}{104}\\
&=\frac{\frac{35}{24}(s+11/5)-\frac{105}{104}(s+7/5)}{s+7/5}\\
&=\boxed{\frac{35}{78}\frac{s+4}{s+7/5}}.
\end{aligned}$$

Se invierte:

$$\boxed{Y_6=\frac{78}{35}\frac{s+7/5}{s+4}}.$$

El polo en $-4$ ya está disponible para remover la segunda rama RC.''')
code(r'''Z6_ej2, Z2_bloque = remover_valor_en_infinito(Z4_ej2, sigma_zero=4)
Y6_ej2 = sp.cancel(1/Z6_ej2)
mostrar('Z_2\mathrm{\ (bloque)}', Z2_bloque)
mostrar('Z_6(s)', Z6_ej2)
mostrar('Y_6(s)', Y6_ej2)
assert Z2_bloque == sp.Rational(105,104)
verificar_cero(Z6_ej2.subs(s,-4))
''')
md(r'''### <ins>Cuarta remoción: Foster RC de la segunda rama serie</ins>

Se remueve:

$$Y_{R_2+C_2}(s)=\frac{k_2s}{s+4}.$$

El coeficiente es:

$$\begin{aligned}
k_2&=\lim_{s\to-4}\frac{s+4}{s}Y_6(s)\\
&=\left.\frac{78}{35}\frac{s+7/5}{s}\right|_{s=-4}\\
&=\frac{78}{35}\frac{-13/5}{-4}
=\boxed{\frac{507}{350}}.
\end{aligned}$$

Por identificación:

$$\boxed{R_2=\frac{350}{507}\;\Omega},\qquad
\boxed{C_2=\frac{k_2}{4}=\frac{507}{1400}\;\mathrm{F}}.$$

Se comprueba:

$$R_2C_2=\frac{350}{507}\frac{507}{1400}=\frac14\;\mathrm{s}.$$

La resta deja una conductancia constante:

$$\begin{aligned}
Y_8&=\frac{78}{35}\frac{s+7/5}{s+4}
-\frac{507}{350}\frac{s}{s+4}\\
&=\frac{\frac{39}{50}s+\frac{78}{25}}{s+4}
=\frac{\frac{39}{50}(s+4)}{s+4}
=\boxed{\frac{39}{50}}.
\end{aligned}$$

### <ins>Quinta remoción: resistencia final Z3</ins>

Al invertir el último resto:

$$\boxed{Z_3=Z_8=\frac1{Y_8}=\frac{50}{39}\;\Omega}.$$

La extracción de esta resistencia termina la síntesis.''')
code('''Y8_ej2, Y_RC2_ej2, R2_ej2, C2_ej2 = remover_polo_sigma(
    Y6_ej2, sigma=4, isImpedance=False, isRC=True
)
Z8_ej2 = sp.cancel(1/Y8_ej2)
Z3_bloque = Z8_ej2
mostrar('Y_{R_2+C_2}(s)', Y_RC2_ej2)
mostrar('Y_8(s)', Y8_ej2)
mostrar('Z_3', Z3_bloque)
tabla_componentes([('R2',R2_ej2,'Ω'),('C2',C2_ej2,'F')])
assert R2_ej2*C2_ej2 == sp.Rational(1,4)
assert Z3_bloque == sp.Rational(50,39)
verificar_cero(Y_RC2_ej2-1/(R2_ej2+1/(s*C2_ej2)))
''')
md(r'''### <ins>Mapa de remociones</ins>

Las cruces representan polos y los círculos representan ceros. Se grafica $\sigma\geq0$, donde cada punto corresponde a $s=-\sigma$ sobre el eje real negativo. RP indica remoción parcial y RT remoción total. Los círculos grises de cancelación no son singularidades del remanente simplificado.

'''+picture('TS8_mapa_remociones_2.png','Mapa del ejercicio 2: remociones parciales y totales',750)+r'''

Las constantes DC e infinito indicadas a cada lado corresponden a cada función de esa fila. En los últimos restos solo queda un valor constante, sin polos ni ceros finitos.

### <ins>Valores de los componentes</ins>

| Componente | Valor exacto | Aproximación | Conexión |
|---|---|---:|---|
| $Z_1$ | $3/8\;\Omega$ | $0{,}375\;\Omega$ | Resistencia serie |
| $Z_2$ | $105/104\;\Omega$ | $1{,}009615\;\Omega$ | Resistencia serie |
| $Z_3$ | $50/39\;\Omega$ | $1{,}282051\;\Omega$ | Resistencia final |
| $R_1$ | $35/32\;\Omega$ | $1{,}09375\;\Omega$ | Primera rama RC serie |
| $C_1$ | $32/175\;\mathrm{F}$ | $0{,}182857\;\mathrm{F}$ | Primera rama RC serie |
| $R_2$ | $350/507\;\Omega$ | $0{,}690335\;\Omega$ | Segunda rama RC serie |
| $C_2$ | $507/1400\;\mathrm{F}$ | $0{,}362143\;\mathrm{F}$ | Segunda rama RC serie |

### <ins>Circuito obtenido</ins>

'''+picture('TS8_circuito_2.png','Circuito RC obtenido con los valores exactos',1000))
md(r'''### <ins>Reconstrucción y verificación simbólica</ins>

Desde el extremo derecho:

$$Z_{RC,1}=R_1+\frac1{sC_1},\qquad Z_{RC,2}=R_2+\frac1{sC_2}.$$

La segunda rama está en paralelo con $Z_3$:

$$Z_{\mathrm{derecha}}=\left(\frac1{Z_{RC,2}}+\frac1{Z_3}\right)^{-1}.$$

Se suma $Z_2$ y se conecta en paralelo con la primera rama:

$$Z_{\mathrm{red}}=Z_1+
\left[\frac1{Z_{RC,1}}+\frac1{Z_2+Z_{\mathrm{derecha}}}\right]^{-1}.$$

Se verifica la igualdad exacta con la función propuesta y las dos constantes de tiempo.''')
code('''Z_RC1_red = R1_ej2+1/(s*C1_ej2)
Z_RC2_red = R2_ej2+1/(s*C2_ej2)
Z_derecha = 1/(1/Z_RC2_red+1/Z3_bloque)
Z_red_ej2 = sp.cancel(Z1_bloque+1/(1/Z_RC1_red+1/(Z2_bloque+Z_derecha)))
mostrar('Z_{red}(s)', Z_red_ej2)
mostrar('Z_{red}(s)-Z(s)', sp.cancel(Z_red_ej2-Z_ej2))
verificar_cero(Z_red_ej2-Z_ej2)
mostrar('R_1C_1', R1_ej2*C1_ej2)
mostrar('R_2C_2', R2_ej2*C2_ej2)
assert all(x>0 for x in [Z1_bloque,Z2_bloque,Z3_bloque,R1_ej2,C1_ej2,R2_ej2,C2_ej2])
''')
md(r'''### <ins>Comportamiento en frecuencia</ins>

En DC, los capacitores abren las dos derivaciones. La entrada ve las tres resistencias serie:

$$Z(0)=Z_1+Z_2+Z_3=\frac38+\frac{105}{104}+\frac{50}{39}=\frac83\;\Omega.$$

A alta frecuencia, los capacitores cortocircuitan dentro de sus ramas y quedan redes resistivas:

$$Z(\infty)=Z_1+\left[R_1\parallel\left(Z_2+(R_2\parallel Z_3)\right)\right]=1\;\Omega.$$

El módulo pasa de $20\log_{10}(8/3)=8{,}5194\;\mathrm{dB}$ a $0\;\mathrm{dB}$ y la fase tiende a $0^\circ$ en ambos extremos.

Los polos y ceros son reales negativos: **las frecuencias de quiebre no son picos ni nulos del barrido AC**. Las frecuencias asociadas a los factores de primer orden son:

| Singularidad | Posición en el plano s | Frecuencia de quiebre (Hz) |
|---|---|---:|
| Polo 1 | $-1$ | $1/(2\pi)=0{,}159155$ |
| Cero 1 | $-2$ | $2/(2\pi)=0{,}318310$ |
| Polo 2 | $-3$ | $3/(2\pi)=0{,}477465$ |
| Cero 2 | $-4$ | $4/(2\pi)=0{,}636620$ |

Las pendientes asintóticas ideales por factores son $0$, $-20$, $0$, $-20$ y $0\;\mathrm{dB/década}$. Como los quiebres están próximos entre sí, los tramos intermedios no aparecen como rectas largas.''')
code(r'''mostrar('Z(0)', sp.limit(Z_ej2,s,0))
mostrar('Z(\infty)', sp.limit(Z_ej2,s,sp.oo))
assert sp.limit(Z_red_ej2,s,0)==sp.Rational(8,3)
assert sp.limit(Z_red_ej2,s,sp.oo)==1
bode(Z_ej2, 'Ejercicio 2 - Impedancia RC teórica')
''')
md(r'''### <ins>Simulación en LTspice</ins>

El circuito existente [Ejercicio 2.asc](Simulacion/Ejercicio%202.asc) utiliza los mismos valores exactos obtenidos en la síntesis. Se mide `V(in)/(-I(V1))`.

**Respuesta simulada y ubicación de singularidades**

<div align="center">
<img src="./Simulacion/Ejercicio%202%20-%20polos%20y%20ceros.png" alt="Respuesta de LTspice y polos y ceros del ejercicio 2" width="1000" style="max-width:100%; height:auto;" />
</div>

La captura disponible muestra la respuesta AC del dipolo y la ubicación teórica de polos y ceros. El archivo `.log` contiene mediciones de factores auxiliares de primer orden, incluidos en el circuito sin cargar el dipolo. Esas referencias permiten asociar cada quiebre a su factor; no representan picos de la impedancia total.

| Factor auxiliar | Frecuencia registrada (Hz) | Lectura del módulo |
|---|---:|---:|
| Polo en $-1$ | $0{,}159154943093$ | $1/\sqrt2$ |
| Cero en $-2$ | $0{,}318309886182$ | $\sqrt2$ |
| Polo en $-3$ | $0{,}477464829266$ | $1/\sqrt2$ |
| Cero en $-4$ | $0{,}636619772358$ | $\sqrt2$ |

Para un polo normalizado se verifica $-3{,}0103\;\mathrm{dB}$ en su quiebre; para un cero normalizado, $+3{,}0103\;\mathrm{dB}$. La reconstrucción del circuito se comprueba por separado comparando toda la respuesta AC con $Z(j\omega)$.

**Comparación numérica de la función y el barrido**''')
code('''raw_ej2=Path('Simulacion/Ejercicio 2.raw')
if raw_ej2.exists():
    errores_ej2=comparar_ltspice(raw_ej2,Z_ej2,'Ejercicio 2 - Teoría y LTspice')
else:
    print('El archivo de barrido del ejercicio 2 no está disponible.')
''')
md(r'''**Captura del circuito en LTspice**

<div style="height:80px"></div>

**Capturas y lecturas manuales de cursores**

| Factor | Frecuencia del cursor (Hz) | Módulo leído (dB) |
|---|---|---|
| Polo en $-1$ | | |
| Cero en $-2$ | | |
| Polo en $-3$ | | |
| Cero en $-4$ | | |

Estos espacios quedan disponibles para incorporar las capturas de LTspice y las lecturas manuales que faltan.''')
md(r'''---
# <ins>Resolución manuscrita</ins>

## <ins>TS8.pdf</ins>

El PDF original se conserva como referencia del desarrollo a mano. Las páginas 1 a 3 corresponden al ejercicio 1; las páginas 4 a 7, al ejercicio 2.

[Abrir resolución manuscrita](Imagenes/TS8.pdf)''')
code('''IFrame('Imagenes/TS8.pdf', width=1000, height=700)''')
nb.cells=cells
nbf.write(nb,BASE/'trabajo_semanal_8.ipynb')
print('Notebook creado:',len(cells),'celdas')
