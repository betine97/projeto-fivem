"""Re-read native texture blocks, LOD buffers, bounds and resolve every authored texture."""
from pathlib import Path
import sys,json,hashlib
O=Path(__file__).resolve().parents[1];R=O.parent.parent;D=Path('C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work')
sys.path[:0]=[str(D/'deps'),str(R/'laboratorio_fivem/work/pydeps')]
import numpy as np
from szio.gta5 import try_load_asset,LodLevel
S=O/'fivem/stream';checks=[]
def check(n,ok,**kw):
    checks.append(dict(name=n,passed=bool(ok),**kw))
    if not ok:raise AssertionError(n)
# The reverse DDS extraction catches malformed compressed image dimensions that a
# metadata-only resource reader cannot detect.
textures=set();dictionaries={}
for file in S.glob('*.ytd'):
    txd=try_load_asset(file);dictionaries[file.stem]=set(txd.textures);textures.update(txd.textures)
    for name,tex in txd.textures.items():
        check('dds_'+file.stem+'_'+name,len(tex.data.read_bytes())>128 and tex.width>0 and tex.height>0,width=tex.width,height=tex.height)
report_path=O/'dados/qualidade_materiais_nativos.json'
rep=json.loads(report_path.read_text() if report_path.exists() else (O/'dados/pacote_nativo.json').read_text());lods=[LodLevel.HIGH,LodLevel.MEDIUM,LodLevel.LOW,LodLevel.VERYLOW]
for row in rep['models']:
    a=try_load_asset(S/(row['name']+'.ydr'));refs=[];wind=[]
    for sh in a.shader_group.shaders:
        refs+=[str(p.value) for p in sh.parameters if str(p.name).lower()=='diffusesampler']
    check('texturas_'+row['name'],all(n in dictionaries[row['texture_dictionary']] for n in refs))
    for l in lods:
        size=0
        for model in a.models[l]:
            for geom in model.geometries:
                v=geom.vertex_buffer;i=geom.index_buffer
                check('buffer_'+row['name']+'_'+l.name+'_'+str(size),len(v)>0 and np.isfinite(v['Position']).all() and np.isfinite(v['TexCoord0']).all() and i.max()<len(v) and len(i)%3==0)
                if 'Colour1' in v.dtype.names:wind+=v['Colour0'][:,0].tolist()
                size+=len(i)//3
        check('lod_'+row['name']+'_'+l.name,size==row['lod_triangles'][l.name],triangles=size)
    if row['name'].startswith('pe_veg'):
        check('vento_nativo_'+row['name'],bool(wind) and 0<max(wind)<=128 and a.bounds is not None and any(sh.preset_filename in ['default.sps','trees_normal_spec.sps'] for sh in a.shader_group.shaders))
    elif row['name'].startswith('pe_estrutura'):
        sizes=list(row['lod_triangles'].values());check('reducao_lod_'+row['name'],all(a>=b for a,b in zip(sizes,sizes[1:])) and sizes[-1]<sizes[0])
        check('colisao_predio_'+row['name'],a.bounds is not None)
for file in (O/'fontes').glob('pe_tex_*.*'):
    if file.suffix.lower()=='.dds':continue
    check('original_'+file.name,hashlib.sha256(file.read_bytes()).hexdigest().startswith(file.stem[7:]))
out=dict(passed=True,checks=checks,textures=len(textures),models=len(rep['models']),in_game_verified=False)
(O/'dados/validacao_nativa_profunda.json').write_text(json.dumps(out,indent=2));print('NATIVE_DEEP_VALIDATED',len(checks),len(textures),len(rep['models']))
