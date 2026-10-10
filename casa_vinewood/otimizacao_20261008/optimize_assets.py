"""Reproducible native optimization; original HD vertices and physics are retained."""
import sys, json, io, struct, copy, subprocess, hashlib
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(ROOT/'laboratorio_fivem/work/pydeps'),
    r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from PIL import Image
from szio.gta5 import try_load_asset, save_asset, AssetTarget, AssetFormat, AssetVersion, LodLevel
from szio.types import DataSource, Vector
BACKUP = Path(json.loads((HERE/'baseline.json').read_text())['backup'])/'resource/stream'
OUT = HERE/'stream'; OUT.mkdir(exist_ok=True)
TEX = HERE/'textures'; TEX.mkdir(exist_ok=True)
WORK = HERE/'meshes'; WORK.mkdir(exist_ok=True)
TARGET = (AssetTarget(AssetFormat.NATIVE, AssetVersion.GEN8),)
NODE = r'C:/Users/erons/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'
NAMES = ['mansao_mobiliario', 'mansao_tv', 'mansao_pendentes', 'mansao_jantar', 'mansao_ilha',
         'mansao_tapete_sala', 'mansao_paredes', 'mansao_porta_madeira_095', 'mansao_pisos', 'mansao_escada']
LOD_NAMES = set(NAMES[:6])
# Colour detail stays large on close-view fabric, stone, doors and brick.
# Normal detail and specularity are sampled independently; not all maps need 4K.
SIZES = {'sofa_albedo':4096,'sofa_normal':2048,'sofa_spec':512,
         'tv_albedo':2048,'tv_normal':1024,'tv_spec':512,
         'linear_albedo':2048,'linear_normal':1024,'linear_spec':256,
         'cylinder_albedo':2048,'cylinder_normal':1024,'cylinder_spec':256,
         'dining_albedo':4096,'dining_normal':2048,'dining_spec':512,
         'island_albedo':4096,'island_normal':2048,'island_spec':512,
         'rug_albedo':4096,'rug_normal':1024,'rug_spec':256,
         'parede_reboco_n':1024,'parede_tijolo_tv_n':1024,
         'corrimao_preto':512,'corrimao_preto_n':256,'piso_marmore_n':1024}

def rsc_memory(path):
    magic, version, system, graphics = struct.unpack('<4I', path.read_bytes()[:16])
    assert magic == 0x37435352
    def size(f):
        counts = [(f>>27)&1, ((f>>26)&1)*2, ((f>>25)&1)*4, ((f>>24)&1)*8,
                  ((f>>17)&127)*16, ((f>>11)&63)*32, ((f>>7)&15)*64,
                  ((f>>5)&3)*128, ((f>>4)&1)*256]
        return (512 << (f&15))*sum(counts)
    return {'disk_bytes':path.stat().st_size,'system_bytes':size(system),'graphics_bytes':size(graphics)}

def normalize(image):
    arr = np.asarray(image.convert('RGBA'),dtype=np.float32).copy()
    n = arr[:,:,:3]/127.5-1
    n /= np.maximum(np.linalg.norm(n,axis=2,keepdims=True),1e-8)
    arr[:,:,:3] = np.clip(np.round((n+1)*127.5),0,255)
    return Image.fromarray(arr.astype(np.uint8))

