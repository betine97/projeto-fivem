from common import *
from szio.gta5 import LodLevel
import collections
C=O/'cache_blender';C.mkdir(exist_ok=True);X=O/'texturas_objetos';X.mkdir(exist_ok=True)
D=read(O/'dados/implantacao.json');materials={};requested={};cache={};models=[]
def texture_files(txd):
    paths=[]
    for base in [O/'stream',P/'cayo_perico/originais/assets',O/'fontes']:
        for suffix in ['', '+hi']:
            p=base/(txd+suffix+'.ytd')
            if p.exists():paths.append(p)
    return paths
def extract_texture(txd,name,embedded):
    dest=X/(name+'.dds')
    if dest.exists():return str(dest)
    found=embedded.get(name)
    for p in texture_files(txd):
        if p not in cache:cache[p]=try_load_asset(p).textures
        for key,t in cache[p].items():
            if str(key).lower()==name.lower():found=t
    if found:dest.write_bytes(found.data.read_bytes());return str(dest)
    old=P/'amostra_natural/texturas'/(name+'.dds')
    return str(old) if old.exists() else None
for n,row in D['models'].items():
    a=try_load_asset(Path(row['drawable_file']));geos=[];mats=[]
    for shader in a.shader_group.shaders:
        refs={str(p.name).lower():p.value for p in shader.parameters if isinstance(p.value,str)}
        mats.append(dict(preset=shader.preset_filename,diffuse=extract_texture(row['txd'],refs.get('diffusesampler',''),a.shader_group.embedded_textures),normal=extract_texture(row['txd'],refs.get('bumpsampler',''),a.shader_group.embedded_textures)))
    arrays={}
    for model in a.models[LodLevel.HIGH]:
        for g in model.geometries:
            if 'shadow_proxy' in mats[g.shader_index]['preset']:continue
            k=len(geos);arrays['v'+str(k)]=g.vertex_buffer;arrays['i'+str(k)]=g.index_buffer;geos.append(g.shader_index)
    np.savez_compressed(C/(row['name']+'.npz') if 'name' in row else C/(n+'.npz'),**arrays)
    models.append(dict(name=n,geometries=geos,materials=mats,family=row['family']))
write(C/'modelos.json',models)
print('BLENDER_NATIVE_CACHE',len(models),flush=True)

