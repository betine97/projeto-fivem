import sys,json,math,collections,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent;W=P.parent;R=W.parent;O=P/'stream';B=P/'baseline/stream'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(W/'work/lua_syntax_deps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from szio.gta5 import *
from szio.gta5.bounds import *
import pymateria.gta5.gen8 as g8
from luaparser import ast
from lupa import LuaRuntime
spec=json.loads((P/'spec.json').read_text());patch=json.loads((P/'patch_report.json').read_text());origin=np.array(spec['origin'])
names={q['file'] for cat in ['native_render','native_collision','occlusion','palm'] for q in patch[cat]}|{'mansao_fachada_entrada.ydr','mansao_garagem_subsolo.ydr','mansao_acesso_garagem.ybn','mansao_acesso_garagem.ytyp','mansao_acesso_garagem.ymap','mansao_tapete_urso.ydr','mansao_piano_tapetes.ytyp'}
assets={n:try_load_asset(O/n) for n in names};assert all(a is not None for a in assets.values())
report={'passed':False,'in_game_verified':False,'assets_loaded':len(names),'models':{},'checks':{}}
def visual(a,lod=LodLevel.HIGH):return np.concatenate([g.vertex_buffer['Position'][g.index_buffer.reshape(-1,3)] for m in a.models[lod] for g in m.geometries])
for name in ['mansao_fachada_entrada','mansao_garagem_subsolo']:
 a=assets[name+'.ydr'];counts=[]
 structural={i for i,s in enumerate(a.shader_group.shaders) if any(isinstance(p.value,str) and p.value in ['im_wall32','fach_creme','fach_cimento','os_ml_idwall_0005_c'] for p in s.parameters)}
 high={g.shader_index:g for m in a.models[LodLevel.HIGH] for g in m.geometries if g.shader_index in structural}
 for lod,models in a.models.items():
  count=0
  for m in models:
   for g in m.geometries:
    vb=g.vertex_buffer;ids=g.index_buffer.reshape(-1,3);assert len(ids) and ids.max()<len(vb)
    for n in vb.dtype.names:assert np.isfinite(vb[n]).all()
    ts=vb['Position'][ids];assert (np.linalg.norm(np.cross(ts[:,1]-ts[:,0],ts[:,2]-ts[:,0]),axis=1)>1e-12).all();count+=len(ids)
    if g.shader_index in structural:
     assert np.array_equal(g.vertex_buffer,high[g.shader_index].vertex_buffer) and np.array_equal(g.index_buffer,high[g.shader_index].index_buffer)
  counts.append(count)
 assert counts==sorted(counts,reverse=True)
 old=try_load_asset(B/(name+'.ydr'));assert len(a.lights)==len(old.lights)
 for lamp,prior in zip(a.lights,old.lights):
  for key in ['position','color','intensity','flags','time_flags','falloff','volume_intensity','light_type']:
   assert np.array_equal(np.asarray(getattr(lamp,key)),np.asarray(getattr(prior,key))),('Light changed',name,key)
 report['models'][name]={'triangles_by_lod':counts,'bytes':(O/(name+'.ydr')).stat().st_size}
for name in ['mansao_tapete_urso.ydr']+[q['file'] for q in patch['native_render']]:
 x=g8.Drawable.import_rsc(B/name).result;y=g8.Drawable.import_rsc(O/name).result
 assert [(s.basis_shader.hash,s.basis_material.hash) for s in x.shader_group.shaders]==[(s.basis_shader.hash,s.basis_material.hash) for s in y.shader_group.shaders]
old=try_load_asset(B/'mansao_tapete_urso.ydr');new=assets['mansao_tapete_urso.ydr']
assert old.models.keys()==new.models.keys()
for lod in old.models:
 for a,b in zip(old.models[lod],new.models[lod]):
  assert len(a.geometries)==len(b.geometries)
  for g,h in zip(a.geometries,b.geometries):
   assert np.array_equal(g.vertex_buffer,h.vertex_buffer) and np.array_equal(g.index_buffer,h.index_buffer) and g.shader_index==h.shader_index
assert len(new.bounds.children)==len(old.bounds.children)+1
head=new.bounds.children[0];assert np.array_equal(np.array([v.co for v in head.geometry_vertices]),np.array([v.co for v in old.bounds.children[0].geometry_vertices]))
lo=visual(new).reshape(-1,3).min(0);hi=visual(new).reshape(-1,3).max(0)
assert np.all(np.array(new.bounds.bb_min)[:2]<=lo[:2]+.004) and np.all(np.array(new.bounds.bb_max)[:2]>=hi[:2]-.004)
typ=next(t for t in assets['mansao_piano_tapetes.ytyp'].archetypes if t.name=='mansao_tapete_urso')
assert np.all(np.array(typ.bb_min)<=lo) and np.all(np.array(typ.bb_max)>=hi)
vertices=visual(new).reshape(-1,3);assert (np.linalg.norm(vertices-np.array(typ.bs_center),axis=1)<typ.bs_radius).all()
other_old=try_load_asset(B/'mansao_piano_tapetes.ytyp');assert [str(t) for t in other_old.archetypes if t.name!='mansao_tapete_urso']==[str(t) for t in assets['mansao_piano_tapetes.ytyp'].archetypes if t.name!='mansao_tapete_urso']

# Every unrelated road prop retains its original parent object, pose and flags.
before=try_load_asset(B/'ch2_roads.ymap');after=assets['ch2_roads.ymap'];victim=next(q['removed_lod_index'] for q in patch['palm'] if 'removed_lod_index' in q)
assert len(after.entities)==len(before.entities)-1
assert [str(e) for i,e in enumerate(before.entities) if i!=victim]==[str(e) for e in after.entities]
links=0
for row in patch['palm']:
 if row['file']=='ch2_roads.ymap':continue
 a=try_load_asset(B/row['file']);b=assets[row['file']];keep=[]
 for e in a.entities:
  if e.parent_index==victim:continue
  if e.parent_index>victim:e.parent_index-=1;links+=1
  keep.append(e)
 assert [str(e) for e in keep]==[str(e) for e in b.entities]
 assert all(e.parent_index<len(after.entities) for e in b.entities)

boxfaces=[(0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),(1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)]
signs=np.array([(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)])
def physical(b,offset,parent=np.eye(4)):
 tx=np.asarray(b.composite_transform)@parent;tri=[]
 for c in getattr(b,'children',[]):tri.extend(physical(c,offset,tx))
 if hasattr(b,'geometry_primitives'):
  vs=np.array([v.co for v in b.geometry_vertices]);vs=(np.c_[vs,np.ones(len(vs))]@tx)[:,:3]+offset
  for t in b.geometry_primitives:
   v=vs[list(t.vertices)]
   if t.primitive_type==BoundPrimitiveType.TRIANGLE:tri.append(v)
   elif t.primitive_type==BoundPrimitiveType.BOX:
    v1,v2,v3,v4=v;center=v.mean(0);e=((v3+v4)-(v1+v2))*.5;edges=np.array([e,v3-e-v1,v4-e-v1])
    if np.linalg.det(edges)<0:edges=edges[[0,2,1]]
    corners=center+signs@edges*.5;tri.extend(corners[list(f)] for f in boxfaces)
 return tri
physics=[]
for f in sorted(B.glob('*ch2_09b_[0-3].ybn')):
 if f.name.startswith(('ch2_','hi@ch2_')):physics.extend(physical(assets.get(f.name) or try_load_asset(f),-origin))
for name in ['mansao_fachada_entrada','mansao_garagem_subsolo']:physics.extend(physical(assets[name+'.ydr'].bounds,np.zeros(3)))
physics.extend(physical(try_load_asset(R/'server-data/resources/cidade_mansao/stream/mansao_paredes.ydr').bounds,np.zeros(3)))
physics.extend(physical(try_load_asset(R/'server-data/resources/cidade_mansao/stream/cidade_mansao.ybn'),-origin))
vt=np.concatenate([visual(assets[n+'.ydr']) for n in ['mansao_fachada_entrada','mansao_garagem_subsolo']]);pt=np.array(physics)
def intersections(p,q,ts,front=False):
 p=np.array(p);d=np.array(q)-p;v=ts[:,0];e1=ts[:,1]-v;e2=ts[:,2]-v;h=np.cross(np.broadcast_to(d,e2.shape),e2);det=np.einsum('ij,ij->i',e1,h);safe=det>1e-7 if front else abs(det)>1e-7;inv=1/np.where(safe,det,1);r=p-v;u=np.einsum('ij,ij->i',r,h)*inv;s=np.cross(r,e1);w=np.einsum('j,ij->i',d,s)*inv;t=np.einsum('ij,ij->i',e2,s)*inv;keep=safe&(u>=-1e-5)&(w>=-1e-5)&(u+w<=1.00001)&(t>=0)&(t<=1)
 return p+t[keep,None]*d
def edge(x):return 16.235+.173*x
def rampz(x,t):
 a=.12;s=t*t/(2*a*(1-a)) if t<a else 1-(1-t)**2/(2*a*(1-a)) if t>1-a else (t-a/2)/(1-a)
 return -4.20+(-3.0606-(x-6.4)*.1126+4.20)*s
rays=0
for x in [7.,8.,9.6,11.2,12.2]:
 for t in np.linspace(.012,.99,40):
  y=9.55+(edge(x)-9.55)*t;z=rampz(x,t)
  h=intersections([x,y,z+.10],[x,y,z-.12],pt);assert len(h) and abs(h[:,2].max()-z)<.025,('Ramp surface',x,t,h)
  assert not len(intersections([x,y,z+.25],[x,y,z+2.65],pt)),('Vehicle clearance',x,t)
  rays+=2
for x0,x1 in [(6.13,6.40),(12.80,13.08)]:
 x=(x0+x1)/2
 for t in np.linspace(.01,.99,45):
  y=9.55+(edge(x)-9.55)*t;bottom=rampz(x,t)-.25;top=-.47-.775*t
  for z in [bottom+.025,(bottom+top)/2,-1.55]:
   for start,end in [([x0-.1,y,z],[x1+.1,y,z]),([x1+.1,y,z],[x0-.1,y,z])]:
    assert len(intersections(start,end,vt,True)),('Open garage side',x,t,z)
    rays+=1
for x0,x1 in [(3.47,3.64),(5.85,6.145)]:
 x=(x0+x1)/2
 for y in np.linspace(12.4,edge(x)-.025,60):
  for z in [-3.15,-2.25,-1.56]:
   for start,end in [([x0-.05,y,z],[x1+.05,y,z]),([x1+.05,y,z],[x0-.05,y,z])]:
    assert len(intersections(start,end,vt,True)),('Open stair side',x,y,z)
    rays+=1
for x in [6.26,12.94]:
 for y in [14.6,14.8,15.1]:
  x0,x1=(6.10,6.44) if x<7 else (12.76,13.12)
  for a,b in [([x0,y,-.87],[x1,y,-.87]),([x1,y,-.87],[x0,y,-.87])]:
   assert len(intersections(a,b,vt,True)),('Upper garden grade exposed',x,y);rays+=1
for x,y0,y1,top in [(3.30,14.59,15.10,-.166),(3.47,16.30,16.81,-1.175),(13.08,14.59,15.10,-.166),(13.08,17.98,18.46,-1.175)]:
 for y in np.linspace(y0+.01,y1-.01,4):
  for z in [top-.02,top-.25]:
   for a,b in [([x-.025,y,z],[x+.025,y,z]),([x+.025,y,z],[x-.025,y,z])]:
    assert len(intersections(a,b,vt,True)),('Open native wall end',x,y,z);rays+=1
for i in range(1,14):
 x=4.745;y=edge(x)-.30-(i-.5)*.30;t=i/13;z=(-2.7435-(x-3.64)*.1145)*(1-t)-.8*t
 h=intersections([x,y,z+.1],[x,y,z-.2],pt);assert len(h) and abs(h[:,2].max()-z)<.012,('Stair traversal',i,h);rays+=1
for x in [3.85,4.745,5.5]:
 for y in [11.9,12.10,12.30,12.50,12.7]:
  assert not len(intersections([x,y,-.55],[x,y,1.05],pt)),('Old railing blocks arrival',x,y)
  h=intersections([x,y,-.65],[x,y,-1.2],pt);assert len(h) and abs(h[:,2].max()+.8)<.12,('Arrival floor',x,y,h)
  rays+=2
for name in spec['models'][:2]:
 for q in spec['collision_meshes'][name]:
  vs=np.array(q['vertices']);assert (vs[:,1]-.173*vs[:,0]<=16.26).all(),('Architecture reaches street',q['name'])
  ts=vs[np.array(q['triangles'])];coords=np.round(ts,5);counts=collections.Counter(tuple(sorted((tuple(t[i]),tuple(t[(i+1)%3])))) for t in coords for i in range(3));assert all(n==2 for n in counts.values()),('Open solid mesh',q['name'])

# Execute the real streaming client: moving around the room must never delete
# the rug; leaving the mansion unloads it, and returning restores its settings.
catalog=json.loads((P/'objetos_catalogo.json').read_text());ast.parse((P/'objetos_client.lua').read_text())
lua=LuaRuntime(unpack_returned_tuples=True);g=lua.globals();g.decode=lambda _:lua.table_from(catalog,recursive=True)
lua.execute('''json={decode=decode,encode=function(_) return 'status' end};source=65535;events={};commands={};threads={};pool={};created=0;deleted=0;prerender={};lods={};now=1000;ped={x=0,y=0,z=0}
function GetCurrentResourceName() return 'cidade_mansao' end
function LoadResourceFile(...) return 'catalog' end
function GetHashKey(x) return x end
function RegisterNetEvent(n,f) events[n]=f end
function AddEventHandler(...) end
function RegisterCommand(n,f,...) commands[n]=f end
function RegisterKeyMapping(...) end
function CreateThread(f) threads[#threads+1]=coroutine.create(f) end
function Wait(ms) coroutine.yield(ms) end
function PlayerPedId() return 1 end
function GetGameTimer() return now end
function GetEntityCoords(e) return e==1 and ped or pool[e] end
function DoesEntityExist(e) return pool[e]~=nil end
function RequestModel(...) end
function HasModelLoaded(...) return true end
function CreateObjectNoOffset(m,x,y,z,...) created=created+1;local e=created+10;pool[e]={x=x,y=y,z=z};return e end
function SetEntityAsMissionEntity(...) end
function FreezeEntityPosition(...) end
function SetEntityCoordsNoOffset(e,x,y,z,...) pool[e]={x=x,y=y,z=z} end
function SetEntityMatrix(...) end
function SetEntityCollision(...) end
function SetEntityLodDist(e,d) lods[e]=d end
function SetEntityAlwaysPrerender(e,active) prerender[e]=active end
function SetModelAsNoLongerNeeded(...) end
function SetEntityDrawOutline(...) end
function DeleteEntity(e) pool[e]=nil;deleted=deleted+1 end
function IsEntityVisible(...) return true end
function IsEntityOnScreen(...) return true end
function IsEntityOccluded(...) return false end
function GetEntityAlpha(...) return 255 end
function GetModelDimensions(...) return {x=-1.9,y=-1.4,z=0},{x=1.9,y=1.4,z=.25} end
function step() local ok,err=coroutine.resume(threads[1]);if not ok then error(err) end end''')
lua.execute((R/'server-data/resources/cidade_mansao/objetos_shared.lua').read_text())
lua.execute((P/'objetos_client.lua').read_text())
d=next(q for q in catalog['objects'] if q['model']=='mansao_tapete_urso');ident=d['id'];pos=d['p']
g.events['cidade:objetos:snapshot'](lua.table_from({ident:d},recursive=True),lua.table_from({ident:{'p':pos,'h':d['h']}},recursive=True),lua.table())
for i in range(72):
 angle=i/72*math.tau;g.ped=lua.table_from(dict(zip(['x','y','z'],[pos[0]+12*math.cos(angle),pos[1]+12*math.sin(angle),pos[2]])));g.now+=300;g.step()
 assert g.created==1 and g.deleted==0
assert g.prerender[11] is True and g.lods[11]==220
g.commands['tapeteursodebug']()
g.ped=lua.table_from(dict(zip(['x','y','z'],[pos[0]+200,pos[1],pos[2]])));g.now+=300;g.step();assert g.deleted==1
g.ped=lua.table_from(dict(zip(['x','y','z'],pos)));g.now+=300;g.step();assert g.created==2 and g.deleted==1 and g.prerender[12] is True
report['checks']={'closed_side_and_driveway_rays':rays,'structural_shells_retained_all_lods':True,'solid_parts_watertight':True,'vehicle_and_pedestrian_clearance':True,'architecture_within_curb':True,'single_palm_removed_hd_and_lod':True,'unrelated_parent_links_preserved':links,'rug_visual_vertices_uvs_textures_unchanged':True,'rug_full_silhouette_collider':True,'rug_walkable_collider_height_m':.012,'rug_client_positions_tested':72,'rug_reload_preserves_render_settings':True,'lighting_preserved':True}
report['passed']=True;report['install_files']=sorted(['stream/'+n for n in names]+['objetos_client.lua','objetos_catalogo.json'])
(P/'verification.json').write_text(json.dumps(report,indent=2));print('REPAIR_VERIFIED',report['checks'],flush=True)
