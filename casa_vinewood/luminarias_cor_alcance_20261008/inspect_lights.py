import sys,json
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1];D=R/'server-data/resources/cidade_mansao'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
from szio.gta5 import try_load_asset
import pymateria.gta5.gen8 as g8
from collections import Counter
import numpy as np
for n in ['mansao_teto','mansao_spot_embutido','mansao_pendentes','mansao_spots_led']:
    a=try_load_asset(D/'stream'/f'{n}.ydr');raw=g8.Drawable.import_rsc(D/'stream'/f'{n}.ydr').result
    print(n,'LIGHTS',len(a.lights),'BOUND',type(a.bounds).__name__)
    for i,s in enumerate(a.shader_group.shaders):
        if n=='mansao_spot_embutido' or s.preset_filename=='emissive.sps':print('shader',i,s.name,s.preset_filename,[(p.name,p.value) for p in s.parameters])
    for lod,ms in a.models.items():
        if lod.name!='HIGH':continue
        for m in ms:
            for g in m.geometries:
                p=g.vertex_buffer['Position']
                if n!='mansao_spots_led':print('geom',g.shader_index,len(g.index_buffer)//3,'bbox',p.min(0).tolist(),p.max(0).tolist())
                if n=='mansao_pendentes' and g.shader_index==1 and p[:,0].mean()<5:
                    # Vertical histogram exposes actual cap elevations rather than the old guessed points.
                    h=Counter(round(float(z),2) for z in p[:,2]);print('emissive height peaks',h.most_common(18))
    print('native light props',str(raw.lights[0])[:300] if raw.lights else 'none')
for n in ['cidade_mansao','mansao_referencias','mansao_decoracao']:
    a=try_load_asset(D/'stream'/f'{n}.ymap');print(n,Counter(str(e.archetype_name) for e in a.entities))
    if n=='mansao_referencias':
        origin=np.array(json.loads((D/'luzes_pendentes.json').read_text())['origin'])
        rows=[{'position':(np.array(e.position)-origin).tolist(),'rotation':list(e.rotation)} for e in a.entities if str(e.archetype_name)=='mansao_spot_embutido']
        (P/'spots_instalados.json').write_text(json.dumps(rows,indent=2))
