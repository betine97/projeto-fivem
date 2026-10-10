"""Salvar os dez modelos texturizados como projetos independentes completos."""
import bpy,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
report=json.loads((P/'dados/aplicacao_texturas_lote01.json').read_text(encoding='utf8'))
target=P/'modelos/texturas_lote01';target.mkdir(parents=True,exist_ok=True)
for model in report['modelos']:
    key=model['id'];bpy.ops.wm.read_factory_settings(use_empty=True)
    s=bpy.context.scene;s.name='Modelo texturizado '+key;s.unit_settings.system='METRIC'
    with bpy.data.libraries.load(str(P/report['arquivo']),link=False) as (src,dst):dst.objects=[key]
    o=dst.objects[0];s.collection.objects.link(o);o.hide_render=False;o.hide_viewport=False
    o.location=(0,0,0);o.rotation_euler=(0,0,0);o.scale=(1,1,1)
    points=[Vector(p) for p in o.bound_box];h=max(p.z for p in points);r=max(max(abs(p.x),abs(p.y)) for p in points)
    d=bpy.data.cameras.new('Camera');cam=bpy.data.objects.new('Camera',d);s.collection.objects.link(cam)
    dist=max(h*2,r*3.8,5);cam.location=(dist*.65,-dist,.55*h+dist*.28)
    cam.rotation_euler=(Vector((0,0,h*.5))-cam.location).to_track_quat('-Z','Y').to_euler();d.lens=48;d.clip_end=1000;s.camera=cam
    ld=bpy.data.lights.new('Sol','SUN');ld.energy=2;ld.angle=.13
    sun=bpy.data.objects.new('Sol',ld);s.collection.objects.link(sun);sun.rotation_euler=(.48,-.44,-.6)
    w=bpy.data.worlds.new('Fundo neutro');w.use_nodes=True
    w.node_tree.nodes.get('Background').inputs[0].default_value=(.40,.50,.60,1);w.node_tree.nodes.get('Background').inputs[1].default_value=.65;s.world=w
    s.render.engine='CYCLES';s.cycles.samples=40;s.cycles.transparent_max_bounces=24
    s.render.resolution_x=900;s.render.resolution_y=1100;s.view_settings.view_transform='AgX'
    s['modelo']=key;s['revisao_texturas']=report['revisao'];s['nome_referencia']=o['nome_referencia']
    s['observacao']='Materiais e imagens originais incorporados; validação visual da primeira amostra pendente. Sem pacote FiveM.'
    bpy.context.view_layer.objects.active=o;o.select_set(True)
    bpy.ops.wm.save_as_mainfile(filepath=str(target/(key+'.blend')),compress=True)
    print('MODELO_TEXTURIZADO_SALVO',key,flush=True)
print('DEZ_MODELOS_TEXTURIZADOS_SALVOS',flush=True)
