import bpy,sys,addon_utils,math,struct,bmesh,copy,shutil,heapq
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.kdtree import KDTree
import xml.etree.ElementTree as ET
root=Path(__file__).resolve().parent;out=root/'exports';out.mkdir(exist_ok=True)
sys.path[:0]=[r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps',r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\sollumz']
addon_utils.enable('Sollumz',default_set=True)
from Sollumz.sollumz_properties import LODLevel
from Sollumz.ydr.shader_materials import create_shader
from Sollumz.tools.meshhelper import mesh_add_missing_uv_maps,mesh_add_missing_color_attrs
from Sollumz.ydd.yddexport import export_ydd
from Sollumz.iecontext import ExportContext,ExportSettings,export_context_scope
from szio.gta5 import try_load_asset,save_asset,AssetTarget,AssetFormat,AssetVersion
from szio.rpf import open_rpf
bpy.ops.wm.open_mainfile(filepath=str(root/'donor.blend'))
rig=bpy.data.objects['a_m_y_business_01'];rig.name='cartelking'
donors=[o for o in bpy.data.objects if o.type=='MESH']
native_materials={o.name:o.data.materials[0].copy() for o in donors}
samples=[]
for o in donors:
 if o.name in ['SKEL_ROOT.004','SKEL_ROOT.006','SKEL_ROOT.007','SKEL_ROOT.001','SKEL_ROOT.002']:continue
 for v in o.data.vertices:
  w={o.vertex_groups[g.group].name:g.weight for g in v.groups if g.weight>0}
  samples.append((v.co.copy(),w))
kd=KDTree(len(samples))
for i,(co,w) in enumerate(samples):kd.insert(co,i)
kd.balance()
before=set(bpy.data.objects)
source=next(Path(r'C:\Users\erons\Downloads\Meshy_AI_The_Cartel_King_1002154146_texture_fbx').rglob('*.fbx'))
bpy.ops.import_scene.fbx(filepath=str(source));src=next(o for o in bpy.data.objects if o not in before and o.type=='MESH')
mesh=src.data.copy();mesh.transform(src.matrix_world)
# Place soles at the donor's ground plane and adapt relaxed arms to GTA A-pose.
arm_ids=set()
for v in mesh.vertices:
 x,y,z=v.co;v.co=(x*1.085,y*1.085,z*1.085-.985)
original_coords=[v.co.copy() for v in mesh.vertices]
adj=[set() for v in mesh.vertices]
for e in mesh.edges:
 a,b=e.vertices;adj[a].add(b);adj[b].add(a)
# Follow connected arms below the shoulder, instead of using a cutoff at the
# wrist that previously sent the fingertips to leg bones.
def surface_dist(seeds):
 distances=[float('inf')]*len(mesh.vertices);queue=[]
 for i in seeds:distances[i]=0;heapq.heappush(queue,(0,i))
 while queue:
  d,i=heapq.heappop(queue)
  if d>distances[i]:continue
  for j in adj[i]:
   nd=d+(original_coords[i]-original_coords[j]).length
   if nd<distances[j]:distances[j]=nd;heapq.heappush(queue,(nd,j))
 return distances
arm_seeds={i for i,p in enumerate(original_coords) if abs(p.x)>.29 and -.40<p.z<.28}
body_seeds={i for i,p in enumerate(original_coords) if p.z<-.58 or (abs(p.x)<.13 and p.z<.45)}
ad,bd=surface_dist(arm_seeds),surface_dist(body_seeds)
arm_ids={i for i,p in enumerate(original_coords) if ad[i]<bd[i] and -.56<p.z<.47}
for v in mesh.vertices:
 if v.index in arm_ids:
  x,y,z=v.co;s=1 if x>=0 else -1
  # Rest-pose correction: rotate the entire connected limb, including fingers.
  dx=abs(x)-.20;dz=z-.45;angle=.43
  v.co.x=s*(.20+.82*(dx*math.cos(angle)-dz*math.sin(angle)))
  v.co.z=.45+.82*(dx*math.sin(angle)+dz*math.cos(angle))
