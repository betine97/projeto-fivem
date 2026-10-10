import sys,json,math,re
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood';OUT=W/'piano_tapetes_fivem'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(W/'work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from szio.gta5 import *
from szio.gta5.bounds import *
from szio.gta5.entities import *
from szio.gta5.maps import *
from szio.types import Vector,Quaternion
spec=json.loads((W/'piano_tapetes.json').read_text());origin=np.array(json.loads((W/'medidas_estudo.json').read_text())['native_origin']);targets=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
names=re.findall(r'CollisionMaterialDef\("([A-Z_0-9]+)"',Path(r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/sollumz/Sollumz/ybn/collision_materials.py').read_text())
def bound(ps,fs,material):
 b=AssetBoundBvh();b.margin=.002;b.composite_collision_type_flags=CollisionFlags.MAP_TYPE_WEAPON|CollisionFlags.MAP_TYPE_MOVER|CollisionFlags.MAP_TYPE_HORSE|CollisionFlags.MAP_TYPE_COVER|CollisionFlags.MAP_TYPE_VEHICLE;b.composite_collision_include_flags=CollisionFlags(0xffffffff)
 b.geometry_vertices=[BoundVertex(Vector(p),None) for p in ps];b.geometry_primitives=[BoundPrimitive.new_triangle(*f,CollisionMaterial.from_packed(names.index(material))) for f in fs]
 mn=np.array(ps).min(0);mx=np.array(ps).max(0);b.bb_min=Vector(mn);b.bb_max=Vector(mx);b.centroid=Vector((mn+mx)/2);b.cg=b.centroid;b.radius_around_centroid=float(np.linalg.norm(mx-mn)/2)
 c=AssetBoundComposite(children=[b]);c.bb_min=b.bb_min;c.bb_max=b.bb_max;c.centroid=b.centroid;c.cg=b.cg;c.radius_around_centroid=b.radius_around_centroid;return c
boxfaces=[(0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),(1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)]
ps=[];fs=[];piano=spec['models']['piano'];ol=piano['body_outline'];n=len(ol);ps.extend((x,y,z) for z in piano['body_height'] for x,y in ol)
# Convex fan triangles are generated from a real tessellated polygon in the source.
from shapely.geometry import Polygon
from shapely.ops import triangulate
poly=Polygon(ol);lookup={tuple(np.round(q,6)):i for i,q in enumerate(ol)}
for tri in triangulate(poly):
 if not poly.covers(tri.representative_point()):continue
 ids=[lookup[tuple(np.round(q,6))] for q in list(tri.exterior.coords)[:3]];fs.extend([tuple(reversed(ids)),tuple(i+n for i in ids)])
for i in range(n):j=(i+1)%n;fs.extend([(i,j,j+n),(i,j+n,i+n)])
def add_box(lo,hi):
 x,y,z=lo;X,Y,Z=hi;offset=len(ps);ps.extend([(x,y,z),(X,y,z),(X,Y,z),(x,Y,z),(x,y,Z),(X,y,Z),(X,Y,Z),(x,Y,Z)]);fs.extend(tuple(i+offset for i in f) for f in boxfaces)
for x,y in piano['leg_centers']:add_box((x-.08,y-.08,.003),(x+.08,y+.08,.743))
add_box((-.77,-.34,.645),(.77,.229,.90));add_box(*piano['bench_box']);add_box((-.15,-.21,.075),(.15,.14,.67))
pianocoll=bound(ps,fs,'WOOD_SOLID_MEDIUM')
# Only the raised head is rigid; the flat hide and woven rug do not obstruct walking.
bear=spec['models']['bear'];cy=bear['head_center'][1];bp=[(0,cy,.018)];bf=[];sides=20;rings=5
for j in range(1,rings+1):
 a=j/rings*math.pi/2;rx=.24*math.sin(a);ry=.285*math.sin(a);z=.016+(bear['head_height_m']-.018)*math.cos(a)
 for i in range(sides):t=i/sides*math.tau;bp.append((rx*math.cos(t),cy+ry*math.sin(t),z))
bp[0]=(0,cy,bear['head_height_m']-.002)
for i in range(sides):bf.append((0,1+i,1+(i+1)%sides))
for j in range(rings-1):
 for i in range(sides):a=1+j*sides+i;b=1+j*sides+(i+1)%sides;bf.extend([(a,b,b+sides),(a,b+sides,a+sides)])
bottom=len(bp);bp.append((0,cy,.002))
for i in range(sides):a=1+(rings-1)*sides+i;b=1+(rings-1)*sides+(i+1)%sides;bf.append((bottom,b,a))
bearcoll=bound(bp,bf,'CARPET_SOLID')
archetypes=[];entities=[];ext=[]
for family,row in spec['models'].items():
 a=try_load_asset(OUT/(row['name']+'.ydr'));a.bounds=pianocoll if family=='piano' else bearcoll if family=='bear' else None;count=0;removed=0
 for models in a.models.values():
  for m in models:
   for g in m.geometries:
    vb=g.vertex_buffer.copy();ids=g.index_buffer.reshape(-1,3);ts=vb['Position'][ids];areas=np.linalg.norm(np.cross(ts[:,1]-ts[:,0],ts[:,2]-ts[:,0]),axis=1)*.5;keep=areas>1e-11;removed+=int(np.sum(~keep));count+=int(np.sum(keep));g.index_buffer=ids[keep].reshape(-1).copy()
    if 'Tangent' in vb.dtype.names:
     bad=np.flatnonzero(np.linalg.norm(vb['Tangent'][:,:3],axis=1)<.5)
     if len(bad):
      nn=vb['Normal'][bad];axis=np.eye(3)[np.argmin(abs(nn),axis=1)];tan=np.cross(axis,nn);tan/=np.linalg.norm(tan,axis=1,keepdims=True);vb['Tangent'][bad,:3]=tan;vb['Tangent'][bad,3]=1;g.vertex_buffer=vb
 save_asset(a,targets,OUT,row['name']);row['triangles']=count;row['removed_zero_area_triangles']=removed;lo=np.array(row['lo']);hi=np.array(row['hi'])
 archetypes.append(Archetype(row['name'],ArchetypeType.BASE,32,130,0,130,'','','',row['name'],Vector(lo),Vector(hi),Vector((lo+hi)/2),float(np.linalg.norm(hi-lo)/2),row['name'],ArchetypeAssetType.DRAWABLE,[]))
 h=row['heading'];row['quaternion']=[math.cos(h/2),0,0,-math.sin(h/2)];p=origin+row['position'];entities.append(Entity(row['name'],Vector(p),Quaternion(row['quaternion']),1,1,EntityFlags.IS_STATIC,0,-1,130,0,EntityLodLevel.ORPHANHD,EntityPriorityLevel.REQUIRED,0,255,255,0,[]))
 c=math.cos(h);s=math.sin(h);rot=np.array([[c,-s,0],[s,c,0],[0,0,1]]);corners=np.array([[x,y,z] for x in (lo[0],hi[0]) for y in (lo[1],hi[1]) for z in (lo[2],hi[2])])@rot.T+p;ext.extend(corners)
save_asset(AssetMapTypes(name='mansao_piano_tapetes',archetypes=archetypes),targets,OUT,'mansao_piano_tapetes')
save_asset(AssetMapData(name='mansao_piano_tapetes',content_flags=MapContentFlags.HAS_ENTITIES_HD|MapContentFlags.HAS_PHYSICS,entities=entities,streaming_extents=(Vector(np.array(ext).min(0)-140),Vector(np.array(ext).max(0)+140)),entities_extents=(Vector(np.array(ext).min(0)-.1),Vector(np.array(ext).max(0)+.1))),targets,OUT,'mansao_piano_tapetes')
spec['origin']=origin.tolist();spec['piano_collision_triangles']=len(fs);spec['bear_head_collision_triangles']=len(bf);(W/'piano_tapetes.json').write_text(json.dumps(spec,indent=2),encoding='utf-8');print('PIANO_RUGS_PACKAGED',len(entities),'entities',flush=True)
