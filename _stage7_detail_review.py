import bpy
from pathlib import Path
from mathutils import Vector

base = Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(base / 'warehouse_stage7_validado.blend'))
scene = bpy.context.scene
cutaway = [o for o in bpy.data.objects if o.name.startswith(('WALL_FRONT', 'FRONT_GATE_FRAME')) or o.name == 'CEILING_SLAB']
for obj in cutaway:
    obj.hide_render = True
scene.render.engine = 'BLENDER_WORKBENCH'
scene.render.use_compositing = False
for name, location, target, scale, filename in (
    ('STAGE7_HOSE_DETAIL', (-0.25,-6.4,2.1), (-2.28,-3.25,0.70), 3.6, 'warehouse_stage7_mangueiras.png'),
    ('STAGE7_DRUM_DETAIL', (-1,2.5,2.4), (-2.6,3.9,0.48), 2.7, 'warehouse_stage7_barris.png'),
):
    cam = bpy.data.objects[name]
    cam.location = location
    cam.rotation_euler = (Vector(target) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.ortho_scale = scale
    scene.camera = cam
    scene.render.filepath = str(base / filename)
    bpy.ops.render.render(write_still=True)
scene.camera = bpy.data.objects['STAGE7_HOSE_DETAIL']
scene.render.engine = 'CYCLES'
scene.render.use_compositing = True
scene.render.filepath = str(base / 'warehouse_stage7_mangueiras_rosa.png')
bpy.ops.render.render(write_still=True)
for obj in cutaway:
    obj.hide_render = False
bpy.ops.wm.save_as_mainfile(filepath=str(base / 'warehouse_stage7_validado.blend'))
