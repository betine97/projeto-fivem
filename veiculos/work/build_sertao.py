"""Sertao: reference-inspired body kit and inert turret on a local GTA vehicle rig."""
import bpy,sys,math,struct,json,shutil
import numpy as np
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parent.parent;out=root/'exports';out.mkdir(exist_ok=True)
sys.path[:0]=[r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps',r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\sollumz']
import addon_utils
addon_utils.enable('Sollumz',default_set=True)
from Sollumz.tools.drawablehelper import convert_obj_to_model
from Sollumz.tools.meshhelper import mesh_add_missing_uv_maps,mesh_add_missing_color_attrs
from Sollumz.ydr.shader_materials import create_shader
from Sollumz.sollumz_properties import LODLevel
from Sollumz.yft.yftexport import export_yft
from Sollumz.iecontext import ExportContext,ExportSettings,export_context_scope
from szio.gta5 import AssetTarget,AssetFormat,AssetVersion,try_load_asset
bpy.ops.wm.open_mainfile(filepath=str(root/'work/donor.blend'))
rig=bpy.data.objects['rebel2'];rig.name='sertao';drawable=bpy.data.objects['rebel2.mesh'];drawable.name='sertao.mesh'
# Keep native doors, glazing, interior, lights, wheels, suspension and collisions.
for o in list(bpy.data.objects):
 if o.type=='MESH' and o.name.startswith('extra_'):bpy.data.objects.remove(o,do_unlink=True)
for o in bpy.data.objects:
 if '.col' in o.name:o.hide_render=True;o.hide_set(True)
materials={}
def material(name,color,weather=False):
 size=256 if weather else 4;rng=np.random.default_rng(sum(map(ord,name)))
 rgb=np.ones((size,size,3))*np.array(color)
 if weather:
  noise=rng.random((size,size));coarse=np.repeat(np.repeat(rng.random((16,16)),16,0),16,1)
  wear=(noise>.985)|(coarse>.86)&(noise>.72)
  rgb*=.72+.38*coarse[:,:,None];rgb[wear]=np.array((.30,.27,.18))
 pixels=np.concatenate((np.clip(rgb*255,0,255).astype(np.uint8),np.full((size,size,1),255,dtype=np.uint8)),2)
 path=out/(name+'.dds');header=[124,0x100f,size,size,size*4,0,0]+[0]*11+[32,0x41,0,32,0xff,0xff00,0xff0000,0xff000000]+[0x1000,0,0,0,0]
 path.write_bytes(b'DDS '+struct.pack('<31I',*header)+pixels.tobytes())
 m=create_shader('default.sps');m.name=name;n=m.node_tree.nodes['DiffuseSampler'];n.image=bpy.data.images.load(str(path));n.texture_properties.embedded=True
 materials[name]=m;return m
def image_to_dds(name,path):
 src=bpy.data.images.load(str(path))
 w,h=src.size
 if w==h:
  tw=th=1024
 elif w>h:
  tw,th=2048,512
 else:
  tw,th=512,2048
 src.scale(tw,th)
 pixels=(np.array(src.pixels[:]).reshape(th,tw,4)*255).clip(0,255).astype(np.uint8)
 if 'cano' in name:
  white=(pixels[:,:,0]>225)&(pixels[:,:,1]>225)&(pixels[:,:,2]>225)
  pixels[white]=np.array([28,27,24,255],dtype=np.uint8)
 dds=out/(name+'.dds')
 header=[124,0x100f,th,tw,tw*4,0,0]+[0]*11+[32,0x41,0,32,0xff,0xff00,0xff0000,0xff000000]+[0x1000,0,0,0,0]
 dds.write_bytes(b'DDS '+struct.pack('<31I',*header)+pixels.tobytes())
 bpy.data.images.remove(src)
 return dds
def image_material(name,path):
 m=create_shader('default.sps');m.name=name
 n=m.node_tree.nodes['DiffuseSampler']
 img=bpy.data.images.load(str(image_to_dds(name,path)));img.pack()
 n.image=img;n.texture_properties.embedded=True
 materials[name]=m;return m
