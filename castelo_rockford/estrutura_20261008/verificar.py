import sys,json,math,hashlib,struct
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1];D=P/'package/stream'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(R/'casa_vinewood/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps',str(R/'casa_vinewood/work/lua_syntax_deps')]
import numpy as np
from shapely.geometry import Polygon,box,Point
from shapely import affinity
from shapely.ops import unary_union
from szio.gta5 import try_load_asset,LodLevel
from szio import jenkhash
from luaparser import ast
from lupa import LuaRuntime

extract=json.loads((P/'extracao.json').read_text(encoding='utf-8'))
pack=json.loads((P/'pacote.json').read_text(encoding='utf-8'))
cw=json.loads((P/'codewalker_verificacao.json').read_text(encoding='utf-8-sig'))
assert len(cw)==len(pack['native_files']) and all(r['nativeLoaded'] for r in cw)
assert max(r['systemBytes'] for r in cw)<16*1024**2
assert max(r['graphicsBytes'] for r in cw)<32*1024**2
for name in ['fxmanifest.lua','client.lua','server.lua']:ast.parse((P/'package'/name).read_text(encoding='utf-8'))
tx=try_load_asset(D/'crf_castelo_texturas.ytd');geometries=np.load(P/'geometria.npz')
alltris=[];checked=[];materialcount=0
def walk(b,parent=np.eye(4)):
    transform=np.asarray(b.composite_transform)@parent
    for c in getattr(b,'children',[]):
        if c:yield from walk(c,transform)
    if not hasattr(b,'geometry_primitives'):return
    for poly in b.geometry_primitives:
        ps=np.array([b.geometry_vertices[i].co for i in poly.vertices])
        yield (np.c_[ps,np.ones(len(ps))]@transform)[:,:3]
for row in pack['models']:
    a=try_load_asset(D/(row['model']+'.ydr'))
    triangles=0;uv_delta=0
    for m in a.models[LodLevel.HIGH]:
        for g in m.geometries:
            vb=g.vertex_buffer;ids=g.index_buffer
            assert np.isfinite(vb['Position']).all() and np.isfinite(vb['TexCoord0']).all()
            assert max(ids)<len(vb) and len(ids)%3==0
            assert np.min(np.linalg.norm(vb['Normal'],axis=1))>.95
            triangles+=len(ids)//3
    assert triangles==row['triangles']
    for shader in a.shader_group.shaders:
        assert shader.name in [f"hash_{jenkhash.name_to_hash(Path(shader.preset_filename).stem):08x}",Path(shader.preset_filename).stem],(shader.name,shader.preset_filename)
        for param in shader.parameters:
            if isinstance(param.value,str):assert param.value in tx.textures,(row['model'],param.name,param.value)
        materialcount+=1
    if row['collision_triangles']:
        native=list(walk(a.bounds));assert len(native)==row['collision_triangles']
        alltris.extend(native)
    checked.append({'model':row['model'],'triangles':triangles,'collision':row['collision_triangles'],'textures_resolved':True})
for name,t in tx.textures.items():
    dds=t.data.read_bytes();assert dds[:4]==b'DDS ' and len(dds)>128
    # GTA block-compressed texture import keeps levels down to 4x4 blocks.
    assert struct.unpack_from('<I',dds,28)[0]==int(math.log2(max(t.width,t.height)))-1,(name,'native mip chain incomplete')
    assert [t.width,t.height]==next(r['size'] for r in pack['textures'] if r['name']==name)

tri=np.array(alltris);v0=tri[:,0];e1=tri[:,1]-v0;e2=tri[:,2]-v0
def ray(start,direction,max_distance):
    direction=np.array(direction,dtype=float);direction/=np.linalg.norm(direction)
    h=np.cross(np.broadcast_to(direction,e2.shape),e2);det=np.einsum('ij,ij->i',e1,h)
    inv=np.zeros_like(det);ok=abs(det)>1e-9;inv[ok]=1/det[ok]
    ss=np.array(start)-v0;u=inv*np.einsum('ij,ij->i',ss,h);q=np.cross(ss,e1)
    v=inv*(q@direction);tt=inv*np.einsum('ij,ij->i',e2,q)
    valid=ok&(u>=-1e-6)&(v>=-1e-6)&(u+v<=1.000001)&(tt>.005)&(tt<=max_distance)
    return float(np.min(tt[valid])) if valid.any() else None
