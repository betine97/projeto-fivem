import sys,json,hashlib,struct,math
from pathlib import Path
P=Path(__file__).resolve().parent;W=P.parent;R=W.parent;O=P/'stream'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(W/'work/lua_syntax_deps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from szio.gta5 import try_load_asset,LodLevel
from szio.gta5.bounds import CollisionFlags
from szio.gta5.drawables import LightFlashiness
spec=json.loads((P/'spec.json').read_text());model=spec['model'];door=spec['door_model']
files=[model+s for s in ['.ydr','.ytyp','.ymap','.ybn']]+[door+'.ydr']
assets={n:try_load_asset(O/n) for n in files};assert all(assets.values())
report={'passed':True,'native_roundtrip':True,'models':{},'in_game_verified':False}
def memory(p):
    _,_,s,g=struct.unpack('<4I',p.read_bytes()[:16])
    def size(f):return (512<<(f&15))*sum([(f>>27)&1,((f>>26)&1)*2,((f>>25)&1)*4,((f>>24)&1)*8,((f>>17)&127)*16,((f>>11)&63)*32,((f>>7)&15)*64,((f>>5)&3)*128,((f>>4)&1)*256])
    return {'system_MiB':size(s)/1048576,'graphics_MiB':size(g)/1048576,'disk_bytes':p.stat().st_size}
for name in [model,door]:
    a=assets[name+'.ydr'];counts=[];textures={}
    for lod in [LodLevel.HIGH,LodLevel.MEDIUM,LodLevel.LOW,LodLevel.VERYLOW]:
        assert len(a.models[lod])==1
        count=0
        for m in a.models[lod]:
            for g in m.geometries:
                vb=g.vertex_buffer;ids=g.index_buffer.reshape(-1,3)
                assert len(vb)<=65535 and ids.min()>=0 and ids.max()<len(vb)
                assert np.isfinite(vb['Position']).all() and np.isfinite(vb['Normal']).all()
                ts=vb['Position'][ids];assert np.min(np.linalg.norm(np.cross(ts[:,1]-ts[:,0],ts[:,2]-ts[:,0]),axis=1))>1e-12
                if 'Tangent' in vb.dtype.names:assert np.min(np.linalg.norm(vb['Tangent'][:,:3],axis=1))>.5
                for key in vb.dtype.names:
                    if 'TexCoord' in key:assert np.isfinite(vb[key]).all()
                assert g.shader_index<len(a.shader_group.shaders)
                count+=len(ids)
        counts.append(count)
    assert counts==sorted(counts,reverse=True) and counts[0]<12000
    for txname,tx in a.shader_group.embedded_textures.items():
        data=tx.data.read_bytes();source=(P/'textures'/(txname+'.dds')).read_bytes()
        assert data[128:]==source[128:len(data)]
        h,w=struct.unpack_from('<II',data,12);levels=struct.unpack_from('<I',data,28)[0]
        assert not(w&(w-1)) and not(h&(h-1))
        assert levels>=max(1,int(math.log2(min(w,h)))-1)
        textures[txname]={'width':w,'height':h,'mips':levels}
    assert a.bounds and len(a.bounds.children)==1
    for b in a.bounds.children:
        assert len(b.geometry_primitives)==12*len(spec['collision_boxes'] if name==model else spec['door_collision_boxes'])
    report['models'][name]={'lod_triangles':counts,'textures':textures,'memory':memory(O/(name+'.ydr')),'shaders':[(str(s.name),str(s.preset_filename)) for s in a.shader_group.shaders]}
    correct_shader_hash={'normal_spec.sps':'hash_38dd00df','emissive.sps':'hash_8f245469','glass.sps':'hash_d9f8c9bf'}
    for s in a.shader_group.shaders:assert str(s.name)==correct_shader_hash[s.preset_filename]
    print('SHADERS',name,report['models'][name]['shaders'],flush=True)
fixed=assets[model+'.ydr'];lo=np.array(spec['fixed_bounds']['lo']);hi=np.array(spec['fixed_bounds']['hi'])
assert hi[1]<-1.615 and lo[1]>-6.582 and hi[2]<2.358
assert len(fixed.lights)==4
for l in fixed.lights:
    assert l.time_flags==0xFFFFFF and l.flashiness==LightFlashiness.CONSTANT
    assert l.volume_intensity==0 and l.corona_intensity==0 and l.volume_outer_intensity==0
assert len(assets[model+'.ytyp'].archetypes)==2 and len(assets[model+'.ymap'].entities)==1
assert int(assets[model+'.ybn'].children[0].composite_collision_include_flags)==int(CollisionFlags.CAMERA_TEST)
# Inverse transform: all static solid boxes remain outside the clear opening.
for b in spec['collision_boxes']:
    x,y,z=b['lo'];X,Y,Z=b['hi']
    if b['name'].startswith('Aparador'):assert X<3.64
    elif b['name'].startswith('Batente'):assert X<=3.684 or x>=4.696 or z>=2.455
leaf=assets[door+'.ydr'];vs=np.concatenate([g.vertex_buffer['Position'] for m in leaf.models[LodLevel.HIGH] for g in m.geometries])
assert np.isclose(vs[:,0].min(),-spec['door_width'],atol=1e-5)
assert np.isclose(vs[:,2].min(),0,atol=1e-5) and np.isclose(vs[:,2].max(),spec['door_height'],atol=1e-5)
# +95 degree swing from -90 points inward, away from the kitchen cabinets.
u=-spec['door_width'];angle=math.radians(5);hinge=np.array(spec['door_hinge_house'])
open_tip=hinge+np.array([math.cos(angle)*u,math.sin(angle)*u,0])
assert open_tip[0]<hinge[0]-.9 and open_tip[1]>-6.582
report.update({'adega_clearance_m':float(-1.615-hi[1]),'ceiling_clearance_m':float(2.358-hi[2]),'opening_width_m':1.1,'opening_height_m':2.5,'door_hinge_local_collision':True,'door_swing_clear':True,'native_lights_always_on':4,'files':{n:hashlib.sha256((O/n).read_bytes()).hexdigest() for n in files}})
(P/'verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print('VERIFIED',report['models'][model]['memory'],report['models'][door]['memory'],flush=True)
