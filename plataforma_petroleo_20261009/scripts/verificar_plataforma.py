"""Reopen the authored rig, verify crane clearance and passive floor collisions."""
import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'plataforma_petroleo.blend'));sc=bpy.context.scene;sc.frame_set(1)
checks=[]
def check(name,ok,details=None):
    checks.append(dict(name=name,passed=bool(ok),details=details));print('CHECK',name,bool(ok),details,flush=True)
check('Arquivo reaberto',bool(sc))
meta=json.loads((ROOT/'dados/modelo.json').read_text());check('Referencia original preservada',hashlib.sha256((ROOT/'referencias/plataforma_aprovada.png').read_bytes()).hexdigest()==meta['source_sha256'])
stairs=json.loads((ROOT/'dados/escadas.json').read_text())
for s in stairs:check('Escada '+s['id'],s['width']>=2.3 and s['step_height']<=.18 and s['step_depth']>=.28,s)
check('Doze estacoes de trabalho',len(json.loads((ROOT/'dados/interacoes.json').read_text())['stations'])==12)
coll=bpy.data.collections['12_COLISAO_PREPARADA'];trees=[]
for o in coll.objects:
    me=o.data;v=[o.matrix_world@p.co for p in me.vertices];polys=[tuple(p.vertices) for p in me.polygons];trees.append((o.name,BVHTree.FromPolygons(v,polys)))
    edges={}
    for f in polys:
        for a,b in zip(f,f[1:]+f[:1]):k=tuple(sorted((a,b)));edges[k]=edges.get(k,0)+1
    check('Volume fechado '+o.name,all(n==2 for n in edges.values()) and o.rigid_body and o.rigid_body.type=='PASSIVE')
for s in json.loads((ROOT/'dados/interacoes.json').read_text())['stations']:
    p=Vector(s['position']);hits=[]
    for name,t in trees:
        pos,normal,idx,dist=t.ray_cast(p+Vector((0,0,.15)),Vector((0,0,-1)),2.4)
        if pos is not None:hits.append((pos.z,name))
    check('Piso da estacao '+s['id'],bool(hits) and p.z-1.9<=max(v[0] for v in hits)<=p.z+.15,sorted(hits,reverse=True)[:1])
# Whole cargo geometry is evaluated each frame against the upper deck floor.
cargo=bpy.data.objects['CARGA | pallet articulado'];moving=[o for o in cargo.children_recursive if o.type=='MESH']
positions=[];violations=[]
for frame in range(sc.frame_start,sc.frame_end+1):
    sc.frame_set(frame);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();cp=cargo.evaluated_get(dg).matrix_world.translation.copy();positions.append(cp[:])
    for o in moving:
        ev=o.evaluated_get(dg);pts=[ev.matrix_world@Vector(p) for p in ev.bound_box];lo=Vector(tuple(min(p[k] for p in pts) for k in range(3)));hi=Vector(tuple(max(p[k] for p in pts) for k in range(3)))
        # If the load crosses the top slab's height, it must be entirely in its notch.
        if lo.z<26.05 and hi.z>25.6:
            overlaps=not (hi.x<-29 or lo.x>29 or hi.y<-19.5 or lo.y>19.5)
            notch=lo.x>=-28 and hi.x<=-17 and lo.y>=-19.5 and hi.y<=-10
            if overlaps and not notch:violations.append(dict(frame=frame,object=o.name,bounds=[list(lo),list(hi)]))
check('Carga atravessa vao sem cortar piso superior',not violations,violations[:3])
dz=max(p[2] for p in positions)-min(p[2] for p in positions);dx=max(p[0] for p in positions)-min(p[0] for p in positions)
check('Guindaste eleva e gira a carga',dz>8 and dx>10,dict(vertical_m=dz,horizontal_x_m=dx))
sc.frame_set(1)
# A separate transient scene keeps test rigid bodies out of the delivered asset.
test=bpy.data.scenes.new('Validacao temporaria');bpy.context.window.scene=test;test.frame_start=1;test.frame_end=90;test.render.fps=24
cc=bpy.data.collections.new('Colisao temporaria');test.collection.children.link(cc)
for src in coll.objects:
    o=src.copy();cc.objects.link(o);o.hide_viewport=False;o.hide_render=False
tests=[('superior',(0,-18,26)),('producao',(0,-22,20)),('inferior',(0,-22,14)),('heliponto',(-49,5,28.7)),('doca',(27,-38,3.725))]
balls=[]
for name,p in tests:
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,radius=.20,location=(p[0],p[1],p[2]+2));o=bpy.context.object;o.name='Teste '+name;bpy.ops.rigidbody.object_add();o.rigid_body.mass=1;o.rigid_body.friction=.7;o.rigid_body.collision_shape='SPHERE';o.rigid_body.use_margin=True;o.rigid_body.collision_margin=.001;balls.append((name,p,o))
# All colliders need to be in the new world's physics collection explicitly.
for o in cc.objects:
    if o.name not in test.rigidbody_world.collection.objects:test.rigidbody_world.collection.objects.link(o)
test.rigidbody_world.substeps_per_frame=8;test.rigidbody_world.solver_iterations=16;test.rigidbody_world.point_cache.frame_end=90
for frame in range(1,91):test.frame_set(frame)
dg=bpy.context.evaluated_depsgraph_get()
for name,p,o in balls:
    z=o.evaluated_get(dg).matrix_world.translation.z;check('Contato fisico '+name,abs(z-(p[2]+.2))<.08,dict(expected_z=p[2]+.2,actual_z=z))
check('Nao instalado no servidor',not meta['installed'] and not meta['in_game_verified'])
out=dict(passed=all(c['passed'] for c in checks),checks=checks,in_game_verified=False,physics_scope='Blender passive collisions; native FiveM export pending')
(ROOT/'dados/verificacao_blender.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
print('PLATAFORMA_VERIFICADA',out['passed'],len(checks),flush=True)
if not out['passed']:raise RuntimeError('Falha na verificacao Blender')
