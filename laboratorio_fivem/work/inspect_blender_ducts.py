import bpy
import numpy as np

for name in ('CEILING_DUCT_MAIN_00', 'DUCT_MAIN_BACK_SEG_00', 'CEILING_DUCT_REAR_JOIN'):
    obj = bpy.data.objects[name]
    print('DUCT_OBJECT', obj.name, obj.type, [material.name for material in obj.data.materials],
          'dimensions', tuple(round(v, 3) for v in obj.dimensions),
          'center', tuple(round(v, 3) for v in obj.matrix_world.translation),
          'uvs', list(obj.data.uv_layers), flush=True)
    for layer in obj.data.uv_layers:
        data = np.asarray([loop.uv[:] for loop in layer.data])
        print('UV_RANGE', obj.name, layer.name, data.min(0), data.max(0), flush=True)
