"""Promote the existing roof into an MLO root, without changing visible meshes.
Move the identical structural colliders into its local-space physics dictionary;
the fixed camera-only world bound and all movable props remain untouched.
"""
import sys,json,hashlib,shutil,copy
from pathlib import Path
from dataclasses import fields
from collections import Counter
P=Path(__file__).resolve().parent;R=P.parents[1];D=R/'server-data/resources/cidade_mansao'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps',str(R/'casa_vinewood/work/pydeps')]
import numpy as np
from shapely.geometry import Polygon,Point
from szio.gta5 import *
from szio.gta5.archetypes import *
from szio.gta5.entities import *
from szio.gta5.bounds import *
from szio.gta5.maps import *
from szio.types import Vector
B=P/'backup'; O=P/'package'; O.mkdir(exist_ok=True)
if not B.exists():
    shutil.copytree(D,B)
    (P/'baseline.json').write_text(json.dumps({f.relative_to(D).as_posix():hashlib.sha256(f.read_bytes()).hexdigest() for f in D.rglob('*') if f.is_file()},indent=2))
S=B/'stream';target=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
spec=json.loads((R/'casa_vinewood/encaixe_fachada.json').read_text())
ground=Polygon(spec['ground_polygon']).buffer(-.045,join_style=2)
upper=Polygon(spec['upper_polygon']).buffer(-.045,join_style=2)
g=list(ground.exterior.coords)[:-1];u=list(upper.exterior.coords)[:-1]
origin=json.loads((R/'casa_vinewood/medidas_estudo.json').read_text())['native_origin']
# Use one connected dry room for both floors, the stairs and double-height void.
# Separate YMAP structures retain their exact vertices, shaders and textures.
names=['mansao_paredes','mansao_pisos','mansao_escada','mansao_teto']
children=[];before=Counter();collider_counts={}
def tris(b):
    if isinstance(b,AssetBoundComposite):
        for child in b.children:
            if child:yield from tris(child)
    elif isinstance(b,AssetBoundBvh):
        for t in b.geometry_primitives:
            assert len(t.vertices)==3
            points=np.array([b.geometry_vertices[i].co for i in t.vertices])
            yield t,points
def key(p,mat):
    return (tuple(sorted(tuple(round(float(x),4) for x in v) for v in p)),mat.material_index,int(mat.material_flags))
for name in names:
    drawable=try_load_asset(S/(name+'.ydr'));assert isinstance(drawable.bounds,AssetBoundComposite)
    collider_counts[name]=0
    for bound in drawable.bounds.children:
        if bound is None:continue
        for t,points in tris(bound):
            before[key(points,t.material)]+=1;collider_counts[name]+=1
            # Room IDs are zero-based: limbo=0, dry interior=1.
            m=copy.copy(t.material);m.room_id=1;t.material=m
        children.append(bound)
    drawable.bounds=None;save_asset(drawable,target,O,name)
lo=np.min([b.bb_min for b in children],axis=0);hi=np.max([b.bb_max for b in children],axis=0)
root=AssetBoundComposite(children=children,bb_min=Vector(lo),bb_max=Vector(hi),centroid=Vector((lo+hi)/2),cg=Vector((lo+hi)/2),radius_around_centroid=float(np.linalg.norm(hi-lo)/2))
save_asset(root,target,O,'mansao_teto')
archetypes=try_load_asset(S/'cidade_mansao.ytyp')
roof=next(a for a in archetypes.archetypes if str(a.name)=='mansao_teto')
roof.type=ArchetypeType.MLO;roof.physics_dictionary='mansao_teto'
roof.bb_min=Vector(lo);roof.bb_max=Vector(hi);roof.bs_center=Vector((lo+hi)/2);roof.bs_radius=float(np.linalg.norm(hi-lo)/2)
portals=[]
for polygon,z0,z1 in [(ground,-.86,2.808),(upper,2.808,6.47)]:
    pts=list(polygon.exterior.coords)[:-1]
    if not polygon.exterior.is_ccw:pts.reverse()
    for a,b in zip(pts,pts[1:]+pts[:1]):
        # Outward winding; room 1 connects to the outdoor/limbo room 0.
        portals.append(MloPortal(1,0,0,0,0,0,tuple(Vector(v) for v in [(a[0],a[1],z0),(b[0],b[1],z0),(b[0],b[1],z1),(a[0],a[1],z1)]),[]))
