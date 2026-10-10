import bpy
from pathlib import Path

# Keep these six source images beside this script. Caption areas are excluded by UV mapping.
BASE = Path(__file__).resolve().parent if '__file__' in globals() else Path(bpy.path.abspath('//'))
TEXTURES = BASE / 'texturas_parede_chao'
if not TEXTURES.exists():
    TEXTURES = Path(bpy.path.abspath('//')) / 'texturas_parede_chao'


def material(kind):
    name = 'STAGE8_' + kind.upper() + '_REFERENCIAS'
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    def node(t, name):
        n=nodes.new(t);n.label=name;return n
    def mathop(op, a, b):
        n=node('ShaderNodeMath',op);n.operation=op
        for socket,value in zip(n.inputs,(a,b)):
            if isinstance(value,(float,int)):socket.default_value=value
            else:links.new(value,socket)
        return n.outputs[0]
    out=node('ShaderNodeOutputMaterial','Saida')
    bsdf=node('ShaderNodeBsdfPrincipled','Concreto das referencias')
    links.new(bsdf.outputs['BSDF'],out.inputs['Surface'])
    uv=node('ShaderNodeUVMap','Mapeamento em metros');uv.uv_map='TEXTURA_CONCRETO'
    sep=node('ShaderNodeSeparateXYZ','Coordenadas');links.new(uv.outputs['UV'],sep.inputs[0])
    u=mathop('PINGPONG',sep.outputs['X'],1.0)
    v=mathop('PINGPONG',sep.outputs['Y'],1.0)
    # Crop borders and bottom captions inside the shader, without altering source files.
    u=mathop('ADD',mathop('MULTIPLY',u,0.954),0.022)
    v=mathop('ADD',mathop('MULTIPLY',v,0.86),0.13)
    comb=node('ShaderNodeCombineXYZ','Apenas a superficie, sem legenda')
    links.new(u,comb.inputs['X']);links.new(v,comb.inputs['Y'])
    names = (['parede_01_limpa','parede_02_usada','parede_03_desgastada'] if kind=='parede'
             else ['chao_01_limpo','chao_02_usado','chao_03_desgastado'])
    colors=[]
    for i,filename in enumerate(names):
        tex=node('ShaderNodeTexImage',filename)
        tex.image=bpy.data.images.load(str(TEXTURES/(filename+'.png')),check_existing=True)
        tex.image.colorspace_settings.name='sRGB'
        tex.extension='EXTEND'
        links.new(comb.outputs[0],tex.inputs['Vector']);colors.append(tex.outputs['Color'])
    coord=node('ShaderNodeTexCoord','Origem comum do galpao')
    coord.object=bpy.data.objects.get('WAREHOUSE_ORIGIN')
    noise=node('ShaderNodeTexNoise','Distribuicao ampla do desgaste')
    links.new(coord.outputs['Object'],noise.inputs['Vector'])
    noise.inputs['Scale'].default_value=0.65 if kind=='parede' else 0.80
    noise.inputs['Detail'].default_value=2.0
    ramp=node('ShaderNodeValToRGB','Manchas graduais')
    ramp.color_ramp.elements[0].position=0.30
    ramp.color_ramp.elements[1].position=0.70
    links.new(noise.outputs['Fac'],ramp.inputs[0])
    mix=node('ShaderNodeMixRGB','Limpa e usada');mix.blend_type='MIX'
    links.new(ramp.outputs['Color'],mix.inputs[0]);links.new(colors[0],mix.inputs[1]);links.new(colors[1],mix.inputs[2])
    wear=node('ShaderNodeValToRGB','Desgaste localizado')
    wear.color_ramp.elements[0].position=0.52
    wear.color_ramp.elements[1].position=0.76
    links.new(noise.outputs['Fac'],wear.inputs[0])
    final=node('ShaderNodeMixRGB','Terceira variacao nos pontos gastos')
    links.new(wear.outputs['Color'],final.inputs[0]);links.new(mix.outputs[0],final.inputs[1]);links.new(colors[2],final.inputs[2])
    links.new(final.outputs[0],bsdf.inputs['Base Color'])
    rough=node('ShaderNodeMapRange','Rugosidade aproximada')
    rough.inputs['From Min'].default_value=0;rough.inputs['From Max'].default_value=1
    rough.inputs['To Min'].default_value=0.85
    rough.inputs['To Max'].default_value=0.68 if kind=='parede' else 0.38
    links.new(wear.outputs['Color'],rough.inputs['Value']);links.new(rough.outputs[0],bsdf.inputs['Roughness'])
    bw=node('ShaderNodeRGBToBW','Relevo aproximado da imagem')
    links.new(final.outputs[0],bw.inputs[0])
    bump=node('ShaderNodeBump','Microrelevo discreto')
    bump.inputs['Strength'].default_value=0.16;bump.inputs['Distance'].default_value=0.012
    links.new(bw.outputs[0],bump.inputs['Height']);links.new(bump.outputs[0],bsdf.inputs['Normal'])
    mat.diffuse_color=(0.30,0.27,0.23,1)
    for i,n in enumerate(nodes):n.location=((i%7)*210,-(i//7)*240)
    return mat


def apply():
    mats={k:material(k) for k in ('parede','chao')}
    modified=[]
    for obj in bpy.data.objects:
        wall=obj.name.startswith(('WALL_','BASEBOARD_','TOP_BAND_','CORNER_GUARD_'))
        floor=obj.name in ('FLOOR_LEFT','FLOOR_RIGHT','FLOOR_DRAIN_FRONT_CAP','FLOOR_DRAIN_BACK_CAP')
        if obj.type!='MESH' or not (wall or floor):continue
        uv=obj.data.uv_layers.get('TEXTURA_CONCRETO') or obj.data.uv_layers.new(name='TEXTURA_CONCRETO')
        for face in obj.data.polygons:
            normal=obj.matrix_world.to_3x3() @ face.normal
            for loop in face.loop_indices:
                p=obj.matrix_world @ obj.data.vertices[obj.data.loops[loop].vertex_index].co
                if floor or abs(normal.z)>0.8: xy=(p.x/3.0,p.y/3.0)
                elif abs(normal.x)>abs(normal.y):xy=((p.y+6)/3.6,p.z/3.6)
                else:xy=((p.x+4)/3.6,p.z/3.6)
                uv.data[loop].uv=xy
            face.material_index=0
        obj.data.materials.clear();obj.data.materials.append(mats['parede' if wall else 'chao'])
        modified.append(obj.name)
    bpy.context.view_layer.update()
    return modified


if __name__=='__main__':
    print('Texturas aplicadas somente a paredes e piso:',len(apply()))
