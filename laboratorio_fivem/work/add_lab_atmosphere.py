"""Add rack mesh, foil duct cladding, wet floor details and brighter LEDs."""
import copy
import io
import math
import sys
from pathlib import Path

import numpy as np

sys.path[:0] = [
    r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps',
    r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\media_deps',
]
from PIL import Image, ImageDraw, ImageFilter
from szio.gta5 import try_load_asset, save_asset, AssetTarget, AssetFormat, AssetVersion
from szio.gta5.drawables import LodLevel
from szio.types import DataSource, Vector

ROOT = Path(__file__).resolve().parents[2]
STREAM = ROOT / 'server-data/resources/cidade_laboratorio/stream'
SOURCE = ROOT / 'laboratorio_fivem/backup_before_atmosphere_fix'
if not SOURCE.is_dir():
    SOURCE = STREAM
OUT = ROOT / 'laboratorio_fivem/atmosphere_fix'
OUT.mkdir(exist_ok=True)
TARGET = (AssetTarget(AssetFormat.NATIVE, AssetVersion.GEN8),)
RNG = np.random.default_rng(62421)


def dds(im):
    out = io.BytesIO()
    im.save(out, format='DDS', pixel_format='DXT5')
    return out.getvalue()


def use_texture(asset, template_key, new_key, image):
    texture = copy.deepcopy(asset.shader_group.embedded_textures[template_key])
    texture.name = new_key
    texture.width, texture.height = image.size
    texture.data = DataSource.create(dds(image))
    asset.shader_group.embedded_textures[new_key] = texture


def point_geometry(template, positions, normals, uvs, triangles, shader_index, color=(255, 255, 255, 255)):
    geom = copy.deepcopy(template)
    verts = np.zeros(len(positions), dtype=template.vertex_buffer.dtype)
    verts['Position'] = np.asarray(positions, np.float32)
    verts['Normal'] = np.asarray(normals, np.float32)
    verts['TexCoord0'] = np.asarray(uvs, np.float32)
    verts['Colour0'] = color
    if 'Tangent' in verts.dtype.names:
        verts['Tangent'] = (1, 0, 0, 1)
    geom.vertex_buffer = verts
    geom.index_buffer = np.asarray(triangles, dtype=template.index_buffer.dtype).ravel()
    geom.shader_index = shader_index
    return geom


def grid_panel(fn, x_steps, y_steps, uv_fn, normal):
    """A sewn panel with two-sided triangles and mildly curved fabric."""
    pts, norms, uvs, tris = [], [], [], []
    for j in range(y_steps + 1):
        for i in range(x_steps + 1):
            u, v = i / x_steps, j / y_steps
            pts.append(fn(u, v))
            norms.append(normal)
            uvs.append(uv_fn(u, v))
    row = x_steps + 1
    for j in range(y_steps):
        for i in range(x_steps):
            a = j * row + i
            b = a + 1
            c = a + row
            d = c + 1
            tris.extend(((a, b, d), (a, d, c), (d, b, a), (c, d, a)))
    return pts, norms, uvs, tris


def net_texture():
    im = Image.new('RGBA', (512, 512), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)
    # 12 woven cells per repeat. The gaps remain transparent so the plants show.
    for p in range(0, 513, 42):
        draw.line((p, 0, p, 511), fill=(178, 191, 196, 255), width=3)
        draw.line((0, p, 511, p), fill=(178, 191, 196, 255), width=3)
        draw.line((p + 3, 0, p + 3, 511), fill=(91, 103, 110, 210), width=1)
        draw.line((0, p + 3, 511, p + 3), fill=(91, 103, 110, 210), width=1)
    return im


