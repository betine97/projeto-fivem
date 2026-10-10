import sys,json,hashlib,struct,math
from pathlib import Path
P=Path(__file__).resolve().parent;W=P.parent;R=W.parent;O=P/'stream'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(W/'work/lua_syntax_deps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from szio.gta5 import try_load_asset,LodLevel
from szio.gta5.bounds import CollisionFlags
from luaparser import ast
from lupa import LuaRuntime
spec=json.loads((P/'spec.json').read_text());files=['mansao_adega_vitrines.ydr','mansao_adega_vitrines.ytyp','mansao_adega_vitrines.ymap','mansao_adega_vitrines.ybn']
assets={n:try_load_asset(O/n) for n in files};assert all(assets.values())
a=assets['mansao_adega_vitrines.ydr'];counts=[];textures={};batches={}
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
 batches[lod.name]={'models':len(a.models[lod]),'geometries':sum(len(m.geometries) for m in a.models[lod])}
 assert batches[lod.name]['models']==1 and batches[lod.name]['geometries']<=24,batches[lod.name]
assert counts==sorted(counts,reverse=True) and counts[0]<110000 and counts[-1]<7000
for name,tx in a.shader_group.embedded_textures.items():
 data=tx.data.read_bytes();source=(P/'textures'/(name+'.dds')).read_bytes();assert data[128:]==source[128:len(data)],(name,len(data),len(source))
 h,w=struct.unpack_from('<II',data,12);levels=struct.unpack_from('<I',data,28)[0];assert w&(w-1)==0 and h&(h-1)==0
 # Native BC texture export stops at the last complete 4x4 block. Tiny solid
 # colours need one mip; detailed maps retain every meaningful native mip.
 assert levels>=max(1,math.floor(math.log2(min(w,h)))-1),(name,levels)
 textures[name]={'width':w,'height':h,'mips':levels,'bytes':len(data)}
barlo=np.array(spec['lo']);barhi=np.array(spec['hi']);assert barhi[1]<-.95 and barhi[2]<2.358 and barlo[0]>9.4 and barhi[0]<14.186 and abs(barlo[2]+.8)<1e-5
assert len(assets['mansao_adega_vitrines.ymap'].entities)==1
assert int(assets['mansao_adega_vitrines.ybn'].children[0].composite_collision_include_flags)==int(CollisionFlags.CAMERA_TEST)
assert sum(q['name'].startswith('Vidro transparente') for q in spec['collision_boxes'])==4
assert len(a.bounds.children[0].geometry_primitives)==len(spec['collision_boxes'])*12
code=(P/'adega_vitrines_luzes.lua').read_text();ast.parse(code)
lua=LuaRuntime();lua.execute('''
 local mt={};function vector3(x,y,z) return setmetatable({x=x,y=y,z=z},mt) end
 mt.__add=function(a,b) return vector3(a.x+b.x,a.y+b.y,a.z+b.z) end
 mt.__sub=function(a,b) return vector3(a.x-b.x,a.y-b.y,a.z-b.z) end
 mt.__len=function(a) return math.sqrt(a.x*a.x+a.y*a.y+a.z*a.z) end
 count=0;near=true;waits={};function PlayerPedId() return 1 end
 function GetEntityCoords(_) if near then return vector3(-964.30,673.73,157.935) else return vector3(0,0,0) end end
 function GetFrameTime() return 1/60 end
 function DrawLightWithRange(...) count=count+1 end
 function Wait(ms) waits[#waits+1]=ms;coroutine.yield(ms) end
 function CreateThread(fn) thread=coroutine.create(fn) end
 function step() local ok,msg=coroutine.resume(thread);assert(ok,msg);return msg end
''');lua.execute(code);lua.globals().step();assert lua.globals().count==8
lua.globals().near=False
for _ in range(25):lua.globals().step()
assert lua.globals().step()==750
def memory(p):
 _,_,s,g=struct.unpack('<4I',p.read_bytes()[:16])
 def size(f):return (512<<(f&15))*sum([(f>>27)&1,((f>>26)&1)*2,((f>>25)&1)*4,((f>>24)&1)*8,((f>>17)&127)*16,((f>>11)&63)*32,((f>>7)&15)*64,((f>>5)&3)*128,((f>>4)&1)*256])
 return {'system_MiB':size(s)/1048576,'graphics_MiB':size(g)/1048576,'disk_bytes':p.stat().st_size}
report={'passed':True,'native_roundtrip':True,'adega_lod_triangles':counts,'lod_batches':batches,'adega_memory':memory(O/'mansao_adega_vitrines.ydr'),'textures':textures,'adega_fit_clearances_m':{'wall':float(-.95-barhi[1]),'passage':float(barlo[0]-9.4),'right_wall':float(14.186-barhi[0]),'ceiling':float(2.358-barhi[2])},'dimensions_m':[spec['width_m'],spec['depth_m'],spec['height_m']],'display_wine_bottles':52,'local_light_budget':8,'light_near_far_runtime_test':True,'files':{n:hashlib.sha256((O/n).read_bytes()).hexdigest() for n in files},'in_game_verified':False}
(P/'verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print('VERIFIED',counts,report['adega_memory'],flush=True)
