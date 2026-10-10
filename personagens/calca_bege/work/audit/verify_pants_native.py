"""Read-only post-export check. Run only after the main exporter has completed."""
from pathlib import Path
import sys, io, struct, json
sys.path[:0] = [r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps', str(Path('laboratorio_fivem/work/pydeps').resolve())]
import numpy as np
from PIL import Image
from szio.gta5 import try_load_asset
from szio.dds import DdsFile

root = Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[2]
config = json.loads((root/'export_config.json').read_text()) if (root/'export_config.json').exists() else {}
out = root/'work/audit';out.mkdir(exist_ok=True)
src = Path(config.get('source', r'C:\Users\erons\Downloads\Meshy_AI_pleated_beige_trouser_1005054816_image-to-3d-texture.glb'))
component = config.get('component', 'lowr_008_u')
diffname = config.get('diffuse', 'lowr_diff_008_a_uni')
raw = src.read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]
gltf = json.loads(raw[20:20+n]); binary = raw[28+n:]
material = gltf['materials'][0]
def source_image(texture_index):
 image = gltf['images'][gltf['textures'][texture_index]['source']]
 view = gltf['bufferViews'][image['bufferView']]
 start = view.get('byteOffset', 0)
 return Image.open(io.BytesIO(binary[start:start+view['byteLength']])).convert('RGBA')
diffuse = np.array(source_image(material['pbrMetallicRoughness']['baseColorTexture']['index']))
normal = np.array(source_image(material['normalTexture']['index']))
ydd = try_load_asset(root/'exports'/(component+'.ydd'))
ytd = try_load_asset(root/'exports'/(diffname+'.ytd'))
assert len(ydd.drawables) == 1
drawable = next(iter(ydd.drawables.values()))
external_skeleton = try_load_asset(root/'source/mp_m_freemode_01.yft').drawable.skeleton
bone_names = [bone.name for bone in external_skeleton.bones]
textures = dict(drawable.shader_group.embedded_textures)
textures.update(ytd.textures)
report = {'textures': {}, 'shaders': [], 'lods': {}}
primary_refs = None
for shader in drawable.shader_group.shaders:
 refs = {p.name: p.value for p in shader.parameters if isinstance(p.value, str) and 'sampler' in p.name}
 missing = [value for value in refs.values() if value not in textures]
 report['shaders'].append({'preset': shader.preset_filename, 'texture_refs': refs, 'missing': missing})
 assert not missing, missing
 if 'diffusesampler' in refs and refs['diffusesampler'] == diffname: primary_refs = refs
for name, tex in textures.items():
 content = tex.data.read_bytes()
 dds = DdsFile.from_buffer(bytearray(content))
 (out/(name+'.dds')).write_bytes(content)
 report['textures'][name] = {'width': dds.width, 'height': dds.height, 'compressed': dds.is_compressed, 'fourcc': dds.header.ddspf.dwFourCC.decode(errors='replace'), 'mip_count': int(dds.header.dwMipMapCount), 'embedded_in_ydd': name in drawable.shader_group.embedded_textures, 'in_ytd': name in ytd.textures}
 assert dds.width > 0 and dds.height > 0 and dds.width & (dds.width-1) == 0 and dds.height & (dds.height-1) == 0
assert diffname in ytd.textures
assert primary_refs is not None
normal_name = primary_refs['bumpsampler']; spec_name = primary_refs['specsampler']
assert normal_name in drawable.shader_group.embedded_textures
assert spec_name in drawable.shader_group.embedded_textures
def pixels(name):
 return np.array(Image.open(io.BytesIO(textures[name].data.read_bytes())).convert('RGBA'))
