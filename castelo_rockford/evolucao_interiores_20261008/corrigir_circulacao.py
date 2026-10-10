import bpy, json
from pathlib import Path
from mathutils import Matrix

OUT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(OUT/'castelo_rockford_evoluido.blend'))
# Move the rear-right bathroom to the exterior corner so the suite entrance
# reaches the suite directly, rather than the bathroom wall or its enclosure.
reflection=Matrix.Identity(4);reflection[0][0]=-1;reflection[0][3]=18.2
changed=[]
for o in list(bpy.data.objects):
    if o.type!='MESH':continue
    pts=[o.matrix_world@v.co for v in o.data.vertices]
    lo=[min(p[i] for p in pts) for i in range(3)]
    hi=[max(p[i] for p in pts) for i in range(3)]
    bathroom=o.name.startswith(('Banheiro suite','Banheiro bancada')) and lo[0]>4 and hi[0]<8.2 and lo[1]>.08 and hi[1]<3.6 and lo[2]>4.8
    hardware=o.name.startswith(('Almofada porta','Macaneta bronze')) and 6.8<o.location.x<7.8 and .8<o.location.y<2.7 and 4.8<o.location.z<8.8
    if bathroom or hardware:
        # Bake reflection into mesh coordinates and restore outward winding.
        local=o.matrix_world.inverted()@reflection@o.matrix_world
        o.data.transform(local);o.data.flip_normals();o.data.update()
        changed.append(o.name)
assert len(changed)>=5,changed
# Keep first-floor door details with their own floor for isolated editing.
c=bpy.data.collections.new('02_ACABAMENTOS_PORTAS')
bpy.data.collections['02_SUITES'].children.link(c)
for o in list(bpy.data.objects):
    if o.name.startswith(('Almofada porta','Macaneta bronze')) and 4.8<o.location.z<8.9:
        for col in list(o.users_collection):col.objects.unlink(o)
        c.objects.link(o)
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'castelo_rockford_evoluido.blend'))
(OUT/'circulacao_corrigida.json').write_text(json.dumps({'suite':'fundos direita','bathroom_relocated_to_exterior_corner':True,'objects':changed},indent=2,ensure_ascii=False),encoding='utf-8')
print('CIRCULACAO_CORRIGIDA',changed,flush=True)
