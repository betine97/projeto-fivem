"""Stream the fitted Meshy enclosure with glass-alpha curtains and opaque rails."""
import copy
import io
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path[:0]=[
 r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps',
 r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\media_deps',
]
from PIL import Image
from szio.gta5 import AssetFormat,AssetTarget,AssetVersion,save_asset,try_load_asset
from szio.gta5.drawables import LodLevel
from szio.gta5.entities import Entity,EntityFlags,EntityLodLevel,EntityPriorityLevel
from szio.types import DataSource,Quaternion,Vector

root=Path(__file__).resolve().parents[2]
lab=root/'laboratorio_fivem'
stream=root/'server-data/resources/cidade_laboratorio/stream'
source=lab/'containment_source'
out=lab/'containment_update';out.mkdir(exist_ok=True)
target=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)

mesh=np.load(source/'containment_fit_mesh.npz')
positions=mesh['position'];normals=mesh['normal'];uvs=mesh['uv']
assert len(positions)%3==0 and len(positions)//3==35908
strips=np.load(source/'containment_strips.npz')
strip_positions=strips['position'];strip_normals=strips['normal'];strip_uvs=strips['uv']
assert len(strip_positions)%3==0 and len(strip_positions)//3==6160

# GTA's transparent glass shader is used rather than alpha-cutout; the latter
# would make the curtains either opaque or invisible instead of see-through.
asset=try_load_asset(lab/'work/translucent_shader_samples/v_ilev_prop_fib_glass.ydr')
asset.name='lab_containment.#dr'
asset.bounds=None
diffuse_name='lab_containment_clear'
shader=asset.shader_group.shaders[0]
assert shader.render_bucket.value==1
original_diffuse=next(param.value for param in shader.parameters if param.name.lower()=='diffusesampler')
for parameter in shader.parameters:
 if parameter.name.lower()=='diffusesampler':parameter.value=diffuse_name
 if parameter.name.lower() in ('reflectivepower','bumpiness','specularintensitymult'):
  parameter.value=Vector((0,0,0,0))
texture=copy.deepcopy(asset.shader_group.embedded_textures[original_diffuse])
texture.name=diffuse_name
image=Image.open(source/'containment_clear_rgba.png').convert('RGBA')
dds=io.BytesIO();image.save(dds,format='DDS',pixel_format='DXT5')
texture.width,texture.height=image.size
texture.data=DataSource.create(dds.getvalue())
asset.shader_group.embedded_textures[diffuse_name]=texture
asset.shader_group.embedded_textures.pop(original_diffuse,None)

strip_shader=copy.deepcopy(shader)
strip_diffuse_name='lab_containment_vinyl'
for parameter in strip_shader.parameters:
 if parameter.name.lower()=='diffusesampler':parameter.value=strip_diffuse_name
asset.shader_group.shaders.append(strip_shader)
strip_texture=copy.deepcopy(texture)
strip_texture.name=strip_diffuse_name
strip_image=Image.open(source/'vinyl_strip_clear_rgba.png').convert('RGBA')
strip_dds=io.BytesIO();strip_image.save(strip_dds,format='DDS',pixel_format='DXT5')
strip_texture.width,strip_texture.height=strip_image.size
strip_texture.data=DataSource.create(strip_dds.getvalue())
asset.shader_group.embedded_textures[strip_diffuse_name]=strip_texture

