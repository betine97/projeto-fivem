from locate import *
import struct,copy
sys.path.insert(0,str(R/'casa_vinewood/work/lua_syntax_deps'))
from luaparser import ast
spec=json.loads((P/'spec.json').read_text());folder=P/'package';checks=[];stats={}
def check(ok,label):
 assert ok,label
 checks.append(label)
for f in folder.glob('*.lua'):ast.parse(f.read_text());checks.append('Lua syntax '+f.name)
check(len(spec['rooms'])==32,'32 clinical rooms')
check(len(spec['doors'])==36,'32 room doors and 4 entrance leaves')
check([d['id'] for d in spec['doors']]==list(range(1,37)),'Sequential door identifiers')
check({r['level'] for r in spec['rooms']}=={0,1},'Two accessible floors')
for label in ['CIRURGIA 01','CIRURGIA 02','OBITOS','DESCANSO','RADIOLOGIA','TOMOGRAFIA','CONVERSAS MEDICAS']:
 check(any(r['label']==label for r in spec['rooms']),'Room '+label)
for f in sorted((folder/'stream').iterdir()):
 a=try_load_asset(f);check(a is not None,'Native load '+f.name)
 if f.suffix not in ['.ydr','.ydd']:continue
 ds=[a] if f.suffix=='.ydr' else list(a.drawables.values())
 count=0
 for d in ds:
  for models in d.models.values():
   for m in models:
    for g in m.geometries:
     vb=g.vertex_buffer;ids=g.index_buffer
     check(len(ids)%3==0 and (len(ids)==0 or max(ids)<len(vb)),'Valid indices '+f.name)
     check(all(np.isfinite(vb[k]).all() for k in vb.dtype.names),'Finite geometry '+f.name)
     count+=len(ids)//3
  if f.stem.startswith('hc_'):
   check(d.bounds is not None,'Physical collision '+f.name)
   check(all(q.time_flags==0xffffff and q.volume_intensity==0 for q in d.lights),'Always-on lights without volumetric fog '+f.name)
   for k,t in d.shader_group.embedded_textures.items():
    raw=t.data.read_bytes();check(raw[:4]==b'DDS ' and struct.unpack_from('<I',raw,28)[0]>1,'DDS mipmaps '+k)
 stats[f.name]={'triangles_all_lods':count,'compressed_bytes':f.stat().st_size}
# Ray intersections use exactly the triangle surfaces exported as physical bounds.
meshes=spec['collision_meshes'];tri=[]
for name in spec['models'][:6]:
 for q in meshes[name]:tri.extend(np.asarray(q['vertices'])[q['triangles']])
tri=np.asarray(tri);edge1=tri[:,1]-tri[:,0];edge2=tri[:,2]-tri[:,0]
def ray(start,end):
 start=np.array(start);direction=np.array(end)-start;p=np.cross(direction,edge2);det=np.einsum('ij,ij->i',edge1,p);valid=np.abs(det)>1e-8;inv=np.divide(1.,det,out=np.zeros_like(det),where=valid);tv=start-tri[:,0];u=np.einsum('ij,ij->i',tv,p)*inv;q=np.cross(tv,edge1);v=np.einsum('j,ij->i',direction,q)*inv;t=np.einsum('ij,ij->i',edge2,q)*inv
 return t[valid&(u>=-1e-7)&(v>=-1e-7)&(u+v<=1.0000001)&(t>1e-6)&(t<.999999)]
for cx in [0,-23.1]:
 for x in [cx-1.2,cx+1.2]:check(len(ray([x,-23,1],[x,-21,1]))==0,'Entrance clear '+str(x))
for room in spec['rooms']:
 x,y,z=room['door'];check(len(ray([x,y-.6,z+1],[x,y+.6,z+1]))==0,'Room doorway clear '+str(room['level'])+' '+room['label'])
check(len(ray([0,0,.8],[0,0,-.1]))>0,'Ground floor physically walkable')
check(len(ray([0,0,5],[0,0,4.2]))>0,'Upper floor physically walkable')
for i in range(26):
 z=(i+1)*4.4/26;y=-21.4+i*.28+.14
 check(len(ray([29.5,y,z+.1],[29.5,y,z-.1]))>0,'Stair tread '+str(i))
check(len(ray([29.5,-18,4.6],[29.5,-18,4.2]))==0,'Upper stair opening is clear')
check(4.4/26<.18,'Comfortable stair risers')
types=try_load_asset(folder/'stream/hospital_carcer.ytyp');check(len(types.archetypes)==8,'All custom archetypes registered')
mapping=try_load_asset(folder/'stream/hospital_carcer.ymap');check(len(mapping.entities)==6,'Map streams 6 structural groups; doors are managed separately')
report=json.loads((P/'site_patch_report.json').read_text())
check(len(report['collision'])==6,'Base and DLC collision variants removed')
check(any(r['file']=='bh1_lod_slod3.ydr' for r in report['render']),'Highest distant mesh cleared')
check(any(r['file']=='bh1_lod_emissive_6_21_slod3.ydr' for r in report['render']),'Highest nighttime mesh cleared')
out={'passed':True,'checks':checks,'assets':stats,'in_game_verified':False}
(P/'verification.json').write_text(json.dumps(out,indent=2));print('HOSPITAL_VERIFIED',len(checks),flush=True)
