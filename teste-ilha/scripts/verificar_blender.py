from pathlib import Path
import json,bpy,numpy as np
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'teste-ilha.blend'))
g=np.load(P/'dados/terreno.npz')['terrain'];meta=json.loads((P/'dados/medidas.json').read_text());checks={}
def check(name,passed,details=None):checks[name]={'passed':bool(passed),'details':details}
check('metric_units',bpy.context.scene.unit_settings.system=='METRIC' and bpy.context.scene.unit_settings.scale_length==1)
check('terrain_sector_count',len(bpy.data.collections['01_TERRENO_EDITAVEL'].objects)==len(meta['tiles']))
errors=[];worst=0;triangles=0
for tile in meta['tiles']:
 x0,y0,x1,y1=tile['grid_bounds']
 for stride,suffix in [(1,''),(2,'_MED'),(4,'_LOW'),(8,'_VLOW')]:
  o=bpy.data.objects[tile['name']+suffix];verts=np.empty((len(o.data.vertices),3),np.float32);o.data.vertices.foreach_get('co',verts.ravel());expected=g[y0:y1+1:stride,x0:x1+1:stride].reshape(-1,3)
  delta=float(np.max(np.abs(verts-expected)));worst=max(worst,delta)
  if delta>1e-4:errors.append(o.name)
  if stride==1:triangles+=sum(len(p.vertices)-2 for p in o.data.polygons)
check('all_sectors_and_lods_match_continuous_grid',not errors,{'max_error_m':worst,'mismatches':errors})
check('high_triangle_count',triangles==meta['terrain_high_triangles'],triangles)
colliders=bpy.data.collections['07_COLISAO_TERRENO'].objects
check('collision_reference_meshes',len(colliders)==len(meta['tiles']) and all(len(o.data.vertices)>0 for o in colliders),{'sectors':len(colliders),'native_YBN_exported':False})
check('hidden_lods_and_collision',all(bpy.data.collections[n].hide_render and bpy.data.collections[n].hide_viewport for n in ['04_LOD_MEDIO','05_LOD_BAIXO','06_LOD_DISTANTE','07_COLISAO_TERRENO']))
check('texture_packed',any(im.packed_file is not None for im in bpy.data.images if im.source=='FILE'))
check('no_original_city_geometry',bpy.context.scene['geometria_cidade_original'] is False)
report={'passed':all(c['passed'] for c in checks.values()),'checks':checks}
(P/'dados/verificacao_blender.json').write_text(json.dumps(report,indent=2));print('BLENDER_VERIFIED',json.dumps(report),flush=True)
if not report['passed']:raise RuntimeError('Blender geometry verification failed')
