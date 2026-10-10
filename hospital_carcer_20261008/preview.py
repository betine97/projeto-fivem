import bpy,json,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(P/'hospital_carcer_editavel.blend'));scene=bpy.context.scene;spec=json.loads((P/'spec.json').read_text())
for m in bpy.data.materials:
 if not m.use_nodes:continue
 nt=m.node_tree;node=nt.nodes.get('DiffuseSampler');im=node.image if node else None;key=m.name.replace('hospital_','');bs=nt.nodes.new('ShaderNodeBsdfPrincipled');bs.inputs['Roughness'].default_value=.6
 if im:
  tx=nt.nodes.new('ShaderNodeTexImage');tx.image=im;nt.links.new(tx.outputs['Color'],bs.inputs['Base Color'])
  uv=nt.nodes.new('ShaderNodeUVMap');uv.uv_map='UVMap 0';nt.links.new(uv.outputs['UV'],tx.inputs['Vector'])
 if key in ['gold','metal']:bs.inputs['Metallic'].default_value=.75;bs.inputs['Roughness'].default_value=.30
 if key=='glass':bs.inputs['Transmission Weight'].default_value=.75;bs.inputs['Roughness'].default_value=.12
 if key=='led':bs.inputs['Emission Color'].default_value=(1,1,.92,1);bs.inputs['Emission Strength'].default_value=2
 output=next(n for n in nt.nodes if n.type=='OUTPUT_MATERIAL');nt.links.new(bs.outputs[0],output.inputs['Surface'])
world=bpy.data.worlds.new('Ceu hospital');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.58,.70,.84,1);world.node_tree.nodes['Background'].inputs[1].default_value=.45;scene.world=world
sun=bpy.data.lights.new('Sol','SUN');sun.energy=2.2;sun.angle=.12;o=bpy.data.objects.new('Sol',sun);scene.collection.objects.link(o);o.rotation_euler=(.45,-.30,-.55)
for q in spec['lights']:
 if q['model'] not in ['hc_terreo','hc_exterior']:continue
 light=bpy.data.lights.new('Iluminacao clinica','AREA');light.energy=65;light.shape='RECTANGLE';light.size=1.2;light.size_y=.6;o=bpy.data.objects.new('Iluminacao clinica',light);scene.collection.objects.link(o);o.location=q['pos']
scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=True;scene.render.resolution_x=1500;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
try:
 pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
 for dev in pref.devices:dev.use=dev.type!='CPU'
 if any(d.use for d in pref.devices):scene.cycles.device='GPU'
except Exception:pass
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
def camera(pos,look,lens):
 bpy.ops.object.camera_add(location=pos);cam=bpy.context.object;cam.rotation_euler=(Vector(look)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens;scene.camera=cam
camera((85,-115,62),(0,-3,3.5),44);scene.render.filepath=str(P/'hospital_exterior.png');bpy.ops.render.render(write_still=True)
camera((1,-25,1.8),(-6,-14,1.35),20);scene.render.filepath=str(P/'hospital_recepcao.png');bpy.ops.render.render(write_still=True)
camera((-14,18,1.6),(-14,9,1.35),23);scene.render.filepath=str(P/'hospital_consultorio.png');bpy.ops.render.render(write_still=True)
for obj in list(bpy.data.objects):
 if obj.type=='MESH':
  mid=sum(v.co.z for v in obj.data.vertices)/max(1,len(obj.data.vertices))
  if mid>3.9:obj.hide_render=True
camera((0,-55,60),(0,0,0),40);scene.render.filepath=str(P/'hospital_planta_terreo.png');bpy.ops.render.render(write_still=True)
print('HOSPITAL_PREVIEWS_READY',flush=True)
