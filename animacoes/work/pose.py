import bpy,sys,math,json
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
root=Path(__file__).resolve().parent.parent
bpy.ops.wm.open_mainfile(filepath=str(root/'combate_base.blend'))
rig=bpy.data.objects['a_m_y_business_01']; rig.name='GTA_Personagem_Rig'
# Keep one face and one jacket variant; bind every visible component to the same skeleton.
for o in list(bpy.data.objects):
 if o.type=='MESH':
  o.hide_render=o.name.startswith('Bound') or (o.parent and o.parent.name in {'hash_A1286BE2','hash_860228B4','hash_D370CA25'})
  o.hide_set(o.hide_render)
  for m in o.modifiers:
   if m.type=='ARMATURE' and m.object and m.object.name not in {'w_ar_carbinerifle','hash_976FBF04','hash_A1286BE2'}: m.object=rig
for o in bpy.data.objects:
 if o.type=='ARMATURE' and o not in [rig,bpy.data.objects['w_ar_carbinerifle']]: o.hide_set(True)
# Head drawable has additional facial bones absent from the body skeleton.
# Keep its original weights and synchronize shared pose bones, preserving facial hierarchy.
for headname in ['hash_976FBF04','hash_A1286BE2']:
 h=bpy.data.objects[headname]
 for pb in h.pose.bones:
  if pb.name in rig.pose.bones:
   c=pb.constraints.new('COPY_TRANSFORMS');c.target=rig;c.subtarget=pb.name;c.owner_space='POSE';c.target_space='POSE'
rig.location=(0,0,0.55)
# Set absolute bone matrices without modifying original rest skeleton or bone tags.
def orient(name,direction):
 b=rig.pose.bones[name]; current=b.matrix.copy()
 q=current.to_quaternion()
 child_name={'Thigh':'Calf','Calf':'Foot','UpperArm':'Forearm','Forearm':'Hand','Foot':'Toe0','Hand':'Finger10'}
 suffix=name.split('_')[-1]; child=rig.pose.bones.get(name.rsplit('_',1)[0]+'_'+child_name.get(suffix,''))
 old=(child.head-b.head).normalized() if child else q@Vector((0,1,0))
 new=old.rotation_difference(Vector(direction).normalized())@q
 b.matrix=Matrix.Translation(current.translation)@new.to_matrix().to_4x4()
 bpy.context.view_layer.update()
def chain(upper,lower,end,target,pole):
 a=rig.pose.bones[upper].head.copy(); endpos=Vector(target)-rig.location
 l1=(rig.data.bones[lower].head_local-rig.data.bones[upper].head_local).length
 l2=(rig.data.bones[end].head_local-rig.data.bones[lower].head_local).length
 axis=endpos-a; d=min(axis.length,l1+l2-0.001); u=axis.normalized()
 p=Vector(pole)-rig.location-a; p=(p-u*p.dot(u)).normalized()
 along=(l1*l1-l2*l2+d*d)/(2*d); height=math.sqrt(max(0,l1*l1-along*along))
 joint=a+u*along+p*height
 orient(upper,joint-a); orient(lower,endpos-rig.pose.bones[lower].head)
# Legs: left foot forward, right knee down and foot behind.
chain('SKEL_R_Thigh','SKEL_R_Calf','SKEL_R_Foot',(-.14,.35,.13),(-.14,-.3,.04))
chain('SKEL_L_Thigh','SKEL_L_Calf','SKEL_L_Foot',(.15,-.44,.085),(.15,-.7,.55))
orient('SKEL_L_Foot',(0,-1,-.40)); orient('SKEL_R_Foot',(0,-.50,-.86))
# Use the supplied tactical aim as a grip reference on the actual GTA skeleton.
# Preserve the independently authored kneeling legs; copy only the spine descendants.
upper=json.loads((root/'work/aim_upper.json').read_text())
for bone in rig.pose.bones:
 if bone.name=='SKEL_Spine_Root' or any(p.name=='SKEL_Spine_Root' for p in bone.parent_recursive):
  if bone.name in upper and bone.name.startswith(('SKEL_','PH_','IK_')):
   bone.rotation_mode='QUATERNION';bone.rotation_quaternion=Matrix(upper[bone.name]['matrix']).to_quaternion()
