from pathlib import Path
import json,bpy,numpy as np,math,csv
from mathutils import Vector
R=Path(__file__).resolve().parents[3];P=R/'teste-ilha';OUT=P/'identidade_cayo_total';O=P/'identidade_natural'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene
col=bpy.data.collections.new('01_CAYO_TERRENO_ORIGINAL_HIGH');scene.collection.children.link(col)
groundmat=bpy.data.materials.new('Relevo de referencia - cores de altitude');groundmat.use_nodes=True;bs=groundmat.node_tree.nodes.get('Principled BSDF');at=groundmat.node_tree.nodes.new('ShaderNodeAttribute');at.attribute_name='Altimetria';groundmat.node_tree.links.new(at.outputs['Color'],bs.inputs['Base Color']);bs.inputs['Roughness'].default_value=1
for row in read(OUT/'referencia_cache/terreno.json'):
    data=np.load(OUT/'referencia_cache'/(row['name']+'.npz'))
    for k,si in enumerate(row['geometries']):
        v=data['v'+str(k)];tri=data['i'+str(k)].reshape(-1,3);me=bpy.data.meshes.new(row['name']+' '+str(k));me.from_pydata(v['Position'].tolist(),[],tri.tolist());me.update();me.materials.append(groundmat)
        vi=np.empty(len(me.loops),int);me.loops.foreach_get('vertex_index',vi)
        if 'TexCoord0' in v.dtype.names:
            uv=me.uv_layers.new(name='UVMap 0');uv.data.foreach_set('uv',v['TexCoord0'][vi].ravel())
        for name in ['Colour0','Colour1']:
            if name in v.dtype.names:me.color_attributes.new(name=name,type='BYTE_COLOR',domain='CORNER').data.foreach_set('color',(v[name][vi]/255).ravel())
        h=np.clip((v['Position'][:,2]+row['position'][2])/66,0,1);color=np.stack([.24+h*.32,.42-h*.15,.13+h*.05,np.ones(len(h))],1)
        me.color_attributes.new(name='Altimetria',type='FLOAT_COLOR',domain='CORNER').data.foreach_set('color',color[vi].ravel())
        if 'Normal' in v.dtype.names:me.normals_split_custom_set_from_vertices(v['Normal'].tolist())
        ob=bpy.data.objects.new(row['name']+' '+str(k),me);col.objects.link(ob);ob.location=row['position'];ob.scale=row['scale'];ob['native_shader']=row['shaders'][si]['preset'];ob['native_parameters']=json.dumps(row['shaders'][si]['parameters']);ob['source']='Actual original HIGH mesh; height colours are analysis display, original UVs/weights retained.'
    print('CAYO_REFERENCE_MESH',row['name'],flush=True)
# Use the same unchanged native plant mesh cache as the running map.
code=(O/'scripts/cena_blender.py').read_text();fragment='prototypes={}'+code.split('prototypes={}',1)[1].split("col=bpy.data.collections.new('14_IDENTIDADE_CAYO_NATIVA')",1)[0];exec(fragment)
plants=bpy.data.collections.new('02_CAYO_VEGETACAO_E_PEDRAS_ORIGINAIS');scene.collection.children.link(plants)
markers=bpy.data.collections.new('03_COMPONENTES_E_INFRAESTRUTURA');scene.collection.children.link(markers)
seen=set();count=0;marker_count=0
for q in csv.DictReader((O/'dados/entidades_cayo.tsv').open(),delimiter='\t'):
    if q['lod'] not in ['LODTYPES_DEPTH_HD','LODTYPES_DEPTH_ORPHANHD']:continue
    pos=[float(q[k]) for k in ['x','y','z']];key=(q['name'],*tuple(round(v,2) for v in pos))
    if key in seen:continue
    seen.add(key)
    if q['name'] in prototypes:
        ob=bpy.data.objects.new(q['name']+' '+str(count),None);ob.instance_type='COLLECTION';ob.instance_collection=prototypes[q['name']];plants.objects.link(ob);ob.location=pos;ob.scale=(float(q['sx']),float(q['sx']),float(q['sz']));ob['native_archetype']=q['name'];count+=1
    elif any(w in q['name'] for w in ['dock','airstrip','wtower','road','hut','barrack','checkpoint','mansion']):
        ob=bpy.data.objects.new(q['name']+' referencia',None);markers.objects.link(ob);ob.location=pos;ob.empty_display_type='CUBE';ob.empty_display_size=2;ob['source_map']=q['map'];marker_count+=1
scene['reference_source']='Installed GTA V mpheist4; actual HIGH terrain and original native natural components. Infrastructure positions marked; not a complete drawable reconstruction of interiors.';scene['native_nature_instances']=count;scene['infrastructure_markers']=marker_count
scene.world=bpy.data.worlds.new('World');scene.world.color=(.35,.4,.5)
sun=bpy.data.lights.new('Sun','SUN');sun.energy=3;ob=bpy.data.objects.new('Sun',sun);scene.collection.objects.link(ob);ob.rotation_euler=(.4,-.3,-.4)
cam=bpy.data.cameras.new('Camera geografica');ob=bpy.data.objects.new('Camera geografica',cam);scene.collection.objects.link(ob);ob.location=(4500,-5200,2800);ob.rotation_euler=(0,0,0);cam.type='ORTHO';cam.ortho_scale=2550;scene.camera=ob
scene.render.engine='CYCLES';scene.cycles.samples=16;scene.render.resolution_x=1600;scene.render.resolution_y=1800;scene.render.resolution_percentage=100
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'cayo_perico_referencia.blend'),compress=True)
print('CAYO_REFERENCE_SAVED',count,marker_count,flush=True)