olive=material('sertao_olive',(.16,.18,.10),True);metal=material('sertao_steel',(.085,.095,.09),True)
black=material('sertao_black',(.025,.03,.03));silver=material('sertao_silver',(.47,.49,.43));brass=material('sertao_brass',(.56,.38,.11));copper=material('sertao_copper',(.51,.23,.075));lamp=material('sertao_lamp',(.68,.71,.63));amber=material('sertao_amber',(.8,.26,.015))
ref_download=Path(r'C:\Users\erons\Downloads')
ref_temp=Path(r'C:\Users\erons\AppData\Local\Temp')
tyre_tex=image_material('sertao_pneu_textura',ref_download/'3ad23b8e-07b9-4e4a-803d-7df161d8fdf0.png')
ammo_tex=image_material('sertao_caixa_municao_textura',ref_download/'0628ae35-15e0-4708-86b3-27c0ab76abbd.png')
barrel_tex=image_material('sertao_cano_textura',ref_temp/'codex-clipboard-33b45168-2db8-44b4-8545-72dd5255fade.png')
grille_tex=image_material('sertao_grade_textura',ref_temp/'codex-clipboard-2ef368bf-8b41-4186-9f2c-9b194555862e.png')
lamp_tex=image_material('sertao_lanterna_textura',ref_temp/'codex-clipboard-e32742a2-c652-4193-a8de-ca81b0862a17.png')
round_tex=image_material('sertao_cartucho_textura',ref_temp/'codex-clipboard-74c70839-0fe8-43c6-ad18-c369d0cc76c4.png')
# Preserve the tyre shader (wheel rendering requires the vehicle layout).
native_tyre=bpy.data.objects['wheel_lf.child'].data.materials[0].copy()
native_tyre.name='sertao_pneu_vehicle'
native_tyre.node_tree.nodes['DiffuseSampler'].image=tyre_tex.node_tree.nodes['DiffuseSampler'].image
native_tyre.node_tree.nodes['DiffuseSampler'].texture_properties.embedded=True
# Replace slots on every LOD, not just the currently displayed mesh.
for o in bpy.data.objects:
 if o.type!='MESH' or o.sollum_type!='sollumz_drawable_model':continue
 for level in LODLevel:
  mesh=o.sz_lods.get_lod(level).mesh
  if mesh is None:continue
  for i,m in enumerate(mesh.materials):
   if m and '[PRIMARY]' in m.name:mesh.materials[i]=ammo_tex
   if o.name=='wheel_lf.child' and m and 'tyrewall' in m.name.lower():mesh.materials[i]=native_tyre
# Recolour the donor paint while retaining native window/interior/wheel shaders.
for o in bpy.data.objects:
 if o.type=='MESH' and o.sollum_type=='sollumz_drawable_model':
  for slot in o.material_slots:
   if slot.material and '[PRIMARY]' in slot.material.name:slot.material=olive
   if o.name=='wheel_lf.child':
    for slot in o.material_slots:
     if slot.material and 'tyrewall' in slot.material.name.lower():slot.material=native_tyre
   if o.name in {'headlight_l','headlight_r','taillight_l','taillight_r'}:
    for slot in o.material_slots:slot.material=lamp_tex
parts=[]
def finish(o,name,mat,bone='chassis',bevel=0):
 o.name=name;o.data.materials.append(mat)
 bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
 if bevel:
  b=o.modifiers.new('Arestas arredondadas','BEVEL');b.width=bevel;b.segments=2;bpy.ops.object.modifier_apply(modifier=b.name)
 # Sollumz exports UVMap 0 specifically; primitive UVMap was previously ignored.
 if o.data.uv_layers:o.data.uv_layers[0].name='UVMap 0'
 mesh_add_missing_uv_maps(o.data);mesh_add_missing_color_attrs(o.data)
 if mat==lamp_tex:
  for loop in o.data.loops:
   co=o.data.vertices[loop.vertex_index].co
   o.data.uv_layers['UVMap 0'].data[loop.index].uv=((co.x-(.635 if co.x>0 else -.635))/.27+.5,(co.z-.52)/.27+.5)
 if mat==round_tex:
  # Copper tips sample the top strip, brass cases sample the lower region.
  for uv in o.data.uv_layers['UVMap 0'].data:
   uv.uv.y=(.80+.18*uv.uv.y) if 'Ponta' in name else (.08+.58*uv.uv.y)
 for a in o.data.color_attributes:
  for v in a.data:v.color=(1,1,1,1)
 convert_obj_to_model(o);o.parent=drawable
 g=o.vertex_groups.new(name=bone);g.add(list(range(len(o.data.vertices))),1,'REPLACE')
 mod=o.modifiers.new('Vehicle skeleton','ARMATURE');mod.object=rig
 parts.append(o);return o
