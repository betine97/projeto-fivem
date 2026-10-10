import sys,json,xml.etree.ElementTree as ET
from pathlib import Path
root=Path(__file__).resolve().parent.parent
sys.path.insert(0,r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
from szio.gta5 import try_load_asset
for name in ['sertao.yft','sertao_hi.yft']:
 a=try_load_asset(root/'exports'/name);assert a
 print('ASSET',name,'fields',list(a.__dataclass_fields__))
 print('DRAWABLE_FIELDS',list(a.drawable.__dataclass_fields__))
 print('SKELETON',[b.name for b in a.drawable.skeleton.bones][-5:])
 assert all(any(b.name==n for b in a.drawable.skeleton.bones) for n in ['chassis','wheel_lf','wheel_rf','wheel_lr','wheel_rr','sertao_turret_yaw','sertao_turret_pitch','sertao_muzzle'])
 assert a.physics is not None
 # A valid skeleton alone does not prove that wheels are drawable.
 wheel_tag=next(b.tag for b in a.drawable.skeleton.bones if b.name=='wheel_lf')
 wheels=[c for c in a.physics.lod1.children if c.bone_tag==wheel_tag and c.drawable and c.drawable.models]
 assert wheels, 'Missing wheel drawable'
 for child in wheels:
  for models in child.drawable.models.values():
   for model in models:
    assert model.geometries
    for g in model.geometries:
     shader=a.drawable.shader_group.shaders[g.shader_index]
     print('WHEEL_SHADER',shader.name,shader.preset_filename)
     assert 'tire' in shader.preset_filename
 for models in a.drawable.models.values():
  for model in models:
   for g in model.geometries:
    uv=g.vertex_buffer['TexCoord0'] if 'TexCoord0' in g.vertex_buffer.dtype.names else None
    if uv is not None and len(uv)>12:
     assert (uv.max(axis=0)-uv.min(axis=0)).max()>0, 'Collapsed UVs'
metadata=ET.parse(root.parent/'server-data/resources/cidade_core/data/sertao_vehicles.meta')
assert metadata.findtext('.//modelName')=='sertao';assert metadata.findtext('.//handlingId')=='REBEL'
ET.parse(root.parent/'server-data/resources/cidade_core/data/sertao_variations.meta')
print('SERTAO structural validation PASS')
txd=try_load_asset(root/'exports/sertao.ytd')
print('TEXTURES',list(txd.textures))
assert 'MILITARY_OLIVE_BODY' in txd.textures or 'military_olive_body' in txd.textures
gun=try_load_asset(root/'exports/sertao_torre.ydr');assert gun is not None
assert len(gun.models)>0
print('REMODEL texture dictionary and separate turret PASS')
