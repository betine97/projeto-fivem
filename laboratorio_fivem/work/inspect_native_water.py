"""Inspect native GTA puddle and rain-blocker drawables for the lab."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
from szio.rpf import open_rpf
from szio.gta5 import try_load_asset

base = Path(r'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V')
work = Path(__file__).parent
out = work / 'native_water_inspect'
out.mkdir(exist_ok=True)
names = {'v_34_puddle','v_55_tor_over_decal_puddles','po1_02_puddle','sc1_00g_b01_puddle',
         'ch3_01_puddle_13b','dt1_03_rain_blocker','id1_04_rain_blockers_10',
         'id1_07_rain_blocker00'}
cache = {}
for line in (work / 'assets_index.txt').read_text().splitlines():
    parts = line.split('|')
    if len(parts) != 3 or Path(parts[2]).stem not in names:
        continue
    key = (parts[0],parts[1])
    try:
        if key not in cache:
            cache[key] = open_rpf(base / parts[0]).open_nested(parts[1])
        path = out / parts[2]
        path.write_bytes(cache[key].read_bytes(parts[2]))
        asset = try_load_asset(path)
        xyz = np.concatenate([g.vertex_buffer[next(k for k in g.vertex_buffer.dtype.names if k.lower() == 'position')]
                              for models in asset.models.values() for model in models for g in model.geometries])
        print('\n',path.name, 'size',path.stat().st_size, 'xyz',np.round(xyz.min(0),3),np.round(xyz.max(0),3),
              'models',[(str(lod),len(models)) for lod,models in asset.models.items()],
              'bounds',type(asset.bounds).__name__ if asset.bounds else None,flush=True)
        for i,sh in enumerate(asset.shader_group.shaders):
            print('shader',i,str(getattr(sh,'name',None)),str(getattr(sh,'filename',None)),
                  [(p.name,str(p.value)[:90]) for p in sh.parameters if 'sampler' in p.name.lower()],flush=True)
        print('geoms',[(g.shader_index,len(g.index_buffer)//3) for models in asset.models.values() for m in models for g in m.geometries],flush=True)
    except Exception as exc:
        print(parts[2],'ERROR',repr(exc),flush=True)
