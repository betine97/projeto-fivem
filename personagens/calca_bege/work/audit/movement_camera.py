import bpy, addon_utils, sys
from pathlib import Path
from mathutils import Quaternion, Vector
sys.path[:0]=[r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps',r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\sollumz']
addon_utils.enable('Sollumz', default_set=True)
out=Path(__file__).resolve().parent; root=out.parents[1]
bpy.ops.wm.open_mainfile(filepath=str(out/'CALCA_NATIVA_REIMPORTADA.blend'))
for rig in [o for o in bpy.data.objects if o.type=='ARMATURE']:
 for name, angle in [('SKEL_L_Thigh',-.35),('SKEL_L_Calf',.60),('SKEL_R_Thigh',.20)]:
  bone=rig.pose.bones.get(name)
  if bone:
   q=bone.bone.matrix_local.to_quaternion(); bone.rotation_mode='QUATERNION'; bone.rotation_quaternion=q.inverted() @ Quaternion((1,0,0),angle) @ q
scene=bpy.context.scene
scene.camera.location=(3,-5,.03)
scene.camera.rotation_euler=(Vector((0,0,-.09))-scene.camera.location).to_track_quat('-Z','Y').to_euler()
scene.render.filepath=str(root/'preview_fivem_movimento.png')
bpy.context.view_layer.update()
bpy.ops.render.render(write_still=True)
