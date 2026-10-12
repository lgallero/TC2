from pathlib import Path
from io import BytesIO
from urllib.parse import unquote
import base64
import re
import sys
import json
import numpy as np
import nbformat as nbf

sys.stdout.reconfigure(encoding='utf-8')
BASE = Path(__file__).resolve().parents[1]
PATH = BASE/'trabajo_semanal_8.ipynb'
nb = nbf.read(PATH,as_version=4)
before = PATH.read_bytes()
(BASE/'tmp/notebook_antes_de_incorporar_capturas.ipynb').write_bytes(before)

def imagen(cell, nombre, archivo, texto):
    mime = 'image/jpeg' if archivo.suffix.lower() in ['.jpg','.jpeg'] else 'image/png'
    cell.setdefault('attachments',{})[nombre] = {mime:base64.b64encode(archivo.read_bytes()).decode('ascii')}
    return f'![{texto}](attachment:{nombre})'

def incrustar_imagenes(cell):
    if cell.cell_type!='markdown':
        return
    def reemplazo(match):
        bloque = match.group(0)
        origen = re.search(r'src="([^"]+)"',bloque).group(1)
        alt = re.search(r'alt="([^"]+)"',bloque)
        ruta = (BASE/unquote(origen)).resolve()
        assert ruta.is_file(),ruta
        nombre = ruta.name
        return imagen(cell,nombre,ruta,alt.group(1) if alt else 'Figura del desarrollo')
    cell.source = re.sub(r'<div align="center">\s*<img[^>]*src="[^"]+"[^>]*>\s*</div>',reemplazo,cell.source)
    cell.source = re.sub(r'^\[[^\]]+\]\((?:Imagenes|Simulacion)/[^\)]+\)\s*$', '',cell.source,flags=re.M)

# El encabezado conserva su alineación y tamaño mediante una imagen incorporada.
logo = base64.b64encode((BASE/'tmp/logo_notebook.png').read_bytes()).decode('ascii')
nb.cells[0].source = re.sub(r'<img[^>]+>',f'<img src="data:image/png;base64,{logo}" align="right" width="150" />',nb.cells[0].source,count=1)
nb.cells[2].source = nb.cells[2].source.replace('from pathlib import Path\n','').replace('import re\n','')
nb.cells[2].source = nb.cells[2].source.replace('from IPython.display import display, Math, Image, IFrame','from IPython.display import display, Math\nfrom io import BytesIO\nimport base64')
for cell in nb.cells:
    incrustar_imagenes(cell)

cell = nb.cells[17]
cell.attachments = {}
img_circuito1 = imagen(cell,'sim_ej1_circuito.png',BASE/'Imagenes/Ejercicio1 - Simulacion - Circuito .png','Circuito del ejercicio 1 en LTspice')
img_respuesta1 = imagen(cell,'sim_ej1_modulo_fase.png',BASE/'Imagenes/Ejercicio1 - Simulacion.png','Módulo y fase de la impedancia del ejercicio 1')
img_baja1 = imagen(cell,'sim_ej1_cursor_baja.png',BASE/'Imagenes/Ejercicio1 - Simulacion - Cursores Baja Freq.png','Cursor de baja frecuencia del ejercicio 1')
img_alta1 = imagen(cell,'sim_ej1_cursores_alta.png',BASE/'Imagenes/Ejercicio1 - Simulacion - Cursores Alta Freq.png','Cursores de alta frecuencia del ejercicio 1')
cell.source = r'''### <ins>Simulación en LTspice</ins>

**Circuito simulado**

'''+img_circuito1+r'''

La impedancia se mide con `V(in)/(-I(V1))`. El signo negativo toma la corriente que entra al dipolo. La inductancia tiene `Rser=0`, de modo que corresponde al componente ideal utilizado en la síntesis.

**Módulo y fase**

'''+img_respuesta1+r'''

En baja frecuencia el módulo se aproxima a $-27{,}96\;\mathrm{dB}$, correspondiente a $Z(0)=0{,}04\;\Omega$, y la fase está próxima a $0^\circ$. Se observan un mínimo y un máximo finitos; a alta frecuencia el módulo decrece y la fase tiende a $-90^\circ$.

Los polos y ceros complejos están fuera del eje $j\omega$. Sus posiciones se verifican mediante las raíces calculadas en la resolución simbólica; los extremos del módulo no coinciden, en general, con las partes imaginarias ni con los módulos de esas raíces.

**Cursores en baja frecuencia**

'''+img_baja1+r'''

La captura contiene una lectura en $f=1\;\mathrm{mHz}$: $M=-27{,}959135\;\mathrm{dB}$ y fase $-64{,}46317\;\mathrm{m}^\circ=-0{,}06446317^\circ$. Es consistente con el comportamiento resistivo en DC. El segundo cursor está desactivado, por lo que no se calcula una pendiente a partir de esa captura.

**Cursores en alta frecuencia**

'''+img_alta1+r'''

La pendiente se calcula a partir de la diferencia de módulo y de la separación logarítmica de las frecuencias:

$$m=\frac{M_2-M_1}{\log_{10}(f_2/f_1)}\quad[\mathrm{dB/década}].$$

| Zona | $f_1$ (Hz) | $f_2$ (Hz) | $M_1$ (dB) | $M_2$ (dB) | Pendiente (dB/década) |
|---|---:|---:|---:|---:|---:|
| Baja frecuencia | $0{,}001$ | | $-27{,}959135$ | | |
| Alta frecuencia | $10{,}052201$ | $100$ | $-35{,}978439$ | $-55{,}963290$ | $-20{,}03014$ |

La medición de alta frecuencia se aproxima al valor asintótico de $-20\;\mathrm{dB/década}$, asociado a $Z(s)\sim1/s$.

**Comparación numérica con los datos de simulación incorporados**

Se compara la impedancia simulada con la función obtenida por remociones. Los datos de frecuencia e impedancia utilizados están guardados dentro de este notebook.
'''

