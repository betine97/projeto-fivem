import sys,json
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1];D=R/'server-data/resources/cidade_mansao'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from szio.gta5 import try_load_asset,LodLevel
for name in ['mansao_paredes','mansao_vidros','mansao_porta_vidro_aparador','mansao_bar_referencia']:
    a=try_load_asset(D/'stream'/f'{name}.ydr')
    ps=np.concatenate([g.vertex_buffer['Position'] for m in a.models[LodLevel.HIGH] for g in m.geometries])
    print(name,ps.min(0),ps.max(0))
    if name=='mansao_paredes':
        for label,axis,limits,otheraxis,otherlimits in [('bar',0,[5,9],1,[-15,-12]),('sala',1,[-6.5,-3.5],0,[-9.5,-8.5])]:
            q=ps[(ps[:,axis]>limits[0])&(ps[:,axis]<limits[1])&(ps[:,otheraxis]>otherlimits[0])&(ps[:,otheraxis]<otherlimits[1])&(ps[:,2]<2)]
            print(label,'coordinates',[np.unique(np.round(q[:,i],4)).tolist() for i in range(3)])
    if name=='mansao_porta_vidro_aparador':print('shaders',[(s.name,s.preset_filename) for s in a.shader_group.shaders]);print('bound',a.bounds)
print('origin doors',json.loads((D/'portas_madeira.json').read_text())['origin'])
