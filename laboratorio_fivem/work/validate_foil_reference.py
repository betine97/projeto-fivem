"""Read-back validation of the Blender foil source scene."""
import hashlib
from pathlib import Path
import bpy

root = Path(__file__).resolve().parents[2]
source = root / 'laboratorio_fivem/textures/foil_ceiling_reference.png'
image = bpy.data.images['LAB_FOIL_REFERENCE_IMAGE']
material = bpy.data.materials['LAB_FOIL_PHOTO_CEILING']
assert image.packed_file is not None
assert hashlib.sha256(image.packed_file.data).digest() == hashlib.sha256(source.read_bytes()).digest()
assert any(node.type == 'TEX_IMAGE' and node.image == image for node in material.node_tree.nodes)
objects = [obj for obj in bpy.data.objects if obj.type == 'MESH' and
           (obj.name.startswith('CEILING_DUCT_MAIN_') or obj.name.startswith('DUCT_MAIN_BACK_SEG_'))]
assert len(objects) == 15
assert all(obj.data.materials[0] == material and obj.data.uv_layers.get('LAB_FOIL_UV') for obj in objects)
print('FOIL_BLENDER_VALIDATED', len(objects), 'objects', image.size[:], flush=True)