def add_rack_net():
    rack = try_load_asset(SOURCE / 'lab_racks.ydr')
    plant = try_load_asset(STREAM / 'lab_planta_00.ydr')
    shader = copy.deepcopy(plant.shader_group.shaders[0])
    for param in shader.parameters:
        if param.name.lower() == 'diffusesampler':
            param.value = 'lab_net_color'
    rack.shader_group.shaders.append(shader)
    net = net_texture()
    use_texture(rack, next(iter(rack.shader_group.embedded_textures)), 'lab_net_color', net)
    # The cloned texture's format is identical to the plant's alpha-cutout DDS.
    geom_template = plant.models[LodLevel.HIGH][0].geometries[0]
    positions, normals, uvs, triangles = [], [], [], []
    roof_count = side_count = 0

    def append(panel):
        nonlocal roof_count, side_count
        pts, nr, uv, tri = panel
        off = len(positions)
        positions.extend(pts)
        normals.extend(nr)
        uvs.extend(uv)
        triangles.extend(tuple(off + i for i in t) for t in tri)

    for x0, x1 in ((-3.56, -1.40), (1.40, 3.56)):
        # A shallow sag gives the upper fabric a tent-like profile above the LEDs.
        append(grid_panel(
            lambda u, v: (x0 + (x1 - x0) * u, -4.50 + 7.40 * v,
                          2.95 - .07 * math.sin(math.pi * u) + .012 * math.sin(5 * math.pi * v)),
            8, 24, lambda u, v: (u * 2.1, v * 6.0), (0, 0, 1)))
        roof_count += 1
        for side_x, sign in ((x0, -1), (x1, 1)):
            append(grid_panel(
                lambda u, v, sx=side_x, sg=sign: (
                    sx + sg * (.018 * math.sin(7 * math.pi * u) * math.sin(math.pi * v)),
                    -4.50 + 7.40 * u,
                    .30 + 2.63 * v),
                24, 8, lambda u, v: (u * 6.0, v * 2.5), (sign, 0, 0)))
            side_count += 1

    rack.models[LodLevel.HIGH][0].geometries.append(
        point_geometry(geom_template, positions, normals, uvs, triangles, len(rack.shader_group.shaders) - 1))
    save_asset(rack, TARGET, OUT, 'lab_racks')
    net.save(OUT / 'lab_net_preview.png')
    return roof_count, side_count, len(triangles)


def foil_maps():
    size = 1024
    y, x = np.mgrid[:size, :size].astype(np.float32)
    low = np.asarray(Image.fromarray(RNG.integers(0, 256, (64, 64), dtype=np.uint8))
                     .resize((size, size), Image.Resampling.BICUBIC), np.float32) / 255 - .5
    fine = RNG.normal(0, 1, (size, size)).astype(np.float32)
    folds = 12 * np.sin(x * .058 + 1.3 * np.sin(y * .025))
    creases = 13 * np.sin(y * .12 + 1.6 * np.sin(x * .042))
    seams = (x % 128 < 5) * 29 - ((x + 6) % 128 < 4) * 24
    light = np.clip(174 + 40 * low + folds + creases + 11 * fine + seams, 85, 240)
    color = np.stack((light * .98, light, light * 1.02, np.full_like(light, 255)), axis=-1)
    normal = np.stack((np.clip(128 + np.gradient(light, axis=1) * 1.8, 30, 225),
                       np.clip(128 + np.gradient(light, axis=0) * 1.8, 30, 225),
                       np.full_like(light, 245), np.full_like(light, 255)), axis=-1)
    return Image.fromarray(color.astype(np.uint8), 'RGBA'), Image.fromarray(normal.astype(np.uint8), 'RGBA')


