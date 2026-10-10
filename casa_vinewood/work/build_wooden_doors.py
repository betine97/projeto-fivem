"""Model solid timber leaves, horizontal grooves, frames and black hardware."""
import bpy,bmesh,json,math,sys
from pathlib import Path
from mathutils import Vector,Matrix
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(W/'work')]
from PIL import Image
from dds_mipmaps import save_dds_mips
bpy.ops.wm.open_mainfile(filepath=str(W/'mansao_encaixada.blend'))
s=bpy.context.scene
for prefix in ('12_','13_'):
 for c in list(bpy.data.collections):
  if c.name.startswith(prefix):
   for ob in list(c.objects):bpy.data.objects.remove(ob,do_unlink=True)
   bpy.data.collections.remove(c)
frames=bpy.data.collections.new('12_MOLDURAS_PORTAS');s.collection.children.link(frames)
leaves=bpy.data.collections.new('13_PORTAS_MOVEIS (origem na dobradica)');s.collection.children.link(leaves)
black=next(m for m in bpy.data.materials if m.get('finish_family')=='metal')
wood=bpy.data.materials.new('Madeira mel portas referencia');wood.use_nodes=True;wood['finish_family']='doorwood';wood['uv_tile_m']=2.5
n=wood.node_tree.nodes;l=wood.node_tree.links;p=n.get('Principled BSDF');p.inputs['Roughness'].default_value=.43
uv=n.new('ShaderNodeTexCoord');mapping=n.new('ShaderNodeVectorMath');mapping.operation='MULTIPLY';mapping.inputs[1].default_value=(.16,1.,1.)
l.new(uv.outputs['UV'],mapping.inputs[0])
wave=n.new('ShaderNodeTexWave');wave.wave_type='BANDS';wave.bands_direction='Y';wave.inputs['Scale'].default_value=55;wave.inputs['Distortion'].default_value=5.5;wave.inputs['Detail Scale'].default_value=1.8;wave.inputs['Detail'].default_value=6
l.new(mapping.outputs['Vector'],wave.inputs['Vector'])
ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.12;ramp.color_ramp.elements[0].color=(.17,.063,.021,1);ramp.color_ramp.elements[1].position=.90;ramp.color_ramp.elements[1].color=(.40,.187,.065,1)
l.new(wave.outputs['Color'],ramp.inputs['Fac']);l.new(ramp.outputs['Color'],p.inputs['Base Color'])
# Bake the procedural timber in Blender, so the editable material and GTA
# texture share the same horizontal grain instead of flattening the reference.
me=bpy.data.meshes.new('UV bake wood');me.from_pydata([(50,50,0),(51,50,0),(51,51,0),(50,51,0)],[],[(0,1,2,3)]);me.update();layer=me.uv_layers.new(name='UVMap 0')
for loop,coord in zip(layer.data,((0,0),(1,0),(1,1),(0,1))):loop.uv=coord
ob=bpy.data.objects.new('Bake wood texture temporary',me);s.collection.objects.link(ob);me.materials.append(wood)
im=bpy.data.images.new('porta_madeira_mel',width=2048,height=2048,alpha=False);tx=n.new('ShaderNodeTexImage');tx.image=im;n.active=tx
em=n.new('ShaderNodeEmission');l.new(ramp.outputs['Color'],em.inputs['Color']);l.new(em.outputs['Emission'],n.get('Material Output').inputs['Surface'])
bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob;s.render.engine='CYCLES';s.cycles.samples=1
bpy.ops.object.bake(type='EMIT');im.filepath_raw=str(W/'work/materiais/porta_madeira_mel.png');im.file_format='PNG';im.save()
l.new(p.outputs['BSDF'],n.get('Material Output').inputs['Surface']);l.new(tx.outputs['Color'],p.inputs['Base Color']);n.remove(em)
save_dds_mips(Image.open(im.filepath_raw),W/'work/materiais/porta_madeira_mel.dds')
bpy.data.objects.remove(ob,do_unlink=True)
groove=bpy.data.materials.new('Fundo dos frisos madeira');groove.diffuse_color=(.06,.026,.010,1);groove['finish_family']='doorgroove'
def box(name,a,b,col,mat,bevel=0):
 vs=[(a[0],a[1],a[2]),(b[0],a[1],a[2]),(b[0],b[1],a[2]),(a[0],b[1],a[2]),(a[0],a[1],b[2]),(b[0],a[1],b[2]),(b[0],b[1],b[2]),(a[0],b[1],b[2])]
 fs=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name,me);col.objects.link(o);me.materials.append(mat)
 if bevel:
  bpy.context.view_layer.objects.active=o;o.select_set(True);mod=o.modifiers.new('Arestas arredondadas','BEVEL');mod.width=bevel;mod.segments=3
  bpy.ops.object.modifier_apply(modifier=mod.name);o.select_set(False)
 return o
