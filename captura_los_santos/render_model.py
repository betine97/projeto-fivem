from pathlib import Path
import bpy,numpy as np,json,sys
from mathutils import Vector
folder=Path(sys.argv[sys.argv.index('--')+1]);row=json.loads((folder/'model.json').read_text());data=np.load(folder/'geometry.npz')
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene;sc.render.engine='BLENDER_EEVEE_NEXT' if bpy.app.version>=(4,2,0) else 'BLENDER_EEVEE'
if hasattr(sc,'eevee') and hasattr(sc.eevee,'taa_render_samples'):sc.eevee.taa_render_samples=32
sc.render.resolution_x=256;sc.render.resolution_y=256;sc.render.resolution_percentage=100;sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.view_settings.view_transform='Standard'
sc.world=bpy.data.worlds.new('Estúdio');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.8,.85,.9,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.65
sun=bpy.data.lights.new('Luz','SUN');sun.energy=2;ob=bpy.data.objects.new('Luz',sun);sc.collection.objects.link(ob);ob.rotation_euler=(.55,-.5,-.4)
cam=bpy.data.cameras.new('Câmera');cam.type='ORTHO';co=bpy.data.objects.new('Câmera',cam);sc.collection.objects.link(co);sc.camera=co;cam.clip_end=10000
mats=[];coordinates=[]
for sh in row['materials']:
    mat=bpy.data.materials.new('Material');mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.7;bs.inputs['Specular IOR Level' if bpy.app.version>=(4,0,0) else 'Specular'].default_value=.1;bs.inputs['Base Color'].default_value=(.42,.46,.45,1)
    if sh['diffuse']:
        tx=mat.node_tree.nodes.new('ShaderNodeTexImage');tx.image=bpy.data.images.load(sh['diffuse'],check_existing=True);mat.node_tree.links.new(tx.outputs['Color'],bs.inputs['Base Color'])
        if any(s in sh['preset'] for s in ['tree','grass','cutout','alpha','glass','decal','fence']):
            mat.node_tree.links.new(tx.outputs['Alpha'],bs.inputs['Alpha'])
            if hasattr(mat,'surface_render_method'):mat.surface_render_method='DITHERED'
            else:mat.blend_method='CLIP'
    elif 'cpv' in sh['preset']:
        col=mat.node_tree.nodes.new('ShaderNodeVertexColor');col.layer_name='NativeColour';mat.node_tree.links.new(col.outputs['Color'],bs.inputs['Base Color'])
    mats.append(mat)
for gi,si in enumerate(row['geometries']):
    v=data['v'+str(gi)];idx=data['i'+str(gi)].reshape(-1,3)
    me=bpy.data.meshes.new(row['name']);me.from_pydata(v['Position'].tolist(),[],idx.tolist());me.update();me.materials.append(mats[si]);vi=np.empty(len(me.loops),int);me.loops.foreach_get('vertex_index',vi)
    if 'TexCoord0' in v.dtype.names:
        uv=v['TexCoord0'][vi].copy();uv[:,1]=1-uv[:,1];me.uv_layers.new().data.foreach_set('uv',uv.ravel())
    if 'Colour0' in v.dtype.names:me.color_attributes.new(name='NativeColour',type='BYTE_COLOR',domain='CORNER').data.foreach_set('color_srgb',(v['Colour0'][vi]/255).ravel())
    me.validate(verbose=False)
    for polygon in me.polygons:polygon.use_smooth=True
    obj=bpy.data.objects.new(row['name'],me);sc.collection.objects.link(obj);coordinates.append(v['Position'])
v=np.concatenate(coordinates);lo=v.min(0);hi=v.max(0);center=(lo+hi)/2;size=max(float(np.linalg.norm(hi-lo)),.10);cam.ortho_scale=size*1.06;cam.clip_start=max(.001,size/1000)
co.location=Vector(center)+Vector((.9,-1.35,.8))*size*2;co.rotation_euler=(Vector(center)-co.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(folder/'preview.png');bpy.ops.render.render(write_still=True)
