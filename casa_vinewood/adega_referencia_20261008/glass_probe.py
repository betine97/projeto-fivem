import bpy
from pathlib import Path
P=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(P/'mansao_com_adega.blend'))
for key in ['adega_cristal','adega_vidro_transparente']:
 m=bpy.data.materials[key]
 glass=m.node_tree.nodes.new('ShaderNodeBsdfGlass')
 glass.inputs['Color'].default_value=(.98,.98,.98,1)
 glass.inputs['Roughness'].default_value=.02
 glass.inputs['IOR'].default_value=1.45
 output=next(n for n in m.node_tree.nodes if n.type=='OUTPUT_MATERIAL')
 m.node_tree.links.new(glass.outputs[0],output.inputs['Surface'])
s=bpy.context.scene;s.cycles.samples=16;s.cycles.max_bounces=24;s.cycles.transmission_bounces=24;s.render.resolution_percentage=50
s.render.filepath=str(P/'glass_probe.png');bpy.ops.render.render(write_still=True)
