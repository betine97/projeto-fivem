"""Validate native GLB furniture closure, maps, preserved architecture and clear walking routes."""
import sys,json,hashlib,io,struct
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(W/'work/lua_syntax_deps'),str(W/'work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from PIL import Image
from szio.gta5 import try_load_asset
from lupa import LuaRuntime
spec=json.loads((W/'componentes_jantar_cozinha.json').read_text());checks=[];assets={};hashes={}
def geometries(a):
 return [g for lod in a.models.values() for m in lod for g in m.geometries]
for name in ('mansao_jantar','mansao_ilha','mansao_pendentes'):
 assets[name]=try_load_asset(W/'fivem'/(name+'.ydr'));assert assets[name] is not None
 hashes[name+'.ydr']=hashlib.sha256((W/'fivem'/(name+'.ydr')).read_bytes()).hexdigest()
for family,name in [('dining','mansao_jantar'),('island','mansao_ilha'),('cylinder','mansao_pendentes'),('linear','mansao_pendentes')]:
 row=spec['assets'][family];assert hashlib.sha256(Path(row['source']).read_bytes()).hexdigest()==row['sha256']
 a=assets[name];triangles=[];zero=0;emissive=0;maps=[]
 for g in geometries(a):
  shader=a.shader_group.shaders[g.shader_index];params={p.name.lower():p.value for p in shader.parameters}
  texture=str(params['diffusesampler']);tri=g.vertex_buffer['Position'][g.index_buffer.reshape(-1,3)]
  if name=='mansao_pendentes':tri=tri[(tri.mean(1)[:,0]<5) if family=='cylinder' else (tri.mean(1)[:,0]>5)]
  if not len(tri):continue
  assert texture in (family+'_albedo','mansao_led_quente'),(family,texture)
  triangles.extend(tri)
  N=g.vertex_buffer['Normal'];assert np.isfinite(N).all() and abs(np.linalg.norm(N,axis=1)-1).max()<1e-4
  assert np.isfinite(g.vertex_buffer['TexCoord0']).all()
  if 'Tangent' in g.vertex_buffer.dtype.names:
   T=g.vertex_buffer['Tangent'];assert np.isfinite(T).all();zero+=int(sum(np.linalg.norm(T[:,:3],axis=1)<.5))
  if texture=='mansao_led_quente':
   emissive+=len(tri);assert shader.preset_filename=='emissive.sps';assert abs(float(params['emissivemultiplier'][0])-3)<1e-6
   normals=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);assert np.all(normals[:,2]<0)
  else:assert float(params['wetnessmultiplier'][0])==0 and float(params['specularintensitymult'][0])<.23
 assert zero==0,(family,zero)
 triangles=np.array(triangles);assert len(triangles)==row['triangles']
 assert np.max(abs(triangles.reshape(-1,3).min(0)-row['lo']))<1e-4
 assert np.max(abs(triangles.reshape(-1,3).max(0)-row['hi']))<1e-4
 verts,ids=np.unique(triangles.reshape(-1,3),axis=0,return_inverse=True);ids=ids.reshape(-1,3)
 edges=np.sort(np.concatenate((ids[:,[0,1]],ids[:,[1,2]],ids[:,[2,0]])),axis=1);_,counts=np.unique(edges,axis=0,return_counts=True)
 boundary=int(sum(counts==1));nonmanifold=int(sum(counts!=2));assert boundary==0 and nonmanifold==0,(family,boundary,nonmanifold)
 area=np.linalg.norm(np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0]),axis=1)*.5
 assert area.min()>1e-12,(family,float(area.min()))
 for suffix in ('albedo','normal','spec'):
  raw=a.shader_group.embedded_textures[family+'_'+suffix].data.read_bytes();im=Image.open(io.BytesIO(raw));mips=struct.unpack_from('<I',raw,28)[0]
  assert im.size==((2048,2048) if suffix=='spec' else (4096,4096))
  assert mips==int(np.log2(max(im.size)))-1
  original=Image.open(W/'work/materiais'/(family+'_'+suffix+'.dds'));assert np.array_equal(np.array(im.convert('RGBA')),np.array(original.convert('RGBA')))
  maps.append(dict(name=family+'_'+suffix,size=list(im.size),mips=mips,decoded_pixels_equal=True))
 checks.append(dict(family=family,triangles=len(triangles),welded_vertices=len(verts),boundary_edges=boundary,nonmanifold_edges=nonmanifold,degenerate_triangles=0,zero_tangents=zero,emissive_triangles=emissive,embedded_maps=maps,bounds_match=True))
 if family in ('cylinder','linear'):assert emissive==row['led_faces']
 assert row['body_scale_uniform']
