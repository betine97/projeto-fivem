import bpy
from pathlib import Path
P=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(P/'estruturas_porto_20261009/modelos/01_Casa_creme_varanda.blend'))
for c in bpy.data.collections:
    if c.name=='Colisao_preparada':c.hide_viewport=False
bpy.context.view_layer.update()
dg=bpy.context.evaluated_depsgraph_get()
for o in bpy.data.objects:
    if o.name.startswith(('Piso','COL_Piso')):
        me=o.evaluated_get(dg).to_mesh()
        print('COLCHECK',o.name,'loc',o.location[:],'scale',o.scale[:],'matrix',[list(r) for r in o.matrix_world],'range',min((o.matrix_world@v.co).z for v in me.vertices),max((o.matrix_world@v.co).z for v in me.vertices),flush=True)
