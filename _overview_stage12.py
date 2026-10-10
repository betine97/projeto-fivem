import bpy
from pathlib import Path
base=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(base/'warehouse_stage12_plantas.blend'))
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=80;s.cycles.use_denoising=True
s.render.resolution_x=1400;s.render.resolution_y=1200;s.render.resolution_percentage=100
s.camera=bpy.data.objects['STAGE7_OVERVIEW']
for o in bpy.data.objects:
    if any(x in o.name.upper() for x in ('ROOF','WALL_FRONT','CEILING_SLAB')):o.hide_render=True
data=bpy.data.lights.new('PREVIEW_FILL','AREA');data.energy=1400;data.size=8
o=bpy.data.objects.new(data.name,data);s.collection.objects.link(o);o.location=(0,0,7)
s.render.filepath=str(base/'warehouse_stage12_visao_geral.png');bpy.ops.render.render(write_still=True)
