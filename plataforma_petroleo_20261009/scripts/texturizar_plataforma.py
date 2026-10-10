"""Apply supplied colour textures in Blender without editing the source PNGs."""
import bpy
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXTURES = [
    ('white', '01_chapa_branca.png', 'bc57dead-0d67-4b3c-ad9b-1a7015d34c4a',
     'Paineis claros e intemperie', 6.0, .16, .65, .008),
    ('yellow', '02_pintura_amarela.png', 'f434b1e3-51f1-4974-af20-a5853c68783d',
     'Pintura amarela industrial', 2.0, .22, .66, .006),
    ('dark', '03_aco_enferrujado.png', 'df7ea133-75d3-4ad4-8312-ba96caa98825',
     'Aco estrutural escuro', 2.5, .55, .77, .010),
    ('steel', '04_metal_cinza.png', 'ac955511-4a41-49b6-be01-0b5454ec65d1',
     'Aco galvanizado | desgaste procedural', 2.0, .64, .52, .004),
    ('deck', '05_piso_antiderrapante.png', '7d6781e5-5632-4884-80a2-3b99424b28ed',
     'Chapas antiderrapantes', .72, .38, .73, .006),
]


def log(*args):
    print('TEXTURAS:', *args, flush=True)


def scene_signature():
    """Track geometry, parenting, transforms, collision and animation structure."""
    rows = []
    for obj in sorted(bpy.context.scene.objects, key=lambda o: o.name):
        row = [obj.name, obj.type, obj.parent.name if obj.parent else None,
               list(obj.location), list(obj.rotation_euler), list(obj.scale)]
        if obj.type == 'MESH':
            geometry = [(tuple(v.co)) for v in obj.data.vertices]
            geometry += [tuple(p.vertices) for p in obj.data.polygons]
            row += [hashlib.sha256(repr(geometry).encode()).hexdigest()]
        if obj.rigid_body:
            row += [obj.rigid_body.type, obj.rigid_body.collision_shape]
        if obj.animation_data:
            row += [obj.animation_data.action.name if obj.animation_data.action else None,
                    [(f.data_path, f.array_index, f.driver.expression)
                     for f in obj.animation_data.drivers]]
        rows.append(row)
    return hashlib.sha256(json.dumps(rows).encode()).hexdigest()