def encode_mips(image, codec, normal):
    levels = []
    while True:
        buf=io.BytesIO(); image.save(buf,format='DDS',pixel_format=codec); levels.append(buf.getvalue())
        if image.size == (1,1): break
        image=image.resize((max(1,image.width//2),max(1,image.height//2)),Image.Resampling.BOX)
        if normal: image=normalize(image)
    header=bytearray(levels[0][:128])
    struct.pack_into('<I',header,8,struct.unpack_from('<I',header,8)[0]|0x20000)
    struct.pack_into('<I',header,28,len(levels))
    struct.pack_into('<I',header,108,0x1000|8|0x400000)
    return bytes(header)+b''.join(x[128:] for x in levels)

def textures(asset, name):
    rows=[]
    for key, tex in asset.shader_group.embedded_textures.items():
        data=tex.data.read_bytes(); before=len(data)
        image=Image.open(io.BytesIO(data)).convert('RGBA')
        normal=key.endswith(('_normal','_n'))
        size=min(SIZES.get(key,tex.width),tex.width)
        codec='DXT5' if normal or image.getchannel('A').getextrema() != (255,255) else 'DXT1'
        resized=size != tex.width
        if resized:
            image=image.resize((size,size),Image.Resampling.LANCZOS)
            if normal:image=normalize(image)
        # Do not re-encode existing BC1, unchanged maps or tiny constant colours.
        if resized or (codec=='DXT1' and data[84:88]!=b'DXT1' and size>4):
            data=encode_mips(image,codec,normal)
        path=TEX/(key+'.dds')
        if path.exists():assert path.read_bytes()==data,('Conflicting shared texture',key)
        else:path.write_bytes(data)
        rows.append({'name':key,'before_size':tex.width,'size':size,'codec':data[84:88].decode(),
                     'before_bytes':before,'bytes':len(data),'normal':normal})
        tex.width=tex.height=size; tex.data=DataSource.create(data,name=key+'.dds')
    return rows

def split_furniture(asset, tv):
    shader=1 if tv else 0
    for models in asset.models.values():
        for m in models:m.geometries=[g for g in m.geometries if g.shader_index==shader]
    asset.models={lod:[m for m in models if m.geometries] for lod,models in asset.models.items()}
    asset.shader_group.shaders=[asset.shader_group.shaders[shader]]
    for models in asset.models.values():
        for m in models:
            for g in m.geometries:g.shader_index=0
    prefix='tv_' if tv else 'sofa_'
    asset.shader_group.embedded_textures={k:v for k,v in asset.shader_group.embedded_textures.items() if k.startswith(prefix)}
    assert asset.bounds and len(asset.bounds.children)==1
    b=asset.bounds.children[0]
    vs=np.array([v.co for v in b.geometry_vertices])
    b.geometry_primitives=[p for p in b.geometry_primitives if (vs[list(p.vertices),0].mean() < -8)==tv]
    assert len(b.geometry_primitives)==(24 if tv else 116)
    used=sorted({i for p in b.geometry_primitives for i in p.vertices})
    remap={old:new for new,old in enumerate(used)}
    b.geometry_vertices=[b.geometry_vertices[i] for i in used]
    for p in b.geometry_primitives:p.vertices=tuple(remap[i] for i in p.vertices)
    lo=vs[used].min(0);hi=vs[used].max(0)
    for bound in [b,asset.bounds]:
        bound.bb_min=Vector(lo);bound.bb_max=Vector(hi);bound.centroid=Vector((lo+hi)*.5)
        bound.cg=bound.centroid;bound.radius_around_centroid=float(np.linalg.norm(hi-lo)*.5)

def geometry_jobs(asset,name):
    originals=asset.models[LodLevel.HIGH]
    jobs=[]; geometries=[]
    for mi,m in enumerate(originals):
        for gi,g in enumerate(m.geometries):
            base=WORK/f'{name}_{mi}_{gi}'
            vb=g.vertex_buffer
            np.asarray(g.index_buffer,dtype='<u4').tofile(str(base)+'.indices')
            np.asarray(vb['Position'],dtype='<f4').tofile(str(base)+'.positions')
            cols=[vb['Normal']];weights=[.1]*3
            for key in vb.dtype.names:
                if key.startswith('TexCoord'):
                    cols.append(vb[key]);weights.extend([.15]*2)
            np.asarray(np.concatenate(cols,axis=1),dtype='<f4').tofile(str(base)+'.attributes')
            levels=[{'ratio':r,'error':e,'output':str(base)+'_'+str(i)} for i,(r,e) in enumerate(
                [(1,0),(.45,.004),(.17,.012),(.06,.025)])]
            jobs.append({'indices':str(base)+'.indices','positions':str(base)+'.positions',
                'attributes':str(base)+'.attributes','weights':weights,'levels':levels,'result':str(base)+'.json'})
            geometries.append((mi,gi,g,levels,str(base)+'.json'))
    file=WORK/(name+'.jobs.json');file.write_text(json.dumps(jobs))
    subprocess.run([NODE,str(HERE/'mesh_lods.mjs'),str(file)],check=True)
    lods={lod:[copy.copy(m) for m in originals] for lod in LodLevel}
    for models in lods.values():
        for m in models:m.geometries=[]
    errors=[]
    for mi,gi,g,levels,result in geometries:
        results=json.loads(Path(result).read_text());errors.append(results)
        for i,lod in enumerate(LodLevel):
            level=levels[i];indices=np.fromfile(level['output']+'.indices',dtype='<u4')
            remap=np.fromfile(level['output']+'.remap',dtype='<u4');count=results[i]['count']
            valid=remap<count; vertices=np.empty(count,dtype=g.vertex_buffer.dtype)
            vertices[remap[valid]]=g.vertex_buffer[:len(remap)][valid]
            n=copy.copy(g);n.vertex_buffer=vertices;n.index_buffer=indices
            lods[lod][mi].geometries.append(n)
    asset.models=lods
    hd=28.0 if name in ('mansao_mobiliario','mansao_tv') else 24.0
    asset.lod_thresholds={LodLevel.HIGH:hd,LodLevel.MEDIUM:55.0,LodLevel.LOW:100.0,LodLevel.VERYLOW:180.0}
    return errors

def box(asset):
    ps=np.concatenate([g.vertex_buffer['Position'] for m in asset.models[LodLevel.HIGH] for g in m.geometries])
    return ps.min(0),ps.max(0)

report={'models':{},'before':{n:rsc_memory(BACKUP/(n+'.ydr')) for n in NAMES if n!='mansao_tv'},
        'game_verified':False,'fps_measured':False,'meshoptimizer_revision':(HERE/'vendor/revision.txt').read_text()}
for name in NAMES:
    source='mansao_mobiliario' if name=='mansao_tv' else name
    asset=try_load_asset(BACKUP/(source+'.ydr'));assert asset is not None
    if name in ('mansao_mobiliario','mansao_tv'):split_furniture(asset,name=='mansao_tv')
    row={'textures':textures(asset,name)}
    if name in LOD_NAMES:row['simplification']=geometry_jobs(asset,name)
    row['triangles']={lod.name:sum(len(g.index_buffer)//3 for m in models for g in m.geometries) for lod,models in asset.models.items()}
    row['lo'],row['hi']=[v.tolist() for v in box(asset)]
    save_asset(asset,TARGET,OUT,name)
    row.update(rsc_memory(OUT/(name+'.ydr')));report['models'][name]=row
    print(name,row['triangles'],round(row['graphics_bytes']/1048576,2),'MiB graphics',flush=True)

# The TV gains its own streaming entity; positions, scale and collision geometry stay exact.
typ=try_load_asset(BACKUP/'cidade_mansao.ytyp');mp=try_load_asset(BACKUP/'cidade_mansao.ymap')
src=next(a for a in typ.archetypes if str(a.name)=='mansao_mobiliario')
tv=copy.copy(src);tv.name=tv.asset_name=tv.physics_dictionary='mansao_tv';typ.archetypes.append(tv)
entity=copy.copy(next(e for e in mp.entities if str(e.archetype_name)=='mansao_mobiliario'))
entity.archetype_name='mansao_tv';mp.entities.append(entity)
for a in typ.archetypes:
    name=str(a.name)
    if name not in LOD_NAMES:continue
    lo=np.array(report['models'][name]['lo']);hi=np.array(report['models'][name]['hi'])
    a.bb_min=Vector(lo);a.bb_max=Vector(hi);a.bs_center=Vector((lo+hi)*.5)
    a.bs_radius=float(np.linalg.norm(hi-lo)*.5);a.lod_dist=180;a.hd_texture_dist=60
for e in mp.entities:
    if str(e.archetype_name) in LOD_NAMES:e.lod_dist=180
save_asset(typ,TARGET,OUT,'cidade_mansao');save_asset(mp,TARGET,OUT,'cidade_mansao')
dt=try_load_asset(BACKUP/'mansao_decoracao.ytyp');dm=try_load_asset(BACKUP/'mansao_decoracao.ymap')
for a in dt.archetypes:
    if str(a.name)=='mansao_tapete_sala':a.lod_dist=180;a.hd_texture_dist=60
for e in dm.entities:
    if str(e.archetype_name)=='mansao_tapete_sala':e.lod_dist=180
save_asset(dt,TARGET,OUT,'mansao_decoracao');save_asset(dm,TARGET,OUT,'mansao_decoracao')
report['after']={n:rsc_memory(OUT/(n+'.ydr')) for n in NAMES}
for metric in ['graphics_bytes','system_bytes','disk_bytes']:
    before=sum(v[metric] for v in report['before'].values());after=sum(v[metric] for v in report['after'].values())
    report[metric]={'before':before,'after':after,'reduction_percent':round(100*(1-after/before),2)}
(HERE/'optimization_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('OPTIMIZATION_STAGED',report['graphics_bytes'],flush=True)
