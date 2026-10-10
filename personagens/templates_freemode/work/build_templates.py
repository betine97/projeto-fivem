import bpy,sys,addon_utils,json,math,hashlib,struct
from pathlib import Path
from mathutils import Vector,Quaternion
sys.path[:0]=[r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps',r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\sollumz']
addon_utils.enable('Sollumz',default_set=True)
from szio.gta5 import try_load_asset
root=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(root/'work/imported.blend'))
sc=bpy.context.scene
sc.unit_settings.system='METRIC';sc.unit_settings.scale_length=1
sc.render.fps=30;sc.frame_start=1;sc.frame_end=60
def collection(name):
 c=bpy.data.collections.new(name);sc.collection.children.link(c);return c
def move(o,c):
 for old in list(o.users_collection):old.objects.unlink(o)
 c.objects.link(o)
original=collection('00_ORIGINAIS_GTA_NAO_EDITAR')
originals=list(bpy.data.objects)
for o in originals:move(o,original)
bodycol=collection('01_CORPO_REFERENCIA')
rigcol=collection('02_ESQUELETO_ORIGINAL')
newcol=collection('03_CRIAR_ROUPAS_AQUI')
preview=collection('90_ESTUDIO_REFERENCIAS')
texdir=root/'source/textures';texdir.mkdir(exist_ok=True)
for pattern in ['head_diff_000_a*','uppr_diff_015_a*','lowr_diff_014_a*','feet_diff_005_a*']:
 for p in (root/'source').glob(pattern):
  for name,tex in try_load_asset(p).textures.items():
   with tex.data.open() as stream:(texdir/(name+'.dds')).write_bytes(stream.read())
   img=bpy.data.images.load(str(texdir/(name+'.dds')),check_existing=True);img.pack()
   for mat in bpy.data.materials:
    if not mat.node_tree:continue
    for node in mat.node_tree.nodes:
     if node.type=='TEX_IMAGE' and node.image and node.image.name.split('.')[0]==name:node.image=img
for img in bpy.data.images:
 if img.source=='FILE' and img.has_data and not img.packed_file:
  try:img.pack()
  except Exception:pass
source_rig=bpy.data.objects['hash_976FBF04']
rig=source_rig.copy();rig.data=source_rig.data.copy();rigcol.objects.link(rig);rig.parent=None;rig.name='MP_M_FREEMODE_01_RIG';rig.show_in_front=True;rig.data.display_type='OCTAHEDRAL'
rig['origem']='head_000_r.ydd: esqueleto nativo da cabeca 000, corpo compativel com mp_m_freemode_01.yft';rig['aviso']='Preservar nomes, hierarquia, tags e pose de repouso dos ossos.'
meshes=[];proof=[]
def fingerprint(mesh):
 h=hashlib.sha256()
 for v in mesh.vertices:h.update(struct.pack('<3f',*v.co))
 for p in mesh.polygons:h.update(struct.pack('<'+'I'*len(p.vertices),*p.vertices))
 for uv in mesh.uv_layers:
  for d in uv.data:h.update(struct.pack('<2f',*d.uv))
 return h.hexdigest()
for src in [o for o in originals if o.type=='MESH']:
 mod=next(m for m in src.modifiers if m.type=='ARMATURE')
 oldrig=mod.object
 used={src.vertex_groups[g.group].name for v in src.data.vertices for g in v.groups if g.weight>0}
 maxdiff=max(max(abs(a-b) for ra,rb in zip(b.matrix_local,rig.data.bones[b.name].matrix_local) for a,b in zip(ra,rb)) for b in oldrig.data.bones if b.name in used)
 print('RIG_MATRIX_DIFF',src.name,maxdiff)
 assert maxdiff<0.0001,(src.name,maxdiff)
 o=src.copy();o.data=src.data.copy();bodycol.objects.link(o)
 world=src.matrix_world.copy();o.parent=rig;o.matrix_world=world
 for m in o.modifiers:
  if m.type=='ARMATURE':m.object=rig
 component=next(m.name.split('_diff')[0] for m in o.data.materials if '_diff' in m.name)
 o.name={'head':'REF_CABECA_000','uppr':'REF_TRONCO_015','lowr':'REF_PERNAS_BERMUDA_014','feet':'REF_PES_005'}[component]
 o['componente_original']=component;o['somente_referencia']=True
 assert fingerprint(o.data)==fingerprint(src.data)
 assert all([(g.group,g.weight) for g in a.groups]==[(g.group,g.weight) for g in b.groups] for a,b in zip(src.data.vertices,o.data.vertices))
 proof.append(dict(object=o.name,vertices=len(o.data.vertices),polygons=len(o.data.polygons),geometry_uv_sha256=fingerprint(o.data),weights_preserved=True,bone_matrix_max_difference=maxdiff))
 meshes.append(o)