def apply_textures():
    target = ROOT / 'texturas'
    target.mkdir(exist_ok=True)
    records = []
    mats = {}
    for key, filename, clip_id, material_name, metres, metallic, roughness, depth in TEXTURES:
        dest = target / filename
        source = Path('C:/Users/erons/AppData/Local/Temp') / ('codex-clipboard-' + clip_id + '.png')
        if source.exists():
            shutil.copy2(source, dest)
        if not dest.exists():
            raise FileNotFoundError(str(dest))
        digest = hashlib.sha256(dest.read_bytes()).hexdigest()
        if source.exists() and digest != hashlib.sha256(source.read_bytes()).hexdigest():
            raise RuntimeError('Original texture copy differs: ' + filename)
        image = bpy.data.images.load(str(dest), check_existing=True)
        image.colorspace_settings.name = 'sRGB'
        image.pack()
        mat = bpy.data.materials[material_name]
        mats[key] = mat
        mat.use_nodes = True
        nodes, links = mat.node_tree.nodes, mat.node_tree.links
        nodes.clear()
        output = nodes.new('ShaderNodeOutputMaterial'); output.location = (740, 40)
        surface = nodes.new('ShaderNodeBsdfPrincipled'); surface.location = (430, 40)
        surface.inputs['Metallic'].default_value = metallic
        surface.inputs['Roughness'].default_value = roughness
        links.new(surface.outputs['BSDF'], output.inputs['Surface'])
        uv = nodes.new('ShaderNodeUVMap'); uv.uv_map = 'UV_Industrial'; uv.location = (-900, 160)
        mapping = nodes.new('ShaderNodeMapping'); mapping.location = (-710, 160)
        # Existing UV_Industrial has one repeat per 5 m. Keep this conversion explicit.
        mapping.inputs['Scale'].default_value = (5 / metres, 5 / metres, 1)
        tex = nodes.new('ShaderNodeTexImage'); tex.image = image; tex.extension = 'REPEAT'
        tex.interpolation = 'Linear'; tex.location = (-480, 170)
        tex.label = filename + ' | cor original'
        links.new(uv.outputs['UV'], mapping.inputs['Vector'])
        links.new(mapping.outputs['Vector'], tex.inputs['Vector'])
        links.new(tex.outputs['Color'], surface.inputs['Base Color'])
        # Only colour images were supplied. This mild shader relief is an approximation,
        # not a measured normal/height map, and does not change the collision geometry.
        grayscale = nodes.new('ShaderNodeRGBToBW'); grayscale.location = (-170, -100)
        bump = nodes.new('ShaderNodeBump'); bump.location = (190, -80)
        bump.label = 'Relevo visual aproximado da imagem de cor'
        bump.inputs['Strength'].default_value = .18
        bump.inputs['Distance'].default_value = depth
        links.new(tex.outputs['Color'], grayscale.inputs['Color'])
        links.new(grayscale.outputs['Val'], bump.inputs['Height'])
        links.new(bump.outputs['Normal'], surface.inputs['Normal'])
        mat['texture_file'] = filename
        mat['tile_metres'] = metres
        mat['texture_source_sha256'] = digest
        mat['relief_is_colour_approximation'] = True
        records.append(dict(key=key, file='texturas/' + filename, material=material_name,
                            tile_metres=metres, source_sha256=digest,
                            resolution=list(image.size), packed=bool(image.packed_file)))
        log(filename, 'embutida', list(image.size))

    # Walking surfaces use the tread pattern. Vertical deck edges use plain metal.
    collision_rows = json.loads((ROOT / 'dados/colisoes.json').read_text(encoding='utf8'))
    walking = [r for r in collision_rows if r['kind'] == 'box' and r['name'].startswith(
        ('Piso do conves', 'Piso superior', 'Entrada ', 'Degrau ', 'Patamar ', 'Saida ',
         'Passagem ', 'Passarela ', 'Doca embarque', 'Mesa de perfuracao'))]
    tread_faces = 0
    for obj in bpy.context.scene.objects:
        if obj.type != 'MESH' or any(c.name == '12_COLISAO_PREPARADA' for c in obj.users_collection):
            continue
        slots = list(obj.data.materials)
        if not all(mat in slots for mat in (mats['deck'], mats['steel'])):
            continue
        deck_idx, steel_idx = slots.index(mats['deck']), slots.index(mats['steel'])
        helipad = any(c.name == '07_HELIPONTO' for c in obj.users_collection)
        for poly in obj.data.polygons:
            current = slots[poly.material_index]
            if current == mats['deck'] and (poly.normal.z < .95 or helipad):
                poly.material_index = steel_idx
            if current not in (mats['deck'], mats['steel']) or poly.normal.z < .95:
                continue
            if obj.name == 'Rampa heliponto':
                poly.material_index = deck_idx; tread_faces += 1; continue
            center = obj.matrix_world @ poly.center
            for row in walking:
                c, s = row['center'], row['size']
                if (abs(center.z - (c[2] + s[2] / 2)) < .006
                    and abs(center.x - c[0]) < s[0] / 2 + .001
                    and abs(center.y - c[1]) < s[1] / 2 + .001):
                    poly.material_index = deck_idx; tread_faces += 1; break
        obj.data.update()
    report = dict(textures=records, walking_faces=tread_faces,
                  source_images_edited=False, relief='Shader approximation from supplied colour PNGs',
                  in_game_exported=False)
    (ROOT / 'dados/texturas.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
    return report


def validate_textures(report):
    checks = []
    for row in report['textures']:
        mat = bpy.data.materials[row['material']]
        nodes = mat.node_tree.nodes
        textures = [n for n in nodes if n.type == 'TEX_IMAGE']
        users = sum(1 for o in bpy.context.scene.objects if o.type == 'MESH'
                    and not any(c.name == '12_COLISAO_PREPARADA' for c in o.users_collection)
                    for p in o.data.polygons if o.data.materials[p.material_index] == mat)
        passed = (len(textures) == 1 and bool(textures[0].image.packed_file)
                  and users > 0 and hashlib.sha256((ROOT / row['file']).read_bytes()).hexdigest()
                  == row['source_sha256'])
        checks.append(dict(texture=row['file'], passed=passed, used_polygons=users))
    checks.append(dict(name='Pisadas texturizadas', passed=report['walking_faces'] >= 100,
                       faces=report['walking_faces']))
    return checks


def main():
    path = ROOT / 'plataforma_petroleo.blend'
    bpy.ops.wm.open_mainfile(filepath=str(path))
    scene = bpy.context.scene; scene.frame_set(1)
    before = scene_signature()
    backup = ROOT / 'backups/plataforma_antes_texturas.blend'
    backup.parent.mkdir(exist_ok=True)
    if not backup.exists():
        shutil.copy2(path, backup)
    report = apply_textures()
    checks = validate_textures(report)
    checks.append(dict(name='Geometria, parentes, colisao e controles preservados',
                       passed=scene_signature() == before))
    if not all(c['passed'] for c in checks):
        raise RuntimeError(repr(checks))
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(path), compress=True)
    # Reopen to check the saved file, not just the in-memory material graph.
    bpy.ops.wm.open_mainfile(filepath=str(path))
    checks += validate_textures(report)
    verification = dict(passed=all(c['passed'] for c in checks), checks=checks,
                        in_game_verified=False)
    (ROOT / 'dados/verificacao_texturas.json').write_text(
        json.dumps(verification, ensure_ascii=False, indent=2), encoding='utf8')
    if not verification['passed']:
        raise RuntimeError('Textures did not survive reopening')
    log('VERIFICADO', verification['passed'])
    if '--sem-render' in sys.argv:
        return
    scene = bpy.context.scene
    scene.render.threads_mode = 'FIXED'; scene.render.threads = 6
    scene.cycles.samples = 32
    for filename, camera in [('01_Plataforma_geral', 'Vista referencia'),
                             ('02_Processo_e_carga', 'Vista producao'),
                             ('03_Refino_e_tubulacoes', 'Vista refino')]:
        scene.camera = bpy.data.objects[camera]
        scene.render.filepath = str(ROOT / 'previews' / (filename + '.png'))
        bpy.ops.render.render(write_still=True)
        log('RENDER', filename)
    scene.camera = bpy.data.objects['Vista referencia']
    log('TEXTURIZACAO_CONCLUIDA')


if __name__ == '__main__':
    main()
