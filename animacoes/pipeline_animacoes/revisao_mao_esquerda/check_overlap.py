"""Check crossings of the actual skinned left hand and the weapon surface."""
import bpy, json, sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
HERE=Path(__file__).resolve().parent
version=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'r03'
settings=json.loads((HERE/version/'ajuste.json').read_text(encoding='utf8'))
bpy.ops.wm.open_mainfile(filepath=str(HERE/version/settings.get('blend_file','deitado_ak_mao_esquerda.blend')))
extra=sys.argv[sys.argv.index('--')+2:] if '--' in sys.argv else []
frame=int(extra[0]) if extra else 1
if extra:
    bpy.data.objects['GTA_Personagem_Rig'].animation_data.action=bpy.data.actions[settings['recoil_action']]
bpy.context.scene.frame_set(frame)
bpy.context.view_layer.update()
gun=bpy.data.objects['w_ar_assaultrifle']
inv=gun.matrix_world.inverted()
dep=bpy.context.evaluated_depsgraph_get()
gun_vertices=[];gun_faces=[]
for obj in gun.children_recursive:
    if obj.type!='MESH' or obj.hide_render:continue
    ev=obj.evaluated_get(dep);mesh=ev.to_mesh();mesh.calc_loop_triangles()
    start=len(gun_vertices)
    gun_vertices.extend(inv@(ev.matrix_world@v.co) for v in mesh.vertices)
    gun_faces.extend(tuple(i+start for i in tri.vertices) for tri in mesh.loop_triangles)
    ev.to_mesh_clear()
gun_bvh=BVHTree.FromPolygons(gun_vertices,gun_faces,all_triangles=True)
results=[]
for obj in bpy.data.objects:
    if obj.type!='MESH' or not obj.vertex_groups or obj.hide_render:continue
    ev=obj.evaluated_get(dep);mesh=ev.to_mesh();mesh.calc_loop_triangles()
    verts=[inv@(ev.matrix_world@v.co) for v in mesh.vertices]
    labels={}
    for v in mesh.vertices:
        weights=[(g.weight,obj.vertex_groups[g.group].name) for g in v.groups]
        left=[w for w,n in weights if n.startswith(('SKEL_L_Hand','SKEL_L_Finger'))]
        if sum(left)>.5:
            labels[v.index]=max(weights)[1]
    tris=[tuple(t.vertices) for t in mesh.loop_triangles if all(i in labels for i in t.vertices)]
    if not tris:
        ev.to_mesh_clear();continue
    hand_bvh=BVHTree.FromPolygons(verts,tris,all_triangles=True)
    overlaps=gun_bvh.overlap(hand_bvh)
    fingers={}
    for gi,hi in overlaps:
        for i in tris[hi]:
            name=labels[i]
            fingers.setdefault(name,set()).add(i)
    results.append({'mesh':obj.name,'crossing_triangle_pairs':len(overlaps),'vertices_by_bone':{n:len(ids) for n,ids in fingers.items()},'crossing_points':{n:[list(verts[i]) for i in ids] for n,ids in fingers.items()}})
    ev.to_mesh_clear()
filename=f'surface_recoil_{frame}.json' if extra else 'surface_check.json'
(HERE/version/filename).write_text(json.dumps(results,indent=2),encoding='utf8')
print('SURFACE_CROSSINGS',frame,[(r['mesh'],r['crossing_triangle_pairs'],r['vertices_by_bone']) for r in results])