def leer_raw(path):
    raw = path.read_bytes()
    marca = 'Binary:\n'.encode('utf-16-le')
    inicio = raw.index(marca)+len(marca)
    cabecera = raw[:inicio].decode('utf-16-le')
    nvars = int(re.search(r'No\. Variables:\s*(\d+)',cabecera).group(1))
    npoints = int(re.search(r'No\. Points:\s*(\d+)',cabecera).group(1))
    nombres = re.findall(r'^\s*\d+\s+(\S+)\s+\S+\s*$',cabecera,re.M)
    matriz = np.frombuffer(raw,dtype='<c16',offset=inicio,count=nvars*npoints).reshape(npoints,nvars)
    datos = {nombre:matriz[:,i] for i,nombre in enumerate(nombres)}
    return datos['frequency'].real.copy(),(datos['V(in)']/(-datos['I(V1)'])).copy()

datos_codificados = {}
for nombre,archivo in [('ejercicio1','Ejercicio 1.raw'),('ejercicio2','Ejercicio 2.raw')]:
    f,z = leer_raw(BASE/'Simulacion'/archivo)
    buf = BytesIO()
    np.savez_compressed(buf,frecuencia=f,impedancia=z)
    datos_codificados[nombre] = base64.b64encode(buf.getvalue()).decode('ascii')

data_cell = nbf.v4.new_code_cell(
    '# Datos de frecuencia e impedancia incorporados para verificar las simulaciones.\n'
    'DATOS_SIMULACION = '+json.dumps(datos_codificados,indent=2)+'\n',
    metadata={'tags':['hide-input'],'jupyter':{'source_hidden':True}})

nb.cells[18].source = '''def comparar_ltspice(nombre, funcion, titulo):
    with np.load(BytesIO(base64.b64decode(DATOS_SIMULACION[nombre])), allow_pickle=False) as datos:
        f = datos['frecuencia'].copy()
        z_lt = datos['impedancia'].copy()
    z_teo = sp.lambdify(s, funcion, 'numpy')(2j*np.pi*f)
    error = np.max(np.abs(z_lt-z_teo))
    error_rel = np.max(np.abs((z_lt-z_teo)/z_teo))
    print(f'Puntos comparados: {len(f)}')
    print(f'Error absoluto máximo: {error:.3e} Ω')
    print(f'Error relativo máximo: {error_rel:.3e}')
    print(f'Z a {f[0]:g} Hz: {abs(z_lt[0]):.9g} Ω')
    print(f'Z a {f[-1]:g} Hz: {abs(z_lt[-1]):.9g} Ω')
    assert error_rel < 1e-5
    fig, ax = plt.subplots(2, 1, figsize=(11, 6), sharex=True, constrained_layout=True)
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

errores_ej1 = comparar_ltspice('ejercicio1', Z_ej1, 'Ejercicio 1 - Teoría y LTspice')
'''
nb.cells[18].outputs = []
nb.cells[18].execution_count = None

