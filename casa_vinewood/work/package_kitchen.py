import sys,json,math,re,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood';OUT=W/'cozinha_fivem';SERVER=R/'server-data/resources/cidade_mansao'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from szio.gta5 import *
from szio.gta5.bounds import *
from szio.gta5.entities import *
from szio.gta5.maps import *
from szio.types import Vector,Quaternion
spec=json.loads((W/'cozinha_completa.json').read_text());name=spec['model'];origin=np.array(json.loads((W/'medidas_estudo.json').read_text())['native_origin']);targets=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
def world(p):u,v,h=p;return np.array([13.534+v,-6.6-u,-.8+h])
names=re.findall(r'CollisionMaterialDef\("([A-Z_0-9]+)"',Path(r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/sollumz/Sollumz/ybn/collision_materials.py').read_text())
b=AssetBoundBvh();b.margin=.002;b.composite_collision_type_flags=CollisionFlags.MAP_TYPE_WEAPON|CollisionFlags.MAP_TYPE_MOVER|CollisionFlags.MAP_TYPE_HORSE|CollisionFlags.MAP_TYPE_COVER|CollisionFlags.MAP_TYPE_VEHICLE;b.composite_collision_include_flags=CollisionFlags(0xffffffff)
ps=[];faces=[]
for q in spec['collision_boxes']:
 x,y,z=q['lo'];X,Y,Z=q['hi'];offset=len(ps);ps.extend([world(p) for p in [(x,y,z),(X,y,z),(X,Y,z),(x,Y,z),(x,y,Z),(X,y,Z),(X,Y,Z),(x,Y,Z)]])
 fs=[(0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),(1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)];faces.extend([tuple(i+offset for i in f) for f in fs])
b.geometry_vertices=[BoundVertex(Vector(p),None) for p in ps];b.geometry_primitives=[BoundPrimitive.new_triangle(*f,CollisionMaterial.from_packed(names.index('WOOD_SOLID_MEDIUM'))) for f in faces]
mn=np.array(ps).min(0);mx=np.array(ps).max(0);b.bb_min=Vector(mn);b.bb_max=Vector(mx);b.centroid=Vector((mn+mx)/2);b.cg=b.centroid;b.radius_around_centroid=float(np.linalg.norm(mx-mn)/2)
comp=AssetBoundComposite(children=[b]);comp.bb_min=b.bb_min;comp.bb_max=b.bb_max;comp.centroid=b.centroid;comp.cg=b.cg;comp.radius_around_centroid=b.radius_around_centroid
a=try_load_asset(OUT/(name+'.ydr'));a.bounds=comp;removed=0;actual_triangles=0
for lod in a.models.values():
 for m in lod:
  for g in m.geometries:
   vb=g.vertex_buffer.copy();ids=g.index_buffer.reshape(-1,3);ts=vb['Position'][ids];area=np.linalg.norm(np.cross(ts[:,1]-ts[:,0],ts[:,2]-ts[:,0]),axis=1)*.5;keep=area>1e-11
   removed+=int(np.sum(~keep));actual_triangles+=int(np.sum(keep));g.index_buffer=ids[keep].reshape(-1).copy()
   if 'Tangent' in vb.dtype.names:
    bad=np.flatnonzero(np.linalg.norm(vb['Tangent'][:,:3],axis=1)<.5)
    if len(bad):
     n=vb['Normal'][bad];axis=np.eye(3)[np.argmin(abs(n),axis=1)];tan=np.cross(axis,n);tan/=np.linalg.norm(tan,axis=1,keepdims=True);vb['Tangent'][bad,:3]=tan;vb['Tangent'][bad,3]=1.;g.vertex_buffer=vb
save_asset(a,targets,OUT,name);spec['authored_triangles']=spec['triangles'];spec['triangles']=actual_triangles;spec['removed_zero_area_export_triangles']=removed
lo=np.array(spec['lo']);hi=np.array(spec['hi']);ar=Archetype(name,ArchetypeType.BASE,32,160,0,160,'','','',name,Vector(lo),Vector(hi),Vector((lo+hi)/2),float(np.linalg.norm(hi-lo)/2),name,ArchetypeAssetType.DRAWABLE,[])
save_asset(AssetMapTypes(name='mansao_cozinha_completa',archetypes=[ar]),targets,OUT,'mansao_cozinha_completa')
plantpos=world([4.92,.44,.913]);spec['counter_plant']={'model':'mansao_vaso_folhagem','position':plantpos.tolist(),'scale':.20}
entities=[Entity(name,Vector(origin),Quaternion((1,0,0,0)),1,1,EntityFlags.IS_STATIC,0,-1,160,0,EntityLodLevel.ORPHANHD,EntityPriorityLevel.REQUIRED,0,255,255,0,[]),Entity('mansao_vaso_folhagem',Vector(origin+plantpos),Quaternion((1,0,0,0)),.20,.20,EntityFlags.IS_STATIC,0,-1,120,0,EntityLodLevel.ORPHANHD,EntityPriorityLevel.REQUIRED,0,255,255,0,[])]
save_asset(AssetMapData(name='mansao_cozinha_completa',content_flags=MapContentFlags.HAS_ENTITIES_HD|MapContentFlags.HAS_PHYSICS,entities=entities,streaming_extents=(Vector(origin+lo-170),Vector(origin+hi+170)),entities_extents=(Vector(origin+lo-.5),Vector(origin+hi+.5))),targets,OUT,'mansao_cozinha_completa')
# Work from the currently installed map/config, preserving the other thread's optimized assets.
baseline={}
for rel in ['stream/mansao_decoracao.ymap','decoracao_iluminacao.json','iluminacao_ambiente.json']:
 baseline[rel]=hashlib.sha256((SERVER/rel).read_bytes()).hexdigest()
decor=json.loads((SERVER/'decoracao_iluminacao.json').read_text());row=next(q for q in decor['plants'] if q['name']=='Cozinha canto');old=np.array(row['position']);new=np.array([12.70,-13.40,old[2]]);delta=new-old
mapa=try_load_asset(SERVER/'stream/mansao_decoracao.ymap');idx=[i for i,e in enumerate(mapa.entities) if str(e.archetype_name)==row['model'] and np.linalg.norm(np.array(e.position)-origin-old)<.001];assert len(idx)==1,idx
mapa.entities[idx[0]].position=Vector(origin+new);save_asset(mapa,targets,OUT,'mansao_decoracao')
row['position']=new.tolist();row['footprint']=[row['footprint'][i]+delta[i%2] for i in range(4)]
(OUT/'decoracao_iluminacao.json').write_text(json.dumps(decor,indent=2),encoding='utf-8')
spec['plant_relocation']={'name':row['name'],'old':old.tolist(),'new':new.tolist(),'map_entity_index':idx[0]}
light=json.loads((SERVER/'iluminacao_ambiente.json').read_text());oldlights=[q for q in light['lights'] if not q['id'].startswith('kitchen_led_')];leds=[]
for j,u in enumerate([1.14,2.18,3.22,4.26,5.05]):leds.append({'id':'kitchen_led_'+str(j+1),'kind':'fixture','level':'terreo','position':world([u,.40,1.55]).tolist(),'rgb':[255,211,153],'range':1.35,'intensity':.50})
light['lights']=oldlights+leds
(OUT/'iluminacao_ambiente.json').write_text(json.dumps(light,indent=2),encoding='utf-8');spec['led_lights']=leds;spec['baseline_hashes']=baseline;spec['origin']=origin.tolist();spec['collision_triangles']=len(faces)
(W/'cozinha_completa.json').write_text(json.dumps(spec,indent=2),encoding='utf-8');print('KITCHEN_PACKAGED',len(entities),'entities;',len(faces),'collision triangles; existing unified lighting budget',light['max_lights'],flush=True)
