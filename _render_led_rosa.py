import bpy
import runpy
import json
from pathlib import Path
from mathutils import Vector

base = Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(base / 'warehouse_stage5_validado.blend'))
before = len(bpy.data.objects)
runpy.run_path(str(base / 'aplicar_luz_rosa.py'), run_name='__main__')
assert len(bpy.data.objects) == before + 12
scene = bpy.context.scene
lights = [o for o in bpy.data.objects if o.type == 'LIGHT' and o.name.startswith('LIGHT_FIXTURE_')]
assert len(lights) == 6
for light in lights:
    assert (light.matrix_world.to_quaternion() @ Vector((0, 0, -1)) - Vector((0, 0, -1))).length < 1e-6
    assert abs(light.data.color[0] - 1.0) < 1e-6 and light.data.color[1] < 0.1
tree = scene.compositing_node_group if hasattr(scene, 'compositing_node_group') else scene.node_tree
assert tree.nodes.get('WAREHOUSE_LED_PINK_GLOW')
# Apply twice: no duplicate compositing nodes or geometry.
runpy.run_path(str(base / 'aplicar_luz_rosa.py'), run_name='__main__')
assert len([n for n in tree.nodes if n.name.startswith('WAREHOUSE_LED_PINK_GLOW')]) == 1
assert len(bpy.data.objects) == before + 12

scene.render.engine = 'CYCLES'
scene.cycles.samples = 32
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 6
scene.cycles.diffuse_bounces = 4
scene.cycles.glossy_bounces = 3
scene.render.resolution_x = 850
scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.view_settings.view_transform = 'AgX'
scene.view_settings.exposure = 0.0
scene.render.filepath = str(base / 'warehouse_stage5_luz_rosa_preview.png')
cutaway = [o for o in bpy.data.objects if o.name.startswith(('WALL_FRONT', 'FRONT_GATE_FRAME'))]
for obj in cutaway:
    obj.hide_render = True
bpy.ops.render.render(write_still=True)
for obj in cutaway:
    obj.hide_render = False
scene.cycles.samples = 64
bpy.ops.wm.save_as_mainfile(filepath=str(base / 'warehouse_stage5_luz_rosa.blend'))
(base / 'warehouse_led_rosa_validacao.json').write_text(json.dumps({
    'area_lights': len(lights), 'direction': 'world -Z', 'added_diffuser_edges': 12,
    'pink_emission': True, 'fog_glow_nodes': 1, 'repeat_application': 'no duplicates'
}, indent=2), encoding='utf-8')
print('PINK LED VALIDATION PASSED')