mesh.update()
weights=[]
for v in mesh.vertices:
 acc={}
 for co,i,dist in kd.find_n(v.co,4):
  factor=1/max(dist,.008)**3
  for name,w in samples[i][1].items():
   if name not in rig.data.bones or name.startswith('FB_'):name='SKEL_Head'
   acc[name]=acc.get(name,0)+w*factor
 x,y,z=v.co
 side='L' if x>=0 else 'R'
 if z>.57:acc={'SKEL_Head':1.0}
 elif v.index in arm_ids:
  # Keep sleeves and hands on their own limb, never the nearby jacket.
  allowed=['UpperArm','Forearm','Hand','Finger','ArmRoll']
  acc={n:w for n,w in acc.items() if ('_'+side+'_') in n and any(a in n for a in allowed)}
  if not acc:acc={'SKEL_'+side+'_UpperArm' if z>.2 else 'SKEL_'+side+'_Forearm':1.0}
 elif z<-.20:
  # Continuous joint blends avoid stray weights across the loose trouser folds.
  if z<-.87:acc={'SKEL_'+side+'_Foot':1.0}
  elif z<-.77:
   t=(-.77-z)/.10;acc={'SKEL_'+side+'_Foot':t,'SKEL_'+side+'_Calf':1-t}
  elif z<-.57:acc={'SKEL_'+side+'_Calf':1.0}
  elif z<-.43:
   t=(-.43-z)/.14;acc={'SKEL_'+side+'_Calf':t,'SKEL_'+side+'_Thigh':1-t}
  else:acc={'SKEL_'+side+'_Thigh':1.0}
 else:
  acc={n:w for n,w in acc.items() if any(a in n for a in ['Spine','Pelvis','Neck','Clavicle','Head'])}
  if not acc:acc={'SKEL_Spine2':1.0}
 best=sorted(acc.items(),key=lambda a:a[1],reverse=True)[:4];total=sum(w for _,w in best)
 assert total>0
 weights.append({n:w/total for n,w in best})

# Smooth only along mesh edges, so adjacent triangles share gradual influences.
# Different limbs separated in space are never blended merely for being close.
for iteration in range(6):
 updated=[]
 for i,w in enumerate(weights):
  if original_coords[i].z>.57 or not adj[i]:updated.append(w);continue
  acc={n:v*.5 for n,v in w.items()}
  neighbors=[j for j in adj[i] if (i in arm_ids)==(j in arm_ids) or original_coords[i].z>.3]
  if not neighbors:updated.append(w);continue
  for j in neighbors:
   for n,value in weights[j].items():acc[n]=acc.get(n,0)+value*.5/len(neighbors)
  best=sorted(acc.items(),key=lambda a:a[1],reverse=True)[:4];total=sum(v for _,v in best)
  updated.append({n:v/total for n,v in best if v>0})
 weights=updated
print('CONNECTED_ARM_VERTICES',len(arm_ids))

def texture(suffix,name,size=1024):
 im=bpy.data.images.load(str(source.with_name(source.stem+suffix+'.png')));im.scale(size,size)
 px=(np.asarray(im.pixels[:]).reshape(size,size,4)*255).clip(0,255).astype(np.uint8)
 hdr=[124,0x100f,size,size,size*4,0,0]+[0]*11+[32,0x41,0,32,255,65280,16711680,4278190080]+[0x1000,0,0,0,0]
 p=out/(name+'.dds');p.write_bytes(b'DDS '+struct.pack('<31I',*hdr)+np.flipud(px).tobytes());bpy.data.images.remove(im)
 im=bpy.data.images.load(str(p));im.pack();return im
mat=create_shader('ped.sps');mat.name='CARTELKING_SKIN_CLOTH'
for key,suffix,name in [('DiffuseSampler','','cartelking_diff'),('BumpSampler','_normal','cartelking_normal'),('SpecSampler','_metallic','cartelking_spec')]:
 n=mat.node_tree.nodes.get(key)
 if n:
  n.image=texture(suffix,name,1024 if not suffix else 256);n.texture_properties.embedded=True
  if suffix:n.image.colorspace_settings.name='Non-Color'
for name,value in [('specularIntensityMult',.12),('specularFalloffMult',35)]:
 n=mat.node_tree.nodes.get(name)
 if n:n.set_float(value)
regions=[]
for p in mesh.polygons:
 z=p.center.z;regions.append('head' if z>.53 else ('lowr' if z<-.16 and abs(p.center.x)<.25 else 'uppr'))