def box(name,pos,dim,mat=olive,bone='chassis',bevel=.015):
 bpy.ops.mesh.primitive_cube_add(size=1,location=pos);o=bpy.context.object;o.dimensions=dim
 return finish(o,name,mat,bone,bevel)
def cylinder(name,a,b,r,mat=metal,bone='chassis',vertices=20,r2=None):
 a,b=Vector(a),Vector(b);d=b-a
 bpy.ops.mesh.primitive_cone_add(vertices=vertices,radius1=r,radius2=r if r2 is None else r2,depth=d.length,location=(a+b)/2)
 o=bpy.context.object;o.rotation_euler=d.to_track_quat('Z','Y').to_euler()
 for p in o.data.polygons:p.use_smooth=len(p.vertices)==4
 return finish(o,name,mat,bone)
# Angular hood, front grille, protected round lamps, bullbar and tow eyes.
box('Capo angular Sertao',(0,1.73,.785),(1.50,1.10,.075),olive,'bonnet',.025)
box('Grade base',(0,2.34,.53),(1.55,.08,.45),grille_tex)
for z in [.37,.44,.51,.58,.65]:box('Grade horizontal',(0,2.392,z),(1.03,.035,.021),grille_tex,bevel=.008)
for side in [-1,1]:
 x=side*.635
 cylinder('Aro farol',(x,2.375,.52),(x,2.425,.52),.151,metal)
 cylinder('Farol circular',(x,2.425,.52),(x,2.437,.52),.127,lamp_tex)
 box('Seta dianteira',(side*.817,2.36,.575),(.09,.07,.13),amber)
 cylinder('Para choque subida',(side*.81,2.51,.18),(side*.81,2.51,.66),.04)
 cylinder('Para choque lateral',(side*.81,2.51,.66),(side*.49,2.51,.66),.04)
 cylinder('Protecao grade',(side*.49,2.51,.30),(side*.49,2.51,.66),.035,grille_tex)
 box('Degrau lateral',(side*.89,.47,.02),(.19,1.30,.055),metal)
 cylinder('Trilho cacamba',(side*.875,-.44,.795),(side*.875,-2.41,.795),.024,olive)
 for y in [-.52,-.96,-1.4,-1.84,-2.3]:
  box('Nervura lateral cacamba',(side*.883,y,.55),(.045,.042,.42),olive,bevel=.009)
  cylinder('Gancho carga',(side*.9,y,.74),(side*.9,y,.68),.012,metal,vertices=10)
 for y in [1.32,.30]:box('Piso antiderrapante',(side*.89,y,.055),(.18,.06,.012),black)
box('Para choque dianteiro',(0,2.50,.24),(1.92,.18,.18),metal)
cylinder('Barra frontal',( -.81,2.51,.66),(.81,2.51,.66),.04)
box('Para choque traseiro',(0,-2.48,.15),(1.90,.18,.19),metal)
box('Painel traseiro cacamba',(0,-2.442,.57),(1.48,.035,.43),olive,'boot',.008)
# Dedicated yaw/pitch/muzzle bones: inert now, ready to address by name later.
bpy.ops.object.select_all(action='DESELECT');rig.hide_set(False);rig.select_set(True);bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for name,parent,pos in [('sertao_turret_yaw','chassis',(0,-1.15,1.30)),('sertao_turret_pitch','sertao_turret_yaw',(0,-1.15,1.61)),('sertao_muzzle','sertao_turret_pitch',(0,.92,1.68))]:
 b=rig.data.edit_bones.new(name);b.head=pos;b.tail=Vector(pos)+Vector((0,.08,0));b.parent=rig.data.edit_bones[parent]
