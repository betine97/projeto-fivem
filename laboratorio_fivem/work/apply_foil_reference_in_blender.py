"""Apply the supplied foil photo to the ceiling duct bodies in the .blend."""
import math
from pathlib import Path

import bpy

root = Path(__file__).resolve().parents[2]
image_path = root / 'laboratorio_fivem/textures/foil_ceiling_reference.png'
image = bpy.data.images.load(str(image_path), check_existing=True)
image.name = 'LAB_FOIL_REFERENCE_IMAGE'
image.colorspace_settings.name = 'sRGB'
image.pack()

material = bpy.data.materials.get('LAB_FOIL_PHOTO_CEILING')
if material is None:
    material = bpy.data.materials.new('LAB_FOIL_PHOTO_CEILING')
material.use_nodes = True
nodes = material.node_tree.nodes
nodes.clear()
links = material.node_tree.links
uv_node = nodes.new('ShaderNodeUVMap')
uv_node.uv_map = 'LAB_FOIL_UV'
uv_node.location = (-520, 0)
texture = nodes.new('ShaderNodeTexImage')
texture.image = image
texture.extension = 'REPEAT'
texture.interpolation = 'Linear'
texture.location = (-280, 0)
surface = nodes.new('ShaderNodeBsdfPrincipled')
surface.inputs['Metallic'].default_value = .82
surface.inputs['Roughness'].default_value = .19
surface.location = (0, 0)
output = nodes.new('ShaderNodeOutputMaterial')
output.location = (300, 0)
links.new(uv_node.outputs['UV'], texture.inputs['Vector'])
links.new(texture.outputs['Color'], surface.inputs['Base Color'])
links.new(surface.outputs['BSDF'], output.inputs['Surface'])

count = 0
for obj in bpy.data.objects:
    is_main = obj.name.startswith('CEILING_DUCT_MAIN_')
    is_back = obj.name.startswith('DUCT_MAIN_BACK_SEG_')
    if obj.type != 'MESH' or not (is_main or is_back):
        continue
    mesh = obj.data
    uv = mesh.uv_layers.get('LAB_FOIL_UV') or mesh.uv_layers.new(name='LAB_FOIL_UV')
    for polygon in mesh.polygons:
        values = []
        for loop_index in polygon.loop_indices:
            point = obj.matrix_world @ mesh.vertices[mesh.loops[loop_index].vertex_index].co
            if is_main:
                u = (point.y + 5.10) / 2.6
                v = (math.atan2(point.z - 3.158, point.x) / (2 * math.pi)) % 1
            else:
                u = (point.x + 2.60) / 2.6
                v = (math.atan2(point.z - 3.08, point.y - 5.69) / (2 * math.pi)) % 1
            values.append((u, v))
        if max(v for _, v in values) - min(v for _, v in values) > .5:
            values = [(u, v + 1 if v < .5 else v) for u, v in values]
        for loop_index, pair in zip(polygon.loop_indices, values):
            uv.data[loop_index].uv = pair
    mesh.materials.clear()
    mesh.materials.append(material)
    count += 1

assert count == 15, count
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(root / 'preparacao_fivem_stage18/warehouse_stage18_preparacao.blend'))
print('FOIL_BLENDER_OK', count, 'duct sections', image.size[:], flush=True)
