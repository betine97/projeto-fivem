import bpy, json, runpy
from pathlib import Path
from mathutils import Vector
base=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(base/'warehouse_stage10_tubulacoes.blend'))
s=bpy.context.scene
settings={k:getattr(s.cycles,k,None) for k in ('preview_samples','use_preview_denoising','preview_denoising_start_sample','samples','use_denoising','preview_adaptive_threshold')}
(base/'stage10_preview_diagnostico.json').write_text(json.dumps(settings,indent=2),encoding='utf-8')
print('ORIGINAL SETTINGS',settings,flush=True)
runpy.run_path(str(base/'melhorar_preview_stage10.py'),run_name='__main__')
bpy.ops.wm.save_as_mainfile(filepath=str(base/'warehouse_stage10_preview_melhorado.blend'))
# Actual unmodified material, close-up under neutral inspection light.
keep=('CEILING_DUCT_MAIN_04','CEILING_DUCT_JOINT_04','CEILING_DUCT_SEAM_04')
for o in bpy.data.objects:
    if o.type in ('MESH','CURVE','LIGHT'):o.hide_render=o.name not in keep
obj=bpy.data.objects[keep[0]]
target=obj.matrix_world.translation.copy()
cam=bpy.data.objects['STAGE7_OVERVIEW'];s.camera=cam
cam.location=target+Vector((2,-2,1.5));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=1.65
for name,offset,energy,size in [('KEY',(1,-2,3),180,2),('FILL',(-2,1,1),65,2)]:
    data=bpy.data.lights.new('INSPECTION_'+name,'AREA');o=bpy.data.objects.new(data.name,data);s.collection.objects.link(o)
    o.location=target+Vector(offset);o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler();data.energy=energy;data.shape='DISK';data.size=size
s.world.node_tree.nodes['Background'].inputs['Color'].default_value=(0.12,0.12,0.12,1)
s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=0.5
s.render.resolution_x=1400;s.render.resolution_y=1000;s.render.resolution_percentage=100
s.render.use_compositing=False;s.view_settings.exposure=0
s.render.filepath=str(base/'stage10_close_material_atual.png')
bpy.ops.render.render(write_still=True)
print('CLOSEUP_COMPLETE',flush=True)
