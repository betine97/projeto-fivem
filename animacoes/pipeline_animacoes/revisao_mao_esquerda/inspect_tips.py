import bpy, json
from pathlib import Path
from mathutils import Vector
HERE=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(HERE/'r07'/'deitado_ak_mao_esquerda.blend'))
bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
rig=bpy.data.objects['GTA_Personagem_Rig'];gun=bpy.data.objects['w_ar_assaultrifle']
dep=bpy.context.evaluated_depsgraph_get();cloud={i:[] for i in range(5)}
for obj in bpy.data.objects:
    if obj.type!='MESH' or obj.hide_render or not obj.vertex_groups:continue
    ev=obj.evaluated_get(dep);mesh=ev.to_mesh()
    for i in range(5):
        name=f'SKEL_L_Finger{i}2';group=obj.vertex_groups.get(name)
        if not group:continue
        inv=(rig.matrix_world@rig.pose.bones[name].matrix).inverted()
        for v in mesh.vertices:
            if any(g.group==group.index and g.weight>.85 for g in v.groups):
                cloud[i].append(inv@(ev.matrix_world@v.co))
    ev.to_mesh_clear()
results={}
for i,points in cloud.items():
    b=rig.pose.bones[f'SKEL_L_Finger{i}2'];prev=rig.pose.bones[f'SKEL_L_Finger{i}1']
    real=sum(points,Vector())/len(points)
    assumed=b.bone.matrix_local.to_3x3().inverted()@(b.bone.head_local-prev.bone.head_local)
    results[i]={'actual_local':list(real),'assumed_local':list(assumed.normalized()),'points':len(points),'actual_gun':list(gun.matrix_world.to_3x3().inverted()@(rig.matrix_world.to_3x3()@(b.matrix.to_3x3()@real))), 'angle_error_degrees':real.angle(assumed)*180/3.14159265}
(HERE/'tip_axes.json').write_text(json.dumps(results,indent=2),encoding='utf8')
print(json.dumps(results,indent=2))
