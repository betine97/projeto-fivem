import bpy
from pathlib import Path
b=Path.cwd();bpy.ops.wm.open_mainfile(filepath=str(b/'warehouse_stage16_projeto_completo.blend'))
for o in bpy.data.objects:
 if o.name in ['CEILING_SLAB','LIGHT_SYSTEM_ROOT','PLACEHOLDER_LEFT_00_00_PLANT'] or o.name.startswith('RACK_LEFT_POST_00') or o.name.startswith('LIGHT_FIXTURE_00_00'):
  print(o.name,tuple(o.location),tuple(o.dimensions),o.type)
