import bpy,sys,json,math
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood';OUT=W/'decor_fivem'
sys.path[:0]=[r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps',r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/sollumz',str(R/'laboratorio_fivem/work/pydeps')]
import addon_utils,numpy as np
addon_utils.enable('Sollumz',default_set=True)
from Sollumz.sollumz_properties import SollumType
from Sollumz.tools.drawablehelper import convert_obj_to_model
from Sollumz.tools.meshhelper import mesh_add_missing_uv_maps,mesh_add_missing_color_attrs
from Sollumz.ydr.shader_materials import create_shader
from Sollumz.iecontext import ExportContext,ExportSettings,export_context_scope,ImportContext,ImportSettings,import_context_scope
from Sollumz.ydr.ydrexport import export_ydr
from Sollumz.ydr.ydrimport import create_drawable
from szio.gta5 import AssetTarget,AssetFormat,AssetVersion,try_load_asset
bpy.ops.wm.open_mainfile(filepath=str(W/'mansao_iluminada.blend'))
col=bpy.data.collections.new('20_TAPETE_E_QUADROS');bpy.context.scene.collection.children.link(col)
with bpy.data.libraries.load(str(W/'work/tapete_otimizado.blend'),link=False) as (source,dest):dest.objects=source.objects
rug=next(o for o in dest.objects if o.type=='MESH');col.objects.link(rug)
m=create_shader('normal_spec.sps');m.name='mansao_tapete_tecido';m['finish_family']='rug'
for sampler,suffix in [('DiffuseSampler','albedo'),('BumpSampler','normal'),('SpecSampler','spec')]:
 tx=m.node_tree.nodes[sampler];im=bpy.data.images.load(str(W/'work/materiais'/('rug_'+suffix+'.dds')),check_existing=False)
 if suffix!='albedo':im.colorspace_settings.name='Non-Color'
 assert len(im.pixels)>0;im.pack();tx.image=im;tx.texture_properties.embedded=True
for parameter,value in [('specularIntensityMult',.1),('specularFalloffMult',12.),('specularFresnel',.04),('wetnessMultiplier',0.),('bumpiness',.55)]:
 node=m.node_tree.nodes.get(parameter)
 if node is not None:node.set(0,value)
rug.data.materials.clear();rug.data.materials.append(m)
for p in rug.data.polygons:p.material_index=0
rug.data.uv_layers[0].name='UVMap 0'
m.node_tree.links.new(m.node_tree.nodes['UVMap 0'].outputs['UV'],m.node_tree.nodes['DiffuseSampler'].inputs['Vector'])
mesh_add_missing_uv_maps(rug.data);mesh_add_missing_color_attrs(rug.data)
for attr in rug.data.color_attributes:attr.data.foreach_set('color_srgb',np.tile(np.array([1,1,1,1],dtype=np.float32),len(attr.data)))
root=bpy.data.objects.new('mansao_tapete_sala',None);bpy.context.scene.collection.objects.link(root);root.sollum_type=SollumType.DRAWABLE
ob=bpy.data.objects.new('mansao_tapete_sala_mesh',rug.data.copy());bpy.context.scene.collection.objects.link(ob);ob.data.transform(rug.matrix_world);ob.parent=root;convert_obj_to_model(ob)
targets=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
with export_context_scope(ExportContext('mansao_tapete_sala',ExportSettings(targets=targets))):export_ydr(root).save(OUT,targets)
bpy.data.objects.remove(ob,do_unlink=True);bpy.data.objects.remove(root,do_unlink=True)
cfg=json.loads((W/'decoracao_iluminacao.json').read_text());cfg['revision']='tapete-quadros-noite-2026-10-08';cfg['night_multiplier']=4.0
cfg['night_schedule']=dict(full_start=20,full_end=5,fade_in_start=18,fade_out_end=8)
for q in cfg['spots']:q['rgb']=[255,211,156]
cfg['rug']=json.loads((W/'tapete_sala.json').read_text());cfg['rug']['model']='mansao_tapete_sala'
artbounds=json.loads((W/'work/decor_art_bounds.json').read_text())
placements=[('Quadro hall escritorio 1','apa_mp_h_acc_artwallm_02',[-8,2.239,.92],.8,0),('Quadro hall escritorio 2','apa_mp_h_acc_artwallm_03',[-4.6,2.239,.92],.8,0),('Quadro hall sala','apa_mp_h_acc_artwalll_01',[-6.6,-.739,.92],.65,math.pi),('Quadro jantar','apa_mp_h_acc_artwallm_04',[5.45,-.961,.92],.75,0)]
cfg['paintings']=[]
for label,model,position,scale,heading in placements:
 f=W/'work/decor_art'/(model+'.ydr');a=try_load_asset(f)
 with import_context_scope(ImportContext(f.stem,targets[0],f.parent,ImportSettings(False,False,False,False))):root=create_drawable(a,name=label)
 root.location=position;root.rotation_euler.z=heading;root.scale=(scale,)*3
 for o in [root,*root.children_recursive]:
  for c in list(o.users_collection):c.objects.unlink(o)
  col.objects.link(o)
  if o.type=='MESH' and 'bound' in str(o.sollum_type).lower():o.hide_render=True
 cfg['paintings'].append(dict(name=label,model=model,position=position,scale=scale,heading=heading,quaternion=[math.cos(heading/2),0,0,-math.sin(heading/2)],bounds=artbounds[model],floor_z=-.8))
for m in bpy.data.materials:
 if not m.use_nodes:continue
 for n in m.node_tree.nodes:
  if n.type!='TEX_IMAGE' or not n.image:continue
  name=Path(n.image.filepath.replace('//','')).stem.lower();p=W/'work/decor_art'/(name+'.dds')
  if p.exists():
   im=bpy.data.images.load(str(p),check_existing=False)
   if n.name!='DiffuseSampler':im.colorspace_settings.name='Non-Color'
   assert len(im.pixels)>0;im.pack();n.image=im
(W/'decoracao_iluminacao.json').write_text(json.dumps(cfg,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(W/'mansao_iluminada.blend'))
print('RUG_AND_FOUR_NATIVE_PAINTINGS_READY',flush=True)
