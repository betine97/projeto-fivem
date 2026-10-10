"""Orthographic product views of the editor's actual native game models."""
from pathlib import Path
import bpy,numpy as np,json,math
from mathutils import Vector
R=Path(__file__).resolve().parent.parent;C=R/'painel_adm_20261009/cayo_thumbnails';OUT=C/'renders';OUT.mkdir(exist_ok=True)
rows=json.loads((C/'models.json').read_text());bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene;sc.render.engine='BLENDER_EEVEE';sc.eevee.taa_render_samples=24;sc.render.resolution_x=384;sc.render.resolution_y=384;sc.render.resolution_percentage=100;sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.view_settings.view_transform='Standard'
sc.world=bpy.data.worlds.new('Thumbnail studio');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.8,.85,.9,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.65
sun=bpy.data.lights.new('Key light','SUN');sun.energy=2;ob=bpy.data.objects.new('Key light',sun);sc.collection.objects.link(ob);ob.rotation_euler=(.55,-.5,-.4)
cam=bpy.data.cameras.new('Camera');cam.type='ORTHO';co=bpy.data.objects.new('Camera',cam);sc.collection.objects.link(co);sc.camera=co;cam.clip_end=10000
report=[]
for k,row in enumerate(rows):
    dest=OUT/(row['name']+'.png')
    cable=any(s.get('preset')=='cable.sps' for s in row['materials'])
    if dest.exists() and not cable:continue
    data=np.load(C/'cache'/(row['name']+'.npz'));objects=[];meshes=[];mats=[];coords=[]
    for sh in row['materials']:
        sh['preset']=sh.get('preset') or ''
        mat=bpy.data.materials.new(row['name']+str(len(mats)));mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.7;bs.inputs['Specular IOR Level'].default_value=.1;bs.inputs['Base Color'].default_value=(.42,.46,.45,1)
        if sh['preset']=='cable.sps':bs.inputs['Base Color'].default_value=(.04,.05,.04,1)
        if sh['diffuse']:
            tx=mat.node_tree.nodes.new('ShaderNodeTexImage');tx.image=bpy.data.images.load(sh['diffuse'],check_existing=True);mat.node_tree.links.new(tx.outputs['Color'],bs.inputs['Base Color'])
            if any(s in sh['preset'] for s in ['tree','grass','cutout','alpha','glass','decal','fence']):mat.node_tree.links.new(tx.outputs['Alpha'],bs.inputs['Alpha']);mat.surface_render_method='DITHERED'
        elif 'cpv' in sh['preset']:
            col=mat.node_tree.nodes.new('ShaderNodeVertexColor');col.layer_name='NativeColour';mat.node_tree.links.new(col.outputs['Color'],bs.inputs['Base Color'])
        if 'glass' in sh['preset']:bs.inputs['Alpha'].default_value=.3;mat.surface_render_method='DITHERED'
        mats.append(mat)
    for gi,si in enumerate(row['geometries']):
        v=data['v'+str(gi)];idx=data['i'+str(gi)].reshape(-1,3);position=v['Position'].copy()
        if row['materials'][si]['preset']=='cable.sps':
            # GTA expands degenerate cable ribbons in the cable shader. Emulate
            # that only for previews; enforce a readable sub-pixel minimum width.
            span=max(float(np.linalg.norm(position.max(0)-position.min(0))),.1)
            side=np.cross(v['Normal'],np.asarray((.9,-1.35,.8)));side/=np.maximum(np.linalg.norm(side,axis=1)[:,None],1e-6)
            width=np.sign(v['TexCoord0'][:,0])*np.maximum(abs(v['TexCoord0'][:,0]),span/800)
            position+=side*width[:,None]
        me=bpy.data.meshes.new(row['name']+str(gi));me.from_pydata(position.tolist(),[],idx.tolist());me.update();me.materials.append(mats[si]);meshes.append(me);vi=np.empty(len(me.loops),int);me.loops.foreach_get('vertex_index',vi)
        if 'TexCoord0' in v.dtype.names:
            uv=v['TexCoord0'][vi].copy();uv[:,1]=1-uv[:,1];me.uv_layers.new().data.foreach_set('uv',uv.ravel())
        if 'Colour0' in v.dtype.names:me.color_attributes.new(name='NativeColour',type='BYTE_COLOR',domain='CORNER').data.foreach_set('color_srgb',(v['Colour0'][vi]/255).ravel())
        # Some native helper meshes contain degenerate faces/loose vertices;
        # Blender's custom-normal setter crashes on those. Preview shading can
        # use calculated normals without changing any game geometry.
        me.validate(verbose=False)
        for poly in me.polygons:poly.use_smooth=True
        obj=bpy.data.objects.new(row['name']+str(gi),me);sc.collection.objects.link(obj);objects.append(obj);coords.append(v['Position'])
    v=np.concatenate(coords);lo=v.min(0);hi=v.max(0);center=(lo+hi)/2;size=max(float(np.linalg.norm(hi-lo)),.10);cam.ortho_scale=size*1.06;cam.clip_start=max(.001,size/1000)
    co.location=Vector(center)+Vector((.9,-1.35,.8))*size*2;co.rotation_euler=(Vector(center)-co.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(dest);bpy.ops.render.render(write_still=True)
    report.append(dict(name=row['name'],geometry=True,textured=any(s['diffuse'] for s in row['materials']),native_cable_shader_emulated=cable))
    for obj in objects:bpy.data.objects.remove(obj,do_unlink=True)
    for me in meshes:bpy.data.meshes.remove(me)
    for mat in mats:bpy.data.materials.remove(mat)
    if k%50==0:print('EDITOR_IMAGE',k,row['name'],flush=True)
(C/'render-report.json').write_text(json.dumps(report,indent=2));print('EDITOR_IMAGES_RENDER_COMPLETE',len(rows),flush=True)
