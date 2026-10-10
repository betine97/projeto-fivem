"""Package native props, shared artwork textures and preserved architecture physics."""
import sys,json,math,copy,struct,re
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1];OUT=P/'stream';D=R/'server-data/resources/cidade_mansao/stream'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from szio.gta5 import *
from szio.gta5.bounds import *
from szio.gta5.entities import *
from szio.gta5.maps import *
from szio.types import Vector,Quaternion,DataSource
TARGET=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
report=json.loads((P/'modeling_report.json').read_text());arts=json.loads((P/'artworks.json').read_text())
origin=np.array(json.loads((D.parent/'decoracao_iluminacao.json').read_text())['origin'])
def load(path):
    a=try_load_asset(path);assert a is not None,path;return a
def save(a,name):save_asset(a,TARGET,OUT,name)
def key(shader):return shader.preset_filename,tuple((p.name,p.value) for p in shader.parameters if isinstance(p.value,str))
def bounds_of(asset,lod=LodLevel.HIGH):
    p=np.concatenate([g.vertex_buffer['Position'] for m in asset.models[lod] for g in m.geometries]);return p.min(0),p.max(0)
def exact_dds(tex):
    path=P/'textures'/(tex.name+'.dds');assert path.is_file(),path
    data=path.read_bytes();h,w=struct.unpack_from('<II',data,12)
    return EmbeddedTexture(tex.name,w,h,DataSource.create(data,name=tex.name+'.dds'))
def prepared_texture(name):
    data=(P/'textures'/(name+'.dds')).read_bytes();h,w=struct.unpack_from('<II',data,12)
    return EmbeddedTexture(name,w,h,DataSource.create(data,name=name+'.dds'))
def remap(asset,shaders):
    mapping={i:next(j for j,s in enumerate(shaders) if key(s)==key(old)) for i,old in enumerate(asset.shader_group.shaders)}
    for models in asset.models.values():
        for m in models:
            for g in m.geometries:g.shader_index=mapping[g.shader_index]

# Keep every architectural shader value, texture byte and existing collider.
for name in ['mansao_pisos','mansao_teto']:
    original=load(D/(name+'.ydr'));a=load(OUT/(name+'.ydr'))
    remap(a,original.shader_group.shaders);a.shader_group=original.shader_group;a.bounds=original.bounds
    save(a,name)

