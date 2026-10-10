import bpy,json
from pathlib import Path
from mathutils import Matrix
OUT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(OUT/'castelo_rockford_evoluido.blend'))
door=bpy.data.objects['Banheiro suite porta aberta.003']
assert 7.5<door.location.x<8.5 and .9<door.location.y<1.5
reflection=Matrix.Identity(4);reflection[0][0]=-1;reflection[0][3]=18.2
selected=[door]+[o for o in bpy.data.objects if o.name.startswith(('Almofada porta','Macaneta bronze')) and 7.3<o.location.x<8.7 and .9<o.location.y<1.5 and 4.8<o.location.z<8.9]
assert len(selected)==7,[(o.name,tuple(o.location)) for o in selected]
for o in selected:
    local=o.matrix_world.inverted()@reflection@o.matrix_world
    o.data.transform(local);o.data.flip_normals();o.data.update()
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'castelo_rockford_evoluido.blend'))
data=json.loads((OUT/'circulacao_corrigida.json').read_text(encoding='utf-8'))
data['door_and_hardware_aligned']=[o.name for o in selected]
(OUT/'circulacao_corrigida.json').write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8')
print('BATHROOM_DOOR_ALIGNED',flush=True)
