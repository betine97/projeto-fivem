"""Native preview package with shared DDS textures and exact metre geometry."""
import sys,json,math,copy,struct,re,io,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1];O=P/'package/stream';O.mkdir(parents=True,exist_ok=True)
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from PIL import Image,ImageOps
from szio.gta5 import *
from szio.gta5.drawables import Geometry,Model,ShaderGroup,VertexDataType,Light,LightType,LightFlashiness
from szio.gta5.bounds import *
from szio.gta5.maps import *
from szio.gta5.entities import *
from szio.types import Vector,Quaternion,DataSource
import pymateria.gta5 as pm
TARGET=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
data=json.loads((P/'extracao.json').read_text(encoding='utf-8'))
geo=np.load(P/'geometria.npz');physics=np.load(P/'colisoes.npz')
anchor=np.array(data['anchor']);angle=math.radians(data['rotation']);cs,sn=math.cos(angle),math.sin(angle)
rotation=np.array([[cs,-sn,0],[sn,cs,0],[0,0,1]])
reference=try_load_asset(R/'server-data/resources/cidade_mansao/stream/mansao_porta_vidro_aparador.ydr')
fixtures=try_load_asset(R/'server-data/resources/cidade_mansao/stream/mansao_spot_embutido.ydr')
templates={s.preset_filename:copy.deepcopy(s) for a in [reference,fixtures] for s in a.shader_group.shaders}
dtype=np.dtype([('Position',np.float32,3),('Normal',np.float32,3),('Colour0',np.uint8,4),('TexCoord0',np.float32,2),('Tangent',np.float32,4)])

