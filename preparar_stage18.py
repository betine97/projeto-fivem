import bpy,json,math
from pathlib import Path
from mathutils import Vector
BASE=Path(__file__).resolve().parent
OUT=BASE/'preparacao_fivem_stage18';OUT.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(BASE/'warehouse_stage17_teto_fechado.blend'))
originals=[o for o in bpy.data.objects if o.name.startswith('PLACEHOLDER_') and o.type in ('MESH','CURVE')]
plants=[o for o in originals if o.name.endswith('_PLANT')];assert len(plants)==18
added=[]
for row,dy in [('FILA_A',-.78),('FILA_C',.78)]:
    for src in originals:
        o=src.copy();o.data=src.data;o.name=src.name+'_'+row
        for col in src.users_collection:col.objects.link(o)
        o.location.y+=dy;o['fileira']=row;added.append(o.name)
        if src.name.endswith('_PLANT'):o['asset_instance']='vegetacao';o['source_mesh']=src.data.name
for o in originals:o['fileira']='FILA_B'
allplants=[o for o in bpy.data.objects if o.name.startswith('PLACEHOLDER_') and '_PLANT' in o.name and o.type=='MESH']
pots=[o for o in bpy.data.objects if o.name.startswith('PLACEHOLDER_') and (o.name.endswith('_POT') or '_POT_FILA_' in o.name)]
assert len(allplants)==54 and len(pots)==54,(len(allplants),len(pots))
for side in ('LEFT','RIGHT'):
    assert sum(o.name.startswith('PLACEHOLDER_'+side) for o in allplants)==27
bpy.context.view_layer.update()
report={'plants':54,'pots':54,'plants_per_rack':27,'plants_per_module':9,'rows_per_module':3,'row_spacing_m':.78,'shared_vegetation_meshes':len({o.data.name for o in allplants}),'installed_on_server':False,'placement_coordinates':None,'game_ready':False,'remaining':['Baking/conversao dos materiais Blender para shaders GTA','LOD e otimizacao final','Exportacao YDR/YTD/YBN e validacao no jogo','Posicionamento YMAP apos receber coordenadas']}
s=bpy.context.scene;s.cycles.samples=64;s.render.filepath=str(BASE/'warehouse_stage18_interior.png')
for im in bpy.data.images:
    if im.source=='FILE' and im.filepath:im.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(BASE/'warehouse_stage18_54_plantas.blend'))
bpy.ops.render.render(write_still=True)

# Separate authoring copy: export groups and simple collision proxies, no placement.
groups={}
for name in ('EXPORT_Estrutura','EXPORT_Props','EXPORT_Vegetacao','COLISAO_Proxies','REFERENCIA_Luzes_Cameras'):
    c=bpy.data.collections.new(name);s.collection.children.link(c);groups[name]=c
for o in list(bpy.data.objects):
    if o.type in ('LIGHT','CAMERA','EMPTY'):dest=groups['REFERENCIA_Luzes_Cameras']
    elif o in allplants:dest=groups['EXPORT_Vegetacao']
    elif o.name.startswith(('WALL_','FLOOR_','CEILING_SLAB','DOOR_')) and 'HOSE' not in o.name:dest=groups['EXPORT_Estrutura']
    else:dest=groups['EXPORT_Props']
    dest.objects.link(o)
    for c in list(o.users_collection):
        if c!=dest:c.objects.unlink(o)
    if o.type=='MESH':o['export_local_origin']='warehouse_origin_0_0_0'
# Simple boxes for architectural pieces only. Door openings remain open.
count=0
for src in list(groups['EXPORT_Estrutura'].objects):
    if src.type!='MESH' or not src.name.startswith(('WALL_','FLOOR','CEILING_SLAB')):continue
    corners=[src.matrix_world@Vector(v) for v in src.bound_box]
    lo=Vector(tuple(min(v[i] for v in corners) for i in range(3)));hi=Vector(tuple(max(v[i] for v in corners) for i in range(3)))
    bpy.ops.mesh.primitive_cube_add(size=1,location=(lo+hi)/2);o=bpy.context.object;o.name='COL_PROXY_'+src.name;o.dimensions=hi-lo
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    for c in list(o.users_collection):c.objects.unlink(o)
    groups['COLISAO_Proxies'].objects.link(o);o.display_type='WIRE';o.hide_render=True;o['source']=src.name;count+=1
groups['COLISAO_Proxies'].hide_render=True;groups['COLISAO_Proxies'].hide_viewport=True
report['collision_proxy_count']=count
report['unique_meshes']=len({o.data.name for o in bpy.data.objects if o.type=='MESH'})
report['instanced_triangle_estimate']=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in bpy.data.objects if o.type=='MESH')
(OUT/'validacao.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'warehouse_stage18_preparacao.blend'))
print('STAGE18 OK',json.dumps(report))
