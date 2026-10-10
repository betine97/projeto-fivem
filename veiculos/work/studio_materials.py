"""PBR studio equivalents of the exported image materials, no granular noise."""
cache={}
for o in bpy.data.objects:
    if o.type!='MESH' or '.col' in o.name:continue
    for slot in o.material_slots:
        src=slot.material
        if not src or not src.use_nodes:continue
        diffuse=src.node_tree.nodes.get('DiffuseSampler')
        if not diffuse or not diffuse.image:continue
        if src.name not in cache:
            m=bpy.data.materials.new('PBR_'+src.name);m.use_nodes=True
            n=m.node_tree.nodes;links=m.node_tree.links;bs=n.get('Principled BSDF')
            tex=n.new('ShaderNodeTexImage');tex.image=diffuse.image
            uv=n.new('ShaderNodeUVMap');uv.uv_map='UVMap 0';links.new(uv.outputs['UV'],tex.inputs['Vector'])
            links.new(tex.outputs['Color'],bs.inputs['Base Color'])
            bs.inputs['Roughness'].default_value=.68
            bs.inputs['Metallic'].default_value=.20
            if 'RUBBER' in src.name:bs.inputs['Metallic'].default_value=0;bs.inputs['Roughness'].default_value=.9
            if 'glass' in src.name.lower():
                bs.inputs['Base Color'].default_value=(.1,.14,.15,1)
                for l in list(bs.inputs['Base Color'].links):links.remove(l)
                bs.inputs['Metallic'].default_value=0;bs.inputs['Roughness'].default_value=.15;bs.inputs['Transmission Weight'].default_value=.85
            if 'MILITARY' in src.name or 'textura' in src.name:
                ramp=n.new('ShaderNodeMapRange');ramp.inputs['From Min'].default_value=0;ramp.inputs['From Max'].default_value=1
                ramp.inputs['To Min'].default_value=.57;ramp.inputs['To Max'].default_value=.78
                links.new(tex.outputs['Color'],ramp.inputs['Value']);links.new(ramp.outputs[0],bs.inputs['Roughness'])
            cache[src.name]=m
        slot.material=cache[src.name]
