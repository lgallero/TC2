from pathlib import Path
from datetime import datetime
import ast, re, shutil
import nbformat

base=Path(r'D:\UTN\4to\TC2\TC2 - Lucas\TC2\Trabajo_semanal_9')
p=base/'trabajo_semanal_9.ipynb'
backup=base/'tmp'/('respaldo_funciones_'+datetime.now().strftime('%Y%m%d_%H%M%S')+'.ipynb')
shutil.copy2(p,backup)
nb=nbformat.read(p,as_version=4)
original_markdown={c.id:c.source for c in nb.cells if c.cell_type=='markdown'}
remove={'verificar_cero','componentes','matriz_pi','evaluar'}
for c in nb.cells:
    if c.cell_type!='code':continue
    source=c.source
    parseable='\n'.join('# '+line if line.lstrip().startswith('%') else line for line in source.splitlines())
    tree=ast.parse(parseable)
    edits=[]
    lines=source.splitlines(keepends=True)
    offsets=[0]
    for line in lines:offsets.append(offsets[-1]+len(line))
    for node in tree.body:
        if isinstance(node,ast.FunctionDef) and node.name in remove:
            edits.append((offsets[node.lineno-1],offsets[node.end_lineno],''))
    for node in ast.walk(tree):
        if isinstance(node,ast.Expr) and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name):
            call=node.value
            name=call.func.id
            if name=='verificar_cero':
                argument=ast.get_source_segment(parseable,call.args[0])
                replacement=f'assert sp.cancel({argument}) == 0'
            elif name=='componentes':
                argument=ast.get_source_segment(parseable,call.args[0])
                replacement=f"for nombre, valor, unidad in {argument}:\n    print(f'{{nombre}}: {{sp.sstr(valor)}} = {{float(valor):.10g}} {{unidad}}')"
            else:continue
            edits.append((offsets[node.lineno-1],offsets[node.end_lineno],replacement+'\n'))
    for start,end,replacement in sorted(edits,reverse=True):
        source=source[:start]+replacement+source[end:]
    source=source.replace('from IPython.display import IFrame\n','') if c.id=='e5d2f4a8' else source
    source=source.replace("h = evaluar(funcion)","h = np.asarray(sp.lambdify(s, funcion, 'numpy')(2j*np.pi*f), dtype=complex)")
    source=source.replace("        eje.semilogx(f, 20*np.log10(np.maximum(abs(evaluar(funcion)), 1e-16)), color=color)","        h = np.asarray(sp.lambdify(s, funcion, 'numpy')(2j*np.pi*f), dtype=complex)\n        eje.semilogx(f, 20*np.log10(np.maximum(abs(h), 1e-16)), color=color)")
    source=source.replace('Z_red1 = matriz_pi(1/(s*L1_1),Zt_1,1/(s*L3_1))', '''Y_red1 = sp.Matrix([
    [1/(s*L1_1)+1/Zt_1, -1/Zt_1],
    [-1/Zt_1, 1/(s*L3_1)+1/Zt_1]
])
Z_red1 = Y_red1.inv().applyfunc(sp.factor)''')
    source=source.replace('Z_red2 = matriz_pi(s*C3_2,Zt_2,s*C1_2)', '''Y_red2 = sp.Matrix([
    [s*C3_2+1/Zt_2, -1/Zt_2],
    [-1/Zt_2, s*C1_2+1/Zt_2]
])
Z_red2 = Y_red2.inv().applyfunc(sp.factor)''')
    source=re.sub(r'\n{3,}','\n\n',source).strip()
    c.source=source
assert all(c.source==original_markdown[c.id] for c in nb.cells if c.cell_type=='markdown')
code='\n'.join('\n'.join(l for l in c.source.splitlines() if not l.lstrip().startswith('%')) for c in nb.cells if c.cell_type=='code')
parsed=ast.parse(code)
remaining=[n.name for n in parsed.body if isinstance(n,ast.FunctionDef)]
assert set(remaining)=={'mostrar','graficar_transferencia','graficar_parametros'},remaining
assert not any(isinstance(n,ast.Name) and n.id in remove for n in ast.walk(parsed))
nbformat.validate(nb)
nbformat.write(nb,p)
print('Funciones restantes:',', '.join(remaining))
print('Markdown y orden de celdas conservados.')
print('Respaldo:',backup)
