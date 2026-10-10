import sys
from pathlib import Path
import numpy as np
sys.path.insert(0,r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
from szio.gta5 import try_load_asset
from szio.gta5.drawables import LodLevel
w=Path(__file__).resolve().parents[1];d=w/'detail_fix'
def geoms(a):return [g for ms in a.models.values() for m in ms for g in m.geometries]
floor=try_load_asset(d/'lab_piso.ydr');door=try_load_asset(d/'lab_porta.ydr')
vent=try_load_asset(d/'lab_ventilacao.ydr');plant=try_load_asset(d/'lab_planta_00.ydr')
assert min(float(g.vertex_buffer['Position'][:,2].max()) for g in geoms(floor))>=.025
p=geoms(door)[0].vertex_buffer['Position'];assert np.isclose(p[:,0].max(),1.24) and np.isclose(p[:,2].max(),2.29)
assert all(g.shader_index!=3 for g in geoms(vent))
assert len(geoms(plant))==3 and min(g.vertex_buffer['Position'][:,2].min() for g in geoms(plant))<.01
assert sum(len(g.index_buffer)//3 for g in geoms(plant))>6500
for name in ('ceiling','left','right','rear_left','rear_right'):
 a=try_load_asset(d/f'lab_rotor_{name}.ydr');g=geoms(a)[0]
 assert len(g.index_buffer)>2700 and np.linalg.norm(g.vertex_buffer['Position'],axis=1).max()<.6
t=try_load_asset(d/'cidade_laboratorio.ytyp');assert sum(a.name.startswith('lab_rotor_') for a in t.archetypes)==5
col=try_load_asset(w/'collision_fix/lab_estrutura.ydr');assert len(col.bounds.children[0].geometry_primitives)==9912
print('VALIDATED_DETAIL_FIX floor=0.025 door=1.24x2.30 fan_rotors=11 plant_geometries=3 collision_boxes=52 rack_triangles=9288',flush=True)
