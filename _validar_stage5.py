import bpy
import json
import sys
from pathlib import Path
from mathutils import Vector

BASE = Path(__file__).resolve().parent
SOURCE = (BASE / 'warehouse_stage5_completo.py').read_text(encoding='utf-8')
finalize = '--finalize' in sys.argv
metrics = json.loads((BASE / 'warehouse_stage5_validacao.json').read_text()) if finalize else {}


def bounds(obj):
    corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    return tuple(min(c[i] for c in corners) for i in range(3)), tuple(max(c[i] for c in corners) for i in range(3))


def verify(count):
    bpy.context.view_layer.update()
    canopies = [o for o in bpy.data.objects if o.name.startswith('PLACEHOLDER_') and o.name.endswith('_CANOPY')]
    pots = [o for o in bpy.data.objects if o.name.startswith('PLACEHOLDER_') and o.name.endswith('_POT')]
    lights = [o for o in bpy.data.objects if o.name.startswith('LIGHT_FIXTURE_') and o.type == 'LIGHT']
    fans = [o for o in bpy.data.objects if o.name.startswith('SIDE_FAN_') and o.name.endswith('_ROOT')]
    assert len(canopies) == len(pots) == 6 * count
    assert len(lights) == len(fans) == 6
    assert len([o for o in bpy.data.objects if o.name.startswith('LIGHT_FIXTURE_') and '_LED_' in o.name]) == 12
    clearance = 100
    for light in lights:
        direction = light.matrix_world.to_quaternion() @ Vector((0, 0, -1))
        assert (direction - Vector((0, 0, -1))).length < 1e-6
        side, bay = light.name.split('_')[2:4]
        prefix = f"PLACEHOLDER_{'LEFT' if side == '00' else 'RIGHT'}_{bay}_"
        group = [o for o in canopies if o.name.startswith(prefix)]
        assert len(group) == count
        centroid = sum((o.matrix_world.translation for o in group), Vector()) / count
        assert abs(centroid.x - light.location.x) < 1e-5
        assert abs(centroid.y - light.location.y) < 1e-5
        xmin, xmax = light.location.x - 1.275, light.location.x + 1.275
        for canopy in group:
            low, high = bounds(canopy)
            assert low[0] > xmin + 0.055 and high[0] < xmax - 0.055
            assert low[1] > light.location.y - 7.4 / 6 + 0.055
            assert high[1] < light.location.y + 7.4 / 6 - 0.055
            clearance = min(clearance, light.location.z - high[2])
            assert light.location.z - high[2] > 0.25
        for i, a in enumerate(group):
            for b in group[i + 1:]:
                alo, ahi = bounds(a)
                blo, bhi = bounds(b)
                assert any(ahi[k] < blo[k] or bhi[k] < alo[k] for k in (0, 1))
    for fan in fans:
        direction = fan.matrix_world.to_quaternion() @ Vector((0, 0, 1))
        expected = Vector((1, 0, 0)) if 'LEFT' in fan.name else Vector((-1, 0, 0))
        assert (direction - expected).length < 1e-6
    tech = bpy.data.collections['ENV_TECHNICAL_PROPS']
    for obj in tech.objects:
        low, high = bounds(obj)
        assert low[1] > 4.20, (obj.name, low)
        assert high[0] < -0.70 or low[0] > 0.70, ('rear door access', obj.name)
    metrics[str(count)] = {'canopies': len(canopies), 'side_fans': len(fans),
                           'downward_lights': len(lights), 'minimum_canopy_to_area_m': round(clearance, 4),
                           'corridor_width_m': 2.40, 'rear_door_access': 'clear'}


# Construct both layouts in Blender, then restore the delivered default.
for count in ((3,) if finalize else (4, 3)):
    code = SOURCE.replace('PLACEHOLDERS_PER_MODULE = 3', f'PLACEHOLDERS_PER_MODULE = {count}')
    exec(compile(code, 'warehouse_stage5_completo.py', 'exec'), {'__name__': '__main__'})
    verify(count)
if not finalize:
    count_before = len(bpy.data.objects)
    exec(compile(SOURCE, 'warehouse_stage5_completo.py', 'exec'), {'__name__': '__main__'})
    verify(3)
    assert count_before == len(bpy.data.objects), 'Rebuild duplicated objects'
metrics['rebuild'] = 'no duplicates'
(BASE / 'warehouse_stage5_validacao.json').write_text(json.dumps(metrics, indent=2), encoding='utf-8')

scene = bpy.context.scene
review = bpy.data.collections.new('STAGE5_REVIEW')
scene.collection.children.link(review)
cam_data = bpy.data.cameras.new('STAGE5_REVIEW_CAMERA')
cam = bpy.data.objects.new('STAGE5_REVIEW_CAMERA', cam_data)
review.objects.link(cam)
cam.location = (0, -16, 19)
cam.rotation_euler = (Vector((0, 0, 1.0)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
cam_data.type = 'ORTHO'
cam_data.ortho_scale = 15.5
scene.camera = cam
scene.render.resolution_x = 1100
scene.render.resolution_y = 1100
scene.render.resolution_percentage = 100
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.studiolight_rotate_z = 0.5
scene.display.shading.color_type = 'MATERIAL'
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.display.shading.cavity_type = 'BOTH'
scene.display.shading.background_type = 'WORLD'
scene.world.color = (0.075, 0.075, 0.075)

# Cutaway only while rendering: the complete front wall stays in the saved scene.
cutaway = [o for o in bpy.data.objects if o.name.startswith(('WALL_FRONT', 'FRONT_GATE_FRAME'))]
for obj in cutaway:
    obj.hide_render = True
scene.render.filepath = str(BASE / 'warehouse_stage5_preview.png')
bpy.ops.render.render(write_still=True)

# Detail view proves the transverse light, simple canopies, pots and fan orientation.
cam.location = (-0.15, -7.50, 4.50)
cam.rotation_euler = (Vector((-2.475, -3.266667, 1.1)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
cam_data.ortho_scale = 4.1
scene.render.filepath = str(BASE / 'warehouse_stage5_modulo.png')
bpy.ops.render.render(write_still=True)
for obj in cutaway:
    obj.hide_render = False
cam.location = (0, -16, 19)
cam.rotation_euler = (Vector((0, 0, 1.0)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
cam_data.ortho_scale = 15.5
for engine in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
    try:
        scene.render.engine = engine
        break
    except TypeError:
        continue
scene.render.filepath = str(BASE / 'warehouse_stage5_render.png')
# Set a useful solid viewport for the delivered Blender project.
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces.active.shading.type = 'SOLID'
            area.spaces.active.shading.color_type = 'MATERIAL'
            area.spaces.active.overlay.show_relationship_lines = False
            region = area.spaces.active.region_3d
            region.view_rotation = cam.rotation_euler.to_quaternion()
            region.view_distance = 17
            region.view_location = (0, 0, 1)
bpy.ops.wm.save_as_mainfile(filepath=str(BASE / 'warehouse_stage5_validado.blend'))
print('STAGE5 VALIDATED: three and four placeholders per bay; downward lights; inward fans; clear door; stable rebuild')