for ob in donors:
 kind='head' if ob.name in ['SKEL_ROOT','SKEL_ROOT.004'] else ('lowr' if ob.name=='SKEL_ROOT.005' else ('uppr' if ob.name=='SKEL_ROOT.003' else 'hidden'))
 m=mesh.copy();bm=bmesh.new();bm.from_mesh(m);bm.faces.ensure_lookup_table()
 layer=bm.verts.layers.int.new('source_index')
 for v in bm.verts:v[layer]=v.index
 bmesh.ops.delete(bm,geom=[f for f in bm.faces if regions[f.index]!=kind],context='FACES')
 bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
 if kind=='hidden':
  vs=[bm.verts.new(co) for co in [(0,0,0),(.001,0,0),(0,.001,0)]];bm.faces.new(vs)
 bm.verts.ensure_lookup_table();source_ids=[v[layer] for v in bm.verts];bm.to_mesh(m);bm.free()
 component_mat=mat.copy();component_mat.name='CARTEL_'+ob.name
 native=native_materials[ob.name]
 for key in ['DiffuseSampler','BumpSampler','SpecSampler']:
  old=native.node_tree.nodes.get(key);new=component_mat.node_tree.nodes.get(key)
  if old and old.image and new and new.image:
   img=new.image.copy();img.name=old.image.name.split('.')[0]+'.dds';img.filepath=str(out/img.name);img.pack();new.image=img
 # Slot zero is the engine-managed ped_default material. The visible mesh
 # must use its own ped.sps material, as in the native donor.
 reserved=create_shader('ped_default.sps');reserved.name='CARTEL_RESERVED_'+ob.name
 m.materials.clear();m.materials.append(reserved);m.materials.append(component_mat)
 if m.uv_layers:m.uv_layers[0].name='UVMap 0'
 mesh_add_missing_uv_maps(m);mesh_add_missing_color_attrs(m)
 for p in m.polygons:p.material_index=1;p.use_smooth=True
 for a in m.color_attributes:
  for d in a.data:d.color=(1,1,1,0) if a.name.endswith('0') else (0,0,0,0)
 ob.data=m;ob.vertex_groups.clear()
 for name in sorted({n for w in weights for n in w}|{'SKEL_Pelvis'}):ob.vertex_groups.new(name=name)
 for i,source_id in enumerate(source_ids):
  for n,w in ({'SKEL_Pelvis':1} if kind=='hidden' else weights[source_id]).items():ob.vertex_groups[n].add([i],w,'REPLACE')
 for lod in [LODLevel.HIGH,LODLevel.MEDIUM,LODLevel.LOW,LODLevel.VERYLOW]:ob.sz_lods.get_lod(lod).mesh=m
 print('COMPONENT',kind,ob.parent.name,len(m.vertices),len(m.polygons))
for o in list(bpy.data.objects):
 if o not in before:bpy.data.objects.remove(o,do_unlink=True)
targets=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
with export_context_scope(ExportContext('cartelking',ExportSettings(targets=targets))):bundle=export_ydd(rig)
txd=try_load_asset(root.parent/'animacoes/work/assets/a_m_y_business_01.ytd');txd.textures.clear()
for d in bundle.main_asset.drawables.values():
 txd.textures.update(d.shader_group.embedded_textures);d.shader_group.embedded_textures.clear()
bundle.save(out,targets);save_asset(txd,targets,out,'cartelking')
shutil.copy2(root.parent/'animacoes/work/assets/a_m_y_business_01.yft',out/'cartelking.yft')
shutil.copy2(root.parent/'animacoes/work/assets/a_m_y_business_01.ymt',out/'cartelking.ymt')
archive=open_rpf(r'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V\update\x64\dlcpacks\mpheist\dlc.rpf')
meta=ET.fromstring(archive.read_bytes('common/data/peds.meta'));items=meta.find('InitDatas');template=copy.deepcopy(next(i for i in items if i.findtext('Name')=='S_M_M_FIBSec_01'));items.clear();items.append(template)
for key,value in {'Name':'cartelking','PropsName':'null','Pedtype':'CIVMALE','DecisionMakerName':'DEFAULT','RelationshipGroup':'CIVMALE','StrafeClipSet':'move_ped_strafing'}.items():template.find(key).text=value
ET.indent(meta);ET.ElementTree(meta).write(out/'peds.meta',encoding='utf-8',xml_declaration=True)
bpy.ops.wm.save_as_mainfile(filepath=str(root/'cartelking.blend'))
assert len(try_load_asset(out/'cartelking.ydd').drawables)==8
assert all('.001' not in n for n in txd.textures), 'Blender image suffix leaked into GTA texture names'
print('CARTEL_EXPORT_OK',len(mesh.vertices),len(txd.textures))