bpy.ops.object.mode_set(mode='OBJECT')
for i,name in enumerate(['sertao_turret_yaw','sertao_turret_pitch','sertao_muzzle']):
 rig.data.bones[name].bone_properties.tag=60010+i
# Visual gun only. These are external game-art shapes, not a functional mechanism.
box('Base pedestal',(0,-1.15,.39),(.49,.52,.08),metal)
cylinder('Coluna pedestal',(0,-1.15,.41),(0,-1.15,1.30),.105,olive)
for x,y in [(-.37,-1.62),(.37,-1.62),(0,-.61)]:cylinder('Escora pedestal',(x,y,.36),(0,-1.15,1.16),.035,olive)
for z in [1.28,1.32]:cylinder('Anel giro',(0,-1.15,z),(0,-1.15,z+.035),.16,metal)
yaw='sertao_turret_yaw';pitch='sertao_turret_pitch'
box('Garfo torre',(0,-1.15,1.43),(.26,.25,.16),metal,yaw)
box('Caixa arma',(0,-1.18,1.65),(.21,.76,.22),metal,pitch,.018)
box('Tampa superior',(0,-1.18,1.775),(.23,.75,.035),metal,pitch,.008)
cylinder('Camisa perfurada',(0,-.80,1.68),(0,-.39,1.68),.083,barrel_tex,pitch)
for y in [-.73,-.61,-.49]:
 for side in [-1,1]:cylinder('Perfuracao visual camisa',(side*.075,y,1.68),(side*.084,y,1.68),.026,black,pitch,12)
cylinder('Cano',(0,-.4,1.68),(0,.82,1.68),.034,barrel_tex,pitch)
cylinder('Freio boca',(0,.80,1.68),(0,.97,1.68),.052,barrel_tex,pitch)
cylinder('Interior boca',(0,.971,1.68),(0,.973,1.68),.033,black,pitch)
for y in [.84,.89,.94]:
 for x in [-1,1]:box('Ranhura boca',(x*.051,y,1.68),(.005,.028,.036),black,pitch,.002)
for y in [-1.42,-.85]:
 box('Base mira',(0,y,1.804),(.11,.12,.035),metal,pitch)
 box('Mira',(0,y,1.85),(.045,.035,.075),metal,pitch)
for x in [-.17,.17]:
 cylinder('Suporte punho',(0,-1.56,1.66),(x,-1.67,1.66),.018,metal,pitch)
 cylinder('Punho traseiro',(x,-1.67,1.55),(x,-1.67,1.78),.025,black,pitch)
box('Caixa municao',(-.30,-1.08,1.40),(.33,.39,.32),ammo_tex,pitch)
box('Tampa caixa municao',(-.30,-1.08,1.57),(.35,.41,.025),ammo_tex,pitch)
box('Fecho caixa',(-.48,-1.08,1.43),(.02,.07,.09),metal,pitch)
for i in range(7):
 x=-.16-i*.023;z=1.7-i*.037
 cylinder('Cartucho visual',(x,-1.05,z),(x,-.94,z),.016,round_tex,pitch,12)
 cylinder('Ponta visual',(x,-.94,z),(x,-.9,z),.016,round_tex,pitch,12,0)
 cylinder('Elo fita',(x,-1.015,z),(x,-.995,z),.019,metal,pitch,12)
for x in [-.117,.117]:
 for y in [-1.48,-1.31,-1.14,-.97]:cylinder('Rebite arma',(x,y,1.69),(x*1.04,y,1.69),.009,silver,pitch,8)
# Smaller models retain the turret silhouette. Native chassis already has its LODs.
exec(compile((root/'work/remodel_sertao.py').read_text(encoding='utf-8'), str(root/'work/remodel_sertao.py'), 'exec'))
for o in parts:
 o.sz_lods.get_lod(LODLevel.VERYHIGH).mesh=o.data
 o.sz_lods.get_lod(LODLevel.MEDIUM).mesh=o.data
 o.sz_lods.get_lod(LODLevel.LOW).mesh=o.data
