"""Bake restrained timber grain and show placed leaves in the editable scene."""
import bpy,json,sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(W/'work')]
from PIL import Image
from dds_mipmaps import save_dds_mips
bpy.ops.wm.open_mainfile(filepath=str(W/'mansao_encaixada.blend'));s=bpy.context.scene
m=bpy.data.materials['Madeira mel portas referencia'];n=m.node_tree.nodes;l=m.node_tree.links
p=n.get('Principled BSDF');ramp=next(q for q in n if q.type=='VALTORGB');wave=next(q for q in n if q.type=='TEX_WAVE')
wave.inputs['Scale'].default_value=85;wave.inputs['Distortion'].default_value=12;wave.inputs['Detail Scale'].default_value=3.5
ramp.color_ramp.elements[0].color=(.23,.089,.028,1);ramp.color_ramp.elements[1].color=(.33,.144,.049,1)
uv=next(q for q in n if q.type=='TEX_COORD');vec=n.new('ShaderNodeVectorMath');vec.operation='MULTIPLY';vec.inputs[1].default_value=(2.5,45.,1.)
l.new(uv.outputs['UV'],vec.inputs[0]);noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=7;noise.inputs['Detail'].default_value=4;noise.inputs['Roughness'].default_value=.65;l.new(vec.outputs['Vector'],noise.inputs['Vector'])
mix=n.new('ShaderNodeMixRGB');mix.blend_type='MIX';mix.inputs[0].default_value=.75;l.new(wave.outputs['Color'],mix.inputs[1]);l.new(noise.outputs['Fac'],mix.inputs[2]);l.new(mix.outputs['Color'],ramp.inputs['Fac'])
me=bpy.data.meshes.new('Wood bake temp');me.from_pydata([(50,50,0),(51,50,0),(51,51,0),(50,51,0)],[],[(0,1,2,3)]);me.update();uvlayer=me.uv_layers.new(name='UVMap 0')
for loop,co in zip(uvlayer.data,((0,0),(1,0),(1,1),(0,1))):loop.uv=co
ob=bpy.data.objects.new('Wood bake temp',me);s.collection.objects.link(ob);me.materials.append(m)
tx=next(q for q in n if q.type=='TEX_IMAGE');n.active=tx;em=n.new('ShaderNodeEmission');l.new(ramp.outputs['Color'],em.inputs['Color']);l.new(em.outputs['Emission'],n.get('Material Output').inputs['Surface'])
bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob;s.render.engine='CYCLES';s.cycles.samples=1
bpy.ops.object.bake(type='EMIT');tx.image.filepath_raw=str(W/'work/materiais/porta_madeira_mel.png');tx.image.save();save_dds_mips(Image.open(tx.image.filepath_raw),W/'work/materiais/porta_madeira_mel.dds')
l.new(p.outputs['BSDF'],n.get('Material Output').inputs['Surface']);n.remove(em);bpy.data.objects.remove(ob,do_unlink=True)
col=bpy.data.collections.get('14_PORTAS_INSTANCIAS_PREVIEW')
if col:
 for o in list(col.objects):bpy.data.objects.remove(o,do_unlink=True)
else:col=bpy.data.collections.new('14_PORTAS_INSTANCIAS_PREVIEW');s.collection.children.link(col)
leaf=bpy.data.objects['mansao_porta_madeira_095'];cfg=json.loads((W/'portas_madeira.json').read_text())
for d in cfg['doors']:
 o=bpy.data.objects.new('Porta madeira '+d['name'],leaf.data);col.objects.link(o);o.location=d['hinge'];o['door_preview_only']=True
leaf.hide_render=True;next(c for c in bpy.data.collections if c.name.startswith('13_')).hide_viewport=True
for im in bpy.data.images:
 if im.has_data:
  try:im.pack()
  except Exception:pass
bpy.ops.wm.save_as_mainfile(filepath=str(W/'mansao_encaixada.blend'));print('DOOR_PREVIEW_PLACED_AND_GRAIN_REFINED',flush=True)
