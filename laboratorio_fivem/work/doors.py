import bpy,json,sys
from pathlib import Path
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath=str(Path('laboratorio_fivem/work/station.blend').resolve()))
o=bpy.data.objects['ch3_08_ppbldg003.model']
for p in o.data.polygons:
 if p.material_index==13:print(p.index,'center',list(p.center),'normal',list(p.normal),'verts',[list(o.data.vertices[v].co) for v in p.vertices])
