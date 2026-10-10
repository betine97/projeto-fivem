"""Record installed hashes and the remaining live-game check."""
import json,hashlib,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood';D=R/'server-data/resources/cidade_mansao'
def read(n):return json.loads((W/n).read_text())
install=read('verificacao_fivem.json');spec=read('aplicacao_materiais_sofa.json')
reports=['verificacao_materiais_sofa.json','verificacao_malha_mobiliario.json','verificacao_portas_moveis.json','verificacao_espessuras_exportadas.json','verificacao_encaixe.json','verificacao_camera.json','verificacao_juntas.json','verificacao_movimento_lua.json','verificacao_portas_instaladas.json','audit_janelas.json']
for n in reports:assert read(n)['passed'],n
for name,row in install['files'].items():assert hashlib.sha256((D/'stream'/name).read_bytes()).hexdigest()==row['sha256'],name
assert json.loads((D/'portas_madeira.json').read_text())==read('portas_madeira.json')
for name in ('auditoria_client.lua','auditoria_server.lua'):assert spec['revision'] in (D/name).read_text(encoding='utf-8')
for n in ('verificacao_materiais_sofa.json','verificacao_espessuras_exportadas.json'):
 for name,h in read(n)['drawable_sha256'].items():assert install['files'][name]['sha256']==h
report=dict(revision=spec['revision'],installed_native_files=len(install['files']),installed_hashes_match=True,backup=str(W/'backup_antes_piso_tv_portas'),editable_blender=str(W/'mansao_fivem_preparada.blend'),upper_wood_area_m2=spec['upper_floor_surface_m2']['wood'],upper_marble_area_m2=spec['upper_floor_surface_m2']['marble'],upper_wood_hall_bounds=spec['upper_wood_hall_bounds'],sofa_width_m=spec['sofa_bounds']['dimensions'][1],sofa_game_triangles=spec['sofa_game_triangles'],tv=spec['tv'],doors=read('portas_madeira.json')['doors'],furniture_mesh_quality=read('verificacao_malha_mobiliario.json')['mesh_checks'],walking_routes=len(read('verificacao_encaixe.json')['routes'])+len(read('verificacao_materiais_sofa.json')['walking_routes']),camera_wall_side_rays=read('verificacao_camera.json')['wall_side_ray_tests'],collision_triangles=install['collision_triangles'],checks=reports,activation_requires_resource_reload=True,in_game_verified=False,preview_files=[str(W/p) for p in ['sala_materiais_visao_geral.png','sala_sofa_frente.png','piso_superior_mezanino.png','porta_madeira_detalhe.png']])
(W/'correcao_piso_tv_portas.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
old=read('correcao_materiais_sofa.json');old['superseded_by']='correcao_piso_tv_portas.json';(W/'correcao_materiais_sofa.json').write_text(json.dumps(old,indent=2),encoding='utf-8')
shutil.copy2(W/'work/revision_cleanup.md',W/'LEIA-ME.md');shutil.copy2(W/'LEIA-ME.md',D/'README.md')
p=R/'README.md';text=p.read_text(encoding='utf-8');lines=text.splitlines()
for i,line in enumerate(lines):
 if line.startswith('Mansão Vinewood:'):
  lines[i]='Mansão Vinewood: mezanino em madeira, demais pisos em mármore, sofá de 5,20 m com malha fechada e mapas 4K, painel de TV e cinco portas de madeira com abertura por E. Revisão `piso-tv-portas-2026-10-07` instalada em `cidade_mansao`; use `restart cidade_mansao` no console do servidor e reconecte o FiveM. Fontes Blender, prévias e validações estão em [casa_vinewood/LEIA-ME.md](casa_vinewood/LEIA-ME.md). A confirmação visual no jogo permanece pendente.'
p.write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('FLOOR_TV_DOORS_INSTALLED',len(install['files']),'native files;',len(report['doors']),'doors;',report['walking_routes'],'walking routes; live-game check pending',flush=True)
