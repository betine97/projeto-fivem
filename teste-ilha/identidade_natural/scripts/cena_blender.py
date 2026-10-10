from pathlib import Path
import sys,json,math,bpy,numpy as np
from mathutils import Matrix,Vector
R=Path(__file__).resolve().parents[3];P=R/'teste-ilha';O=P/'identidade_natural'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
bpy.ops.wm.open_mainfile(filepath=str(P/'porto_construido/ilha_porto_esperanca_qualidade.blend'))
scene=bpy.context.scene;grid=np.load(P/'porto_construido/dados/terreno.npz')['terrain'];F=dict(np.load(O/'dados/biomas.npz'));rows=read(P/'porto_construido/qualidade_terreno/dados/terrain_quality.json')['sectors']
palette=read(O/'dados/solo.json')['layers'];mats=[]
for family in palette:
    m=bpy.data.materials.new('Solo nativo '+family[-1]['diffuse']);m.use_nodes=True;m['native_shader']='terrain_cb_4lyr.sps'
    ns=m.node_tree.nodes;ls=m.node_tree.links;bs=ns.get('Principled BSDF');bs.inputs['Roughness'].default_value=.92;bs.inputs['Specular IOR Level'].default_value=.05
    at=ns.new('ShaderNodeAttribute');at.attribute_name='Solo_Mistura';sep=ns.new('ShaderNodeSeparateColor');ls.new(at.outputs['Color'],sep.inputs[0]);uv=ns.new('ShaderNodeUVMap');uv.uv_map='UVMap 0'
    for channel in ['diffuse','normal']:
        nodes=[]
        for layer in family:
            p=O/'texturas'/(layer[channel]+'.dds')
            if not p.exists():p=P/'amostra_natural/texturas'/(layer[channel]+'.dds')
            im=bpy.data.images.load(str(p),check_existing=True);im.pack()
            if channel=='normal':im.colorspace_settings.name='Non-Color'
            tx=ns.new('ShaderNodeTexImage');tx.image=im;ls.new(uv.outputs[0],tx.inputs[0]);nodes.append(tx)
        pairs=[]
        for a,b in [(0,1),(2,3)]:
            mix=ns.new('ShaderNodeMixRGB');ls.new(sep.outputs['Blue'],mix.inputs[0]);ls.new(nodes[a].outputs['Color'],mix.inputs[1]);ls.new(nodes[b].outputs['Color'],mix.inputs[2]);pairs.append(mix)
        mix=ns.new('ShaderNodeMixRGB');ls.new(sep.outputs['Green'],mix.inputs[0]);ls.new(pairs[0].outputs[0],mix.inputs[1]);ls.new(pairs[1].outputs[0],mix.inputs[2])
        if channel=='diffuse':ls.new(mix.outputs[0],bs.inputs['Base Color'])
        else:
            nm=ns.new('ShaderNodeNormalMap');ls.new(mix.outputs[0],nm.inputs['Color']);ls.new(nm.outputs[0],bs.inputs['Normal'])
    mats.append(m)
for row in rows:
    x0,y0,x1,y1=row['grid_bounds']
    for suffix,step in [('',1),('_MED',2),('_LOW',4),('_VLOW',8)]:
        o=bpy.data.objects.get(row['name']+suffix)
        if not o:continue
        me=o.data;me.materials.clear()
        for m in mats:me.materials.append(m)
        g=grid[y0:y1+1:step,x0:x1+1:step];co=g.reshape(-1,3);vi=np.empty(len(me.loops),int);me.loops.foreach_get('vertex_index',vi)
        attr=me.color_attributes.get('Solo_Mistura') or me.color_attributes.new(name='Solo_Mistura',type='FLOAT_COLOR',domain='CORNER')
        attr.data.foreach_set('color',(F['mask'][y0:y1+1:step,x0:x1+1:step].reshape(-1,4)[vi]/255).ravel())
        for poly in me.polygons:
            p=co[list(poly.vertices)].mean(0);i=int(np.clip(round((p[0]-grid[0,0,0])/(grid[0,1,0]-grid[0,0,0])),0,768));j=int(np.clip(round((p[1]-grid[0,0,1])/(grid[1,0,1]-grid[0,0,1])),0,768))
            poly.material_index=2 if p[2]>95 else 1 if F['road_distance'][j,i]<1.5 else 0
    print('BLENDER_SOIL',row['name'],flush=True)