cell = nb.cells[34]
cell.attachments = {}
circuito2 = imagen(cell,'sim_ej2_circuito.png',BASE/'Imagenes/Ejercicio2 - Simulacion - Circuito .png','Circuito del ejercicio 2 en LTspice')
respuesta2 = imagen(cell,'sim_ej2_modulo_fase.png',BASE/'Imagenes/Ejercicio1 - Simulacion - Modulo y Fase .png','Módulo y fase del ejercicio 2')
cursores21 = imagen(cell,'sim_ej2_cursores_1.png',BASE/'Imagenes/Ejercicio1 - Simulacion- Polo y cero parte 1.png','Cursores próximos al primer polo y al primer cero del ejercicio 2')
cursores22 = imagen(cell,'sim_ej2_cursores_2.png',BASE/'Imagenes/Ejercicio1 - Simulacion- Polo y cero parte 2.png','Cursores próximos al segundo polo y al segundo cero del ejercicio 2')
cell.source = r'''### <ins>Simulación en LTspice</ins>

**Circuito simulado**

'''+circuito2+r'''

El circuito utiliza los valores exactos obtenidos por remociones. La impedancia se mide mediante `V(in)/(-I(V1))`.

**Módulo y fase**

'''+respuesta2+r'''

El módulo desciende desde aproximadamente $8{,}52\;\mathrm{dB}$ hasta $0\;\mathrm{dB}$, de acuerdo con $Z(0)=8/3\;\Omega$ y $Z(\infty)=1\;\Omega$. La fase es negativa en la zona intermedia y se aproxima a $0^\circ$ en los extremos, como corresponde al dipolo RC.

**Cursores próximos a los quiebres de polos y ceros**

'''+cursores21+r'''

'''+cursores22+r'''

| Singularidad | Frecuencia teórica (Hz) | Frecuencia del cursor (Hz) | Módulo leído (dB) | Fase leída (°) |
|---|---:|---:|---:|---:|
| Polo en $-1$ | $0{,}159155$ | $0{,}15922087$ | $6{,}2826618$ | $-22{,}837562$ |
| Cero en $-2$ | $0{,}318310$ | $0{,}31841975$ | $3{,}9108443$ | $-25{,}559204$ |
| Polo en $-3$ | $0{,}477465$ | $0{,}47752927$ | $2{,}5657010$ | $-23{,}384126$ |
| Cero en $-4$ | $0{,}636620$ | $0{,}63679552$ | $1{,}7772364$ | $-20{,}655989$ |

Las frecuencias de los cursores están próximas a $f=\sigma/(2\pi)$ de cada factor. Los valores de módulo y fase son lecturas de la **impedancia total**, por lo que no deben compararse con los $\pm3{,}0103\;\mathrm{dB}$ de un factor normalizado aislado. Las posiciones exactas de las singularidades se verifican mediante la factorización de $Z(s)$.

**Comparación numérica con los datos de simulación incorporados**

Se verifica la función completa con los datos de frecuencia e impedancia guardados en el notebook.
'''
nb.cells[35].source = "errores_ej2 = comparar_ltspice('ejercicio2', Z_ej2, 'Ejercicio 2 - Teoría y LTspice')"
nb.cells[35].outputs = []
nb.cells[35].execution_count = None

# Se conserva el espacio de las mediciones de pendientes que no tienen captura.
nb.cells[36].source = r'''**Ley de variación: lecturas pendientes**

| Zona | $f_1$ (Hz) | $f_2$ (Hz) | $M_1$ (dB) | $M_2$ (dB) | Pendiente (dB/década) |
|---|---|---|---|---|---|
| Baja frecuencia | | | | | |
| Alta frecuencia | | | | | |

No se dispone de capturas con dos cursores ubicados en las zonas asintóticas de este ejercicio. Se conservan esos campos en blanco. Teóricamente, la pendiente tiende a $0\;\mathrm{dB/década}$ en ambos extremos porque la impedancia tiene valores resistivos finitos en DC e infinito.
'''
nb.cells[37].source = r'''---
# <ins>Resolución manuscrita</ins>

Las páginas del desarrollo a mano están incorporadas a continuación. Las tres primeras corresponden al ejercicio 1 y las cuatro restantes al ejercicio 2.
'''
manuscrito = nbf.v4.new_markdown_cell('')
contenido = []
for i in range(1,8):
    contenido += [f'### Página {i}',imagen(manuscrito,f'manuscrito_pagina_{i}.jpg',BASE/f'tmp/manuscrito_{i}.jpg',f'Desarrollo manuscrito, página {i}')]
manuscrito.source = '\n\n'.join(contenido)
nb.cells[38] = manuscrito
nb.cells.insert(18,data_cell)

# Comprobación de las referencias visuales: todas están incorporadas.
for i,c in enumerate(nb.cells):
    if c.cell_type=='markdown':
        for ref in re.findall(r'(?:src="|\]\()([^"\)]+)',c.source):
            assert ref.startswith(('attachment:','data:')), (i,ref)
            if ref.startswith('attachment:'):
                assert ref[len('attachment:'):] in c.get('attachments',{}),(i,ref)
    assert not re.search(r'Imagenes[/\\]|Simulacion[/\\]|IFrame\(|\.(?:raw|asc|cir|plt|log)(?!\w)|TS8\.pdf',c.source),(i,'Referencia externa')
nbf.validate(nb)
nbf.write(nb,PATH)
print('Notebook autocontenido:',len(nb.cells),'celdas')
print('Imágenes incorporadas:',sum(len(c.get('attachments',{})) for c in nb.cells))
print('Tamaño:',PATH.stat().st_size)
