import bpy,json,sys
from pathlib import Path
from mathutils import Matrix,Vector
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood'
bpy.ops.wm.open_mainfile(filepath=str(W/'mansao_otimizada.blend'));s=bpy.context.scene;spec=json.loads((W/'cozinha_completa.json').read_text())
col=bpy.data.collections.new('22_COZINHA_COMPLETA');s.collection.children.link(col)
with bpy.data.libraries.load(str(W/'cozinha_completa.blend'),link=False) as (src,dst):dst.objects=list(src.objects)
root=bpy.data.objects.new('Cozinha parede - conjunto completo',None);col.objects.link(root);root.matrix_world=Matrix(((0,1,0,13.534),(-1,0,0,-6.6),(0,0,1,-.8),(0,0,0,1)))
for o in dst.objects:
 if o.type=='MESH':col.objects.link(o);o.parent=root
# Clone an already authored potted plant at countertop scale; linked mesh data prevents duplication.
sources=[o for o in bpy.data.objects if o.parent and o.parent.name=='Vaso autoral sala' and o.type=='MESH'];assert sources
q=spec['counter_plant'];plant=bpy.data.objects.new('Vaso pequeno na bancada',None);col.objects.link(plant);plant.location=q['position'];plant.scale=(q['scale'],)*3
for src in sources:o=src.copy();o.data=src.data;col.objects.link(o);o.parent=plant;o.matrix_parent_inverse=Matrix.Identity(4)
# Move the native floor pot indicated by the arrow in the screenshot.
old=Vector(spec['plant_relocation']['old']);delta=Vector(spec['plant_relocation']['new'])-old
matches=[o for o in bpy.data.objects if o.type=='EMPTY' and (o.location-old).length<.01 and 'Cozinha' in o.name]
if not matches:matches=[o for o in bpy.data.objects if o.type=='EMPTY' and (o.location-old).length<.01]
assert len(matches)==1,[(o.name,list(o.location)) for o in matches]
matches[0].location+=delta
bpy.context.view_layer.update();assert spec['hi'][0]<14.186 and spec['hi'][2]<2.358
for c in bpy.data.collections:
 if c.name.startswith(('07_','09_','11_','13_','90_','91_','92_')):c.hide_render=True;c.hide_viewport=True
bpy.ops.wm.save_as_mainfile(filepath=str(W/'mansao_cozinha_completa.blend'));print('KITCHEN_PLACED_IN_LATEST_OPTIMIZED_SCENE',len(col.objects),'objects; native pot moved',matches[0].name,flush=True)
