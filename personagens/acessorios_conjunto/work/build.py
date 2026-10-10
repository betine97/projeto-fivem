import bpy,sys,addon_utils,json,hashlib,math
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
import numpy as np
sys.path[:0]=[r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps',r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\sollumz']
addon_utils.enable('Sollumz',default_set=True)
root=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(root.parent/'camisa_estampada/PERSONAGEM_COM_CAMISA.blend'))
rig=bpy.data.objects['MP_M_FREEMODE_01_RIG'];sc=bpy.context.scene
def import_piece(name,filename):
 before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(Path(r'C:\Users\erons\Downloads')/filename))
 obj=next(o for o in set(bpy.data.objects)-before if o.type=='MESH');obj.name=name
 for c in list(obj.users_collection):c.objects.unlink(obj)
 bpy.data.collections['03_CRIAR_ROUPAS_AQUI'].objects.link(obj)
 for mat in obj.data.materials:
  for n in mat.node_tree.nodes:
   if n.type=='TEX_IMAGE':n.image.pack()
 obj.parent=rig;mod=obj.modifiers.new('ESQUELETO_ORIGINAL_GTA','ARMATURE');mod.object=rig
 return obj
def uvhash(obj):
 a=np.empty(len(obj.data.uv_layers[0].data)*2,dtype=np.float32);obj.data.uv_layers[0].data.foreach_get('uv',a);return hashlib.sha256(a.tobytes()).hexdigest()
shoes=import_piece('MOCASSINS_MARRONS','Meshy_AI_brown_leather_loafers_1005054801_image-to-3d-texture.glb')
shoe_uv=uvhash(shoes)
# The pair is separated by the X=0 plane; keep all source geometry and UVs.
assert not any(min(shoes.data.vertices[i].co.x for i in p.vertices)<0<max(shoes.data.vertices[i].co.x for i in p.vertices) for p in shoes.data.polygons),'Shoes cross the pair separator'
centers={}
for sign in (-1,1):
 xs=[v.co.x for v in shoes.data.vertices if (v.co.x>=0)==(sign>0)];centers[sign]=(min(xs)+max(xs))/2
 for suffix in ('Foot','Toe0'):shoes.vertex_groups.new(name='SKEL_'+('L' if sign>0 else 'R')+'_'+suffix)
for v in shoes.data.vertices:
 sign=1 if v.co.x>=0 else -1;side='L' if sign>0 else 'R'
 x,y,z=v.co;v.co=(sign*.16+(x-centers[sign])*.15,y*.15-.035,z*.15-.956)
 toe=max(0,min(1,(-v.co.y-.10)/.075))*.25
 shoes.vertex_groups['SKEL_'+side+'_Foot'].add([v.index],1-toe,'REPLACE')
 if toe:shoes.vertex_groups['SKEL_'+side+'_Toe0'].add([v.index],toe,'REPLACE')
assert uvhash(shoes)==shoe_uv
# Native bare feet remain as hidden authoring reference; the shoe component replaces them.
feet=bpy.data.objects.get('REF_PES_DESCALCOS_APT01')
if feet:feet.hide_render=True;feet.hide_set(True)
watch=import_piece('RELOGIO_DOURADO','Meshy_AI_gold_luxury_watch_3d_1005054634_image-to-3d-texture.glb')
watch_uv=uvhash(watch)
forearm=rig.data.bones['SKEL_L_Forearm'];hand=rig.data.bones['SKEL_L_Hand']
direction=(hand.head_local-forearm.head_local).normalized()
center=hand.head_local-direction*.035
rotation=forearm.matrix_local.to_3x3()@Matrix.Rotation(math.pi,3,'X')
for v in watch.data.vertices:v.co=center+rotation@(v.co*.044)
watch.vertex_groups.new(name='SKEL_L_Forearm').add(list(range(len(watch.data.vertices))),1,'REPLACE')
assert uvhash(watch)==watch_uv
bpy.ops.object.select_all(action='DESELECT');watch.select_set(True);bpy.context.view_layer.objects.active=watch
bpy.ops.wm.save_as_mainfile(filepath=str(root/'CONJUNTO_COMPLETO.blend'))
for side,angle in [('L',.4),('R',-.4)]:
 b=rig.pose.bones['SKEL_'+side+'_UpperArm'];q=b.bone.matrix_local.to_quaternion();b.rotation_mode='QUATERNION';b.rotation_quaternion=q.inverted()@Quaternion((0,1,0),angle)@q
sc.render.filepath=str(root/'preview.png');bpy.ops.render.render(write_still=True)
# A single close-up lets us inspect the wrist fit without another full-body render.
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();w=watch.evaluated_get(dg);mesh=w.to_mesh();center=sum((v.co for v in mesh.vertices),Vector())/len(mesh.vertices);w.to_mesh_clear()
cam=sc.camera;cam.location=center+Vector((.22,-.45,.12));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.22
sc.render.resolution_x=700;sc.render.resolution_y=700;sc.render.filepath=str(root/'relogio_encaixe.png');bpy.ops.render.render(write_still=True)
report={'shoes':{'vertices':len(shoes.data.vertices),'triangles':len(shoes.data.polygons),'uv_sha256':shoe_uv,'scale':.15,'native_foot_centers_x':[-.16,.16]},'watch':{'vertices':len(watch.data.vertices),'triangles':len(watch.data.polygons),'uv_sha256':watch_uv,'scale':.044,'bone':'SKEL_L_Forearm'},'original_uvs_preserved':True}
(root/'work/validation.json').write_text(json.dumps(report,indent=2));print('ACCESSORIES_BUILD_OK',json.dumps(report),flush=True)
