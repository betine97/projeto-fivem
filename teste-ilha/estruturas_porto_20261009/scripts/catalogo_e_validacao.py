"""Reabre e verifica cada .blend; monta catalogo separado, sem instalar na ilha."""
import bpy, json, math, sys, importlib.util
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]

def prepare_library():
    spec=importlib.util.spec_from_file_location('modelagem',ROOT/'scripts'/'modelar_estruturas.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    for path in sorted((ROOT/'modelos').glob('[0-9][0-9]_*.blend')):
        bpy.ops.wm.open_mainfile(filepath=str(path));sc=bpy.context.scene
        # Portal stone frames were caught by the old 'Porta' wood prefix.
        repaired=False;stone=bpy.data.materials.get('Pedra');cache={}
        for o in bpy.data.objects:
            if o.type=='MESH' and o.name.startswith(('Portal_pedra','Portal_verga')) and stone and any(m!=stone for m in o.data.materials):
                key=o.data.name
                if key not in cache:
                    me=o.data.copy();me.materials.clear();me.materials.append(stone);cache[key]=me
                o.data=cache[key];repaired=True
        root=next(o for o in bpy.data.objects if 'id_referencia' in o)
        asset=bpy.data.collections.get('Modelo_completo') or bpy.data.collections.new('Modelo_completo')
        if asset.name not in sc.collection.children:sc.collection.children.link(asset)
        for co in list(sc.collection.children):
            if co==asset or co.name=='Apresentacao':continue
            for o in co.all_objects:
                if o!=root and not o.parent:o.parent=root
            if co.name not in asset.children:asset.children.link(co)
            sc.collection.children.unlink(co)
        asset.asset_mark();asset.asset_data.description=path.stem.replace('_',' ')+' — estrutura editavel com interior'
        sc['colecao_reutilizavel']='Modelo_completo'
        for o in bpy.context.view_layer.objects:o.select_set(False)
        root.select_set(True);bpy.context.view_layer.objects.active=root
        for screen in bpy.data.screens:
            for area in screen.areas:
                if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.shading.type='MATERIAL'
        bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)
        if repaired:
            id=int(path.stem[:2]);mod.BUILDID=id;mod.C=dict(mod.CFG[id]);mod.C.update(story=3.2,H=mod.C.get('h',mod.C['n']*3.2));mod.COL={c.name:c for c in bpy.data.collections};mod.M={m.name:m for m in bpy.data.materials}
            mod.render(ROOT/'previews'/f'{id:02}_exterior.png')
        print('ASSET_PREPARADO',path.name,flush=True)

def validate():
    reports=[]
    paths=sorted((ROOT/'modelos').glob('[0-9][0-9]_*.blend'))
    assert len(paths)==10,f'Esperados 10 modelos, encontrados {len(paths)}'
    for path in paths:
        bpy.ops.wm.open_mainfile(filepath=str(path));sc=bpy.context.scene;sc.frame_set(1);issues=[]
        meshes=[o for o in bpy.data.objects if o.type=='MESH' and not o.name.startswith('COL_')]
        if not meshes:issues.append('sem geometria')
        for o in meshes:
            if any(not math.isfinite(v) for p in o.data.vertices for v in p.co):issues.append('vertice invalido: '+o.name)
            if any(abs(v)<1e-6 for v in o.scale):issues.append('escala nula: '+o.name)
        images=[i for i in bpy.data.images if i.type!='RENDER_RESULT']
        if not any(i.packed_file for i in images):issues.append('referencia nao empacotada')
        for i in images:
            if not i.packed_file and i.source=='FILE':issues.append('imagem externa: '+i.name)
        for font in bpy.data.fonts:
            if font.filepath and font.name!='Bfont' and not font.packed_file:issues.append('fonte nao empacotada: '+font.name)
        roots=[o for o in bpy.data.objects if 'id_referencia' in o]
        if len(roots)!=1:issues.append('metadados ausentes')
        info=json.loads((ROOT/'dados'/f'{path.name[:2]}_modelo.json').read_text(encoding='utf-8'))
        floors=len(info['interiores'])
        stairs=[o for o in meshes if o.name.startswith('Degrau_')]
        if floors>1:
            if len(stairs)!=18*(floors-1):issues.append('numero incorreto de degraus')
            for hole in [a for a in info['aberturas'] if a['tipo']=='vao_escada']:
                x0,x1,y0,y1=hole['limites'];z=hole['z'];p=Vector(((x0+x1)/2,(y0+y1)/2,z-.1))
                for o in meshes:
                    if o.name.startswith('Laje_com_abertura'):
                        b=[o.matrix_world@Vector(c) for c in o.bound_box]
                        if all(min(v[j] for v in b)<p[j]<max(v[j] for v in b) for j in range(3)):issues.append('laje bloqueia escada')
        doors=[o for o in bpy.data.objects if o.get('tipo')=='porta_abrir']
        for o in doors:
            if not o.children:issues.append('porta sem folhas')
            if o.get('passagem_largura',0)<.80:issues.append('porta estreita')
        if not sc.get('texturas_planas_do_usuario'):issues.append('texturas fornecidas nao aplicadas')
        if not sc.get('passagens_conferidas'):issues.append('passagens nao revisadas')
        if path.name.startswith('10'):
            # Check concrete trim leaves the center of the gate physically open.
            for o in meshes:
                if o.name.startswith('Rodape_concreto'):
                    bb=[o.matrix_world@Vector(c) for c in o.bound_box]
                    if min(v.x for v in bb)<0<max(v.x for v in bb) and min(v.z for v in bb)<.5<max(v.z for v in bb):issues.append('rodape bloqueia portao')
        collision=bpy.data.collections.get('Colisao_preparada')
        if not collision or not collision.objects:issues.append('colisao de referencia ausente')
        for suffix in ('exterior','interior'):
            if not (ROOT/'previews'/f'{path.name[:2]}_{suffix}.png').exists():issues.append('preview ausente '+suffix)
        report=dict(arquivo=path.name,ok=not issues,pendencias=issues,objetos=len(meshes),malhas_unicas=len(set(o.data.name for o in meshes)),
          texturas_empacotadas=sum(bool(i.packed_file) for i in images),andares=floors,portas_articuladas=len(doors),degraus=len(stairs))
        reports.append(report);print('VALIDADO',json.dumps(report,ensure_ascii=False),flush=True)
    (ROOT/'dados'/'validacao_blender.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf-8')
    assert all(r['ok'] for r in reports),'Falha na validacao; veja o relatorio.'
    return paths

