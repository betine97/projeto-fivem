"""Render the approved Blender surface graphs to GTA material maps.

This is a technical material bake. Source images and .blend files are read only.
The original sampler coordinates remain in the native mesh for image materials;
untextured procedural surfaces use a four metre canonical projection instead.
Run with Blender --background --python this_file -- [--only 06] [--trees].
"""
from pathlib import Path
import argparse
import hashlib
import json
import sys
import bpy
import numpy as np

O = Path(__file__).resolve().parents[1]
P = O.parent
OUT = O / 'fontes' / 'material_bakes'
MANIFEST = O / 'dados' / 'materiais_baked.json'
REPORT = O / 'dados' / 'materiais_baked_report.json'
OUT.mkdir(parents=True, exist_ok=True)
parser = argparse.ArgumentParser()
parser.add_argument('--only', default='')
parser.add_argument('--trees', action='store_true')
parser.add_argument('--resolution', type=int, default=2048)
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
manifest = json.loads(MANIFEST.read_text(encoding='utf8')) if MANIFEST.exists() else {}
for model, materials in manifest.items():
    if model.startswith('pe_veg_'):
        for name in list(materials):
            if name.startswith('Folhagem'):
                del materials[name]


def log(*values):
    print('MATERIAL_BAKE:', *values, flush=True)


def scalar(socket):
    value = socket.default_value
    return list(value) if hasattr(value, '__len__') else value


def signature(material, attributes):
    """Include shader values and packed image identity; share identical bakes."""
    nodes = list(material.node_tree.nodes)
    index = {node: i for i, node in enumerate(nodes)}
    data = []
    for node in nodes:
        item = {'type': node.bl_idname,
                'values': [scalar(socket) for socket in node.inputs
                           if hasattr(socket, 'default_value')]}
        for prop in ('operation', 'blend_type', 'extension', 'uv_map', 'attribute_name', 'layer_name'):
            if hasattr(node, prop):
                item[prop] = getattr(node, prop)
        if node.type == 'TEX_IMAGE' and node.image:
            image = node.image
            raw = bytes(image.packed_file.data) if image.packed_file else Path(bpy.path.abspath(image.filepath)).read_bytes()
            item['image'] = hashlib.sha256(raw).hexdigest()
        if node.type == 'VALTORGB':
            item['ramp'] = [[el.position, list(el.color)] for el in node.color_ramp.elements]
        data.append(item)
    links = [[index[x.from_node], x.from_socket.identifier,
              index[x.to_node], x.to_socket.identifier] for x in material.node_tree.links]
    encoded = json.dumps({'nodes': data, 'links': links, 'attributes': attributes,
                          'resolution': args.resolution, 'canonical_period': 4,
                          'normal_g': 'NEG_Y', 'version': 1}, sort_keys=True).encode('utf8')
    return hashlib.sha256(encoded).hexdigest()[:18]


def used_attributes(material, objects):
    result = {}
    for node in material.node_tree.nodes:
        name = getattr(node, 'layer_name', '') if node.type == 'VERTEX_COLOR' else ''
        if not name:
            continue
        values = []
        for obj in objects:
            if obj.type != 'MESH' or material not in obj.data.materials.values():
                continue
            attr = obj.data.color_attributes.get(name)
            if attr and len(attr.data):
                array = np.empty(len(attr.data) * 4, dtype=np.float32)
                attr.data.foreach_get('color', array)
                values.append(array.reshape(-1, 4))
        result[name] = np.concatenate(values).mean(axis=0).tolist() if values else [.37, .095, .025, 1]
    return result


def clear_geometry():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


