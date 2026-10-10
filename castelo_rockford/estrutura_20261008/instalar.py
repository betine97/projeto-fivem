import json,hashlib,shutil,os
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1];resources=R/'server-data/resources'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for f in ['verificacao.json','trajeto_verificacao.json']:
 assert json.loads((P/f).read_text(encoding='utf-8'))['passed']
for f in ['codewalker_verificacao.json','codewalker_terreno.json']:
 assert all(r['nativeLoaded'] for r in json.loads((P/f).read_text(encoding='utf-8-sig')))
pack=json.loads((P/'pacote.json').read_text(encoding='utf-8'));assert sha(Path(pack['source']))==pack['source_sha256']
previous=json.loads((P.parent/'instalacao_previa_20261008/instalacao.json').read_text(encoding='utf-8'))
terrain=json.loads((P/'terreno_alteracoes.json').read_text(encoding='utf-8'))
expected={'cidade_castelo_previa':previous['files'],'cidade_castelo_livre':terrain['input_hashes']}
for resource,files in expected.items():
 for name,digest in files.items():assert sha(resources/resource/name)==digest,('Concurrent castle edit',resource,name)
cfg=R/'server-data/server.cfg';cfg_before=cfg.read_bytes()
backup=P/'backup_instalacao';assert not backup.exists(),'Existing install snapshot: inspect before retrying'
backup.mkdir()
for resource in expected:shutil.copytree(resources/resource,backup/resource)
shutil.copy2(P/'implantacao.json',P/'terrain/implantacao_atual.json');shutil.copy2(P/'trajeto_verificacao.json',P/'terrain/trajeto_verificacao.json')
(P/'terrain/LEIA-ME.md').write_text('Terreno integrado ao castelo, revisão 08/10/2026. A geometria e colisão foram recortadas somente no volume de implantação e circulação indicado em implantacao_atual.json. Os relatórios anteriores registram a primeira limpeza do lote. A revisão atual está em trajeto_verificacao.json. Consulte o LEIA-ME do recurso cidade_castelo_previa para ativação e detalhes.\n',encoding='utf-8')
changed=[];added=[]
try:
 for resource,source in [('cidade_castelo_livre',P/'terrain'),('cidade_castelo_previa',P/'package')]:
  dest=resources/resource
  for f in source.rglob('*'):
   if not f.is_file():continue
   rel=f.relative_to(source);target=dest/rel
   if target.exists() and sha(target)==sha(f):continue
   if not target.exists():added.append(target)
   target.parent.mkdir(parents=True,exist_ok=True);temp=target.with_name(target.name+'.castle-install');assert not temp.exists();shutil.copy2(f,temp);os.replace(temp,target);changed.append((resource,str(rel)))
  assert all(sha(dest/f.relative_to(source))==sha(f) for f in source.rglob('*') if f.is_file())
 assert cfg.read_bytes()==cfg_before,'Server config changed during installation; review'
except Exception:
 for target in added:
  if target.exists():target.unlink()
 for resource,rel in changed:
  old=backup/resource/rel
  if old.exists():shutil.copy2(old,resources/resource/rel)
 raise
report={'installed':True,'resources':list(expected),'changed_files':changed,'backup':str(backup),'server_cfg_unchanged':True,'live_activation_performed':False,'in_game_verified':False,'rotation_degrees':-30,'front_turned_degrees':-90,'road_width_m':5,'triangles':sum(r['triangles'] for r in pack['models']),'doors_and_unwanted_furniture_removed':True,'castle_blender_source':pack['source']}
(P/'instalacao.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
print('STRUCTURE_INSTALLED',len(changed),'changed files; only two castle resources; server.cfg unchanged',flush=True)
