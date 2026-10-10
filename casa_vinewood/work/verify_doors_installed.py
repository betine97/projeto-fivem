"""Check door traversal both ways against the resource actually installed."""
from pathlib import Path
import hashlib,json
source=Path(__file__).with_name('verify_fit.py').read_text()
prefix=source.split('routes={}')[0]
prefix=prefix.replace("OUT=W/('backup_antes_limpeza/fivem' if BASELINE else 'fivem')", "OUT=R/'server-data/resources/cidade_mansao/stream'")
exec(prefix)
validation=json.loads((W/'verificacao_fivem.json').read_text())
for name,data in validation['files'].items():
 assert hashlib.sha256((OUT/name).read_bytes()).hexdigest()==data['sha256'],f'Installed file differs: {name}'
route_code='routes={}\n'+source.split('routes={}')[1].split("route('entrada_original'")[0]
exec(route_code)
exits={
 'Entrada original':[(5.85,-12.90,-.8),(7.10,-12.90,-.8),(7.7,-11.9,-.8)],
 'Sacada esquerda':[(-8.5,-5.17,-.8),(-9.77,-5.17,-.8)],
 'Sacada direita':[(13.6,-5.17,-.8),(15,-5.17,-.8)],
 'Sala para deck':[(-5.53,-12.4,-.8),(-5.53,-13.60,-.8)],
 'Porta dos fundos':[(-2.20,6.98,-.8),(-.40,6.98,-.8)],
 'Portao da rua':[(2.30,8.10,-.8),(2.30,6.65,-.8),(.10,6.65,-.8),(-.40,6.98,-.8),(-2.20,6.98,-.8)]
}
for d in spec['door_openings']:
 if d['key'] not in ('ground','upper') or d['name'] in ('Hall para Escada','Suite master lado hall'):continue
 a,b,z0,z1=d['opening'];center=(a+b)/2;fixed=d['fixed']
 pts=[(center,fixed-.45,z0),(center,fixed+.45,z0)] if d['axis']=='X' else [(fixed-.45,center,z0),(fixed+.45,center,z0)]
 exits[d['name']]=[(np.array(p)+O).tolist() for p in pts]
exits['Suite master lado hall']=[(-2,2.05,2.808),(-1.10,2.05,2.808)]
for name,points in exits.items():
 for direction,way in [('ida',points),('volta',points[::-1])]:route(name+' | '+direction,way)
results={'installed_directory':str(OUT),'installed_hashes_match':True,'door_or_access_count':len(exits),'directions_checked':len(routes),'body_clearance_and_floor_support_checked':True,'in_game_test':False,'routes':routes,'passed':all(r['passed'] for r in routes.values())}
results['collision_files_checked']=[p.name for p in collision_sources]
(W/'verificacao_portas_instaladas.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
for name,q in routes.items():
 if not q['passed']:print('FAILED',name,q)
print('INSTALLED_DOORS',len(exits),'accesses;',len(routes),'directions;',sum(q['samples'] for q in routes.values()),'samples;',results['passed'])
assert results['passed']
