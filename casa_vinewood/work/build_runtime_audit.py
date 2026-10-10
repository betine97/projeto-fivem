"""Generate in-game capsule paths from the same door definitions as the model."""
import json
from pathlib import Path
W=Path(__file__).resolve().parents[1];R=W.parent
spec=json.loads((W/'medidas_estudo.json').read_text());offset=spec['interior_origin_relative_native']
routes={
 'Entrada original':[(5.85,-12.90,-.8),(7.10,-12.90,-.8),(7.7,-11.9,-.8)],
 'Sacada esquerda':[(-8.5,-5.17,-.8),(-9.77,-5.17,-.8)],
 'Sacada direita':[(13.6,-5.17,-.8),(15,-5.17,-.8)],
 'Sala para deck':[(-5.53,-12.4,-.8),(-5.53,-13.60,-.8)],
 'Porta dos fundos':[(-2.20,6.98,-.8),(-.40,6.98,-.8)],
 'Portao da rua':[(2.30,8.10,-.8),(2.30,6.65,-.8),(.10,6.65,-.8),(-.40,6.98,-.8),(-2.20,6.98,-.8)],
 'Sala perto do vidro':[(-7.75,-12.6,-.8),(.85,-12.6,-.8),(.85,-11.1,-.8)],
 'Sala antigo suporte':[(-7,-6.45,-.8),(-5.7,-6.45,-.8)],
 'Cozinha antigo suporte':[(10.7,-6.45,-.8),(12,-6.45,-.8)],
 'Escada':[(.4,1.45,-.8),(.4,4.45,1.004),(.4,5.05,1.004),(1.8,5.05,1.004),(1.8,4.45,1.004),(1.8,1.75,2.808),(1.8,1.40,2.808)],
 'Quarto superior':[(10.5,-12.5,2.808),(10.5,-8,2.808)],
}
for d in spec['door_openings']:
 if d['key'] not in ('ground','upper') or d['name'] in ('Hall para Escada','Suite master lado hall'):continue
 a,b,z0,z1=d['opening'];center=(a+b)/2;fixed=d['fixed']
 ps=[(center,fixed-.45,z0),(center,fixed+.45,z0)] if d['axis']=='X' else [(fixed-.45,center,z0),(fixed+.45,center,z0)]
 routes[d['name']]=[[v+o for v,o in zip(p,offset)] for p in ps]
routes['Suite master lado hall']=[(-2,2.05,2.808),(-1.1,2.05,2.808)]
p=R/'server-data/resources/cidade_mansao/auditoria_rotas.json'
p.write_text(json.dumps([{'name':n,'points':p} for n,p in routes.items()],ensure_ascii=False),encoding='utf-8')
print('RUNTIME_PATHS',len(routes))
