"""Extract the registered, unmodified native plants for an offline LOD bake."""
from common import *
import io, collections
from PIL import Image
from szio.gta5 import LodLevel
S=O/'stream';C=O/'atlas_rasteira/cache';C.mkdir(parents=True,exist_ok=True)
grass=read(O/'dados/rasteira.json')
types={str(t.name):t for t in try_load_asset(S/'natureza_integrada.ytyp').archetypes}
for p in (P/'cayo_perico/originais/assets').glob('*.ytyp'):
    types.update({str(t.name):t for t in try_load_asset(p).archetypes})
texture_cache={};textures={};rows=[]
index_path=O/'dados/indice_texturas_rasteira.json'
if index_path.exists():texture_index=read(index_path)
else:
    texture_index={}
    wanted={str(types[grass.get('alias_map',{}).get(n,n)].texture_dictionary)+suffix+'.ytd' for n in grass['source_counts'] for suffix in ['', '+hi']}
    def walk(arc,folder='',prefix='',depth=0):
        for name in arc.list_dir(folder):
            p=folder+'/'+name if folder else name
            if arc.is_dir(p):walk(arc,p,prefix,depth)
            elif p.endswith('.rpf') and depth<2:
                try:walk(arc.open_nested(p),'',prefix+p+'|',depth+1)
                except Exception:pass
            elif name in wanted:texture_index[name]=prefix+p
    for p in sorted(G.glob('x64*.rpf'),key=lambda p:p.name!='x64i.rpf'):
        walk(open_rpf(p),prefix=p.name+'|')
    write(index_path,texture_index)
    print('NATIVE_GRASS_TXD_INDEX',len(texture_index),flush=True)
def source_texture(filename):
    if filename not in texture_index:return None
    parts=texture_index[filename].split('|');arc=open_rpf(G/parts[0])
    for part in parts[1:-1]:arc=arc.open_nested(part)
    dest=O/'fontes'/filename;dest.write_bytes(arc.read_bytes(parts[-1]));return dest
def texture(name,draw,typ):
    name=str(name)
    if name in textures:return textures[name]
    tex={str(k).lower():v for k,v in draw.shader_group.embedded_textures.items()}.get(name.lower())
    if not tex:
        txd=str(typ.texture_dictionary)
        for suffix in ['', '+hi']:
            candidates=[S/(txd+suffix+'.ytd'),P/'cayo_perico/originais/assets'/(txd+suffix+'.ytd')]
            p=next((p for p in candidates if p.exists()),None)
            if not p:p=source_texture(txd+suffix+'.ytd')
            if p:
                if p not in texture_cache:texture_cache[p]={str(k).lower():v for k,v in try_load_asset(p).textures.items()}
                tex=texture_cache[p].get(name.lower())
                if tex:break
    if not tex:raise RuntimeError('Missing native diffuse '+name+' txd='+str(typ.texture_dictionary)+' embedded='+str(list(draw.shader_group.embedded_textures)))
    dest=C/(name+'.png');Image.open(io.BytesIO(tex.data.read_bytes())).convert('RGBA').save(dest)
    textures[name]=str(dest);return str(dest)
colors=collections.defaultdict(list)
for p in list(S.glob('ni_rasteira_*.ymap'))[:12]:
    for b in try_load_asset(p).grass_instance_lists:
        colors[str(b.archetype_name)].extend(b.instances['Color'][::max(1,len(b.instances)//30)].tolist())
for name,count in grass['source_counts'].items():
    if 'stones' in name:continue
    alias=grass.get('alias_map',{}).get(name,name);typ=types[alias]
    p=S/(alias+'.ydr') if (S/(alias+'.ydr')).exists() else P/'cayo_perico/originais/assets'/(name+'.ydr')
    draw=try_load_asset(p);materials=[]
    for sh in draw.shader_group.shaders:
        diffuse=next((p.value for p in sh.parameters if str(p.name).lower()=='diffusesampler'),None)
        materials.append(dict(preset=sh.preset_filename,diffuse=texture(diffuse,draw,typ) if diffuse else None))
    arrays={};geo=[];bounds=[]
    for model in draw.models[LodLevel.HIGH]:
        for g in model.geometries:
            k=len(geo);arrays['v'+str(k)]=g.vertex_buffer;arrays['i'+str(k)]=g.index_buffer;geo.append(g.shader_index);bounds.append(g.vertex_buffer['Position'])
    np.savez_compressed(C/(name+'.npz'),**arrays)
    bounds=np.concatenate(bounds);lo=bounds.min(0);hi=bounds.max(0)
    rows.append(dict(name=name,count=count,geometries=geo,materials=materials,bb_min=lo.tolist(),bb_max=hi.tolist(),instance_color=np.median(colors[alias],axis=0).tolist()))
write(O/'atlas_rasteira/modelos.json',rows)
print('GROUND_COVER_NATIVE_MODELS',len(rows),flush=True)
