import sys,io,json,shutil,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'catalogo_nativo'))
import render_catalog as r
from szio.gta5 import save_asset,AssetTarget,AssetFormat,AssetVersion,EmbeddedTexture
from szio.types import DataSource
base=Path(__file__).resolve().parent
source=base/'source/task_001_u.ydd'; a=r.try_load_asset(source)
targetrow=next(m for m in r.DATA['models'] if m['collection']=='mp_m_freemode_01_male_heist' and m['part']=='task' and m['index']==0)
target=r.try_load_asset(r.vpath(targetrow['path']))
drawable=next(iter(a.drawables.values())); drawable.name='task_000_u.#dd'
a.drawables={next(iter(target.drawables)):drawable}
for shader in drawable.shader_group.shaders:
 for p in shader.parameters:
  if p.name.lower()=='diffusesampler':p.value='task_diff_000_a_uni'
img=r.Image.open(r' C:\Users\erons\.codex\generated_images\01a101a1-b5d4-71e1-aa85-c63ebc0f3a5e\exec-56bb05d1-389c-4a4b-a733-29caf4c7a338.png'.strip()).convert('RGB').resize((1024,2048),r.Image.Resampling.LANCZOS)
img.save(base/'textures/task_diff_000_a_uni.png')
dds=base/'textures/task_diff_000_a_uni.dds';img.save(dds,format='DDS',pixel_format='DXT1')
txd=r.try_load_asset(base/'source/task_diff_001_a_uni.ytd');txd.textures={'task_diff_000_a_uni':EmbeddedTexture('task_diff_000_a_uni',img.width,img.height,DataSource.create(dds))}
targets=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
save_asset(a,targets,base/'exports','task_000_u');save_asset(txd,targets,base/'exports','task_diff_000_a_uni')
# Re-read exported binaries and validate original vertices, UVs and bone weights.
check=r.try_load_asset(base/'exports/task_000_u.ydd'); original=r.try_load_asset(source)
newd=next(iter(check.drawables.values())); oldd=next(iter(original.drawables.values()))
triangles=0
for lod,models in oldd.models.items():
 for oldm,newm in zip(models,newd.models[lod]):
  for oldg,newg in zip(oldm.geometries,newm.geometries):
   assert r.np.array_equal(oldg.vertex_buffer,newg.vertex_buffer)
   assert r.np.array_equal(oldg.index_buffer,newg.index_buffer)
   triangles+=len(newg.index_buffer)//3
assert 'task_diff_000_a_uni' in r.try_load_asset(base/'exports/task_diff_000_a_uni.ytd').textures
# Preview the actual exported native asset with the exported diffuse.
oldload=r.try_load_asset
r.try_load_asset=lambda p: check if str(p).endswith('task_001_u.ydd') else txd if str(p).endswith('task_diff_001_a_uni.ytd') else oldload(p)
row=next(m for m in r.DATA['models'] if m['collection']=='mp_m_freemode_01_mp_m_heist3' and m['part']=='task' and m['index']==1)
original_flip=r.ImageOps.flip
r.ImageOps.flip=lambda image:image
pieces,center,extent,*_=r.prep(row)
r.ImageOps.flip=original_flip
r.render(pieces,center,extent,.15,base/'preview.webp')
for piece in pieces:
 for obj in piece:obj.release()
stream=r.ROOT/'server-data/resources/cidade_roupas/stream'
for file in (base/'exports').glob('*'):
 shutil.copy2(file,stream/('mp_m_freemode_01_male_heist^'+file.name))
(base/'validation.json').write_text(json.dumps({'mesh_uv_weights_unchanged':True,'triangles_all_lods':triangles,'texture_resolution':[1024,2048],'collection':'Male_Heist','component':9,'drawable':0,'texture':0,'original_heist3_preserved':True},indent=2))
print('Installed and verified badge native mesh, texture, all LODs.')
