"""Always-on native lights in the existing MLO root, with no player-based pool.
Keep meshes, materials, weather rooms, camera and movable objects unchanged.
"""
import sys,json,math,shutil,hashlib
from pathlib import Path
from dataclasses import fields
P=Path(__file__).resolve().parent;R=P.parents[1];D=R/'server-data/resources/cidade_mansao'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps',str(R/'casa_vinewood/work/pydeps')]
import numpy as np
from shapely.geometry import Polygon,box,Point
from szio.gta5 import *
from szio.gta5.drawables import Light,LightType,LightFlashiness
from szio.types import Vector
import pymateria.gta5 as pm
B=P/'backup';O=P/'package';O.mkdir(parents=True,exist_ok=True)
if not B.exists():
    shutil.copytree(D,B)
    (P/'baseline.json').write_text(json.dumps({f.relative_to(D).as_posix():hashlib.sha256(f.read_bytes()).hexdigest() for f in D.rglob('*') if f.is_file()},indent=2))
climate=json.loads((B/'clima_interior.json').read_text());origin=climate['origin']
footprints={level:Polygon(climate[key]) for level,key in [('terreo','ground_polygon'),('superior','upper_polygon')]}
study=json.loads((R/'casa_vinewood/medidas_estudo.json').read_text())
rows=[];regions=[];boost=[]
def add(ident,room,level,pos,radius,power,accent=False,shadow=False):
    # White/cream fill preserves wall and fabric colours; warm accents add depth.
    rows.append(dict(id=ident,room=room,level=level,position=pos,rgb=[255,228,195] if accent else [255,243,228],
        range=radius,intensity=power,falloff_exponent=16 if accent else 12,
        kind='accent' if accent else 'ambient',shadow=shadow))
for n,room in enumerate(study['rooms']):
    level,name=room['level'],room['name'];a,b,c,d=room['bounds']
    # The fitted facade changed the rear extent of the western rooms.
    a-=8.8;b-=8.8;c-=12.85;d-=12.85
    if d>=7.1 and b<-.65:d=9.65
    shape=box(a+.18,c+.18,b-.18,d-.18).intersection(footprints[level].buffer(-.10))
    if shape.is_empty:continue
    tall=level=='terreo' and name in ['Sala de estar','Sala de jantar']
    z=4.25 if tall else (1.92 if level=='terreo' else 5.88)
    # Native volumes replace the old 88 coincident fills and 8 huge anchors.
    # Compact grids cover each room rather than piling all lights near the player.
    minx,miny,maxx,maxy=shape.bounds
    nx=max(1,math.ceil((maxx-minx)/4.8));ny=max(1,math.ceil((maxy-miny)/4.8))
    radius=7.4 if tall else (5.5 if max(maxx-minx,maxy-miny)>4 else 4.4)
    power=5.2 if tall else 2.8
    roompoints=[]
    for i in range(nx):
        for j in range(ny):
            x=minx+(i+.5)*(maxx-minx)/nx;y=miny+(j+.5)*(maxy-miny)/ny
            if not shape.covers(Point(x,y)):continue
            pos=[round(x,3),round(y,3),z]
            add(f'room_{n}_{i}_{j}',name,level,pos,radius,power)
            roompoints.append(pos)
    if not roompoints:
        q=shape.representative_point();pos=[q.x,q.y,z];add(f'room_{n}',name,level,pos,radius,power);roompoints.append(pos)
    # One optional additive adjustment per room; baseline lives entirely in YDR.
    q=shape.representative_point()
    boost.append(dict(id='boost_'+str(n),kind='ambient',level=level,position=[q.x,q.y,z],rgb=[255,243,228],range=radius+1,intensity=.65))
    regions.append(dict(name=name,level=level,polygon=list(shape.exterior.coords),light_ids=[r['id'] for r in rows if r['room']==name and r['level']==level]))
