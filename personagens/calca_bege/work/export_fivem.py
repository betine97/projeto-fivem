import bpy, bmesh, sys, addon_utils, json
from pathlib import Path
sys.path[:0] = [r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps', r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\sollumz']
addon_utils.enable('Sollumz', default_set=True)
from Sollumz.sollumz_properties import LODLevel
from Sollumz.ydr.shader_materials import create_shader
from Sollumz.tools.meshhelper import mesh_add_missing_uv_maps, mesh_add_missing_color_attrs, get_color_attr_name
from Sollumz.ydd.yddexport import export_ydd
from Sollumz.iecontext import ExportContext, ExportSettings, export_context_scope
from szio.gta5 import try_load_asset, save_asset, AssetTarget, AssetFormat, AssetVersion, AssetTextureDictionary, EmbeddedTexture
from szio.types import DataSource

ROOT = Path(sys.argv[sys.argv.index('--')+1]).resolve() if '--' in sys.argv else Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT/'export_config.json').read_text()) if (ROOT/'export_config.json').exists() else {}
OUT = ROOT / 'exports'
OUT.mkdir(exist_ok=True)
FILE = CONFIG.get('component', 'lowr_008_u')
DIFFUSE = CONFIG.get('diffuse', 'lowr_diff_008_a_uni')
PREFIX = CONFIG.get('texture_prefix', 'calca_bege')
targets = (AssetTarget(AssetFormat.NATIVE, AssetVersion.GEN8),)
bpy.ops.wm.open_mainfile(filepath=str(ROOT / CONFIG.get('blend', 'PERSONAGEM_COM_CALCA_BEGE.blend')))
scene = bpy.context.scene
source = bpy.data.objects[CONFIG.get('object', 'CALCA_BEGE')]
work = source.copy()
work.data = source.data.copy()
scene.collection.objects.link(work)
work.parent = None
for modifier in list(work.modifiers):
    work.modifiers.remove(modifier)
work.hide_set(False)
work.hide_select = False
high_ratio = CONFIG.get('high_ratio', 1)
if high_ratio < 1:
    bpy.ops.object.select_all(action='DESELECT')
    work.select_set(True)
    bpy.context.view_layer.objects.active = work
    modifier = work.modifiers.new('DETALHE_OTIMIZADO', 'DECIMATE')
    modifier.ratio = high_ratio
    modifier.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier=modifier.name)
# Preserve the source UV unwrap; high_ratio defaults to the original mesh.
for uv in list(work.data.uv_layers)[1:]:
    work.data.uv_layers.remove(uv)
work.data.uv_layers[0].name = 'UVMap 0'
reserved = create_shader('ped_default.sps')
reserved.name = FILE + '_RESERVADO'
material = create_shader('ped.sps')
material.name = PREFIX.upper() + '_NATIVA'
for sampler, name, embedded in [('DiffuseSampler', DIFFUSE, False), ('BumpSampler', PREFIX+'_normal', True), ('SpecSampler', PREFIX+'_spec', True)]:
    texture = bpy.data.images.load(str(ROOT / 'textures' / (name + '.dds')), check_existing=False)
    texture.name = name + '.dds'
    if sampler != 'DiffuseSampler':
        texture.colorspace_settings.name = 'Non-Color'
    texture.pack()
    node = material.node_tree.nodes.get(sampler)
    node.image = texture
    node.texture_properties.embedded = embedded
for name, value in [('specularIntensityMult', CONFIG.get('specular_intensity', .28)), ('specularFalloffMult', CONFIG.get('specular_falloff', 35)), ('bumpiness', 1.0)]:
    node = material.node_tree.nodes.get(name)
    if node:
        node.set_float(value)
work.data.materials.clear()
work.data.materials.append(reserved)
work.data.materials.append(material)
for polygon in work.data.polygons:
    polygon.material_index = 1
mesh_add_missing_uv_maps(work.data)
mesh_add_missing_color_attrs(work.data)
for i in (0, 1):
    attribute = work.data.color_attributes[get_color_attr_name(i)]
    rgba = (1, 128 / 255, 0, 1) if i == 0 else (0, 0, 0, 0)
    for datum in attribute.data:
        datum.color_srgb = rgba

