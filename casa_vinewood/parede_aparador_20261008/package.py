import sys,json,re,struct,copy
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
def load(p):
    a=try_load_asset(p);assert a is not None,p;return a
def bounds(a):
    ps=np.concatenate([g.vertex_buffer['Position'] for m in a.models[LodLevel.HIGH] for g in m.geometries]);return ps.min(0),ps.max(0)
def shaderkey(s):return s.preset_filename,tuple((p.name,p.value) for p in s.parameters if isinstance(p.value,str))
def batch(models):
    groups={}
    for m in models:
        for g in m.geometries:groups.setdefault((g.shader_index,str(g.vertex_buffer.dtype),g.vertex_data_type,tuple(g.bone_ids)),[]).append(g)
    result=[]
    for gs in groups.values():
        vertices=[];indices=[];total=0;first=gs[0]
        def flush():
            out=copy.deepcopy(first);out.vertex_buffer=np.concatenate(vertices);out.index_buffer=np.concatenate(indices).astype(np.uint16);result.append(out)
        for g in gs:
            if total+len(g.vertex_buffer)>65535:flush();vertices=[];indices=[];total=0;first=g
            vertices.append(g.vertex_buffer);indices.append(g.index_buffer.astype(np.uint32)+total);total+=len(g.vertex_buffer)
        if vertices:flush()
    m=copy.deepcopy(models[0]);m.geometries=result;return [m]
