import sys,json,math,re
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood';OUT=W/'vaso_fivem'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from szio.gta5 import *
from szio.gta5.bounds import *
from szio.gta5.entities import *
from szio.gta5.maps import *
from szio.types import Vector,Quaternion
spec=json.loads((W/'vaso_planta_autoral.json').read_text());name=spec['model'];origin=np.array(json.loads((W/'medidas_estudo.json').read_text())['native_origin']);targets=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
names=re.findall(r'CollisionMaterialDef\("([A-Z_0-9]+)"',Path(r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/sollumz/Sollumz/ybn/collision_materials.py').read_text())
b=AssetBoundBvh();b.margin=.002;b.composite_collision_type_flags=CollisionFlags.MAP_TYPE_WEAPON|CollisionFlags.MAP_TYPE_MOVER|CollisionFlags.MAP_TYPE_HORSE|CollisionFlags.MAP_TYPE_COVER|CollisionFlags.MAP_TYPE_VEHICLE;b.composite_collision_include_flags=CollisionFlags(0xffffffff)
ps=[];faces=[];N=20
for z,r in [(0,.237),(.14,.302),(.34,.331),(.51,.319),(.632,.290)]:
 for i in range(N):a=i/N*2*math.pi;ps.append((r*math.cos(a),r*math.sin(a),z))
for k in range(4):
 for i in range(N):
  a=k*N+i;c=k*N+(i+1)%N;d=a+N;e=c+N;faces.extend([(a,c,e),(a,e,d)])
ps.extend([(0,0,0),(0,0,.632)])
for i in range(N):faces.extend([(100,(i+1)%N,i),(101,80+i,80+(i+1)%N)])
b.geometry_vertices=[BoundVertex(Vector(p),None) for p in ps];b.geometry_primitives=[BoundPrimitive.new_triangle(*f,CollisionMaterial.from_packed(names.index('CONCRETE'))) for f in faces]
mn=np.array(ps).min(0);mx=np.array(ps).max(0);b.bb_min=Vector(mn);b.bb_max=Vector(mx);b.centroid=Vector((mn+mx)/2);b.cg=b.centroid;b.radius_around_centroid=float(np.linalg.norm(mx-mn)/2)
comp=AssetBoundComposite(children=[b]);comp.bb_min=b.bb_min;comp.bb_max=b.bb_max;comp.centroid=b.centroid;comp.cg=b.cg;comp.radius_around_centroid=b.radius_around_centroid
a=try_load_asset(OUT/(name+'.ydr'));a.bounds=comp
for lod in a.models.values():
 for m in lod:
  for g in m.geometries:
   vb=g.vertex_buffer.copy()
   if 'Tangent' in vb.dtype.names:
    bad=np.flatnonzero(np.linalg.norm(vb['Tangent'][:,:3],axis=1)<.5)
    if len(bad):
     n=vb['Normal'][bad];axis=np.eye(3)[np.argmin(abs(n),axis=1)];tan=np.cross(axis,n);tan/=np.linalg.norm(tan,axis=1,keepdims=True);vb['Tangent'][bad,:3]=tan;vb['Tangent'][bad,3]=1.;g.vertex_buffer=vb
save_asset(a,targets,OUT,name)
lo=np.array(spec['lo']);hi=np.array(spec['hi']);ar=Archetype(name,ArchetypeType.BASE,32,120,0,120,'','','',name,Vector(lo),Vector(hi),Vector((lo+hi)/2),float(np.linalg.norm(hi-lo)/2),name,ArchetypeAssetType.DRAWABLE,[])
save_asset(AssetMapTypes(name='mansao_vasos_autorais',archetypes=[ar]),targets,OUT,'mansao_vasos_autorais')
spec['origin']=origin.tolist();spec['instances']=[dict(name='Vaso autoral sala',position=[-7.65,-2.45,-.8],heading=0),dict(name='Vaso autoral hall escada',position=[4.9,.4,-.8],heading=math.radians(26))]
entities=[];ext=[]
for q in spec['instances']:
 p=np.array(q['position']);h=q['heading'];q['quaternion']=[math.cos(h/2),0,0,-math.sin(h/2)]
 entities.append(Entity(name,Vector(origin+p),Quaternion(q['quaternion']),1,1,EntityFlags.IS_STATIC,0,-1,120,0,EntityLodLevel.ORPHANHD,EntityPriorityLevel.REQUIRED,0,255,255,0,[]));ext.extend([origin+p+lo,origin+p+hi])
save_asset(AssetMapData(name='mansao_vasos_autorais',content_flags=MapContentFlags.HAS_ENTITIES_HD|MapContentFlags.HAS_PHYSICS,entities=entities,streaming_extents=(Vector(origin-140),Vector(origin+140)),entities_extents=(Vector(np.array(ext).min(0)-.5),Vector(np.array(ext).max(0)+.5))),targets,OUT,'mansao_vasos_autorais')
spec['collision_triangles']=len(faces);spec['collision_only_pot']=True;(W/'vaso_planta_autoral.json').write_text(json.dumps(spec,indent=2),encoding='utf-8')
print('CUSTOM_PLANTS_PACKAGED',len(entities),'instances;',len(faces),'pot collision triangles',flush=True)
