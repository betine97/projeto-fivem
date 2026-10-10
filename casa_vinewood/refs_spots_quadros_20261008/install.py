"""Install only this verified revision, keeping concurrent and unrelated work."""
import sys,json,hashlib,shutil
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1];D=R/'server-data/resources/cidade_mansao'
sys.path.insert(0,str(R/'casa_vinewood/work/lua_syntax_deps'))
from luaparser import ast
qa=json.loads((P/'verification.json').read_text());assert qa['passed']
pack=json.loads((P/'package.json').read_text());baseline=json.loads((P/'baseline.json').read_text())
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
changes={'stream/'+name:P/'stream'/name for name in pack['installed_files']}
for name,source in changes.items():
    current=D/name
    if current.exists():assert digest(current) in (baseline['files'].get(name),digest(source)),('Concurrent change to this asset',name)
original={str(p.relative_to(D)).replace('\\','/'):digest(p) for p in D.rglob('*') if p.is_file()}
manifest=(D/'fxmanifest.lua').read_text(encoding='utf-8')
if "'stream/mansao_referencias.ytyp'" not in manifest:
    manifest+="\nfiles { 'stream/mansao_referencias.ytyp' }\ndata_file 'DLC_ITYP_REQUEST' 'stream/mansao_referencias.ytyp'\n"
ast.parse(manifest)
backup=P/'backup_imediato_instalacao';backup.mkdir(exist_ok=True)
for name in [*changes,'fxmanifest.lua']:
    if (D/name).exists():
        target=backup/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(D/name,target)
installed={}
try:
    for name,source in changes.items():
        target=D/name;temporary=target.with_suffix(target.suffix+'.installing');shutil.copy2(source,temporary);temporary.replace(target)
        assert digest(target)==digest(source);installed[name]=digest(target)
    temp=D/'fxmanifest.lua.installing';temp.write_text(manifest,encoding='utf-8');temp.replace(D/'fxmanifest.lua');installed['fxmanifest.lua']=digest(D/'fxmanifest.lua')
    for name,expected in original.items():
        if name not in installed:assert digest(D/name)==expected,('Unrelated file changed',name)
    ast.parse((D/'fxmanifest.lua').read_text())
except Exception:
    for name in [*changes,'fxmanifest.lua']:
        if (backup/name).exists():shutil.copy2(backup/name,D/name)
        elif name not in original and (D/name).exists():(D/name).unlink()
    raise
record={'passed':True,'revision':'spots-quadros-referencias-2026-10-08','installed_files':installed,
        'unrelated_files_preserved':len(original)-len(set(original)&set(installed)),
        'backup':baseline['backup'],'immediate_backup':str(backup),
        'spot_entities':88,'new_artworks':4,'light_controller_preserved':True,
        'allocation_delta':qa['allocation_delta'],'reload_required':True,'in_game_verified':False,
        'blender_source':str(P.parent/'mansao_spots_quadros.blend')}
(P/'installation.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
(P.parent/'instalacao_spots_quadros.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
print('INSTALLED_SPOTS_AND_ARTWORKS',len(installed),'files;',record['unrelated_files_preserved'],'other files preserved',flush=True)
