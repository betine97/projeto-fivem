"""Native round-trip, HD appearance, physics, mip chains and real Lua runtime QA."""
import sys,json,io,hashlib,struct
from collections import Counter
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1]
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(R/'casa_vinewood/work/lua_syntax_deps'),
    r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from PIL import Image
from szio.gta5 import try_load_asset,LodLevel
from luaparser import ast
from lupa import LuaRuntime
report=json.loads((P/'optimization_report.json').read_text())
backup=Path(json.loads((P/'baseline.json').read_text())['backup'])/'resource/stream'
out=P/'stream'
results={}

def faces(geo):
    # Compare actual coloured, textured corners after native export, not only counts.
    vb=geo.vertex_buffer
    cols=[]
    for key in vb.dtype.names:
        cols.append(np.round(vb[key].astype(np.float64),5))
    vertices=np.concatenate(cols,axis=1).astype('<f4')
    tris=vertices[np.asarray(geo.index_buffer).reshape(-1,3)]
    return Counter(hashlib.sha256(t.tobytes()).digest() for t in tris)

def collision(asset):
    if asset.bounds is None:return Counter()
    rows=[]
    for b in asset.bounds.children:
        vs=np.array([v.co for v in b.geometry_vertices])
        for prim in b.geometry_primitives:
            rows.append((int(prim.material.to_packed()),prim.primitive_type.value,
                tuple(np.round(vs[list(prim.vertices)].ravel(),4)),prim.radius,
                int(b.composite_collision_type_flags),int(b.composite_collision_include_flags)))
    return Counter(rows)

