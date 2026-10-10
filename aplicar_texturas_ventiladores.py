import bpy, math
from pathlib import Path
BASE=Path(__file__).resolve().parent if '__file__' in globals() else Path(bpy.path.abspath('//'))
FOLDER=BASE/'texturas_ventiladores'
if not FOLDER.exists():FOLDER=Path(bpy.path.abspath('//'))/'texturas_ventiladores'

def material(kind):
    name='STAGE11_FAN_'+kind
    mat=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes=True;t=mat.node_tree;t.nodes.clear()
    uv=t.nodes.new('ShaderNodeNewGeometry')
    density=t.nodes.new('ShaderNodeVectorMath');density.operation='SCALE';density.inputs[3].default_value=2.0 if kind=='metal_riscado' else 6.0
    t.links.new(uv.outputs['Position'],density.inputs[0])
    repeat=t.nodes.new('ShaderNodeVectorMath');repeat.operation='FRACTION'
    t.links.new(density.outputs[0],repeat.inputs[0])
    mapping=t.nodes.new('ShaderNodeVectorMath');mapping.operation='MULTIPLY_ADD'
    t.links.new(repeat.outputs[0],mapping.inputs[0])
    # Sample only relevant metal surfaces, not the black openings or pictured bolts.
    regions={'grade':((0.08,)*3,(0.46,)*3),
             'moldura':((0.065,)*3,(0.895,)*3),
             'carcaca_oxidada':((0.105,)*3,(0.865,)*3),
             'metal_riscado':((0.92,)*3,(0.04,)*3)}
    scale,offset=regions[kind];mapping.inputs[1].default_value=scale;mapping.inputs[2].default_value=offset
    tex=t.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(FOLDER/(kind+'.png')),check_existing=True)
    tex.image.colorspace_settings.name='sRGB';tex.extension='EXTEND'
    # World-space triplanar weights must match the world-space coordinates.
    img=tex.image;t.nodes.remove(tex)
    coords=t.nodes.new('ShaderNodeSeparateXYZ');t.links.new(repeat.outputs[0],coords.inputs[0])
    ab=t.nodes.new('ShaderNodeVectorMath');ab.operation='ABSOLUTE';t.links.new(uv.outputs['Normal'],ab.inputs[0])
    normal=t.nodes.new('ShaderNodeSeparateXYZ');t.links.new(ab.outputs[0],normal.inputs[0])
    weights=[]
    for axis in range(3):
        p=t.nodes.new('ShaderNodeMath');p.operation='POWER';p.inputs[1].default_value=4
        t.links.new(normal.outputs[axis],p.inputs[0]);weights.append(p.outputs[0])
    total=t.nodes.new('ShaderNodeMath');total.operation='ADD';t.links.new(weights[0],total.inputs[0]);t.links.new(weights[1],total.inputs[1])
    total2=t.nodes.new('ShaderNodeMath');total2.operation='ADD';t.links.new(total.outputs[0],total2.inputs[0]);t.links.new(weights[2],total2.inputs[1])
    colors=[]
    for axis,(a,b) in enumerate(((1,2),(0,2),(0,1))):
        vec=t.nodes.new('ShaderNodeCombineXYZ');t.links.new(coords.outputs[a],vec.inputs[0]);t.links.new(coords.outputs[b],vec.inputs[1])
        crop=t.nodes.new('ShaderNodeVectorMath');crop.operation='MULTIPLY_ADD'
        crops={'grade':((0.08,0.08,0),(0.46,0.46,0)), 'moldura':((0.35,0.055,0),(0.32,0.885,0)), 'carcaca_oxidada':((0.11,0.09,0),(0.75,0.865,0)), 'metal_riscado':((0.92,0.92,0),(0.04,0.04,0))}
        crop.inputs[1].default_value,crop.inputs[2].default_value=crops[kind]
        t.links.new(vec.outputs[0],crop.inputs[0])
        sample=t.nodes.new('ShaderNodeTexImage');sample.image=img;sample.extension='EXTEND';t.links.new(crop.outputs[0],sample.inputs[0])
        w=t.nodes.new('ShaderNodeMath');w.operation='DIVIDE';t.links.new(weights[axis],w.inputs[0]);t.links.new(total2.outputs[0],w.inputs[1])
        mul=t.nodes.new('ShaderNodeMixRGB');mul.blend_type='MULTIPLY';mul.inputs[0].default_value=1
        t.links.new(sample.outputs['Color'],mul.inputs[1]);t.links.new(w.outputs[0],mul.inputs[2]);colors.append(mul.outputs[0])
    add=t.nodes.new('ShaderNodeMixRGB');add.blend_type='ADD';add.inputs[0].default_value=1;t.links.new(colors[0],add.inputs[1]);t.links.new(colors[1],add.inputs[2])
    tex=t.nodes.new('ShaderNodeMixRGB');tex.blend_type='ADD';tex.inputs[0].default_value=1;t.links.new(add.outputs[0],tex.inputs[1]);t.links.new(colors[2],tex.inputs[2])
    bsdf=t.nodes.new('ShaderNodeBsdfPrincipled')
    t.links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
    bsdf.inputs['Metallic'].default_value=0.65 if kind=='carcaca_oxidada' else 0.82
    bsdf.inputs['Roughness'].default_value=0.58 if kind=='carcaca_oxidada' else 0.46
    bump=t.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=0.13;bump.inputs['Distance'].default_value=0.001
    t.links.new(tex.outputs['Color'],bump.inputs['Height']);t.links.new(bump.outputs[0],bsdf.inputs['Normal'])
    out=t.nodes.new('ShaderNodeOutputMaterial');t.links.new(bsdf.outputs[0],out.inputs[0])
    mat.diffuse_color=(0.30,0.24,0.19,1) if kind=='carcaca_oxidada' else (0.23,0.25,0.26,1)
    for i,n in enumerate(t.nodes):n.location=(i*210,0)
    return mat

def apply():
    mats={k:material(k) for k in ('grade','moldura','carcaca_oxidada','metal_riscado')}
    changed={}
    for obj in bpy.data.objects:
        n=obj.name
        if obj.type not in ('MESH','CURVE') or not n.startswith(('SIDE_FAN_','EXHAUST_FAN_','CEILING_VENT_')):continue
        if any(x in n for x in ('CABLE','_INNER')):continue
        if any(x in n for x in ('CASING','HOUSING','_BELL','_NECK','_FLANGE')):kind='carcaca_oxidada'
        elif any(x in n for x in ('FRAME','_TAB')):kind='moldura'
        elif any(x in n for x in ('GRILLE','SPOKE','BADGE','BOLT')):kind='grade'
        else:kind='metal_riscado'
        obj.data.materials.clear();obj.data.materials.append(mats[kind])
        if obj.type=='MESH':
            for p in obj.data.polygons:p.material_index=0
        else:
            for s in obj.data.splines:s.material_index=0
        changed[n]=kind
    return changed

if __name__=='__main__':print('Pecas dos ventiladores texturizadas:',len(apply()))