def proxy(material, attributes):
    mesh = bpy.data.meshes.new('Surface_bake_proxy')
    mesh.from_pydata([(0, 0, 0), (4, 0, 0), (4, 4, 0), (0, 4, 0)], [], [(0, 1, 2, 3)])
    mesh.update()
    uv = mesh.uv_layers.new(name='CanonicalUV')
    for loop, coord in zip(uv.data, [(0, 0), (1, 0), (1, 1), (0, 1)]):
        loop.uv = coord
    for name, value in attributes.items():
        attr = mesh.color_attributes.new(name=name, type='FLOAT_COLOR', domain='POINT')
        for el in attr.data:
            el.color = value
    obj = bpy.data.objects.new('Surface_bake_proxy', mesh)
    bpy.context.scene.collection.objects.link(obj)
    mesh.materials.append(material)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    for node in material.node_tree.nodes:
        if node.type == 'UVMAP':
            node.uv_map = 'CanonicalUV'
        if node.type == 'TEX_IMAGE' and node.image:
            # Native extraction applies the original first image sampler transform
            # to mesh UVs. Render the shader appearance in that sampler domain.
            for link in list(node.inputs['Vector'].links):
                material.node_tree.links.remove(link)
    return obj


def configure_scene():
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 1
    scene.cycles.use_denoising = False
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 8
    scene.render.bake.margin = 2
    scene.render.bake.use_clear = True
    scene.render.bake.normal_space = 'TANGENT'
    scene.render.bake.normal_r = 'POS_X'
    scene.render.bake.normal_g = 'NEG_Y'
    scene.render.bake.normal_b = 'POS_Z'


def baked_map(material, bsdf, digest, channel, size):
    path = OUT / f'pe_bake_{digest}_{channel}.png'
    if path.exists():
        return path
    nodes, links = material.node_tree.nodes, material.node_tree.links
    image = bpy.data.images.new(path.stem, width=size, height=size, alpha=True)
    image.colorspace_settings.name = 'sRGB' if channel == 'd' else 'Non-Color'
    target = nodes.new('ShaderNodeTexImage')
    target.image = image
    for node in nodes:
        node.select = node == target
    nodes.active = target
    output = next(node for node in nodes if node.type == 'OUTPUT_MATERIAL' and node.is_active_output)
    output_socket = output.inputs['Surface'].links[0].from_socket
    created = []
    if channel != 'n':
        emission = nodes.new('ShaderNodeEmission')
        created.append(emission)
        if channel == 'd':
            color = bsdf.inputs['Base Color']
            if color.is_linked:
                links.new(color.links[0].from_socket, emission.inputs['Color'])
            else:
                emission.inputs['Color'].default_value = color.default_value
        else:
            # GTA SpecSampler contains reflectivity, rather than PBR roughness.
            invert = nodes.new('ShaderNodeMath')
            invert.operation = 'SUBTRACT'
            invert.inputs[0].default_value = 1
            roughness = bsdf.inputs['Roughness']
            if roughness.is_linked:
                links.new(roughness.links[0].from_socket, invert.inputs[1])
            else:
                invert.inputs[1].default_value = roughness.default_value
            links.new(invert.outputs[0], emission.inputs['Color'])
            created.append(invert)
        links.new(emission.outputs[0], output.inputs['Surface'])
    bpy.ops.object.bake(type='NORMAL' if channel == 'n' else 'EMIT')
    image.filepath_raw = str(path)
    image.file_format = 'PNG'
    image.save()
    if channel != 'n':
        links.new(output_socket, output.inputs['Surface'])
    for node in created:
        nodes.remove(node)
    nodes.remove(target)
    bpy.data.images.remove(image)
    log('MAP_READY', path.name, size)
    return path