original_furniture=try_load_asset(backup/'mansao_mobiliario.ydr')
split_collision=Counter()
for name,row in report['models'].items():
    a=try_load_asset(out/(name+'.ydr'));assert a is not None
    original=try_load_asset(backup/(('mansao_mobiliario' if name=='mansao_tv' else name)+'.ydr'))
    old=[g for m in original.models[LodLevel.HIGH] for g in m.geometries]
    if name in ('mansao_mobiliario','mansao_tv'):
        old=[g for g in old if g.shader_index==(1 if name=='mansao_tv' else 0)]
        split_collision.update(collision(a))
    else:assert collision(a)==collision(original),(name,'Physics changed')
    new=[g for m in a.models[LodLevel.HIGH] for g in m.geometries]
    assert len(old)==len(new)
    for i,(g,h) in enumerate(zip(old,new)):
        assert faces(g)==faces(h),(name,i,'HD textured triangles changed')
    for lod,models in a.models.items():
        for m in models:
            for g in m.geometries:
                assert np.isfinite(g.vertex_buffer['Position']).all()
                assert len(g.index_buffer)%3==0 and len(g.index_buffer)>0
                assert g.index_buffer.max()<len(g.vertex_buffer)
                assert 0<=g.shader_index<len(a.shader_group.shaders)
                for key in g.vertex_buffer.dtype.names:
                    assert np.isfinite(g.vertex_buffer[key]).all(),(name,lod,key)
        assert sum(len(g.index_buffer)//3 for m in models for g in m.geometries)==row['triangles'][lod.name]
    for shader in a.shader_group.shaders:
        for param in shader.parameters:
            if isinstance(param.value,str):assert param.value in a.shader_group.embedded_textures,(name,param.value)
    for key,t in a.shader_group.embedded_textures.items():
        data=t.data.read_bytes();im=Image.open(io.BytesIO(data))
        assert im.size==(t.width,t.height)
        mips=struct.unpack_from('<I',data,28)[0]
        assert mips >= max(1,int(np.log2(t.width))-1),(name,key,mips)
        if data[84:88]==b'DXT1':assert im.convert('RGBA').getchannel('A').getextrema()==(255,255)
    results[name]={'native_roundtrip':True,'hd_corners_preserved':True,'physics_preserved':True,
                   'lod_triangles':row['triangles']}
# BVH vertices are quantized again around the new per-prop centre, and the
# exporter may cyclically rotate triangle corners. Check winding and position
# within 0.2 mm instead of relying on identical quantization bytes.
remaining=list(collision(original_furniture).elements());max_physics_error=0
for row in split_collision.elements():
    found=None
    points=np.array(row[2]).reshape(-1,3)
    for i,other in enumerate(remaining):
        if row[:2]!=other[:2] or row[3:]!=other[3:]:continue
        oldpoints=np.array(other[2]).reshape(-1,3)
        error=min(float(np.max(abs(points-np.roll(oldpoints,j,axis=0)))) for j in range(3))
        if error<=.0002:found=i;max_physics_error=max(max_physics_error,error);break
    assert found is not None,('Split collision changed',row)
    remaining.pop(found)
assert not remaining
results['split_collision_tolerance_m']=round(max_physics_error,6)
typ=try_load_asset(out/'cidade_mansao.ytyp');mp=try_load_asset(out/'cidade_mansao.ymap')
oldtyp=try_load_asset(backup/'cidade_mansao.ytyp');oldmp=try_load_asset(backup/'cidade_mansao.ymap')
assert len(typ.archetypes)==len(oldtyp.archetypes)+1 and len(mp.entities)==len(oldmp.entities)+1
refs={str(a.name):a for a in typ.archetypes}
for e in mp.entities:
    assert str(e.archetype_name) in refs
    a=refs[str(e.archetype_name)]
    if str(a.name) in report['models']:
        asset=try_load_asset(out/(str(a.name)+'.ydr'))
        ps=np.concatenate([g.vertex_buffer['Position'] for m in asset.models[LodLevel.HIGH] for g in m.geometries])
        assert (ps.min(0)>=np.array(a.bb_min)-.001).all() and (ps.max(0)<=np.array(a.bb_max)+.001).all()
for e,previous in zip(mp.entities,oldmp.entities):
    assert str(e.archetype_name)==str(previous.archetype_name)
    assert np.array_equal(e.position,previous.position) and np.array_equal(e.rotation,previous.rotation)
    assert e.scale_xy==previous.scale_xy and e.scale_z==previous.scale_z
assert report['graphics_bytes']['reduction_percent']>60

# Same-size BC1 conversion must retain close-view colour accuracy. Auxiliary
# maps are independently resized; this check covers unchanged 4K hero colour.
texture_quality={}
for name in ['mansao_mobiliario','mansao_jantar','mansao_ilha','mansao_tapete_sala','mansao_paredes']:
    old=try_load_asset(backup/(name+'.ydr'));new=try_load_asset(out/(name+'.ydr'))
    for key,t in new.shader_group.embedded_textures.items():
        if key.endswith(('_normal','_n','_spec')):continue
        previous=old.shader_group.embedded_textures[key]
        if t.width!=previous.width:continue
        a=np.asarray(Image.open(io.BytesIO(previous.data.read_bytes())).convert('RGB'),dtype=np.float32)
        b=np.asarray(Image.open(io.BytesIO(t.data.read_bytes())).convert('RGB'),dtype=np.float32)
        error=np.mean((a-b)**2);psnr=99.0 if error==0 else float(10*np.log10(255**2/error))
        assert psnr>=37,(key,psnr)
        texture_quality[key]={'psnr_db':round(psnr,2),'size':t.width}

# Execute the shipped Lua coroutine with real selection/time/fade logic.
cfg=json.loads((P/'iluminacao_ambiente.json').read_text())
script=(P/'iluminacao_decorativa.lua').read_text();ast.parse(script)
ast.parse((P/'luzes_pendentes.lua').read_text())
assert 'DrawSpotLight' not in script and 'WithShadow' not in script
lua=LuaRuntime(unpack_returned_tuples=True);g=lua.globals()
def table(v):
    if isinstance(v,dict):return lua.table_from({k:table(x) for k,x in v.items()})
    if isinstance(v,list):return lua.table_from([table(x) for x in v])
    return v
g.cfg=table(cfg)
lua.execute('''
local mt={__add=function(a,b) return vector3(a.x+b.x,a.y+b.y,a.z+b.z) end,__sub=function(a,b) return vector3(a.x-b.x,a.y-b.y,a.z-b.z) end,__len=function(a) return math.sqrt(a.x*a.x+a.y*a.y+a.z*a.z) end}
function vector3(x,y,z) return setmetatable({x=x,y=y,z=z},mt) end
timer=0;hour=23;minute=0;calls={};commands={};threads={};frame_count=0;peak_count=0
coords=vector3(cfg.origin[1]+2,cfg.origin[2]-5,cfg.origin[3]+.2);camera=coords
function GetClockHours() return hour end
function GetClockMinutes() return minute end
json={decode=function(_) return cfg end}
function GetCurrentResourceName() return 'cidade_mansao' end
function LoadResourceFile(...) return '' end
function CreateThread(f) threads[#threads+1]=coroutine.create(f) end
function Wait(t) delay=t;coroutine.yield() end
function PlayerPedId() return 1 end
function GetGameTimer() return timer end
function GetEntityCoords(_) return coords end
function GetGameplayCamCoord() return camera end
function RegisterCommand(n,f,_) commands[n]=f end
function DrawLightWithRange(...) calls[#calls+1]={...} end
function frame(t) timer=timer+t;calls={};for _,thread in ipairs(threads) do local ok,e=coroutine.resume(thread);assert(ok,e) end;frame_count=frame_count+1;peak_count=math.max(peak_count,#calls) end
''')
lua.execute(script)
def position(x,y,z):
    return g.vector3(cfg['origin'][0]+x,cfg['origin'][1]+y,cfg['origin'][2]+z)
def frames(n=60):
    for _ in range(n):
        g.frame(16);assert len(g.calls)<=cfg['max_lights']
    return [[g.calls[i][j] for j in range(1,9)] for i in range(1,len(g.calls)+1)]
night=frames();assert len(night)>=12 and g.delay==0
assert min(r[6] for r in night)>2 and max(r[6] for r in night)>=6.6
night_power=sum(r[7] for r in night)
g.hour=12;day=frames();assert sum(r[7] for r in day)<night_power*.4
g.hour=23
max_count=0
for x,y,z in [(-5,-8,.2),(10,-8,.2),(-7,7,.2),(12,5,.2),(-5,6,3.8),(10,-11,3.8),(4,-1,3.8),(1,3,1.9)]:
    g.coords=position(x,y,z);g.camera=g.coords
    rows=frames();assert len(rows)>5
    max_count=max(max_count,len(rows))
    for r in rows:
        assert r[6]>=2.4 and r[7]>0
g.coords=position(500,500,0);g.camera=g.coords;g.frame(1000)
assert len(g.calls)==0 and g.delay==1000
g.camera=position(0,-8,1);assert len(frames())>5 and g.delay==0
lua.execute("commands.luzmansao(0, {'2'})");full=frames()
lua.execute("commands.luzmansao(0, {'99'})");clamped=frames()
assert abs(sum(r[7] for r in full)-sum(r[7] for r in clamped))<.01
results['lighting']={'lua_parsed':True,'runtime_frames':g.frame_count,'max_calls':g.peak_count,
    'budget':24,'night_day_factor':round(night_power/sum(r[7] for r in day),2),
    'far_sleep':True,'camera_only':True,'spotlight_calls':0,'shadow_calls':0}
results['colour_quality']=texture_quality
g.coords=position(5.5,-3.5,.2);g.camera=position(5.5,-3.5,.9)
lua.execute("commands.luzmansao(0, {'1'})")
preview=frames()
results['lighting']['runtime_frames']=g.frame_count
results['lighting']['max_calls']=g.peak_count
(P/'preview_lights.json').write_text(json.dumps([
    {'position':[r[i]-cfg['origin'][i] for i in range(3)],'rgb':r[3:6],
     'range':r[6],'intensity':r[7]} for r in preview],indent=2))
results['passed']=True;results['game_verified']=False
(P/'verification.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print('OPTIMIZATION_VERIFIED',report['graphics_bytes'],results['lighting'],flush=True)
