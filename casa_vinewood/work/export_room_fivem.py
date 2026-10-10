"""Export finishes and furniture while preserving supplied UVs."""
import bpy,sys,json,numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];W=ROOT/'casa_vinewood';OUT=W/'fivem';OUT.mkdir(exist_ok=True)
sys.path[:0]=[r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps',r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/sollumz',str(ROOT/'laboratorio_fivem/work/pydeps')]
import addon_utils
addon_utils.enable('Sollumz',default_set=True)
from PIL import Image
from Sollumz.sollumz_properties import SollumType
from Sollumz.tools.drawablehelper import convert_obj_to_model
from Sollumz.tools.meshhelper import mesh_add_missing_uv_maps,mesh_add_missing_color_attrs
from Sollumz.ydr.shader_materials import create_shader
from Sollumz.iecontext import ExportContext,ExportSettings,export_context_scope
from Sollumz.ydr.ydrexport import export_ydr
from szio.gta5 import AssetTarget,AssetFormat,AssetVersion
bpy.ops.wm.open_mainfile(filepath=str(W/'mansao_encaixada.blend'));s=bpy.context.scene
cols={k:next(c for c in bpy.data.collections if c.name.startswith(p)) for k,p in [('outer','01_'),('ground','02_'),('upper','03_'),('slabs','04_'),('stairs','05_'),('ceil','06_'),('furniture','10_'),('doorframes','12_'),('doors','13_'),('dining','15_'),('island','16_'),('pendants','17_')]}
for c in cols.values():c.hide_viewport=False
config=json.loads((W/'materiais_sala.json').read_text())
def texture(m,sampler,path):
 tx=m.node_tree.nodes[sampler];tx.image=bpy.data.images.load(str(path),check_existing=True);tx.texture_properties.embedded=True
 if sampler!='DiffuseSampler':tx.image.colorspace_settings.name='Non-Color'
 # This is a static interior. Direct UVs also keep the saved Blender preview
 # correct when opened without the optional animation property registration.
 if sampler=='DiffuseSampler':m.node_tree.links.new(m.node_tree.nodes['UVMap 0'].outputs['UV'],tx.inputs['Vector'])
def plain(name,color,family):
 m=create_shader('default.sps');m.name=name;m['finish_family']=family
 p=OUT/(name+'.dds');Image.new('RGBA',(4,4),(*color,255)).save(p,pixel_format='DXT5');texture(m,'DiffuseSampler',p);return m
styles={'ceiling':plain('mansao_teto_claro',(211,207,195),'ceiling'),'frame':plain('mansao_caixilho',(184,184,173),'frame'),'stone':plain('mansao_pedra',(67,70,65),'stone')}
wood=create_shader('normal.sps');wood.name='mansao_madeira_nativa';wood['finish_family']='wood';wood['uv_tile_m']=2.4
texture(wood,'DiffuseSampler',W/'work/textures/im_wood_panels_05.dds');texture(wood,'BumpSampler',W/'work/textures/im_wood_panels_05_n.dds');styles['wood']=wood
for key in ('marble','wall','brick','metal'):
 row=config[key];m=create_shader('normal.sps');m.name='mansao_'+Path(row['diffuse']).stem;m['finish_family']=key;m['uv_tile_m']=row['tile_m']
 texture(m,'DiffuseSampler',row['diffuse']);texture(m,'BumpSampler',row['normal'])
 for node in m.node_tree.nodes:
  if node.type=='BSDF_PRINCIPLED':node.inputs['Roughness'].default_value=row['roughness']
 for parameter,value in [('specularFalloffMult',(1-row['roughness'])*512),('specularIntensityMult',.15 if key in ('brick','wall') else .4)]:
  node=m.node_tree.nodes.get(parameter)
  if node is not None:node.set(0,value)
 styles[key]=m
glass=create_shader('glass.sps');glass.name='mansao_vidro';glass['finish_family']='glass'
Image.new('RGBA',(4,4),(170,200,210,48)).save(OUT/'mansao_vidro.dds',pixel_format='DXT5');texture(glass,'DiffuseSampler',OUT/'mansao_vidro.dds');styles['glass']=glass
for family in ('sofa','tv','dining','island','cylinder','linear'):
 m=create_shader('normal_spec.sps');m.name='mansao_'+family+'_meshy';m['finish_family']=family
 for sampler,suffix in [('DiffuseSampler','albedo'),('BumpSampler','normal'),('SpecSampler','spec')]:texture(m,sampler,W/'work/materiais'/(family+'_'+suffix+'.dds'))
 for parameter,value in [('specularIntensityMult',.22),('specularFalloffMult',35.),('specularFresnel',.12),('wetnessMultiplier',0.),('bumpiness',.75)]:
  node=m.node_tree.nodes.get(parameter)
  if node is not None:node.set(0,value)
 styles[family]=m
