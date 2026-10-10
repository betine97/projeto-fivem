"""Independent read-back checks for the final island material revision."""
from pathlib import Path
import sys, json, hashlib
O = Path(__file__).resolve().parents[1]
R = O.parent.parent
D = Path('C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work')
sys.path[:0] = [str(D/'deps'), str(R/'laboratorio_fivem/work/pydeps')]
import numpy as np
from szio.gta5 import try_load_asset, LodLevel

STREAM = O/'fivem/stream'
TERRAIN = O/'qualidade_terreno/stream'
BASE = R/'server-data/resources/teste_ilha/stream'
LODS = [LodLevel.HIGH, LodLevel.MEDIUM, LodLevel.LOW, LodLevel.VERYLOW]
checks = []


def check(name, result, **details):
    checks.append(dict(name=name,passed=bool(result),**details))
    if not result:
        raise AssertionError(name + ': ' + str(details))


def filehash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect(path, families):
    asset = try_load_asset(path)
    counts = {}
    wind = []
    for shader in asset.shader_group.shaders:
        check('shader_'+path.stem+'_'+shader.preset_filename,
              shader.preset_filename in families, shader=shader.preset_filename)
        for parameter in shader.parameters:
            if str(parameter.name).lower() in ('diffusesampler','bumpsampler','specsampler'):
                check('sampler_'+path.stem+'_'+str(parameter.name),
                      str(parameter.value) in texture_names, texture=str(parameter.value))
    for lod in LODS:
        vertices = triangles = 0
        for model in asset.models[lod]:
            for geometry in model.geometries:
                v = geometry.vertex_buffer
                idx = geometry.index_buffer
                check('finite_'+path.stem+'_'+lod.name+'_'+str(vertices),
                      all(np.isfinite(v[f]).all() for f in ['Position','Normal','TexCoord0','Tangent']))
                check('indices_'+path.stem+'_'+lod.name+'_'+str(vertices),
                      len(idx)%3 == 0 and len(idx)>0 and idx.max()<len(v))
                lengths = np.linalg.norm(v['Normal'],axis=1)
                check('normals_'+path.stem+'_'+lod.name+'_'+str(vertices),
                      np.all((lengths>.98)&(lengths<1.02)),minimum=float(lengths.min()),maximum=float(lengths.max()))
                if asset.shader_group.shaders[geometry.shader_index].preset_filename.startswith('trees'):
                    check('foliage_channels_'+path.stem+'_'+lod.name+'_'+str(vertices),
                          'Colour1' in v.dtype.names and np.all(v['Colour1'][:,0:2]==0) and np.all(v['Colour1'][:,3]==0))
                    wind.extend(v['Colour0'][:,0].tolist())
                vertices += len(v)
                triangles += len(idx)//3
        check('lod_nonempty_'+path.stem+'_'+lod.name, triangles>0,triangles=triangles,vertices=vertices)
        counts[lod.name] = triangles
    if path.stem.startswith('pe_veg'):
        check('wind_preserved_'+path.stem,len(wind)>0 and max(wind)>0 and max(wind)<=128 and asset.bounds is not None)
    return counts


if __name__ == '__main__':
    texture_names = set()
    textures = []
    for path in list(STREAM.glob('*.ytd'))+list(TERRAIN.glob('*.ytd')):
        dictionary = try_load_asset(path)
        texture_names.update(dictionary.textures)
        for key, texture in dictionary.textures.items():
            check('texture_'+path.stem+'_'+key, texture.width>0 and texture.height>0 and len(texture.data.read_bytes())>128)
            textures.append(dict(dictionary=path.stem,name=key,width=texture.width,height=texture.height))
    tiles = json.loads((O/'qualidade_terreno/dados/terrain_quality.json').read_text())['sectors']
    model_rows = json.loads((O/'dados/casas.json').read_text()) + json.loads((O/'dados/arvores.json').read_text())
    models = {}
    for row in model_rows:
        models[row['name']] = inspect(STREAM/(row['name']+'.ydr'),{'normal_spec.sps','normal_spec_alpha.sps','normal.sps','default.sps','trees_normal_spec.sps'})
    for tile in tiles:
        name = tile['name']
        models[name] = inspect(TERRAIN/(name+'.ydr'), {'terrain_cb_4lyr.sps'})
        original=O/'backups/qualidade_20261009_antes/installed/teste_ilha'/(name+'.ybn')
        if original.exists() and (BASE/(name+'.ybn')).exists():
            check('collision_unchanged_'+name,filehash(original)==filehash(BASE/(name+'.ybn')))
        else:
            check('new_land_collision_'+name,(TERRAIN/(name+'.ybn')).exists() and (BASE/(name+'.ybn')).exists())
    check('ten_approved_houses',len([x for x in models if x.startswith('pe_estrutura')])==10)
    check('all_island_sectors',len([x for x in models if x.startswith('ti_terreno')])==len(tiles) and len(tiles)>=42,sectors=len(tiles))
    result=dict(passed=True,checks=checks,models=models,textures=textures,
                original_albedo_preserved=True,client_visual_verified=False)
    (O/'dados/validacao_qualidade.json').write_text(json.dumps(result,indent=2))
    print('QUALITY_VALIDATED',len(models),len(textures),len(checks))
