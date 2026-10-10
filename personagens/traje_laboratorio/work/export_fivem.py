import bpy,sys,addon_utils,bmesh,math,json,struct,shutil
import numpy as np
from pathlib import Path
sys.path[:0]=[r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps',r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\sollumz']
addon_utils.enable('Sollumz',default_set=True)
from Sollumz.sollumz_properties import LODLevel
from Sollumz.ydr.shader_materials import create_shader
from Sollumz.tools.meshhelper import mesh_add_missing_uv_maps,mesh_add_missing_color_attrs
from Sollumz.ydd.yddexport import export_ydd
from Sollumz.iecontext import ExportContext,ExportSettings,export_context_scope
from szio.gta5 import try_load_asset,save_asset,AssetTarget,AssetFormat,AssetVersion,AssetTextureDictionary
root=Path(__file__).resolve().parents[1];out=root/'exports';out.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(root/'TRAJE_LABORATORIO.blend'))
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=4;sc.render.bake.margin=8
rig=bpy.data.objects['MP_M_FREEMODE_01_RIG']
for pb in rig.pose.bones:pb.matrix_basis.identity()
pieces=list(bpy.data.collections['TRAJE_LAB_AUTORAL'].objects)
for o in bpy.data.objects:
 if o not in pieces and o.type=='MESH':o.hide_render=True
for o in pieces:o.hide_set(False);o.hide_render=False;o.hide_select=False
groups={
 'jbib_008_u':lambda n: n in {'MACACAO_TRONCO','ABA_ZIPER','PATCH_PRETO','BORDA_PATCH','DISCO_AMARELO','NUCLEO_RADIACAO','COSTURA_CINTURA'} or n.startswith(('COSTURA_ZIPER','SETOR_RADIACAO','ELASTICO_PUNHO')),
 'lowr_007_u':lambda n:n=='MACACAO_PERNAS' or n.startswith('ELASTICO_TORNOZELO'),
 'uppr_000_r':lambda n:n=='LUVAS_AZUIS',
 'feet_000_u':lambda n:n.startswith('COBRE_BOTA'),
 'berd_020_u':lambda n:n in {'CAPUZ_BRANCO','VEDACAO_VISOR','COSTURA_CAPUZ','VISOR_TRANSPARENTE'},
}
targets=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
reports=[]
def write_dds(img,name):
 w,h=img.size;px=(np.asarray(img.pixels[:]).reshape(h,w,4)*255).clip(0,255).astype(np.uint8)
 hdr=[124,0x100f,h,w,w*4,0,0]+[0]*11+[32,0x41,0,32,255,65280,16711680,4278190080]+[0x1000,0,0,0,0]
 p=out/(name+'.dds');p.write_bytes(b'DDS '+struct.pack('<31I',*hdr)+np.flipud(px).tobytes())
 loaded=bpy.data.images.load(str(p),check_existing=True);loaded.name=name+'.dds';loaded.pack();return loaded
def constant(name,color,size=64):
 im=bpy.data.images.new(name,width=size,height=size);im.colorspace_settings.name='Non-Color';im.pixels[:]=list(color)*(size*size);return write_dds(im,name)