# Retain authored vegetation in the remaining half; native plants replace the Cayo half.
for collection_name in ['04_VEGETACAO','13_MATAS_DO_RESTANTE_DA_ILHA']:
    col=bpy.data.collections.get(collection_name)
    if not col:continue
    for o in col.objects:
        p=o.matrix_world @ (sum((Vector(v) for v in o.bound_box),Vector())/8)
        i=int(np.clip(round((p.x-grid[0,0,0])/(grid[0,1,0]-grid[0,0,0])),0,768));j=int(np.clip(round((p.y-grid[0,0,1])/(grid[1,0,1]-grid[0,0,1])),0,768))
        if F['identity'][j,i]:o.hide_render=True;o.hide_viewport=True
prototypes={}
for row in read(O/'cache_blender/modelos.json'):
    col=bpy.data.collections.new('Nativo | '+row['name']);data=np.load(O/'cache_blender'/(row['name']+'.npz'));materials=[]
    for k,sh in enumerate(row['materials']):
        m=bpy.data.materials.new(row['name']+' '+str(k));m.use_nodes=True;m['native_shader']=sh['preset'];bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.85;ls=m.node_tree.links
        for channel in ['diffuse','normal']:
            p=sh[channel]
            if not p:continue
            im=bpy.data.images.load(p,check_existing=True);im.pack();tx=m.node_tree.nodes.new('ShaderNodeTexImage');tx.image=im
            if channel=='diffuse':
                ls.new(tx.outputs['Color'],bs.inputs['Base Color']);ls.new(tx.outputs['Alpha'],bs.inputs['Alpha']);m.surface_render_method='DITHERED'
            else:
                im.colorspace_settings.name='Non-Color';nm=m.node_tree.nodes.new('ShaderNodeNormalMap');ls.new(tx.outputs['Color'],nm.inputs['Color']);ls.new(nm.outputs[0],bs.inputs['Normal'])
        materials.append(m)
    for k,si in enumerate(row['geometries']):
        if row['materials'][si]['preset']=='cpv_only.sps':continue
        v=data['v'+str(k)];tri=data['i'+str(k)].reshape(-1,3);me=bpy.data.meshes.new(row['name']+' '+str(k));me.from_pydata(v['Position'].tolist(),[],tri.tolist());me.update();me.materials.append(materials[si]);vi=np.empty(len(me.loops),int);me.loops.foreach_get('vertex_index',vi)
        if 'TexCoord0' in v.dtype.names:
            uv=me.uv_layers.new(name='UVMap 0');coords=v['TexCoord0'][vi].copy();coords[:,1]=1-coords[:,1];uv.data.foreach_set('uv',coords.ravel())
        for poly in me.polygons:poly.use_smooth=True
        if 'Normal' in v.dtype.names:me.normals_split_custom_set_from_vertices(v['Normal'].tolist())
        o=bpy.data.objects.new(row['name']+' '+str(k),me);col.objects.link(o)
    prototypes[row['name']]=col
col=bpy.data.collections.new('14_IDENTIDADE_CAYO_NATIVA');scene.collection.children.link(col)
for i,q in enumerate(read(O/'dados/posicoes.json')):
    o=bpy.data.objects.new(q['family']+' '+str(i),None);o.instance_type='COLLECTION';o.instance_collection=prototypes[q['name']];col.objects.link(o);o.location=q['position'];o.rotation_euler[2]=math.radians(q['heading']);o.scale=(q['scale'],)*3;o['native_archetype']=q['alias'];o['family']=q['family']
scene['identidade_revision']=read(O/'dados/plano.json')['revision'];scene['cayo_fraction']=.5;scene['grass_note']='Full native grass batches are in stream/ni_rasteira_*.ymap; GPU instancing remains authoritative in FiveM.'
scene['native_render_note']='Editable rest-pose preview; native wind, physics and render shaders preserved in the game files.'
bpy.ops.wm.save_as_mainfile(filepath=str(O/'ilha_identidade_cayo_chiliad.blend'),compress=True)
print('BLENDER_INTEGRATED_SAVED',flush=True)