def bake(material, attributes):
    bsdf = next((node for node in material.node_tree.nodes if node.type == 'BSDF_PRINCIPLED'), None)
    if not bsdf:
        return None
    images = [node for node in material.node_tree.nodes if node.type == 'TEX_IMAGE' and node.image]
    digest = signature(material, attributes)
    copy = material.copy()
    copy.name = 'BAKE_' + material.name
    bsdf = next(node for node in copy.node_tree.nodes if node.type == 'BSDF_PRINCIPLED')
    obj = proxy(copy, attributes)
    configure_scene()
    color_linked = bsdf.inputs['Base Color'].is_linked
    normal_linked = bsdf.inputs['Normal'].is_linked
    roughness_linked = bsdf.inputs['Roughness'].is_linked
    # Small authored solid colors retain their scalar values. Textures are
    # rendered only for source image graphs or meaningful procedural variation.
    result = {'roughness': float(bsdf.inputs['Roughness'].default_value),
              'metallic': float(bsdf.inputs['Metallic'].default_value),
              'transmission': float(bsdf.inputs['Transmission Weight'].default_value),
              'color': list(bsdf.inputs['Base Color'].default_value[:3]),
              'baked': bool(color_linked or normal_linked or roughness_linked),
              'uv_mode': 'source_sampler' if images else 'object_projection',
              'canonical_period': 4, 'normal_green': 'NEG_Y',
              'attribute_representatives': attributes,
              'source_images_unchanged': True}
    channels = [('d', args.resolution)] if color_linked else []
    if normal_linked:
        channels.append(('n', min(args.resolution, 1024)))
    if roughness_linked or color_linked or normal_linked:
        channels.append(('s', min(args.resolution, 1024)))
    for channel, size in channels:
        path = baked_map(copy, bsdf, digest, channel, size)
        key = {'d': ('texture', 'file'), 'n': ('normal_texture', 'normal_file'),
               's': ('spec_texture', 'spec_file')}[channel]
        result[key[0]] = path.stem
        result[key[1]] = str(path)
    bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.materials.remove(copy)
    return result


paths = sorted((P / 'estruturas_porto_20261009' / 'modelos').glob('*.blend'))
if args.only:
    paths = [path for path in paths if path.stem[:2] == args.only]
if args.trees:
    paths += sorted((P / 'porto_esperanca' / 'modelos' / 'vegetacao_vento').glob('*.blend'))
for path in paths:
    bpy.ops.wm.open_mainfile(filepath=str(path))
    bpy.context.scene.frame_set(40)
    house = path.parent.name == 'modelos'
    key = 'pe_estrutura_' + path.stem[:2] if house else 'pe_veg_' + path.stem
    objects = list(bpy.data.collections['Modelo_completo'].all_objects) if house else [obj for obj in bpy.data.objects if obj.type == 'MESH' and obj.name == path.stem]
    materials = list({material.as_pointer(): material for obj in objects if hasattr(obj.data, 'materials')
                      for material in obj.data.materials if material}.values())
    # Read representatives before removing all source geometry; copies of source
    # geometry are not needed for canonical texture baking and would slow BVH.
    attributes_by_material = {material.name: used_attributes(material, objects) for material in materials}
    for material in materials:
        material.use_fake_user = True
    clear_geometry()
    manifest[key] = {}
    for material in materials:
        if not material.use_nodes:
            continue
        output = next((node for node in material.node_tree.nodes if node.type == 'OUTPUT_MATERIAL' and node.is_active_output), None)
        if not house and (material.name.startswith('Folhagem') or not output or not output.inputs['Surface'].is_linked or
                          output.inputs['Surface'].links[0].from_node.type != 'BSDF_PRINCIPLED'):
            # Preserve the user's complete original foliage alpha and wind data.
            continue
        attrs = attributes_by_material[material.name]
        result = bake(material, attrs)
        if result:
            manifest[key][material.name] = result
            log('MATERIAL_READY', key, material.name)
    manifest_tmp = MANIFEST.with_suffix('.json.tmp')
    manifest_tmp.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf8')
    manifest_tmp.replace(MANIFEST)
    records = [{'model': model, 'material': name, **metadata}
               for model, materials in manifest.items() for name, metadata in materials.items()]
    report_tmp = REPORT.with_suffix('.json.tmp')
    report_tmp.write_text(json.dumps({'records': records, 'source_blends_unchanged': True,
                                 'source_images_unchanged': True,
                                 'foliage_rgba_preserved': True,
                                 'canonical_object_period_m': 4,
                                 'in_game_verified': False}, indent=2, ensure_ascii=False), encoding='utf8')
    report_tmp.replace(REPORT)
    log('MODEL_READY', key, len(manifest[key]))
log('DONE', sum(len(materials) for materials in manifest.values()), str(MANIFEST))
