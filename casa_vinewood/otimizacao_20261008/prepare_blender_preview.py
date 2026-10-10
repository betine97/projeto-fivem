"""Editable scene plus native LOD meshes. Preview approximates game lighting."""
import bpy,sys,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parent;W=P.parent;R=P.parents[1]
sys.path[:0]=[r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps',str(R/'laboratorio_fivem/work/pydeps')]
from szio.gta5 import try_load_asset,LodLevel
source=W/'mansao_vasos_autorais.blend'
if not source.exists():source=W/'mansao_iluminada.blend'
bpy.ops.wm.open_mainfile(filepath=str(source));s=bpy.context.scene
replaced=0;materials={}
for m in bpy.data.materials:
    if not m.use_nodes:continue
    for node in m.node_tree.nodes:
        if node.type!='TEX_IMAGE' or not node.image:continue
        names=[Path(node.image.filepath.replace('//','')).stem.lower(),node.image.name.lower()]
        path=next((p for p in (P/'textures').glob('*.dds') if any(n==p.stem or n.startswith(p.stem+'.') for n in names)),None)
        family=m.get('finish_family')
        if path is None and family in ('sofa','tv','dining','island','cylinder','linear'):
            links=[link for socket in node.outputs for link in socket.links]
            suffix='normal' if any(link.to_node.type=='NORMAL_MAP' for link in links) else (
                'albedo' if any(link.to_socket.name=='Base Color' for link in links) else None)
            if suffix:path=P/'textures'/(family+'_'+suffix+'.dds')
        if not path:continue
        im=bpy.data.images.load(str(path),check_existing=True)
        if path.stem.endswith(('_normal','_n','_spec')):im.colorspace_settings.name='Non-Color'
        im.pack();node.image=im;replaced+=1
        if not path.stem.endswith(('_normal','_n','_spec')):materials[path.stem]=m
(P/'blender_image_bindings.json').write_text(json.dumps([
    {'material':m.name,'nodes':[{'name':n.name,'image':n.image.name,'file':n.image.filepath}
    for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image]}
    for m in bpy.data.materials if m.use_nodes],indent=2))
assert replaced>=15,('Missing optimization image bindings',replaced)
# Keep original authored HD objects editable. Native lower LODs are available
# separately for inspection/export; hidden in the architectural render.
lodcol=bpy.data.collections.new('92_LODS_OTIMIZADOS');s.collection.children.link(lodcol)
lodcol.hide_render=True;lodcol.hide_viewport=True
lodobjects=0
for name in ['mansao_mobiliario','mansao_tv','mansao_jantar','mansao_ilha','mansao_pendentes','mansao_tapete_sala']:
    a=try_load_asset(P/'stream'/(name+'.ydr'))
    for lod,models in a.models.items():
        if lod==LodLevel.HIGH:continue
        for mi,model in enumerate(models):
            for gi,g in enumerate(model.geometries):
                mesh=bpy.data.meshes.new(f'{name}_{lod.name}_{mi}_{gi}')
                mesh.from_pydata(g.vertex_buffer['Position'].tolist(),[],g.index_buffer.reshape(-1,3).tolist())
                mesh.update();obj=bpy.data.objects.new(mesh.name,mesh);lodcol.objects.link(obj)
                for poly in mesh.polygons:poly.use_smooth=True
                mesh.normals_split_custom_set_from_vertices(g.vertex_buffer['Normal'].tolist())
                for key in g.vertex_buffer.dtype.names:
                    if not key.startswith('TexCoord'):continue
                    uv=mesh.uv_layers.new(name=key)
                    for loop in mesh.loops:
                        value=g.vertex_buffer[key][loop.vertex_index];uv.data[loop.index].uv=(float(value[0]),1-float(value[1]))
                shader=a.shader_group.shaders[g.shader_index]
                diffuse=next((p.value for p in shader.parameters if 'diffuse' in p.name.lower()),None)
                if diffuse in materials:mesh.materials.append(materials[diffuse])
                obj['native_asset']=name;obj['native_lod']=lod.name;lodobjects+=1
for c in bpy.data.collections:
    if c.name.startswith(('07_','09_','11_','13_','90_','91_')):c.hide_render=True;c.hide_viewport=True
for o in list(bpy.data.objects):
    if o.type=='LIGHT':bpy.data.objects.remove(o,do_unlink=True)
cfg=json.loads((P/'iluminacao_ambiente.json').read_text())
# Selection is exported by the actual Lua verification, with local coordinates.
rows=json.loads((P/'preview_lights.json').read_text())
lightcol=bpy.data.collections.new('93_PREVIA_LUZ_AMPLA');s.collection.children.link(lightcol)
for i,row in enumerate(rows):
    light=bpy.data.lights.new('Luz ambiente ampla '+str(i),'POINT')
    light.energy=row['intensity']*100;light.color=[c/255 for c in row['rgb']]
    light.shadow_soft_size=1.0
    obj=bpy.data.objects.new(light.name,light);lightcol.objects.link(obj);obj.location=row['position']
lightcol['preview_only']=True
s.render.engine='CYCLES';s.cycles.samples=24;s.cycles.use_denoising=True
s.render.resolution_x=1280;s.render.resolution_y=900;s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG';s.world.use_nodes=True
s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.04
s.view_settings.view_transform='AgX'
bpy.ops.object.camera_add(location=(5.5,-3.5,.9));cam=bpy.context.object;s.camera=cam
cam.rotation_euler=(Vector((-3.3,-8.1,2.1))-cam.location).to_track_quat('-Z','Y').to_euler()
cam.data.lens=23;cam.data.clip_start=.05
s['lighting_revision']='otimizacao-luz-ampla-2026-10-08'
s['preview_note']='Blender approximation. FiveM native intensity needs in-game confirmation.'
bpy.ops.wm.save_as_mainfile(filepath=str(W/'mansao_otimizada.blend'),compress=True)
s.render.filepath=str(P/'previa_noite_luz_ampla.png');bpy.ops.render.render(write_still=True)
print('BLENDER_OPTIMIZED_PREVIEW',replaced,'texture nodes;',lodobjects,'native LOD objects',flush=True)
