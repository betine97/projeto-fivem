import bpy,math,json
from pathlib import Path
from mathutils import Vector
from collections import Counter
bpy.ops.wm.open_mainfile(filepath=str(Path('laboratorio_fivem/work/station.blend').resolve()))
o=bpy.data.objects['ch3_08_ppbldg003.model'];u=Vector((.873294,-.487193,0));v=Vector((.487193,.873294,0))
for idx in [4,10,14]:
 ps=[o.data.vertices[i].co for p in o.data.polygons if p.material_index==idx for i in p.vertices]
 print('MAT',idx,'U',Counter(round(p.dot(u),1) for p in ps).most_common(16),'V',Counter(round(p.dot(v),1) for p in ps).most_common(16))
for i,ids in enumerate([(8630,8634),(8634,8638),(8638,8642),(8642,8646)]):
 p=o.data.polygons[ids[0]];c=p.center;bpy.ops.object.text_add(location=c+Vector((0,0,5)));t=bpy.context.object;t.data.body=str(i+1);t.data.size=2
s=bpy.context.scene;s.camera.location=(0,0,100);s.camera.rotation_euler=(0,0,0);s.camera.data.ortho_scale=100;s.render.filepath=str(Path('laboratorio_fivem/work/station_top.png').resolve());bpy.ops.render.render(write_still=True)
