"""Verifica el barrido de Ejercicio 1.asc y genera la figura para el notebook.

Ejecutar primero el circuito en LTspice y luego este archivo en el entorno TC2.
"""
from pathlib import Path
import re
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parent

def leer_raw_ac(path):
    datos = path.read_bytes()
    marca = 'Binary:\n'.encode('utf-16-le')
    inicio = datos.index(marca)+len(marca)
    cabecera = datos[:inicio].decode('utf-16-le')
    if 'complex' not in cabecera or 'FastAccess' in cabecera:
        raise ValueError('Se espera un archivo AC binario normal de LTspice.')
    nvars = int(re.search(r'No\. Variables:\s*(\d+)', cabecera).group(1))
    npoints = int(re.search(r'No\. Points:\s*(\d+)', cabecera).group(1))
    nombres = re.findall(r'^\s*\d+\s+(\S+)\s+\S+\s*$', cabecera, re.M)
    matriz = np.frombuffer(datos, dtype='<c16', offset=inicio,
                          count=npoints*nvars).reshape(npoints,nvars)
    return {nombre:matriz[:,i] for i,nombre in enumerate(nombres)}

datos = leer_raw_ac(BASE/'Ejercicio 1.raw')
f = datos['frequency'].real
z = datos['V(in)']/(-datos['I(V1)'])
h = -10*np.cos(np.deg2rad(116.6))
s = 2j*np.pi*f
z_teorica = (s*s+s+1)/((s+1)*(s*s+h*s+25))
error = np.max(np.abs(z-z_teorica))
error_relativo = np.max(np.abs((z-z_teorica)/z_teorica))
assert error_relativo < 1e-6

fig = plt.figure(figsize=(12,10),constrained_layout=True)
gs = fig.add_gridspec(3,1,height_ratios=[1,1,.85])
axm = fig.add_subplot(gs[0])
axf = fig.add_subplot(gs[1],sharex=axm)
axp = fig.add_subplot(gs[2])
axm.semilogx(f,20*np.log10(np.abs(z)),color='#173f7a',lw=2,
             label='LTspice: V(in)/[-I(V1)]')
axm.semilogx(f,20*np.log10(np.abs(z_teorica)),'--',color='#d97706',lw=1,
             label='Función teórica')
axf.semilogx(f,np.angle(z,deg=True),color='#173f7a',lw=2)
axm.set_title('Ejercicio 1 - Impedancia simulada, K=1')
axm.set_ylabel('Módulo (dB ref. 1 Ω)')
axf.set_ylabel('Fase (°)')
axf.set_xlabel('Frecuencia (Hz)')
axm.legend()
for ax in [axm,axf]:
    ax.grid(True,which='both',alpha=.25)
    ax.set_xlim(1e-3,1e2)
    for omega,color in [(1,'#059669'),(5,'#c2410c')]:
        ax.axvline(omega/(2*np.pi),ls=':',color=color,alpha=.6)
axm.text(1/(2*np.pi),.97,r'$\omega_{0,z}=1$; polo real $s=-1$',
         transform=axm.get_xaxis_transform(),ha='right',va='top',fontsize=10,
         color='#047857')
axm.text(5/(2*np.pi),.70,r'$\omega_{0,p}=5$',
         transform=axm.get_xaxis_transform(),ha='left',va='top',fontsize=10,
         color='#c2410c')
polos = np.roots([1,h,25])
polos = np.append(polos,-1)
ceros = np.roots([1,1,1])
axp.axhline(0,color='#64748b',lw=.8)
axp.axvline(0,color='#64748b',lw=.8)
axp.plot(polos.real,polos.imag,'x',ms=10,mew=2,color='#c2410c',label='Polos')
axp.plot(ceros.real,ceros.imag,'o',ms=10,mew=2,mfc='none',color='#059669',label='Ceros')
for p in polos:
    if abs(p.imag)>1e-8:
        axp.annotate(f'{p.real:.4f} {p.imag:+.4f}j',(p.real,p.imag),
                     xytext=(8,5),textcoords='offset points',fontsize=9)
    else:
        axp.annotate('-1',(p.real,p.imag),xytext=(5,-16),textcoords='offset points',fontsize=9)
for c in ceros:
    axp.annotate(f'{c.real:.1f} {c.imag:+.4f}j',(c.real,c.imag),
                 xytext=(8,6 if c.imag>0 else -17),textcoords='offset points',fontsize=9)
axp.set_title('Plano s: raíces de la función teórica')
axp.set_xlabel('Re(s) (s⁻¹)')
axp.set_ylabel('Im(s) (rad/s)')
axp.set_xlim(-3,.8)
axp.set_ylim(-5.5,5.5)
axp.grid(True,alpha=.25)
axp.legend(loc='upper right')
fig.savefig(BASE/'Ejercicio 1 - polos y ceros.png',dpi=150,facecolor='white')
plt.close(fig)

def pendiente(f1,f2):
    m1=np.interp(np.log10(f1),np.log10(f),20*np.log10(np.abs(z)))
    m2=np.interp(np.log10(f2),np.log10(f),20*np.log10(np.abs(z)))
    return (m2-m1)/np.log10(f2/f1)

resumen = '\n'.join([
    'TS8 - Ejercicio 1 - Verificacion del circuito grafico de LTspice',
    f'Puntos del barrido: {len(f)}',
    f'Error absoluto maximo: {error:.6e} ohm',
    f'Error relativo maximo: {error_relativo:.6e}',
    f'Z a 0.001 Hz: {abs(z[0]):.10g} ohm',
    f'Z a 100 Hz: {abs(z[-1]):.10g} ohm',
    f'Pendiente 0.001 a 0.01 Hz: {pendiente(.001,.01):.8g} dB/decada',
    f'Pendiente 10 a 100 Hz: {pendiente(10,100):.8g} dB/decada',
    'L1 ideal: Rser=0.',
    'Las raices complejas se verifican algebraicamente; los factores auxiliares',
    'de LTspice indican las frecuencias naturales, no las posiciones completas',
    'de los polos ni los extremos de la impedancia.',
])+'\n'
(BASE/'Ejercicio 1 - verificacion.txt').write_text(resumen,encoding='utf-8')
print(resumen)
