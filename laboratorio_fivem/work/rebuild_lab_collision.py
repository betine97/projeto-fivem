"""Replace broad invisible rack blockers with collision on the visible equipment."""
import sys,json,numpy as np
from pathlib import Path
sys.path.insert(0,r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
from szio.gta5 import try_load_asset,save_asset,AssetTarget,AssetFormat,AssetVersion
from szio.gta5.bounds import AssetBoundBvh,AssetBoundComposite,BoundVertex,BoundPrimitive,CollisionFlags,CollisionMaterial
from szio.gta5.drawables import LodLevel
from szio.types import Vector

w=Path(__file__).resolve().parent;root=w.parent
path=root/'collisions.json';boxes=json.loads(path.read_text())
broad=[b for b in boxes if abs(b['loc'][0])==2.475 and b['dims'][1]==7.4 and b['dims'][2]==2.3]
boxes=[b for b in boxes if b not in broad]
for box in boxes:
 # Match the visible slab after lifting it clear of the native terrain.
 if abs(box['loc'][2]+.1)<.001 and abs(box['dims'][2]-.2)<.001:
  box['loc'][2]=-.075
equipment=[
 ('Tambor verde', [3.10,3.91,.49],[.58,.58,.98]),
 ('Unidade de bombeamento', [2.52,3.78,.16],[.40,.30,.32]),
 ('Tambor verde esquerdo',[-3.10,3.91,.49],[.58,.58,.98]),
 ('Unidade de bombeamento esquerda',[-2.52,3.78,.16],[.40,.30,.32]),
 ('Balde', [2.60,4.48,.20],[.36,.38,.40]),
 ('Reservatorio azul',[-3.08,5.08,.86],[1.10,1.10,1.62]),
 ('Armario tecnico',[-1.55,5.42,.49],[.84,.67,.92]),
 ('Bancada tecnica',[1.70,5.27,.50],[1.58,.70,1.00]),
 ('Estante tecnica',[3.24,5.28,.95],[1.04,.70,1.90]),
]
for name,loc,dims in equipment:
 if not any(b.get('name')==name for b in boxes):boxes.append({'name':name,'loc':loc,'dims':dims})
path.write_text(json.dumps(boxes,indent=2))

b=AssetBoundBvh();b.composite_collision_type_flags=CollisionFlags.MAP_TYPE_MOVER|CollisionFlags.MAP_TYPE_WEAPON
b.composite_collision_include_flags=CollisionFlags(0xffffffff)
mat=CollisionMaterial.from_packed(1)
for entry in boxes+[{'name':'Piso principal','loc':[0,0,-.15],'dims':[8,12,.2]}]:
 c=np.array(entry['loc']);d=np.array(entry['dims'])/2;off=len(b.geometry_vertices)
 b.geometry_vertices.extend(BoundVertex(Vector(c+d*np.array(v)),None) for v in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)])
 for a,z,c1 in [(0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),(1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)]:
  b.geometry_primitives.append(BoundPrimitive.new_triangle(off+a,off+z,off+c1,mat))
# Use the authored rack triangles themselves. This keeps posts, trays and rails
# solid without reintroducing the wide invisible boxes that blocked the aisle.
rack=try_load_asset(root.parent/'server-data/resources/cidade_laboratorio/stream/lab_racks.ydr')
rack_triangles=0
for model in rack.models[LodLevel.HIGH]:
 for g in model.geometries:
  if g.shader_index!=0:continue # Fabric is visual; preserve the walkable aisle.
  xyz=np.asarray(g.vertex_buffer['Position']);off=len(b.geometry_vertices)
  b.geometry_vertices.extend(BoundVertex(Vector(p),None) for p in xyz)
  for i,j,k in g.index_buffer.reshape(-1,3):
   b.geometry_primitives.append(BoundPrimitive.new_triangle(off+int(i),off+int(j),off+int(k),mat));rack_triangles+=1
xyz=np.array([v.co for v in b.geometry_vertices]);lo=xyz.min(0);hi=xyz.max(0)
b.bb_min=Vector(lo);b.bb_max=Vector(hi);b.centroid=Vector((lo+hi)/2);b.cg=b.centroid
b.radius_around_centroid=float(np.linalg.norm(hi-lo)/2);b.margin=.005
comp=AssetBoundComposite(children=[b]);comp.bb_min=b.bb_min;comp.bb_max=b.bb_max
comp.centroid=b.centroid;comp.cg=b.cg;comp.radius_around_centroid=b.radius_around_centroid
src=root.parent/'server-data/resources/cidade_laboratorio/stream/lab_estrutura.ydr'
a=try_load_asset(src);a.bounds=comp
out=root/'collision_fix';out.mkdir(exist_ok=True)
save_asset(a,(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),),out,'lab_estrutura')
check=try_load_asset(out/'lab_estrutura.ydr')
assert len(check.bounds.children[0].geometry_primitives)==len(b.geometry_primitives)
print('COLLISION_OK',len(boxes),'proxies',len(equipment),'equipment',rack_triangles,'rack_triangles',flush=True)
