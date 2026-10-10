"""Bake sixteen mixed Cayo ground-cover patches; no generated replacement plants."""
from pathlib import Path
import bpy, numpy as np, json, math
from mathutils import Vector
R=Path(__file__).resolve().parents[3];O=R/'teste-ilha/identidade_cayo_total';C=O/'atlas_rasteira/cache';OUT=O/'atlas_rasteira'
rows=json.loads((OUT/'modelos.json').read_text());rng=np.random.default_rng(90427)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene;sc.render.engine='BLENDER_EEVEE';sc.render.resolution_x=256;sc.render.resolution_y=256;sc.render.resolution_percentage=100;sc.eevee.taa_render_samples=32
sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.view_settings.view_transform='Standard'
sc.world=bpy.data.worlds.new('Cayo ambient');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.7,.7,.7,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.65
sun=bpy.data.lights.new('Sun','SUN');sun.energy=1.2;ob=bpy.data.objects.new('Sun',sun);sc.collection.objects.link(ob);ob.rotation_euler=(.25,-.15,-.4)
cam=bpy.data.cameras.new('Camera');co=bpy.data.objects.new('Camera',cam);sc.collection.objects.link(co);cam.type='ORTHO';cam.sensor_fit='HORIZONTAL';sc.camera=co
prototypes={}
for row in rows:
    data=np.load(C/(row['name']+'.npz'));col=bpy.data.collections.new(row['name']);materials=[]
    for sh in row['materials']:
        mat=bpy.data.materials.new(row['name']+str(len(materials)));mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=1;bs.inputs['Specular IOR Level'].default_value=.05
        if sh['diffuse']:
            tx=mat.node_tree.nodes.new('ShaderNodeTexImage');tx.image=bpy.data.images.load(sh['diffuse'],check_existing=True)
            # RAGE multiplies the procedural diffuse by each batch's instance
            # colour. Baking the grey diffuse alone loses the native green tint.
            tint=mat.node_tree.nodes.new('ShaderNodeMixRGB');tint.blend_type='MULTIPLY';tint.inputs[0].default_value=1;tint.inputs[2].default_value=(*np.asarray(row['instance_color'])/255,1)
            mat.node_tree.links.new(tx.outputs['Color'],tint.inputs[1]);mat.node_tree.links.new(tint.outputs[0],bs.inputs['Base Color']);mat.node_tree.links.new(tx.outputs['Alpha'],bs.inputs['Alpha']);mat.surface_render_method='DITHERED'
        materials.append(mat)
    for k,si in enumerate(row['geometries']):
        if not row['materials'][si]['diffuse']:continue
        v=data['v'+str(k)];idx=data['i'+str(k)].reshape(-1,3);me=bpy.data.meshes.new(row['name']+str(k));me.from_pydata(v['Position'].tolist(),[],idx.tolist());me.materials.append(materials[si]);vi=np.empty(len(me.loops),int);me.loops.foreach_get('vertex_index',vi)
        if 'TexCoord0' in v.dtype.names:
            uv=v['TexCoord0'][vi].copy();uv[:,1]=1-uv[:,1];me.uv_layers.new().data.foreach_set('uv',uv.ravel())
        if 'Normal' in v.dtype.names:me.normals_split_custom_set_from_vertices(v['Normal'].tolist())
        obj=bpy.data.objects.new(row['name']+str(k),me);col.objects.link(obj)
    prototypes[row['name']]=col
weights=np.asarray([r['count'] for r in rows],float);weights/=weights.sum();metadata=[]
for patch in range(16):
    objects=[]
    # 75 native plants in a 6 x 6 m patch, with the original species proportions.
    for i in range(75):
        row=rows[rng.choice(len(rows),p=weights)];obj=bpy.data.objects.new('Native patch plant',None);obj.instance_type='COLLECTION';obj.instance_collection=prototypes[row['name']];sc.collection.objects.link(obj)
        height=row['bb_max'][2]-row['bb_min'][2];scale=float(rng.uniform(.65,1.10));scale=min(scale,1.35/max(height,.2))
        obj.location=(float(rng.uniform(-2.65,2.65)),float(rng.uniform(-2.65,2.65)),-row['bb_min'][2]*scale);obj.rotation_euler[2]=float(rng.uniform(0,math.tau));obj.scale=(scale,)*3;objects.append(obj)
    for key,pos,target,sx,sy in [('top',(0,0,100),(0,0,.5),6,6),('front',(0,-100,.8),(0,0,.8),6,1.6),('side',(100,0,.8),(0,0,.8),6,1.6)]:
        dest=OUT/(f'patch_{patch:02}_{key}.png')
        # Actual image dimensions give an unambiguous camera footprint;
        # pixel-aspect metadata is ignored by most texture packers.
        sc.render.resolution_x=256;sc.render.resolution_y=round(256*sy/sx);sc.render.pixel_aspect_x=1;sc.render.pixel_aspect_y=1;cam.ortho_scale=sx
        co.location=pos;co.rotation_euler=(Vector(target)-co.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(dest);bpy.ops.render.render(write_still=True)
    metadata.append(dict(name=f'patch_{patch:02}',width=6,height=1.6,plants=75))
    for obj in objects:bpy.data.objects.remove(obj,do_unlink=True)
    print('GROUND_COVER_PATCH',patch,flush=True)
(OUT/'patches.json').write_text(json.dumps(metadata,indent=2))
print('GROUND_COVER_ATLAS_RENDER_COMPLETE',len(metadata),flush=True)
