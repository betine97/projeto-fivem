import sys,json,hashlib,struct,math
from pathlib import Path
P=Path(__file__).resolve().parent;W=P.parent;R=W.parent;O=P/'stream'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(W/'work/lua_syntax_deps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from szio.gta5 import try_load_asset,LodLevel
from szio.gta5.bounds import CollisionFlags
from luaparser import ast
from lupa import LuaRuntime
spec=json.loads((P/'spec.json').read_text());files=['mansao_bar_referencia.ydr','mansao_bar_referencia.ytyp','mansao_bar_referencia.ymap','mansao_bar_referencia.ybn','mansao_tapete_urso.ydr','mansao_piano_tapetes.ytyp']
assets={n:try_load_asset(O/n) for n in files};assert all(assets.values())
a=assets['mansao_bar_referencia.ydr'];counts=[];textures={}
for lod in [LodLevel.HIGH,LodLevel.MEDIUM,LodLevel.LOW,LodLevel.VERYLOW]:
 count=0
 for m in a.models[lod]:
  for g in m.geometries:
   vb=g.vertex_buffer;ids=g.index_buffer.reshape(-1,3);assert np.isfinite(vb['Position']).all();assert ids.max()<len(vb);assert len(ids)>0
   ts=vb['Position'][ids];assert np.min(np.linalg.norm(np.cross(ts[:,1]-ts[:,0],ts[:,2]-ts[:,0]),axis=1))>1e-12
   assert np.isfinite(vb['Normal']).all()
   if 'Tangent' in vb.dtype.names:assert np.min(np.linalg.norm(vb['Tangent'][:,:3],axis=1))>.5
   count+=len(ids)
 counts.append(count)
assert counts==sorted(counts,reverse=True) and counts[0]<35000 and counts[-1]<3000
for name,tx in a.shader_group.embedded_textures.items():
 data=tx.data.read_bytes();source=(P/'textures'/(name+'.dds')).read_bytes();assert data[128:]==source[128:len(data)],(name,len(data),len(source))
 h,w=struct.unpack_from('<II',data,12);levels=struct.unpack_from('<I',data,28)[0];assert w&(w-1)==0 and h&(h-1)==0
 # Native BC texture export stops at the last complete 4x4 block. Tiny solid
 # colours need one mip; detailed maps retain every meaningful native mip.
 assert levels>=max(1,math.floor(math.log2(min(w,h)))-1),(name,levels)
 textures[name]={'width':w,'height':h,'mips':levels,'bytes':len(data)}
barlo=np.array(spec['lo']);barhi=np.array(spec['hi']);assert barlo[1]>-14.241 and barhi[2]<2.358 and barlo[0]>6.3 and barhi[0]<13.5
assert len(assets['mansao_bar_referencia.ymap'].entities)==1
assert int(assets['mansao_bar_referencia.ybn'].children[0].composite_collision_include_flags)==int(CollisionFlags.CAMERA_TEST)
old=try_load_asset(P/'backup_antes/mansao_tapete_urso.ydr');new=assets['mansao_tapete_urso.ydr']
for lod,models in old.models.items():
 for om,nm in zip(models,new.models[lod]):
  for og,ng in zip(om.geometries,nm.geometries):
   assert np.allclose(ng.vertex_buffer['Position'],og.vertex_buffer['Position']*1.5,atol=1e-6)
   for attr in og.vertex_buffer.dtype.names:
    if attr!='Position':assert np.array_equal(og.vertex_buffer[attr],ng.vertex_buffer[attr]),attr
   assert np.array_equal(og.index_buffer,ng.index_buffer)
for name,tx in old.shader_group.embedded_textures.items():assert tx.data.read_bytes()==new.shader_group.embedded_textures[name].data.read_bytes()
for ob,nb in zip(old.bounds.children,new.bounds.children):
 assert np.allclose(np.array([v.co for v in nb.geometry_vertices]),np.array([v.co for v in ob.geometry_vertices])*1.5,atol=2e-4)
 assert len(ob.geometry_primitives)==len(nb.geometry_primitives)
oldtypes=try_load_asset(P/'backup_antes/mansao_piano_tapetes.ytyp')
for oa,na in zip(oldtypes.archetypes,assets['mansao_piano_tapetes.ytyp'].archetypes):
 assert str(oa.name)==str(na.name)
 if str(oa.name)!='mansao_tapete_urso':
  assert tuple(oa.bb_min)==tuple(na.bb_min) and tuple(oa.bb_max)==tuple(na.bb_max) and oa.bs_radius==na.bs_radius
code=(P/'bar_referencia_luzes.lua').read_text();ast.parse(code)
lua=LuaRuntime();lua.execute('''
 local mt={};function vector3(x,y,z) return setmetatable({x=x,y=y,z=z},mt) end
 mt.__add=function(a,b) return vector3(a.x+b.x,a.y+b.y,a.z+b.z) end
 mt.__sub=function(a,b) return vector3(a.x-b.x,a.y-b.y,a.z-b.z) end
 mt.__len=function(a) return math.sqrt(a.x*a.x+a.y*a.y+a.z*a.z) end
 count=0;near=true;waits={};function PlayerPedId() return 1 end
 function GetEntityCoords(_) if near then return vector3(-966.75,662.93,158.435) else return vector3(0,0,0) end end
 function GetFrameTime() return 1/60 end
 function DrawLightWithRange(...) count=count+1 end
 function Wait(ms) waits[#waits+1]=ms;coroutine.yield(ms) end
 function CreateThread(fn) thread=coroutine.create(fn) end
 function step() local ok,msg=coroutine.resume(thread);assert(ok,msg);return msg end
''');lua.execute(code);lua.globals().step();assert lua.globals().count==4
lua.globals().near=False
for _ in range(25):lua.globals().step()
assert lua.globals().step()==750
def memory(p):
 _,_,s,g=struct.unpack('<4I',p.read_bytes()[:16])
 def size(f):return (512<<(f&15))*sum([(f>>27)&1,((f>>26)&1)*2,((f>>25)&1)*4,((f>>24)&1)*8,((f>>17)&127)*16,((f>>11)&63)*32,((f>>7)&15)*64,((f>>5)&3)*128,((f>>4)&1)*256])
 return {'system_MiB':size(s)/1048576,'graphics_MiB':size(g)/1048576,'disk_bytes':p.stat().st_size}
report={'passed':True,'native_roundtrip':True,'bar_lod_triangles':counts,'bar_memory':memory(O/'mansao_bar_referencia.ydr'),'textures':textures,'bar_fit_clearances_m':{'wall':float(barlo[1]+14.241),'ceiling':float(2.358-barhi[2])},'bear_dimensions_m':spec['bear_resize']['new_dimensions'],'bear_geometry_factor':1.5,'bear_uv_normal_texture_collision_checks':True,'other_piano_rug_archetypes_preserved':True,'local_light_budget':4,'light_near_far_runtime_test':True,'files':{n:hashlib.sha256((O/n).read_bytes()).hexdigest() for n in files},'in_game_verified':False}
(P/'verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print('VERIFIED',counts,report['bar_memory'],flush=True)
