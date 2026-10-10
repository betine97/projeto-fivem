import bpy

# Procedural galvanized steel inspired by the supplied clean, dirty and oxidized references.
# Real reflections and continuous 3D coordinates, including elbows and tapered outlets.
OXIDATION_AMOUNT = 0.22
DIRT_AMOUNT = 0.38


def make_metal(name, dark=False):
    mat=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes=True
    tree=mat.node_tree;tree.nodes.clear();nodes=tree.nodes;links=tree.links
    def new(kind,label):
        n=nodes.new(kind);n.label=label;return n
    def ramp(source, stops, label):
        n=new('ShaderNodeValToRGB',label)
        for i,(pos,color) in enumerate(stops):
            e=n.color_ramp.elements[i] if i<2 else n.color_ramp.elements.new(pos)
            e.position=pos;e.color=(*color,1)
        links.new(source,n.inputs[0]);return n.outputs['Color']
    def mathop(op,a,b):
        n=new('ShaderNodeMath',op);n.operation=op
        for inp,val in zip(n.inputs,(a,b)):
            if isinstance(val,(int,float)):inp.default_value=val
            else:links.new(val,inp)
        return n.outputs[0]
    def mix(factor,a,b,label):
        n=new('ShaderNodeMixRGB',label)
        for inp,val in zip(n.inputs,(factor,a,b)):
            if isinstance(val,(int,float)):inp.default_value=val
            elif isinstance(val,tuple):inp.default_value=(*val,1)
            else:links.new(val,inp)
        return n.outputs[0]
    coord=new('ShaderNodeTexCoord','Coordenadas comuns — escala em metros')
    coord.object=bpy.data.objects.get('WAREHOUSE_ORIGIN')
    def noise(scale,detail,label):
        n=new('ShaderNodeTexNoise',label);n.inputs['Scale'].default_value=scale;n.inputs['Detail'].default_value=detail
        links.new(coord.outputs['Object'],n.inputs['Vector']);return n
    broad=noise(1.7,3,'Manchas amplas')
    fine=noise(68,2,'Microvariacao superficial')
    grain=new('ShaderNodeTexVoronoi','Cristais de zinco')
    grain.inputs['Scale'].default_value=95
    links.new(coord.outputs['Object'],grain.inputs['Vector'])
    bw=new('ShaderNodeRGBToBW','Variacao por cristal');links.new(grain.outputs['Color'],bw.inputs[0])
    base=ramp(bw.outputs[0],[(0.18,(0.21,0.23,0.25)),(0.82,(0.42,0.44,0.46))],'Aco galvanizado')
    if dark:base=mix(0.62,base,(0.065,0.070,0.074),'Cintas e suportes escuros')
    grime=ramp(broad.outputs['Fac'],[(0.30,(0,0,0)),(0.69,(DIRT_AMOUNT,)*3)],'Sujeira irregular')
    base=mix(grime,base,(0.055,0.050,0.043),'Patina de uso')
    rust_noise=noise(7.5,4,'Oxidacao fragmentada')
    rust_mask=mathop('MULTIPLY',broad.outputs['Fac'],rust_noise.outputs['Fac'])
    rust=ramp(rust_mask,[(0.30,(0,0,0)),(0.43,(OXIDATION_AMOUNT,)*3),(0.58,(0.80,)*3)],'Oxidacao localizada')
    rust_color=ramp(fine.outputs['Fac'],[(0.20,(0.075,0.026,0.009)),(0.78,(0.26,0.10,0.024))],'Tons de ferrugem')
    color=mix(rust,base,rust_color,'Acabamento final')
    bsdf=new('ShaderNodeBsdfPrincipled','Metal com reflexo fisico')
    links.new(color,bsdf.inputs['Base Color'])
    metallic=mathop('SUBTRACT',0.92,mathop('MULTIPLY',rust,0.85))
    links.new(metallic,bsdf.inputs['Metallic'])
    rough=mathop('ADD',0.36 if not dark else 0.47,mathop('ADD',mathop('MULTIPLY',grime,0.30),mathop('MULTIPLY',rust,0.32)))
    links.new(rough,bsdf.inputs['Roughness'])
    bump=new('ShaderNodeBump','Textura fina sem deformar a chapa')
    bump.inputs['Strength'].default_value=0.18;bump.inputs['Distance'].default_value=0.0015
    links.new(fine.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs[0],bsdf.inputs['Normal'])
    out=new('ShaderNodeOutputMaterial','Saida');links.new(bsdf.outputs[0],out.inputs[0])
    mat.diffuse_color=(0.12,0.13,0.14,1) if dark else (0.32,0.34,0.36,1)
    for i,n in enumerate(nodes):n.location=((i%7)*225,-(i//7)*240)
    return mat


def target(obj):
    n=obj.name
    if obj.type not in ('MESH','CURVE'):return False
    if n.startswith(('DUCT_','CEILING_DUCT_')):return True
    if n.startswith('CEILING_VENT_'):
        return any(token in n for token in ('_NECK','_BELL','_COLLAR','_FLANGE'))
    if n.startswith('SERVICE_'):
        return any(token in n for token in ('_PIPE_','_CLAMP_','_STANDOFF_'))
    return n.startswith(('CONDUIT_','VENT_PORT_'))


def apply():
    steel=make_metal('STAGE10_Galvanizado_Industrial')
    dark=make_metal('STAGE10_Cintas_Suportes',True)
    changed={}
    for obj in bpy.data.objects:
        if not target(obj):continue
        is_support=any(t in obj.name for t in ('SUPPORT','STRAP','CRADLE','CLAMP','HANGER','CROSS_RAIL','STANDOFF'))
        mat=dark if is_support else steel
        obj.data.materials.clear();obj.data.materials.append(mat)
        if obj.type=='MESH':
            for face in obj.data.polygons:face.material_index=0
        elif obj.type=='CURVE':
            for spline in obj.data.splines:spline.material_index=0
        changed[obj.name]=mat.name
    bpy.context.view_layer.update()
    return changed


if __name__=='__main__':print('Tubulacoes atualizadas:',len(apply()))
