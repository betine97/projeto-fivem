"""Render the supplied finishes at walking distance, without saving scene changes."""
import bpy
from pathlib import Path
from mathutils import Vector

root = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(root / 'plataforma_petroleo.blend'))
scene = bpy.context.scene
scene.frame_set(1)
data = bpy.data.cameras.new('Detalhe dos acabamentos')
camera = bpy.data.objects.new('Detalhe dos acabamentos', data)
scene.collection.objects.link(camera)
camera.location = (-16.5, -21.8, 22.45)
camera.rotation_euler = (Vector((-21, -7.5, 21.5)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
data.lens = 26
data.clip_end = 12000
scene.camera = camera
scene.render.threads_mode = 'FIXED'
scene.render.threads = 6
scene.cycles.samples = 40
scene.render.resolution_x = 1440
scene.render.resolution_y = 1000
scene.render.filepath = str(root / 'previews/04_Detalhe_das_texturas.png')
bpy.ops.render.render(write_still=True)
