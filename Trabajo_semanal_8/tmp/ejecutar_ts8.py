from pathlib import Path
import sys
import os
import re
import base64
import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager
from nbconvert import HTMLExporter

sys.stdout.reconfigure(encoding='utf-8')
base = Path(__file__).resolve().parents[1]
path = base / 'trabajo_semanal_8.ipynb'
nb = nbformat.read(path, as_version=4)
nbformat.validate(nb)
km = KernelManager(kernel_name='python3')
km.kernel_spec.argv[0] = sys.executable
client = NotebookClient(nb, km=km, timeout=180, resources={'metadata':{'path':str(base)}})
client.execute()
nbformat.write(nb, path)
errors = [out for cell in nb.cells for out in cell.get('outputs',[]) if out.output_type=='error']
assert not errors, errors
print('Notebook ejecutado sin errores:', sum(c.cell_type=='code' for c in nb.cells),'celdas de código')
for i,c in enumerate(nb.cells):
    for j,out in enumerate(c.get('outputs',[])):
        if out.output_type=='stream' and ('Error' in out.text or 'Puntos comparados' in out.text):
            print(out.text)
        if 'image/png' in out.get('data',{}):
            (base/'tmp'/f'celda_{i}_salida_{j}.png').write_bytes(base64.b64decode(out.data['image/png']))
exporter = HTMLExporter()
html, _ = exporter.from_notebook_node(nb)
(base/'tmp'/'vista_previa.html').write_text(html,encoding='utf-8')
for c in nb.cells:
    if c.cell_type=='markdown':
        for href in re.findall(r'(?:src="|\]\()([^"\)]+)',c.source):
            from urllib.parse import unquote
            if not href.startswith(('http:','https:','data:')):
                assert (base/unquote(href)).exists(),href
print('Referencias locales verificadas')
