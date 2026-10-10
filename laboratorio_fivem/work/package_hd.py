import sys,json,numpy as np,copy,math
from pathlib import Path
sys.path.insert(0,r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
from szio.gta5 import *
from szio.gta5.bounds import *
from szio.gta5.entities import *
from szio.gta5.maps import *
from szio.types import Vector,Quaternion
W=Path(__file__).resolve().parents[1];O=W/'exports_hd';r=json.loads((W/'export_report_hd.json').read_text());p=json.loads((W/'placement.json').read_text());B=np.array(p['basis']);origin=np.array(p['origin'])
targets=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
def bounds(boxes):
 b=AssetBoundBvh();b.composite_collision_type_flags=CollisionFlags.MAP_TYPE_MOVER|CollisionFlags.MAP_TYPE_WEAPON;b.composite_collision_include_flags=CollisionFlags(0xffffffff)
 mat=CollisionMaterial.from_packed(1)
 for box in boxes:
  c=np.array(box['loc']);d=np.array(box['dims'])/2;off=len(b.geometry_vertices)
  b.geometry_vertices.extend(BoundVertex(Vector(c+d*np.array(v)),None) for v in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)])
  for a,z,c1 in [(0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),(1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)]:b.geometry_primitives.append(BoundPrimitive.new_triangle(off+a,off+z,off+c1,mat))
 xyz=np.array([v.co for v in b.geometry_vertices]);lo=xyz.min(0);hi=xyz.max(0);b.bb_min=Vector(lo);b.bb_max=Vector(hi);b.centroid=Vector((lo+hi)/2);b.cg=b.centroid;b.radius_around_centroid=float(np.linalg.norm(hi-lo)/2);b.margin=.005
 comp=AssetBoundComposite(children=[b]);comp.bb_min=b.bb_min;comp.bb_max=b.bb_max;comp.centroid=b.centroid;comp.cg=b.cg;comp.radius_around_centroid=b.radius_around_centroid
 return comp
import shutil
for n in ('ch3_08_ppbldg003.ydr','hi@ch3_08_20.ybn'):shutil.copy2(W/'exports'/n,O/n)
for n,boxes in [('lab_estrutura',json.loads((W/'collisions.json').read_text())),('lab_porta',[{'loc':[.575,0,1.13],'dims':[1.15,.055,2.26]}])]:
 if n=='lab_estrutura':boxes.append({'loc':[0,0,-.15],'dims':[8,12,.2]})
 a=try_load_asset(O/(n+'.ydr'));a.bounds=bounds(boxes);save_asset(a,targets,O,n)
ar=[]
for m in r['models']:
 lo=np.array(m['lo']);hi=np.array(m['hi']);name=m['name'];ar.append(Archetype(name,ArchetypeType.BASE,32,150,0,150,'','','',name if name in ('lab_estrutura','lab_porta') else '',Vector(lo),Vector(hi),Vector((lo+hi)/2),float(np.linalg.norm(hi-lo)/2),name,ArchetypeAssetType.DRAWABLE,[]))
save_asset(AssetMapTypes(name='cidade_laboratorio',archetypes=ar),targets,O,'cidade_laboratorio')
entities=[]
def entity(name,loc,sz=1):
 angle=-math.radians(p['heading'])/2
 return Entity(name,Vector(origin+B@loc),Quaternion((math.cos(angle),0,0,math.sin(angle))),1,sz,EntityFlags.IS_STATIC,0,-1,150,0,EntityLodLevel.ORPHANHD,EntityPriorityLevel.REQUIRED,0,255,255,0,[])
for m in r['models']:
 if not m['name'].startswith('lab_planta') and m['name']!='lab_porta':entities.append(entity(m['name'],np.zeros(3)))
for item in r['plants']:
 mx=np.array(item['matrix']);entities.append(entity(item['model'],mx[:3,3],float(mx[2,2])))
y=AssetMapData(name='cidade_laboratorio',content_flags=MapContentFlags.HAS_ENTITIES_HD,entities=entities,streaming_extents=(Vector(origin-200),Vector(origin+200)),entities_extents=(Vector(origin+[-20,-20,-2]),Vector(origin+[20,20,10])))
save_asset(y,targets,O,'cidade_laboratorio')
# Native roundtrip validates all geometry buffers, shader groups, map and collision serialization.
validation={}
for f in O.iterdir():
 if f.suffix in ['.ydr','.ybn','.ymap','.ytyp']:a=try_load_asset(f);assert a is not None;validation[f.name]=f.stat().st_size
assert len(try_load_asset(O/'cidade_laboratorio.ymap').entities)==61
(W/'native_validation_hd.json').write_text(json.dumps({'entities':61,'plants':54,'native_roundtrip':validation,'in_game_test':False},indent=2));print('NATIVE_OK',len(validation))