native_diff = pixels(diffname)
assert native_diff.shape == diffuse.shape, (native_diff.shape, diffuse.shape)
color_error = np.abs(native_diff[:, :, :3].astype(float)-diffuse[:, :, :3].astype(float))
report['diffuse'] = {'source_rgb_mean': diffuse[:, :, :3].mean((0, 1)).tolist(), 'native_rgb_mean': native_diff[:, :, :3].mean((0, 1)).tolist(), 'direct_mae_255': float(color_error.mean()), 'flipped_mae_255': float(np.abs(native_diff[:, :, :3].astype(float)-diffuse[::-1, :, :3].astype(float)).mean()), 'max_error_255': int(color_error.max())}
assert report['diffuse']['direct_mae_255'] < 8, report['diffuse']
assert report['diffuse']['direct_mae_255'] < report['diffuse']['flipped_mae_255'], report['diffuse']
dx_normal = normal.copy(); dx_normal[:, :, 1] = 255-dx_normal[:, :, 1]
native_normal = pixels(normal_name)
assert native_normal.shape == dx_normal.shape
report['normal'] = {'mae_against_source_green_inverted': float(np.abs(native_normal[:, :, :3].astype(float)-dx_normal[:, :, :3].astype(float)).mean()), 'mae_against_source_without_green_inverted': float(np.abs(native_normal[:, :, :3].astype(float)-normal[:, :, :3].astype(float)).mean())}
assert report['normal']['mae_against_source_green_inverted'] < 8, report['normal']
positions = []; uvs = []; native_weights = []; native_bone_indices = []
for lod, models in drawable.models.items():
 geometries = [g for model in models for g in model.geometries]
 colors = {}
 for channel, expected in [('Colour0', [255, 128, 0, 255]), ('Colour1', [0, 0, 0, 0])]:
  entries = [g.vertex_buffer[channel] for g in geometries if channel in g.vertex_buffer.dtype.names]
  assert entries, (lod, channel)
  unique = np.unique(np.concatenate(entries), axis=0)
  colors[channel] = unique.tolist()
  assert len(unique) == 1 and np.max(np.abs(unique[0].astype(int)-expected)) <= 1, (lod.name, channel, colors[channel])
 geometry_info = []
 for g in geometries:
  buffer = g.vertex_buffer
  weights = buffer['BlendWeights'].astype(int)
  blend_indices = buffer['BlendIndices'].astype(int)
  assert np.all(weights.sum(axis=1) == 255), lod.name
  assert np.all(blend_indices[weights > 0] < len(g.bone_ids)), (lod.name, len(g.bone_ids))
  assert np.all(np.asarray(g.bone_ids) < len(bone_names)), (lod.name, g.bone_ids)
  assert np.count_nonzero(weights, axis=1).max() <= 4
  assert len(buffer) <= 65535 and int(g.index_buffer.max()) < len(buffer) and int(g.index_buffer.max()) <= 65535
  geometry_info.append({'vertices': len(buffer), 'max_vertex_index': int(g.index_buffer.max()), 'bone_palette_count': len(g.bone_ids), 'weight_sum_min': int(weights.sum(axis=1).min()), 'weight_sum_max': int(weights.sum(axis=1).max()), 'max_influences': int(np.count_nonzero(weights, axis=1).max())})
 report['lods'][lod.name] = {'vertices': sum(len(g.vertex_buffer) for g in geometries), 'triangles': sum(len(g.index_buffer)//3 for g in geometries), 'colors': colors, 'geometries': geometry_info}
 if lod.name == 'HIGH':
  for g in geometries:
   assert 'TexCoord0' in g.vertex_buffer.dtype.names
   positions.append(g.vertex_buffer['Position']); uvs.append(g.vertex_buffer['TexCoord0'])
   native_weights.append(g.vertex_buffer['BlendWeights'])
   native_bone_indices.append(np.asarray(g.bone_ids)[g.vertex_buffer['BlendIndices']])
assert positions
np.savez_compressed(out/'native_pants_uv.npz', positions=np.concatenate(positions), uvs=np.concatenate(uvs), weights=np.concatenate(native_weights), bone_indices=np.concatenate(native_bone_indices), bone_names=np.array(bone_names))
(out/'verification_native.json').write_text(json.dumps(report, indent=2))
print('PANTS_NATIVE_VERIFIED', json.dumps(report, indent=2))
