import json
from pathlib import Path
P=Path(__file__).resolve().parent; R=P.parents[1]; D=R/'server-data/resources/cidade_mansao'
original=json.loads((P/'backup/iluminacao_ambiente.json').read_text(encoding='utf-8-sig'))
c=json.loads(json.dumps(original))
c.update(night_multiplier=3.8,day_multiplier=.85,selection_distance=24)
c['budgets']={'ambient':14,'fixture':2,'pendant':2,'stair':2}
for light in c['lights']:
    if light['kind']=='ambient':
        high=light['position'][2]<2 and light['range']==8
        light['range']=12.5 if high else 8.5
        light['intensity']=2.25 if high else 1.8
        if light['level']=='terreo':light['position'][2]=2.5 if high else 1.25
    elif light['kind']=='fixture':
        # Fixtures add local detail; diffuse anchors provide overall room coverage.
        light['range']=max(light['range'],8.5)
        light['intensity']*=1.15
anchors=[
    ('sala_tv',[-5.7,-11.0,2.5],13,2.7),
    ('sala_sofa',[-5.4,-6.7,2.5],12,2.35),
    ('sala_janela',[-1.5,-11.0,2.8],12,2.35),
    ('jantar',[2.7,-8.3,2.5],12,2.45),
    ('sala_teto',[-5.5,-9.0,5.1],10,1.6),
    ('jantar_teto',[1.8,-8.0,5.1],10,1.6),
    ('cozinha_frente',[8.8,-10.6,1.35],9,2.3),
    ('cozinha_fundo',[12.0,-8.1,1.35],9,2.3),
]
for name,pos,reach,power in anchors:
    c['lights'].append({'id':'room_'+name,'kind':'ambient','level':'both' if 'teto' in name else 'terreo','position':pos,'rgb':[255,244,228],'range':reach,'intensity':power,'open_anchor':True})
assert sum(c['budgets'].values())==20 and c['max_lights']==24
(D/'iluminacao_ambiente.json').write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding='utf-8')
(P/'lighting_changes.json').write_text(json.dumps({'night_before':original['night_multiplier'],'night_after':c['night_multiplier'],'ambient_budget_before':original['budgets']['ambient'],'ambient_budget_after':14,'broad_open_room_anchors':len(anchors),'max_draw_calls_unchanged':24,'in_game_verified':False},indent=2))
print('LIGHTING_INSTALLED',len(anchors),'room anchors; cap remains 24')
