import sys,json,hashlib,shutil
from pathlib import Path
from collections import Counter
P=Path(__file__).resolve().parent;R=P.parents[1];D=R/'server-data/resources/cidade_mansao';O=P/'package';B=P/'backup'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
from szio.gta5 import try_load_asset
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
native=list(O.glob('*.ymap'))+list(O.glob('*.ybn'))
for f in native:
    existing=D/'stream'/f.name; baseline=B/'stream'/f.name
    assert sha(existing)==sha(baseline) or sha(existing)==sha(f),f'Concurrent change: {f.name}'
    a=try_load_asset(f);assert a is not None
    if f.suffix=='.ymap':
        old=try_load_asset(baseline)
        def describe(e):return (str(e.archetype_name),tuple(e.position),tuple(e.rotation),e.scale_xy,e.scale_z,str(e.flags),e.lod_dist)
        oldset=Counter(describe(e) for e in old.entities);newset=Counter(describe(e) for e in a.entities)
        assert not (newset-oldset),f'Unexpected transform change: {f.name}'
        for entity in a.entities:assert str(entity.archetype_name) in json.loads((O/'objetos_catalogo.json').read_text())['protectedModels']
for f in native:shutil.copy2(f,D/'stream'/f.name)
shutil.copy2(O/'objetos_catalogo.json',D/'objetos_catalogo.json')
# Keep the deployable package with the scripts matching its catalog/maps.
for name in ['objetos_shared.lua','objetos_client.lua','objetos_server.lua','fxmanifest.lua','iluminacao_decorativa.lua','iluminacao_ambiente.json']:
    shutil.copy2(D/name,O/name)
baseline={k.replace('\\','/'):v for k,v in json.loads((P/'baseline.json').read_text()).items()}
changed={};preserved=[];additional=[]
expected={f'stream/{f.name}' for f in native}|{'objetos_catalogo.json','objetos_shared.lua','objetos_client.lua','objetos_server.lua','fxmanifest.lua','iluminacao_decorativa.lua','iluminacao_ambiente.json','diagnostico_colisoes_runtime.json','stream/mansao_piano_tapetes.ymap','README.md'}
for f in D.rglob('*'):
    if not f.is_file():continue
    key=f.relative_to(D).as_posix();h=sha(f)
    if key not in baseline:additional.append(key)
    elif h==baseline[key]:preserved.append(key)
    else:
        assert key in expected,f'Unrelated changed file: {key}'
        changed[key]=h
assert all(sha(f)==sha(D/'stream'/f.name) for f in native)
assert all(sha(f)==sha(D/'stream'/f.name) for f in (B/'stream').glob('*.ydr'))
assert all(sha(f)==sha(D/'stream'/f.name) for f in (B/'stream').glob('*.ytd'))
v=json.loads((P/'catalog_verification.json').read_text())
(P/'installation.json').write_text(json.dumps({'catalog_objects':v['objects'],'installed_native_files':[f.name for f in native],'changed':changed,'preserved_files':len(preserved),'additional_files':additional,'mesh_and_texture_hashes_unchanged':True,'camera_duplicate_triangles_removed':v['camera_removed'],'live_restart':False,'in_game_test':False},indent=2))
print('INSTALLED',v['objects'],'editable props;',len(native),'native files; meshes/textures unchanged;',len(preserved),'files preserved')
