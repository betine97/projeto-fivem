"""Review the native meshes from the three reported exterior viewpoints."""
import bpy,sys,json,addon_utils
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parent;W=P.parent;R=W.parent
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps',r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/sollumz']
bpy.ops.wm.open_mainfile(filepath=str(W/'recuo_frente_despensa_20261008/mansao_recuo_despensa.blend'));addon_utils.enable('Sollumz',default_set=True)
from szio.gta5 import try_load_asset,AssetTarget,AssetFormat,AssetVersion
from Sollumz.ydr.ydrimport import create_drawable
from Sollumz.iecontext import ImportContext,ImportSettings,import_context_scope
spec=json.loads((P/'spec.json').read_text());origin=Vector(spec['origin']);scene=bpy.context.scene
names=['ch2_09b_hs05','ch2_09b_hs05_details','ch2_09b_l2','mansao_fachada_entrada','mansao_garagem_subsolo']
roots=[obj.name for obj in bpy.data.objects if obj.type=='EMPTY' and any(obj.name==n or obj.name.startswith(n+'.') for n in names+['prop_palm_sm_01d'])]
for name in roots:
 root=bpy.data.objects.get(name)
 if root:
  for obj in list(root.children_recursive)+[root]:bpy.data.objects.remove(obj,do_unlink=True)
rows=json.loads((W/'work/near_house_entities.json').read_text())
col=bpy.data.collections.new('72_FECHAMENTOS_ACESSO');scene.collection.children.link(col)
for name in names:
 f=P/'stream'/(name+'.ydr');a=try_load_asset(f)
 off=Vector(next(e['pos'] for e in rows if e['name']==name))-origin if name.startswith('ch2_') else Vector((0,0,0))
 with import_context_scope(ImportContext(name,AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),W/'work/textures',ImportSettings(False,False,False,False))):root=create_drawable(a,name=name)
 root.location=off
 for obj in [root,*root.children_recursive]:
  for c in list(obj.users_collection):c.objects.unlink(obj)
  col.objects.link(obj)
  if 'bound' in str(obj.sollum_type).lower():obj.hide_render=True;obj.hide_viewport=True
scene['revision']='Fechos garagem/escada + coqueiro removido; limites físicos do tapete corrigidos'
bpy.ops.wm.save_as_mainfile(filepath=str(P/'mansao_acesso_reparado.blend'),compress=True)
for obj in col.objects:
 if obj.type!='MESH' or obj.hide_render:continue
 for slot in obj.material_slots:
  if not slot.material or not slot.material.use_nodes:continue
  old=slot.material;m=old.copy();slot.material=m;nt=m.node_tree;diff=nt.nodes.get('DiffuseSampler');im=diff.image if diff else None
  if im and not im.packed_file:
   name=im.filepath.replace('\\','/').rsplit('/',1)[-1]
   found=next((q for base in [P/'textures',W/'work/textures',W/'texturas'] if (q:=base/name).exists()),None)
   if found:im=bpy.data.images.load(str(found),check_existing=True);im.pack()
   else:im=None
  bs=nt.nodes.new('ShaderNodeBsdfPrincipled');bs.inputs['Base Color'].default_value=(.65,.61,.54,1);bs.inputs['Roughness'].default_value=.65
  key=(im.name.lower() if im else '')+' '+old.name.lower()
  if im:
   node=nt.nodes.new('ShaderNodeTexImage');node.image=im;nt.links.new(node.outputs['Color'],bs.inputs['Base Color'])
  if 'preto' in key:bs.inputs['Base Color'].default_value=(.018,.022,.024,1);bs.inputs['Roughness'].default_value=.38
  if 'led' in key:bs.inputs['Emission Color'].default_value=(1,.75,.42,1);bs.inputs['Emission Strength'].default_value=1.2
  if 'vidro' in key or 'glass' in key or 'wins' in key:bs.inputs['Transmission Weight'].default_value=.7;bs.inputs['Roughness'].default_value=.1
  output=next((n for n in nt.nodes if n.type=='OUTPUT_MATERIAL'),None)
  if output:
   for link in list(output.inputs['Surface'].links):nt.links.remove(link)
   nt.links.new(bs.outputs['BSDF'],output.inputs['Surface'])
scene.render.resolution_x=1300;scene.render.resolution_y=950;scene.render.resolution_percentage=100;scene.cycles.samples=12
for name,pos,look,lens in [('acesso_frente',(18.5,26,4.0),(9.2,13.8,-1.1),30),('escada_lateral',(.5,23,4.6),(5,15,-1.2),34),('encontros_superiores',(8.8,22,9.5),(8.2,14,-1.3),34)]:
 scene.camera.location=pos;scene.camera.rotation_euler=(Vector(look)-scene.camera.location).to_track_quat('-Z','Y').to_euler();scene.camera.data.lens=lens
 scene.render.filepath=str(P/(name+'.png'));bpy.ops.render.render(write_still=True)
print('ACCESS_PREVIEWS_READY',flush=True)
for obj in list(bpy.data.objects):bpy.data.objects.remove(obj,do_unlink=True)
bpy.data.orphans_purge(do_local_ids=True,do_linked_ids=False,do_recursive=True)
f=P/'stream/mansao_tapete_urso.ydr'
with import_context_scope(ImportContext(f.stem,AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),W/'work/textures',ImportSettings(False,False,False,False))):root=create_drawable(try_load_asset(f),name=f.stem)
bpy.context.scene['revision']='Tapete: colisao baixa da silhueta inteira e cabeca preservada; malha/UV/texturas originais'
bpy.ops.wm.save_as_mainfile(filepath=str(P/'tapete_urso_render_corrigido.blend'),compress=True)
