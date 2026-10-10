from common import *
import shutil,datetime
from szio.gta5 import *
base=R/'server-data/resources/porto_esperanca';stream=base/'stream';backup=R/'server-data/backups'/('vegetacao-autoral-removida-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'));backup.mkdir(parents=True)
for path in stream.glob('*.ymap'):
    assert not any(str(e.archetype_name).startswith('pe_veg_') for e in try_load_asset(path).entities),path
path=stream/'porto_esperanca.ytyp';typ=try_load_asset(path);old=[a for a in typ.archetypes if str(a.name).startswith('pe_veg_')];kept=[a for a in typ.archetypes if not str(a.name).startswith('pe_veg_')];referenced_txd={str(a.texture_dictionary) for a in kept}
files=list(stream.glob('pe_veg_*.ydr'))+list(stream.glob('pe_veg_*.ybn'))
for p in stream.glob('pe_veg_*.ytd'):
    if p.stem not in referenced_txd:files.append(p)
shutil.copy2(path,backup/path.name);typ.archetypes=kept;save_asset(typ,(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),),stream,path.stem)
for p in files:
    assert p.resolve().parent==stream.resolve()
    shutil.move(str(p),str(backup/p.name))
config=base/'data/config.json';shutil.copy2(config,backup/config.name);cfg=read(config);cfg['probe_models']=[n for n in cfg['probe_models'] if not n.startswith('pe_veg_')];cfg['revision']='porto-cayo-total-20261009-2';write(config,cfg)
write(O/'dados/modelos_antigos_arquivados.json',dict(removed_archetypes=len(old),removed_stream_files=[p.name for p in files],backup=str(backup),remaining_custom_forest_instances=0,original_house_archetypes_preserved=10))
print('LEGACY_ASSETS_ARCHIVED',len(old),len(files),flush=True)
