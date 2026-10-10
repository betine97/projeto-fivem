import bpy
from pathlib import Path
W=Path(__file__).resolve().parent.parent
bpy.ops.wm.open_mainfile(filepath=str(W/'mansao_fivem_preparada.blend'))
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=16
s.render.resolution_x=1120;s.render.resolution_y=800;s.render.resolution_percentage=100
s.camera=bpy.data.objects['Camera sala pe direito duplo'];s.render.filepath=str(W/'interior_madeira_fivem.png')
bpy.ops.render.render(write_still=True)
print('WOOD_PREVIEW_OK',flush=True)
