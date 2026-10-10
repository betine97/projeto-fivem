import bpy,sys,json,math,addon_utils
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parent;W=P.parent;R=W.parent
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps',r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/sollumz']
bpy.ops.wm.open_mainfile(filepath=str(W/'parede_aparador_20261008/mansao_parede_aparador.blend'));addon_utils.enable('Sollumz',default_set=True)
from szio.gta5 import try_load_asset,AssetTarget,AssetFormat,AssetVersion
from Sollumz.ydr.ydrimport import create_drawable
from Sollumz.iecontext import ImportContext,ImportSettings,import_context_scope
spec=json.loads((P/'spec.json').read_text());scene=bpy.context.scene
for o in list(bpy.data.objects):
    if o.type in ['CAMERA','LIGHT']:bpy.data.objects.remove(o,do_unlink=True)
for c in bpy.data.collections:
    if c.name.startswith(('01_','02_','03_','90_REFERENCIA','00_FACHADA','08_')) or 'REFERENCIA_NATIVA' in c.name:c.hide_render=True;c.hide_viewport=True
col=bpy.data.collections.new('70_ACESSO_PRINCIPAL_GARAGEM_INSTALACAO');scene.collection.children.link(col)
rows=json.loads((W/'work/near_house_entities.json').read_text());origin=Vector(spec['origin'])
imports=[]
for name in ['ch2_09b_hs05','ch2_09b_hs05_details','ch2_09b_l2']:
    imports.append((P/'stream'/(name+'.ydr'),Vector(next(e['pos'] for e in rows if e['name']==name))-origin,W/'work/textures',False))
imports.append((P/'stream/mansao_paredes.ydr',Vector((0,0,0)),W/'texturas',False))
road=json.loads((P/'road_samples.json').read_text())['entity'];imports.append((P/'native/ch2_roads_rd_26.ydr',Vector(road['pos'])-origin,W/'work/textures',False))
for i,name in enumerate(spec['models']):
    off=Vector(spec['door_hinge'] if i==2 else spec['gate_hinge'] if i==3 else [0,0,0]);imports.append((P/'stream'/(name+'.ydr'),off,P/'textures',i==3))
for f,off,tex,gate in imports:
    a=try_load_asset(f)
    with import_context_scope(ImportContext(f.stem,AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),tex,ImportSettings(False,False,False,False))):root=create_drawable(a,name=f.stem)
    root.location=off
    if gate:root.rotation_euler.x=-math.pi/2
    for o in [root,*root.children_recursive]:
        for c in list(o.users_collection):c.objects.unlink(o)
        col.objects.link(o)
        if str(o.sollum_type).lower().find('bound')>=0:o.hide_render=True;o.hide_viewport=True
# Repair missing preview image paths in this independent scene only.
for m in list(bpy.data.materials):
    if not m.use_nodes:continue
    nt=m.node_tree;diff=nt.nodes.get('DiffuseSampler');im=diff.image if diff else None
    if im:
        name=im.filepath.replace('\\','/').rsplit('/',1)[-1]
        candidates=[P/'textures'/name,W/'work/textures'/name,W/'texturas'/name,W/'parede_aparador_20261008/textures'/name]
        found=next((q for q in candidates if q.exists()),None)
        if found:
            try:im=bpy.data.images.load(str(found),check_existing=True);im.pack()
            except Exception:im=None
        elif not im.packed_file:im=None
    # Keep exporter materials intact on disk; use a simple PBR output for the preview.
    bs=nt.nodes.new('ShaderNodeBsdfPrincipled');bs.inputs['Base Color'].default_value=(.60,.56,.48,1);bs.inputs['Roughness'].default_value=.66
    txname=(im.name.lower() if im else '')+' '+m.name.lower()
    if im:
        node=nt.nodes.new('ShaderNodeTexImage');node.image=im;nt.links.new(node.outputs['Color'],bs.inputs['Base Color'])
    elif 'roof' in txname:bs.inputs['Base Color'].default_value=(.23,.21,.17,1)
    elif 'ground' in txname or 'roads' in txname:bs.inputs['Base Color'].default_value=(.17,.17,.16,1)
    if 'preto' in txname:bs.inputs['Base Color'].default_value=(.018,.022,.024,1);bs.inputs['Roughness'].default_value=.38
    if 'vidro' in txname or 'glass' in txname or 'wins' in txname:
        bs.inputs['Transmission Weight'].default_value=.75;bs.inputs['Roughness'].default_value=.10
    if 'led' in txname or 'emissive' in str(getattr(m.shader_properties,'filename','')).lower():
        bs.inputs['Emission Color'].default_value=(1,.75,.42,1);bs.inputs['Emission Strength'].default_value=1.2
    output=nt.nodes.get('Material Output') or next((n for n in nt.nodes if n.type=='OUTPUT_MATERIAL'),None)
    if output:
        for link in list(output.inputs['Surface'].links):nt.links.remove(link)
        nt.links.new(bs.outputs['BSDF'],output.inputs['Surface'])
