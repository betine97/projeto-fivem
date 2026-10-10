import sys,json,gc
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1];D=R/'server-data/resources/cidade_mansao'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import pymateria.gta5 as pm
import pymateria.gta5.gen8 as g8
rows=[]
for path in sorted((D/'stream').glob('*.ydr')):
    a=g8.Drawable.import_rsc(path).result;emission=[]
    for i,s in enumerate(a.shader_group.shaders):
        for p in s.parameters:
            if p.name==pm.HashString('emissivemultiplier'):
                emission.append(dict(shader_index=i,preset=s.basis_material.string_or_placeholder,power=float(p.data[0][0])))
    if len(a.lights) or emission:
        row=dict(file=path.name,native_lights=len(a.lights),emission=emission);rows.append(row);print(row,flush=True)
    del a;gc.collect()
(P/'audit.json').write_text(json.dumps(rows,indent=2))
