"""Use actual exported YDD/YTD for the preview; leave production files untouched."""
import bpy, sys, json, addon_utils
from pathlib import Path
import numpy as np
from mathutils import Vector, Quaternion
from mathutils.kdtree import KDTree
sys.path[:0] = [r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps', r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\sollumz']
addon_utils.enable('Sollumz', default_set=True)
root = Path(__file__).resolve().parents[2]; out = Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(root/'PERSONAGEM_COM_CALCA_BEGE.blend'))
source = bpy.data.objects['CALCA_BEGE']
tree = KDTree(len(source.data.vertices))
for v in source.data.vertices: tree.insert(source.matrix_world @ v.co, v.index)
tree.balance()
uvs_by_vertex = {}
for loop in source.data.loops:
 uvs_by_vertex.setdefault(loop.vertex_index, []).append(tuple(source.data.uv_layers[0].data[loop.index].uv))
native = np.load(out/'native_pants_uv.npz')
positions = native['positions']; uvs = native['uvs']; uv_error = []; position_error = []; weight_error = []
source_weights = [{source.vertex_groups[g.group].name: g.weight for g in v.groups if g.weight > 0} for v in source.data.vertices]
for i in np.random.default_rng(12).choice(len(positions), size=min(3000, len(positions)), replace=False):
 candidates = tree.find_n(positions[i], 16)
 nearest_distance = candidates[0][2]; position_error.append(nearest_distance)
 candidate_ids = [index for co, index, dist in candidates if dist <= max(nearest_distance+1e-6, 1e-6)]
 uv = uvs[i].copy(); uv[1] = 1-uv[1]
 uv_error.append(min(np.linalg.norm(uv-np.array(v)) for index in candidate_ids for v in uvs_by_vertex[index]))
 native_weights = {str(native['bone_names'][bone]): float(w)/255 for bone, w in zip(native['bone_indices'][i], native['weights'][i]) if w > 0}
 weight_error.append(min(max(abs(native_weights.get(name, 0)-source_weights[index].get(name, 0)) for name in native_weights.keys() | source_weights[index].keys()) for index in candidate_ids))
report = {'samples': len(uv_error), 'max_position_error_metres': max(position_error), 'max_uv_error': float(max(uv_error)), 'mean_uv_error': float(np.mean(uv_error)), 'max_weight_quantization_error': max(weight_error), 'mean_weight_quantization_error': float(np.mean(weight_error))}
assert report['max_position_error_metres'] < 1e-5, report
assert report['max_uv_error'] < 2e-6, report
assert report['max_weight_quantization_error'] <= 2/255+1e-5, report
(out/'verification_uv.json').write_text(json.dumps(report, indent=2))
source.hide_render=True
source.hide_set(False)
before = set(bpy.data.objects)
bpy.ops.sollumz.import_assets(directory=str(root/'exports'), files=[{'name':'lowr_008_u.ydd'}], use_custom_settings=True, dwd_import_external_skeleton='SAVED', dwd_import_external_skeleton_saved_path=str(root/'source/mp_m_freemode_01.yft'))
imported = set(bpy.data.objects)-before
models = [o for o in imported if o.type == 'MESH']
assert models
for model in models:
 for mat in model.data.materials:
  if not mat or not mat.node_tree: continue
  for node in mat.node_tree.nodes:
   if node.type != 'TEX_IMAGE': continue
   texture_name = node.sollumz_texture_name
   if not texture_name and node.name == 'DiffuseSampler': texture_name = 'lowr_diff_008_a_uni'
   texture_path = out/(texture_name+'.dds')
   if texture_path.is_file():
    node.image = bpy.data.images.load(str(texture_path), check_existing=False)
    if node.name != 'DiffuseSampler': node.image.colorspace_settings.name = 'Non-Color'
 for modifier in model.modifiers:
  if modifier.type == 'ARMATURE':
   for pose in modifier.object.pose.bones: pose.matrix_basis.identity()
for rig in [o for o in bpy.data.objects if o.type == 'ARMATURE']:
 for side, angle in [('L', .4), ('R', -.4)]:
  bone = rig.pose.bones.get('SKEL_'+side+'_UpperArm')
  if bone:
   q = bone.bone.matrix_local.to_quaternion(); bone.rotation_mode='QUATERNION'; bone.rotation_quaternion=q.inverted() @ Quaternion((0, 1, 0), angle) @ q
sc = bpy.context.scene; sc.render.filepath = str(root/'preview_fivem_reimportado.png')
bpy.context.view_layer.update()
bpy.ops.render.render(write_still=True)
for rig in [o for o in bpy.data.objects if o.type == 'ARMATURE']:
 for name, angle in [('SKEL_L_Thigh', -.35), ('SKEL_L_Calf', .60), ('SKEL_R_Thigh', .20)]:
  bone = rig.pose.bones.get(name)
  if bone:
   q=bone.bone.matrix_local.to_quaternion(); bone.rotation_mode='QUATERNION'; bone.rotation_quaternion=q.inverted() @ Quaternion((1, 0, 0), angle) @ q
bpy.context.view_layer.update()
depsgraph=bpy.context.evaluated_depsgraph_get()
source_eval=source.evaluated_get(depsgraph); source_mesh=source_eval.to_mesh()
deformed_source=[source_eval.matrix_world @ v.co for v in source_mesh.vertices]
pose_errors=[]
for model in models:
 model_eval=model.evaluated_get(depsgraph); posed_mesh=model_eval.to_mesh()
 for i in np.random.default_rng(4).choice(len(model.data.vertices), size=min(3000, len(model.data.vertices)), replace=False):
  rest=model.matrix_world @ model.data.vertices[i].co
  nearest=tree.find_n(rest, 16); nearest_dist=nearest[0][2]
  candidate_ids=[index for co, index, dist in nearest if dist <= max(nearest_dist+1e-6, 1e-6)]
  posed=model_eval.matrix_world @ posed_mesh.vertices[i].co
  pose_errors.append(min((posed-deformed_source[index]).length for index in candidate_ids))
 model_eval.to_mesh_clear()
source_eval.to_mesh_clear()
report['posed_max_difference_metres']=max(pose_errors)
report['posed_mean_difference_metres']=float(np.mean(pose_errors))
report['posed_samples']=len(pose_errors)
assert report['posed_max_difference_metres'] < .005, report
(out/'verification_uv.json').write_text(json.dumps(report, indent=2))
sc.render.filepath=str(root/'preview_fivem_movimento.png')
camera_matrix=sc.camera.matrix_world.copy()
sc.camera.location=(3, -5, .03)
sc.camera.rotation_euler=(Vector((0, 0, -.09))-sc.camera.location).to_track_quat('-Z', 'Y').to_euler()
bpy.ops.render.render(write_still=True)
sc.camera.matrix_world=camera_matrix
for rig in [o for o in bpy.data.objects if o.type == 'ARMATURE']:
 for name in ['SKEL_L_Thigh', 'SKEL_L_Calf', 'SKEL_R_Thigh']:
  bone=rig.pose.bones.get(name)
  if bone: bone.matrix_basis.identity()
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(out/'CALCA_NATIVA_REIMPORTADA.blend'))
print('PANTS_UV_AND_REIMPORT_RENDER_VERIFIED', json.dumps(report))
