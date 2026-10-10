import bpy,sys,addon_utils,json,hashlib,struct,math
from pathlib import Path
from mathutils import Vector,Quaternion
from mathutils.kdtree import KDTree
import numpy as np
sys.path[:0]=[r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps',r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\sollumz']
addon_utils.enable('Sollumz',default_set=True)
root=Path(__file__).resolve().parents[1]
source=Path(r'C:\Users\erons\Downloads\Meshy_AI_guard_character_3d_1005050026_image-to-3d-texture.glb')
bpy.ops.wm.open_mainfile(filepath=str(root.parent/'templates_freemode/01_BASE_ROUPAS.blend'))
rig=bpy.data.objects['MP_M_FREEMODE_01_RIG'];rig.hide_select=False;rig.show_in_front=True
body=list(bpy.data.collections['01_CORPO_REFERENCIA'].objects)
# Partition donors by limb, so glove weights never come from the adjacent hip.
regions={k:[] for k in ['body','L_arm','R_arm','L_leg','R_leg','head']}
for o in body:
 for v in o.data.vertices:
  w={o.vertex_groups[g.group].name:g.weight for g in v.groups if g.weight>1e-6}
  side='L' if v.co.x>0 else 'R'
  if o.name=='REF_CABECA_000':key='head'
  elif abs(v.co.x)>.225 and v.co.z>-.42:key=side+'_arm'
  elif v.co.z<-.15:key=side+'_leg'
  else:key='body'
  regions[key].append((v.co.copy(),w))
trees={}
for key,rows in regions.items():
 tree=KDTree(len(rows))
 for i,(co,w) in enumerate(rows):tree.insert(co,i)
 tree.balance();trees[key]=tree
before=set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=str(source))
mesh=next(o for o in set(bpy.data.objects)-before if o.type=='MESH')
mesh.name='GUARDA_MALHA_ORIGINAL';mesh.data.name='GUARDA_TOPOLOGIA_ORIGINAL'
for mat in mesh.data.materials:
 for n in mat.node_tree.nodes:
  if n.type=='TEX_IMAGE' and n.image:n.image.pack()
def arrays(m):
 co=np.empty(len(m.vertices)*3,dtype=np.float32);m.vertices.foreach_get('co',co)
 ix=np.empty(len(m.loops),dtype=np.int32);m.loops.foreach_get('vertex_index',ix)
 uv=np.empty(len(m.uv_layers[0].data)*2,dtype=np.float32);m.uv_layers[0].data.foreach_get('uv',uv)
 return co,ix,uv
original_arrays=arrays(mesh.data)
original_mat=mesh.data.materials[0]
texture_hashes={n.image.name:hashlib.sha256(bytes(n.image.packed_file.data)).hexdigest() for n in original_mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image}
# Only a global placement transform: no sculpt, welding, remesh or reduction.
# The source already uses the GTA A pose and metres.
mesh.location.z=-1.002028
mesh.parent=rig
for b in rig.data.bones:mesh.vertex_groups.new(name=b.name)
weights=[];unweighted=[]
for v in mesh.data.vertices:
 p=v.co+Vector((0,0,-1.002028));side='L' if p.x>0 else 'R'
 if p.z>.53:key='head'
 elif abs(p.x)>(.215+max(0,.40-p.z)*.18) and p.z>-.40:key=side+'_arm'
 elif p.z<-.17:key=side+'_leg'
 else:key='body'
 acc={}
 for co,idx,dist in trees[key].find_n(p,8):
  fac=1/max(dist,.006)**3
  for name,w in regions[key][idx][1].items():
   if name.startswith('MH_'):continue
   if name.startswith('FB_'):name='SKEL_Head'
   if key.endswith('_arm') and not ('_'+side+'_' in name and any(s in name for s in ['UpperArm','Forearm','Hand','Finger','ArmRoll'])):continue
   if key.endswith('_leg') and not (name=='SKEL_Pelvis' or ('_'+side+'_' in name and any(s in name for s in ['Thigh','Calf','Foot','Toe']))):continue
   acc[name]=acc.get(name,0)+w*fac
 if key=='head':acc={'SKEL_Head':1}
 if key.endswith('_leg') and p.z>-.32 and abs(p.x)<.07:
  t=max(0,min(1,(-.17-p.z)/.15));left=max(0,min(1,(p.x+.07)/.14));acc={'SKEL_Pelvis':1-t,'SKEL_L_Thigh':t*left,'SKEL_R_Thigh':t*(1-left)}
 if not acc:acc={('SKEL_'+side+'_UpperArm' if key.endswith('_arm') else 'SKEL_'+side+'_Thigh' if key.endswith('_leg') else 'SKEL_Spine2'):1}
 top=sorted(acc.items(),key=lambda x:x[1],reverse=True)[:4];total=sum(w for n,w in top)
 row={n:w/total for n,w in top if w>0}
 for name,w in row.items():mesh.vertex_groups[name].add([v.index],w,'REPLACE')
 weights.append(row)
 if not row:unweighted.append(v.index)
 if v.index%50000==0:print('BIND',v.index,flush=True)
