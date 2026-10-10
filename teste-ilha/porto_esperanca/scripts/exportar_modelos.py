"""Salvar cada planta como projeto Blender completo, importando a malha mestre."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
models=json.loads((P/'dados/implantacao.json').read_text(encoding='utf8'))['modelos']
for model in models:
    key=model['id'];bpy.ops.wm.read_factory_settings(use_empty=True)
    s=bpy.context.scene;s.name='Modelo '+key;s.unit_settings.system='METRIC'
    with bpy.data.libraries.load(str(P/'porto_esperanca.blend'),link=False) as (src,dst):
        dst.objects=[key]
    o=dst.objects[0];s.collection.objects.link(o);o.hide_render=False;o.hide_viewport=False
    o.location=(0,0,0);o.rotation_euler=(0,0,0);o.scale=(1,1,1)
    points=[Vector(p) for p in o.bound_box];h=max(p.z for p in points);r=max(max(abs(p.x),abs(p.y)) for p in points)
    d=bpy.data.cameras.new('Camera');cam=bpy.data.objects.new('Camera',d);s.collection.objects.link(cam)
    dist=max(h*2,r*3.8,5);cam.location=(dist*.65,-dist,.55*h+dist*.28)
    cam.rotation_euler=(Vector((0,0,h*.5))-cam.location).to_track_quat('-Z','Y').to_euler();d.lens=48;d.clip_end=1000;s.camera=cam
    ld=bpy.data.lights.new('Sol','SUN');ld.energy=3;ld.angle=.08;sun=bpy.data.objects.new('Sol',ld);s.collection.objects.link(sun);sun.rotation_euler=(.48,-.44,-.6)
    w=bpy.data.worlds.new('Fundo neutro');w.use_nodes=True;w.node_tree.nodes.get('Background').inputs[0].default_value=(.40,.50,.60,1);w.node_tree.nodes.get('Background').inputs[1].default_value=.65;s.world=w
    s.render.engine='CYCLES';s.cycles.samples=24;s.render.resolution_x=900;s.render.resolution_y=1100
    s.view_settings.view_transform='AgX';s['modelo']=key;s['nome_referencia']=model['nome']
    s['observacao']='Modelo autoral editavel; preparar LOD e colisao de tronco antes do FiveM'
    bpy.context.view_layer.objects.active=o;o.select_set(True)
    for a in bpy.context.screen.areas if bpy.context.screen else []:
        if a.type=='VIEW_3D':
            a.spaces.active.region_3d.view_location=(0,0,h*.5);a.spaces.active.region_3d.view_distance=max(h,r*2,4)*1.5
    bpy.ops.wm.save_as_mainfile(filepath=str(P/model['arquivo']),compress=True)
    print('MODELO_INDIVIDUAL_SALVO',key,flush=True)
print('MODELOS_INDIVIDUAIS_COM_CENA',len(models),flush=True)