# All ceiling fixtures share a single small drawable with four real mesh LODs.
spot=load(OUT/'ref_spot_48.ydr');spot.name='mansao_spot_embutido';spot.bounds=None
spot.shader_group.embedded_textures={k:exact_dds(t) for k,t in spot.shader_group.embedded_textures.items()}
triangles={}
for lod,segments in [(LodLevel.HIGH,48),(LodLevel.MEDIUM,24),(LodLevel.LOW,12),(LodLevel.VERYLOW,8)]:
    variant=load(OUT/f'ref_spot_{segments}.ydr');remap(variant,spot.shader_group.shaders)
    spot.models[lod]=variant.models[LodLevel.HIGH]
    triangles[lod.name]=sum(len(g.index_buffer)//3 for m in spot.models[lod] for g in m.geometries)
spot.lod_thresholds={LodLevel.HIGH:5.,LodLevel.MEDIUM:12.,LodLevel.LOW:30.,LodLevel.VERYLOW:70.}
save(spot,spot.name)

material_names=re.findall(r'CollisionMaterialDef\("([A-Z_0-9]+)"',Path(r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/sollumz/Sollumz/ybn/collision_materials.py').read_text())
FACES=[(0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),(1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)]
def box_bound(lo,hi):
    vertices=np.array([(lo[0],lo[1],lo[2]),(hi[0],lo[1],lo[2]),(hi[0],hi[1],lo[2]),(lo[0],hi[1],lo[2]),
                       (lo[0],lo[1],hi[2]),(hi[0],lo[1],hi[2]),(hi[0],hi[1],hi[2]),(lo[0],hi[1],hi[2])])
    b=AssetBoundBvh();b.margin=.001
    b.composite_collision_type_flags=CollisionFlags.MAP_TYPE_WEAPON|CollisionFlags.MAP_TYPE_MOVER|CollisionFlags.MAP_TYPE_HORSE|CollisionFlags.MAP_TYPE_COVER|CollisionFlags.MAP_TYPE_VEHICLE
    b.composite_collision_include_flags=CollisionFlags(0xffffffff)
    b.geometry_vertices=[BoundVertex(Vector(v),None) for v in vertices]
    b.geometry_primitives=[BoundPrimitive.new_triangle(*f,CollisionMaterial.from_packed(material_names.index('WOOD_SOLID_MEDIUM'))) for f in FACES]
    b.bb_min=Vector(lo);b.bb_max=Vector(hi);b.centroid=Vector((lo+hi)/2);b.cg=b.centroid;b.radius_around_centroid=float(np.linalg.norm(hi-lo)/2)
    comp=AssetBoundComposite(children=[b]);comp.bb_min=b.bb_min;comp.bb_max=b.bb_max;comp.centroid=b.centroid;comp.cg=b.cg;comp.radius_around_centroid=b.radius_around_centroid
    return comp
def archetype(name,lo,hi,texture_dict='',dist=100):
    return Archetype(name,ArchetypeType.BASE,32,dist,0,dist,texture_dict,'','',name,
                     Vector(lo),Vector(hi),Vector((lo+hi)/2),float(np.linalg.norm(hi-lo)/2),name,ArchetypeAssetType.DRAWABLE,[])
lo,hi=bounds_of(spot);types=[archetype(spot.name,lo,hi,dist=70)]
shared={}
for art in arts:
    a=load(OUT/(art['model']+'.ydr'));lo,hi=bounds_of(a)
    a.bounds=box_bound(lo,hi)
    required={p.value for s in a.shader_group.shaders for p in s.parameters if isinstance(p.value,str)}
    for k in required:
        t=prepared_texture(k)
        if k in shared:assert shared[k].data.read_bytes()==t.data.read_bytes()
        shared[k]=t
    a.shader_group.embedded_textures={};save(a,art['model'])
    types.append(archetype(art['model'],lo,hi,'mansao_quadros_refs',dist=100))
    art['native_bounds']={'lo':lo.tolist(),'hi':hi.tolist()}
save(AssetTextureDictionary(textures=shared),'mansao_quadros_refs')
save(AssetMapTypes(name='mansao_referencias',archetypes=types),'mansao_referencias')

# Original map stays intact, including the rug LODs, plants, existing paintings.
stair=load(OUT/'mansao_spots_led.ydr');stair.bounds=None;save(stair,'mansao_spots_led')
lo,hi=bounds_of(stair);decor=load(D/'mansao_decoracao.ytyp')
target=next(a for a in decor.archetypes if str(a.name)=='mansao_spots_led')
target.bb_min=Vector(lo);target.bb_max=Vector(hi);target.bs_center=Vector((lo+hi)/2);target.bs_radius=float(np.linalg.norm(hi-lo)/2)
save(decor,'mansao_decoracao')

entities=[];ext=[]
byname={a.name:a for a in types}
def entity(name,position,heading,dist):
    p=origin+np.array(position);q=[math.cos(heading/2),0,0,-math.sin(heading/2)]
    entities.append(Entity(name,Vector(p),Quaternion(q),1,1,EntityFlags.IS_STATIC,0,-1,dist,0,EntityLodLevel.ORPHANHD,EntityPriorityLevel.REQUIRED,0,255,255,0,[]))
    ar=byname[name];lo=np.array(ar.bb_min);hi=np.array(ar.bb_max)
    rot=np.array([[math.cos(heading),-math.sin(heading),0],[math.sin(heading),math.cos(heading),0],[0,0,1]])
    corners=np.array([[x,y,z] for x in [lo[0],hi[0]] for y in [lo[1],hi[1]] for z in [lo[2],hi[2]]])
    ext.extend(corners@rot.T+p)
for row in report['spots']:entity(spot.name,row['position'],0,70)
for art in arts:entity(art['model'],art['position'],art['heading'],100)
lo=np.array(ext).min(0)-.1;hi=np.array(ext).max(0)+.1
save(AssetMapData(name='mansao_referencias',content_flags=MapContentFlags.HAS_ENTITIES_HD|MapContentFlags.HAS_PHYSICS,entities=entities,
                 streaming_extents=(Vector(lo-100),Vector(hi+100)),entities_extents=(Vector(lo),Vector(hi))),'mansao_referencias')
names=['mansao_spot_embutido.ydr','mansao_quadros_refs.ytd','mansao_referencias.ytyp','mansao_referencias.ymap',
       'mansao_pisos.ydr','mansao_teto.ydr','mansao_spots_led.ydr','mansao_decoracao.ytyp']+[a['model']+'.ydr' for a in arts]
pack={'origin':origin.tolist(),'installed_files':names,'spot_lod_triangles':triangles,'artworks':arts,'spot_entities':len(report['spots']),
      'preserve_lighting_controller':True,'preserve_architecture_physics':True,'new_collision_triangles':48,'in_game_verified':False}
(P/'package.json').write_text(json.dumps(pack,indent=2),encoding='utf-8')
print('NATIVE_PACKAGE_READY',len(names),'files;',len(entities),'instances; spot LODs',triangles,flush=True)
