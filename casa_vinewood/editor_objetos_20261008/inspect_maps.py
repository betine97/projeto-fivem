import sys
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1]
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
from szio.gta5 import try_load_asset
D=R/'server-data/resources/cidade_mansao/stream'
for name in ['cidade_mansao','mansao_decoracao','mansao_vasos_autorais','mansao_referencias','mansao_cozinha_completa']:
    a=try_load_asset(D/(name+'.ymap'))
    print(name,len(a.entities))
    for i,e in enumerate(a.entities):
        if str(e.archetype_name)=='mansao_spot_embutido':continue
        print(i,str(e.archetype_name),tuple(round(float(v),3) for v in e.position),tuple(round(float(v),3) for v in e.rotation),e.scale_xy,e.scale_z)
