import bpy,sys,math,struct,bmesh,json
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
root=Path(__file__).resolve().parent.parent;out=root/'jeep_exports';out.mkdir(exist_ok=True)
source=Path(r'C:\Users\erons\Downloads\Meshy_AI_WWII_U_S_Army_Jeep_1002142336_texture_fbx\Meshy_AI_WWII_U_S_Army_Jeep_1002142336_texture_fbx')
sys.path[:0]=[r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps',r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\sollumz']
import addon_utils
addon_utils.enable('Sollumz',default_set=True)
from Sollumz.sollumz_properties import LODLevel
from Sollumz.ydr.shader_materials import create_shader
from Sollumz.tools.meshhelper import mesh_add_missing_uv_maps,mesh_add_missing_color_attrs
from Sollumz.yft.yftexport import export_yft
from Sollumz.iecontext import ExportContext,ExportSettings,export_context_scope
from szio.gta5 import try_load_asset,save_asset,AssetTarget,AssetFormat,AssetVersion
bpy.ops.wm.open_mainfile(filepath=str(root/'work/donor.blend'))
rig=bpy.data.objects['rebel2'];rig.name='jeepmilitar';draw=bpy.data.objects['rebel2.mesh'];draw.name='jeepmilitar.mesh'
body=bpy.data.objects['bodyshell'];wheel=bpy.data.objects['wheel_lf.child']
native_wheel=wheel.data.copy()
for o in list(bpy.data.objects):
 if o.type=='MESH' and o.sollum_type=='sollumz_drawable_model' and o not in [body,wheel]:bpy.data.objects.remove(o,do_unlink=True)
# Rescale the proven native collision/physics rig for this compact open jeep.
scale=Matrix.Diagonal((.93,.76,.86,1))
for o in bpy.data.objects:
 if '.col' in o.name:
  o.hide_render=True
  if o.type=='MESH':o.data.transform(scale)
bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
for b in rig.data.edit_bones:
 b.head=scale@b.head;b.tail=scale@b.tail
bpy.ops.object.mode_set(mode='OBJECT')
for b in rig.pose.bones:
 for c in b.constraints:
  if c.type=='LIMIT_ROTATION':c.min_x=min(0,c.min_x);c.max_x=max(0,c.max_x)
before=set(bpy.data.objects)
bpy.ops.import_scene.fbx(filepath=str(next(source.glob('*.fbx'))))
imported=next(o for o in bpy.data.objects if o not in before and o.type=='MESH')
mesh=imported.data.copy();mesh.transform(imported.matrix_world)
# Source front points -X. GTA front points +Y, ground at -0.50.
for v in mesh.vertices:
 x,y,z=v.co;v.co=(y*1.25,-x*1.25,z*1.25-.50)
mesh.update()
def dds(suffix,name,size=2048):
 img=bpy.data.images.load(str(source/('Meshy_AI_WWII_U_S_Army_Jeep_1002142336_texture'+suffix+'.png')));img.scale(size,size)
 pixels=(np.array(img.pixels[:]).reshape(size,size,4)*255).clip(0,255).astype(np.uint8)
 header=[124,0x100f,size,size,size*4,0,0]+[0]*11+[32,0x41,0,32,0xff,0xff00,0xff0000,0xff000000]+[0x1000,0,0,0,0]
 path=out/(name+'.dds');path.write_bytes(b'DDS '+struct.pack('<31I',*header)+np.flipud(pixels).tobytes());bpy.data.images.remove(img)
 result=bpy.data.images.load(str(path));result.pack();return result
diff=dds('','jeepmilitar_diffuse');normal=dds('_normal','jeepmilitar_normal');spec=dds('_metallic','jeepmilitar_spec',1024)
normal.colorspace_settings.name='Non-Color';spec.colorspace_settings.name='Non-Color'
mat=create_shader('normal_spec.sps');mat.name='JEEP_MILITAR_PBR'
for name,img in [('DiffuseSampler',diff),('BumpSampler',normal),('SpecSampler',spec)]:
 n=mat.node_tree.nodes.get(name)
 if n:n.image=img;n.texture_properties.embedded=True
for name,value in [('specularIntensityMult',.22),('specularFalloffMult',100),('bumpiness',.35)]:
 n=mat.node_tree.nodes.get(name)
 if n:n.set_float(value)
tyre=wheel.data.materials[0].copy();tyre.name='JEEP_MILITAR_WHEEL_NATIVE'
for n in tyre.node_tree.nodes:
 if n.type=='TEX_IMAGE' and n.image:
  candidate=root/'work'/(n.image.name.split('.')[0]+'.dds')
  if candidate.exists():n.image=bpy.data.images.load(str(candidate),check_existing=True);n.image.pack()
  n.texture_properties.embedded=True