def cylinder(name,pos,radius,depth,col,mat,rotation=(0,0,0)):
 bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=radius,depth=depth,location=pos,rotation=rotation);o=bpy.context.object;o.name=name
 for c in list(o.users_collection):c.objects.unlink(o)
 col.objects.link(o);o.data.materials.append(mat)
 bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);o.select_set(False);return o
width=.946;height=2.430;thick=.045;parts=[]
parts.append(box('Folha macica 45mm',(-width,-.0205,0),(0,.0205,height),leaves,groove,.001))
for side in (-1,1):
 for i in range(7):
  z0=i*height/7+.0008;z1=(i+1)*height/7-.0008
  y0,y1=(-thick/2,-.0198) if side==-1 else (.0198,thick/2)
  parts.append(box('Painel horizontal madeira',(-width,y0,z0),(0,y1,z1),leaves,wood,.0006))
 x=-width+.105;z=1.020
 y=side*(thick/2+.003)
 parts.append(box('Roseta quadrada preta',(x-.027,y-.004,z-.027),(x+.027,y+.004,z+.027),leaves,black,.002))
 parts.append(box('Haste da macaneta',(x-.009,min(y,y+side*.030),z-.009),(x+.009,max(y,y+side*.030),z+.009),leaves,black,.003))
 yy=y+side*.030
 parts.append(box('Alavanca preta',(x-.009,yy-.009,z-.008),(x+.123,yy+.009,z+.008),leaves,black,.003))
 z=.895
 parts.append(box('Espelho quadrado fechadura',(x-.027,y-.004,z-.027),(x+.027,y+.004,z+.027),leaves,black,.002))
 # Recessed keyhole silhouette uses a dark recess inside the black escutcheon.
 parts.append(cylinder('Boca da fechadura',(x,y+side*.0041,z+.004),.006,.0006,leaves,groove,(math.pi/2,0,0)))
 parts.append(box('Canal da chave',(x-.0025,y+side*.004-.0004,z-.012),(x+.0025,y+side*.004+.0004,z+.005),leaves,groove,.0004))
for z in (.25,1.215,2.18):parts.append(cylinder('Dobradica preta',(0,0,z),.009,.080,leaves,black))
bpy.ops.object.select_all(action='DESELECT')
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();leaf=bpy.context.object;leaf.name='mansao_porta_madeira_095';leaf['dynamic_door']=True
leaf['collision_box_lo']=[-width,-thick/2,0];leaf['collision_box_hi']=[0,thick/2,height]
spec=json.loads((W/'medidas_estudo.json').read_text());O=spec['interior_origin_relative_native'];placements=[]
for d in spec['door_openings']:
 if d['key']!='ground' or d['name'] in ('Hall para Escada','Hall estar','Hall jantar','Hall cozinha','Cozinha lateral'):continue
 a,b,z0,z1=d['opening'];a+=O[0];b+=O[0];y=d['fixed']+O[1];floor=O[2]+z0;top=O[2]+z1
 assert abs((b-a)-1.05)<.001
 for x0,x1,label in [(a,a+.045,'esquerdo'),(b-.045,b,'direito')]:box('Batente '+d['name']+' '+label,(x0,y-.112,floor),(x1,y+.112,top),frames,wood,.002)
 box('Batente superior '+d['name'],(a,y-.112,top-.045),(b,y+.112,top),frames,wood,.002)
 for side in (-1,1):
  y0,y1=(y-.133,y-.112) if side<0 else (y+.112,y+.133)
  for x0,x1 in [(a-.045,a+.022),(b-.022,b+.045)]:box('Guarnicao '+d['name'],(x0,y0,floor),(x1,y1,top+.045),frames,wood,.002)
  box('Guarnicao topo '+d['name'],(a-.045,y0,top-.022),(b+.045,y1,top+.045),frames,wood,.002)
 placements.append(dict(id=len(placements)+1,name=d['name'].replace('Hall para ',''),model=leaf.name,hinge=[b-.049,y,floor+.015],closed_heading=0,open_heading=-95,width_m=width,height_m=height,leaf_thickness_m=thick,opening_center=[(a+b)*.5,y,floor+1.05],opening_bounds=[a,b,y-.10,y+.10,floor,top]))
leaves.hide_render=True
report=dict(revision='piso-tv-portas-2026-10-07',origin=spec['native_origin'],doors=placements,prototypes=[dict(name=leaf.name,width_m=width,height_m=height,thickness_m=thick)],reserved_entrances=['Entrada principal ao lado do deck','Porta de vidro a esquerda do sofa'],wide_arches_remain_open=True,interaction_key='E',reference_door=str(W/'source_assets/referencia_porta.png'),reference_handle=str(W/'source_assets/referencia_macaneta.png'))
(W/'portas_madeira.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
for im in bpy.data.images:
 if im.has_data:
  try:im.pack()
  except Exception:pass
bpy.ops.wm.save_as_mainfile(filepath=str(W/'mansao_encaixada.blend'))
print('WOODEN_DOORS_MODELED',len(placements),'doors',width,height,thick,flush=True)