def catalog(paths):
    bpy.ops.wm.read_factory_settings(use_empty=True);sc=bpy.context.scene
    for i,path in enumerate(paths):
        with bpy.data.libraries.load(str(path),link=False) as (src,dst):
            dst.collections=['Modelo_completo'] if 'Modelo_completo' in src.collections else [n for n in src.collections if n not in ('Apresentacao','Colisao_preparada')]
        root=bpy.data.objects.new(path.stem,None);sc.collection.objects.link(root)
        root['arquivo_original']=str(path);root['catalogo_apenas']=True
        top=[]
        for co in dst.collections:
            if co:
                sc.collection.children.link(co)
                top.extend(o for o in co.all_objects if not o.parent)
        for o in top:o.parent=root
        root.location=((i%5-2)*23,(i//5-.5)*34,0)
        label=bpy.data.curves.new('Identificacao_'+path.name[:2],'FONT');label.body=path.stem.replace('_',' ');label.align_x='CENTER';label.size=.90;label.extrude=.003
        obj=bpy.data.objects.new('Identificacao_'+path.name[:2],label);sc.collection.objects.link(obj);obj.location=(root.location.x,root.location.y-(18 if path.name.startswith('09') else 8),.02)
    # Remap equivalent material/cube data only; reference images keep their IDs.
    known={}
    for m in list(bpy.data.materials):
        name=m.name.split('.')[0]
        if any(n in name for n in ('referencia','Referencia','Reboco','Telha')):continue
        key=(name,tuple(round(v,5) for v in m.diffuse_color))
        if key in known:m.user_remap(known[key]);bpy.data.materials.remove(m)
        else:known[key]=m
    cubes={}
    for me in list(bpy.data.meshes):
        if not me.name.startswith('Modulo_cubo_'):continue
        uv=me.uv_layers.active
        key=(tuple(m.name for m in me.materials),tuple((round(p.uv.x,6),round(p.uv.y,6)) for p in uv.data) if uv else ())
        if key in cubes:me.user_remap(cubes[key]);bpy.data.meshes.remove(me)
        else:cubes[key]=me
    world=bpy.data.worlds.new('Ceu_catalogo');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.65,.72,.82,1)
    world.node_tree.nodes['Background'].inputs[1].default_value=.65;sc.world=world
    sun=bpy.data.lights.new('Sol_catalogo','SUN');sun.energy=2.5;sun.angle=.16;o=bpy.data.objects.new('Sol_catalogo',sun);sc.collection.objects.link(o);o.rotation_euler=(.4,-.5,-.3)
    m=bpy.data.materials.new('Piso_catalogo');m.diffuse_color=(.25,.28,.29,1)
    bpy.ops.mesh.primitive_plane_add(size=250,location=(0,0,-.28));bpy.context.object.name='Chao_catalogo';bpy.context.object.data.materials.append(m)
    cam=bpy.data.cameras.new('Camera_catalogo');o=bpy.data.objects.new('Camera_catalogo',cam);sc.collection.objects.link(o);o.location=(44,-115,90)
    target=Vector((0,0,3));o.rotation_euler=(target-Vector(o.location)).to_track_quat('-Z','Y').to_euler();cam.type='ORTHO';cam.clip_end=1000;cam.ortho_scale=140;sc.camera=o
    sc.render.engine='CYCLES';sc.cycles.samples=48;sc.cycles.use_denoising=True
    try:
        prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
        for device in prefs.devices:device.use=device.type=='OPTIX'
        sc.cycles.device='GPU'
    except Exception:sc.cycles.device='CPU'
    sc.render.resolution_x=2400;sc.render.resolution_y=1600;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG'
    sc.view_settings.view_transform='AgX';sc.unit_settings.system='METRIC';sc.frame_set(1)
    sc['uso']='Catalogo isolado; as posicoes nao sao coordenadas de implantacao na ilha.'
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.shading.type='MATERIAL'
    bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Catalogo_10_estruturas.blend'),compress=True)
    sc.render.filepath=str(ROOT/'previews'/'catalogo.png');bpy.ops.render.render(write_still=True)
    print('CATALOGO_CONCLUIDO',flush=True)

if __name__=='__main__':
    if '--so-validar' not in sys.argv:prepare_library()
    paths=validate()
    if '--so-validar' not in sys.argv:catalog(paths)
