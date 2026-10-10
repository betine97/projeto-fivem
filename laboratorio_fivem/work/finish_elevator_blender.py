"""Give the movable doors the same brushed finish used by the streamed model."""
from pathlib import Path
import bpy

root=Path(__file__).resolve().parents[2]
image_path=root/'laboratorio_fivem/elevator_source/elevator_door_metal.png'
image=bpy.data.images.load(str(image_path),check_existing=True)
image.pack()
material=bpy.data.materials['LAB_ELEVATOR_BRUSHED_STEEL']
material.use_nodes=True
nodes=material.node_tree.nodes
principled=nodes.get('Principled BSDF')
old=nodes.get('LAB_ELEVATOR_BRUSHED_IMAGE')
if old:nodes.remove(old)
tex=nodes.new('ShaderNodeTexImage')
tex.name='LAB_ELEVATOR_BRUSHED_IMAGE'
tex.image=image
material.node_tree.links.new(tex.outputs['Color'],principled.inputs['Base Color'])
principled.inputs['Metallic'].default_value=.72
principled.inputs['Roughness'].default_value=.31
concrete=bpy.data.materials['LAB_SUBLEVEL_CONCRETE']
concrete.use_nodes=True
concrete.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.12,.105,.095,1)
concrete.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.88
for suffix in ('0','MINUS_1'):
    delta=0 if suffix=='0' else -8
    for letter,sign in (('L',-1),('R',1)):
        bpy.data.objects[f'LAB_ELEVATOR_DOOR_{suffix}_{letter}'].location.x=sign*.35
    bpy.data.objects[f'LAB_ELEVATOR_DISPLAY_{suffix}'].location.z=2.40+delta
    bpy.data.objects[f'LAB_ELEVATOR_DISPLAY_{suffix}'].dimensions=(.58,.035,.42)
    bpy.data.objects[f'LAB_ELEVATOR_NUMBER_{suffix}'].location.z=2.40+delta

# The showroom source is retained but hidden. The game-ready version and both
# pairs of door panels remain individually selectable for fitting and editing.
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(root/'preparacao_fivem_stage18/warehouse_stage18_preparacao.blend'))
print('ELEVATOR_BLENDER_FINISH_OK',flush=True)
