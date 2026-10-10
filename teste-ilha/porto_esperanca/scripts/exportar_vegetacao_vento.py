"""Projetos individuais com vento editável e colisor passivo funcional no Blender."""
import bpy,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
report=json.loads((P/'dados/preparacao_vegetacao_vento.json').read_text(encoding='utf8'))
target=P/'modelos/vegetacao_vento';target.mkdir(parents=True,exist_ok=True)
for item in report['vento']:
    key=item['id'];bpy.ops.wm.read_factory_settings(use_empty=True);s=bpy.context.scene;s.name='Vegetacao com vento '+key
    s.unit_settings.system='METRIC';s.render.fps=24;s.frame_end=144
    with bpy.data.libraries.load(str(P/report['arquivo']),link=False) as (src,dst):dst.objects=[key,'COL_'+key]
    o,c=dst.objects
    for ob in [o,c]:s.collection.objects.link(ob);ob.hide_viewport=False;ob.hide_set(False);ob.location=(0,0,0);ob.rotation_euler=(0,0,0);ob.scale=(1,1,1)
    o.hide_render=False;c.hide_render=True;c.display_type='WIRE';c['folhas_colidem']=False
    raw=P/'dados/colisoes_vegetacao';raw.mkdir(exist_ok=True);c.data.calc_loop_triangles()
    np.savez_compressed(raw/(key+'.npz'),vertices=np.array([v.co[:] for v in c.data.vertices],np.float32),triangulos=np.array([t.vertices[:] for t in c.data.loop_triangles],np.int32))
    bpy.context.view_layer.objects.active=c;c.select_set(True);bpy.ops.rigidbody.object_add();c.rigid_body.type='PASSIVE';c.rigid_body.collision_shape='MESH';c.rigid_body.use_margin=True;c.rigid_body.collision_margin=.003;c.select_set(False)
    s.rigidbody_world.substeps_per_frame=8;s.rigidbody_world.solver_iterations=20;s.rigidbody_world.point_cache.frame_end=144
    pts=[Vector(p) for p in o.bound_box];h=max(p.z for p in pts);r=max(max(abs(p.x),abs(p.y)) for p in pts);dist=max(h*2,r*3.8,5)
    d=bpy.data.cameras.new('Camera');cam=bpy.data.objects.new('Camera',d);s.collection.objects.link(cam);cam.location=(dist*.65,-dist,h*.5+dist*.28)
    cam.rotation_euler=(Vector((0,0,h*.5))-cam.location).to_track_quat('-Z','Y').to_euler();d.lens=48;d.clip_end=1000;s.camera=cam
    ld=bpy.data.lights.new('Sol','SUN');ld.energy=2;ld.angle=.13;sun=bpy.data.objects.new('Sol',ld);s.collection.objects.link(sun);sun.rotation_euler=(.48,-.44,-.6)
    w=bpy.data.worlds.new('Fundo neutro');w.use_nodes=True;w.node_tree.nodes['Background'].inputs[0].default_value=(.40,.50,.60,1);w.node_tree.nodes['Background'].inputs[1].default_value=.65;s.world=w
    s.render.engine='CYCLES';s.cycles.samples=32;s.render.resolution_x=900;s.render.resolution_y=1100;s.view_settings.view_transform='AgX'
    text=bpy.data.texts.new('LEIA-ME | vento e colisao');text.write('Reproduza quadros 1 a 144 para ver o vento. Amplitude (m) e Fase instancia ficam no modificador VENTO. O colisor COL_ é uma malha independente, invisível no render, com corpo rígido PASSIVE/MESH. Folhas sem colisão. Árvores enraizadas. Este modificador não se transforma automaticamente em vento nativo do GTA; conversão e teste no FiveM pendentes. As imagens originais estão incorporadas.\n')
    s['modelo']=key;s['revisao']=report['revisao'];s['colisao_passiva']=True;s['vento_nativo_validado']=False
    bpy.context.view_layer.objects.active=o;o.select_set(True);s.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=str(target/(key+'.blend')),compress=True)
    print('MODELO_VENTO_COLISAO_SALVO',key,flush=True)
