"""Broad room fill, ceiling diffusion and pooled pendant/stair lights."""
import json
from pathlib import Path
P=Path(__file__).resolve().parent
R=P.parents[1]/'server-data/resources/cidade_mansao'
cfg=json.loads((R/'decoracao_iluminacao.json').read_text())
pendants=json.loads((R/'luzes_pendentes.json').read_text())['lights']
rows=[]
for spot in cfg['spots']:
    x,y,z=spot['position'];floor=-.8 if spot['level']=='terreo' else 2.808
    tall=spot['ceiling_z']-floor>4
    rows.append(dict(id='fill_'+str(spot['id']),kind='ambient',level=spot['level'],
        position=[x,y,floor+(2.2 if tall else 1.8)],rgb=[255,239,218],
        range=8.0 if tall else 6.6,intensity=1.75 if tall else 1.4))
    rows.append(dict(id='ceiling_'+str(spot['id']),kind='fixture',level=spot['level'],
        position=[x,y,z-.30],rgb=[255,232,198],range=7.5 if tall else 5.8,
        intensity=1.05 if tall else .8))
# Six neighbouring dining cylinders share two broad light volumes. The kitchen
# bar shares one volume. All physical emitters remain visible in streamed geometry.
for ident,group in [('dining_a',pendants[:3]),('dining_b',pendants[3:6]),('kitchen',pendants[6:])]:
    pos=[sum(p['position'][i] for p in group)/len(group) for i in range(3)]
    rows.append(dict(id=ident,kind='pendant',level='terreo',position=pos,
        rgb=[255,226,187],range=6.2,intensity=1.5))
stairs=sorted(cfg['stairs'],key=lambda q:q['position'][2])
for i in range(0,len(stairs),5):
    group=stairs[i:i+5];pos=[sum(p['position'][axis] for p in group)/len(group) for axis in range(3)]
    rows.append(dict(id='stair_'+str(i//5),kind='stair',level='both',position=pos,
        rgb=[255,213,163],range=2.4,intensity=.48))
out=dict(origin=cfg['origin'],night_multiplier=2.2,day_multiplier=.6,
    max_lights=24,selection_ms=200,fade_ms=450,selection_distance=14,
    budgets=dict(ambient=8,fixture=6,pendant=3,stair=3),lights=rows,
    description='Diffuse point lights and broad bounce fill; no spotlight cones or shadow passes.')
(P/'iluminacao_ambiente.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print('BROAD_LIGHTS_CONFIG',len(rows),'candidates; <=24 drawn per frame')