rig['project']='Sertao - carroceria adaptada e torre visual autoral';rig['turret_functional']=False
rig['source']='Rebel2 da instalacao local: chassi, cabine, rodas, interior e colisoes; novas pecas modeladas neste script.'
notes=bpy.data.texts.new('LEIA-ME Sertao');notes.write('SERTAO\nComando FiveM: veiculo sertao\nBase local Rebel2 preserva conducao e entrada. Carroceria adaptada, grade, farois, para-choques e torre autorais inspirados nas referencias.\nTorre sem disparo. Ossos: sertao_turret_yaw, sertao_turret_pitch, sertao_muzzle.\nNao redistribuir os componentes extraidos do GTA.\n')
for i,filename in enumerate(['a5798003-068b-4f02-88ba-4acfec5cef69.png','f8fdde1d-44d5-45c4-8352-34f6759e3372.png','b54a3842-9578-47aa-8049-1834217b8cd9.png','c7540b50-4314-4600-883f-dc4bb69da26b.png']):
 ref=bpy.data.objects.new('Referencia '+str(i+1),None);bpy.context.collection.objects.link(ref);ref.empty_display_type='IMAGE';ref.data=bpy.data.images.load(str(Path(r'C:\Users\erons\Downloads')/filename));ref.data.pack();ref.empty_display_size=4;ref.location=(8+i*5,0,2)
# Export a real add-on vehicle, not a prop attached to an invisible vehicle.
import runpy
runpy.run_path(str(root/'work/repair_assembly.py'))['repair_assembly']()
runpy.run_path(str(root/'work/finish_materials.py'))['apply_finish']()
targets=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
with export_context_scope(ExportContext('sertao',ExportSettings(targets=targets))):
 bundle=export_yft(rig);assert bundle;bundle.save(out,targets)
shutil.copyfile(root/'work/assets/rebel2.ytd',out/'sertao.ytd')
asset=try_load_asset(out/'sertao.yft');assert asset is not None
report={'model':'sertao','native_yft_readback':True,'custom_meshes':len(parts),'turret_functional':False,'in_game_validated':False}
(out/'validation.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(root/'sertao.blend'))
# Studio rendering; save separately so export source retains game materials.
exec(compile((root/'work/studio_materials.py').read_text(encoding='utf-8'), str(root/'work/studio_materials.py'), 'exec'))
for o in bpy.data.objects:
 if o.type=='MESH' and o.sollum_type=='sollumz_drawable_model':o.hide_render=False
# The native rig instantiates one wheel geometry at four bones in-game.
wheel=bpy.data.objects.get('wheel_lf.child')
if wheel:
 for name in ['wheel_rf','wheel_lr','wheel_rr']:
  clone=wheel.copy();clone.data=wheel.data.copy();bpy.context.collection.objects.link(clone);clone.modifiers.clear();clone.constraints.clear();clone.parent=None
  clone.matrix_world=rig.matrix_world@rig.pose.bones[name].matrix
for o in bpy.data.objects:
 if '.col' in o.name:o.hide_render=True
for n,p,power in [('Key',(3,4,6),1700),('Fill',(-4,1,4),1300),('Rim',(1,-5,5),1600)]:
 d=bpy.data.lights.new(n,'AREA');d.energy=power;d.shape='DISK';d.size=5;o=bpy.data.objects.new(n,d);bpy.context.collection.objects.link(o);o.location=p;o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler()
d=bpy.data.cameras.new('Camera Sertao');cam=bpy.data.objects.new('Camera Sertao',d);bpy.context.collection.objects.link(cam);cam.location=(5,7,3.4);cam.rotation_euler=(Vector((0,-.12,.55))-cam.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=6.65
sc=bpy.context.scene;sc.camera=cam;sc.render.engine='CYCLES';sc.cycles.samples=24;sc.render.resolution_x=1400;sc.render.resolution_y=1000;sc.render.resolution_percentage=100;sc.world.color=(.2,.2,.2)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.61));plane=bpy.context.object;m=bpy.data.materials.new('Studio floor');m.diffuse_color=(.15,.17,.19,1);plane.data.materials.append(m)
sc.render.filepath=str(root/'sertao_previa.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(root/'sertao_studio.blend'))
print('SERTAO_EXPORT_OK',report)
