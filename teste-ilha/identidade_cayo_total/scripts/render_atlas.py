from pathlib import Path
import json, math, bpy, numpy as np
from mathutils import Vector
R=Path(__file__).resolve().parents[3];P=R/'teste-ilha';O=P/'identidade_cayo_total'
C=P/'identidade_natural/cache_blender';out=O/'atlas';out.mkdir(exist_ok=True)
rows=json.loads((C/'modelos.json').read_text())
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene;sc.render.engine='BLENDER_EEVEE';sc.render.resolution_x=256;sc.render.resolution_y=256;sc.render.resolution_percentage=100
sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA'
sc.view_settings.view_transform='Standard';sc.world=bpy.data.worlds.new('World');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.8,.8,.8,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.7
light=bpy.data.lights.new('Sun','SUN');light.energy=2.0;ob=bpy.data.objects.new('Sun',light);sc.collection.objects.link(ob);ob.rotation_euler=(.4,-.5,-.3)
cam=bpy.data.cameras.new('Camera');co=bpy.data.objects.new('Camera',cam);sc.collection.objects.link(co);cam.type='ORTHO';sc.camera=co
metadata=[]
for row in rows:
    if row['family'] not in ['tree','subcanopy','bush']:continue
    name=row['name'];data=np.load(C/(name+'.npz'));objects=[];vs=[];mats=[]
    for si,sh in enumerate(row['materials']):
        mat=bpy.data.materials.new(name+str(si));mat.use_nodes=True;ns=mat.node_tree.nodes;ls=mat.node_tree.links;bs=ns.get('Principled BSDF');bs.inputs['Roughness'].default_value=.95;bs.inputs['Specular IOR Level'].default_value=.1
        if sh['diffuse']:
            tx=ns.new('ShaderNodeTexImage');tx.image=bpy.data.images.load(sh['diffuse'],check_existing=True);ls.new(tx.outputs['Color'],bs.inputs['Base Color']);ls.new(tx.outputs['Alpha'],bs.inputs['Alpha']);mat.surface_render_method='DITHERED'
        mats.append(mat)
    for gi,si in enumerate(row['geometries']):
        if row['materials'][si]['preset']=='cpv_only.sps':continue
        v=data['v'+str(gi)];idx=data['i'+str(gi)].reshape(-1,3);me=bpy.data.meshes.new(name+str(gi));me.from_pydata(v['Position'].tolist(),[],idx.tolist());me.materials.append(mats[si]);vi=np.empty(len(me.loops),int);me.loops.foreach_get('vertex_index',vi)
        if 'TexCoord0' in v.dtype.names:
            uv=v['TexCoord0'][vi].copy();uv[:,1]=1-uv[:,1];me.uv_layers.new().data.foreach_set('uv',uv.ravel())
        if 'Normal' in v.dtype.names:me.normals_split_custom_set_from_vertices(v['Normal'].tolist())
        ob=bpy.data.objects.new(name+str(gi),me);sc.collection.objects.link(ob);objects.append(ob);vs.append(v['Position'])
    if not vs:continue
    v=np.concatenate(vs);lo=v.min(0);hi=v.max(0);center=(lo+hi)/2;size=hi-lo
    width=float(max(size[0],size[1],size[2])*1.08);cam.ortho_scale=width
    meta=dict(name=name,width=width,center=center.tolist(),bb_min=lo.tolist(),bb_max=hi.tolist(),family=row['family'])
    for key,offset in [('front',(0,-100,0)),('side',(100,0,0)),('top',(0,0,100))]:
        dest=out/(name+'_'+key+'.png')
        if not dest.exists():
            co.location=Vector(center)+Vector(offset);co.rotation_euler=(Vector(center)-co.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(dest);bpy.ops.render.render(write_still=True)
    metadata.append(meta)
    for ob in objects:bpy.data.objects.remove(ob,do_unlink=True)
    print('ATLAS_RENDER',name,flush=True)
(out/'models.json').write_text(json.dumps(metadata,indent=2))
print('ATLAS_RENDER_COMPLETE',len(metadata),flush=True)