for obj in list(bpy.data.objects):
    if obj.type=='LIGHT':bpy.data.objects.remove(obj,do_unlink=True)
world=bpy.data.worlds.new('Entardecer projeto acesso');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.25,.30,.39,1);world.node_tree.nodes['Background'].inputs[1].default_value=.35;scene.world=world
def light(name,pos,energy,color,size=3,kind='AREA',look=None):
    data=bpy.data.lights.new(name,kind);data.energy=energy;data.color=color
    if kind=='AREA':data.shape='DISK';data.size=size
    obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj);obj.location=pos
    if look:obj.rotation_euler=(Vector(look)-obj.location).to_track_quat('-Z','Y').to_euler()
    return obj
sun=light('Sol suave',(0,0,20),1.8,(1,.86,.69),kind='SUN');sun.rotation_euler=(.55,-.50,-.7);sun.data.angle=.12
light('Preenchimento ceu',(5,23,11),1800,(.70,.82,1),12,look=(3,6,0))
for x in [7.9,11.2]:
    for y in [.2,3.5,6.8]:light('Garagem painel branco',(x,y,-1.43),120,(1,.94,.83),2.3,look=(x,y,-4.2))
for x in [3.84,5.485]:light('Entrada arandela',(x,7.84,.83),35,(1,.70,.36),kind='POINT')
for y in [15,16,17,18]:light('Degraus LED',(4.7,y,-.8-(y-14.6)*.54+.18),17,(1,.73,.41),kind='POINT')
for y in [12.5,16.5]:
    for x in [6.57,12.6]:light('Rampa balizador',(x,y,-3.2),25,(1,.73,.41),kind='POINT')
scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=True;scene.render.resolution_x=1400;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
try:
    pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
    for dev in pref.devices:dev.use=dev.type!='CPU'
    if any(d.use for d in pref.devices):scene.cycles.device='GPU'
except Exception:pass
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=0
def camera(name,pos,look,lens):
    bpy.ops.object.camera_add(location=pos);obj=bpy.context.object;obj.name=name;obj.rotation_euler=(Vector(look)-obj.location).to_track_quat('-Z','Y').to_euler();obj.data.lens=lens;scene.camera=obj;return obj
camera('Fachada entrada e garagem',(5,34.5,4.1),(4,7.9,.75),31)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'mansao_entrada_garagem.blend'),compress=True)
scene.render.filepath=str(P/'fachada_garagem_blender.png');bpy.ops.render.render(write_still=True)
camera('Garagem subterranea',(10.9,8.40,-2.40),(8.9,1.4,-3.15),21);scene.render.filepath=str(P/'garagem_interna_blender.png');bpy.ops.render.render(write_still=True)
print('GARAGE_PREVIEW_READY',flush=True)
