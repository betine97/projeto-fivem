import bpy,sys,json,addon_utils
from pathlib import Path
from mathutils import Quaternion
sys.path[:0]=[r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps',r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\sollumz']
addon_utils.enable('Sollumz',default_set=True)
root=Path(__file__).resolve().parents[1];config=json.loads((root/'export_config.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(root/config['blend']))
bpy.data.objects.remove(bpy.data.objects[config['object']],do_unlink=True)
before=set(bpy.data.objects)
bpy.ops.sollumz.import_assets(directory=str(root/'exports'),files=[{'name':config['component']+'.ydd'}],use_custom_settings=True,dwd_import_external_skeleton='SAVED',dwd_import_external_skeleton_saved_path=str(root/'source/mp_m_freemode_01.yft'))
for obj in set(bpy.data.objects)-before:
 if obj.type!='MESH':continue
 for mat in obj.data.materials:
  if not mat or not mat.node_tree:continue
  for node in mat.node_tree.nodes:
   if node.type!='TEX_IMAGE':continue
   file=root/'work/audit'/(node.sollumz_texture_name+'.dds')
   if file.exists():
    node.image=bpy.data.images.load(str(file),check_existing=False)
    if node.name!='DiffuseSampler':node.image.colorspace_settings.name='Non-Color'
for rig in [o for o in bpy.data.objects if o.type=='ARMATURE']:
 for side,angle in [('L',.4),('R',-.4)]:
  b=rig.pose.bones.get('SKEL_'+side+'_UpperArm')
  if b:
   q=b.bone.matrix_local.to_quaternion();b.rotation_mode='QUATERNION';b.rotation_quaternion=q.inverted()@Quaternion((0,1,0),angle)@q
bpy.context.view_layer.update();bpy.context.scene.render.filepath=str(root/'preview_exportada.png');bpy.ops.render.render(write_still=True)
print('NATIVE_SHIRT_RENDER_OK',flush=True)
