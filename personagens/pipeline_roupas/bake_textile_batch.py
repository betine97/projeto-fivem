"""Bake supplied square textiles into the original native shirt UV atlas.

The input bitmaps are sampled through Blender materials, without painting or
generating replacement art. The base geometry and export UVs stay unchanged.
"""
import bpy
import sys
import json
import math
from pathlib import Path
from mathutils import Vector

batch_path = Path(sys.argv[sys.argv.index('--')+1])
here = batch_path.parent.parent
cfg = json.loads((here/'settings.json').read_text(encoding='utf-8'))
root = here.parents[1]
sys.path[:0] = [str(root/p) for p in cfg['native_dependencies']] + [cfg['sollumz']]
import addon_utils
addon_utils.enable('Sollumz', default_set=True)
from Sollumz.ydr.shader_materials import create_shader
from Sollumz.shared.shader_nodes import SzShaderNodeParameter

for entry in json.loads(batch_path.read_text(encoding='utf-8'))['jobs']:
    job, base = Path(entry['job']), Path(entry['base'])
    bpy.ops.wm.open_mainfile(filepath=entry['project'])
    scene = bpy.context.scene
    obj = next(o for o in bpy.data.collections['10_VARIACAO_TRABALHO'].objects if o.type=='MESH')
    originals = list(obj.data.materials)
    cloth = bpy.data.images.load(str(job/'inputs/tecido_original.png')); cloth.pack()
    native = bpy.data.images.load(str(base/'source/textures/jbib_diff_000_a_uni.dds')); native.pack()
    mat = bpy.data.materials.new('TEXTILE_PROJECTION'); mat.use_nodes=True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links; nodes.clear()
    # A continuous authoring UV prevents normal-driven box projection from
    # switching axes within the chest and breaking thin printed stripes.
    # Only the first, original UV layer is used as the output bake target.
    native_uv = obj.data.uv_layers[0]
    textile_uv = obj.data.uv_layers.new(name='TEXTILE_AUTHORING')
    for polygon in obj.data.polygons:
        center=obj.matrix_world @ polygon.center
        sleeve=abs(center.x)+.3*center.z>.325 and center.z>.22
        circumference=.45 if sleeve else 1.05
        points=[]
        for loop_index in polygon.loop_indices:
            vertex=obj.data.vertices[obj.data.loops[loop_index].vertex_index]
            pos=obj.matrix_world @ vertex.co
            x,y,z=pos
            if sleeve:
                # Separate sleeve cylinder follows the angled native upper arm;
                # a torso/sleeve coordinate blend would stretch the textile.
                outward=abs(x)-.17
                height=z-.50
                around=.8*outward+.6*height
                along=.6*outward-.8*height
                horizontal=(math.atan2(y,around)/(2*math.pi)+.5)*circumference
                vertical=-along+.5
            else:
                horizontal=(math.atan2(x,-y)/(2*math.pi)+.5)*circumference
                vertical=z
            points.append((loop_index,horizontal,vertical))
        # Unwrap the rear seam inside each polygon, rather than interpolating
        # through the complete texture when crossing -pi/pi.
        if max(p[1] for p in points)-min(p[1] for p in points)>circumference/2:
            points=[(i,u+circumference if u<circumference/2 else u,v) for i,u,v in points]
        for i,u,v in points:
            if entry.get('projection')=='native_uv':
                textile_uv.data[i].uv=native_uv.data[i].uv*entry['scale']
            else:textile_uv.data[i].uv=(u*entry['scale'],v*entry['scale'])
    obj.data.uv_layers.active=native_uv
    coords=nodes.new('ShaderNodeUVMap');coords.uv_map=textile_uv.name
    sample = nodes.new('ShaderNodeTexImage'); sample.image=cloth
    sample.extension='REPEAT'
    links.new(coords.outputs[0],sample.inputs[0])
    fabric_color=sample.outputs['Color']
    fine_path=job/'inputs/tecido_fino_original.png'
    if fine_path.exists():
        # Keep the supplied stripe artwork at garment scale and its fine dark
        # textile at fiber scale. Sampling both at one scale makes the yarn
        # look like coarse knitwear, unlike the complete reference shirt.
        fine=bpy.data.images.load(str(fine_path));fine.pack()
        fine_coords=nodes.new('ShaderNodeVectorMath');fine_coords.operation='SCALE'
        fine_coords.inputs['Scale'].default_value=5/entry['scale'];links.new(coords.outputs[0],fine_coords.inputs[0])
        fine_sample=nodes.new('ShaderNodeTexImage');fine_sample.image=fine;fine_sample.extension='REPEAT'
        links.new(fine_coords.outputs[0],fine_sample.inputs[0])
        stripe_luma=nodes.new('ShaderNodeRGBToBW');links.new(sample.outputs['Color'],stripe_luma.inputs[0])
        threshold=nodes.new('ShaderNodeMath');threshold.operation='SUBTRACT';threshold.inputs[1].default_value=.04
        links.new(stripe_luma.outputs[0],threshold.inputs[0])
        strength=nodes.new('ShaderNodeMath');strength.operation='DIVIDE';strength.inputs[1].default_value=.10;strength.use_clamp=True
        links.new(threshold.outputs[0],strength.inputs[0])
        mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MIX'
        links.new(strength.outputs[0],mix.inputs[0]);links.new(fine_sample.outputs['Color'],mix.inputs[1]);links.new(sample.outputs['Color'],mix.inputs[2])
        fabric_color=mix.outputs[0]
    uv = nodes.new('ShaderNodeUVMap'); uv.uv_map=obj.data.uv_layers[0].name
    original = nodes.new('ShaderNodeTexImage'); original.image=native
    links.new(uv.outputs[0],original.inputs[0])
    luma=nodes.new('ShaderNodeRGBToBW');links.new(original.outputs['Color'],luma.inputs[0])
    divide=nodes.new('ShaderNodeMath');divide.operation='DIVIDE';divide.inputs[1].default_value=.30;links.new(luma.outputs[0],divide.inputs[0])
    lower=nodes.new('ShaderNodeMath');lower.operation='MAXIMUM';lower.inputs[1].default_value=.85;links.new(divide.outputs[0],lower.inputs[0])
    upper=nodes.new('ShaderNodeMath');upper.operation='MINIMUM';upper.inputs[1].default_value=1.08;links.new(lower.outputs[0],upper.inputs[0])
    multiply=nodes.new('ShaderNodeMixRGB');multiply.blend_type='MULTIPLY';multiply.inputs[0].default_value=1
    links.new(fabric_color,multiply.inputs[1]);links.new(upper.outputs[0],multiply.inputs[2])
    emission=nodes.new('ShaderNodeEmission');links.new(multiply.outputs[0],emission.inputs['Color'])
    output=nodes.new('ShaderNodeOutputMaterial');links.new(emission.outputs[0],output.inputs['Surface'])
    atlas=bpy.data.images.new('TEXTILE_NATIVE_UV_ATLAS',width=2048,height=2048,alpha=False)
    target=nodes.new('ShaderNodeTexImage');target.image=atlas;nodes.active=target
    obj.data.materials.clear();obj.data.materials.append(mat)
    for poly in obj.data.polygons:poly.material_index=0
    bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
    scene.render.engine='CYCLES';scene.cycles.samples=1;scene.render.bake.margin=16
    bpy.ops.object.bake(type='EMIT')
    atlas.filepath_raw=str(job/'inputs/atlas_tecido.png');atlas.file_format='PNG';atlas.save();atlas.pack()
    obj.data.materials.clear()
    for material in originals:obj.data.materials.append(material)
    meshes={obj.data}
    for level in ('high','medium','low','very_low'):
        lod=getattr(obj.sz_lods,level)
        if lod.mesh:meshes.add(lod.mesh)
    for mesh in meshes:
        for index,material in enumerate(list(mesh.materials)):
            if not material or not material.node_tree:continue
            preset='ped_default.sps' if 'ped_default' in material.shader_properties.filename else 'ped.sps'
            replacement=create_shader(preset)
            old_nodes={n.name.lower():n for n in material.node_tree.nodes}
            for n in replacement.node_tree.nodes:
                old=old_nodes.get(n.name.lower())
                if n.type=='TEX_IMAGE' and old and old.type=='TEX_IMAGE':n.image=old.image
                if isinstance(n,SzShaderNodeParameter) and isinstance(old,SzShaderNodeParameter):
                    for i in range(min(n.num_cols*n.num_rows,old.num_cols*old.num_rows)):n.set(i,old.get(i))
                if n.name.lower()=='diffusesampler':n.image=atlas
            mesh.materials[index]=replacement
    scene.cycles.samples=12
    scene.render.resolution_x=640;scene.render.resolution_y=800;scene.render.resolution_percentage=100
    scene.world.color=(.35,.35,.35);scene.view_settings.view_transform='Standard'
    scene.render.image_settings.file_format='PNG';scene.render.film_transparent=True
    for name,position,power,size in [('KEY',(-1,-2,2),90,2),('FILL',(1,-1,1),40,2),('RIM',(0,2,1),60,2)]:
        data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size
        light=bpy.data.objects.new(name,data);scene.collection.objects.link(light);light.location=position
        light.rotation_euler=(Vector((0,0,.25))-light.location).to_track_quat('-Z','Y').to_euler()
    data=bpy.data.cameras.new('QA_CAMERA');camera=bpy.data.objects.new('QA_CAMERA',data);scene.collection.objects.link(camera)
    data.type='ORTHO';data.ortho_scale=.91;scene.camera=camera
    for name,angle in [('front',0),('back',math.pi),('left',math.pi/2),('right',-math.pi/2)]:
        camera.location=(2*math.sin(angle),-2*math.cos(angle),.28)
        camera.rotation_euler=(Vector((0,0,.25))-camera.location).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath=str(job/'qa'/f'{name}.png');bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(job/'work/variacao.blend'))
    rig=next(o for o in bpy.data.collections['10_VARIACAO_TRABALHO'].objects if o.type=='ARMATURE')
    action=bpy.data.actions.get('QA_FLEXAO_'+rig.name)
    if not action:raise RuntimeError('Missing native rig flexion test action')
    rig.animation_data_create();rig.animation_data.action=action;scene.frame_set(15);bpy.context.view_layer.update()
    for name,angle in [('pose_front',0),('pose_side',math.pi/2)]:
        camera.location=(2*math.sin(angle),-2*math.cos(angle),.28)
        camera.rotation_euler=(Vector((0,0,.25))-camera.location).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath=str(job/'qa'/f'{name}.png');bpy.ops.render.render(write_still=True)
    report={'method':'Blender emission bake of exact supplied textile','texture_scale':entry['scale'],'projection':entry.get('projection','separate torso and sleeve cylinders, original UV output'),'native_geometry_uv_weights_lods':'unchanged','normal_specular':'preserved','atlas_size':[2048,2048],'views':['front','back','left','right'],'visual_review':'pending'}
    (job/'qa/art_projection.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    (job/'qa/pose.json').write_text(json.dumps({'action':action.name,'frame':15,'views':['pose_front','pose_side'],'visual_review':'pending','in_game_motion':'pending'},indent=2),encoding='utf-8')
    print('TEXTILE_VARIATION_RENDERED',job.name,job.parent.name,flush=True)
