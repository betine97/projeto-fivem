import bpy,json
from pathlib import Path
p=Path(__file__).resolve().parent.parent
r=json.loads((p/'medidas_estudo.json').read_text(encoding='utf-8'))
assert len(bpy.data.collections)>=9
assert bpy.data.collections['90_REFERENCIA_NATIVA_ORIGINAL (oculta)'].hide_viewport
assert bpy.data.collections['90_REFERENCIA_NATIVA_ORIGINAL (oculta)'].hide_render
assert bpy.data.collections['06_TETO_SUPERIOR (oculto para inspecao)'].hide_viewport
assert bpy.context.scene.unit_settings.system=='METRIC'
for b in r['boxes']:
 o=bpy.data.objects.get(b['name']);assert o is not None,b['name']
 lo=b['bounds'];expected=[lo[1]-lo[0],lo[3]-lo[2],lo[5]-lo[4]]
 assert all(abs(o.dimensions[i]-expected[i])<1e-5 for i in range(3)),b['name']
assert abs(r['areas_brutas_estudo_m2']['total']-771.57)<1e-5
print('SAVED VERIFIED',len(r['boxes']),'mesh boxes;',r['areas_brutas_estudo_m2'])
print('NAVIGATION MODE',getattr(bpy.context.preferences.inputs,'navigation_mode','not exposed'))
for k in bpy.context.window_manager.keyconfigs.default.keymaps:
 if 'Fly' in k.name:
  print('FLY KEYMAP',k.name,[(i.propvalue,i.type,i.value) for i in k.keymap_items])
(p/'verificacao_blender.json').write_text(json.dumps({'saved_file_verified':True,'boxes':len(r['boxes']),'metric_scale':True,'source_reference_preserved_and_hidden':True,'areas':r['areas_brutas_estudo_m2']},ensure_ascii=False,indent=2),encoding='utf-8')
