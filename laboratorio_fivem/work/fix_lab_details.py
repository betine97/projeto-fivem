"""Repair floor overlap, lab door, plants, and separate the animated fan rotors."""
import copy, io, json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0,r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\media_deps')
from PIL import Image

sys.path.insert(0,r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
from szio.gta5 import try_load_asset, save_asset, AssetTarget, AssetFormat, AssetVersion
from szio.gta5.drawables import LodLevel
from szio.gta5.bounds import AssetBoundBvh, AssetBoundComposite, BoundVertex, BoundPrimitive, CollisionFlags, CollisionMaterial
from szio.types import DataSource, Vector

ROOT=Path(__file__).resolve().parents[2]
W=ROOT/'laboratorio_fivem'
STREAM=ROOT/'server-data/resources/cidade_laboratorio/stream'
SOURCE=W/'backup_before_detail_fix'
assert SOURCE.is_dir(), 'Baseline anterior a esta correção não encontrado'
OUT=W/'detail_fix';OUT.mkdir(exist_ok=True)
TARGET=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)

def solid_dds(rgb):
 im=Image.new('RGBA',(8,8),(*rgb,255));buffer=io.BytesIO();im.save(buffer,format='DDS',pixel_format='DXT5');return buffer.getvalue()

def update_bounds(boxes):
 b=AssetBoundBvh();b.composite_collision_type_flags=CollisionFlags.MAP_TYPE_MOVER|CollisionFlags.MAP_TYPE_WEAPON
 b.composite_collision_include_flags=CollisionFlags(0xffffffff)
 mat=CollisionMaterial.from_packed(1)
 for c,d in boxes:
  c=np.array(c);d=np.array(d)/2;off=len(b.geometry_vertices)
  b.geometry_vertices.extend(BoundVertex(Vector(c+d*np.array(v)),None) for v in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)])
  for i,j,k in [(0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),(1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)]:
   b.geometry_primitives.append(BoundPrimitive.new_triangle(off+i,off+j,off+k,mat))
 xyz=np.array([v.co for v in b.geometry_vertices]);lo=xyz.min(0);hi=xyz.max(0)
 b.bb_min=Vector(lo);b.bb_max=Vector(hi);b.centroid=Vector((lo+hi)/2);b.cg=b.centroid;b.radius_around_centroid=float(np.linalg.norm(hi-lo)/2);b.margin=.005
 comp=AssetBoundComposite(children=[b]);comp.bb_min=b.bb_min;comp.bb_max=b.bb_max;comp.centroid=b.centroid;comp.cg=b.cg;comp.radius_around_centroid=b.radius_around_centroid
 return comp

# The gray slab and pre-existing terrain shared z=0, producing depth-buffer flicker.
floor=try_load_asset(SOURCE/'lab_piso.ydr')
for models in floor.models.values():
 for model in models:
  for g in model.geometries:g.vertex_buffer['Position'][:,2]+=.025
save_asset(floor,TARGET,OUT,'lab_piso')

# Add a small closed-door overlap on both jambs and under the lintel.
door=try_load_asset(SOURCE/'lab_porta.ydr')
for models in door.models.values():
 for model in models:
  for g in model.geometries:
   p=g.vertex_buffer['Position'];p[:,0]*=1.24/1.15;p[:,2]=p[:,2]*(2.30/2.26)-.01
door.bounds=update_bounds([([.62,0,1.14],[1.24,.055,2.30])])
save_asset(door,TARGET,OUT,'lab_porta')

# Restore the original UV assignment, replacing only fan metal albedo with gray.
vent=try_load_asset(W/'backup_before_office_fix/lab_ventilacao.ydr')
gray=solid_dds((151,158,157))
for i in (2,3,4,6):
 name=f'lab_ventilacao_{i}_color';tex=vent.shader_group.embedded_textures[name]
 tex.width=8;tex.height=8;tex.data=DataSource.create(gray)

blade_model=next(m for m in vent.models[LodLevel.HIGH] if len(m.geometries)==1 and m.geometries[0].shader_index==3)
g=blade_model.geometries[0];tri=g.index_buffer.reshape(-1,3);pos=g.vertex_buffer['Position']
centers=[
 ('teto_a',(0,-3.2667,2.56),'ceiling'),('teto_b',(0,-.8,2.56),'ceiling'),('teto_c',(0,1.6667,2.56),'ceiling'),
 ('parede_esq_a',(-3.80,-2.4,2.6),'left'),('parede_esq_b',(-3.80,-.8,2.6),'left'),('parede_esq_c',(-3.80,1.6667,2.6),'left'),
 ('parede_dir_a',(3.80,-3.2667,2.6),'right'),('parede_dir_b',(3.80,-.8,2.6),'right'),('parede_dir_c',(3.80,1.6667,2.6),'right'),
 ('fundo_esq',(-3.15,5.79,2.93),'rear_left'),('fundo_dir',(3.15,5.79,2.93),'rear_right'),
]
xyz=np.asarray(pos[tri]).mean(axis=1)
distance=np.linalg.norm(xyz[:,None,:]-np.array([c for _,c,_ in centers])[None,:,:],axis=2)
assignment=np.argmin(distance,axis=1)
counts=[int((assignment==i).sum()) for i in range(len(centers))]
assert sum(counts)==len(tri) and min(counts)>300,counts

