import bpy
import math
from pathlib import Path

BASE = Path(__file__).resolve().parent if '__file__' in globals() else Path(bpy.path.abspath('//'))
TEXTURES = BASE / 'texturas_dutos_retos'
if not TEXTURES.exists():
    TEXTURES = Path(bpy.path.abspath('//')) / 'texturas_dutos_retos'
FINISHES = ['01_galvanizado_limpo','02_galvanizado_usado','03_metal_escuro',
            '04_escovado_sujo','05_oxidacao_leve','06_industrial_gasto']


def make_material(index):
    name='STAGE9_DUTO_'+FINISHES[index]
    mat=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes=True
    tree=mat.node_tree;tree.nodes.clear()
    def node(kind,label):
        n=tree.nodes.new(kind);n.label=label;return n
    uv=node('ShaderNodeUVMap','UV cilindrico — chapa entre as cintas');uv.uv_map='DUTO_CHAPA_UV'
    tex=node('ShaderNodeTexImage',FINISHES[index])
    tex.image=bpy.data.images.load(str(TEXTURES/(FINISHES[index]+'.png')),check_existing=True)
    tex.image.colorspace_settings.name='sRGB';tex.extension='EXTEND'
    tree.links.new(uv.outputs['UV'],tex.inputs['Vector'])
    bsdf=node('ShaderNodeBsdfPrincipled','Chapa metalica')
    tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
    bsdf.inputs['Metallic'].default_value=[0.88,0.84,0.78,0.78,0.65,0.62][index]
    bsdf.inputs['Roughness'].default_value=[0.37,0.46,0.51,0.53,0.58,0.65][index]
    gray=node('ShaderNodeRGBToBW','Relevo sutil aproximado')
    tree.links.new(tex.outputs['Color'],gray.inputs[0])
    bump=node('ShaderNodeBump','Marcas superficiais')
    bump.inputs['Strength'].default_value=0.10;bump.inputs['Distance'].default_value=0.003
    tree.links.new(gray.outputs[0],bump.inputs['Height']);tree.links.new(bump.outputs[0],bsdf.inputs['Normal'])
    out=node('ShaderNodeOutputMaterial','Saida');tree.links.new(bsdf.outputs[0],out.inputs['Surface'])
    mat.diffuse_color=(0.27,0.28,0.28,1)
    for i,n in enumerate(tree.nodes):n.location=(i*200,0)
    return mat


def apply():
    mats=[make_material(i) for i in range(6)]
    changed={}
    for obj in bpy.data.objects:
        if obj.type!='MESH':continue
        if obj.name.startswith('CEILING_DUCT_MAIN_'):
            i=int(obj.name.rsplit('_',1)[1]);variant=[1,1,0,1,3,1,2,1,4,1][i%10]
        elif obj.name.startswith('DUCT_MAIN_BACK_SEG_'):
            i=int(obj.name.rsplit('_',1)[1]);variant=[1,4,1,3,5][i%5]
        elif obj.name=='DUCT_LEFT_VERTICAL':variant=2
        elif obj.name=='DUCT_RIGHT_CONNECTOR':variant=1
        else:continue
        # These generated cylinders have their longitudinal axis in local Z.
        verts=obj.data.vertices
        zmin=min(v.co.z for v in verts);zmax=max(v.co.z for v in verts)
        uv=obj.data.uv_layers.get('DUTO_CHAPA_UV') or obj.data.uv_layers.new(name='DUTO_CHAPA_UV')
        mat=mats[variant]
        slot=next((i for i,m in enumerate(obj.data.materials) if m==mat),None)
        if slot is None:slot=len(obj.data.materials);obj.data.materials.append(mat)
        for face in obj.data.polygons:
            if abs(face.normal.z)>0.90:continue # Leave cylinder end faces unchanged.
            face.material_index=slot
            for loop in face.loop_indices:
                co=verts[obj.data.loops[loop].vertex_index].co
                axial=(co.z-zmin)/max(zmax-zmin,1e-6)
                # Mirrored wrap closes at the hidden seam without caption or riveted strips.
                angle=(math.atan2(co.y,co.x)+math.pi)/math.tau
                mirrored=1-abs(2*angle-1)
                uv.data[loop].uv=(0.19+0.62*axial,0.145+0.835*mirrored)
        changed[obj.name]=FINISHES[variant]
    bpy.context.view_layer.update()
    return changed


if __name__=='__main__':
    print('Trechos retos atualizados:',apply())
