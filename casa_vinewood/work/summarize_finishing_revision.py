import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood';D=R/'server-data/resources/cidade_mansao'
def read(name):return json.loads((W/name).read_text())
package=read('verificacao_fivem.json');doors=read('verificacao_portas_instaladas.json');windows=read('audit_janelas.json');plants=read('audit_vegetacao_todas_camadas.json');camera=read('verificacao_camera.json');pace=read('verificacao_movimento_lua.json');walk=read('verificacao_encaixe.json')
for name,q in package['files'].items():assert hashlib.sha256((D/'stream'/name).read_bytes()).hexdigest()==q['sha256']
assert all(q['passed'] for q in [doors,windows,camera,pace,walk]) and plants['intruding_instances']==0
report=dict(revision='acabamentos-camera-2026-10-07',installed_native_files=len(package['files']),installed_hashes_match=True,geometry=read('acabamentos_geometria.json'),landscape_changes=read('correcao_plantas_camadas.json'),landscape_instances_audited=len(plants['instances']),landscape_intrusions=plants['intruding_instances'],wall_camera_ray_tests=camera['wall_side_ray_tests'],camera_local_alignment_error_m=camera['world_local_alignment_error_m'],indoor_lua_behavior_cases=len(pace['cases']),walking_routes=len(walk['routes']),doors_or_accesses=doors['door_or_access_count'],door_directions_checked=doors['directions_checked'],window_regions=len(windows['window_panes']),sealed_windows=windows['sealed_panes'],activation_requires_resource_reload=True,in_game_camera_and_pace_test=False,previous_runtime_audit_revision=json.loads((D/'diagnostico_colisoes_runtime.json').read_text())['revision'])
(W/'correcao_acabamentos_camera.json').write_text(json.dumps(report,indent=2))
print('FINISHING_REVISION_COMPLETE',len(package['files']),'installed native files;',report['walking_routes'],'walking routes;',report['doors_or_accesses'],'doors/accesses;',report['window_regions'],'window regions;',report['landscape_intrusions'],'plant intrusions',flush=True)
