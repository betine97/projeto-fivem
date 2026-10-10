import sys,json,copy,re,struct
from pathlib import Path
P=Path(__file__).resolve().parent;W=P.parent;R=W.parent;O=P/'stream'
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
    a=try_load_asset(O/(name+'.ydr'));stats[name]={}
    for lod,suffix in [(LodLevel.HIGH,''),(LodLevel.MEDIUM,'_medium'),(LodLevel.LOW,'_low'),(LodLevel.VERYLOW,'_verylow')]:
        v=try_load_asset(O/(name+suffix+'.ydr'));mapping={i:next(j for j,s in enumerate(a.shader_group.shaders) if key(s)==key(old)) for i,old in enumerate(v.shader_group.shaders)}
        for m in v.models[LodLevel.HIGH]:
            for g in m.geometries:
                g.shader_index=mapping[g.shader_index];vb=g.vertex_buffer.copy();ids=g.index_buffer.reshape(-1,3);ts=vb['Position'][ids];keep=np.linalg.norm(np.cross(ts[:,1]-ts[:,0],ts[:,2]-ts[:,0]),axis=1)>1e-12;g.index_buffer=ids[keep].reshape(-1).copy()
                if 'Tangent' in vb.dtype.names:
                    bad=np.flatnonzero(np.linalg.norm(vb['Tangent'][:,:3],axis=1)<.5)
                    if len(bad):
                        n=vb['Normal'][bad];axis=np.eye(3)[np.argmin(abs(n),axis=1)];t=np.cross(axis,n);t/=np.maximum(np.linalg.norm(t,axis=1,keepdims=True),1e-9);vb['Tangent'][bad,:3]=t;vb['Tangent'][bad,3]=1
                g.vertex_buffer=vb
        a.models[lod]=batch(v.models[LodLevel.HIGH]);stats[name][lod.name]={'triangles':sum(len(g.index_buffer)//3 for m in a.models[lod] for g in m.geometries),'geometries':sum(len(m.geometries) for m in a.models[lod])}
    for txname,tx in list(a.shader_group.embedded_textures.items()):
        data=(P/'textures'/(txname+'.dds')).read_bytes();h,w=struct.unpack_from('<II',data,12);a.shader_group.embedded_textures[txname]=EmbeddedTexture(txname,w,h,DataSource.create(data,name=txname+'.dds'))
    for s in a.shader_group.shaders:s.name=Path(s.preset_filename).stem
    a.lod_thresholds={LodLevel.HIGH:45.,LodLevel.MEDIUM:85.,LodLevel.LOW:145.,LodLevel.VERYLOW:220.}
    off=-np.array(spec['door_hinge'] if index==2 else spec['gate_hinge'] if index==3 else [0,0,0]);a.bounds=collision(spec['collision_meshes'][name],off)
    a.lights=[]
    if index==0:
        for i,x in enumerate([3.84,5.485]):a.lights.append(light([x,7.88,.83],(255,213,160),.95,2.7,170+i))
        for i,y in enumerate([15,16,17,18]):a.lights.append(light([4.745,y,-.8-(y-14.6)*.54+.20],(255,216,162),.5,2.4,175+i))
    if index==1:
        for i,(x,y) in enumerate((x,y) for x in [7.9,11.2] for y in [.2,3.5,6.8]):a.lights.append(light([x,y,-1.56],(255,248,235),1.8,5.5,190+i))
        for i,(x,y,z) in enumerate([(6.57,12.5,-3.1),(12.60,12.5,-3.2),(6.57,16.5,-2.8),(12.60,16.5,-3.4)]):a.lights.append(light([x,y,z],(255,215,160),.8,3.3,199+i))
    save_asset(a,target,O,name);lo=np.array(spec['bounds'][name]['lo']);hi=np.array(spec['bounds'][name]['hi']);types.append(Archetype(name,ArchetypeType.BASE,32,220,0,220,'','','',name,Vector(lo),Vector(hi),Vector((lo+hi)/2),float(np.linalg.norm(hi-lo)/2),name,ArchetypeAssetType.DRAWABLE,[]))
    if index<2:
        entities.append(Entity(name,Vector(origin),Quaternion((1,0,0,0)),1,1,EntityFlags.IS_STATIC,0,-1,220,0,EntityLodLevel.ORPHANHD,EntityPriorityLevel.REQUIRED,0,255,255,0,[]));extents.extend([lo,hi])
save_asset(AssetMapTypes(name='mansao_acesso_garagem',archetypes=types),target,O,'mansao_acesso_garagem')
lo=np.min(extents,0);hi=np.max(extents,0)
save_asset(AssetMapData(name='mansao_acesso_garagem',content_flags=MapContentFlags.HAS_ENTITIES_HD|MapContentFlags.HAS_PHYSICS,entities=entities,streaming_extents=(Vector(origin+lo-225),Vector(origin+hi+225)),entities_extents=(Vector(origin+lo-.01),Vector(origin+hi+.01))),target,O,'mansao_acesso_garagem')
save_asset(collision(spec['collision_meshes'][spec['models'][0]]+spec['collision_meshes'][spec['models'][1]],origin,camera=True),target,O,'mansao_acesso_garagem')
spec['lods']=stats;(P/'spec.json').write_text(json.dumps(spec,indent=2));print('GARAGE_PACKAGED',stats,flush=True)