names=re.findall(r'CollisionMaterialDef\("([A-Z_0-9]+)"',Path(r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/sollumz/Sollumz/ybn/collision_materials.py').read_text())
faces12=[(0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),(1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)]
def setbounds(b,lo,hi):
    b.bb_min=Vector(lo);b.bb_max=Vector(hi);b.centroid=Vector((lo+hi)/2);b.cg=b.centroid;b.radius_around_centroid=float(np.linalg.norm(hi-lo)/2)
def collision(qs,door=False,world=False,camera=False):
    b=AssetBoundBvh();b.margin=.002
    b.composite_collision_type_flags=CollisionFlags.MAP_TYPE_WEAPON|CollisionFlags.MAP_TYPE_MOVER|CollisionFlags.MAP_TYPE_HORSE|CollisionFlags.MAP_TYPE_COVER|CollisionFlags.MAP_TYPE_VEHICLE
    b.composite_collision_include_flags=CollisionFlags.CAMERA_TEST if camera else CollisionFlags(0xffffffff)
    ps=[];fs=[];materials=[]
    def transform(v):
        if door:return np.array(v)-np.array(spec['door_hinge_local'])
        u,d,z=v;v=np.array([14.168+d,-.98-u,-.8+z]);return v+origin if world else v
    for q in qs:
        x,y,z=q['lo'];X,Y,Z=q['hi'];n=len(ps)
        ps.extend(transform(v) for v in [(x,y,z),(X,y,z),(X,Y,z),(x,Y,z),(x,y,Z),(X,y,Z),(X,Y,Z),(x,Y,Z)])
        fs.extend(tuple(n+i for i in f) for f in faces12)
        materials.extend([names.index('GLASS_SHOOT_THROUGH' if q['name'].startswith('Visor') else 'WOOD_SOLID_MEDIUM')]*12)
    b.geometry_vertices=[BoundVertex(Vector(v),None) for v in ps]
    b.geometry_primitives=[BoundPrimitive.new_triangle(*f,CollisionMaterial.from_packed(mat)) for f,mat in zip(fs,materials)]
    setbounds(b,np.min(ps,0),np.max(ps,0));c=AssetBoundComposite(children=[b]);setbounds(c,np.min(ps,0),np.max(ps,0));return c
archetypes=[];stats={}
for door,model in [(False,spec['model']),(True,spec['door_model'])]:
    a=load(O/(model+'.ydr'));stats[model]={}
    for lod,suffix in [(LodLevel.HIGH,''),(LodLevel.MEDIUM,'_medium'),(LodLevel.LOW,'_low'),(LodLevel.VERYLOW,'_verylow')]:
        v=load(O/(model+suffix+'.ydr'))
        mapping={i:next(j for j,s in enumerate(a.shader_group.shaders) if shaderkey(s)==shaderkey(old)) for i,old in enumerate(v.shader_group.shaders)}
        removed=0
        for m in v.models[LodLevel.HIGH]:
            for g in m.geometries:
                g.shader_index=mapping[g.shader_index];vb=g.vertex_buffer.copy();ids=g.index_buffer.reshape(-1,3);ts=vb['Position'][ids]
                keep=np.linalg.norm(np.cross(ts[:,1]-ts[:,0],ts[:,2]-ts[:,0]),axis=1)>1e-12;removed+=int(sum(~keep));g.index_buffer=ids[keep].reshape(-1).copy()
                if 'Tangent' in vb.dtype.names:
                    bad=np.flatnonzero(np.linalg.norm(vb['Tangent'][:,:3],axis=1)<.5)
                    if len(bad):
                        n=vb['Normal'][bad];axis=np.eye(3)[np.argmin(abs(n),axis=1)];t=np.cross(axis,n);t/=np.maximum(np.linalg.norm(t,axis=1,keepdims=True),1e-9);vb['Tangent'][bad,:3]=t;vb['Tangent'][bad,3]=1
                g.vertex_buffer=vb
        a.models[lod]=batch(v.models[LodLevel.HIGH]);stats[model][lod.name]={'triangles':sum(len(g.index_buffer)//3 for m in a.models[lod] for g in m.geometries),'geometries':sum(len(m.geometries) for m in a.models[lod]),'removed_degenerates':removed}
    a.lod_thresholds={LodLevel.HIGH:18.,LodLevel.MEDIUM:35.,LodLevel.LOW:65.,LodLevel.VERYLOW:120.}
    for name,tx in list(a.shader_group.embedded_textures.items()):
        data=(P/'textures'/(name+'.dds')).read_bytes();h,w=struct.unpack_from('<II',data,12);a.shader_group.embedded_textures[name]=EmbeddedTexture(name,w,h,DataSource.create(data,name=name+'.dds'))
    a.bounds=collision(spec['door_collision_boxes'] if door else spec['collision_boxes'],door=door)
    # Native imports return hash_* shader labels; never hash those labels again.
    # All three original shaders were authored here with these known presets.
    for s in a.shader_group.shaders:
        assert s.preset_filename in ['normal_spec.sps','emissive.sps','glass.sps']
        s.name=Path(s.preset_filename).stem
    if not door:
        f=int((pm.LightFlags.BOTH_INTERIOR_AND_EXTERIOR|pm.LightFlags.FX|pm.LightFlags.NO_SPECULAR|pm.LightFlags.DONT_LIGHT_ALPHA).value)
        s=(3.42-.72)/(3.42-.15)
        rows=[(.72+(u-.15)*s,-.188,2.886,True) for u in [1.075,2.505]]
        rows += [(u,-.214,.334,False) for u in [1.5,2.55]]
        a.lights=[]
        for i,(u,d,z,spot) in enumerate(rows):
            direction=np.array([.24,0.,-1.]) if spot else np.array([0.,0.,-1.]);direction/=np.linalg.norm(direction)
            a.lights.append(Light(light_type=LightType.SPOT if spot else LightType.POINT,position=Vector([14.168+d,-.98-u,-.8+z]),direction=Vector(direction),tangent=Vector([0,1,0]),extent=Vector([1,1,1]),color=(255,210,151),flashiness=LightFlashiness.CONSTANT,intensity=1.1 if spot else .55,flags=f,time_flags=0xFFFFFF,bone_id=0,group_id=0,light_hash=210+i,falloff=2.25 if spot else 1.35,falloff_exponent=2,culling_plane_normal=Vector([0,0,0]),culling_plane_offset=0,volume_intensity=0,volume_size_scale=1,volume_outer_color=(255,210,151),volume_outer_intensity=0,volume_outer_exponent=1,corona_size=0,corona_intensity=0,corona_z_bias=0,projected_texture_hash='',light_fade_distance=120,shadow_fade_distance=0,specular_fade_distance=0,volumetric_fade_distance=0,shadow_near_clip=.05,shadow_blur=0,cone_inner_angle=22 if spot else 0,cone_outer_angle=48 if spot else 0))
    save_asset(a,target,O,model);lo,hi=bounds(a)
    archetypes.append(Archetype(model,ArchetypeType.BASE,32,120,0,120,'','','',model,Vector(lo),Vector(hi),Vector((lo+hi)/2),float(np.linalg.norm(hi-lo)/2),model,ArchetypeAssetType.DRAWABLE,[]))
save_asset(AssetMapTypes(name=spec['model'],archetypes=archetypes),target,O,spec['model'])
lo=np.array(spec['fixed_bounds']['lo']);hi=np.array(spec['fixed_bounds']['hi'])
e=Entity(spec['model'],Vector(origin),Quaternion((1,0,0,0)),1,1,EntityFlags.IS_STATIC,0,-1,120,0,EntityLodLevel.ORPHANHD,EntityPriorityLevel.REQUIRED,0,255,255,0,[])
save_asset(AssetMapData(name=spec['model'],content_flags=MapContentFlags.HAS_ENTITIES_HD|MapContentFlags.HAS_PHYSICS,entities=[e],streaming_extents=(Vector(origin+lo-125),Vector(origin+hi+125)),entities_extents=(Vector(origin+lo-.01),Vector(origin+hi+.01))),target,O,spec['model'])
save_asset(collision(spec['collision_boxes'],world=True,camera=True),target,O,spec['model'])
spec['lods']=stats;spec['native_lights']=4
(P/'spec.json').write_text(json.dumps(spec,indent=2),encoding='utf-8');print('APARADOR_PACKAGE_READY',stats,flush=True)