doorwood=create_shader('default.sps');doorwood.name='mansao_porta_madeira_mel';doorwood['finish_family']='doorwood';doorwood['uv_tile_m']=2.5
texture(doorwood,'DiffuseSampler',W/'work/materiais/porta_madeira_mel.dds');styles['doorwood']=doorwood
styles['doorgroove']=plain('mansao_friso_porta',(53,30,15),'doorgroove')
led=create_shader('emissive.sps');led.name='mansao_led_quente';led['finish_family']='led'
Image.new('RGBA',(4,4),(255,207,145,255)).save(OUT/'mansao_led_quente.dds',pixel_format='DXT5')
texture(led,'DiffuseSampler',OUT/'mansao_led_quente.dds');led.node_tree.nodes['emissiveMultiplier'].set(0,3.0);styles['led']=led
def fallback(src,group):
 old=src.data.materials[0].name.lower() if src.data.materials else ''
 if group=='mansao_mobiliario':return 'sofa'
 if group=='mansao_vidros':return 'glass'
 if src.name.startswith('Caixilhos'):return 'frame'
 if 'grafite' in old or any(t in src.name for t in ('montante','travessa','corrimao')):return 'metal'
 if group=='mansao_pisos' or group=='mansao_escada':return 'wood'
 if group=='mansao_teto':return 'ceiling'
 return 'stone' if 'pedra escura' in old else 'wall'
def project_uv(mesh):
 uv=mesh.uv_layers[0] if mesh.uv_layers else mesh.uv_layers.new(name='UVMap 0');uv.name='UVMap 0'
 for p in mesh.polygons:
  axis=max(range(3),key=lambda i:abs(p.normal[i]));axes=(0,1) if axis==2 else ((0,2) if axis==1 else (1,2));tile=mesh.materials[p.material_index].get('uv_tile_m',2.4)
  for i in p.loop_indices:
   co=mesh.vertices[mesh.loops[i].vertex_index].co;uv.data[i].uv=(co[axes[0]]/tile,co[axes[1]]/tile)
