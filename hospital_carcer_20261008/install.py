from pathlib import Path
import json,shutil,hashlib
r=Path.cwd();p=r/'hospital_carcer_20261008';package=p/'package';dest=r/'server-data/resources/cidade_hospital_carcer';backup=p/'backup_instalacao';backup.mkdir(exist_ok=True)
for report in ['verification.json','native_validation.json','runtime_validation.json']:
 assert json.loads((p/report).read_text(encoding='utf-8-sig'))['passed'],report
for report in ['verification.json','client_verification.json']:
 assert json.loads((r/'admin_sistema_20261008'/report).read_text())['passed'],report
s=json.loads((p/'spec.json').read_text());(package/'hospital.json').write_text(json.dumps({k:s[k] for k in ['origin','doors','rooms']},indent=2))
installed=[]
for f in package.rglob('*'):
 if not f.is_file():continue
 rel=f.relative_to(package);target=dest/rel
 if f.suffix in ['.ydr','.ydd','.ybn','.ymap','.ytyp']:
  existing=[x for x in (r/'server-data/resources').rglob(f.name) if x.is_file() and dest not in x.parents]
  assert len(existing)<=1,'Multiple active overrides: '+f.name
  if existing:
   target=existing[0];source=p/'native'/f.name
   assert source.read_bytes()==target.read_bytes(),'Existing resource changed while preparing '+f.name
 if target.exists():
  b=backup/target.relative_to(r/'server-data');b.parent.mkdir(parents=True,exist_ok=True)
  if not b.exists():shutil.copy2(target,b)
 target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,target)
 assert f.read_bytes()==target.read_bytes()
 installed.append({'file':str(target.relative_to(r)),'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
cfg=r/'server-data/server.cfg';b=r/'admin_sistema_20261008/backup/server.cfg'
if not b.exists():shutil.copy2(cfg,b)
text=cfg.read_text(encoding='utf-8-sig')
if 'ensure cidade_admin' not in text:text=text.replace('ensure cidade_acesso','ensure cidade_acesso\nensure cidade_admin',1)
if 'ensure cidade_hospital_carcer' not in text:text+='\n# Hospital autoral no terreno de Carcer Way\nensure cidade_hospital_carcer\n'
cfg.write_text(text,encoding='utf-8')
(p/'installation.json').write_text(json.dumps({'installed':installed,'server_running_requires_reload':True,'in_game_verified':False},indent=2));print('INSTALLED',len(installed))
