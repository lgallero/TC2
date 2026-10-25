"""Ejecuta los esquemas de TS9 y compara los resultados de LTspice con la teoría.

Uso desde esta carpeta: python verificar_ts9.py --simular
Sin --simular se verifican los archivos .raw ya existentes.
"""
from pathlib import Path
import argparse
import json
import os
import re
import subprocess
import shutil
import tempfile
import numpy as np

BASE = Path(__file__).resolve().parent


def leer_raw_ac(path):
    datos = Path(path).read_bytes()
    marca = 'Binary:\n'.encode('utf-16-le')
    if marca not in datos:
        raise ValueError('Se espera un archivo AC binario de LTspice.')
    inicio = datos.index(marca) + len(marca)
    cabecera = datos[:inicio].decode('utf-16-le')
    if 'complex' not in cabecera or 'FastAccess' in cabecera:
        raise ValueError('El archivo debe ser AC complejo, sin conversión FastAccess.')
    nv = int(re.search(r'No\. Variables:\s*(\d+)', cabecera).group(1))
    npuntos = int(re.search(r'No\. Points:\s*(\d+)', cabecera).group(1))
    nombres = re.findall(r'^\s*\d+\s+(\S+)\s+\S+\s*$', cabecera, re.M)
    matriz = np.frombuffer(datos, dtype='<c16', offset=inicio,
                          count=npuntos*nv).reshape(npuntos, nv)
    return {nombre.lower(): matriz[:, i].copy() for i, nombre in enumerate(nombres)}


def cargar_ejercicio(numero):
    datos = leer_raw_ac(BASE / f'Ejercicio{numero}.raw')
    f = datos['frequency'].real
    referencia = datos['v(vg)'] if numero == 1 else datos['i(i1)' if numero == 2 else 'i(ig)']
    return f, datos['v(v2)']/referencia, datos


def teorica(numero, frecuencia):
    s = 2j*np.pi*np.asarray(frecuencia)
    q = s**3+2*s**2+2*s+1
    if numero == 2:
        return (s*s+9)/(9*q)
    k = 1 if numero == 1 else 10**(-6/20)
    return k*s*(s*s+1/16)/q


def cargar_parametros(numero):
    datos = leer_raw_ac(BASE/f'Ejercicio{numero}_parametros.raw')
    f = datos['frequency'].real
    if numero == 2:
        corriente = -datos['i(vprueba)']
        return f, datos['v(pout)']/corriente, datos['v(pin)']/corriente
    corriente = datos['i(iprueba)']
    return f, datos['v(pin)']/corriente, datos['v(pout)']/corriente


def verificar_parametros(numero):
    f, excitacion, transferencia = cargar_parametros(numero)
    s = 2j*np.pi*f
    if numero == 2:
        exc = (2*s*s+1)/(s*(s*s+2))
        trans = (s*s+9)/(9*s*(s*s+2))
    else:
        exc = s*(s*s+2)/(2*s*s+1)
        trans = (1 if numero == 1 else 10**(-6/20))*s*(s*s+1/16)/(2*s*s+1)
    # Normalización mixta: evita dividir por ceros y conserva la escala local.
    errores = [float(np.max(np.abs(sim-teo)/np.maximum(1, np.abs(teo))))
               for sim, teo in [(excitacion, exc), (transferencia, trans)]]
    assert max(errores) < 1e-4, (numero, errores)
    return dict(ejercicio=numero, error_normalizado_excitacion=errores[0],
                error_normalizado_parametro_transferencia=errores[1])


def verificar(numero):
    f, sim, _ = cargar_ejercicio(numero)
    teo = teorica(numero, f)
    error = np.abs(sim-teo)
    # El error relativo pierde significado en el nulo de transmisión.
    mascara = np.abs(teo) > 1e-5*np.max(np.abs(teo))
    eabs = float(np.max(error))
    erel = float(np.max(error[mascara]/np.abs(teo[mascara])))
    assert eabs < 1e-6, (numero, eabs)
    assert erel < 1e-4, (numero, erel)
    fz = (3 if numero == 2 else .25)/(2*np.pi)
    cerca = (f > .9*fz) & (f < 1.1*fz)
    ids = np.flatnonzero(cerca)
    imin = ids[np.argmin(np.abs(sim[cerca]))]
    return dict(ejercicio=numero, puntos=len(f), error_absoluto_maximo=eabs,
                error_relativo_maximo_fuera_del_nulo=erel,
                frecuencia_cero_teorica_hz=fz,
                frecuencia_minimo_barrido_hz=float(f[imin]),
                modulo_minimo_barrido_db=float(20*np.log10(abs(sim[imin]))),
                modulo_baja_db=float(20*np.log10(abs(sim[0]))),
                modulo_alta_db=float(20*np.log10(abs(sim[-1]))))


