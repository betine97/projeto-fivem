"""Install only the castle preview, with an additive guarded cfg change."""
import sys,json,hashlib,shutil
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1];SOURCE=P/'package';DEST=R/'server-data/resources/cidade_castelo_previa'
sys.path.insert(0,str(R/'casa_vinewood/work/lua_syntax_deps'))
from luaparser import ast
qa=json.loads((P/'verificacao.json').read_text(encoding='utf-8'));assert qa['passed']
assert (R/'server-data/resources/cidade_castelo_livre/fxmanifest.lua').exists()
cfg=R/'server-data/server.cfg';before=cfg.read_bytes()
assert b'ensure cidade_castelo_livre' in before
assert not DEST.exists(),'Existing preview resource; inspect before replacing'
assert b'ensure cidade_castelo_previa' not in before
for name in ['fxmanifest.lua','client.lua','server.lua']:ast.parse((SOURCE/name).read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
preserved={p.relative_to(R/'server-data/resources/cidade_castelo_livre').as_posix():sha(p) for p in (R/'server-data/resources/cidade_castelo_livre').rglob('*') if p.is_file()}
backup=P/'backup';backup.mkdir(exist_ok=True);shutil.copy2(cfg,backup/'server.cfg')
TEMP=DEST.with_name(DEST.name+'.installing');assert not TEMP.exists()
shutil.copytree(SOURCE,TEMP)
assert cfg.read_bytes()==before,'Concurrent server config edit'
TEMP.rename(DEST)
updated=before+(b'' if before.endswith(b'\n') else b'\r\n')+b'\r\n# Previa do castelo em escala real com texturas externas\r\nensure cidade_castelo_previa\r\n'
try:
    assert cfg.read_bytes()==before,'Concurrent cfg edit'
    cfg.write_bytes(updated)
    assert cfg.read_bytes().startswith(before)
    assert cfg.read_bytes().count(b'ensure cidade_castelo_previa')==1
    for name,value in preserved.items():assert sha(R/'server-data/resources/cidade_castelo_livre'/name)==value
    installed={p.relative_to(DEST).as_posix():sha(p) for p in DEST.rglob('*') if p.is_file()}
    assert all(value==sha(SOURCE/name) for name,value in installed.items())
except Exception:
    if cfg.read_bytes()==updated:cfg.write_bytes(before)
    raise
data={'installed':True,'resource':str(DEST),'files':installed,'cfg_previous_sha256':hashlib.sha256(before).hexdigest(),'cfg_backup':str(backup/'server.cfg'),'cleared_lot_resource_preserved_files':len(preserved),'original_blender_unchanged':True,'command':'castelo','return_command':'voltarcastelo','live_server_activated':False,'in_game_verified':False}
(P/'instalacao.json').write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8')
print('CASTLE_PREVIEW_INSTALLED',len(installed),'files; cleared lot resource preserved',flush=True)