bpy.context.view_layer.update()
# Bring the support wrist under the carbine handguard while preserving its palm orientation.
hand=rig.pose.bones['SKEL_L_Hand'];hand_q=hand.matrix.to_quaternion()
chain('SKEL_L_UpperArm','SKEL_L_Forearm','SKEL_L_Hand',(-.15,-.58,.935),(.28,-.25,.75))
hand.matrix=Matrix.Translation(hand.head)@hand_q.to_matrix().to_4x4()
bpy.context.view_layer.update()
# Close the fingers using quaternion channels (same representation used by the exporter).
for side in ['L','R']:
 for finger in range(1,5):
  for segment in [0,1,2]:
   pb=rig.pose.bones[f'SKEL_{side}_Finger{finger}{segment}'];pb.rotation_mode='QUATERNION'
   # The reference already includes the grip. Extra local-Z curls twisted
   # fingers outwards and made the left hand appear open beside the rifle.
   if pb.name in upper: pb.rotation_quaternion=Quaternion(upper[pb.name]['quat'])
bpy.context.view_layer.update()
# Bake the standing ped origin convention into the root track, keeping scene world pose unchanged.
rootbone=rig.pose.bones['SKEL_ROOT'];rootmatrix=rootbone.matrix.copy();rootmatrix.translation.z-=0.43;rootbone.matrix=rootmatrix
rig.location.z+=0.43
bpy.context.view_layer.update()
# Explicitly mark this as a first pose study, not an approved game clip.
rig['status']='CANDIDATO DE TESTE - pose e recuo; validar encaixe da arma no FiveM'
rig.show_in_front=True
for b in rig.pose.bones:
 b.rotation_mode='QUATERNION'
 b.keyframe_insert(data_path='location',frame=1,group=b.name)
 b.keyframe_insert(data_path='rotation_quaternion',frame=1,group=b.name)
 b.keyframe_insert(data_path='location',frame=30,group=b.name)
 b.keyframe_insert(data_path='rotation_quaternion',frame=30,group=b.name)
rig.animation_data.action.name='ESTUDO_ajoelhar_mira'
# Separate recoil action: all base channels retained, spine motion layered locally.
idle_action=rig.animation_data.action;idle_action.use_fake_user=True
recoil_action=idle_action.copy();recoil_action.name='ESTUDO_recuo';recoil_action.use_fake_user=True
rig.animation_data.action=recoil_action
spine=rig.pose.bones['SKEL_Spine2'];base_q=spine.rotation_quaternion.copy()
for frame,angle in [(1,0),(3,-2),(7,0.6),(12,0),(30,0)]:
 spine.rotation_quaternion=base_q@Quaternion((0,1,0),math.radians(angle));spine.keyframe_insert(data_path='rotation_quaternion',frame=frame,group=spine.name)
