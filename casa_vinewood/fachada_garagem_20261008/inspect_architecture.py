import bpy,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parent;W=P.parent
bpy.ops.wm.open_mainfile(filepath=str(W/'parede_aparador_20261008/mansao_parede_aparador.blend'))
rows=[]
for c in bpy.data.collections:
    if not c.name.startswith(('01_','02_','05_')):continue
    for o in c.all_objects:
        if o.type!='MESH':continue
        v=[o.matrix_world@Vector(p) for p in o.bound_box];lo=[min(p[i] for p in v) for i in range(3)];hi=[max(p[i] for p in v) for i in range(3)]
        if hi[1]>1.5:rows.append({'name':o.name,'col':c.name,'lo':lo,'hi':hi})
(P/'architecture_measurements.json').write_text(json.dumps(rows,indent=2))
for row in rows:print('ARCH',row)
for c in bpy.data.collections:
    if 'REFERENCIA' in c.name:c.hide_render=False
s=bpy.context.scene;s.render.engine='BLENDER_WORKBENCH';s.display.shading.color_type='TEXTURE';s.display.shading.show_shadows=True;s.display.shading.show_cavity=True;s.render.resolution_x=1300;s.render.resolution_y=900;s.render.resolution_percentage=100
for name,pos,look,scale in [('fachada_existente',(2,38,13),(2,7,1.8),29),('planta_frente',(2,10,34),(2,10,0),32)]:
    bpy.ops.object.camera_add(location=pos);c=bpy.context.object;c.rotation_euler=(Vector(look)-c.location).to_track_quat('-Z','Y').to_euler();c.data.type='ORTHO';c.data.ortho_scale=scale;s.camera=c;s.render.filepath=str(P/(name+'.png'));bpy.ops.render.render(write_still=True)
print('ARCHITECTURE_MEASURED',flush=True)