for filename,predicate in groups.items():
 print('PREPARE_COMPONENT',filename,flush=True)
 objs=[o for o in pieces if predicate(o.name)]
 assert objs,filename
 bpy.ops.object.select_all(action='DESELECT')
 clones=[]
 for src in objs:
  o=src.copy();o.data=src.data.copy();sc.collection.objects.link(o);o.hide_set(False);o.hide_render=False;clones.append(o)
  bpy.context.view_layer.objects.active=o;o.select_set(True)
  for mod in list(o.modifiers):
   if mod.type=='ARMATURE':o.modifiers.remove(mod)
   else:bpy.ops.object.modifier_apply(modifier=mod.name)
  o.parent=None;o.select_set(False)
 for o in clones:o.select_set(True)
 bpy.context.view_layer.objects.active=clones[0];bpy.ops.object.join();work=bpy.context.object
 # Slim the game mesh while keeping folds, seams and independently weighted fingers.
 if filename.startswith(('jbib','lowr')):
  mod=work.modifiers.new('LOD_HIGH_OPTIMIZADO','DECIMATE');mod.ratio=.40;mod.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=mod.name)
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.004);bpy.ops.object.mode_set(mode='OBJECT')
 for uv in list(work.data.uv_layers)[1:]:work.data.uv_layers.remove(uv)
 work.data.uv_layers[0].name='UVMap 0'
 glass_ids={i for i,m in enumerate(work.data.materials) if m and m.name.startswith('VISOR_PVC')}
 mats=list(work.data.materials)
 size=2048 if filename.startswith('jbib') else (1024 if filename.startswith(('lowr','berd')) else 512)
 diffname=filename.split('_')[0]+'_diff_'+filename.split('_')[1]+'_a_'+('whi' if filename.endswith('_r') else 'uni')
 images={}
 for kind in ['diff','normal']:
  image=bpy.data.images.new(filename+'_'+kind,width=size,height=size,alpha=True)
  image.colorspace_settings.name='sRGB' if kind=='diff' else 'Non-Color'
  for m in mats:
   node=m.node_tree.nodes.new('ShaderNodeTexImage');node.name='BAKE_TARGET';node.image=image;m.node_tree.nodes.active=node
  if kind=='diff':
   sc.render.bake.use_pass_direct=False;sc.render.bake.use_pass_indirect=False;sc.render.bake.use_pass_color=True
   # PVC is baked as a clear white film, alpha is set separately below.
   restore=[]
   for i in glass_ids:
    m=mats[i];output=m.node_tree.nodes.get('Material Output');socket=output.inputs['Surface'];old=socket.links[0].from_socket;restore.append((m,old));m.node_tree.links.new(m.node_tree.nodes.get('Principled BSDF').outputs[0],socket)
   bpy.ops.object.bake(type='DIFFUSE')
   for m,old in restore:m.node_tree.links.new(old,m.node_tree.nodes.get('Material Output').inputs['Surface'])
   images[kind]=write_dds(image,diffname)
  else:
   bpy.ops.object.bake(type='NORMAL');images[kind]=write_dds(image,filename.split('_')[0]+'_normal_'+filename.split('_')[1])
  for m in mats:
   for node in list(m.node_tree.nodes):
    if node.name=='BAKE_TARGET':m.node_tree.nodes.remove(node)
  bpy.data.images.remove(image)
 normal=images['normal'];normal.colorspace_settings.name='Non-Color'
 spec=constant(filename.split('_')[0]+'_spec_'+filename.split('_')[1],(.20,.20,.20,0))
 reserved=create_shader('ped_default.sps');reserved.name=filename+'_RESERVADO'
 mat=create_shader('ped.sps');mat.name=filename+'_TECIDO'
 for key,img in [('DiffuseSampler',images['diff']),('BumpSampler',normal),('SpecSampler',spec)]:
  node=mat.node_tree.nodes.get(key);node.image=img;node.texture_properties.embedded=key!='DiffuseSampler'
 for name,value in [('specularIntensityMult',.22),('specularFalloffMult',35),('bumpiness',.65)]:
  node=mat.node_tree.nodes.get(name)
  if node:node.set_float(value)
 pmat=None
 if glass_ids:
  pmat=create_shader('ped_alpha.sps');pmat.name='VISOR_PVC_FIVEM'
  for key,img in [('DiffuseSampler',constant('berd_visor_diff',(.85,.93,1,.075))),('BumpSampler',constant('berd_visor_normal',(.5,.5,1,1))),('SpecSampler',constant('berd_visor_spec',(.7,.7,.7,0)))]:
   n=pmat.node_tree.nodes.get(key);n.image=img;n.texture_properties.embedded=True
  for name,value in [('specularIntensityMult',1),('specularFalloffMult',120),('bumpiness',0)]:
   node=pmat.node_tree.nodes.get(name)
   if node:node.set_float(value)
 oldids=[p.material_index for p in work.data.polygons]
 work.data.materials.clear();work.data.materials.append(reserved);work.data.materials.append(mat)
 if pmat:work.data.materials.append(pmat)
 for p,old in zip(work.data.polygons,oldids):p.material_index=2 if old in glass_ids else 1;p.use_smooth=True
 mesh_add_missing_uv_maps(work.data);mesh_add_missing_color_attrs(work.data)
 for attr in work.data.color_attributes:
  for datum in attr.data:datum.color=(1,.21586,0,1) if attr.name.endswith('0') else (0,0,0,0)
 # Import the exact native dictionary wrapper for the component, including skeleton tags.
 before=set(bpy.data.objects)
 bpy.ops.sollumz.import_assets(directory=str(root/'source'),files=[{'name':filename+'.ydd'}],use_custom_settings=True,dwd_import_external_skeleton='FROM_DIR')
 imported=set(bpy.data.objects)-before
 dictionary=next(o for o in imported if o.type=='ARMATURE' and o.parent is None)
 model=next(o for o in imported if o.type=='MESH');model.data=work.data.copy();model.vertex_groups.clear()
 for vg in work.vertex_groups:model.vertex_groups.new(name=vg.name)
 for v in work.data.vertices:
  for g in v.groups:
   if g.weight<=0:continue
   name=work.vertex_groups[g.group].name
   if name not in dictionary.data.bones:
    matches=[b.name for b in dictionary.data.bones if b.name.rsplit('_',1)[0]==name.rsplit('_',1)[0]]
    assert len(matches)==1,(name,matches)
    name=matches[0]
   if name not in model.vertex_groups:model.vertex_groups.new(name=name)
   model.vertex_groups[name].add([v.index],g.weight,'REPLACE')
 model.data=model.data.copy()
 lod_counts={}
 for lod,ratio in [(LODLevel.HIGH,1),(LODLevel.MEDIUM,.58),(LODLevel.LOW,.30),(LODLevel.VERYLOW,.15)]:
  if ratio==1:m=model.data
  else:
   temp=model.copy();temp.data=model.data.copy();sc.collection.objects.link(temp)
   for mod in list(temp.modifiers):temp.modifiers.remove(mod)
   bpy.ops.object.select_all(action='DESELECT');temp.select_set(True);bpy.context.view_layer.objects.active=temp
   mod=temp.modifiers.new('SIMPLIFICAR','DECIMATE');mod.ratio=ratio;mod.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=mod.name);m=temp.data
   bpy.data.objects.remove(temp,do_unlink=True)
  model.sz_lods.get_lod(lod).mesh=m;lod_counts[str(lod)]=len(m.polygons)
 # Native component naming includes a drawable suffix understood by the ped streamer.
 drawable=model.parent;drawable.name=filename+'.#dd'
 dictionary.name=filename
 with export_context_scope(ExportContext(filename,ExportSettings(targets=targets))):bundle=export_ydd(dictionary)
 txd=AssetTextureDictionary(textures={diffname:__import__('szio.gta5',fromlist=['EmbeddedTexture']).EmbeddedTexture(name=diffname,width=size,height=size,data=__import__('szio.types',fromlist=['DataSource']).DataSource.create(out/(diffname+'.dds')))})
 bundle.save(out,targets);save_asset(txd,targets,out,diffname)
 roundtrip=try_load_asset(out/(filename+'.ydd'));assert len(roundtrip.drawables)==1
 d=next(iter(roundtrip.drawables.values()))
 report={'component':filename,'vertices':len(model.data.vertices),'lod_faces':lod_counts,'embedded_textures':list(d.shader_group.embedded_textures),'diffuse':diffname,'shaders':[s.preset_filename for s in d.shader_group.shaders]}
 reports.append(report);print('EXPORT_COMPONENT_OK',json.dumps(report),flush=True)
 for o in list(imported):bpy.data.objects.remove(o,do_unlink=True)
 bpy.data.objects.remove(work,do_unlink=True)
(out/'validation.json').write_text(json.dumps(reports,indent=2))
print('EXPORT_ALL_OK',flush=True)
