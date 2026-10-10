"""Verify the installed resource and record the pending live-game inspection."""
import json,hashlib,shutil,re
from pathlib import Path
from datetime import datetime
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood';D=R/'server-data/resources/cidade_mansao'
def read(name):return json.loads((W/name).read_text())
validation=read('verificacao_fivem.json');spec=read('componentes_jantar_cozinha.json');revision=spec['revision']
reports=['verificacao_jantar_cozinha.json','verificacao_materiais_sofa.json','verificacao_malha_mobiliario.json','verificacao_portas_moveis.json','verificacao_espessuras_exportadas.json','verificacao_encaixe.json','verificacao_camera.json','verificacao_juntas.json','verificacao_movimento_lua.json','verificacao_portas_instaladas.json','audit_janelas.json']
for name in reports:assert read(name)['passed'],name
for name,row in validation['files'].items():
 for directory in (W/'fivem',D/'stream'):assert hashlib.sha256((directory/name).read_bytes()).hexdigest()==row['sha256'],name
extras=sorted(p.name for p in (D/'stream').iterdir() if p.is_file() and p.name not in validation['files']);assert not extras,extras
assert len(validation['files'])==42
for name in ('luzes_pendentes.json','portas_madeira.json'):assert json.loads((D/name).read_text())==read(name)
assert (D/'luzes_pendentes.lua').read_bytes()==(W/'work/luzes_pendentes.lua').read_bytes()
manifest=(D/'fxmanifest.lua').read_text();registered=re.findall(r"(?:client|server)_script\s+'([^']+)'",manifest)
assert len(registered)==7 and all((D/name).is_file() for name in registered)
assert "'luzes_pendentes.json'" in manifest
for name in ('auditoria_client.lua','auditoria_server.lua'):assert revision in (D/name).read_text(encoding='utf-8')
assert re.search(r'^\s*ensure\s+cidade_mansao\s*$',(R/'server-data/server.cfg').read_text(),re.M)
for report in ('verificacao_jantar_cozinha.json','verificacao_materiais_sofa.json','verificacao_espessuras_exportadas.json'):
 for name,h in read(report)['drawable_sha256'].items():assert validation['files'][name]['sha256']==h
previews=['jantar_cozinha_visao_geral.png','mesa_jantar_detalhe.png','ilha_cozinha_detalhe.png']
assert all((W/name).is_file() for name in previews)
report=dict(checked_at=datetime.now().astimezone().isoformat(),revision=revision,passed=True,installed_native_files=42,installed_hashes_match=True,registered_scripts=registered,light_points=9,components=spec['assets'],checks={name:True for name in reports},backup=str(W/'backup_antes_jantar_cozinha'),editable_blender=str(W/'mansao_fivem_preparada.blend'),preview_files=[str(W/name) for name in previews],activation_requires_resource_reload=True,in_game_verified=False,extra_stream_files=extras,failures=[])
(W/'instalacao_jantar_cozinha.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
audit=dict(report);audit.pop('components');audit['native_files_checked']=42;audit['native_files_match_final_export']=True;audit['resource_enabled_in_server_cfg']=True;audit['door_count']=5
(W/'auditoria_instalacao_final.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
old=read('correcao_piso_tv_portas.json');old['superseded_by']='instalacao_jantar_cozinha.json';(W/'correcao_piso_tv_portas.json').write_text(json.dumps(old,indent=2),encoding='utf-8')
shutil.copy2(W/'work/revision_jantar_cozinha.md',W/'LEIA-ME.md');shutil.copy2(W/'LEIA-ME.md',D/'README.md')
p=R/'README.md';s=p.read_text(encoding='utf-8');lines=s.splitlines()
for i,line in enumerate(lines):
 if line.startswith('Mansão Vinewood:'):lines[i]='Mansão Vinewood: sala com sofá e TV, mesa de jantar com oito cadeiras, ilha com quatro banquetas e dois pendentes com iluminação quente. Revisão `jantar-cozinha-2026-10-07` instalada em `cidade_mansao`; use `restart cidade_mansao` no console e reconecte o FiveM. Fontes Blender, prévias e verificações em [casa_vinewood/LEIA-ME.md](casa_vinewood/LEIA-ME.md). Confirmação visual no jogo pendente.'
p.write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('DINING_KITCHEN_INSTALLED 42 native files; 4 components; 9 lights; 11 validation reports passed; live-game inspection pending',flush=True)
