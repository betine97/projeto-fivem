"""Install one native island revision, preserving the original city and selected-file backups."""
from pathlib import Path
import json,shutil,hashlib,datetime
O=Path(__file__).resolve().parents[1];P=O.parent;R=P.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for name in ['validacao_codewalker.json','validacao_integracao.json','validacao_nativa_profunda.json','testes_client.json']:
    assert json.loads((O/'dados'/name).read_text(encoding='utf-8-sig'))['passed'],name
stream=O/'fivem/stream';sectors=json.loads((O/'dados/setores_alterados.json').read_text());replacement={r['name']+ext for r in sectors for ext in ['.ydr','.ybn']}|{'teste_ilha.ytyp'}
cfg=R/'server-data/server-ilha.cfg';installed=R/'server-data/resources';port=installed/'porto_esperanca'
stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S');backup=O/'backups'/stamp;records=[]
def preserve(dest):
    if dest.exists():
        relative=dest.relative_to(R);target=backup/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(dest,target)
        records.append(dict(target=str(relative),backup=str(target.relative_to(backup)),sha256=sha(target)))
def copy(src,dst):
    preserve(dst);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);assert sha(src)==sha(dst)
preserve(cfg)
for base in [P/'fivem',installed/'teste_ilha']:
    for name in sorted(replacement):copy(stream/name,base/'stream'/name)
    for name in ['water.xml','config.json']:copy(O/'exportados/data'/name,base/'data'/name)
for src in (O/'fivem').rglob('*'):
    if not src.is_file():continue
    if src.parent==stream and src.name in replacement:continue
    copy(src,port/src.relative_to(O/'fivem'))
valid_files={p.name for p in stream.iterdir() if p.is_file() and p.name not in replacement}
if (port/'stream').exists():
    for stale in (port/'stream').iterdir():
        if stale.is_file() and stale.suffix in ['.ydr','.ytd','.ytyp','.ymap','.ymf'] and stale.name not in valid_files:
            assert stale.resolve().parent==(port/'stream').resolve();preserve(stale);stale.unlink()
assert not any((port/'stream'/n).exists() for n in replacement),'Terrain must have a single owner'
text=cfg.read_text(encoding='utf-8-sig')
if 'ensure porto_esperanca' not in text:
    assert 'ensure teste_ilha' in text;text=text.replace('ensure teste_ilha','ensure teste_ilha\nensure porto_esperanca',1);cfg.write_text(text,encoding='utf8')
manifest=dict(created_at=stamp,revision='ilha-20261009-porto-construido-1',backup=str(backup),records=records,replaced_terrain_files=len(replacement),new_resource_files=len(list(port.rglob('*.*'))),server_verified=False,client_verified=False)
backup.mkdir(parents=True,exist_ok=True);(backup/'restauracao.json').write_text(json.dumps(manifest,indent=2))
(O/'dados/instalacao.json').write_text(json.dumps(manifest,indent=2));print(json.dumps({k:v for k,v in manifest.items() if k!='records'},indent=2))