assert assets['mansao_pendentes'].bounds is None
assert abs(spec['assets']['cylinder']['hi'][2]-6.448)<1e-4
assert abs(spec['assets']['linear']['hi'][2]-2.356)<1e-4
assert .9<spec['assets']['island']['surface_height_above_floor_m']<1.0
assert .75<spec['assets']['dining']['surface_height_above_floor_m']<.85
preserved=[]
for name in ('mansao_paredes','mansao_pisos','mansao_escada','mansao_teto','mansao_vidros','mansao_mobiliario','mansao_porta_madeira_095'):
 old=try_load_asset(W/'backup_antes_jantar_cozinha/fivem'/(name+'.ydr'));new=try_load_asset(W/'fivem'/(name+'.ydr'))
 previous,current=geometries(old),geometries(new);assert len(previous)==len(current),name
 for a,b in zip(previous,current):
  assert np.array_equal(a.index_buffer,b.index_buffer),name
  for key in ('Position','Normal','TexCoord0'):assert np.array_equal(a.vertex_buffer[key],b.vertex_buffer[key]),(name,key)
 preserved.append(name)
rows=json.loads((W/'colisoes_fivem.json').read_text())
assert sum(r['group']=='mansao_jantar' for r in rows)==13*12
assert sum(r['group']=='mansao_ilha' for r in rows)==5*12
source=Path(__file__).with_name('verify_fit.py').read_text();saved_spec=spec
exec(source.split('routes={}')[0]);exec('routes={}\n'+source.split('routes={}')[1].split("route('entrada_original'")[0]);spec=saved_spec
route('Circulacao mesa e oito cadeiras',[(.8,-10.85,-.8),(4.5,-10.85,-.8),(4.5,-5.8,-.8),(.8,-5.8,-.8),(.8,-10.85,-.8)])
route('Circulacao ilha e quatro banquetas',[(8.85,-11.05,-.8),(11.35,-11.05,-.8),(11.35,-6.95,-.8),(8.85,-6.95,-.8),(8.85,-11.05,-.8)])
route('Entre jantar e cozinha',[(4.5,-8.3,-.8),(8.85,-8.3,-.8)])
assert all(r['passed'] for r in routes.values()),routes
lights=json.loads((W/'luzes_pendentes.json').read_text());assert len(lights['lights'])==9
lua=LuaRuntime(unpack_returned_tuples=True);g=lua.globals()
def table(v):
 if isinstance(v,dict):return lua.table_from({k:table(x) for k,x in v.items()})
 if isinstance(v,list):return lua.table_from([table(x) for x in v])
 return v
g.test_config=table(lights)
lua.execute('''
local mt={__add=function(a,b) return vector3(a.x+b.x,a.y+b.y,a.z+b.z) end,__sub=function(a,b) return vector3(a.x-b.x,a.y-b.y,a.z-b.z) end,__len=function(a) return math.sqrt(a.x*a.x+a.y*a.y+a.z*a.z) end}
function vector3(x,y,z) return setmetatable({x=x,y=y,z=z},mt) end
coords=vector3(test_config.origin[1],test_config.origin[2],test_config.origin[3]);camera=coords;calls={}
json={decode=function(_) return test_config end}
function GetCurrentResourceName() return 'cidade_mansao' end
function LoadResourceFile(_,_) return '' end
function CreateThread(f) thread=coroutine.create(f) end
function Wait(t) delay=t;coroutine.yield() end
function PlayerPedId() return 1 end
function GetEntityCoords(_) return coords end
function GetGameplayCamCoord() return camera end
function DrawLightWithRange(...) table.insert(calls,{...}) end
function frame() local ok,err=coroutine.resume(thread);assert(ok,err) end
''')
lua.execute((W/'work/luzes_pendentes.lua').read_text());g.frame();assert len(g.calls)==9 and g.delay==0
for i,lamp in enumerate(lights['lights'],1):
 values=g.calls[i];expected=np.array(lights['origin'])+lamp['position'];assert np.max(abs(np.array([values[1],values[2],values[3]])-expected))<1e-6
g.coords=g.vector3(-800,676,157);g.camera=g.coords;g.calls=lua.table();g.frame();assert len(g.calls)==0 and g.delay==1000
g.camera=g.vector3(*lights['origin']);g.frame();assert len(g.calls)==9 and g.delay==0
report=dict(passed=True,revision=spec['revision'],mesh_checks=checks,drawable_sha256=hashes,existing_geometry_and_uvs_preserved=preserved,walking_routes=routes,pendant_mounts_match_ceiling=True,light_points=9,light_behavior_cases=3,in_game_verified=False)
(W/'verificacao_jantar_cozinha.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('DINING_KITCHEN_NATIVE_OK',[(c['family'],c['triangles']) for c in checks],len(routes),'clear routes; existing geometry preserved; 9 warm lights',flush=True)
