import bpy, json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parent;W=P.parent
bpy.ops.wm.open_mainfile(filepath=str(W/'adega_referencia_20261008/mansao_com_adega.blend'))
o=bpy.data.objects.get('Revestimento continuo terreo 10 0')
assert o
inv=o.matrix_world.inverted()
for z in [-.6,0,1,1.5,1.8,2.1]:
    ys=[]
    for i in range(120):
        y=-6.65+i*.05
        hit,p,n,face=o.ray_cast(inv@Vector((13,y,z)),inv.to_3x3()@Vector((1,0,0)),distance=2)
        if not hit:ys.append(round(y,3))
    print('WALL_OPENING_AT_Z',z,ys,flush=True)
for c in bpy.data.collections:
    if c.name.startswith(('24_','25_')):
        ps=[o.matrix_world@v.co for o in c.objects if o.type=='MESH' for v in o.data.vertices]
        print('NEIGHBOR',c.name,[min(p[i] for p in ps) for i in range(3)],[max(p[i] for p in ps) for i in range(3)],flush=True)
for name in ['Caixilhos solidos das janelas','Vidros nos vaos nativos.001']:
    o=bpy.data.objects.get(name)
    inv=o.matrix_world.inverted()
    for z in [-.75,-.65,-.6,1.55,1.65,1.7]:
        try:hit,p,n,f=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).ray_cast(inv@Vector((13,-5.17,z)),inv.to_3x3()@Vector((1,0,0)),distance=2)
        except RuntimeError:continue
        print('DOOR_RETURN',name,z,tuple(o.matrix_world@p) if hit else None,flush=True)
for z in [-.66,-.62,-.59,1.6,1.66,1.69]:
    hits=[]
    for o in bpy.context.scene.objects:
        if o.type!='MESH' or o.hide_render:continue
        inv=o.matrix_world.inverted()
        try:hit,p,n,f=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).ray_cast(inv@Vector((13,-5.17,z)),inv.to_3x3()@Vector((1,0,0)),distance=2)
        except RuntimeError:continue
        if hit:
            world=o.matrix_world@p
            if 13.7<world.x<14.5:hits.append((o.name,round(world.x,4)))
    print('DOOR_ALL_HITS',z,hits,flush=True)
