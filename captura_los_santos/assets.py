"""Prepare textured native geometry for a catalogue image, without replacing GTA assets."""
from pathlib import Path
import sys,json,io,struct,os
ROOT=Path(__file__).resolve().parent.parent
sys.path[:0]=[str(ROOT/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from PIL import Image
from szio.rpf import open_rpf
from szio.gta5 import try_load_asset,LodLevel
GTA=Path(os.environ.get('GTA_ROOT',r'C:/Program Files (x86)/Steam/steamapps/common/Grand Theft Auto V'))
def prepare(meta,index,folder):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True);arcs={};assets={}
    def file(name):
        path=index.get(name.lower())
        if not path:return None
        parts=path.split('|');key='|'.join(parts[:-1])
        if key not in arcs:
            a=open_rpf(GTA/parts[0])
            for part in parts[1:-1]:a=a.open_nested(part)
            arcs[key]=a
        dest=folder/name;dest.write_bytes(arcs[key].read_bytes(parts[-1]));return dest
    def asset(name):
        if name not in assets:
            p=file(name);assets[name]=try_load_asset(p) if p else None
        return assets[name]
    name=meta['model'];draw=asset(meta['asset']+'.ydr')
    if not draw:
        fragment=asset(meta['asset']+'.yft')
        if fragment:draw=fragment.base_drawable
    if not draw and meta.get('drawableDictionary'):
        dictionary=asset(meta['drawableDictionary']+'.ydd')
        if dictionary:draw=dictionary.drawables.get(meta['asset']) or dictionary.drawables.get(name)
    if not draw:raise ValueError('Geometria nativa não localizada no índice de arquivos.')
    txds=[meta.get('textureDictionary'),meta.get('asset'),name]
    # Filename variations frequently share a single prop texture dictionary.
    for candidate in list(txds):
        if candidate and '_' in candidate:txds.append(candidate.rsplit('_',1)[0])
    if meta.get('file'):
        arc=meta['file'].rsplit('|',1)[0]
        txds.extend(Path(n).stem for n,p in index.items() if n.endswith('.ytd') and p.rsplit('|',1)[0]==arc)
    materials=[];missing=[]
    for shader in draw.shader_group.shaders:
        diffuse=next((p.value for p in shader.parameters if str(p.name).lower() in ['diffusesampler','texturesampler']),None)
        texname=str(diffuse).lower();tex={str(k).lower():v for k,v in draw.shader_group.embedded_textures.items()}.get(texname)
        used=None
        if diffuse and not tex:
            for txd in dict.fromkeys(x for x in txds if x):
                a=asset(txd+'.ytd')
                if a:tex={str(k).lower():v for k,v in a.textures.items()}.get(texname)
                if tex:used=index.get(txd+'.ytd');break
        texture=None
        if tex:
            data=tex.data.read_bytes()
            try:im=Image.open(io.BytesIO(data)).convert('RGBA')
            except NotImplementedError:
                if struct.unpack_from('<I',data,80)[0]!=2:raise
                h,w=struct.unpack_from('<II',data,12);alpha=np.frombuffer(data[128:128+w*h],np.uint8).reshape(h,w);rgba=np.full((h,w,4),255,np.uint8);rgba[...,3]=alpha;im=Image.fromarray(rgba)
            dest=folder/(texname+'.png');im.save(dest);texture=str(dest)
        elif diffuse:missing.append(texname)
        materials.append({'preset':shader.preset_filename or '', 'diffuse':texture,'sourceTextureFile':used})
    arrays={};geometries=[]
    models=draw.models.get(LodLevel.HIGH) or next(iter(draw.models.values()))
    for model in models:
        for geometry in model.geometries:
            n=len(geometries);arrays['v'+str(n)]=geometry.vertex_buffer;arrays['i'+str(n)]=geometry.index_buffer;geometries.append(geometry.shader_index)
    if not geometries:raise ValueError('Modelo sem geometria reutilizável.')
    np.savez_compressed(folder/'geometry.npz',**arrays)
    report={'name':name,'materials':materials,'geometries':geometries,'missingTextures':missing,'source':meta}
    (folder/'model.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    return report
if __name__=='__main__':
    folder=Path(sys.argv[1]);meta=json.loads((folder/'source.json').read_text(encoding='utf8'))
    index=json.loads((ROOT/'captura_los_santos/data/model_index.json').read_text(encoding='utf8'))
    prepare(meta,index['files'],folder)