original.hide_render=True;original.hide_viewport=True
for o in originals:o.hide_select=True
sc.world.color=(.08,.08,.08)
sc.render.engine='CYCLES';sc.cycles.samples=24;sc.cycles.use_denoising=True
sc.render.resolution_x=850;sc.render.resolution_y=1000;sc.render.resolution_percentage=100
sc.view_settings.view_transform='AgX'
points=[o.matrix_world@v.co for o in meshes for v in o.data.vertices]
floor=min(v.z for v in points);top=max(v.z for v in points);mid=(floor+top)/2
cd=bpy.data.cameras.new('Referencia');cam=bpy.data.objects.new('CAM_FRENTE',cd);preview.objects.link(cam);sc.camera=cam;cd.type='ORTHO';cd.ortho_scale=2.25
def aim(o,pos,target):o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
aim(cam,(0,-6,mid),(0,0,mid))
for name,pos,power,size in [('Principal',(-3,-4,4),400,4),('Preenchimento',(3,-2,1),200,3),('Recorte',(0,3,3),350,3)]:
 d=bpy.data.lights.new(name,'AREA');o=bpy.data.objects.new(name,d);preview.objects.link(o);d.energy=power;d.shape='DISK';d.size=size;aim(o,pos,(0,0,mid))
# Cross-section perimeter of torso only; count a closed welded loop, not arms.
def section(z):
 obj=next(o for o in meshes if o['componente_original']=='uppr');m=obj.data;m.calc_loop_triangles();segments={}
 for tri in m.loop_triangles:
  vs=[obj.matrix_world@m.vertices[i].co for i in tri.vertices];hits=[]
  for a,b in zip(vs,vs[1:]+vs[:1]):
   if (a.z<z<=b.z) or (b.z<z<=a.z):hits.append(a+(b-a)*((z-a.z)/(b.z-a.z)))
  if len(hits)==2:
   keys=[tuple(round(v,5) for v in p[:2]) for p in hits]
   if keys[0]!=keys[1]:segments[tuple(sorted(keys))]=(hits[1]-hits[0]).length
 adjacency={}
 for a,b in segments:adjacency.setdefault(a,set()).add(b);adjacency.setdefault(b,set()).add(a)
 components=[];unseen=set(adjacency)
 while unseen:
  todo=[unseen.pop()];group=set(todo)
  while todo:
   for n in adjacency[todo.pop()]:
    if n in unseen:unseen.remove(n);group.add(n);todo.append(n)
  components.append(group)
 central=[c for c in components if min(p[0] for p in c)<0<max(p[0] for p in c)]
 center=max(central,key=lambda c:max(p[0] for p in c)-min(p[0] for p in c))
 assert all(len(adjacency[p])==2 for p in center),('open section',z)
 return {'perimeter_cm':round(sum(l for (a,b),l in segments.items() if a in center and b in center)*100,1),'width_cm':round((max(p[0] for p in center)-min(p[0] for p in center))*100,1),'depth_cm':round((max(p[1] for p in center)-min(p[1] for p in center))*100,1),'z_original_m':z,'height_from_soles_cm':round((z-floor)*100,1)}
