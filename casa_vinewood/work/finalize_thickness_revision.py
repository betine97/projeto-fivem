"""Record the completed installation separately from pending live-game checks."""
import hashlib,json,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood';D=R/'server-data/resources/cidade_mansao'
def read(name):return json.loads((W/name).read_text())
spec=read('espessuras_estruturais.json');structural=read('verificacao_espessuras_exportadas.json')
fit=read('verificacao_encaixe.json');doors=read('verificacao_portas_instaladas.json')
glass=read('audit_janelas.json');camera=read('verificacao_camera.json');install=read('verificacao_fivem.json')
for result in (structural,fit,doors,glass,camera):assert result['passed']
for name,row in install['files'].items():
 assert hashlib.sha256((D/'stream'/name).read_bytes()).hexdigest()==row['sha256'],name
for name,digest in structural['drawable_sha256'].items():assert install['files'][name]['sha256']==digest
for name in ('auditoria_client.lua','auditoria_server.lua'):assert spec['revision'] in (D/name).read_text(encoding='utf-8')
prior_runtime=D/'diagnostico_colisoes_runtime.json'
runtime=json.loads(prior_runtime.read_text()) if prior_runtime.exists() else {}
report=dict(revision=spec['revision'],files_verified=True,installed_native_files=len(install['files']),installed_hashes_match=True,
 editable_blender=str(W/'mansao_fivem_preparada.blend'),backup=str(W/'backup_antes_espessuras'),
 dimensions_m={k:v for k,v in spec.items() if k.endswith('_thickness_m')},closed_structural_solids=spec['solid_count'],
 exported_wall_dimensions_checked=len(structural['wall_thickness_checks']),exported_slab_dimensions_checked=len(structural['slab_thickness_checks']),
 visible_triangles_checked=structural['visible_triangles_checked'],incorrect_exported_faces=structural['reversed_triangles'],
 missing_exported_faces=structural['missing_triangles'],front_face_edge_tests=structural['front_face_edge_tests'],
 stair_arrival_surface_overlap=structural['stair_arrival_surface_overlap'],walking_routes=len(fit['routes']),
 floor_scan=fit['full_floor_scan'],door_accesses=doors['door_or_access_count'],door_directions=doors['directions_checked'],
 window_regions=glass['window_panes'],sealed_windows=glass['sealed_panes'],camera_wall_side_rays=camera['wall_side_ray_tests'],
 collision_triangles=install['collision_triangles'],activation_requires_resource_reload=True,in_game_verified=False,
 previous_runtime_revision=runtime.get('revision'),preview_files=[str(W/'espessura_escada.png'),str(W/'espessura_paredes.png')])
(W/'correcao_espessuras.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
prior=W/'correcao_acabamentos_camera.json';old=json.loads(prior.read_text());old['superseded_by']='correcao_espessuras.json';prior.write_text(json.dumps(old,indent=2))
shutil.copy2(W/'work/revision_cleanup.md',W/'LEIA-ME.md')
print('STRUCTURAL_REVISION_INSTALLED',len(install['files']),'files;',spec['solid_count'],'closed solids; live-game confirmation pending')
