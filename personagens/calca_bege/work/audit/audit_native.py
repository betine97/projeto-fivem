from pathlib import Path
import sys, json, io, struct
sys.path[:0] = [r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps', str(Path('laboratorio_fivem/work/pydeps').resolve())]
import numpy as np
from PIL import Image
from szio.gta5 import try_load_asset
from szio.dds import DdsFile

out = Path(__file__).resolve().parent
src = Path('personagens/traje_guarda/textures/guard_diff.png')
native = try_load_asset('personagens/traje_guarda/exports/guardalab.ydd')
txd = try_load_asset('personagens/traje_guarda/exports/guardalab.ytd')
source_pixels = np.array(Image.open(src).convert('RGBA'))
native_pixels = np.array(Image.open(io.BytesIO(txd.textures['uppr_diff_000_a_uni'].data.read_bytes())).convert('RGBA'))
source_rgb = source_pixels[:, :, :3]
native_rgb = native_pixels[:, :, :3]
report = {
 'original_diffuse_rgb_mean': source_rgb.mean((0, 1)).tolist(),
 'native_direct_mae_255': float(np.abs(native_rgb.astype(float)-source_rgb.astype(float)).mean()),
 'native_against_vertically_flipped_source_mae_255': float(np.abs(native_rgb.astype(float)-source_rgb[::-1].astype(float)).mean()),
 'pixel_100_100': {'source': source_pixels[100, 100].tolist(), 'native': native_pixels[100, 100].tolist()},
 'components': {},
}
for name, drawable in native.drawables.items():
 shaders = []
 for shader in drawable.shader_group.shaders:
  textures = {p.name: p.value for p in shader.parameters if 'sampler' in p.name and isinstance(p.value, str)}
  shaders.append({'preset': shader.preset_filename, 'textures': textures, 'missing': [t for t in textures.values() if t not in txd.textures]})
 models = drawable.models
 high = next((rows for lod, rows in models.items() if 'HIGH' == lod.name), [])
 if not high: high = next(iter(models.values()), [])
 geos = [g for m in high for g in m.geometries]
 colors = {}
 for channel in ['Colour0', 'Colour1']:
  rows = [g.vertex_buffer[channel] for g in geos if channel in g.vertex_buffer.dtype.names]
  if rows: colors[channel] = np.unique(np.concatenate(rows), axis=0).tolist()
 report['components'][name] = {'shaders': shaders, 'colors': colors, 'high_triangles': sum(len(g.index_buffer)//3 for g in geos)}
 if name == 'hash_7CEAC270':
  rows = [g.vertex_buffer for g in geos]
  np.savez_compressed(out/'native_guard_uv.npz', positions=np.concatenate([r['Position'] for r in rows]), uvs=np.concatenate([r['TexCoord0'] for r in rows]))
for key in ['uppr_diff_000_a_uni', 'uppr_normal_000', 'uppr_spec_000']:
 tex = txd.textures[key]
 raw = tex.data.read_bytes()
 dds = DdsFile.from_buffer(bytearray(raw))
 report[key] = {'size': [dds.width, dds.height], 'compressed': dds.is_compressed, 'mips': int(dds.header.dwMipMapCount), 'fourcc': dds.header.ddspf.dwFourCC.decode(errors='replace')}
(out/'audit_native.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