def add_foil():
    vent = try_load_asset(SOURCE / 'lab_ventilacao.ydr')
    shader = copy.deepcopy(vent.shader_group.shaders[0])
    names = {'diffusesampler': 'lab_foil_color', 'bumpsampler': 'lab_foil_normal',
             'specsampler': 'lab_foil_spec'}
    for param in shader.parameters:
        key = param.name.lower()
        if key in names:
            param.value = names[key]
        elif key == 'specularintensitymult':
            param.value = Vector((2.4, 0, 0, 0))
        elif key == 'specularfalloffmult':
            param.value = Vector((46, 0, 0, 0))
        elif key == 'bumpiness':
            param.value = Vector((.65, 0, 0, 0))
    vent.shader_group.shaders.append(shader)
    color, normal = foil_maps()
    use_texture(vent, 'lab_ventilacao_0_color', 'lab_foil_color', color)
    use_texture(vent, 'lab_ventilacao_0_normal', 'lab_foil_normal', normal)
    spec = Image.new('RGBA', (8, 8), (222, 225, 227, 255))
    use_texture(vent, 'lab_ventilacao_0_spec', 'lab_foil_spec', spec)
    color.save(OUT / 'lab_foil_preview.png')

    positions, normals, uvs, triangles = [], [], [], []
    axial, radial = 130, 32
    y0, y1 = -5.10, 5.69
    for j in range(axial + 1):
        y = y0 + (y1 - y0) * j / axial
        ridge = .003 * math.sin(2 * math.pi * (y - y0) / .19)
        for i in range(radial + 1):
            angle = 2 * math.pi * i / radial
            wobble = .003 * math.sin(11 * angle + 5 * y)
            rx = rz = .370 + ridge + wobble
            positions.append((rx * math.cos(angle), y, 3.158 + rz * math.sin(angle)))
            normals.append((math.cos(angle), 0, math.sin(angle)))
            uvs.append(((y - y0) / 2.6, i / radial))
    row = radial + 1
    for j in range(axial):
        for i in range(radial):
            a = j * row + i
            b = a + 1
            c = a + row
            d = c + 1
            triangles.extend(((a, d, b), (a, c, d)))

    # The duct across the rear wall is perpendicular to the main ceiling run.
    off = len(positions)
    back_axial, back_radial = 65, 24
    x0, x1 = -2.60, 2.62
    for j in range(back_axial + 1):
        x = x0 + (x1 - x0) * j / back_axial
        ridge = .003 * math.sin(2 * math.pi * (x - x0) / .18)
        for i in range(back_radial + 1):
            angle = 2 * math.pi * i / back_radial
            r = .295 + ridge + .002 * math.sin(9 * angle + 4 * x)
            positions.append((x, 5.69 + r * math.cos(angle), 3.08 + r * math.sin(angle)))
            normals.append((0, math.cos(angle), math.sin(angle)))
            uvs.append(((x - x0) / 2.6, i / back_radial))
    row = back_radial + 1
    for j in range(back_axial):
        for i in range(back_radial):
            a = off + j * row + i
            b = a + 1
            c = a + row
            d = c + 1
            triangles.extend(((a, b, d), (a, d, c)))
    geom = point_geometry(vent.models[LodLevel.HIGH][0].geometries[0],
                          positions, normals, uvs, triangles,
                          len(vent.shader_group.shaders) - 1, (230, 230, 230, 255))
    vent.models[LodLevel.HIGH][0].geometries.append(geom)
    save_asset(vent, TARGET, OUT, 'lab_ventilacao')
    return len(triangles)


def puddle_maps():
    size = 512
    y, x = np.mgrid[:size, :size].astype(np.float32)
    radius = np.sqrt(((x - 256) / 255) ** 2 + ((y - 256) / 255) ** 2)
    low = np.asarray(Image.fromarray(RNG.integers(0, 256, (32, 32), dtype=np.uint8))
                     .resize((size, size), Image.Resampling.BICUBIC), np.float32) / 255 - .5
    glint = 37 * np.exp(-((y - 190 - 10 * np.sin(x * .055)) / 7) ** 2)
    red = 20 * np.exp(-((x - 320 - 15 * np.sin(y * .04)) / 22) ** 2)
    liquid = np.clip(1 - radius, 0, 1) ** .5
    base = np.clip(48 - 29 * liquid + 12 * low + glint + red, 5, 120)
    rgba = np.stack((base + .45 * red, base + .06 * red, base + .2 * glint,
                     np.full_like(base, 255)), axis=-1)
    # Water receives concentrated specular highlights without changing the floor.
    spec = np.clip(40 + 200 * liquid + 20 * low, 0, 255)
    spec_rgba = np.stack((spec, spec, spec, np.full_like(spec, 255)), axis=-1)
    norm = np.stack((np.clip(128 + 4 * np.sin(x * .1), 0, 255),
                     np.clip(128 + 4 * np.sin(y * .12), 0, 255),
                     np.full_like(base, 250), np.full_like(base, 255)), axis=-1)
    return (Image.fromarray(rgba.astype(np.uint8), 'RGBA'),
            Image.fromarray(norm.astype(np.uint8), 'RGBA'),
            Image.fromarray(spec_rgba.astype(np.uint8), 'RGBA'))


