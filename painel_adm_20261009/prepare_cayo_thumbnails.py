"""Extract actual game geometry/textures for every model in the editor catalogue."""
from pathlib import Path
import sys,json,io,collections,struct
R=Path(__file__).resolve().parent.parent;P=R/'teste-ilha';O=P/'identidade_cayo_total'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from PIL import Image
from szio.gta5 import try_load_asset,LodLevel
from szio.rpf import open_rpf
G=Path(r'C:/Program Files (x86)/Steam/steamapps/common/Grand Theft Auto V');C=R/'painel_adm_20261009/cayo_thumbnails';C.mkdir(exist_ok=True);(C/'cache').mkdir(exist_ok=True)
catalog=json.loads((R/'server-data/resources/cidade_admin/ui/cayo.json').read_text(encoding='utf-8-sig'))['objects'];indexfile=C/'native_index.json'
types={}
for p in list((P/'cayo_perico/originais/assets').glob('*.ytyp'))+list((P/'identidade_natural/fontes').glob('*.ytyp'))+list((O/'fontes').glob('*.ytyp')):
    for t in try_load_asset(p).archetypes:types[str(t.name)]=t
if indexfile.exists():index=json.loads(indexfile.read_text())
else:
    index={}
    def walk(a,folder='',prefix='',depth=0):
        for name in a.list_dir(folder):
            p=folder+'/'+name if folder else name
            if a.is_dir(p):walk(a,p,prefix,depth)
            elif p.endswith('.rpf') and depth<3:
                try:walk(a.open_nested(p),'',prefix+p+'|',depth+1)
                except Exception:pass
            elif name.endswith(('.ydr','.ydd','.ytd','.yft')):index[name.lower()]=prefix+p
    for p in G.glob('x64*.rpf'):walk(open_rpf(p),prefix=p.name+'|')
    for p in (G/'update/x64/dlcpacks/mpheist4').glob('*.rpf'):walk(open_rpf(p),prefix=str(p.relative_to(G)).replace('\\','/')+'|')
    indexfile.write_text(json.dumps(index));print('THUMB_NATIVE_INDEX',len(index),flush=True)
arcs={};assets={};textures={};missing=[];rows=[]
previous={q['name']:q for q in json.loads((C/'models.json').read_text())} if (C/'models.json').exists() else {}
def file(name):
    for folder in [P/'cayo_perico/originais/assets',O/'stream',P/'identidade_natural/fontes',O/'fontes']:
        p=folder/name
        if p.exists():return p
    path=index.get(name.lower())
    if not path:return None
    parts=path.split('|');key='|'.join(parts[:-1])
    if key not in arcs:
        a=open_rpf(G/parts[0])
        for part in parts[1:-1]:a=a.open_nested(part)
        arcs[key]=a
    dest=C/'cache'/name;dest.write_bytes(arcs[key].read_bytes(parts[-1]));return dest
def asset(name):
    if name in assets:return assets[name]
    p=file(name)
    if not p:return None
    a=try_load_asset(p);assets[name]=a;return a
def diffuse(name,draw,t):
    name=str(name).lower()
    if name in textures:return textures[name]
    tex={str(k).lower():v for k,v in draw.shader_group.embedded_textures.items()}.get(name)
    if not tex:
        for txd in [str(t.texture_dictionary)+'+hi',str(t.texture_dictionary)]:
            a=asset(txd+'.ytd')
            if a:tex={str(k).lower():v for k,v in a.textures.items()}.get(name)
            if tex:break
    if not tex:return None
    dest=C/'cache'/(name+'.png');data=tex.data.read_bytes()
    try:im=Image.open(io.BytesIO(data)).convert('RGBA')
    except NotImplementedError:
        # Native A8 masks are valid DDS, but Pillow lacks that legacy format.
        flags=struct.unpack_from('<I',data,80)[0]
        if flags!=2:raise
        h,w=struct.unpack_from('<II',data,12);a=np.frombuffer(data[128:128+w*h],np.uint8).reshape(h,w);rgba=np.full((h,w,4),255,np.uint8);rgba[...,3]=a;im=Image.fromarray(rgba)
    im.save(dest);textures[name]=str(dest);return str(dest)
for k,row in enumerate(catalog):
    name=row['sourceModel'];t=types.get(name)
    if name in previous:rows.append(previous[name]);continue
    if not t:missing.append(dict(name=name,reason='Archetype missing'));continue
    draw=asset(str(t.asset_name)+'.ydr')
    if not draw:
        dictionary=asset(str(t.drawable_dictionary)+'.ydd')
        if dictionary:
            candidates=getattr(dictionary,'drawables',{});draw=candidates.get(str(t.asset_name)) or candidates.get(name)
    if not draw:
        fragment=asset(str(t.asset_name)+'.yft')
        if fragment:draw=fragment.base_drawable
    if not draw:missing.append(dict(name=name,reason='Native drawable missing',asset=str(t.asset_name),dictionary=str(t.drawable_dictionary)));continue
    materials=[]
    for sh in draw.shader_group.shaders:
        dn=next((p.value for p in sh.parameters if str(p.name).lower() in ['diffusesampler','texturesampler']),None)
        materials.append(dict(preset=sh.preset_filename,diffuse=diffuse(dn,draw,t) if dn else None))
    arrays={};geos=[]
    models=draw.models.get(LodLevel.HIGH) or next(iter(draw.models.values()))
    for model in models:
        for g in model.geometries:
            n=len(geos);arrays['v'+str(n)]=g.vertex_buffer;arrays['i'+str(n)]=g.index_buffer;geos.append(g.shader_index)
    if not geos:missing.append(dict(name=name,reason='Native geometry empty'));continue
    np.savez_compressed(C/'cache'/(name+'.npz'),**arrays);rows.append(dict(name=name,materials=materials,geometries=geos,category=row['category'],bb_min=list(t.bb_min),bb_max=list(t.bb_max)))
    if k%100==0:print('THUMB_CACHE',k,flush=True)
(C/'models.json').write_text(json.dumps(rows,indent=2));(C/'missing.json').write_text(json.dumps(missing,indent=2));print('THUMB_CACHE_COMPLETE',len(rows),'missing',len(missing),flush=True)
