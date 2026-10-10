import bpy
from pathlib import Path
bpy.ops.wm.open_mainfile(filepath=str(Path(__file__).resolve().parent/'adega_vitrines_editavel.blend'))
for key in ['adega_vinho_escuro','adega_ambar','adega_cristal','adega_vidro_transparente','adega_madeira']:
 m=bpy.data.materials[key]
 for n in m.node_tree.nodes:
  if n.type=='BSDF_PRINCIPLED':
   print('MATERIAL_PREVIEW',key,[(k,n.inputs[k].default_value,[(l.from_node.name,l.from_socket.name) for l in n.inputs[k].links]) for k in ['Roughness','Metallic','Specular IOR Level','Transmission Weight','Alpha']],flush=True)
 print('DIFFUSE_PIXELS',key,list(m.node_tree.nodes['DiffuseSampler'].image.pixels[:4]),flush=True)
 print('NORMAL_PIXELS',key,list(m.node_tree.nodes['BumpSampler'].image.pixels[:4]),flush=True)
 n=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
 print('IOR_WEIGHT',[(k,n.inputs[k].default_value) for k in ['IOR','Coat Weight','Thin Film Thickness'] if k in n.inputs],flush=True)
 print('SURFACE',[(l.from_node.name,l.to_node.name,l.to_socket.name) for l in m.node_tree.links if l.to_node.type=='OUTPUT_MATERIAL'],flush=True)
print('CYCLES',[(k,getattr(bpy.context.scene.cycles,k)) for k in ['max_bounces','transmission_bounces','transparent_max_bounces']],flush=True)
