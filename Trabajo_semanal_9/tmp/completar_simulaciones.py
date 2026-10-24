from pathlib import Path
import re
import shutil

base = Path(__file__).resolve().parents[1]
carpeta = base/'Simulaciones'
respaldo = base/'tmp/respaldo_simulaciones'
respaldo.mkdir(exist_ok=True)


def completar(numero, cambios, flags, directivas):
    path = carpeta/f'Ejercicio{numero}.asc'
    if not (respaldo/path.name).exists():
        shutil.copy2(path, respaldo/path.name)
    texto = (respaldo/path.name).read_text(encoding='utf-8')
    cabecera, *simbolos = re.split(r'(?m)^SYMBOL ', texto)
    cabecera = re.sub(r'SHEET .*', 'SHEET 1 1480 1040', cabecera)
    cabecera += ''.join(f'FLAG {pos} {nombre}\n' for pos, nombre in flags)
    nuevos = []
    for bloque in simbolos:
        # Las directivas se reconstruyen debajo del dibujo.
        bloque = re.split(r'(?m)^TEXT ', bloque)[0]
        nombre = re.search(r'(?m)^SYMATTR InstName (.+)$', bloque).group(1).strip()
        if nombre in cambios:
            attrs = cambios[nombre]
            for attr, valor in attrs.items():
                patron = rf'(?m)^SYMATTR {attr} .*$'
                linea = f'SYMATTR {attr} {valor}'
                if re.search(patron, bloque):
                    bloque = re.sub(patron, lambda m: linea, bloque)
                else:
                    bloque = bloque.rstrip()+'\n'+linea+'\n'
        nuevos.append('SYMBOL '+bloque.rstrip()+'\n')
    texto = cabecera+''.join(nuevos)
    texto += ''.join(f'TEXT 32 {416+40*i} Left 2 !{d}\n' for i, d in enumerate(directivas))
    texto += 'TEXT 32 920 Left 2 ;Frecuencias AC en Hz: f = omega/(2*pi).\n'
    if numero in (1, 3):
        texto += 'TEXT 32 952 Left 2 ;L1: Rser=1n evita el lazo ideal de inductores en DC.\n'
    path.write_text(texto, encoding='utf-8')


completar(1, {'Vg': {'Value':'AC 1'}, 'L1': {'SpiceLine':'Rser=1n'},
              'L2': {'SpiceLine':'Rser=0'}, 'L3': {'SpiceLine':'Rser=0'}},
          [('32 64','Vg'), ('336 64','V1')],
          ['.ac dec 1000 0.0001 1000', '.options plotwinsize=0',
           '.save V(Vg) V(V1) V(V2) I(Vg)',
           '.meas AC baja FIND mag(V(V2)/V(Vg)) AT=0.0001',
           '.meas AC alta FIND mag(V(V2)/V(Vg)) AT=1000',
           '.meas AC nulo_re FIND re(V(V2)/V(Vg)) AT={0.25/(2*pi)}',
           '.meas AC nulo_im FIND im(V(V2)/V(Vg)) AT={0.25/(2*pi)}'])

# Se conserva la numeración de las remociones: C1 en la salida, C3 en la entrada.
completar(2, {'I1': {'Value':'AC 1'},
              'C1': {'InstName':'C3', 'Value':'{27/17}'},
              'C3': {'InstName':'C1', 'Value':'{7/17}'},
              'C2': {'Value':'{27/289}'},
              'L1': {'InstName':'L2', 'Value':'{289/243}', 'SpiceLine':'Rser=0'}},
          [('240 48','V1')],
          ['.ac dec 1000 0.0001 1000', '.options plotwinsize=0',
           '.save V(V1) V(V2) I(I1)',
           '.meas AC baja FIND mag(V(V2)/I(I1)) AT=0.0001',
           '.meas AC alta FIND mag(V(V2)/I(I1)) AT=1000',
           '.meas AC nulo_re FIND re(V(V2)/I(I1)) AT={3/(2*pi)}',
           '.meas AC nulo_im FIND im(V(V2)/I(I1)) AT={3/(2*pi)}'])

completar(3, {'I1': {'InstName':'Ig', 'Value':'AC 1'},
              'L1': {'SpiceLine':'Rser=1n'}, 'L2': {'SpiceLine':'Rser=0'},
              'C1': {'InstName':'C2'},
              'L3A': {'Value':'{La}', 'SpiceLine':'Rser=0'},
              'L3B': {'Value':'{Lb}', 'SpiceLine':'Rser=0'}},
          [('432 16','V1'), ('704 16','Vb')],
          ['.param K=10**(-6/20) La=(1-K)*31/48 Lb=K*31/48',
           '.ac dec 1000 0.0001 1000', '.options plotwinsize=0',
           '.save V(V1) V(Vb) V(V2) I(Ig)',
           '.meas AC baja FIND mag(V(V2)/I(Ig)) AT=0.0001',
           '.meas AC alta FIND mag(V(V2)/I(Ig)) AT=1000',
           '.meas AC divisor FIND mag(V(V2)/V(Vb)) AT=1',
           '.meas AC nulo_re FIND re(V(V2)/I(Ig)) AT={0.25/(2*pi)}',
           '.meas AC nulo_im FIND im(V(V2)/I(Ig)) AT={0.25/(2*pi)}'])

for n, expresion in [(1,'V(v2)/V(vg)'),(2,'V(v2)/I(I1)'),(3,'V(v2)/I(Ig)')]:
    plt = '[AC Analysis]\n{\n   Npanes: 1\n   {\n'
    plt += f'      traces: 1 {{524290,0,"{expresion}"}}\n'
    plt += "      X: (' ',0,0.0001,0,1000)\n      Y[0]: (' ',0,0.000001,20,2)\n"
    plt += "      Y[1]: (' ',0,-180,90,180)\n      Log: 1 2 0\n      GridStyle: 1\n      PltMag: 1\n      PltPhi: 1 0\n   }\n}\n"
    (carpeta/f'Ejercicio{n}.plt').write_text(plt, encoding='ascii')
print('Esquemas y configuraciones de gráficos completados.')
