import bpy
from mathutils import Vector
from pathlib import Path

path = Path(r'C:\Users\erons\Downloads\Meshy_AI_cleanroom_containment_1004173529_image-to-3d-texture.glb')
bpy.ops.import_scene.gltf(filepath=str(path))
meshes = [obj for obj in bpy.data.objects if obj.type == 'MESH']
print('GLB_MESH_COUNT', len(meshes), flush=True)
for obj in sorted(meshes, key=lambda item: len(item.data.polygons), reverse=True)[:30]:
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    lo = [min(point[axis] for point in points) for axis in range(3)]
    hi = [max(point[axis] for point in points) for axis in range(3)]
    print('GLB_OBJECT', obj.name, 'verts', len(obj.data.vertices), 'faces', len(obj.data.polygons),
          'bounds', [tuple(round(value, 3) for value in pair) for pair in zip(lo, hi)],
          'materials', [material.name for material in obj.data.materials], flush=True)
for material in bpy.data.materials:
    if not material.users:
        continue
    print('GLB_MATERIAL', material.name, 'blend_method', getattr(material, 'surface_render_method', None),
          'nodes', [(node.type, getattr(node, 'image', None).name if getattr(node, 'image', None) else None)
                    for node in material.node_tree.nodes if node.type in {'TEX_IMAGE', 'BSDF_PRINCIPLED'}], flush=True)
    for node in material.node_tree.nodes:
        if node.type == 'BSDF_PRINCIPLED':
            print('GLB_BSDF', material.name, 'alpha', node.inputs['Alpha'].default_value,
                  'roughness', node.inputs['Roughness'].default_value,
                  'metallic', node.inputs['Metallic'].default_value, flush=True)
for image in bpy.data.images:
    if image.users:
        print('GLB_IMAGE', image.name, 'size', tuple(image.size), 'channels', image.channels, flush=True)
