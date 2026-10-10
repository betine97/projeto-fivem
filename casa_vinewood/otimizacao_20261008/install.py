"""Install only verified artifacts; preserve unrelated and concurrent changes."""
import sys,json,hashlib,shutil
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1];D=R/'server-data/resources/cidade_mansao'
sys.path.insert(0,str(R/'casa_vinewood/work/lua_syntax_deps'))
from luaparser import ast
verification=json.loads((P/'verification.json').read_text());assert verification['passed']
baseline=json.loads((P/'baseline.json').read_text())
hashfile=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
changes={str(p.relative_to(P)).replace('\\','/'):p for p in (P/'stream').iterdir() if p.is_file()}
for name in ['iluminacao_decorativa.lua','luzes_pendentes.lua','iluminacao_ambiente.json']:changes[name]=P/name
for name,source in changes.items():
    current=D/name
    if current.exists():assert hashfile(current) in (baseline['files'].get(name),hashfile(source)),('Resource changed during work',name)
saved={str(p.relative_to(D)).replace('\\','/'):hashfile(p) for p in D.rglob('*') if p.is_file()}
# Preserve the latest manifest, including the newly installed custom plant map.
manifest=(D/'fxmanifest.lua').read_text(encoding='utf-8')
if "'iluminacao_ambiente.json'" not in manifest:manifest+="\nfiles { 'iluminacao_ambiente.json' }\n"
ast.parse(manifest)
latest=P/'backup_imediato_instalacao';latest.mkdir(exist_ok=True)
for name in [*changes,'fxmanifest.lua']:
    path=D/name
    if path.exists():
        dst=latest/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dst)
for p in [P/'iluminacao_decorativa.lua',P/'luzes_pendentes.lua']:ast.parse(p.read_text())
installed={}
try:
    for name,source in changes.items():
        dst=D/name;temp=dst.with_suffix(dst.suffix+'.installing')
        shutil.copy2(source,temp);temp.replace(dst);installed[name]=hashfile(dst)
        assert installed[name]==hashfile(source)
    temp=D/'fxmanifest.lua.installing';temp.write_text(manifest,encoding='utf-8');temp.replace(D/'fxmanifest.lua')
    installed['fxmanifest.lua']=hashfile(D/'fxmanifest.lua')
    for name,digest in saved.items():
        if name not in installed:assert hashfile(D/name)==digest,('Unrelated file changed',name)
    for p in D.glob('*.lua'):ast.parse(p.read_text(encoding='utf-8'))
except Exception:
    for name in [*changes,'fxmanifest.lua']:
        restore=latest/name
        if restore.exists():shutil.copy2(restore,D/name)
        elif name not in saved and (D/name).exists():(D/name).unlink()
    raise
# Keep the editable lighting source in sync for subsequent decoration work.
shutil.copy2(P/'iluminacao_decorativa.lua',R/'casa_vinewood/work/iluminacao_decorativa.lua')
result={'passed':True,'revision':'otimizacao-luz-ampla-2026-10-08',
        'files':installed,'unrelated_files_preserved':len(saved)-len(set(saved)&set(installed)),
        'backup':baseline['backup'],'immediate_backup':str(latest),
        'resource_reload_required':True,'game_verified':False}
(P/'installation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
(R/'casa_vinewood/instalacao_otimizacao_iluminacao.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('INSTALLED_OPTIMIZATION',len(installed),'files;',result['unrelated_files_preserved'],'unrelated files preserved',flush=True)
