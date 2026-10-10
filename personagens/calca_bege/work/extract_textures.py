import hashlib
import io
import json
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT/'export_config.json').read_text()) if (ROOT/'export_config.json').exists() else {}
SOURCE = Path(CONFIG.get('source', r'C:\Users\erons\Downloads\Meshy_AI_pleated_beige_trouser_1005054816_image-to-3d-texture.glb'))
DIFFUSE = CONFIG.get('diffuse', 'lowr_diff_008_a_uni')
PREFIX = CONFIG.get('texture_prefix', 'calca_bege')
OUT = ROOT / 'textures'
OUT.mkdir(exist_ok=True)
raw = SOURCE.read_bytes()
assert raw[:4] == b'glTF'
chunks = {}
offset = 12
while offset < len(raw):
    size, kind = struct.unpack_from('<II', raw, offset)
    chunks[kind] = raw[offset + 8:offset + 8 + size]
    offset += size + 8
document = json.loads(chunks[0x4E4F534A])
buffer = chunks[0x004E4942]
material = document['materials'][0]
refs = {
    'diffuse': material['pbrMetallicRoughness']['baseColorTexture']['index'],
    'normal': material['normalTexture']['index'],
    'metallic_roughness': material['pbrMetallicRoughness']['metallicRoughnessTexture']['index'],
}
report = {'source_sha256': hashlib.sha256(raw).hexdigest(), 'images': {}}
images = {}
for kind, texture_index in refs.items():
    entry = document['images'][document['textures'][texture_index]['source']]
    view = document['bufferViews'][entry['bufferView']]
    start = view.get('byteOffset', 0)
    blob = buffer[start:start + view['byteLength']]
    extension = '.jpg' if entry['mimeType'] == 'image/jpeg' else '.png'
    original_path = OUT / ('original_' + kind + extension)
    original_path.write_bytes(blob)
    images[kind] = Image.open(io.BytesIO(blob)).convert('RGBA')
    report['images'][kind] = {'sha256': hashlib.sha256(blob).hexdigest(), 'size': images[kind].size}

# Pillow PNG/JPEG and DDS use the same top-to-bottom pixel order. Sollumz
# handles the GTA UV V conversion; flipping pixels here would flip them twice.
images['diffuse'].save(OUT / (DIFFUSE+'.dds'), pixel_format='DXT5')
normal = np.asarray(images['normal']).copy()
normal[:, :, 1] = 255 - normal[:, :, 1]  # glTF OpenGL to GTA DirectX normal.
Image.fromarray(normal).save(OUT / (PREFIX+'_normal.dds'), pixel_format='DXT5')
mr = np.asarray(images['metallic_roughness']).astype(np.float32) / 255
# GTA ped.sps uses a specular texture, rather than the glTF metallic/roughness
# packing. Retain its spatial detail and keep cloth matte, with a leather belt.
reflectance = (.06 + .42 * (1 - mr[:, :, 1]) ** 2 + .08 * mr[:, :, 2]).clip(0, 1)
spec = np.zeros(mr.shape, dtype=np.uint8)
spec[:, :, :3] = (reflectance[:, :, None] * 255).astype(np.uint8)
Image.fromarray(spec).save(OUT / (PREFIX+'_spec.dds'), pixel_format='DXT5')
decoded = np.asarray(Image.open(OUT / (DIFFUSE+'.dds')).convert('RGB'), dtype=np.int16)
original = np.asarray(images['diffuse'].convert('RGB'), dtype=np.int16)
report['dds_diffuse_mean_absolute_error'] = float(np.abs(decoded - original).mean())
report['dds_diffuse_flipped_error'] = float(np.abs(decoded - original[::-1]).mean())
assert report['dds_diffuse_mean_absolute_error'] < report['dds_diffuse_flipped_error']
(OUT / 'texture_validation.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