groups={'mansao_paredes':[o for o in cols['outer'].objects if not o.name.startswith('Vidros')]+list(cols['ground'].objects)+list(cols['upper'].objects)+list(cols['doorframes'].objects),'mansao_pisos':list(cols['slabs'].objects),'mansao_escada':list(cols['stairs'].objects),'mansao_teto':list(cols['ceil'].objects),'mansao_vidros':[o for o in cols['outer'].objects if o.name.startswith('Vidros')],'mansao_mobiliario':list(cols['furniture'].objects)}
groups.update(mansao_jantar=list(cols['dining'].objects),mansao_ilha=list(cols['island'].objects),mansao_pendentes=list(cols['pendants'].objects))
groups.update({o.name:[o] for o in cols['doors'].objects if o.type=='MESH' and o.get('dynamic_door')})
collision=[];report=[];assignments=[];targets=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
for name,objects in groups.items():
 root=bpy.data.objects.new(name,None);s.collection.objects.link(root);root.sollum_type=SollumType.DRAWABLE;parts=[];dg=bpy.context.evaluated_depsgraph_get()
 for src in objects:
  if src.type!='MESH':continue
  default=fallback(src,name);families=[m.get('finish_family',default) if m else default for m in src.data.materials] or [default]
  mesh=bpy.data.meshes.new_from_object(src.evaluated_get(dg),depsgraph=dg);mesh.transform(src.matrix_world)
  material_indices=[p.material_index for p in mesh.polygons]
  source_material_indices=[p.material_index for p in src.data.polygons]
  mesh.materials.clear()
  for family in families:mesh.materials.append(styles[family])
  for p,index in zip(mesh.polygons,material_indices):p.material_index=min(index,len(families)-1)
  if src.get('preserve_source_uv'):
   assert mesh.uv_layers,src.name;mesh.uv_layers[0].name='UVMap 0'
  else:project_uv(mesh)
  dynamic=bool(src.get('dynamic_door'))
  mesh.calc_loop_triangles();physical=name not in ('mansao_mobiliario','mansao_jantar','mansao_ilha','mansao_pendentes') and not dynamic and not(name=='mansao_escada' and 'degrau' in src.name)
  if physical:
   for t in mesh.loop_triangles:
    family=families[t.material_index];collision.append(dict(points=[list(mesh.vertices[i].co) for i in t.vertices],wood=family in ('wood','doorwood'),source=src.name,group=name,collision_material='MARBLE' if family=='marble' else 'WOOD_SOLID_POLISHED' if family in ('wood','doorwood') else 'CONCRETE'))
  src.data.materials.clear()
  for family in families:src.data.materials.append(styles[family])
  for p,index in zip(src.data.polygons,source_material_indices):p.material_index=min(index,len(families)-1)
  uv=src.data.uv_layers[0] if src.data.uv_layers else src.data.uv_layers.new(name='UVMap 0');uv.name='UVMap 0'
  for i,v in enumerate(mesh.uv_layers[0].data):uv.data[i].uv=v.uv
  assignments.append(dict(source=src.name,drawable=name,materials=families,preserve_source_uv=bool(src.get('preserve_source_uv'))))
  ob=bpy.data.objects.new(name+'_part',mesh);s.collection.objects.link(ob);ob.parent=root;mesh_add_missing_uv_maps(mesh);mesh_add_missing_color_attrs(mesh)
  shade=1.0 if any(k in ('marble','wall','brick','metal','sofa','tv','dining','island','cylinder','linear','led','doorwood','doorgroove') for k in families) else .65
  for attr in mesh.color_attributes:attr.data.foreach_set('color_srgb',np.tile(np.array([shade,shade,shade,1],dtype=np.float32),len(attr.data)))
  mesh_add_missing_color_attrs(src.data)
  for attr in src.data.color_attributes:attr.data.foreach_set('color_srgb',np.tile(np.array([shade,shade,shade,1],dtype=np.float32),len(attr.data)))
  convert_obj_to_model(ob);parts.append(ob)
 xyz=np.array([v.co for ob in parts for v in ob.data.vertices]);lo=xyz.min(0);hi=xyz.max(0)
 with export_context_scope(ExportContext(name,ExportSettings(targets=targets))):export_ydr(root).save(OUT,targets)
 row=dict(name=name,lo=lo.tolist(),hi=hi.tolist(),objects=len(parts),triangles=sum(len(o.data.loop_triangles) for o in parts))
 if objects[0].get('dynamic_door'):
  row.update(dynamic=True,collision_box_lo=list(objects[0]['collision_box_lo']),collision_box_hi=list(objects[0]['collision_box_hi']))
 report.append(row)
 for ob in parts:bpy.data.objects.remove(ob,do_unlink=True)
 bpy.data.objects.remove(root,do_unlink=True);print('EXPORTED',name,flush=True)
for prefix,group in [('09_','mansao_escada'),('11_','mansao_mobiliario')]:
 col=next(c for c in bpy.data.collections if c.name.startswith(prefix));col.hide_viewport=False;bpy.context.view_layer.update()
 for src in col.objects:
  src.data.calc_loop_triangles();kind=src.get('collision_material','WOOD_SOLID_POLISHED')
  collision.extend(dict(points=[list(src.matrix_world@src.data.vertices[i].co) for i in t.vertices],wood=kind=='WOOD_SOLID_POLISHED',source=src.name,group=src.get('collision_group',group),collision_material=kind) for t in src.data.loop_triangles)
 col.hide_viewport=True
(W/'colisoes_fivem.json').write_text(json.dumps(collision,indent=2),encoding='utf-8')
(W/'exportacao_fivem.json').write_text(json.dumps(dict(models=[r for r in report if not r.get('dynamic')],dynamic_models=[r for r in report if r.get('dynamic')],wood_source='Central upper hall and stairs: native wood; other walking floor areas: supplied marble',finish_assignments=assignments,revision='jantar-cozinha-2026-10-07'),indent=2),encoding='utf-8')
cols['ceil'].hide_viewport=True;cols['doors'].hide_viewport=True;s['status']='Mezanino de madeira, demais pisos em marmore, sofa ampliado sem frestas, TV e portas moveis exportados. Recarregamento FiveM pendente.'
for im in bpy.data.images:
 if im.has_data:
  try:im.pack()
  except Exception:pass
bpy.ops.wm.save_as_mainfile(filepath=str(W/'mansao_fivem_preparada.blend'));print('ROOM_FINISHES_AND_SOFA_EXPORTED',flush=True)
