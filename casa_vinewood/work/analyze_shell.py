import bpy,json
from pathlib import Path
from mathutils import Vector
o=bpy.data.objects['ch2_09b_hs05.model']
r=[]
for p in o.data.polygons:
 pts=[o.matrix_world@o.data.vertices[i].co for i in p.vertices]
 if p.area>.3:
  r.append(dict(material=o.data.materials[p.material_index].name,normal=list(p.normal),area=p.area,points=[list(v) for v in pts]))
Path(__file__).with_name('shell_faces.json').write_text(json.dumps(r))
print('SHELL ANALYZED',len(r))
