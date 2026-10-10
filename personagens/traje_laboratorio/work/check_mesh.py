import bpy,sys,addon_utils,json,bmesh
from pathlib import Path
sys.path[:0]=[r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps',r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\sollumz']
addon_utils.enable('Sollumz',default_set=True)
r=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(r/'TRAJE_LABORATORIO.blend'))
for n in ['MACACAO_TRONCO','MACACAO_PERNAS','LUVAS_AZUIS']:
 o=bpy.data.objects[n];bm=bmesh.new();bm.from_mesh(o.data)
 edges=[e for e in bm.edges if e.is_boundary]
 points={v for e in edges for v in e.verts};groups=[]
 while points:
  v=points.pop();group={v};queue=[v]
  while queue:
   for e in queue.pop().link_edges:
    if e in edges:
     for v in e.verts:
      if v in points:points.remove(v);group.add(v);queue.append(v)
  center=sum((v.co for v in group),__import__('mathutils').Vector())/len(group)
  groups.append((len(group),[round(v,4) for v in center]))
 print(n,'bounds',[round(min(v.co[i] for v in bm.verts),3) for i in range(3)],[round(max(v.co[i] for v in bm.verts),3) for i in range(3)],'BOUNDARY',groups)
 bm.free()
