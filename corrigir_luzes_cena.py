import bpy
from mathutils import Matrix

# Correct only the six generated warehouse lights, without rebuilding geometry.
count = 0
for sx, x in enumerate((-2.20, 2.20)):
    for sy, y in enumerate((-3.80, 0.00, 3.80)):
        obj = bpy.data.objects.get(f"LIGHT_FIXTURE_{sx:02d}_{sy:02d}_AREA")
        if obj is None or obj.type != 'LIGHT' or obj.data.type != 'AREA':
            continue
        for constraint in list(obj.constraints):
            obj.constraints.remove(constraint)
        obj.parent = None
        obj.matrix_world = Matrix.Translation((x, y, 3.08 - 0.09))
        obj.data.shape = 'RECTANGLE'
        obj.data.size = 0.20
        obj.data.size_y = 1.05
        count += 1

for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces.active.overlay.show_relationship_lines = False

bpy.context.view_layer.update()
print(f"{count} warehouse AREA lights point vertically down (-Z world).")
