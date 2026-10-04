"""TS7: verificacion simbolica con pytc2 y comparacion con los .raw de LTspice.
Instalacion: python -m pip install pytc2 matplotlib numpy
Ejecucion: python verificacion_pytc2.py
"""
from pathlib import Path
import re
import sympy as sp
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pytc2.general import s
from pytc2.sintesis_dipolo import foster, cauer_LC
from pytc2.remociones import remover_polo_dc, remover_polo_jw

BASE = Path(__file__).resolve().parent
R = sp.Rational
paralelo = lambda a, b: sp.cancel(a*b/(a+b))
F = (s**4+4*s**2+3)/(s*(s**2+2))
Y2 = (s**5+18*s**3+48*s)/(6*s**4+42*s**2+48)
redes = {
    'ejercicio1a': 1/(s*R(2,3))+s+paralelo(s/4,1/(2*s)),
    'ejercicio1b': 1/(s*R(2,3))+s+1/(2*s+4/s),
    'ejercicio1c': s+1/(s/2+1/(4*s+6/s)),
    'ejercicio1d': R(3,2)/s+1/(R(4,5)/s+1/(R(25,2)/s+5*s)),
    'ejercicio2': 1/(1/s+paralelo(s/2,paralelo(s/4,2/s)+3/s)),
}
salida = []
def registrar(texto):
    print(texto)
    salida.append(str(texto))

registrar('VERIFICACION TS7 CON PYTC2')
registrar('1b interpreta F como admitancia Y=F, como en el desarrollo manuscrito.')
for nombre, funcion in redes.items():
    objetivo = Y2 if nombre=='ejercicio2' else F
    diferencia = sp.cancel(funcion-objetivo)
    assert diferencia == 0, nombre
    registrar(f'{nombre}: funcion de la red menos funcion propuesta = {diferencia}')

k0, koo, ki, kk, F_foster = foster(F)
assert sp.cancel(F_foster-F)==0
registrar(f'Foster: k0={k0}, k_infinito={koo}, ki={ki}; F={F_foster}')
for infinito in [True, False]:
    terminos, F_cauer, remanente = cauer_LC(F, remover_en_inf=infinito)
    assert sp.cancel(F_cauer-F)==0 and remanente==0
    registrar(f'Cauer {"infinito" if infinito else "DC"}: {terminos}; remanente={remanente}')

Z2, Z_C1 = remover_polo_dc(sp.cancel(1/Y2))
Y4, Y_L1 = remover_polo_dc(sp.cancel(1/Z2))
Z4 = sp.cancel(1/Y4)
# La API exige omega numerico. Normalizar a omega=1 conserva valores exactos.
escala = sp.sqrt(8)
Z6n, Z_tanquen, L2n, C2n = remover_polo_jw(sp.cancel(Z4.subs(s, s*escala)), omega=1, isImpedance=True)
Z6 = sp.cancel(Z6n.subs(s, s/escala))
Z_tanque = sp.cancel(Z_tanquen.subs(s, s/escala))
L2, C2 = sp.simplify(L2n/escala), sp.simplify(C2n/escala)
resto, Z_C3 = remover_polo_dc(sp.cancel(Z6))
assert sp.cancel(resto)==0
for nombre, funcion in [('Z_C1',Z_C1),('Z2',Z2),('Y_L1',Y_L1),('Y4',Y4),('Z4',Z4),('Z_tanque',Z_tanque),('Z6',Z6),('Z_C3',Z_C3)]:
    registrar(f'2: {nombre}(s) = {sp.cancel(funcion)}')
registrar(f'2: C1={sp.simplify(1/(s*Z_C1))}, L1={sp.simplify(1/(s*Y_L1))}, L2={L2}, C2={C2}, C3={sp.simplify(1/(s*Z_C3))}')

def leer_raw(path):
    datos = path.read_bytes()
    marca = 'Binary:\n'.encode('utf-16-le')
    inicio = datos.index(marca)+len(marca)
    cabecera = datos[:inicio].decode('utf-16-le')
    if 'complex' not in cabecera or 'FastAccess' in cabecera:
        raise ValueError('Se espera un archivo AC binario normal de LTspice.')
    nvar = int(re.search(r'No\. Variables:\s*(\d+)',cabecera).group(1))
    npts = int(re.search(r'No\. Points:\s*(\d+)',cabecera).group(1))
    nombres = [linea.split()[1].lower() for linea in cabecera.split('Variables:\n')[1].split('Binary:')[0].splitlines() if linea.strip()]
    matriz = np.frombuffer(datos[inicio:],dtype='<c16').reshape(npts,nvar)
    return {nombre:matriz[:,i] for i,nombre in enumerate(nombres)}

fig, axes = plt.subplots(3,2,figsize=(12,9),layout='constrained')
for nombre in redes:
    path = BASE/(nombre+'.raw')
    if not path.exists():
        registrar(f'{nombre}: falta .raw; ejecutar primero el esquema en LTspice.')
        continue
    datos = leer_raw(path)
    f = datos['frequency'].real
    if nombre=='ejercicio1b': medida=datos['i(i1)']/datos['v(in)']
    elif nombre=='ejercicio2': medida=-datos['i(v1)']/datos['v(in)']
    else: medida=datos['v(in)']/(-datos['i(v1)'])
    formula = Y2 if nombre=='ejercicio2' else F
    referencia = sp.lambdify(s,formula,'numpy')(2j*np.pi*f)
    error = np.max(np.abs(medida-referencia)/np.maximum(np.abs(referencia),1e-12))
    registrar(f'{nombre}: error relativo maximo de {len(f)} puntos AC = {error:.3e}')
    assert error<1e-6, f'{nombre}: error excesivo en los datos de LTspice'
    col = 1 if nombre=='ejercicio2' else 0
    label = nombre.replace('ejercicio','')
    db = 20*np.log10(np.abs(medida))
    axes[0,col].semilogx(f,db,label=label,lw=1)
    axes[1,col].semilogx(f,np.angle(medida,deg=True),label=label,lw=1)
    pendiente = np.gradient(db,np.log10(f))
    axes[2,col].semilogx(f,pendiente,label=label,lw=1)
for col in [0,1]:
    axes[0,col].set_title('Ejercicio 1: Z en 1a/1c/1d; Y en 1b' if col==0 else 'Ejercicio 2: admitancia Y')
    for fila, ylabel in enumerate(['Modulo (dB ref. 1 ohm o 1 S)','Fase (grados)','Pendiente (dB/decada)']):
        axes[fila,col].set_ylabel(ylabel)
        axes[fila,col].grid(True,which='both',alpha=.25)
        axes[fila,col].legend()
    axes[0,col].set_ylim(-80,100)
    axes[1,col].set_ylim(-110,110)
    axes[1,col].set_xlim(.1,.5 if col==0 else 1)
    axes[2,col].set_ylim(-60,60)
    axes[2,col].set_xlabel('Frecuencia (Hz)')
fig.savefig(BASE/'verificacion_AC.png',dpi=160)
(BASE/'resultado_verificacion.txt').write_text('\n'.join(salida)+'\n',encoding='utf8')
registrar('Comprobaciones completadas. Graficos guardados en verificacion_AC.png.')