# Dedicated vertical fill lights reach the tall walls, not just the floor.
for ident,pos,radius,power,shadow in [
    ('tv_wall',[-6.1,-11.5,3.05],5.8,2.1,True),
    ('living_wall',[-7.45,-7.8,4.1],5.4,1.6,False),
    ('dining_wall',[2.5,-10.15,4.2],5.6,1.8,True),
    ('piano_wall',[4.65,-4.95,3.45],5.0,1.6,False),
    ('kitchen_worktop',[13.3,-9.7,1.25],3.2,1.1,True),
    ('kitchen_island',[10.45,-9,1.85],4.5,1.5,False),
    ('stair_landing',[.6,4.0,1.5],3.6,1.2,False),
    ('stair_upper',[1.3,2.0,4.25],3.6,1.2,False),
    ('living_ceiling',[-4.6,-8.75,5.9],6.8,1.5,False),
    ('dining_ceiling',[2.8,-8.4,5.9],6.8,1.5,False),
]:add(ident,'Destaques', 'both',pos,radius,power,True,shadow)
assert len(boost)<=24
assert all(footprints['superior' if r['position'][2]>2.808 else 'terreo'].covers(Point(r['position'][:2])) for r in rows)
flags=(pm.LightFlags.BOTH_INTERIOR_AND_EXTERIOR|pm.LightFlags.FX|pm.LightFlags.DONT_LIGHT_ALPHA)
native=[]
for i,r in enumerate(rows):
    f=flags
    if r['kind']=='ambient':f|=pm.LightFlags.NO_SPECULAR
    if r['shadow']:f|=pm.LightFlags.CAST_SHADOWS|pm.LightFlags.CAST_STATIC_GEOM_SHADOWS|pm.LightFlags.CAST_DYNAMIC_GEOM_SHADOWS|pm.LightFlags.CAST_ONLY_LOWRES_SHADOWS
    native.append(Light(light_type=LightType.POINT,position=Vector(r['position']),direction=Vector([0,0,-1]),tangent=Vector([1,0,0]),extent=Vector([1,1,1]),
        color=tuple(r['rgb']),flashiness=LightFlashiness.CONSTANT,intensity=r['intensity'],flags=f.value,time_flags=0xFFFFFF,
        bone_id=0,group_id=0,light_hash=i+1,falloff=r['range'],falloff_exponent=r['falloff_exponent'],
        culling_plane_normal=Vector([0,0,0]),culling_plane_offset=0,volume_intensity=0,volume_size_scale=1,
        volume_outer_color=tuple(r['rgb']),volume_outer_intensity=0,volume_outer_exponent=1,
        corona_size=0,corona_intensity=0,corona_z_bias=0,projected_texture_hash='',light_fade_distance=120,
        shadow_fade_distance=35 if r['shadow'] else 0,specular_fade_distance=50 if r['kind']=='accent' else 0,
        volumetric_fade_distance=0,shadow_near_clip=.10,shadow_blur=140,cone_inner_angle=0,cone_outer_angle=0))
roof=try_load_asset(B/'stream/mansao_teto.ydr');assert not roof.lights
roof.lights=native;save_asset(roof,(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),),O,'mansao_teto')
rt=try_load_asset(O/'mansao_teto.ydr');assert len(rt.lights)==len(native) and rt.bounds is None
before=try_load_asset(B/'stream/mansao_teto.ydr')
for lod in before.models:
    for a,b in zip(before.models[lod],rt.models[lod]):
        for ga,gb in zip(a.geometries,b.geometries):
            assert np.array_equal(ga.vertex_buffer,gb.vertex_buffer) and np.array_equal(ga.index_buffer,gb.index_buffer)
for k,tx in before.shader_group.embedded_textures.items():assert tx.data.read_bytes()==rt.shader_group.embedded_textures[k].data.read_bytes()
for a,b in zip(native,rt.lights):
    assert tuple(a.position)==tuple(b.position) or np.allclose(a.position,b.position,atol=1e-5)
    assert a.flags==b.flags and a.time_flags==b.time_flags and a.color==b.color
    assert math.isclose(a.intensity,b.intensity,rel_tol=1e-6)
config=dict(version=2,origin=origin,native_always_on=True,native_count=len(rows),max_lights=len(boost),activation_distance=120,lights=boost,
    description='Permanent native lights cover all rooms. Lua only supplies an optional uniform additive boost above luzmansao 1.')
(O/'iluminacao_ambiente.json').write_text(json.dumps(config,indent=2),encoding='utf-8')
(P/'projeto_luminotecnico.json').write_text(json.dumps(dict(origin=origin,lights=rows,regions=regions,description='Fixed room fill, vertical wall wash and restrained shadow accents; permanent all hours.'),ensure_ascii=False,indent=2),encoding='utf-8')
(P/'native_verification.json').write_text(json.dumps(dict(native_roundtrip=True,native_lights=len(rows),rooms=len(regions),all_hours=True,constant=True,
    visible_from_exterior=True,shadows=sum(r['shadow'] for r in rows),volumetric_lights=0,coronas=0,mesh_uv_normals_indices_textures_preserved=True,
    old_candidates=196,optional_script_boost=len(boost),default_script_draws=0,roof_file_bytes=(O/'mansao_teto.ydr').stat().st_size,
    bytes_added=(O/'mansao_teto.ydr').stat().st_size-(B/'stream/mansao_teto.ydr').stat().st_size,in_game_verified=False),indent=2))
print('PERMANENT_LIGHTS_READY',len(rows),'native lights;',len(regions),'rooms; optional boost',len(boost))
