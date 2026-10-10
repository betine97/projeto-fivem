import bpy, runpy, math
from pathlib import Path
from mathutils import Vector
base = Path(__file__).resolve().parent
runpy.run_path(str(base / "warehouse_stage4_completo.py"))
scene = bpy.context.scene
bpy.context.view_layer.update()
lights = [o for o in bpy.data.objects if o.name.startswith("LIGHT_FIXTURE_") and o.type == 'LIGHT']
assert len(lights) == 6, len(lights)
for o in lights:
    direction = o.matrix_world.to_quaternion() @ Vector((0,0,-1))
    assert (direction - Vector((0,0,-1))).length < 1e-6, o.name
    assert abs(abs(o.location.x) - 2.475) < 1e-6
assert len([o for o in bpy.data.objects if o.name.startswith("RACK_") and "_TRAY_" in o.name]) == 6
# Run again: rebuilding must not duplicate the structures or lights.
count = len(bpy.data.objects)
runpy.run_path(str(base / "warehouse_stage4_completo.py"))
assert len(bpy.data.objects) == count
cam_data = bpy.data.cameras.new("STAGE4_REVIEW_CAMERA")
cam = bpy.data.objects.new("STAGE4_REVIEW_CAMERA", cam_data)
scene.collection.objects.link(cam)
cam.location = (0, -16, 19)
cam.rotation_euler = (Vector((0,0,1.0)) - cam.location).to_track_quat('-Z','Y').to_euler()
cam_data.type = 'ORTHO'
cam_data.ortho_scale = 17
scene.camera = cam
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'MATERIAL'
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.render.resolution_x = 1000
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.filepath = str(base / "warehouse_stage4_preview.png")
bpy.ops.wm.save_as_mainfile(filepath=str(base / "warehouse_stage4_validado.blend"))
bpy.ops.render.render(write_still=True)
print("STAGE4 CHECKS PASSED: 2 racks, 6 bays, 6 downward lights, rebuild stable")
