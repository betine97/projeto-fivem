"""Stream the supplied Meshy elevator, sliding doors and empty sublevel."""
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
from PIL import Image,ImageDraw,ImageFont
from szio.gta5 import AssetFormat,AssetTarget,AssetVersion,save_asset,try_load_asset
from szio.gta5.bounds import AssetBoundBvh,AssetBoundComposite,BoundVertex,BoundPrimitive,CollisionFlags,CollisionMaterial
from szio.gta5.drawables import LodLevel
from szio.gta5.entities import Entity,EntityFlags,EntityLodLevel,EntityPriorityLevel
from szio.types import DataSource,Quaternion,Vector

root=Path(__file__).resolve().parents[2]
lab=root/'laboratorio_fivem'
stream=root/'server-data/resources/cidade_laboratorio/stream'
source=lab/'elevator_source'
out=lab/'elevator_update';out.mkdir(exist_ok=True)
target=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
placement=json.loads((lab/'placement.json').read_text())
origin=np.asarray(placement['origin']);basis=np.asarray(placement['basis'])
heading=math.radians(placement['heading'])

def entity(name,local,draw_distance=120):
 position=Vector(origin+basis@np.asarray(local))
 rotation=Quaternion((math.cos(-heading/2),0,0,math.sin(-heading/2)))
 return Entity(name,position,rotation,1,1,EntityFlags.IS_STATIC,0,-1,draw_distance,0,
               EntityLodLevel.ORPHANHD,EntityPriorityLevel.REQUIRED,0,255,255,0,[])

def geometry(template,positions,normals,uvs,shader=0,flip_v=False):
 assert len(positions)==len(normals)==len(uvs)<65535
 vertices=np.zeros(len(positions),dtype=template.vertex_buffer.dtype)
 vertices['Position']=positions
 vertices['Normal']=normals
 texcoords=np.asarray(uvs,dtype=np.float32).copy()
 if flip_v:texcoords[:,1]=1.0-texcoords[:,1]
 vertices['TexCoord0']=texcoords
 vertices['Colour0']=(255,255,255,255)
 vertices['Tangent']=(1,0,0,1)
 result=copy.deepcopy(template)
 result.vertex_buffer=vertices
 result.index_buffer=np.arange(len(positions),dtype=np.uint16)
 result.shader_index=shader
 return result

def box_faces(center,size):
 x,y,z=center;a,b,c=np.asarray(size)/2
 corners=np.asarray([(x-a,y-b,z-c),(x+a,y-b,z-c),
                     (x+a,y+b,z-c),(x-a,y+b,z-c),
                     (x-a,y-b,z+c),(x+a,y-b,z+c),
                     (x+a,y+b,z+c),(x-a,y+b,z+c)],np.float32)
 for side in ((0,3,2,1),(4,5,6,7),(0,1,5,4),
              (1,2,6,5),(2,3,7,6),(3,0,4,7)):
  for ids,uv in (((0,1,2),((0,0),(1,0),(1,1))),
                 ((0,2,3),((0,0),(1,1),(0,1)))):
   yield corners[[side[i] for i in ids]],uv

def append_triangle(pos,norm,uvs,points,coords):
 a,b,c=np.asarray(points,np.float32)
 normal=np.cross(b-a,c-a);normal/=max(np.linalg.norm(normal),1e-8)
 pos.extend(points);norm.extend((normal,normal,normal));uvs.extend(coords)