# Visible native skin belongs in the same shoe component, with its own UVs
# and embedded diffuse. Keep it separate from the accessory's decimation.
skin_parts = []
for name in CONFIG.get('skin_objects', []):
    original = bpy.data.objects[name]
    skin = original.copy()
    skin.data = original.data.copy()
    scene.collection.objects.link(skin)
    skin.parent = None
    for modifier in list(skin.modifiers):
        skin.modifiers.remove(modifier)
    for uv in list(skin.data.uv_layers)[1:]:
        skin.data.uv_layers.remove(uv)
    skin.data.uv_layers[0].name = 'UVMap 0'
    old = original.data.materials[0]
    image = next(n.image for n in old.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image)
    skin_mat = create_shader('ped.sps')
    skin_mat.name = name + '_NATIVA'
    texture = bpy.data.images.load(bpy.path.abspath(image.filepath), check_existing=False)
    texture.name = Path(image.filepath).name
    texture.pack()
    node = skin_mat.node_tree.nodes.get('DiffuseSampler')
    node.image = texture
    node.texture_properties.embedded = True
    # Use the original GTA skin normal/specular maps as well as the diffuse.
    donor = ROOT.parent.parent / ('calca_bege/source/mp_m_freemode_01_male_apt01^feet_001_r.ydd' if 'PELE_PES' in name else 'templates_freemode/source/lowr_014_r.ydd')
    native_skin = next(iter(try_load_asset(donor).drawables.values()))
    prefix = 'feet' if 'PELE_PES' in name else 'lowr'
    number = '001' if prefix == 'feet' else '014'
    for sampler, suffix in [('BumpSampler', 'normal'), ('SpecSampler', 'spec')]:
        texname = prefix + '_' + suffix + '_' + number
        path = ROOT / 'textures' / (texname + '.dds')
        path.write_bytes(native_skin.shader_group.embedded_textures[texname].data.read_bytes())
        tex = bpy.data.images.load(str(path), check_existing=False)
        tex.name = texname + '.dds'
        tex.colorspace_settings.name = 'Non-Color'
        tex.pack()
        skin_mat.node_tree.nodes[sampler].image = tex
        skin_mat.node_tree.nodes[sampler].texture_properties.embedded = True
    skin.data.materials.clear()
    skin.data.materials.append(skin_mat)
    for polygon in skin.data.polygons:
        polygon.material_index = 0
    mesh_add_missing_uv_maps(skin.data)
    mesh_add_missing_color_attrs(skin.data)
    for i in (0, 1):
        for datum in skin.data.color_attributes[get_color_attr_name(i)].data:
            datum.color_srgb = (1, 128 / 255, 0, 1) if i == 0 else (0, 0, 0, 0)
    skin.hide_set(False)
    skin.hide_select = False
    skin_parts.append(skin)
for name in CONFIG.get('overlay_objects', []):
    original = bpy.data.objects[name]
    overlay = original.copy()
    overlay.data = original.data.copy()
    scene.collection.objects.link(overlay)
    overlay.parent = None
    for modifier in list(overlay.modifiers):
        overlay.modifiers.remove(modifier)
    for uv in list(overlay.data.uv_layers)[1:]:
        overlay.data.uv_layers.remove(uv)
    overlay.data.uv_layers[0].name = 'UVMap 0'
    overlay.data.materials.clear()
    overlay.data.materials.append(material.copy())
    for polygon in overlay.data.polygons:
        polygon.material_index = 0
    mesh_add_missing_uv_maps(overlay.data)
    mesh_add_missing_color_attrs(overlay.data)
    for i in (0, 1):
        for datum in overlay.data.color_attributes[get_color_attr_name(i)].data:
            datum.color_srgb = (1, 128 / 255, 0, 1) if i == 0 else (0, 0, 0, 0)
    overlay.hide_set(False)
    overlay.hide_select = False
    skin_parts.append(overlay)
if skin_parts:
    bpy.ops.object.select_all(action='DESELECT')
    work.select_set(True)
    for skin in skin_parts:
        skin.select_set(True)
    bpy.context.view_layer.objects.active = work
    bpy.ops.object.join()