def verificar_cuadripolos(numero):
    """Verifica los cuatro Z calculados con .net contra el circuito LC."""
    datos = leer_raw_ac(BASE/f'Ejercicio{numero}_cuadripolos.raw')
    frecuencia = datos['frequency'].real
    s = 2j*np.pi*frecuencia
    dimension = 3 if numero == 3 else 2
    y = np.zeros((len(s), dimension, dimension), dtype=complex)

    def derivacion(nodo, admitancia):
        y[:, nodo, nodo] += admitancia

    def rama(nodo1, nodo2, admitancia):
        derivacion(nodo1, admitancia)
        derivacion(nodo2, admitancia)
        y[:, nodo1, nodo2] -= admitancia
        y[:, nodo2, nodo1] -= admitancia

    if numero == 2:
        derivacion(0, s*27/17)
        rama(0, 1, 1/(s*289/243)+s*27/289)
        derivacion(1, s*7/17)
        salida = 1
    else:
        derivacion(0, 1/(s*31/14))
        rama(0, 1, 1/(s*961/48)+s*768/961)
        if numero == 1:
            derivacion(1, 1/(s*31/48))
            salida = 1
        else:
            k = 10**(-6/20)
            rama(1, 2, 1/(s*(1-k)*31/48))
            derivacion(2, 1/(s*k*31/48))
            salida = 2
    z = np.linalg.inv(y)
    indices = {'Z11': (0, 0), 'Z21': (salida, 0),
               'Z12': (0, salida), 'Z22': (salida, salida)}
    errores = {}
    for nombre, (fila, columna) in indices.items():
        teorico = z[:, fila, columna]
        simulado = datos[f'{nombre}(V1)'.lower()]
        error = float(np.max(np.abs(simulado-teorico)/np.maximum(1, np.abs(teorico))))
        assert error < 1e-4, (numero, nombre, error)
        errores[nombre] = error
    return dict(puntos=len(frecuencia), errores_normalizados=errores)


def buscar_ltspice():
    candidatos = [os.environ.get('LTSPICE_EXE', ''),
                  str(Path(os.environ.get('LOCALAPPDATA', ''))/'Programs/ADI/LTspice/LTspice.exe'),
                  r'C:\Program Files\ADI\LTspice\LTspice.exe',
                  r'C:\Program Files\LTC\LTspiceXVII\XVIIx64.exe']
    for candidato in candidatos:
        if candidato and Path(candidato).is_file():
            return candidato
    raise FileNotFoundError('No se encontró LTspice. Definir LTSPICE_EXE con su ubicación.')


def simular():
    exe = buscar_ltspice()
    for numero in (1, 2, 3):
        for esquema in [BASE/f'Ejercicio{numero}.asc', BASE/f'Ejercicio{numero}_parametros.cir',
                        BASE/f'Ejercicio{numero}_cuadripolos.asc']:
            r = subprocess.run([exe, '-b', str(esquema)], cwd=BASE, timeout=90,
                               creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
                               capture_output=True)
            if r.returncode:
                log = esquema.with_suffix('.log')
                mensaje = log.read_text(errors='replace') if log.exists() else ''
                if 'Unable to open' not in mensaje or 'for writing' not in mensaje:
                    raise RuntimeError(f'Falló {esquema.name}. Revisar {esquema.stem}.log.')
                # El visor mantiene abierto el RAW. Se verifica una simulación nueva
                # en una carpeta temporal sin cerrar la ventana del usuario.
                with tempfile.TemporaryDirectory(prefix='ts9_verificacion_') as carpeta:
                    copia = Path(carpeta)/esquema.name
                    shutil.copy2(esquema, copia)
                    nuevo = subprocess.run([exe, '-b', str(copia)], cwd=carpeta,
                                           timeout=90, capture_output=True,
                                           creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                    if nuevo.returncode:
                        raise RuntimeError(copia.with_suffix('.log').read_text(errors='replace'))
                    actual = leer_raw_ac(esquema.with_suffix('.raw'))
                    reciente = leer_raw_ac(copia.with_suffix('.raw'))
                    if actual.keys() != reciente.keys() or any(
                        not np.allclose(actual[nombre], reciente[nombre], rtol=1e-10, atol=1e-12)
                        for nombre in reciente
                    ):
                        raise RuntimeError(f'El RAW abierto de {esquema.name} difiere del nuevo cálculo.')
                    shutil.copy2(copia.with_suffix('.log'), log)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--simular', action='store_true')
    args = parser.parse_args()
    if args.simular:
        simular()
    resultados = [dict(**verificar(n), parametros=verificar_parametros(n),
                       cuadripolos=verificar_cuadripolos(n)) for n in (1, 2, 3)]
    texto = json.dumps(resultados, indent=2, ensure_ascii=False)
    (BASE/'verificacion_resultados.json').write_text(texto+'\n', encoding='utf-8')
    print(texto)