def dds_mips(im,fmt):
    chunks=[];header=None;levels=0
    while True:
        buffer=io.BytesIO();im.save(buffer,format='DDS',pixel_format=fmt);raw=buffer.getvalue()
        assert raw[:4]==b'DDS ' and raw[84:88] in [b'DXT1',b'DXT5']
        if header is None:header=bytearray(raw[:128])
        chunks.append(raw[128:]);levels+=1
        if im.width==im.height==1:break
        im=im.resize((max(1,im.width//2),max(1,im.height//2)),Image.Resampling.LANCZOS)
    struct.pack_into('<I',header,8,struct.unpack_from('<I',header,8)[0]|0x20000)
    struct.pack_into('<I',header,28,levels)
    struct.pack_into('<I',header,108,0x1000|0x8|0x400000)
    return bytes(header)+b''.join(chunks),levels

textures={};shaders={};tex_report=[]
used={r['material'] for r in data['geometry']}
for row in data['materials']:
    if row['id'] not in used:continue
    preset='glass.sps' if row['glass'] else 'emissive.sps' if row['emission']>0 else 'normal_spec.sps'
    shader=copy.deepcopy(templates[preset]);shader.name=Path(preset).stem
    txnames={}
    for sampler,suffix in [('diffusesampler','diffuse'),('bumpsampler','normal'),('specsampler','spec')]:
        if not any(p.name==sampler for p in shader.parameters):continue
        name=row['key']+'_'+suffix
        if suffix=='spec':
            value=int(20+(1-row['roughness'])*100+row['metallic']*70)
            im=Image.new('RGBA',(16,16),(value,value,value,255));fmt='DXT1'
        else:
            im=Image.open(P/'texturas'/(name+'.png')).convert('RGBA');fmt='DXT1' if suffix=='diffuse' else 'DXT5'
            if suffix=='normal':
                rr,gg,bb,aa=im.split();im=Image.merge('RGBA',(rr,ImageOps.invert(gg),bb,aa))
            if row['glass'] and suffix=='diffuse':im.putalpha(40);fmt='DXT5'
        raw,levels=dds_mips(im,fmt)
        (P/'texturas'/(name+'.dds')).write_bytes(raw)
        textures[name]=EmbeddedTexture(name,im.width,im.height,DataSource.create(raw,name=name+'.dds'))
        txnames[sampler]=name;tex_report.append({'name':name,'size':[im.width,im.height],'dds_bytes':len(raw),'mips':levels,'format':fmt,'source_material':row['name']})
    for param in shader.parameters:
        if param.name in txnames:param.value=txnames[param.name]
        elif param.name=='bumpiness':param.value=Vector([1,0,0,0])
        elif param.name=='wetnessmultiplier':param.value=Vector([0,0,0,0])
        elif param.name=='specularintensitymult':param.value=Vector([.45 if row['metallic']>.5 else .12 if row['glass'] else .04+(1-row['roughness'])*.18,0,0,0])
        elif param.name=='specularfalloffmult':param.value=Vector([16+(1-row['roughness'])*100,0,0,0])
        elif param.name=='specularfresnel':param.value=Vector([.35 if row['metallic']>.5 else .05,0,0,0])
        elif param.name=='emissivemultiplier':param.value=Vector([min(4,row['emission']),0,0,0])
    shaders[row['id']]=shader
save_asset(AssetTextureDictionary(textures=textures),TARGET,O,'crf_castelo_texturas')

names=re.findall(r'CollisionMaterialDef\("([A-Z_0-9]+)"',Path(r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/sollumz/Sollumz/ybn/collision_materials.py').read_text())
def bounds(b,lo,hi):
    b.bb_min=Vector(lo);b.bb_max=Vector(hi);b.centroid=Vector((lo+hi)/2);b.cg=b.centroid;b.radius_around_centroid=float(np.linalg.norm(hi-lo)/2)
def collision(tris):
    if len(tris)==0:return None
    tris=np.array(tris);p,inv=np.unique(np.round(tris.reshape(-1,3),6),axis=0,return_inverse=True);ids=inv.reshape(-1,3)
    assert len(p)<65535,('Collision vertex limit',len(p))
    b=AssetBoundBvh();b.margin=.001
    b.composite_collision_type_flags=CollisionFlags.MAP_TYPE_WEAPON|CollisionFlags.MAP_TYPE_MOVER|CollisionFlags.MAP_TYPE_VEHICLE|CollisionFlags.MAP_TYPE_COVER
    b.composite_collision_include_flags=CollisionFlags(0xffffffff)
    b.geometry_vertices=[BoundVertex(Vector(v),None) for v in p]
    material=CollisionMaterial.from_packed(names.index('CONCRETE'))
    b.geometry_primitives=[BoundPrimitive.new_triangle(*map(int,f),copy.deepcopy(material)) for f in ids]
    bounds(b,p.min(0),p.max(0));comp=AssetBoundComposite(children=[b]);bounds(comp,p.min(0),p.max(0));return comp
def light(row,i):
    color=tuple(int(min(255,round(c*255))) for c in row['color'])
    flags=int((pm.LightFlags.BOTH_INTERIOR_AND_EXTERIOR|pm.LightFlags.NO_SPECULAR|pm.LightFlags.DONT_LIGHT_ALPHA|pm.LightFlags.FX).value)
    return Light(light_type=LightType.POINT,position=Vector(row['position']),direction=Vector([0,0,-1]),tangent=Vector([1,0,0]),extent=Vector([1,1,1]),color=color,flashiness=LightFlashiness.CONSTANT,intensity=1.8 if row['energy']>=400 else 1.1,flags=flags,time_flags=0xFFFFFF,bone_id=0,group_id=0,light_hash=40+i,falloff=5.8,falloff_exponent=2,culling_plane_normal=Vector([0,0,0]),culling_plane_offset=0,volume_intensity=0,volume_size_scale=1,volume_outer_color=color,volume_outer_intensity=0,volume_outer_exponent=1,corona_size=0,corona_intensity=0,corona_z_bias=0,projected_texture_hash='',light_fade_distance=150,shadow_fade_distance=0,specular_fade_distance=0,volumetric_fade_distance=0,shadow_near_clip=.05,shadow_blur=0,cone_inner_angle=0,cone_outer_angle=0)

types=[];entities=[];ext=[];stats=[];assets={}
for group in sorted({r['group'] for r in data['geometry']}):
    rows=[r for r in data['geometry'] if r['group']==group];mids=sorted({r['material'] for r in rows})
    a=AssetDrawable(name=group,shader_group=ShaderGroup([shaders[k] for k in mids],{}));geometries=[];allpts=[]
    for row in rows:
        raw=geo[row['key']]
        assert np.isfinite(raw).all()
        for start in range(0,len(raw),65532):
            source=raw[start:start+65532];vb=np.zeros(len(source),dtype=dtype)
            vb['Position']=source[:,:3];vb['Normal']=source[:,3:6];vb['Colour0']=255;vb['TexCoord0']=source[:,6:8];vb['Tangent']=source[:,8:12]
            # Collapse repeated identical corner attributes to reduce streaming.
            vb,inv=np.unique(vb,return_inverse=True)
            geometries.append(Geometry(VertexDataType.DEFAULT,vb,inv.astype(np.uint16),np.zeros(0,dtype=np.uint16),mids.index(row['material'])))
            allpts.append(vb['Position'])
    ps=np.concatenate(allpts);lo,hi=ps.min(0),ps.max(0)
    a.models[LodLevel.HIGH]=[Model(0,geometries,255,False,0,0)]
    dist=320 if 'arquitetura' in group else 150
    a.lod_thresholds={LodLevel.HIGH:float(dist),LodLevel.MEDIUM:float(dist),LodLevel.LOW:float(dist),LodLevel.VERYLOW:float(dist)}
    a.bounds=collision(physics[group]) if group in physics else None
    if group.endswith('_arquitetura'):
        for i,row in enumerate(data['lights']):
            floor='terreo' if row['position'][2]<4.9 else 'suites' if row['position'][2]<9.1 else 'conselho'
            if group=='crf_'+floor+'_arquitetura':a.lights.append(light(row,i))
    save_asset(a,TARGET,O,group);assets[group]=a
    types.append(Archetype(group,ArchetypeType.BASE,32,dist,0,dist,'crf_castelo_texturas','','',group,Vector(lo),Vector(hi),Vector((lo+hi)/2),float(np.linalg.norm(hi-lo)/2),group,ArchetypeAssetType.DRAWABLE,[]))
    entities.append(Entity(group,Vector(anchor),Quaternion([math.cos(angle/2),0,0,-math.sin(angle/2)]),1,1,EntityFlags.IS_STATIC,0,-1,dist,0,EntityLodLevel.ORPHANHD,EntityPriorityLevel.REQUIRED,0,255,255,0,[]))
    corners=np.array([[x,y,z] for x in [lo[0],hi[0]] for y in [lo[1],hi[1]] for z in [lo[2],hi[2]]]);ext.extend(corners@rotation.T+anchor)
    stats.append({'model':group,'triangles':sum(len(g.index_buffer)//3 for g in geometries),'vertices':sum(len(g.vertex_buffer) for g in geometries),'geometries':len(geometries),'lights':len(a.lights),'collision_triangles':len(physics[group]) if group in physics else 0,'local_bounds':[lo.tolist(),hi.tolist()]})
    print('PACKED',group,stats[-1]['triangles'],'triangles',flush=True)
save_asset(AssetMapTypes(name='crf_castelo_previa',archetypes=types),TARGET,O,'crf_castelo_previa')
lo,hi=np.min(ext,0),np.max(ext,0)
save_asset(AssetMapData(name='crf_castelo_previa',content_flags=MapContentFlags.HAS_ENTITIES_HD|MapContentFlags.HAS_PHYSICS,entities=entities,streaming_extents=(Vector(lo-320),Vector(hi+320)),entities_extents=(Vector(lo-.05),Vector(hi+.05))),TARGET,O,'crf_castelo_previa')
required={p.value for a in assets.values() for s in a.shader_group.shaders for p in s.parameters if isinstance(p.value,str)}
assert required<=textures.keys(),required-textures.keys()
assert hashlib.sha256(Path(data['source']).read_bytes()).hexdigest()==data['source_sha256']
report={'passed':True,'source':data['source'],'source_sha256':data['source_sha256'],'scale':[1,1,1],'anchor':anchor.tolist(),'rotation_degrees':data['rotation'],'textures':tex_report,'models':stats,'texture_dds_bytes':sum(t['dds_bytes'] for t in tex_report),'exterior_materials_baked':True,'source_unchanged':True,'world_bounds':[lo.tolist(),hi.tolist()],'native_files':[f.name for f in O.iterdir()],'geometry_lods':'Full detail preview; texture mipmaps supplied. Simplified geometry LOD pending.','in_game_verified':False}
(P/'pacote.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
print('PACKAGE_READY',len(stats),'models',report['texture_dds_bytes'],'texture bytes',flush=True)
