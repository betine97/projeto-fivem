import bpy,bmesh,json
from pathlib import Path
W=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(W/'mansao_encaixada.blend'))
rows=[]
for c in bpy.data.collections:
 if not c.name.startswith(('01_','02_','03_','04_','05_','06_')):continue
 for ob in c.objects:
  if ob.type!='MESH':continue
  ps=[ob.matrix_world@v.co for v in ob.data.vertices]
  low=[min(p[i] for p in ps) for i in range(3)];high=[max(p[i] for p in ps) for i in range(3)]
  bm=bmesh.new();bm.from_mesh(ob.data);bm.transform(ob.matrix_world);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00001)
  bm.normal_update();vol=bm.calc_volume(signed=True)
  row=dict(name=ob.name,collection=c.name,lo=low,hi=high,dimensions=[b-a for a,b in zip(low,high)],faces=len(bm.faces),open_edges=sum(e.is_boundary for e in bm.edges),nonmanifold_edges=sum(not e.is_manifold for e in bm.edges),signed_volume_m3=vol,modifiers=[m.type for m in ob.modifiers])
  rows.append(row);bm.free()
(W/'audit_volumes_antes_espessuras.json').write_text(json.dumps(rows,indent=2))
for q in rows:
 if q['collection'].startswith(('02_','03_')) or q['name'].startswith(('Laje superior','Escada chegada','Piso terreo')):
  print(q['name'],[round(x,5) for x in q['dimensions']], 'open',q['open_edges'],'nonmanifold',q['nonmanifold_edges'],'volume',round(q['signed_volume_m3'],5),flush=True)