# Cut four circular wheel regions from the AI mesh, retaining the rear spare.
centers=[(-.71,1.255,-.155),(.71,1.255,-.155),(-.71,-.945,-.155),(.71,-.945,-.155)]
def wheel_id(co):
 for i,(x,y,z) in enumerate(centers):
  if co.x*x>0 and abs(co.x)>.535 and (co.y-y)**2+(co.z-z)**2<.46**2:return i
 return -1
assigned=[wheel_id(p.center) for p in mesh.polygons]
def subset(keep,name):
 m=mesh.copy();bm=bmesh.new();bm.from_mesh(m);bm.faces.ensure_lookup_table()
 bmesh.ops.delete(bm,geom=[f for f in bm.faces if not keep(assigned[f.index])],context='FACES');bm.to_mesh(m);bm.free();m.name=name
 if m.uv_layers:m.uv_layers[0].name='UVMap 0'
 m.materials.clear();m.materials.append(mat);mesh_add_missing_uv_maps(m);mesh_add_missing_color_attrs(m)
 for p in m.polygons:p.material_index=0
 for a in m.color_attributes:
  for d in a.data:d.color=(1,1,1,1)
 return m
bm=subset(lambda i:i<0,'JEEP_BODY');body.data=bm;body.vertex_groups.clear();g=body.vertex_groups.new(name='chassis');g.add(list(range(len(bm.vertices))),1,'REPLACE')
wm=native_wheel;wm.name='JEEP_NATIVE_OFFROAD_WHEEL';wm.transform(Matrix.Scale(.82,4));wm.materials[0]=tyre
wheel.data=wm
mesh_add_missing_uv_maps(wm)
for obj in [body,wheel]:
 for level in [LODLevel.VERYHIGH,LODLevel.HIGH,LODLevel.MEDIUM,LODLevel.LOW]:obj.sz_lods.get_lod(level).mesh=obj.data
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for name,pos in zip(['wheel_lf','wheel_rf','wheel_lr','wheel_rr'],centers):
 b=rig.data.edit_bones[name];delta=Vector(pos)-b.head;b.head+=delta;b.tail+=delta
for name,pos in [('seat_dside_f',(-.39,-.11,.10)),('seat_pside_f',(.39,-.11,.10)),('steeringwheel',(-.37,-.025,.63))]:
 b=rig.data.edit_bones.get(name)
 if b:delta=Vector(pos)-b.head;b.head+=delta;b.tail+=delta
bpy.ops.object.mode_set(mode='OBJECT')
for o in list(bpy.data.objects):
 if o in before:continue
 bpy.data.objects.remove(o,do_unlink=True)
exec(compile((root/'work/jeep_refinements.py').read_text(encoding='utf-8'),str(root/'work/jeep_refinements.py'),'exec'))
targets=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
with export_context_scope(ExportContext('jeepmilitar',ExportSettings(targets=targets))):export_yft(rig).save(out,targets)
txd=try_load_asset(root/'work/assets/rebel2.ytd');txd.textures.clear()
for name in ['jeepmilitar.yft','jeepmilitar_hi.yft']:
 a=try_load_asset(out/name);assert a and a.physics
 txd.textures.update(a.drawable.shader_group.embedded_textures)
 # Store shared textures in the external YTD to avoid duplicating them
 # in both fragment files.
 a.drawable.shader_group.embedded_textures.clear()
 save_asset(a,targets,out,name.removesuffix('.yft'))
save_asset(txd,targets,out,'jeepmilitar')
bpy.ops.wm.save_as_mainfile(filepath=str(root/'jeepmilitar.blend'))
print('JEEP_EXPORT_OK',len(bm.polygons),len(wm.polygons),len(txd.textures))
for name in ['wheel_rf','wheel_lr','wheel_rr']:
 clone=wheel.copy();clone.data=wheel.data.copy();bpy.context.collection.objects.link(clone);clone.constraints.clear();clone.modifiers.clear();clone.parent=None;clone.matrix_world=rig.matrix_world@rig.pose.bones[name].matrix
 if name in ['wheel_rf','wheel_rr']:clone.scale.x=-1
for name,loc in [('Key',(4,5,6)),('Fill',(-4,2,4))]:
 d=bpy.data.lights.new(name,'AREA');d.energy=900;d.size=5;o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);o.location=loc;o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler()
d=bpy.data.cameras.new('Jeep preview');cam=bpy.data.objects.new('Jeep preview',d);bpy.context.collection.objects.link(cam);cam.location=(-5,6,3.5);cam.rotation_euler=(Vector((0,0,.3))-cam.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=5.3
sc=bpy.context.scene;sc.camera=cam;sc.render.engine='CYCLES';sc.cycles.samples=16;sc.render.resolution_x=1100;sc.render.resolution_y=850;sc.render.resolution_percentage=100;sc.world.color=(.25,.25,.25);sc.render.filepath=str(root/'jeepmilitar_previa.png');bpy.ops.render.render(write_still=True)
