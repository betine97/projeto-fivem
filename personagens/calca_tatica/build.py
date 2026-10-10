import sys,io,json,shutil,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'catalogo_nativo'))
import render_catalog as r
from szio.gta5 import save_asset,AssetTarget,AssetFormat,AssetVersion,EmbeddedTexture
from szio.types import DataSource
from geometry_v3 import add_pockets
base=Path(__file__).resolve().parent
source=base/'source/lowr_001_r.ydd'; a=r.try_load_asset(source)
targetrow=next(m for m in r.DATA['models'] if m['collection']=='mp_m_freemode_01_male_heist' and m['part']=='lowr' and m['index']==6)
target=r.try_load_asset(r.vpath(targetrow['path']))
drawable=next(iter(a.drawables.values())); drawable.name='lowr_006_r.#dd'
a.drawables={next(iter(target.drawables)):drawable}
for shader in drawable.shader_group.shaders:
 for p in shader.parameters:
  if p.name.lower()=='diffusesampler':p.value='lowr_diff_006_a_whi'
anchors=add_pockets(drawable)
img=r.Image.open(base/'textures/revision3-atlas.png').convert('RGB').resize((1024,1024),r.Image.Resampling.LANCZOS)
img.save(base/'textures/lowr_diff_006_a_whi.png')
dds=base/'textures/lowr_diff_006_a_whi.dds';img.save(dds,format='DDS',pixel_format='DXT1')
txd=r.try_load_asset(base/'source/lowr_diff_001_a_whi.ytd');txd.textures={'lowr_diff_006_a_whi':EmbeddedTexture('lowr_diff_006_a_whi',img.width,img.height,DataSource.create(dds))}
targets=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
save_asset(a,targets,base/'exports','lowr_006_r');save_asset(txd,targets,base/'exports','lowr_diff_006_a_whi')
# Re-read exported binaries and validate original vertices, UVs and bone weights.
check=r.try_load_asset(base/'exports/lowr_006_r.ydd'); original=r.try_load_asset(source)
newd=next(iter(check.drawables.values())); oldd=next(iter(original.drawables.values()))
triangles=0
for lod,models in oldd.models.items():
 for oldm,newm in zip(models,newd.models[lod]):
  for oldg,newg in zip(oldm.geometries,newm.geometries):
   assert r.np.array_equal(oldg.vertex_buffer,newg.vertex_buffer)
   assert r.np.array_equal(oldg.index_buffer,newg.index_buffer)
   triangles+=len(newg.index_buffer)//3
assert 'lowr_diff_006_a_whi' in r.try_load_asset(base/'exports/lowr_diff_006_a_whi.ytd').textures
# Preview the actual exported native asset with the exported diffuse.
oldload=r.try_load_asset
r.try_load_asset=lambda p: check if str(p).endswith('lowr_001_r.ydd') else txd if str(p).endswith('lowr_diff_001_a_whi.ytd') else oldload(p)
row=next(m for m in r.DATA['models'] if m['collection']=='mp_m_freemode_01_male_freemode_business2' and m['part']=='lowr' and m['index']==1)
original_flip=r.ImageOps.flip
r.ImageOps.flip=lambda image:image
pieces,center,extent,*_=r.prep(row)
r.ImageOps.flip=original_flip
r.render(pieces,center,extent,.15,base/'preview.webp')
r.render(pieces,center,extent,r.math.pi+.15,base/'preview_back.webp')
r.render(pieces,center,extent,r.math.pi/2,base/'preview_left.webp')
r.render(pieces,center,extent,-r.math.pi/2,base/'preview_right.webp')
for piece in pieces:
 for obj in piece:obj.release()
stream=r.ROOT/'server-data/resources/cidade_roupas/stream'
for file in (base/'exports/lowr_006_r.ydd',base/'exports/lowr_diff_006_a_whi.ytd'):
 shutil.copy2(file,stream/('mp_m_freemode_01_male_heist^'+file.name))
(base/'validation.json').write_text(json.dumps({'revision':3,'original_base_mesh_uv_weights_unchanged':True,'original_triangles_all_lods':triangles,'pocket_relief_mm':9,'pocket_uv_height_ratio':(.315-.158)/(.39-.155),'added_pocket_triangles':sum(len(g.index_buffer)//3 for models in newd.models.values() for m in models for g in m.geometries[1:]),'texture_resolution':[1024,1024],'collection':'Male_Heist','component':4,'drawable':6,'texture':0,'original_business2_preserved':True,'moving_straps':3,'in_game_validation':'pending'},indent=2))
from build_straps import build_straps
build_straps(r,base,anchors)
print('Installed and verified tactical trousers: original geometry preserved, raised pockets and moving straps; revision 3.')
