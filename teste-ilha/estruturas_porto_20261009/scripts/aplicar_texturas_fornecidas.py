"""Aplica os PNGs planos fornecidos pelo usuario, sem modificar seus pixels."""
import bpy,sys,json,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
WALLS={1:7,2:8,3:5,4:9,5:7,6:5,7:6,8:5,9:7}
WOOD={1:4,2:1,3:3,4:1,5:1,6:2,7:1,8:4,9:2}
LABELS={1:'Madeira_verde_escura',2:'Madeira_azul_clara',3:'Madeira_verde_agua',4:'Madeira_azul_petroleo',
 5:'Reboco_azul',6:'Reboco_verde',7:'Reboco_creme',8:'Reboco_amarelo',9:'Reboco_turquesa',10:'Reboco_laranja'}

def source_image(id):
    name='Textura_fornecida_'+f'{id:02}'
    if name in bpy.data.images:return bpy.data.images[name]
    im=bpy.data.images.load(str(ROOT/'texturas'/f'{id:02}.png'));im.name=name;im.pack();return im

def texture_material(id):
    name='Usuario_'+LABELS[id]
    if name in bpy.data.materials:return bpy.data.materials[name]
    m=bpy.data.materials.new(name);m.use_nodes=True;m.use_fake_user=True;m.asset_mark()
    m['arquivo_original_sem_edicao']=f'texturas/{id:02}.png';m['mapa_cor']='imagem fornecida';m['relevo']='aproximado a partir da luminancia; nao e um mapa de altura medido'
    nt=m.node_tree;bs=nt.nodes.get('Principled BSDF');tx=nt.nodes.new('ShaderNodeTexImage');tx.image=source_image(id);tx.extension='EXTEND';tx.label='Cor original fornecida pelo usuario'
    nt.links.new(tx.outputs['Color'],bs.inputs['Base Color'])
    gray=nt.nodes.new('ShaderNodeRGBToBW');nt.links.new(tx.outputs['Color'],gray.inputs[0])
    bump=nt.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.24;bump.inputs['Distance'].default_value=.014 if id<5 else .022
    nt.links.new(gray.outputs[0],bump.inputs['Height']);nt.links.new(bump.outputs[0],bs.inputs['Normal'])
    rough=nt.nodes.new('ShaderNodeMapRange');rough.inputs['To Min'].default_value=.64;rough.inputs['To Max'].default_value=.91
    nt.links.new(gray.outputs[0],rough.inputs[0]);nt.links.new(rough.outputs[0],bs.inputs['Roughness'])
    return m

def cube_uv(me):
    if me.uv_layers:return
    uv=me.uv_layers.new(name='UV_modulo_madeira')
    for p in me.polygons:
        axis=max(range(3),key=lambda k:abs(p.normal[k]))
        for li in p.loop_indices:
            co=me.vertices[me.loops[li].vertex_index].co
            uv.data[li].uv=(co.x+.5,co.z+.5) if axis==1 else ((co.y+.5,co.z+.5) if axis==0 else (co.x+.5,co.y+.5))

def apply_textures(id,cfg):
    if bpy.context.scene.get('texturas_planas_do_usuario'):
        return dict(parede=WALLS.get(id),madeira=WOOD.get(id))
    width=cfg['w'];depth=cfg['d'];height=cfg.get('H',cfg.get('h',cfg['n']*3.2))
    wall=texture_material(WALLS[id]) if id in WALLS else None
    if wall:
        old=bpy.data.materials.get('Reboco_extraido_da_referencia')
        if old:old.user_remap(wall)
        for o in bpy.data.objects:
            if o.type!='MESH' or o.name.startswith('COL_'):continue
            if o.name.startswith(('Parede_frente','Parede_lado')):
                layer=o.data.uv_layers.active
                if layer:
                    span=width if o.name.startswith('Parede_frente') else depth
                    for uv in layer.data:uv.uv=(uv.uv.x/span,uv.uv.y/height)
            elif o.name in ('Parede_traseira','Parede_lateral_oculta'):
                o.data=o.data.copy();o.data.materials.clear();o.data.materials.append(wall)
                layer=o.data.uv_layers.new(name='UV_parede')
                for p in o.data.polygons:
                    for li in p.loop_indices:
                        c=o.data.vertices[o.data.loops[li].vertex_index].co
                        layer.data[li].uv=((c.x+.5) if o.name=='Parede_traseira' else (c.y+.5),c.z+.5)
    if id in WOOD:
        wood=texture_material(WOOD[id]);old=bpy.data.materials.get('Madeira_verde')
        if old:old.user_remap(wood)
        for me in bpy.data.meshes:
            if any(m==wood for m in me.materials):cube_uv(me)
    bpy.context.scene['texturas_planas_do_usuario']=True
    for o in bpy.data.objects:
        if 'id_referencia' in o:o['texturas_fornecidas']=json.dumps(dict(parede=WALLS.get(id),madeira=WOOD.get(id)))
    return dict(parede=WALLS.get(id),madeira=WOOD.get(id))

def update_library():
    spec=importlib.util.spec_from_file_location('modelagem',ROOT/'scripts'/'modelar_estruturas.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    spec=importlib.util.spec_from_file_location('refinamento',ROOT/'scripts'/'refinar_modelo.py');ref=importlib.util.module_from_spec(spec);spec.loader.exec_module(ref)
    for path in sorted((ROOT/'modelos').glob('[0-9][0-9]_*.blend')):
        bpy.ops.wm.open_mainfile(filepath=str(path));id=int(path.stem[:2]);mod.BUILDID=id;mod.C=dict(mod.CFG[id]);mod.C.update(story=3.2,H=mod.C.get('h',mod.C['n']*3.2))
        mod.COL={c.name:c for c in bpy.data.collections};mod.M={m.name:m for m in bpy.data.materials}
        assigned=apply_textures(id,mod.C)
        mod.MATCACHE={};ref.apply_polish(mod)
        # Correct the mezzanine landing to meet the top stair without a gap.
        if id==10:
            for o in bpy.data.objects:
                if o.name.startswith('Mezanino') and o.scale.x<2:o.location.y=7.20;o.scale.y=1.0
        bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)
        mod.render(ROOT/'previews'/f'{id:02}_exterior.png');mod.render(ROOT/'previews'/f'{id:02}_interior.png',True)
        jf=ROOT/'dados'/f'{id:02}_modelo.json';info=json.loads(jf.read_text(encoding='utf-8'));info['texturas_fornecidas']=assigned
        if id==10:
            for a in info['aberturas']:
                if a['tipo']=='vao_escada_mezanino':a['limites'][3]=6.7
        jf.write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
        print('TEXTURAS_APLICADAS',id,assigned,flush=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for id in range(1,11):texture_material(id)
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Biblioteca_materiais.blend'),compress=True)
    print('TEXTURIZACAO_CONCLUIDA',flush=True)

if __name__=='__main__':update_library()
