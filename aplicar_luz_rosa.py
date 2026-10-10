import bpy

# Visual palette for the existing warehouse LEDs; no geometry is rebuilt.
LED_EMISSION_COLOR = (1.0, 0.035, 0.32, 1.0)
LED_LIGHT_COLOR = (1.0, 0.065, 0.36)
LED_EMISSION_STRENGTH = 9.0
LED_AREA_ENERGY = 120.0


def configure_led_glow(scene):
    """Add a subtle Fog Glow after the current compositor, Blender 4.x/5.x."""
    if hasattr(scene, 'compositing_node_group'):
        tree = scene.compositing_node_group
        if tree is None:
            tree = bpy.data.node_groups.new('WAREHOUSE_LED_COMPOSITOR', 'CompositorNodeTree')
            tree.interface.new_socket(name='Image', in_out='OUTPUT', socket_type='NodeSocketColor')
            scene.compositing_node_group = tree
        output = next((n for n in tree.nodes if n.type == 'GROUP_OUTPUT' and n.is_active_output), None)
        if output is None:
            output = tree.nodes.new('NodeGroupOutput')
        destination = output.inputs.get('Image')
        if destination is None:
            print('LED glow skipped: existing compositor has no Image output.')
            return
    else:
        scene.use_nodes = True
        tree = scene.node_tree
        output = next((n for n in tree.nodes if n.type == 'COMPOSITE'), None)
        if output is None:
            output = tree.nodes.new('CompositorNodeComposite')
        destination = output.inputs['Image']

    glow = tree.nodes.get('WAREHOUSE_LED_PINK_GLOW')
    if glow is None:
        # Preserve any existing compositing by inserting the glow at the output.
        if destination.is_linked:
            source = destination.links[0].from_socket
        else:
            layers = next((n for n in tree.nodes if n.type == 'R_LAYERS'), None)
            if layers is None:
                layers = tree.nodes.new('CompositorNodeRLayers')
            source = layers.outputs['Image']
        glow = tree.nodes.new('CompositorNodeGlare')
        glow.name = 'WAREHOUSE_LED_PINK_GLOW'
        glow.label = 'LED rosa - brilho suave'
        glow.location = (output.location.x - 240, output.location.y)
        tree.links.new(source, glow.inputs['Image'])
        tree.links.new(glow.outputs['Image'], destination)

    # Blender 5 exposes settings as sockets; older versions use node attributes.
    if glow.inputs.get('Type') is not None:
        glow.inputs['Type'].default_value = 'Fog Glow'
    elif hasattr(glow, 'glare_type'):
        glow.glare_type = 'FOG_GLOW'
    if glow.inputs.get('Quality') is not None:
        glow.inputs['Quality'].default_value = 'High'
    elif hasattr(glow, 'quality'):
        glow.quality = 'HIGH'
    if glow.inputs.get('Threshold') is not None:
        glow.inputs['Threshold'].default_value = 1.2
    elif hasattr(glow, 'threshold'):
        glow.threshold = 1.2
    if glow.inputs.get('Strength') is not None:
        glow.inputs['Strength'].default_value = 0.25
    elif hasattr(glow, 'mix'):
        glow.mix = -0.75
    if glow.inputs.get('Size') is not None:
        glow.inputs['Size'].default_value = 0.22
    elif hasattr(glow, 'size'):
        glow.size = 7
    scene.render.use_compositing = True


def add_led_diffuser_edges(material):
    """Thin emitting diffuser edges make the LEDs readable from above."""
    added = 0
    for body in list(bpy.data.objects):
        if not (body.name.startswith('LIGHT_FIXTURE_') and body.name.endswith('_BODY')
                and body.type == 'MESH'):
            continue
        for side, sign in enumerate((-1, 1)):
            name = body.name[:-5] + f'_PINK_EDGE_{side}'
            if bpy.data.objects.get(name) is not None:
                continue
            hx, hy, hz = (body.dimensions.x - 0.18) / 2, 0.006, 0.010
            vertices = [(-hx,-hy,-hz), (hx,-hy,-hz), (hx,hy,-hz), (-hx,hy,-hz),
                        (-hx,-hy,hz), (hx,-hy,hz), (hx,hy,hz), (-hx,hy,hz)]
            faces = [(0,3,2,1), (4,5,6,7), (0,1,5,4), (1,2,6,5), (2,3,7,6), (3,0,4,7)]
            mesh = bpy.data.meshes.new(name + '_DATA')
            mesh.from_pydata(vertices, [], faces)
            mesh.update()
            edge = bpy.data.objects.new(name, mesh)
            body.users_collection[0].objects.link(edge)
            edge.parent = body
            edge.location = (0.0, sign * (body.dimensions.y / 2 + 0.006),
                             -body.dimensions.z / 2 - 0.010)
            edge.data.materials.append(material)
            added += 1
    return added


def apply_pink_leds():
    material = bpy.data.materials.get('MAT_Light_Diffuser_Emission')
    if material is None:
        raise RuntimeError('Execute o Stage 5 antes deste ajuste: material das LEDs não encontrado.')
    material.diffuse_color = LED_EMISSION_COLOR
    material.use_nodes = True
    emission = next((n for n in material.node_tree.nodes if n.type == 'EMISSION'), None)
    if emission is None:
        raise RuntimeError('O material das LEDs não possui o nó de emissão esperado.')
    emission.inputs['Color'].default_value = LED_EMISSION_COLOR
    emission.inputs['Strength'].default_value = LED_EMISSION_STRENGTH

    count = 0
    for obj in bpy.data.objects:
        if (obj.name.startswith('LIGHT_FIXTURE_') and obj.name.endswith('_AREA')
                and obj.type == 'LIGHT' and obj.data.type == 'AREA'):
            obj.data.color = LED_LIGHT_COLOR
            obj.data.energy = LED_AREA_ENERGY
            count += 1
    added = add_led_diffuser_edges(material)
    configure_led_glow(bpy.context.scene)
    bpy.context.view_layer.update()
    print(f'LEDs rosa aplicadas: {count} luzes AREA; {added} bordas de difusor criadas; brilho suave.')


if __name__ == '__main__':
    apply_pink_leds()
