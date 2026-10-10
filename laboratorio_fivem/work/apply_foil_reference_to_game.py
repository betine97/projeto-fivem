"""Embed the user's foil reference in the existing ceiling duct drawable."""
import io
import sys
from pathlib import Path

sys.path[:0] = [
    r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps',
    r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\media_deps',
]
from PIL import Image
from szio.gta5 import AssetFormat, AssetTarget, AssetVersion, save_asset, try_load_asset
from szio.types import DataSource

root = Path(__file__).resolve().parents[2]
source = root / 'server-data/resources/cidade_laboratorio/stream/lab_ventilacao.ydr'
reference = root / 'laboratorio_fivem/textures/foil_ceiling_reference.png'
out = root / 'laboratorio_fivem/foil_reference_update'
out.mkdir(exist_ok=True)

asset = try_load_asset(source)
texture = asset.shader_group.embedded_textures['lab_foil_color']
image = Image.open(reference).convert('RGBA')
dds = io.BytesIO()
# The uncompressed DDS retains the exact 1254x1254 pixels of the reference.
image.save(dds, format='DDS')
texture.width, texture.height = image.size
texture.data = DataSource.create(dds.getvalue())
save_asset(asset, (AssetTarget(AssetFormat.NATIVE, AssetVersion.GEN8),),
           out, 'lab_ventilacao')

check = try_load_asset(out / 'lab_ventilacao.ydr')
foil = check.shader_group.embedded_textures['lab_foil_color']
assert (foil.width, foil.height) == image.size
assert len(check.models[0][0].geometries) == len(asset.models[0][0].geometries)
decoded = Image.open(io.BytesIO(foil.data.read_bytes())).convert('RGBA')
assert decoded.size == image.size
assert decoded.tobytes() == image.tobytes(), 'Native texture differs from supplied image'
print('FOIL_GAME_OK', image.size, 'geometries',
      len(check.models[0][0].geometries), flush=True)