bones=rig.data.bones
measure={'character':'mp_m_freemode_01','variant':'head 000 / uppr 015 / lowr 014 / feet 005','units':'1 Blender unit = 1 metre','height_cm':round((top-floor)*100,1),'rest_pose_hand_span_cm':round((max(p.x for p in points)-min(p.x for p in points))*100,1),'shoulder_joint_span_cm':round((bones['SKEL_L_UpperArm'].head_local-bones['SKEL_R_UpperArm'].head_local).length*100,1),'arm_joint_chain_cm':round(((bones['SKEL_L_UpperArm'].head_local-bones['SKEL_L_Forearm'].head_local).length+(bones['SKEL_L_Forearm'].head_local-bones['SKEL_L_Hand'].head_local).length)*100,1),'chest_section':section(.32),'abdomen_section':section(.08),'floor_z_original_m':floor,'head_top_z_original_m':top,'note':'Sections at fixed Z in original rest pose. Lower pelvis is covered by original shorts; no nude hip circumference inferred. Shoulder measure is between joints, not outer skin.'}
(root/'medidas.json').write_text(json.dumps(measure,indent=2,ensure_ascii=False),encoding='utf-8')
report={'rig_bones':len(bones),'original_meshes_unchanged':True,'meshes':proof,'skeleton':[{'name':b.name,'parent':b.parent.name if b.parent else None,'head':list(b.head_local),'matrix':[list(row) for row in b.matrix_local]} for b in bones]}
(root/'work/validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
readme='''BASE ORIGINAL MP_M_FREEMODE_01\n\nCorpo e esqueleto importados dos arquivos GTA locais, sem reconstrução por IA.\nCabeça padrão 000: não inclui a mistura de rosto de um jogador específico.\nA bermuda 014 cobre a pelve; não há corpo nu reconstruído sob ela.\n128 ossos, nomes, tags, repouso, UV e pesos originais preservados.\nFrente = -Y, cima = +Z, escala = 1 metro. Origem GTA preservada junto à pelve.\n\nROUPAS: crie na coleção 03; use o corpo como referência sem deformá-lo.\nNão exporte câmera, luzes ou arquivo de originais como parte da peça.\nA roupa final precisa de retopologia, UV, materiais, pesos, LOD e validação no jogo.\n\nANIMAÇÕES: use Pose Mode no MP_M_FREEMODE_01_RIG.\nNOVA_ANIMACAO tem uma chave neutra no quadro 1, timeline 30 FPS.\nTESTE_FLEXAO é somente um teste técnico arquivado; não é um movimento final.\nNão use Apply Pose as Rest Pose nem altere os ossos em Edit Mode.\nExportar futuramente para YCD com Sollumz; testar a animação no FiveM.\n\n00_ORIGINAIS fica oculto e preserva a estrutura importada para consulta.\nLeia LEIA-ME.md e PROMPT_ROUPAS.txt nesta pasta.\n'''
txt=bpy.data.texts.new('LEIA-ME');txt.write(readme)
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   area.spaces.active.region_3d.view_distance=2.8;area.spaces.active.region_3d.view_location=(0,0,mid)
   area.spaces.active.region_3d.view_rotation=Quaternion((1,0,0),math.pi/2)
   area.spaces.active.shading.type='MATERIAL'
   area.spaces.active.overlay.show_floor=False
preview.hide_viewport=True
for o in meshes:o.hide_select=True
rig.hide_select=True
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.wm.save_as_mainfile(filepath=str(root/'01_BASE_ROUPAS.blend'))
for label,loc in [('frente',(0,-6,mid)),('lateral',(6,0,mid)),('costas',(0,6,mid))]:
 aim(cam,loc,(0,0,mid));sc.render.filepath=str(root/f'referencia_{label}.png');bpy.ops.render.render(write_still=True)
aim(cam,(2,-5,mid+.3),(0,0,mid))
rig.hide_select=False;rig.select_set(True);bpy.context.view_layer.objects.active=rig
for o in meshes:o.hide_select=False
rig.animation_data_create()
act=bpy.data.actions.new('TESTE_FLEXAO');act.use_fake_user=True;rig.animation_data.action=act
for f in [1,15,30]:
 for name,angle in [('SKEL_L_Forearm',-.75),('SKEL_R_Forearm',-.6),('SKEL_L_Calf',.45)]:
  pb=rig.pose.bones[name];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=Quaternion((0,1,0),angle if f==15 else 0);pb.keyframe_insert(data_path='rotation_quaternion',frame=f,group=name)
sc.frame_set(15);bpy.context.view_layer.update()
dg=bpy.context.evaluated_depsgraph_get();displacement={}
for o in meshes:
 ev=o.evaluated_get(dg);em=ev.to_mesh();displacement[o.name]=max((a.co-b.co).length for a,b in zip(em.vertices,o.data.vertices));ev.to_mesh_clear()
assert displacement['REF_TRONCO_015']>.02 and displacement['REF_PERNAS_BERMUDA_014']>.02,displacement
(root/'work/pose_validation.json').write_text(json.dumps(displacement,indent=2))
sc.render.filepath=str(root/'teste_esqueleto.png');bpy.ops.render.render(write_still=True)
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
newact=bpy.data.actions.new('NOVA_ANIMACAO');newact.use_fake_user=True;rig.animation_data.action=newact
for pb in rig.pose.bones:
 pb.rotation_mode='QUATERNION';pb.keyframe_insert(data_path='rotation_quaternion',frame=1,group=pb.name)
sc.frame_set(1)
rig.pose.bones['SKEL_ROOT'].keyframe_insert(data_path='location',frame=1,group='SKEL_ROOT')
aim(cam,(0,-6,mid),(0,0,mid))
bpy.ops.object.mode_set(mode='POSE')
bpy.ops.wm.save_as_mainfile(filepath=str(root/'02_BASE_ANIMACOES.blend'))
print('COMPLETE',json.dumps(measure))

