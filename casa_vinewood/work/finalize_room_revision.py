"""Record the verified installation and keep live-game confirmation separate."""
import json,hashlib,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood';D=R/'server-data/resources/cidade_mansao'
def read(name):return json.loads((W/name).read_text())
spec=read('aplicacao_materiais_sofa.json');material=read('verificacao_materiais_sofa.json');install=read('verificacao_fivem.json')
structural=read('verificacao_espessuras_exportadas.json');fit=read('verificacao_encaixe.json');doors=read('verificacao_portas_instaladas.json');glass=read('audit_janelas.json');camera=read('verificacao_camera.json')
for q in (material,structural,fit,doors,glass,camera):assert q['passed']
for name,row in install['files'].items():assert hashlib.sha256((D/'stream'/name).read_bytes()).hexdigest()==row['sha256'],name
for q in (material,structural):
 for name,h in q['drawable_sha256'].items():assert install['files'][name]['sha256']==h
for name in ('auditoria_client.lua','auditoria_server.lua'):assert spec['revision'] in (D/name).read_text(encoding='utf-8')
runtime_path=D/'diagnostico_colisoes_runtime.json';runtime=json.loads(runtime_path.read_text()) if runtime_path.exists() else {}
report=dict(revision=spec['revision'],installed_native_files=len(install['files']),installed_hashes_match=True,source_assets=str(W/'source_assets'),backup=str(W/'backup_antes_materiais_sofa'),editable_blender=str(W/'mansao_fivem_preparada.blend'),finish_objects=spec['finish_objects'],tv_wall_objects=spec['tv_wall_objects'],sofa_width_m=material['sofa_width_m'],sofa_bounds=spec['sofa_bounds'],sofa_game_triangles=spec['sofa_game_triangles'],sofa_original_triangles=spec['sofa_original_triangles'],sofa_physics_components=spec['physics_components'],material_surface_probes=material['architectural_material_surface_probes'],sofa_uv_probes=material['sofa_source_uv_probes'],walking_routes=len(fit['routes'])+len(material['walking_routes']),floor_scan=fit['full_floor_scan'],door_accesses=doors['door_or_access_count'],door_directions=doors['directions_checked'],closed_structural_solids=read('espessuras_estruturais.json')['solid_count'],camera_wall_side_rays=camera['wall_side_ray_tests'],collision_triangles=install['collision_triangles'],activation_requires_resource_reload=True,in_game_verified=False,previous_runtime_revision=runtime.get('revision'),preview_files=[str(W/'sala_materiais_visao_geral.png'),str(W/'sala_sofa_frente.png')])
(W/'correcao_materiais_sofa.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
old=read('correcao_espessuras.json');old['superseded_by']='correcao_materiais_sofa.json';(W/'correcao_espessuras.json').write_text(json.dumps(old,indent=2),encoding='utf-8')
shutil.copy2(W/'work/revision_cleanup.md',W/'LEIA-ME.md');shutil.copy2(W/'LEIA-ME.md',D/'README.md')
print('ROOM_REVISION_INSTALLED',len(install['files']),'native files;',report['walking_routes'],'walking routes;',material['architectural_material_surface_probes'],'material probes; live-game confirmation pending',flush=True)