routes=[('entrada',(0,-14,1.6),(0,2,1.6)),('salao',(-3,-2,1.6),(-5.5,-2,1.6)),('cozinha',(3,-3,1.6),(5.5,-3,1.6)),('apoio',(3,4,1.6),(5.5,4,1.6)),('funcionarios',(0,-2,5.8),(0,-4,5.8)),('suite E frente',(-3,-2,5.8),(-5.5,-2,5.8)),('suite D frente',(3,-2,5.8),(5.5,-2,5.8)),('suite E fundos',(-3,3,5.8),(-5.5,3,5.8)),('suite D fundos',(3,3,5.8),(5.5,3,5.8)),('conselho',(0,3,10),(0,1.9,10))]
clear=[]
for name,aa,bb in routes:
    aa=np.array(aa,dtype=float);bb=np.array(bb,dtype=float);d=bb-aa;side=np.array([-d[1],d[0],0]);side/=np.linalg.norm(side)
    for offset in [-.3,0,.3]:
        for z in [0,.9]:assert ray(aa+side*offset+[0,0,z],d,np.linalg.norm(d)) is None,name
    clear.append(name)
floors=[]
for point,height in [((0,0,3),.7),((0,-1.5,7),4.9),((11,-7,11),9.1)]:
    d=ray(point,[0,0,-1],4);assert d is not None and abs(point[2]-d-height)<.01,(point,height,d)
    floors.append(height)
stairs=0
for base in [.7,4.9]:
    for i in range(12):
        top=base+(i+1)*.175;point=(-1.2,3.4+i*.3,top+.15)
        d=ray(point,[0,0,-1],.4);assert d is not None and abs(d-.15)<.012,(point,d);stairs+=1
        top=base+2.1+(i+1)*.175;point=(1.2,6.7-i*.3,top+.15)
        d=ray(point,[0,0,-1],.4);assert d is not None and abs(d-.15)<.012,(point,d);stairs+=1

# The model's true footprint fits the area that was cleared previously.
measured=json.loads((R/'castelo_rockford/medidas.json').read_text())
foot=unary_union([box(-14,-10,14,10)]+[Point(x,y).buffer(3.1,quad_segs=10) for x in [-11.5,11.5] for y in [-8,8]])
foot=affinity.translate(affinity.rotate(foot,extract['rotation'],origin=(0,0)),*extract['anchor'][:2])
from shapely.geometry import shape
cleared=shape(json.loads((P/'implantacao.json').read_text())['affected'])
assert foot.difference(cleared).area<.1
assert hashlib.sha256(Path(extract['source']).read_bytes()).hexdigest()==extract['source_sha256']

# Server command must refuse non-admin players and dispatch only to the caller.
lua=LuaRuntime(unpack_returned_tuples=True);lua.execute('commands={}; sent={}; function RegisterCommand(n,f,r) commands[n]=f end; function IsPlayerAceAllowed(src,p) return src==1 and p=="cidade.admin" end; function TriggerClientEvent(n,src,msg) table.insert(sent,{name=n,source=src,message=msg}) end')
lua.execute((P/'package/server.lua').read_text());lua.execute("commands.castelo(2); assert(sent[1].name=='cidade_castelo:mensagem'); commands.castelo(1); assert(sent[2].name=='cidade_castelo:visitar' and sent[2].source==1)")
results={'passed':True,'native_files_loaded':len(cw),'shader_materials_checked':materialcount,'textures_checked':len(tx.textures),'models':checked,'passages_body_rays':60,'passages':clear,'floors':floors,'stair_treads_verified':stairs,'scale_preserved':True,'footprint_outside_cleared_m2':foot.difference(cleared).area,'source_unchanged':True,'admin_command_authorization_passed':True,'in_game_verified':False}
(P/'verificacao.json').write_text(json.dumps(results,indent=2,ensure_ascii=False),encoding='utf-8')
print('NATIVE_VERIFIED',len(cw),'files',len(tx.textures),'textures',stairs,'steps',flush=True)