rotors=[]
for type_name in ('ceiling','left','right','rear_left','rear_right'):
 idx=next(i for i,(_,_,t) in enumerate(centers) if t==type_name)
 selected=tri[assignment==idx];used=np.unique(selected);remap=np.zeros(len(pos),dtype=np.uint16);remap[used]=np.arange(len(used),dtype=np.uint16)
 rotor=copy.deepcopy(vent);rotor.name='lab_rotor_'+type_name
 rm=copy.deepcopy(blade_model);rg=rm.geometries[0]
 rg.vertex_buffer=rg.vertex_buffer[used].copy();rg.vertex_buffer['Position']-=np.array(centers[idx][1],dtype=np.float32)
 rg.index_buffer=remap[selected].ravel().astype(g.index_buffer.dtype);rg.shader_index=0
 rotor.models={LodLevel.HIGH:[rm]};rotor.bounds=None
 rotor.shader_group.shaders=[copy.deepcopy(vent.shader_group.shaders[3])]
 rotor.shader_group.embedded_textures={k:copy.deepcopy(v) for k,v in vent.shader_group.embedded_textures.items() if k.startswith('lab_ventilacao_3_')}
 save_asset(rotor,TARGET,OUT,rotor.name)
 rotors.append((rotor.name,type_name))

# The fixed prop retains the hoods and guards; only the rotor triangles move.
vent.models[LodLevel.HIGH]=[m for m in vent.models[LodLevel.HIGH] if m is not blade_model]
save_asset(vent,TARGET,OUT,'lab_ventilacao')

# The streamlined runtime plants omitted all authored stems. Reintroduce their
# trunk/twigs and rotate a second foliage layer to fill out every pot.
brown=solid_dds((112,78,45));plants=[]
for i in range(18):
 name=f'lab_planta_{i:02d}';a=try_load_asset(SOURCE/(name+'.ydr'));full=try_load_asset(W/'polido'/(name+'.ydr')) or try_load_asset(W/'exports_hd'/(name+'.ydr'))
 foliage=a.models[LodLevel.HIGH][0].geometries[0]
 stem=copy.deepcopy(full.models[LodLevel.HIGH][0].geometries[0]);stem.shader_index=1
 stem_shader=copy.deepcopy(full.shader_group.shaders[0]);a.shader_group.shaders.append(stem_shader)
 for key in (f'{name}_0_color',f'{name}_0_normal',f'{name}_0_spec'):
  t=copy.deepcopy(full.shader_group.embedded_textures[key])
  if key.endswith('_color'):t.width=8;t.height=8;t.data=DataSource.create(brown)
  a.shader_group.embedded_textures[key]=t
 extra=copy.deepcopy(foliage);angle=np.deg2rad(27);cs=np.cos(angle);sn=np.sin(angle)
 for mesh in (extra,):
  p=mesh.vertex_buffer['Position'];x=p[:,0].copy();y=p[:,1].copy();p[:,0]=1.04*(cs*x-sn*y);p[:,1]=1.04*(sn*x+cs*y)
 a.models[LodLevel.HIGH][0].geometries.extend([stem,extra])
 save_asset(a,TARGET,OUT,name);plants.append(name)

typ=try_load_asset(SOURCE/'cidade_laboratorio.ytyp')
floor_arch=next(a for a in typ.archetypes if a.name=='lab_piso')
floor_xyz=np.concatenate([g.vertex_buffer['Position'] for ms in floor.models.values() for m in ms for g in m.geometries])
floor_lo=floor_xyz.min(axis=0);floor_hi=floor_xyz.max(axis=0)
floor_arch.bb_min=Vector(floor_lo);floor_arch.bb_max=Vector(floor_hi)
floor_arch.bs_center=Vector((floor_lo+floor_hi)/2);floor_arch.bs_radius=float(np.linalg.norm(floor_hi-floor_lo)/2)
door_arch=next(a for a in typ.archetypes if a.name=='lab_porta')
door_arch.bb_min=Vector((0,-.028,-.01));door_arch.bb_max=Vector((1.24,.028,2.29));door_arch.bs_center=Vector((.62,0,1.14));door_arch.bs_radius=1.42
template=next(a for a in typ.archetypes if a.name=='lab_ventilacao')
typ.archetypes=[a for a in typ.archetypes if not a.name.startswith('lab_rotor_')]
for name,_ in rotors:
 ar=copy.deepcopy(template);ar.name=name;ar.asset_name=name
 ar.bb_min=Vector((-.48,-.48,-.48));ar.bb_max=Vector((.48,.48,.48));ar.bs_center=Vector((0,0,0));ar.bs_radius=.84;ar.lod_dist=120
 typ.archetypes.append(ar)
save_asset(typ,TARGET,OUT,'cidade_laboratorio')

for name in ('lab_piso','lab_porta','lab_ventilacao',*plants,*[n for n,_ in rotors]):
 assert try_load_asset(OUT/(name+'.ydr')) is not None,name
assert try_load_asset(OUT/'cidade_laboratorio.ytyp') is not None
print('DETAIL_FIX_OK',json.dumps({'fan_triangles':counts,'rotors':rotors,'plants':len(plants)}),flush=True)
