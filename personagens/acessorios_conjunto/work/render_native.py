import bpy,sys,json,addon_utils
from pathlib import Path
from mathutils import Quaternion,Vector
sys.path[:0]=[r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps',r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\sollumz']
addon_utils.enable('Sollumz',default_set=True)
root=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(root/'CONJUNTO_COMPLETO.blend'))
for name in ('PELE_PES_MOCASSINS','PELE_TORNOZELOS_MOCASSINS','FORRO_MOCASSINS'):
 if name in bpy.data.objects:bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
pieces=[(root.parent/'calca_bege',{'object':'CALCA_BEGE','component':'lowr_008_u'}),(root.parent/'camisa_estampada',None),(root/'sapatos',None),(root/'relogio',None)]
for folder,cfg in pieces:
 cfg=cfg or json.loads((folder/'export_config.json').read_text())
 bpy.data.objects.remove(bpy.data.objects[cfg['object']],do_unlink=True)
 before=set(bpy.data.objects)
 bpy.ops.sollumz.import_assets(directory=str(folder/'exports'),files=[{'name':cfg['component']+'.ydd'}],use_custom_settings=True,dwd_import_external_skeleton='SAVED',dwd_import_external_skeleton_saved_path=str(folder/'source/mp_m_freemode_01.yft'))
 for obj in set(bpy.data.objects)-before:
  if obj.type!='MESH':continue
  for mat in obj.data.materials:
   if not mat or not mat.node_tree:continue
   for node in mat.node_tree.nodes:
    if node.type!='TEX_IMAGE':continue
    file=folder/'work/audit'/(node.sollumz_texture_name+'.dds')
    if file.exists():
     node.image=bpy.data.images.load(str(file),check_existing=False)
     if node.name!='DiffuseSampler':node.image.colorspace_settings.name='Non-Color'
  # Match the neutral native-body preview for skin; the game's ped shader
  # includes skin tinting features that the Blender node preview approximates.
  for slot,mat in enumerate(list(obj.data.materials)):
   if not mat or not mat.node_tree:continue
   node=mat.node_tree.nodes.get('DiffuseSampler')
   if node and node.image and node.sollumz_texture_name in {'feet_diff_001_a_whi','lowr_diff_014_a_whi'}:
    skin=bpy.data.materials.new('PREVIEW_PELE_NATIVA');skin.use_nodes=True
    tex=skin.node_tree.nodes.new('ShaderNodeTexImage');tex.image=node.image
    bs=skin.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.55
    skin.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);obj.data.materials[slot]=skin
rigs=[o for o in bpy.data.objects if o.type=='ARMATURE']
def pose(name,axis,angle):
 for rig in rigs:
  b=rig.pose.bones.get(name)
  if b:
   q=b.bone.matrix_local.to_quaternion();b.rotation_mode='QUATERNION';b.rotation_quaternion=q.inverted()@Quaternion(axis,angle)@q
pose('SKEL_L_UpperArm',(0,1,0),.4);pose('SKEL_R_UpperArm',(0,1,0),-.4)
if '--revision3' in sys.argv:
 sc=bpy.context.scene;sc.cycles.samples=16;cam=sc.camera
 def render(name,location,target,scale,rx,ry):
  cam.location=location;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;sc.render.resolution_x=rx;sc.render.resolution_y=ry;sc.render.filepath=str(root/name);bpy.ops.render.render(write_still=True)
 render('conjunto_exportado_revisao3.png',(3,-5,.02),(0,0,-.09),2.11,800,1000)
 render('pes_exportados_revisao3.png',(2,-3,-.83),(0,-.025,-.91),.46,800,600)
 render('mangas_exportadas_revisao3.png',(3,-4,.33),(0,0,.30),.96,800,800)
 pose('SKEL_L_UpperArm',(0,1,0),-.40);pose('SKEL_L_Forearm',(0,1,0),-.75)
 pose('SKEL_R_UpperArm',(1,0,0),-.65);pose('SKEL_R_Forearm',(0,1,0),.6)
 render('mangas_movimento_exportadas_revisao3.png',(3,-4,.33),(0,0,.30),1.15,800,800)
 print('NATIVE_REVISION3_RENDER_OK',flush=True);sys.exit(0)
sc=bpy.context.scene;sc.render.filepath=str(root/'preview_exportada.png');bpy.ops.render.render(write_still=True)
pose('SKEL_L_UpperArm',(0,1,0),.15);pose('SKEL_L_Forearm',(0,1,0),-.65)
pose('SKEL_L_Thigh',(1,0,0),-.4);pose('SKEL_L_Calf',(1,0,0),.7);pose('SKEL_L_Toe0',(1,0,0),.15)
sc.camera.location=(3,-5,.02);sc.camera.rotation_euler=(Vector((0,0,-.09))-sc.camera.location).to_track_quat('-Z','Y').to_euler()
sc.render.filepath=str(root/'movimento_exportado.png');bpy.ops.render.render(write_still=True)
print('ACCESSORIES_NATIVE_RENDER_OK',flush=True)
sc.camera.location=(5,-2,-.09);sc.camera.rotation_euler=(Vector((0,0,-.09))-sc.camera.location).to_track_quat('-Z','Y').to_euler()
sc.render.filepath=str(root/'perfil_exportado_corrigido.png');bpy.ops.render.render(write_still=True)
sc.camera.location=(2,-3,-.84);sc.camera.rotation_euler=(Vector((0,0,-.87))-sc.camera.location).to_track_quat('-Z','Y').to_euler();sc.camera.data.ortho_scale=.46
sc.render.resolution_x=800;sc.render.resolution_y=600;sc.render.filepath=str(root/'barra_exportada_corrigida.png');bpy.ops.render.render(write_still=True)
