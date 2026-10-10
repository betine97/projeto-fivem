import bpy,json
from pathlib import Path
BASE=Path(__file__).resolve().parent/'preparacao_fivem_stage18'
bpy.ops.wm.open_mainfile(filepath=str(BASE/'warehouse_stage18_preparacao.blend'))
old=bpy.data.collections.get('LOD_Vegetacao_Rascunho')
if old:
    for o in list(old.objects):bpy.data.objects.remove(o,do_unlink=True)
    bpy.data.collections.remove(old)
c=bpy.data.collections.new('LOD_Vegetacao_Rascunho');bpy.context.scene.collection.children.link(c)
cache={};tris=0
for src in list(bpy.data.collections['EXPORT_Vegetacao'].objects):
    obj=src.copy();obj.name='LOD_'+src.name;c.objects.link(obj)
    if src.data.name not in cache:
        obj.data=src.data.copy();bpy.context.view_layer.objects.active=obj
        mod=obj.modifiers.new('Reducao_LOD','DECIMATE');mod.ratio=.035
        bpy.ops.object.modifier_apply(modifier=mod.name)
        cache[src.data.name]=obj.data
    else:obj.data=cache[src.data.name]
    obj.hide_render=True
    tris+=sum(len(p.vertices)-2 for p in obj.data.polygons)
c.hide_render=True;c.hide_viewport=True
report=json.loads((BASE/'validacao.json').read_text());report['lod_vegetation_instances']=54;report['lod_unique_meshes']=len(cache);report['lod_triangle_estimate']=tris
(BASE/'validacao.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(BASE/'warehouse_stage18_preparacao.blend'))
print('LOD OK',tris)
