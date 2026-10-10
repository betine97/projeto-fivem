import json,hashlib,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood';dest=R/'server-data/resources/cidade_mansao/stream'
checks=json.loads((W/'verificacao_encaixe.json').read_text());assert checks['passed']
assert json.loads((W/'verificacao_juntas.json').read_text())['passed']
assert json.loads((W/'correcao_oclusao.json').read_text())['passed']
assert json.loads((W/'verificacao_camera.json').read_text())['passed']
assert json.loads((W/'verificacao_movimento_lua.json').read_text())['passed']
assert json.loads((W/'audit_vegetacao_todas_camadas.json').read_text())['intruding_instances']==0
validation=json.loads((W/'verificacao_fivem.json').read_text());installed={}
jantar=json.loads((W/'verificacao_jantar_cozinha.json').read_text());assert jantar['passed']
for name,digest in jantar['drawable_sha256'].items():assert digest==validation['files'][name]['sha256'],f'Dining validation is stale: {name}'
quality=json.loads((W/'verificacao_malha_mobiliario.json').read_text());assert quality['passed']
assert quality['sha256']==validation['files']['mansao_mobiliario.ydr']['sha256']
doors=json.loads((W/'verificacao_portas_moveis.json').read_text());assert doors['passed']
assert doors['leaf_sha256']==validation['files']['mansao_porta_madeira_095.ydr']['sha256']
finishes=json.loads((W/'verificacao_materiais_sofa.json').read_text());assert finishes['passed']
for name,digest in finishes['drawable_sha256'].items():assert digest==validation['files'][name]['sha256'],f'Material validation is stale: {name}'
thickness=json.loads((W/'verificacao_espessuras_exportadas.json').read_text());assert thickness['passed']
for name,digest in thickness['drawable_sha256'].items():assert digest==validation['files'][name]['sha256'],f'Structural validation is stale: {name}'
for name,data in validation['files'].items():
 src=W/'fivem'/name;dst=dest/name
 assert hashlib.sha256(src.read_bytes()).hexdigest()==data['sha256']
 shutil.copy2(src,dst);assert hashlib.sha256(dst.read_bytes()).hexdigest()==data['sha256'];installed[name]=data
validation.update(installed_files_match=True,installation_directory=str(dest),activation_requires_resource_reload=True,in_game_test=False)
(W/'verificacao_fivem.json').write_text(json.dumps(validation,indent=2))
for name in ['verificacao_fisica.json']:
 p=W/name;a=json.loads(p.read_text());a['superseded_by']='verificacao_encaixe.json';a['status']='Relatorio historico da primeira versao; nao descreve as colisoes instaladas atuais.';p.write_text(json.dumps(a,indent=2))
assert json.loads((W/'verificacao_limpeza_nativa.json').read_text())['passed']
shutil.copy2(W/'work/revision_cleanup.md',W/'LEIA-ME.md')
print('INSTALLED',len(installed),'native files;',len(checks['routes']),'walking routes passed')
