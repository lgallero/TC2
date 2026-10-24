from pathlib import Path
import shutil
import nbformat

BASE = Path(__file__).resolve().parents[1]
nbpath = BASE/'trabajo_semanal_9.ipynb'
respaldo = BASE/'tmp/respaldo_20261024'
respaldo.mkdir(exist_ok=True)
for p in [nbpath]+list((BASE/'Imagenes').glob('TS9_mapa_remociones_*.png')):
    if not (respaldo/p.name).exists():
        shutil.copy2(p,respaldo/p.name)

nb = nbformat.read(nbpath,as_version=4)
enunciado = r'''
# Enunciado

**1)** Dada la siguiente **transferencia de tensión:**

<div align="center">
    <img src="./Imagenes/Enunciado1.png" alt="Circuito del enunciado 1" width="430" />
</div>

$$T(s)=\frac{V_2}{V_g}=k\cdot\frac{s\cdot\left(s^2+\frac{1}{16}\right)}{s^3+2\cdot s^2+2\cdot s+1}$$

**a)** Sintetizar el cuadripolo pasivo sin pérdidas.

**b)** Hallar el valor de $k$ que cumple con la síntesis y el valor de los componentes hallados.

<br>

**2)** Dada la siguiente **transimpedancia:**

<div align="center">
    <img src="./Imagenes/Enunciado2.png" alt="Circuito del enunciado 2" width="430" />
</div>

$$T(s)=\frac{V_2}{I_1}=k\cdot\frac{s^2+9}{s^3+2\cdot s^2+2\cdot s+1}$$

**a)** Sintetizar el cuadripolo pasivo sin pérdidas.

**b)** Hallar el valor de $k$ que cumple con la síntesis y valor de los componentes hallados.

<br>

**3)** Dada la siguiente **transimpedancia:**

<div align="center">
    <img src="./Imagenes/Enunciado3.png" alt="Circuito del enunciado 3" width="430" />
</div>

$$T(s)=\frac{V_2}{I_g}=k\cdot\frac{s\cdot\left(s^2+\frac{1}{16}\right)}{s^3+2\cdot s^2+2\cdot s+1}$$

**a)** Sintetizar el cuadripolo pasivo sin pérdidas.

**b)** Hallar el valor de $k$ para obtener **-6 dB** en el centro de la banda de paso.
'''.strip()

for cell in nb.cells:
    if cell.cell_type == 'markdown' and cell.source.startswith('# Enunciado'):
        cell.source = enunciado
        continue
    if cell.cell_type == 'markdown':
        cell.source = cell.source.replace('Y_{11}', 'Y_0').replace('Y_{22}', 'Y_0')
        cell.source = cell.source.replace(
            'Se invierte la impedancia:\n\n$$Y_0=',
            'Se invierte la impedancia de entrada, conservando la condición $I_2=0$:\n\n$$Y_0=\\frac{1}{Z_{11}}=')
        if 'Primera remoción: capacitor C1 en la salida' in cell.source:
            cell.source = cell.source.replace('$$Y_0=',r'$$Y_0=\frac{1}{Z_{22}}=',1)
        if 'Remociones y cierre equivalente' in cell.source:
            cell.source = cell.source.replace(
                'Se repite la remoción parcial de $14/(31s)$ de $Y_0$',
                r'Se define $Y_0=1/Z_{11}$ y se repite la remoción parcial de $14/(31s)$ de $Y_0$')
        if 'Criterio de síntesis y normalización' in cell.source:
            cell.source += r'''

Para las remociones se invierte la función de excitación bajo su condición de medición: se usa $Y_0=1/Z_{11}$ con $I_2=0$ en los ejercicios 1 y 3, y $Y_0=1/Z_{22}$ con $I_1=0$ en el ejercicio 2. $Y_0$ es una función auxiliar de síntesis, no un parámetro de la matriz de admitancias. La conversión entre matrices es $\mathbf{Y}=\mathbf{Z}^{-1}$; no se obtiene invirtiendo cada parámetro por separado.
'''
    else:
        cell.source = cell.source.replace('Y11_1', 'Y0_1').replace('Y22_2', 'Y0_2')
        if 'Y0_1 = sp.cancel(1/Z11_1)' in cell.source:
            cell.source = cell.source.replace('Y0_1 = sp.cancel(1/Z11_1)',
                "Y0_1 = sp.cancel(1/Z11_1)\nmostrar('Y_0=1/Z_{11}', Y0_1)")
        if 'Y0_2 = sp.cancel(1/Z22_2)' in cell.source:
            cell.source = cell.source.replace('Y0_2 = sp.cancel(1/Z22_2)',
                "Y0_2 = sp.cancel(1/Z22_2)\nmostrar('Y_0=1/Z_{22}', Y0_2)")
        if 'Y2_3, YL1_3 = remover_polo_dc(1/Z11_3,' in cell.source:
            cell.source = cell.source.replace(
                'Y2_3, YL1_3 = remover_polo_dc(1/Z11_3,',
                "Y0_3 = sp.cancel(1/Z11_3)\nmostrar('Y_0=1/Z_{11}', Y0_3)\nY2_3, YL1_3 = remover_polo_dc(Y0_3,")

nbformat.validate(nb)
nbformat.write(nb,nbpath)

# Regenerar únicamente los mapas: no reconstruir el notebook desde su plantilla
# inicial, para conservar las ediciones y el orden de celdas del alumno.
generador = BASE/'tmp/armar_ts9.py'
prefijo = generador.read_text(encoding='utf-8').split('\ncells=[]')[0]
exec(compile(prefijo,str(generador),'exec'),{'__file__':str(generador)})
print('Enunciado, notación y mapas actualizados sobre el notebook existente.')