def make_bounds(boxes):
 b=AssetBoundBvh()
 b.composite_collision_type_flags=CollisionFlags.MAP_TYPE_MOVER|CollisionFlags.MAP_TYPE_WEAPON
 b.composite_collision_include_flags=CollisionFlags(0xffffffff)
 material=CollisionMaterial.from_packed(1)
 for center,size in boxes:
  c=np.asarray(center);d=np.asarray(size)/2;offset=len(b.geometry_vertices)
  b.geometry_vertices.extend(BoundVertex(Vector(c+d*np.asarray(v)),None) for v in
   ((-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
    (-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)))
  for a,z,c1 in ((0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),
                 (1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)):
   b.geometry_primitives.append(BoundPrimitive.new_triangle(offset+a,offset+z,offset+c1,material))
 xyz=np.asarray([v.co for v in b.geometry_vertices]);low,high=xyz.min(0),xyz.max(0)
 b.bb_min=Vector(low);b.bb_max=Vector(high)
 b.centroid=Vector((low+high)/2);b.cg=b.centroid
 b.radius_around_centroid=float(np.linalg.norm(high-low)/2);b.margin=.005
 composite=AssetBoundComposite(children=[b])
 composite.bb_min=b.bb_min;composite.bb_max=b.bb_max
 composite.centroid=b.centroid;composite.cg=b.cg
 composite.radius_around_centroid=b.radius_around_centroid
 return composite

def image_texture(asset,image,name):
 shader=asset.shader_group.shaders[0]
 old=next(p.value for p in shader.parameters if p.name.lower()=='diffusesampler')
 texture=copy.deepcopy(asset.shader_group.embedded_textures[old])
 texture.name=name;texture.width,texture.height=image.size
 buffer=io.BytesIO();image.convert('RGBA').save(buffer,format='DDS',pixel_format='DXT5')
 texture.data=DataSource.create(buffer.getvalue())
 asset.shader_group.embedded_textures[name]=texture
 asset.shader_group.embedded_textures.pop(old,None)
 for p in shader.parameters:
  if p.name.lower()=='diffusesampler':p.value=name

def blank_asset(name,image,texture_name,plain=False):
 asset=try_load_asset(stream/'lab_racks.ydr')
 asset.name=name+'.#dr'
 shader=copy.deepcopy(asset.shader_group.shaders[1 if plain else 0])
 assert shader.preset_filename==('default.sps' if plain else 'normal_spec.sps')
 assert shader.render_bucket.value==0
 asset.shader_group.shaders=[shader]
 asset.bounds=None
 image_texture(asset,image,texture_name)
 if plain:asset.shader_group.embedded_textures={texture_name:asset.shader_group.embedded_textures[texture_name]}
 return asset

# 1. The actual supplied cabin and facade retain their own image atlases.
# Blender exports triangle-corner UVs. GTA's TexCoord0 convention flips V.
def imported_asset(name,mesh_name,image_name,texture_name,collision_boxes=None):
 mesh=np.load(source/mesh_name)
 positions,normals,uvs=(np.asarray(mesh[k],dtype=np.float32) for k in ('position','normal','uv'))
 if name=='lab_elevador':
  # glTF source is double-sided; explicitly retain interior backfaces in GTA.
  positions=np.concatenate((positions,positions.reshape(-1,3,3)[:,::-1].reshape(-1,3)))
  normals=np.concatenate((normals,-normals.reshape(-1,3,3)[:,::-1].reshape(-1,3)))
  uvs=np.concatenate((uvs,uvs.reshape(-1,3,2)[:,::-1].reshape(-1,2)))
 assert len(positions)>0 and len(positions)%3==0
 assert np.isfinite(positions).all() and np.isfinite(normals).all() and np.isfinite(uvs).all()
 color=Image.open(source/image_name).convert('RGBA')
 # The 4K original JPEG is kept beside the Blender source. A 2K texture
 # stays sharp at the model's in-game size without duplicating huge atlases.
 # Preserve the original 4K atlas for close-up cabin and door detail.
 asset=blank_asset(name,color,texture_name,plain=True)
 template=asset.models[LodLevel.HIGH][0].geometries[0]
 chunks=[]
 for start in range(0,len(positions)//3,18000):
  lo=start*3;hi=min(start+18000,len(positions)//3)*3
  chunks.append(geometry(template,positions[lo:hi],normals[lo:hi],uvs[lo:hi],flip_v=True))
 asset.models[LodLevel.HIGH][0].geometries=chunks
 for lod in list(asset.models):
  if lod!=LodLevel.HIGH:asset.models[lod]=[]
 if collision_boxes=='mesh':
  low,high=positions.min(0),positions.max(0)
  asset.bounds=make_bounds([(((low+high)/2).tolist(),
                            np.maximum(high-low,(.03,.04,.03)).tolist())])
 elif collision_boxes:asset.bounds=make_bounds(collision_boxes)
 save_asset(asset,target,out,name)
 print('SOURCE_GLB',name,len(positions)//3,'triangles',flush=True)
 return asset

elevator=imported_asset(
 'lab_elevador','elevator_3901_cabin.npz','elevator_3901_albedo.jpg','lab_elevator_3901',[
 ((-.952,.595,1.24),(.065,2.55,2.48)),
 (( .952,.595,1.24),(.065,2.55,2.48)),
 ((0,1.87,1.24),(1.904,.065,2.48)),
 ((0,.595,.005),(1.904,2.55,.07)),
 ((0,.595,2.48),(1.904,2.55,.06)),
 ])
facade=imported_asset('lab_elev_fachada','elevator_4234_facade.npz',
                      'elevator_4234_albedo.jpg','lab_elevator_4234')
doors={}
for side,label in (('left','l'),('right','r')):
 name='lab_elev_porta_'+label
 doors[label]=imported_asset(name,'elevator_4234_door_'+side+'.npz',
                             'elevator_4234_albedo.jpg',name+'_tex',
                             'mesh')

# 2. Opaque digit plates update the floor shown by the supplied model.
font_path=Path(r'C:\Windows\Fonts\arialbd.ttf')
font=ImageFont.truetype(str(font_path),90)
indicators={}
for suffix,label in (('0','0'),('m1','-1')):
 image=Image.new('RGBA',(512,128),(4,5,6,255))
 draw=ImageDraw.Draw(image)
 box=draw.textbbox((0,0),label,font=font)
 left=(512-(box[2]-box[0]))/2-box[0]
 top=(128-(box[3]-box[1]))/2-box[1]
 draw.text((left,top),label,font=font,fill=(255,88,10,255))
 image.save(source/f'elevator_indicator_{suffix}.png')
 indicator=blank_asset('lab_elev_ind_'+suffix,image,'lab_elev_digit_'+suffix)
 ip,inn,iu=[],[],[]
 verts=((- .43,0,-.12),(.43,0,-.12),(.43,0,.12),(-.43,0,.12))
 for ids,tex in (((0,1,2),((0,0),(1,0),(1,1))),
                 ((0,2,3),((0,0),(1,1),(0,1)))):
  append_triangle(ip,inn,iu,[verts[i] for i in ids],tex)
 indicator.models[LodLevel.HIGH][0].geometries=[
  geometry(indicator.models[LodLevel.HIGH][0].geometries[0],ip,inn,iu,flip_v=True)]
 for lod in list(indicator.models):
  if lod!=LodLevel.HIGH:indicator.models[lod]=[]
 save_asset(indicator,target,out,'lab_elev_ind_'+suffix)
 indicators[suffix]=indicator

# 5. Floor -1 uses crops of the actual floor-0 wall and floor atlases.
wall_image=Image.open(source/'elevator_basement_wall.png').convert('RGBA')
floor_image=Image.open(source/'elevator_basement_floor.png').convert('RGBA')
shell_boxes=[
 ((-4.1,.7,1.8),(.2,13.6,3.6)),
 ((4.1,.7,1.8),(.2,13.6,3.6)),
 ((0,-6.1,1.8),(8.2,.2,3.6)),
 ((0,7.5,1.8),(8.2,.2,3.6)),
 ((0,.7,3.62),(8.2,13.6,.16)),
]
floor_boxes=[((0,.7,-.12),(8.2,13.6,.24))]
def shell_asset(name,image,texture,boxes):
 asset=blank_asset(name,image,texture)
 asset.bounds=make_bounds(boxes)
 p,n,u=[],[],[]
 def quad(corners):
  tex=((0,0),(1,0),(1,1),(0,1))
  append_triangle(p,n,u,[corners[j] for j in (0,1,2)],[tex[j] for j in (0,1,2)])
  append_triangle(p,n,u,[corners[j] for j in (0,2,3)],[tex[j] for j in (0,2,3)])
 def intervals(start,end,step=1.9):
  return np.linspace(start,end,math.ceil((end-start)/step)+1)
 xs=intervals(-4.0,4.0);ys=intervals(-6.0,7.4);zs=intervals(0,3.6)
 if name=='lab_subpiso':
  for x0,x1 in zip(xs[:-1],xs[1:]):
   for y0,y1 in zip(ys[:-1],ys[1:]):
    quad(((x0,y0,0),(x1,y0,0),(x1,y1,0),(x0,y1,0)))
 else:
  for x0,x1 in zip(xs[:-1],xs[1:]):
   for y0,y1 in zip(ys[:-1],ys[1:]):
    quad(((x0,y0,3.54),(x0,y1,3.54),(x1,y1,3.54),(x1,y0,3.54)))
  for y0,y1 in zip(ys[:-1],ys[1:]):
   for z0,z1 in zip(zs[:-1],zs[1:]):
    quad(((-4.0,y0,z0),(-4.0,y1,z0),(-4.0,y1,z1),(-4.0,y0,z1)))
    quad(((4.0,y0,z0),(4.0,y0,z1),(4.0,y1,z1),(4.0,y1,z0)))
  for x0,x1 in zip(xs[:-1],xs[1:]):
   for z0,z1 in zip(zs[:-1],zs[1:]):
    quad(((x0,-6.0,z0),(x0,-6.0,z1),(x1,-6.0,z1),(x1,-6.0,z0)))
    quad(((x0,7.4,z0),(x1,7.4,z0),(x1,7.4,z1),(x0,7.4,z1)))
 asset.models[LodLevel.HIGH][0].geometries=[
  geometry(asset.models[LodLevel.HIGH][0].geometries[0],p,n,u)]
 for lod in list(asset.models):
  if lod!=LodLevel.HIGH:asset.models[lod]=[]
 save_asset(asset,target,out,name)
 return asset
sub=shell_asset('lab_subestrutura',wall_image,'lab_elev_basement_wall',shell_boxes)
subfloor=shell_asset('lab_subpiso',floor_image,'lab_elev_basement_floor',floor_boxes)

ymap=try_load_asset(stream/'cidade_laboratorio.ymap')
new_names={'lab_elevador','lab_elev_fachada','lab_elev_ind_0','lab_elev_ind_m1','lab_subestrutura','lab_subpiso'}
ymap.entities=[e for e in ymap.entities
               if e.archetype_name not in new_names and
               not (e.archetype_name=='lab_piso' and e.position.z<origin[2]-4)]
ymap.entities.extend((
 entity('lab_elevador',(0,5.33,0)),
 entity('lab_elevador',(0,5.33,-8)),
 entity('lab_elev_fachada',(0,5.33,0)),
 entity('lab_elev_fachada',(0,5.33,-8)),
 entity('lab_elev_ind_0',(0,4.61,2.35)),
 entity('lab_elev_ind_m1',(0,4.61,-5.65)),
 entity('lab_subestrutura',(0,0,-8)),
 entity('lab_subpiso',(0,0,-8)),
))
ymap.streaming_extents=(Vector(origin+[-40,-40,-15]),Vector(origin+[40,40,15]))
ymap.entities_extents=(Vector(origin+[-12,-12,-12]),Vector(origin+[12,12,8]))
save_asset(ymap,target,out,'cidade_laboratorio')

typ=try_load_asset(stream/'cidade_laboratorio.ytyp')
all_assets={'lab_elevador':elevator,'lab_elev_fachada':facade,
            'lab_elev_porta_l':doors['l'],'lab_elev_porta_r':doors['r'],
            'lab_elev_ind_0':indicators['0'],'lab_elev_ind_m1':indicators['m1'],
            'lab_subestrutura':sub,'lab_subpiso':subfloor}
typ.archetypes=[a for a in typ.archetypes if a.name not in all_assets and a.name!='lab_elev_porta']
template_arch=next(a for a in typ.archetypes if a.name=='lab_estrutura')
for name,asset in all_assets.items():
 arch=copy.deepcopy(template_arch)
 arch.name=arch.asset_name=name
 arch.physics_dictionary=name if asset.bounds else ''
 vertices=np.concatenate([g.vertex_buffer['Position'] for g in asset.models[LodLevel.HIGH][0].geometries])
 low,high=vertices.min(0),vertices.max(0)
 arch.bb_min=Vector(low);arch.bb_max=Vector(high)
 arch.bs_center=Vector((low+high)/2)
 arch.bs_radius=float(np.linalg.norm(high-low)/2)
 typ.archetypes.append(arch)
save_asset(typ,target,out,'cidade_laboratorio')

for name in (*[n+'.ydr' for n in all_assets], 'cidade_laboratorio.ytyp','cidade_laboratorio.ymap'):
 assert try_load_asset(out/name) is not None,name
check=try_load_asset(out/'cidade_laboratorio.ymap')
assert sum(e.archetype_name=='lab_elevador' for e in check.entities)==2
assert sum(e.archetype_name=='lab_subestrutura' for e in check.entities)==1
print('ELEVATOR_GAME_OK',len(elevator.models[LodLevel.HIGH][0].geometries),'cabin chunks',
      len(check.entities),'map entities',flush=True)
