"""Inspect the copied prone pose for a local hand-grip review."""
import bpy, json, sys
from pathlib import Path
from mathutils import Vector
HERE = Path(__file__).resolve().parent
PIPE = HERE.parent
DEPS = Path(r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
sys.path[:0] = [str(DEPS), str(DEPS.parent / 'sollumz')]
import addon_utils
addon_utils.enable('Sollumz', default_set=True)
bpy.ops.wm.open_mainfile(filepath=str(PIPE/'sources'/'deitado_ak.blend'))
rig = bpy.data.objects['GTA_Personagem_Rig']
rig.animation_data.action = bpy.data.actions['MIRA_deitado_ak']
bpy.context.scene.frame_set(1)
bpy.context.view_layer.update()
gun = bpy.data.objects['w_ar_assaultrifle']
inverse = gun.matrix_world.inverted()
hand = rig.pose.bones['SKEL_L_Hand']
report = {'gun_matrix': [list(r) for r in gun.matrix_world], 'hand_matrix': [list(r) for r in hand.matrix], 'bones': {}, 'meshes': {}}
for bone in rig.pose.bones:
    if bone.name.startswith(('SKEL_L_Hand','SKEL_L_Finger','SKEL_L_Forearm','SKEL_L_UpperArm','SKEL_L_Clavicle')):
        world = rig.matrix_world @ bone.head
        report['bones'][bone.name] = {'world': list(world), 'gun_local': list(inverse @ world), 'hand_local': list(hand.matrix.inverted() @ bone.head), 'matrix': [list(r) for r in bone.matrix], 'basis': [list(r) for r in bone.matrix_basis], 'rest_matrix': [list(r) for r in bone.bone.matrix_local], 'rest_head':list(bone.bone.head_local), 'rest_tail':list(bone.bone.tail_local)}
depsgraph = bpy.context.evaluated_depsgraph_get()
for obj in bpy.data.objects:
    if obj.type != 'MESH' or obj.hide_render:
        continue
    ev = obj.evaluated_get(depsgraph)
    mesh = ev.to_mesh()
    points = []
    for v in mesh.vertices:
        weighted = any(obj.vertex_groups[g.group].name.startswith(('SKEL_L_Hand','SKEL_L_Finger')) and g.weight > .15 for g in v.groups) if len(obj.vertex_groups) else False
        if weighted:
            points.append(list(inverse @ (ev.matrix_world @ v.co)))
    if points:
        report['meshes'][obj.name] = {'hand_points_gun_local': points}
    if obj in gun.children_recursive:
        region = [inverse @ (ev.matrix_world @ v.co) for v in mesh.vertices if .11 < (inverse @ (ev.matrix_world @ v.co)).x < .32]
        if region:
            report['meshes'][obj.name] = {'guard_bounds': [[min(p[i] for p in region), max(p[i] for p in region)] for i in range(3)], 'points_gun_local': [list(p) for p in region]}
    ev.to_mesh_clear()
(HERE/'contact_before.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in report.items() if k!='meshes'},indent=2))
print('MESHES', {k: len(v.get('hand_points_gun_local',v.get('points_gun_local',[]))) for k,v in report['meshes'].items()})
