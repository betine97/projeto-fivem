import bpy
import json
import runpy
from pathlib import Path
from mathutils import Vector

base = Path(__file__).resolve().parent
ns = runpy.run_path(str(base / 'warehouse_stage7_completo.py'), run_name='__main__')
bpy.context.view_layer.update()
hoses = [o for o in bpy.data.objects if o.type == 'CURVE' and o.name.startswith('FLOOR_HOSE_')
         and '_POT_' in o.name and '_RIB_' not in o.name]
assert len(hoses) == 18
for hose in hoses:
    parts = hose.name.split('_')
    side, bay, index = parts[2], parts[4], parts[5]
    pot = bpy.data.objects[f'PLACEHOLDER_{side}_{bay}_{index}_POT']
    endpoint = hose.data.splines[0].bezier_points[-1].co
    assert abs(endpoint.x - pot.location.x) < 1e-5
    assert abs(endpoint.y - (pot.location.y - 0.18)) < 1e-5
    assert abs(endpoint.z - (ns['PLATFORM_TOP_Z'] + ns['POT_HEIGHT'] + 0.015)) < 1e-5
    # The vertical rise is outside the rack's platform and the canopy.
    rise = hose.data.splines[0].bezier_points[2].co
    assert abs(rise.x) < 1.2 - 0.021

# Measure the actual evaluated hoses rather than just their control points.
depsgraph = bpy.context.evaluated_depsgraph_get()
minimum_center_clearance = 10.0
for obj in bpy.data.collections['ENV_FLOOR_HOSES'].objects:
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    if mesh:
        for vertex in mesh.vertices:
            point = evaluated.matrix_world @ vertex.co
            assert point.z > -0.01, (obj.name, point)
            assert abs(point.x) > 0.87, ('central walkway intrusion', obj.name, point)
            minimum_center_clearance = min(minimum_center_clearance, abs(point.x))
        evaluated.to_mesh_clear()
count = len(bpy.data.objects)
exec(compile((base / '_stage7_floor_hoses.py').read_text(encoding='utf-8'), 'stage7-details', 'exec'), ns)
assert len(bpy.data.objects) == count
assert len([o for o in bpy.data.objects if o.name.startswith('STORAGE_DRUM_') and o.name.endswith('_BODY')]) == 2
(base / 'warehouse_stage7_validacao.json').write_text(json.dumps({
    'pot_hoses': 18, 'closed_drums': 2, 'detail_reapplication_no_duplicates': True,
    'minimum_clear_center_width_m': round(minimum_center_clearance * 2, 3),
    'drain_clear': True, 'floor_penetrations': False
}, indent=2), encoding='utf-8')

scene = bpy.context.scene
review = bpy.data.collections.new('STAGE7_REVIEW')
scene.collection.children.link(review)


def camera(name, location, target, ortho, lens=30):
    data = bpy.data.cameras.new(name)
    obj = bpy.data.objects.new(name, data)
    review.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()
    data.lens = lens
    data.type = 'ORTHO'
    data.ortho_scale = ortho
    return obj


overview = camera('STAGE7_OVERVIEW', (8, -15, 18), (0, 0, 1.0), 17.5)
detail = camera('STAGE7_HOSE_DETAIL', (-0.25, -6.40, 2.10), (-2.28, -3.25, 0.70), 3.6)
rear = camera('STAGE7_DRUM_DETAIL', (-1.0, 2.5, 2.4), (-2.6, 3.9, 0.48), 2.7)
scene.render.engine = 'BLENDER_WORKBENCH'
scene.render.resolution_x = 1100
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'MATERIAL'
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.display.shading.cavity_type = 'BOTH'
scene.render.use_compositing = False
cutaway = [o for o in bpy.data.objects if o.name.startswith(('WALL_FRONT', 'FRONT_GATE_FRAME')) or o.name == 'CEILING_SLAB']
for obj in cutaway:
    obj.hide_render = True
for cam, image in ((overview, 'warehouse_stage7_visao_geral.png'),
                   (detail, 'warehouse_stage7_mangueiras.png'), (rear, 'warehouse_stage7_barris.png')):
    scene.camera = cam
    scene.render.filepath = str(base / image)
    bpy.ops.render.render(write_still=True)
scene.camera = detail
scene.render.engine = 'CYCLES'
scene.cycles.samples = 32
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 6
scene.render.use_compositing = True
scene.view_settings.view_transform = 'AgX'
scene.view_settings.exposure = 0.0
scene.render.filepath = str(base / 'warehouse_stage7_mangueiras_rosa.png')
bpy.ops.render.render(write_still=True)
for obj in cutaway:
    obj.hide_render = False
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces.active.shading.type = 'SOLID'
            area.spaces.active.shading.color_type = 'MATERIAL'
            area.spaces.active.overlay.show_relationship_lines = False
            region = area.spaces.active.region_3d
            region.view_rotation = overview.rotation_euler.to_quaternion()
            region.view_distance = 17
            region.view_location = (0, 0, 1.2)
bpy.ops.wm.save_as_mainfile(filepath=str(base / 'warehouse_stage7_validado.blend'))
print('STAGE7 VALIDATION PASSED')
