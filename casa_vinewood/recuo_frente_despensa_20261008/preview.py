"""Independent Blender composition of the installed geometry being replaced."""
import bpy,sys,json,math,addon_utils
from pathlib import Path
from mathutils import Vector,Quaternion
P=Path(__file__).resolve().parent;W=P.parent;R=W.parent;F=W/'fachada_garagem_20261008'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps',r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/sollumz']
bpy.ops.wm.open_mainfile(filepath=str(F/'mansao_entrada_garagem.blend'));addon_utils.enable('Sollumz',default_set=True)
from szio.gta5 import try_load_asset,AssetTarget,AssetFormat,AssetVersion
from Sollumz.ydr.ydrimport import create_drawable
from Sollumz.iecontext import ImportContext,ImportSettings,import_context_scope
spec=json.loads((P/'spec.json').read_text());origin=Vector(spec['origin']);scene=bpy.context.scene
names=['ch2_09b_hs05','ch2_09b_hs05_details','ch2_09b_l2','mansao_paredes','mansao_fachada_entrada','mansao_garagem_subsolo','mansao_pisos','mansao_escada']
for name in names:
    root=bpy.data.objects.get(name)
    if root:
        for obj in list(root.children_recursive)+[root]:bpy.data.objects.remove(obj,do_unlink=True)
# Remove the corresponding authoring parts as well, so a future export uses the open hall.
removed=[]
for obj in list(bpy.data.objects):
    if obj.name.startswith('Hall para Despensa'):
        removed.append(obj.name);bpy.data.objects.remove(obj,do_unlink=True)
for obj in list(bpy.data.objects):
    if obj.type!='MESH':continue
    points=[obj.matrix_world@Vector(p) for p in obj.bound_box]
    lo=[min(v[k] for v in points) for k in range(3)];hi=[max(v[k] for v in points) for k in range(3)]
    if all(lo[k]>=spec['removed_wall'][0][k]-.002 and hi[k]<=spec['removed_wall'][1][k]+.002 for k in range(3)):
        removed.append(obj.name);bpy.data.objects.remove(obj,do_unlink=True)
for c in bpy.data.collections:
    if any(s in c.name.lower() for s in ['porta','batente']):
        print('DOOR_COLLECTION',c.name,flush=True)
rows=json.loads((W/'work/near_house_entities.json').read_text())
col=bpy.data.collections.new('71_RECUO_CALCADA_DESPENSA');scene.collection.children.link(col)
imports=[]
for name in names:
    f=P/'stream'/(name+'.ydr')
    if not f.exists():f=R/'server-data/resources/cidade_mansao/stream'/(name+'.ydr')
    off=Vector(next(e['pos'] for e in rows if e['name']==name))-origin if name.startswith('ch2_') else Vector((0,0,0))
    imports.append((f,off,None))
map_=try_load_asset(P/'stream/ch2_roads_long_0.ymap');palm=next(e for e in map_.entities if str(e.archetype_name)=='prop_palm_sm_01d' and abs(e.position[0]-origin.x-14.03)<.01)
imports.append((P/'native/prop_palm_sm_01d.ydr',Vector(palm.position)-origin,Quaternion(tuple(palm.rotation))))
for f,off,rotation in imports:
    a=try_load_asset(f)
    with import_context_scope(ImportContext(f.stem,AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),W/'work/textures',ImportSettings(False,False,False,False))):root=create_drawable(a,name=f.stem)
    root.location=off
    if rotation:root.rotation_mode='QUATERNION';root.rotation_quaternion=rotation
    for obj in [root,*root.children_recursive]:
        for c in list(obj.users_collection):c.objects.unlink(obj)
        col.objects.link(obj)
        if 'bound' in str(obj.sollum_type).lower():obj.hide_render=True;obj.hide_viewport=True
# Save the actual shader materials before making disposable preview materials.
scene['revision']='Recuo calçada + remoção da divisória e porta Despensa'
scene['removed_authoring_objects']=removed
for obj in list(bpy.data.objects):
    if obj.type=='MESH' and 'despensa' in obj.name.lower() and 'porta' in obj.name.lower():obj.hide_render=True;obj.hide_viewport=True
bpy.ops.wm.save_as_mainfile(filepath=str(P/'mansao_recuo_despensa.blend'),compress=True)
for obj in col.objects:
    if obj.type!='MESH' or obj.hide_render:continue
    for slot in obj.material_slots:
        if not slot.material or not slot.material.use_nodes:continue
        old=slot.material;m=old.copy();slot.material=m;nt=m.node_tree;diff=nt.nodes.get('DiffuseSampler');im=diff.image if diff else None
        if im and not im.packed_file:
            name=im.filepath.replace('\\','/').rsplit('/',1)[-1]
            found=next((q for base in [P/'textures',W/'work/textures',W/'texturas',W/'parede_aparador_20261008/textures'] if (q:=base/name).exists()),None)
            if found:im=bpy.data.images.load(str(found),check_existing=True);im.pack()
            else:im=None
        bs=nt.nodes.new('ShaderNodeBsdfPrincipled');bs.inputs['Base Color'].default_value=(.65,.61,.54,1);bs.inputs['Roughness'].default_value=.65
        key=(im.name.lower() if im else '')+' '+old.name.lower()
        if im:
            node=nt.nodes.new('ShaderNodeTexImage');node.image=im;nt.links.new(node.outputs['Color'],bs.inputs['Base Color'])
            if 'palm' in key or 'leaf' in key:
                nt.links.new(node.outputs['Alpha'],bs.inputs['Alpha'])
        elif 'palm' in obj.name.lower():bs.inputs['Base Color'].default_value=(.11,.18,.055,1)
        if 'preto' in key:bs.inputs['Base Color'].default_value=(.018,.022,.024,1);bs.inputs['Roughness'].default_value=.38
        if 'led' in key:bs.inputs['Emission Color'].default_value=(1,.75,.42,1);bs.inputs['Emission Strength'].default_value=1.2
        if 'vidro' in key or 'glass' in key or 'wins' in key:bs.inputs['Transmission Weight'].default_value=.70;bs.inputs['Roughness'].default_value=.1
        output=next((n for n in nt.nodes if n.type=='OUTPUT_MATERIAL'),None)
        if output:
            for link in list(output.inputs['Surface'].links):nt.links.remove(link)
            nt.links.new(bs.outputs['BSDF'],output.inputs['Surface'])
for obj in scene.objects:
    if obj.type=='LIGHT' and obj.name.startswith('Degraus LED'):
        obj.hide_render=True
scene.render.resolution_x=1400;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.cycles.samples=16
def camera(pos,look,lens):
    scene.camera.location=pos;scene.camera.rotation_euler=(Vector(look)-scene.camera.location).to_track_quat('-Z','Y').to_euler();scene.camera.data.lens=lens
camera((8.5,28.5,1.65),(7.4,12.1,-.4),26)
scene.render.filepath=str(P/'fachada_recuada.png');bpy.ops.render.render(write_still=True)
camera((5.10,1.88,1.15),(3.95,4.8,.40),17)
light=bpy.data.lights.new('Luz prévia hall','AREA');light.energy=500;light.size=4;obj=bpy.data.objects.new('Luz prévia hall',light);scene.collection.objects.link(obj);obj.location=(4,1.2,2.2)
scene.render.filepath=str(P/'hall_sem_divisoria.png');bpy.ops.render.render(write_still=True)
print('PREVIEW_READY',removed,flush=True)
