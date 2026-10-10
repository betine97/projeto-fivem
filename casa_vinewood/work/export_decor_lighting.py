import bpy,sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood';OUT=W/'decor_fivem';OUT.mkdir(exist_ok=True)
sys.path[:0]=[r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps',r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/sollumz',str(R/'laboratorio_fivem/work/pydeps')]
import addon_utils,numpy as np
addon_utils.enable('Sollumz',default_set=True)
from PIL import Image
from Sollumz.sollumz_properties import SollumType
from Sollumz.tools.drawablehelper import convert_obj_to_model
from Sollumz.tools.meshhelper import mesh_add_missing_uv_maps,mesh_add_missing_color_attrs
from Sollumz.ydr.shader_materials import create_shader
from Sollumz.iecontext import ExportContext,ExportSettings,export_context_scope
from Sollumz.ydr.ydrexport import export_ydr
from szio.gta5 import AssetTarget,AssetFormat,AssetVersion
bpy.ops.wm.open_mainfile(filepath=str(W/'mansao_iluminada.blend'))
c=bpy.data.collections['18_SPOTS_E_LED_ESCADA'];c.hide_viewport=False
styles={}
for family,color in [('led',(255,214,166,255)),('trim',(194,187,173,255))]:
 m=create_shader('emissive.sps' if family=='led' else 'default.sps');m.name='mansao_decor_'+family
 p=OUT/(m.name+'.dds');Image.new('RGBA',(4,4),color).save(p,pixel_format='DXT5')
 tx=m.node_tree.nodes['DiffuseSampler'];tx.image=bpy.data.images.load(str(p),check_existing=True);tx.texture_properties.embedded=True
 if family=='led':m.node_tree.nodes['emissiveMultiplier'].set(0,2.5)
 styles[family]=m
root=bpy.data.objects.new('mansao_spots_led',None);bpy.context.scene.collection.objects.link(root);root.sollum_type=SollumType.DRAWABLE
parts=[];dg=bpy.context.evaluated_depsgraph_get()
for src in c.objects:
 if src.type!='MESH':continue
 me=bpy.data.meshes.new_from_object(src.evaluated_get(dg),depsgraph=dg);me.transform(src.matrix_world)
 family=src.data.materials[0]['decor_family'];me.materials.clear();me.materials.append(styles[family])
 uv=me.uv_layers[0] if me.uv_layers else me.uv_layers.new(name='UVMap 0');uv.name='UVMap 0'
 for p in me.polygons:
  p.material_index=0
  for i in p.loop_indices:
   q=me.vertices[me.loops[i].vertex_index].co;uv.data[i].uv=(q.x,q.y)
 mesh_add_missing_uv_maps(me);mesh_add_missing_color_attrs(me)
 for attr in me.color_attributes:attr.data.foreach_set('color_srgb',np.tile(np.array([1,1,1,1],dtype=np.float32),len(attr.data)))
 o=bpy.data.objects.new(src.name+'_export',me);bpy.context.scene.collection.objects.link(o);o.parent=root;convert_obj_to_model(o);parts.append(o)
targets=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
with export_context_scope(ExportContext('mansao_spots_led',ExportSettings(targets=targets))):export_ydr(root).save(OUT,targets)
pts=np.array([v.co for o in parts for v in o.data.vertices]);bounds=dict(lo=pts.min(0).tolist(),hi=pts.max(0).tolist())
(W/'work/decor_export_bounds.json').write_text(json.dumps(bounds,indent=2))
print('DECOR_EXPORTED',len(parts),'objects',flush=True)
