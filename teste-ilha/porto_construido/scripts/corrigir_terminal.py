"""Make terminal roof rotations local to each roof panel, then refresh port caches."""
import bpy,numpy as np,json,math,sys
from pathlib import Path
from mathutils import Vector
O=Path(__file__).resolve().parents[1];sys.path.insert(0,str(O/'scripts'));from cache_blender import extract
bpy.ops.wm.open_mainfile(filepath=str(O/'ilha_porto_esperanca.blend'));s=bpy.context.scene
for o in bpy.data.collections['11_CAIS_TERMINAL_PRACA_E_PONTE'].objects:
    if o.name.startswith('Terminal telhado') and o.location.length<.01:
        angle=o.rotation_euler.copy();o.rotation_euler=(0,0,0);center=sum((v.co for v in o.data.vertices),Vector())/len(o.data.vertices)
        for v in o.data.vertices:v.co-=center
        o.location=center;o.rotation_euler=angle
    if o.name.startswith('Terminal telhado'):o.rotation_euler[0]=-math.copysign(math.radians(16),o.location.y+785)
bpy.context.view_layer.update();groups={}
objs=list(bpy.data.collections['03_CIRCULACAO'].all_objects)+list(bpy.data.collections['11_CAIS_TERMINAL_PRACA_E_PONTE'].all_objects)
for o in objs:
    if o.type!='MESH' or o.hide_render:continue
    pos=np.mean([o.matrix_world@Vector(c) for c in o.bound_box],0);key=(math.floor((pos[0]-250)/160),math.floor((pos[1]+850)/160));groups.setdefault(key,[]).append(o)
rows=[extract(objs,f'pe_porto_{i:02}') for i,(key,objs) in enumerate(sorted(groups.items()))]
(O/'dados/porto.json').write_text(json.dumps(rows,indent=2));s.camera=bpy.data.objects['Porto construido | panorama'];bpy.ops.wm.save_as_mainfile(filepath=str(O/'ilha_porto_esperanca.blend'),compress=True)
print('TERMINAL_CORRECTED',len(rows),flush=True)