roof.rooms=[
    MloRoom('limbo',Vector(lo),Vector(hi),1.0,'','',0,len(portals),0,-1,[]),
    MloRoom('mansao_seca',Vector([-9.35,-16.05,-.86]),Vector([14.5,9.9,6.47]),1.0,'mansao_ar_seco','',0,len(portals),0,-1,[])
]
roof.entities=[];roof.portals=portals;roof.entity_sets=[];roof.timecycle_modifiers=[]
save_asset(archetypes,target,O,'cidade_mansao')
worldmap=try_load_asset(S/'cidade_mansao.ymap');old_entity=next(e for e in worldmap.entities if str(e.archetype_name)=='mansao_teto')
new=EntityMloInstance(**{f.name:getattr(old_entity,f.name) for f in fields(Entity)},group_id=0,floor_id=0,default_entity_sets=[],num_exit_portals=len(portals),mlo_inst_flags=EntityMloInstanceFlags(0))
worldmap.entities=[new if e is old_entity else e for e in worldmap.entities]
worldmap.content_flags|=MapContentFlags.HAS_MLO_INSTANCE
save_asset(worldmap,target,O,'cidade_mansao')
config={'version':1,'origin':origin,'archetype':'mansao_teto','room':'mansao_seca','probe':[2,-7,1],
    'ground_polygon':g,'upper_polygon':u,'floor_z':-.86,'upper_z':2.808,'ceiling_z':6.47,'edge_hysteresis_m':.03}
(O/'clima_interior.json').write_text(json.dumps(config,indent=2))
# Round-trip verifies collider surfaces and all graphical bytes independently.
rt=try_load_asset(O/'mansao_teto.ybn');after=Counter(key(p,t.material) for t,p in tris(rt))
assert after==before,'Structural triangles/materials changed'
assert all(t.material.room_id==1 for t,_ in tris(rt))
graphical={}
for name in names:
    a=try_load_asset(S/(name+'.ydr'));b=try_load_asset(O/(name+'.ydr'));assert b.bounds is None
    count=0
    assert set(a.models)==set(b.models)
    for lod in a.models:
        assert len(a.models[lod])==len(b.models[lod])
        for x,y in zip(a.models[lod],b.models[lod]):
            assert len(x.geometries)==len(y.geometries)
            for gx,gy in zip(x.geometries,y.geometries):
                assert np.array_equal(gx.vertex_buffer,gy.vertex_buffer)
                assert np.array_equal(gx.index_buffer,gy.index_buffer);count+=len(gx.index_buffer)//3
    assert a.shader_group.embedded_textures.keys()==b.shader_group.embedded_textures.keys()
    for k,texture in a.shader_group.embedded_textures.items():
        assert texture.data.read_bytes()==b.shader_group.embedded_textures[k].data.read_bytes()
    graphical[name]={'vertices_uv_normals_and_indices_identical':True,'triangles_all_lods':count,'textures_identical':True,'collision_triangles':collider_counts[name]}
rtmap=try_load_asset(O/'cidade_mansao.ymap');assert len(rtmap.entities)==len(worldmap.entities)
rtroot=next(e for e in rtmap.entities if str(e.archetype_name)=='mansao_teto');assert isinstance(rtroot,EntityMloInstance)
rtar=next(a for a in try_load_asset(O/'cidade_mansao.ytyp').archetypes if str(a.name)=='mansao_teto')
assert rtar.type==ArchetypeType.MLO and len(rtar.rooms)==2 and len(rtar.portals)==len(portals)
(P/'native_verification.json').write_text(json.dumps({'mlo_root':'mansao_teto','rooms':2,'exit_portals':len(portals),'structural_collision_triangles':sum(before.values()),'collider_positions_materials_preserved':True,'graphical':graphical,'native_roundtrip':True,'in_game_verified':False},indent=2))
print('WEATHER_MLO_READY',len(portals),'portals;',sum(before.values()),'unchanged collision triangles')
