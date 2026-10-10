import bpy
import json
import runpy
from pathlib import Path
from mathutils import Vector

base = Path(__file__).resolve().parent
script = str(base / 'warehouse_stage6_completo.py')
runpy.run_path(script, run_name='__main__')
bpy.context.view_layer.update()


def bounds(obj):
    corners = [obj.matrix_world @ Vector(p) for p in obj.bound_box]
    return tuple(min(p[i] for p in corners) for i in range(3)), tuple(max(p[i] for p in corners) for i in range(3))


def check_scene():
    bpy.context.view_layer.update()
    vents = [o for o in bpy.data.objects if o.name.startswith('CEILING_VENT_') and o.name.endswith('_ROOT')]
    fans = [o for o in bpy.data.objects if o.name.startswith('SIDE_FAN_') and o.name.endswith('_ROOT')]
    lights = [o for o in bpy.data.objects if o.name.startswith('LIGHT_FIXTURE_') and o.type == 'LIGHT']
    assert len(vents) == 3 and len(fans) == len(lights) == 6
    assert len([o for o in bpy.data.objects if o.name.startswith('PLACEHOLDER_') and o.name.endswith('_CANOPY')]) == 18
    for obj in vents:
        assert ((obj.matrix_world.to_quaternion() @ Vector((0, 0, 1))) - Vector((0, 0, -1))).length < 1e-5
    for obj in fans:
        direction = Vector((1, 0, 0)) if 'LEFT' in obj.name else Vector((-1, 0, 0))
        assert ((obj.matrix_world.to_quaternion() @ Vector((0, 0, 1))) - direction).length < 1e-5
        assert abs(obj['nominal_diameter_m'] - 0.82) < 1e-6
    for obj in lights:
        assert ((obj.matrix_world.to_quaternion() @ Vector((0, 0, -1))) - Vector((0, 0, -1))).length < 1e-5
        assert obj.data.color[0] > 0.99 and obj.data.color[1] < 0.1
    overhead = [o for o in bpy.data.collections['ENV_CEILING_DUCTS'].objects if o.type in ('MESH', 'CURVE')]
    minimum = min(bounds(o)[0][2] for o in overhead)
    maximum = max(bounds(o)[1][2] for o in overhead)
    assert minimum > 2.40 and maximum < 3.60, (minimum, maximum)
    # New left-wall details below the door header must avoid its full framed width.
    for collection in ('ENV_WALL_SERVICES', 'ENV_SIDE_FANS'):
        for obj in bpy.data.collections[collection].objects:
            if obj.type not in ('MESH', 'CURVE'):
                continue
            low, high = bounds(obj)
            if high[0] < -3.55 and low[2] < 2.31:
                assert high[1] < -4.25 or low[1] > -2.95, ('side door overlap', obj.name, low, high)
    return {'ceiling_vents': 3, 'ceiling_vent_diameter_m': 0.90,
            'side_fans': 6, 'side_fan_diameter_m': 0.82,
            'overhead_min_height_m': round(minimum, 3),
            'overhead_max_height_m': round(maximum, 3),
            'pink_downward_area_lights': 6, 'placeholders': 18,
            'side_door_new_services_clear': True}


metrics = check_scene()
count = len(bpy.data.objects)
runpy.run_path(script, run_name='__main__')
metrics = check_scene()
assert len(bpy.data.objects) == count
metrics['rebuild_no_duplicates'] = True
(base / 'warehouse_stage6_validacao.json').write_text(json.dumps(metrics, indent=2), encoding='utf-8')

scene = bpy.context.scene
review = bpy.data.collections.new('STAGE6_REVIEW')
scene.collection.children.link(review)


def camera(name, location, target, lens=24, ortho=None):
    data = bpy.data.cameras.new(name)
    obj = bpy.data.objects.new(name, data)
    review.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()
    data.lens = lens
    data.clip_start = 0.05
    if ortho:
        data.type = 'ORTHO'
        data.ortho_scale = ortho
    return obj


overview = camera('STAGE6_OVERVIEW', (9, -16, 18), (0, 0.2, 1.4), ortho=17.5)
interior = camera('STAGE6_INTERIOR', (0.65, -5.35, 1.22), (-0.10, 1.1, 3.05), lens=22)
scene.camera = overview
scene.render.resolution_x = 1100
scene.render.resolution_y = 1100
scene.render.resolution_percentage = 100
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'MATERIAL'
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.display.shading.cavity_type = 'BOTH'
scene.render.use_compositing = False
roof = bpy.data.objects['CEILING_SLAB']
cutaway = [o for o in bpy.data.objects if o.name.startswith(('WALL_FRONT', 'FRONT_GATE_FRAME'))] + [roof]
for obj in cutaway:
    obj.hide_render = True
scene.render.filepath = str(base / 'warehouse_stage6_visao_geral.png')
bpy.ops.render.render(write_still=True)
for obj in cutaway:
    obj.hide_render = False

scene.camera = interior
scene.render.resolution_x = 1100
scene.render.resolution_y = 850
scene.render.filepath = str(base / 'warehouse_stage6_teto_estrutura.png')
bpy.ops.render.render(write_still=True)
scene.render.engine = 'CYCLES'
scene.cycles.samples = 32
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 6
scene.cycles.diffuse_bounces = 4
scene.render.use_compositing = True
scene.view_settings.view_transform = 'AgX'
scene.view_settings.exposure = 0.7
scene.render.filepath = str(base / 'warehouse_stage6_teto_rosa.png')

# Render the existing scene lighting; no extra inspection light is added.
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
bpy.ops.wm.save_as_mainfile(filepath=str(base / 'warehouse_stage6_validado.blend'))
bpy.ops.render.render(write_still=True)
print('STAGE6 VALIDATION PASSED: ducts, fans, wall services, headroom, side door and pink LEDs')