mod=mesh.modifiers.new('ESQUELETO_GTA','ARMATURE');mod.object=rig
assert all(np.array_equal(a,b) for a,b in zip(original_arrays,arrays(mesh.data)))
assert all(n.image.packed_file and hashlib.sha256(bytes(n.image.packed_file.data)).hexdigest()==texture_hashes[n.image.name] for n in original_mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image)
assert not unweighted
for o in list(bpy.data.objects):
 if o not in [mesh,rig]:bpy.data.objects.remove(o,do_unlink=True)
sc=bpy.context.scene;sc.unit_settings.system='METRIC';sc.unit_settings.scale_length=1
sc.render.engine='CYCLES';sc.cycles.samples=20;sc.cycles.use_denoising=True;sc.render.resolution_x=800;sc.render.resolution_y=1000;sc.render.resolution_percentage=100;sc.render.film_transparent=True
sc.world.use_nodes=True;sc.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.5
def aim(o,pos,target):o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
d=bpy.data.cameras.new('Camera');cam=bpy.data.objects.new('Camera',d);sc.collection.objects.link(cam);d.type='ORTHO';d.ortho_scale=2.07;sc.camera=cam;aim(cam,(0,-5,-.1),(0,0,-.1))
for pos,energy in [((-3,-4,3),400),((3,-3,1),250)]:
 d=bpy.data.lights.new('Estudio','AREA');o=bpy.data.objects.new('Estudio',d);sc.collection.objects.link(o);d.energy=energy;d.size=3;aim(o,pos,(0,0,-.1))
bpy.ops.object.select_all(action='DESELECT');mesh.select_set(True);bpy.context.view_layer.objects.active=mesh
bpy.ops.wm.save_as_mainfile(filepath=str(root/'GUARDA_ESQUELETO_GTA.blend'))
sc.render.filepath=str(root/'preview_frente.png');bpy.ops.render.render(write_still=True)
for side,angle in [('L',.40),('R',-.40)]:
 b=rig.pose.bones['SKEL_'+side+'_UpperArm'];q=b.bone.matrix_local.to_quaternion();b.rotation_mode='QUATERNION';b.rotation_quaternion=q.inverted()@Quaternion((0,1,0),angle)@q
bpy.context.view_layer.update();sc.render.filepath=str(root/'preview_bracos_baixos.png');bpy.ops.render.render(write_still=True)
for name,angle in [('SKEL_L_Forearm',-.8),('SKEL_R_Thigh',-.35),('SKEL_L_Calf',.55)]:
 b=rig.pose.bones[name];q=b.bone.matrix_local.to_quaternion();b.rotation_mode='QUATERNION';b.rotation_quaternion=q.inverted()@Quaternion((1,0,0),angle)@q
bpy.context.view_layer.update();sc.render.filepath=str(root/'teste_articulacao.png');bpy.ops.render.render(write_still=True)
dg=bpy.context.evaluated_depsgraph_get();ev=mesh.evaluated_get(dg);deformed=ev.to_mesh()
stretched=[]
for e in mesh.data.edges:
 a,b=e.vertices;d0=(mesh.data.vertices[a].co-mesh.data.vertices[b].co).length;d1=(deformed.vertices[a].co-deformed.vertices[b].co).length
 if d1>max(.12,d0*5):stretched.append((e.index,d0,d1,[list(mesh.data.vertices[i].co) for i in (a,b)],[[ (mesh.vertex_groups[g.group].name,g.weight) for g in mesh.data.vertices[i].groups] for i in (a,b)]))
ev.to_mesh_clear()
report={'source':str(source),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'vertices':len(mesh.data.vertices),'triangles':len(mesh.data.polygons),'geometry_unchanged':True,'uv_unchanged':True,'material_unchanged':True,'packed_texture_sha256':texture_hashes,'placement_translation':[0,0,-1.002028],'scale':[1,1,1],'bones':len(rig.data.bones),'max_influences':max(map(len,weights)),'unweighted_vertices':len(unweighted),'extreme_stretched_edges':stretched[:20],'extreme_stretched_edge_count':len(stretched)}
(root/'work/validation.json').write_text(json.dumps(report,indent=2))
print('GUARD_BIND_OK',json.dumps(report),flush=True)
