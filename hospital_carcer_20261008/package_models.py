import sys,json,copy,re,struct
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parent;O=P/'package/stream'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from szio.gta5 import *
from szio.gta5.bounds import *
from szio.gta5.maps import *
from szio.gta5.entities import *
from szio.gta5.drawables import Light,LightType,LightFlashiness
from szio.types import Vector,Quaternion,DataSource
import pymateria.gta5 as pm
spec=json.loads((P/'spec.json').read_text());origin=np.array(spec['origin']);target=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
names=re.findall(r'CollisionMaterialDef\("([A-Z_0-9]+)"',Path(r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/sollumz/Sollumz/ybn/collision_materials.py').read_text())
def setbounds(b,lo,hi):
    b.bb_min=Vector(lo);b.bb_max=Vector(hi);b.centroid=Vector((lo+hi)/2);b.cg=b.centroid;b.radius_around_centroid=float(np.linalg.norm(hi-lo)/2)
def collision(groups,offset,camera=False):
    b=AssetBoundBvh();b.margin=.002;b.composite_collision_type_flags=CollisionFlags.MAP_TYPE_WEAPON|CollisionFlags.MAP_TYPE_MOVER|CollisionFlags.MAP_TYPE_HORSE|CollisionFlags.MAP_TYPE_COVER|CollisionFlags.MAP_TYPE_VEHICLE
    b.composite_collision_include_flags=CollisionFlags.CAMERA_TEST if camera else CollisionFlags(0xffffffff)
    vertices=[];primitives=[]
    for q in groups:
        off=len(vertices);vertices.extend(np.array(q['vertices'])+offset)
        mat=CollisionMaterial.from_packed(names.index(q['material']))
        primitives.extend(BoundPrimitive.new_triangle(*(off+i for i in t),mat) for t in q['triangles'])
    b.geometry_vertices=[BoundVertex(Vector(v),None) for v in vertices];b.geometry_primitives=primitives;lo=np.min(vertices,0);hi=np.max(vertices,0);setbounds(b,lo,hi);c=AssetBoundComposite(children=[b]);setbounds(c,lo,hi);return c
def batch(models):
    groups={}
    for m in models:
        for g in m.geometries:groups.setdefault((g.shader_index,str(g.vertex_buffer.dtype),g.vertex_data_type,tuple(g.bone_ids)),[]).append(g)
    gs=[]
    for parts in groups.values():
        g=copy.deepcopy(parts[0]);g.vertex_buffer=np.concatenate([v.vertex_buffer for v in parts]);assert len(g.vertex_buffer)<65535;total=0;ids=[]
        for v in parts:ids.append(v.index_buffer.astype(np.uint32)+total);total+=len(v.vertex_buffer)
        g.index_buffer=np.concatenate(ids).astype(np.uint16);gs.append(g)
    m=copy.deepcopy(models[0]);m.geometries=gs;return [m]
def key(s):return s.preset_filename,tuple((p.name,p.value) for p in s.parameters if isinstance(p.value,str))
def light(pos,color,intensity,range_,ident):
    flags=int((pm.LightFlags.BOTH_INTERIOR_AND_EXTERIOR|pm.LightFlags.NO_SPECULAR|pm.LightFlags.DONT_LIGHT_ALPHA).value)
    return Light(light_type=LightType.POINT,position=Vector(pos),direction=Vector([0,0,-1]),tangent=Vector([1,0,0]),extent=Vector([1,1,1]),color=color,flashiness=LightFlashiness.CONSTANT,intensity=intensity,flags=flags,time_flags=0xffffff,bone_id=0,group_id=0,light_hash=ident,falloff=range_,falloff_exponent=2,culling_plane_normal=Vector([0,0,0]),culling_plane_offset=0,volume_intensity=0,volume_size_scale=1,volume_outer_color=color,volume_outer_intensity=0,volume_outer_exponent=1,corona_size=0,corona_intensity=0,corona_z_bias=0,projected_texture_hash='',light_fade_distance=220,shadow_fade_distance=0,specular_fade_distance=0,volumetric_fade_distance=0,shadow_near_clip=.05,shadow_blur=0,cone_inner_angle=0,cone_outer_angle=0)

types=[];entities=[];stats={};extents=[]
for index,name in enumerate(spec['models']):
    a=try_load_asset(P/'stream'/(name+'.ydr'));stats[name]={}
    for lod,suffix in [(LodLevel.HIGH,''),(LodLevel.MEDIUM,'_medium'),(LodLevel.LOW,'_low'),(LodLevel.VERYLOW,'_verylow')]:
        f=P/'stream'/(name+suffix+'.ydr');v=try_load_asset(f) if f.exists() else copy.deepcopy(a)
        mapping={i:next(j for j,s in enumerate(a.shader_group.shaders) if key(s)==key(old)) for i,old in enumerate(v.shader_group.shaders)}
        for m in v.models[LodLevel.HIGH]:
            for g in m.geometries:
                g.shader_index=mapping[g.shader_index];vb=g.vertex_buffer.copy();ids=g.index_buffer.reshape(-1,3);ts=vb['Position'][ids];g.index_buffer=ids[np.linalg.norm(np.cross(ts[:,1]-ts[:,0],ts[:,2]-ts[:,0]),axis=1)>1e-12].reshape(-1).copy()
                if 'Tangent' in vb.dtype.names:
                    bad=np.flatnonzero(np.linalg.norm(vb['Tangent'][:,:3],axis=1)<.5)
                    if len(bad):
                        n=vb['Normal'][bad];axis=np.eye(3)[np.argmin(abs(n),axis=1)];t=np.cross(axis,n);t/=np.maximum(np.linalg.norm(t,axis=1,keepdims=True),1e-9);vb['Tangent'][bad,:3]=t;vb['Tangent'][bad,3]=1
                g.vertex_buffer=vb
        a.models[lod]=batch(v.models[LodLevel.HIGH]);stats[name][lod.name]=sum(len(g.index_buffer)//3 for m in a.models[lod] for g in m.geometries)
    for txname,tx in list(a.shader_group.embedded_textures.items()):
        data=(P/'textures'/(txname+'.dds')).read_bytes();h,w=struct.unpack_from('<II',data,12);a.shader_group.embedded_textures[txname]=EmbeddedTexture(txname,w,h,DataSource.create(data,name=txname+'.dds'))
    for s in a.shader_group.shaders:s.name=Path(s.preset_filename).stem
    a.lod_thresholds={LodLevel.HIGH:90.,LodLevel.MEDIUM:145.,LodLevel.LOW:220.,LodLevel.VERYLOW:450.}
    a.bounds=collision(spec['collision_meshes'][name],np.zeros(3))
    a.lights=[light(q['pos'],tuple(q['color']),q['intensity'],q['range'],20+i) for i,q in enumerate(spec['lights']) if q['model']==name]
    save_asset(a,target,O,name);lo=np.array(spec['bounds'][name]['lo']);hi=np.array(spec['bounds'][name]['hi']);types.append(Archetype(name,ArchetypeType.BASE,32,450,0,450,'','','',name,Vector(lo),Vector(hi),Vector((lo+hi)/2),float(np.linalg.norm(hi-lo)/2),name,ArchetypeAssetType.DRAWABLE,[]))
    if index<6:
        entities.append(Entity(name,Vector(origin),Quaternion((1,0,0,0)),1,1,EntityFlags.IS_STATIC,0,-1,450,0,EntityLodLevel.ORPHANHD,EntityPriorityLevel.REQUIRED,0,255,255,0,[]));extents.extend([lo,hi])
save_asset(AssetMapTypes(name='hospital_carcer',archetypes=types),target,O,'hospital_carcer')
lo=np.min(extents,0);hi=np.max(extents,0)
save_asset(AssetMapData(name='hospital_carcer',content_flags=MapContentFlags.HAS_ENTITIES_HD|MapContentFlags.HAS_PHYSICS,entities=entities,streaming_extents=(Vector(origin+lo-450),Vector(origin+hi+450)),entities_extents=(Vector(origin+lo-.01),Vector(origin+hi+.01))),target,O,'hospital_carcer')
save_asset(collision(sum((spec['collision_meshes'][n] for n in spec['models'][:6]),[]),origin,camera=True),target,O,'hospital_carcer')
spec['lods']=stats;(P/'spec.json').write_text(json.dumps(spec,indent=2));print('HOSPITAL_PACKAGED',stats,flush=True)