before = set(bpy.data.objects)
bpy.ops.sollumz.import_assets(directory=str(ROOT / 'source'), files=[{'name': FILE + '.ydd'}], use_custom_settings=True, dwd_import_external_skeleton='FROM_DIR')
imported = set(bpy.data.objects) - before
dictionary = next(o for o in imported if o.type == 'ARMATURE' and o.parent is None)
model = next(o for o in imported if o.type == 'MESH')
model.data = work.data.copy()
model.vertex_groups.clear()
mapped_groups = {}
for group in work.vertex_groups:
    name = group.name
    if name not in dictionary.data.bones:
        matches = [b.name for b in dictionary.data.bones if b.name.rsplit('_', 1)[0] == name.rsplit('_', 1)[0]]
        assert len(matches) == 1, (name, matches)
        name = matches[0]
    mapped_groups[group.index] = model.vertex_groups.new(name=name)
for vertex in work.data.vertices:
    for group in vertex.groups:
        if group.weight > 0:
            mapped_groups[group.group].add([vertex.index], group.weight, 'REPLACE')
model.data = model.data.copy()
skin_payload = None
if CONFIG.get('skin_objects'):
    skin_payload = model.copy()
    skin_payload.data = model.data.copy()
    scene.collection.objects.link(skin_payload)
    # Native feet remain intact at every distance; simplify only the shoe.
    bm = bmesh.new()
    bm.from_mesh(skin_payload.data)
    skin_vertices = {v for f in bm.faces if f.material_index >= 2 for v in f.verts}
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v not in skin_vertices], context='VERTS')
    bm.to_mesh(skin_payload.data)
    bm.free()
lod_counts = {}
for lod, ratio in [(LODLevel.HIGH, 1), (LODLevel.MEDIUM, .20), (LODLevel.LOW, .06), (LODLevel.VERYLOW, .015)]:
    if ratio == 1:
        mesh = model.data
    else:
        temporary = model.copy()
        temporary.data = model.data.copy()
        scene.collection.objects.link(temporary)
        if skin_payload:
            bm = bmesh.new()
            bm.from_mesh(temporary.data)
            garment_vertices = {v for f in bm.faces if f.material_index < 2 for v in f.verts}
            bmesh.ops.delete(bm, geom=[v for v in bm.verts if v not in garment_vertices], context='VERTS')
            bm.to_mesh(temporary.data)
            bm.free()
        for modifier in list(temporary.modifiers):
            temporary.modifiers.remove(modifier)
        bpy.ops.object.select_all(action='DESELECT')
        temporary.hide_set(False)
        temporary.hide_select = False
        temporary.select_set(True)
        bpy.context.view_layer.objects.active = temporary
        modifier = temporary.modifiers.new('LOD_SIMPLIFICADO', 'DECIMATE')
        modifier.ratio = ratio
        modifier.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        if skin_payload:
            skin = skin_payload.copy()
            skin.data = skin_payload.data.copy()
            scene.collection.objects.link(skin)
            skin.hide_set(False)
            skin.hide_select = False
            skin.select_set(True)
            bpy.context.view_layer.objects.active = temporary
            bpy.ops.object.join()
        mesh = temporary.data
        bpy.data.objects.remove(temporary, do_unlink=True)
    model.sz_lods.get_lod(lod).mesh = mesh
    lod_counts[str(lod)] = len(mesh.polygons)
if skin_payload:
    bpy.data.objects.remove(skin_payload, do_unlink=True)
model.parent.name = FILE + '.#dd'
dictionary.name = FILE
with export_context_scope(ExportContext(FILE, ExportSettings(targets=targets))):
    bundle = export_ydd(dictionary)
bundle.save(OUT, targets)
txd = AssetTextureDictionary(textures={DIFFUSE: EmbeddedTexture(name=DIFFUSE, width=4096, height=4096, data=DataSource.create(ROOT / 'textures' / (DIFFUSE + '.dds')))})
save_asset(txd, targets, OUT, DIFFUSE)
native = try_load_asset(OUT / (FILE + '.ydd'))
assert len(native.drawables) == 1
drawable = next(iter(native.drawables.values()))
report = {'component': FILE, 'source_vertices': len(source.data.vertices), 'source_triangles': len(source.data.polygons), 'lod_triangles': lod_counts, 'embedded_textures': list(drawable.shader_group.embedded_textures), 'diffuse': DIFFUSE, 'shaders': [s.preset_filename for s in drawable.shader_group.shaders]}
assert {PREFIX+'_normal', PREFIX+'_spec'} <= set(drawable.shader_group.embedded_textures)
(OUT / 'validation.json').write_text(json.dumps(report, indent=2))
print('EXPORT_CALCA_OK', json.dumps(report), flush=True)
