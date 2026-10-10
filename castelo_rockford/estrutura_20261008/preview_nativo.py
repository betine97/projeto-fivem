"""Visual QA from native exported drawables and compressed YTD textures."""
import bpy,sys,json,io
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1]
sys.path[:0]=[r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps',str(R/'laboratorio_fivem/work/pydeps')]
from szio.gta5 import try_load_asset,LodLevel
from PIL import Image
info=json.loads((P/'pacote.json').read_text(encoding='utf-8'))
bpy.ops.wm.open_mainfile(filepath=info['source'])
for o in list(bpy.data.objects):
    if o.type=='MESH' :bpy.data.objects.remove(o,do_unlink=True)
    elif o.type=='FONT':o.hide_render=True
s=bpy.context.scene
tx=try_load_asset(P/'package/stream/crf_castelo_texturas.ytd')
images={};cache=P/'preview_texturas';cache.mkdir(exist_ok=True)
for name,t in tx.textures.items():
    im=Image.open(io.BytesIO(t.data.read_bytes())).convert('RGBA')
    if name.endswith('_normal'):
        rr,gg,bb,aa=im.split();gg=gg.point(lambda x:255-x);im=Image.merge('RGBA',(rr,gg,bb,aa))
    path=cache/(name+'.png');im.save(path)
    b=bpy.data.images.load(str(path),check_existing=True)
    if name.endswith(('_normal','_spec')):b.colorspace_settings.name='Non-Color'
    images[name]=b
for row in info['models']:
    a=try_load_asset(P/'package/stream'/(row['model']+'.ydr'));mats=[]
    for shader in a.shader_group.shaders:
        m=bpy.data.materials.new(row['model']+str(len(mats)));m.use_nodes=True;nt=m.node_tree;p=nt.nodes.get('Principled BSDF')
        names={param.name:param.value for param in shader.parameters if isinstance(param.value,str)}
        diffuse=nt.nodes.new('ShaderNodeTexImage');diffuse.image=images[names['diffusesampler']]
        nt.links.new(diffuse.outputs['Color'],p.inputs['Base Color'])
        p.inputs['Roughness'].default_value=.65
        if 'bumpsampler' in names:
            tex=nt.nodes.new('ShaderNodeTexImage');tex.image=images[names['bumpsampler']]
            normal=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(tex.outputs['Color'],normal.inputs['Color']);nt.links.new(normal.outputs['Normal'],p.inputs['Normal'])
        if shader.preset_filename=='glass.sps':
            p.inputs['Transmission Weight'].default_value=1;p.inputs['Roughness'].default_value=.09;p.inputs['IOR'].default_value=1.45
        if shader.preset_filename=='emissive.sps':
            nt.links.new(diffuse.outputs['Color'],p.inputs['Emission Color']);p.inputs['Emission Strength'].default_value=4
        mats.append(m)
    for model in a.models[LodLevel.HIGH]:
        for i,g in enumerate(model.geometries):
            vb=g.vertex_buffer;tri=g.index_buffer.reshape(-1,3)
            me=bpy.data.meshes.new(row['model']+str(i));me.from_pydata(vb['Position'].tolist(),[],tri.tolist());me.update()
            uv=me.uv_layers.new(name='UVMap 0')
            for loop in me.loops:uv.data[loop.index].uv=vb['TexCoord0'][loop.vertex_index]
            me.normals_split_custom_set_from_vertices(vb['Normal'].tolist())
            for poly in me.polygons:poly.use_smooth=True
            me.materials.append(mats[g.shader_index]);o=bpy.data.objects.new(me.name,me);s.collection.objects.link(o)

# Native retained terrain is displayed at its actual position relative to the rotated castle.
import math,numpy as np
from mathutils import Vector
plan=json.loads((P/'implantacao.json').read_text());anchor=np.array(plan['anchor']);ang=math.radians(plan['rotation']);rot=np.array([[math.cos(ang),-math.sin(ang),0],[math.sin(ang),math.cos(ang),0],[0,0,1]])
origin=np.array(json.loads((R/'castelo_rockford/medidas.json').read_text())['origin']);terrain=try_load_asset(P/'terrain/stream/bh1_45_plot4a_ter_dcs.ydr')
colors={4:(.09,.19,.06,1),9:(.15,.28,.24,1),19:(.15,.28,.24,1),12:(.055,.11,.035,1),17:(.055,.11,.035,1),13:(.57,.54,.43,1),8:(.63,.60,.5,1),23:(.55,.52,.43,1)}
for model in terrain.models[LodLevel.HIGH]:
 for i,g in enumerate(model.geometries):
  vb=g.vertex_buffer;vertices=(vb['Position']+origin-anchor)@rot
  me=bpy.data.meshes.new('Terreno GTA '+str(i));me.from_pydata(vertices.tolist(),[],g.index_buffer.reshape(-1,3).tolist());me.update()
  m=bpy.data.materials.new('Terreno original '+str(i));m.diffuse_color=colors.get(g.shader_index,(.38,.29,.2,1));m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=m.diffuse_color;p.inputs['Roughness'].default_value=.85
  me.materials.append(m);o=bpy.data.objects.new(me.name,me);s.collection.objects.link(o)

s.render.engine='CYCLES';s.cycles.samples=24;s.cycles.use_denoising=True
s.render.resolution_x=1200;s.render.resolution_y=900;s.render.resolution_percentage=100
s.camera=bpy.data.objects['CAM Fachada'];s.camera.data.lens=42;s.render.filepath=str(P/'previa_arquivos_convertidos.png')
bpy.ops.render.render(write_still=True)
print('NATIVE_VISUAL_QA_RENDERED',flush=True)
print('CAMERAS',[o.name for o in bpy.data.objects if o.type=='CAMERA'],flush=True)