rig.animation_data.action=idle_action;spine.rotation_quaternion=base_q
# GTA weapon attachment uses the PH_R_Hand attachment bone; preserve its transform.
gun=bpy.data.objects['w_ar_carbinerifle']
right=rig.matrix_world@rig.pose.bones['SKEL_R_Hand'].head
left=rig.matrix_world@rig.pose.bones['SKEL_L_Hand'].head
forward=Vector((0,-1,0))
gun.rotation_mode='QUATERNION';gun.rotation_quaternion=Matrix((forward,Vector((0,0,1)).cross(forward).normalized(),forward.cross(Vector((0,0,1)).cross(forward)).normalized())).transposed().to_quaternion()
gripR=gun.data.bones['Gun_GripR'].head_local
gun.location=right-(gun.rotation_quaternion@gripR)
bpy.context.view_layer.update()
gun_world=gun.matrix_world.copy()
follow=gun.constraints.new('CHILD_OF');follow.target=rig;follow.subtarget='SKEL_R_Hand';follow.inverse_matrix=(rig.matrix_world@rig.pose.bones['SKEL_R_Hand'].matrix).inverted()
# Studio materials isolate deformation from the original game's shader implementation.
def mat(name,color):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(*color,1);return m
cloth=mat('Estudo - tecido',(.20,.25,.29));skin=mat('Estudo - pele',(.48,.32,.23));metal=mat('Estudo - carabina',(.045,.055,.065))
for o in bpy.data.objects:
 if o.type=='MESH' and not o.hide_render:
  original=' '.join(m.name for m in o.data.materials)
  m=metal if o.name=='Gun_Root' else skin if 'head_' in original else cloth
  for i in range(len(o.data.materials)):o.data.materials[i]=m
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,0));ground=bpy.context.object;ground.name='Chao referencia Z=0';ground.data.materials.append(mat('Chao',(.15,.17,.2)))
# Reference images packed into the blend, off to the side of the character.
for name,file,x in [('Referencia ajoelhado','ajoelhado-mira.png',3),('Referencia posturas','posturas.png',7)]:
 o=bpy.data.objects.new(name,None);bpy.context.collection.objects.link(o);o.empty_display_type='IMAGE';o.data=bpy.data.images.load(str(root/'referencias'/file));o.data.pack();o.empty_display_size=3.5;o.location=(x,1,1.3);o.rotation_euler=(math.pi/2,0,0)
for name,pos,power,size in [('Principal',(2,-3,4),900,4),('Preenchimento',(-3,-1,3),600,3),('Recorte',(1,3,4),1100,3)]:
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,.7))-o.location).to_track_quat('-Z','Y').to_euler()
d=bpy.data.cameras.new('Camera estudo');cam=bpy.data.objects.new('Camera estudo',d);bpy.context.collection.objects.link(cam);cam.location=(2.4,-3.5,1.8);cam.rotation_euler=(Vector((0,-.12,.7))-cam.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=2.0
sc=bpy.context.scene;sc.camera=cam;sc.render.engine='CYCLES';sc.cycles.samples=16;sc.render.resolution_x=1000;sc.render.resolution_y=1000;sc.render.resolution_percentage=100;sc.render.fps=30;sc.frame_end=30;sc.world.color=(.25,.25,.25)
bpy.ops.object.select_all(action='DESELECT');rig.hide_set(False);rig.select_set(True);bpy.context.view_layer.objects.active=rig
for area in bpy.context.screen.areas:
 if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'
text=bpy.data.texts.new('LEIA-ME');text.write('Estudo inicial da pose ajoelhada baseado nas referencias do usuario.\nEsqueleto e carabina extraidos da instalacao local do GTA.\nNao substitui os arquivos do servidor. Exportacao e deformacao ainda em validacao.\n')
bpy.ops.wm.save_as_mainfile(filepath=str(root/'ajoelhado_refinado.blend'))
sc.render.filepath=str(root/'previa_refinada.png');bpy.ops.render.render(write_still=True)
print('JOINTS',[(n,tuple(rig.matrix_world@rig.pose.bones[n].head)) for n in ['SKEL_R_Calf','SKEL_L_Foot','SKEL_R_Hand','SKEL_L_Hand']])




print('GUNPOINTS',[(n,tuple(gun.matrix_world@gun.data.bones[n].head_local)) for n in ['Gun_GripR','Gun_GripL','Gun_Muzzle','NM_Butt_Marker']])

cam.location=(3,-.1,1.25);cam.rotation_euler=(Vector((0,-.2,.65))-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(root/'previa_lateral.png');bpy.ops.render.render(write_still=True)