def add_puddles():
    floor = try_load_asset(SOURCE / 'lab_piso.ydr')
    shader = copy.deepcopy(floor.shader_group.shaders[0])
    names = {'diffusesampler': 'lab_puddle_color', 'bumpsampler': 'lab_puddle_normal',
             'specsampler': 'lab_puddle_spec'}
    for param in shader.parameters:
        key = param.name.lower()
        if key in names:
            param.value = names[key]
        elif key == 'specularintensitymult':
            param.value = Vector((2.8, 0, 0, 0))
        elif key == 'specularfalloffmult':
            param.value = Vector((32, 0, 0, 0))
    floor.shader_group.shaders.append(shader)
    col, norm, spec = puddle_maps()
    for key, im, old in (('lab_puddle_color', col, 'lab_piso_0_color'),
                         ('lab_puddle_normal', norm, 'lab_piso_0_normal'),
                         ('lab_puddle_spec', spec, 'lab_piso_0_spec')):
        use_texture(floor, old, key, im)
    col.save(OUT / 'lab_puddle_preview.png')

    positions, normals, uvs, triangles = [], [], [], []
    patches = [(-.75, -3.82, .62, .36, .15), (.87, -1.81, .42, .28, 1.1),
               (-.72, .20, .58, .37, 2.2), (.75, 2.33, .51, .32, .8),
               (-.39, 4.00, .38, .25, 1.7)]
    segments = 48
    for cx, cy, rx, ry, phase in patches:
        off = len(positions)
        positions.append((cx, cy, .038))
        normals.append((0, 0, 1))
        uvs.append((.5, .5))
        for k in range(segments + 1):
            a = 2 * math.pi * k / segments
            irregular = 1 + .11 * math.sin(5 * a + phase) + .08 * math.sin(9 * a - 2 * phase)
            xx = rx * irregular * math.cos(a)
            yy = ry * irregular * math.sin(a)
            positions.append((cx + xx, cy + yy, .037))
            normals.append((0, 0, 1))
            uvs.append((.5 + .49 * xx / rx, .5 + .49 * yy / ry))
            if k < segments:
                triangles.append((off, off + k + 1, off + k + 2))
    geom = point_geometry(floor.models[LodLevel.HIGH][0].geometries[0],
                          positions, normals, uvs, triangles,
                          len(floor.shader_group.shaders) - 1, (255, 255, 255, 255))
    floor.models[LodLevel.HIGH][0].geometries.append(geom)
    save_asset(floor, TARGET, OUT, 'lab_piso')
    return len(patches), len(triangles)


def boost_leds():
    leds = try_load_asset(SOURCE / 'lab_leds.ydr')
    for param in leds.shader_group.shaders[2].parameters:
        if param.name.lower() == 'emissivemultiplier':
            param.value = Vector((5.5, 0, 0, 0))
    save_asset(leds, TARGET, OUT, 'lab_leds')


def update_archetypes():
    typ = try_load_asset(SOURCE / 'cidade_laboratorio.ytyp')
    for name in ('lab_racks', 'lab_piso', 'lab_ventilacao'):
        asset = try_load_asset(OUT / (name + '.ydr'))
        p = np.concatenate([g.vertex_buffer['Position'] for models in asset.models.values()
                            for model in models for g in model.geometries])
        lo, hi = p.min(0), p.max(0)
        archetype = next(a for a in typ.archetypes if a.name == name)
        archetype.bb_min = Vector(lo)
        archetype.bb_max = Vector(hi)
        archetype.bs_center = Vector((lo + hi) / 2)
        archetype.bs_radius = float(np.linalg.norm(hi - lo) / 2)
    save_asset(typ, TARGET, OUT, 'cidade_laboratorio')


if __name__ == '__main__':
    roofs, sides, net_triangles = add_rack_net()
    foil_triangles = add_foil()
    puddles, puddle_triangles = add_puddles()
    boost_leds()
    update_archetypes()
    for name in ('lab_racks.ydr', 'lab_ventilacao.ydr', 'lab_piso.ydr',
                 'lab_leds.ydr', 'cidade_laboratorio.ytyp'):
        assert try_load_asset(OUT / name) is not None, name
    print('ATMOSPHERE_OK', roofs, 'roofs', sides, 'sides', net_triangles,
          'net_triangles', foil_triangles, 'foil_triangles', puddles,
          'puddles', puddle_triangles, 'puddle_triangles', flush=True)
