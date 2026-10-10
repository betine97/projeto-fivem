import datetime, hashlib, json, shutil
from pathlib import Path
R=Path(__file__).resolve().parents[3];P=R/'teste-ilha/cayo_perico';F=P/'fivem'
stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S');backup=P/'backups'/stamp
paths=['server-data/server-ilha.cfg','server-data/resources/teste_ilha/client.lua']
backup.mkdir(parents=True)
records=[]
for name in paths:
    path=R/name;dest=backup/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dest)
    records.append(dict(path=name,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
target=R/'server-data/resources/cayo_vizinha'
if target.exists(): raise RuntimeError('Resource already exists: inspect before replacing')
shutil.copytree(F,target)
client=R/paths[1];text=client.read_text(encoding='utf-8')
text+="\n-- Shared world preparation for the adjacent Cayo Perico resource.\nexports('prepareWater',prepareWater)\nexports('closeMap',closeMap)\n"
client.write_text(text,encoding='utf-8')
cfg=R/paths[0];text=cfg.read_text(encoding='utf-8')
assert 'ensure teste_ilha' in text
text=text.replace('ensure teste_ilha','ensure teste_ilha\nensure cayo_vizinha',1)
if 'sv_enforceGameBuild' not in text:text=text.replace('setr cidade_modo ilha','setr cidade_modo ilha\nset sv_enforceGameBuild 3258',1)
cfg.write_text(text,encoding='utf-8')
report=dict(revision='cayo-vizinha-20261009-1',created_at=stamp,backup=str(backup),records=records,
            resource=str(target),files=sum(f.is_file() for f in target.rglob('*')),server_verified=False,client_verified=False)
(P/'instalacao.json').write_text(json.dumps(report,indent=2))
(backup/'restauracao.json').write_text(json.dumps(report,indent=2))
print('INSTALADO',report['files'],'files','backup',str(backup),flush=True)