template=asset.models[LodLevel.HIGH][0].geometries[0]
geometries=[]
max_faces=18000
for shader_index,(mesh_positions,mesh_normals,mesh_uvs) in enumerate((
 (positions,normals,uvs),(strip_positions,strip_normals,strip_uvs))):
 for begin in range(0,len(mesh_positions)//3,max_faces):
  end=min(begin+max_faces,len(mesh_positions)//3)
  lo,hi=begin*3,end*3
  vertices=np.zeros(hi-lo,dtype=template.vertex_buffer.dtype)
  vertices['Position']=mesh_positions[lo:hi]
  vertices['Normal']=mesh_normals[lo:hi]
  vertices['TexCoord0']=mesh_uvs[lo:hi]
  vertices['Colour0']=(255,255,255,255)
  vertices['Tangent']=(1,0,0,1)
  geometry=copy.deepcopy(template)
  geometry.vertex_buffer=vertices
  geometry.index_buffer=np.arange(hi-lo,dtype=np.uint16)
  geometry.shader_index=shader_index
  geometries.append(geometry)
asset.models[LodLevel.HIGH][0].geometries=geometries
for lod in list(asset.models):
 if lod!=LodLevel.HIGH:asset.models[lod]=[]
save_asset(asset,target,out,'lab_containment')

# The former dark fabric mesh sits in front of the new clear curtain and would
# hide plants. Keep the metal trays/posts and their existing collision intact.
racks=try_load_asset(stream/'lab_racks.ydr')
metal=racks.models[LodLevel.HIGH][0].geometries
assert len(metal) in (1,2) and metal[0].shader_index==0
if len(metal)==2:assert metal[1].shader_index==1
racks.models[LodLevel.HIGH][0].geometries=[metal[0]]
save_asset(racks,target,out,'lab_racks')

placement=json.loads((lab/'placement.json').read_text())
origin=np.asarray(placement['origin']);basis=np.asarray(placement['basis'])
heading=math.radians(placement['heading'])
def entity(x):
 angle=-heading/2
 position=Vector(origin+basis@np.asarray([x,-.8,0]))
 rotation=Quaternion((math.cos(angle),0,0,math.sin(angle)))
 return Entity('lab_containment',position,rotation,1,1,EntityFlags.IS_STATIC,
               0,-1,120,0,EntityLodLevel.ORPHANHD,EntityPriorityLevel.REQUIRED,
               0,255,255,0,[])

ymap=try_load_asset(stream/'cidade_laboratorio.ymap')
ymap.entities=[e for e in ymap.entities if e.archetype_name!='lab_containment']
ymap.entities.extend((entity(-2.48),entity(2.48)))
save_asset(ymap,target,out,'cidade_laboratorio')

typ=try_load_asset(stream/'cidade_laboratorio.ytyp')
typ.archetypes=[a for a in typ.archetypes if a.name!='lab_containment']
arch=copy.deepcopy(next(a for a in typ.archetypes if a.name=='lab_racks'))
arch.name='lab_containment';arch.asset_name='lab_containment'
low=np.minimum(positions.min(0),strip_positions.min(0))
high=np.maximum(positions.max(0),strip_positions.max(0))
arch.bb_min=Vector(low);arch.bb_max=Vector(high)
arch.bs_center=Vector((low+high)/2)
arch.bs_radius=float(np.linalg.norm(high-low)/2)
typ.archetypes.append(arch)
save_asset(typ,target,out,'cidade_laboratorio')

for filename in ('lab_containment.ydr','lab_racks.ydr','cidade_laboratorio.ymap','cidade_laboratorio.ytyp'):
 assert try_load_asset(out/filename) is not None,filename
check=try_load_asset(out/'lab_containment.ydr')
assert len(check.models[LodLevel.HIGH][0].geometries)==3
assert len(check.shader_group.shaders)==2
assert all(s.render_bucket.value==1 for s in check.shader_group.shaders)
frame_alpha=np.asarray(Image.open(io.BytesIO(check.shader_group.embedded_textures[diffuse_name].data.read_bytes())).convert('RGBA'))[:,:,3]
vinyl_alpha=np.asarray(Image.open(io.BytesIO(check.shader_group.embedded_textures[strip_diffuse_name].data.read_bytes())).convert('RGBA'))[:,:,3]
assert frame_alpha.min()<10 and frame_alpha.max()>200
assert vinyl_alpha.min()<15 and vinyl_alpha.max()<100
print('CONTAINMENT_GAME_OK',len(positions)//3+len(strip_positions)//3,'triangles',
      'frame_alpha',int(frame_alpha.min()),int(frame_alpha.max()),
      'vinyl_alpha',int(vinyl_alpha.min()),int(vinyl_alpha.max()),
      'entities',len(ymap.entities),flush=True)
