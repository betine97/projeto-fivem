import bpy,json
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parent.parent
bpy.ops.wm.open_mainfile(filepath=str(root/'jeep_importado.blend'))
o=next(o for o in bpy.data.objects if o.type=='MESH');m=o.data
parent=list(range(len(m.vertices)))
def find(a):
 while parent[a]!=a:parent[a]=parent[parent[a]];a=parent[a]
 return a
for e in m.edges:parent[find(e.vertices[0])]=find(e.vertices[1])
groups={}
for v in m.vertices:groups.setdefault(find(v.index),[]).append(o.matrix_world@v.co)
for pts in sorted(groups.values(),key=len,reverse=True)[:25]:print('COMPONENT',len(pts),[[round(fn(v[i] for v in pts),3) for i in range(3)] for fn in [min,max]])
pts=[o.matrix_world@v.co for v in m.vertices]
for side in [-1,1]:
 for end in [-1,1]:
  p=[v for v in pts if v.y*side>.45 and v.x*end>.4 and v.z<.20]
  print('WHEEL_BOUND',side,end,[[round(fn(v[i] for v in p),3) for i in range(3)] for fn in [min,max]])

