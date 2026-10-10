"""Full-island native soil finish, using the installed game's terrain textures.

Unlike the earlier port-only pass, every existing terrain sector gets a shared
four-layer normal-mapped shader. Height, placement and collision stay intact.
Run with Python for native assets, or Blender --background --python this.py --
--blender for a separately saved authoring scene. No source raster is edited.
"""
from pathlib import Path
import copy
import hashlib
import json
import math
import struct
import sys
import time

O = Path(__file__).resolve().parents[1]
P = O.parent
R = P.parent
D = Path('C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work')
sys.path[:0] = [str(R / 'laboratorio_fivem/work/pydeps'), str(D / 'deps')]
import numpy as np

OUT = O / 'qualidade_terreno'
STREAM = OUT / 'stream'
DATA = OUT / 'dados'
for folder in [STREAM, DATA]:
    folder.mkdir(parents=True, exist_ok=True)

TEXTURES = P / 'amostra_natural/texturas'
CONFIG = json.loads((P / 'amostra_natural/config.json').read_text(encoding='utf8'))
# Native terrain_cb_4lyr uses B to blend each pair and G to blend the pairs.
LAYERS = [CONFIG['layers'][i] for i in [0, 4, 2, 3]]
LAYERNAMES = ['grama', 'areia', 'barro', 'rocha']
TXDNAME = 'pe_terreno_hd'
TILE_ROWS = json.loads((P / 'dados/medidas.json').read_text(encoding='utf8'))['tiles']
EXISTING_TILE_NAMES = {r['name'] for r in TILE_ROWS}


def complete_tiles(grid):
    """The graded port adds a small beach in an originally submerged sector."""
    rows = {r['name']:dict(r, new_sector=False) for r in TILE_ROWS}
    for j in range(8):
        for i in range(8):
            name=f'ti_terreno_{j:02}_{i:02}'
            bounds=[i*96,j*96,(i+1)*96,(j+1)*96]
            patch=grid[j*96:(j+1)*96+1,i*96:(i+1)*96+1]
            if name not in rows and np.any(patch[:,:,2]>0):
                rows[name]={'name':name,'grid_bounds':bounds,'new_sector':True}
    return [rows[name] for name in sorted(rows)]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def smooth(a, b, values):
    t = np.clip((values - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def distance_to_sea(z, dx, dy):
    """Bounded world-space distance field; shore blend only needs its first 80m."""
    distance = np.where(z <= .3, 0., 1000.).astype(np.float32)
    diagonal = math.hypot(dx, dy)
    # Jacobi chamfer iterations avoid a SciPy dependency in Blender and Python.
    # Each iteration advances one cell; 24 exceeds the 40m beach transition.
    for _ in range(24):
        old = distance.copy()
        np.minimum(distance[1:], old[:-1] + dy, out=distance[1:])
        np.minimum(distance[:-1], old[1:] + dy, out=distance[:-1])
        np.minimum(distance[:, 1:], old[:, :-1] + dx, out=distance[:, 1:])
        np.minimum(distance[:, :-1], old[:, 1:] + dx, out=distance[:, :-1])
        np.minimum(distance[1:, 1:], old[:-1, :-1] + diagonal, out=distance[1:, 1:])
        np.minimum(distance[:-1, :-1], old[1:, 1:] + diagonal, out=distance[:-1, :-1])
        np.minimum(distance[1:, :-1], old[:-1, 1:] + diagonal, out=distance[1:, :-1])
        np.minimum(distance[:-1, 1:], old[1:, :-1] + diagonal, out=distance[:-1, 1:])
    return distance


def river_distance(x, y, points, levels, widths):
    nearest = np.full(x.shape, np.inf, np.float32)
    water = np.zeros(x.shape, np.float32)
    halfwidth = np.zeros(x.shape, np.float32)
    for i, (a, b) in enumerate(zip(points[:-1], points[1:])):
        vx, vy = b - a
        t = np.clip(((x - a[0]) * vx + (y - a[1]) * vy) / (vx * vx + vy * vy), 0, 1)
        d = (x - a[0] - t * vx) ** 2 + (y - a[1] - t * vy) ** 2
        mask = d < nearest
        nearest[mask] = d[mask]
        water[mask] = (levels[i] + t * (levels[i + 1] - levels[i]))[mask]
        halfwidth[mask] = (widths[i] + t * (widths[i + 1] - widths[i]))[mask]
    return np.sqrt(nearest), water, halfwidth


def fields():
    grid = np.load(O / 'dados/terreno.npz')['terrain']
    x, y, z = np.moveaxis(grid, -1, 0)
    dx = float(x[0, 1] - x[0, 0])
    dy = float(y[1, 0] - y[0, 0])
    gy, gx = np.gradient(z, dy, dx)
    slope = np.hypot(gx, gy)
    normal = np.stack([-gx, -gy, np.ones_like(z)], axis=-1)
    normal /= np.linalg.norm(normal, axis=-1, keepdims=True)
    tangent = np.stack([np.ones_like(z), np.zeros_like(z), gx], axis=-1)
    tangent -= normal * (normal * tangent).sum(-1, keepdims=True)
    tangent /= np.linalg.norm(tangent, axis=-1, keepdims=True)

    shore_distance = distance_to_sea(z, dx, dy)
    patch = .5 + .24 * np.sin(x / 29 + .6 * np.sin(y / 57)) + .16 * np.sin(y / 31 - x / 73)
    shore_width = 28 + 9 * np.sin(x / 77 + y / 115)
    sand = (1 - smooth(7, shore_width, shore_distance)) * (1 - smooth(8, 18, z))
    sand *= 1 - smooth(.48, .80, slope)
    sand = np.where(z <= .3, 1., sand)

    old = np.load(P / 'dados/terreno.npz')
    rd, rz, rw = river_distance(x, y, old['river_points'], old['river_z'], old['river_halfwidth'])
    wet = (1 - smooth(rw + 2, rw + 22, rd)) * (1 - smooth(2, 9, np.maximum(z - rz, 0)))
    # The port reshapes the south-western river; its original channel must no
    # longer paint a second wet strip across the graded neighbourhood.
    port_region = (x > -380) & (x < 880) & (y > -1160) & (y < 70)
    wet[port_region] = 0
    py = y + 850
    new_river_x = -35 + 32 * np.sin((py + 50) / 125)
    new_width = 10 + 8 * np.exp(-((py - 55) / 150) ** 2)
    new_water = np.maximum(0, (py - 185) * .035)
    new_wet = (1 - smooth(new_width + 2, new_width + 21, abs(x - new_river_x)))
    new_wet *= 1 - smooth(2, 8, np.maximum(z - new_water, 0))
    new_wet *= port_region & (py > -100) & (py < 795)
    wet = np.maximum(wet, new_wet)

    # Earthen river trail uses the existing plan rather than an invented road.
    plan = json.loads((P / 'porto_esperanca/dados/implantacao.json').read_text(encoding='utf8'))
    dirt = np.zeros_like(z)
    for route in plan['rotas']:
        if route['kind'] != 'terra':
            continue
        points = np.asarray(route['points']) + np.array([250, -850])
        for a, b in zip(points[:-1], points[1:]):
            vx, vy = b - a
            t = np.clip(((x-a[0])*vx + (y-a[1])*vy) / (vx*vx + vy*vy), 0, 1)
            d = np.hypot(x-a[0]-t*vx, y-a[1]-t*vy)
            dirt = np.maximum(dirt, 1-smooth(route['width']/2, route['width']/2+2.5, d))

    # Soil variation is continuous across sector borders and broad enough to
    # avoid the previous 8-pixel block texture's repeated checker pattern.
    mud = (.075 + .11 * patch) * (1 - smooth(.40, .75, slope))
    mud = np.maximum(mud, wet * (.68 + .17 * patch))
    mud = np.maximum(mud, dirt * .78)
    mud *= (1 - sand) * smooth(.3, 1.6, z)
    rock = smooth(.52, 1.05, slope)
    rock = np.maximum(rock, smooth(255, 345, z) * smooth(.25, .7, slope))
    rock *= smooth(1, 10, z)

    mask = np.zeros(grid.shape[:2] + (4,), np.uint8)
    mask[..., 1] = np.rint(np.maximum(mud, rock) * 255).astype(np.uint8)
    mask[..., 2] = np.rint(np.maximum(sand, rock) * 255).astype(np.uint8)
    mask[..., 3] = 255
    return grid, normal.astype(np.float32), tangent.astype(np.float32), mask, shore_distance


def faces(ny, nx):
    j, i = np.meshgrid(np.arange(ny-1), np.arange(nx-1), indexing='ij')
    q = (j*nx+i).ravel()
    return np.stack([np.stack([q, q+1, q+nx+1], 1), np.stack([q, q+nx+1, q+nx], 1)], 1).reshape(-1, 3).astype(np.uint16)


def native_export(grid, normals, tangents, mask):
    from szio.gta5 import (
        AssetDrawable, AssetTextureDictionary, EmbeddedTexture, AssetTarget,
        AssetFormat, AssetVersion, LodLevel, save_asset, try_load_asset,
    )
    from szio.gta5.drawables import Geometry, Model, ShaderGroup, VertexDataType
    from szio.gta5.bounds import AssetBoundBvh, AssetBoundComposite, BoundVertex, BoundPrimitive, CollisionFlags, CollisionMaterial
    from szio.gta5.maps import AssetMapData, MapContentFlags
    from szio.gta5.entities import Entity, EntityFlags, EntityLodLevel, EntityPriorityLevel
    from szio.types import Vector, Quaternion, DataSource
    import re

    start = time.time()
    target = (AssetTarget(AssetFormat.NATIVE, AssetVersion.GEN8),)
    pilot = try_load_asset(P / 'amostra_natural/exportados/ti_terreno_03_01.ydr')
    shader = copy.deepcopy(next(s for s in pilot.shader_group.shaders if s.preset_filename == 'terrain_cb_4lyr.sps'))
    shader.name = 'terrain_cb_4lyr'
    references = {}
    for i, layer in enumerate(LAYERS):
        references['texturesampler_layer'+str(i)] = layer['diffuse']
        references['bumpsampler_layer'+str(i)] = layer['normal']
    for parameter in shader.parameters:
        key = str(parameter.name).lower()
        if key in references:
            parameter.value = references[key]
        elif key == 'wetnessmultiplier':
            parameter.value = Vector((.3, 0, 0, 0))
        elif key == 'specularintensitymult':
            parameter.value = Vector((.012, 0, 0, 0))

    textures = {}
    for name in references.values():
        file = TEXTURES / (name + '.dds')
        data = file.read_bytes()
        h, w = struct.unpack_from('<II', data, 12)
        textures[name] = EmbeddedTexture(name, w, h, DataSource.create(data, name=name+'.dds'))
    save_asset(AssetTextureDictionary(textures=textures), target, STREAM, TXDNAME)

    typ = try_load_asset(R / 'server-data/resources/teste_ilha/stream/teste_ilha.ytyp')
    dtype = np.dtype([
        ('Position', '<f4', 3), ('Normal', '<f4', 3), ('Colour0', 'u1', 4),
        ('Colour1', 'u1', 4), ('TexCoord0', '<f4', 2), ('Tangent', '<f4', 4),
    ])
    lods = [LodLevel.HIGH, LodLevel.MEDIUM, LodLevel.LOW, LodLevel.VERYLOW]
    rows = []
    material_names=re.findall(r'CollisionMaterialDef\("([A-Z_0-9]+)"',(D/'sollumz/Sollumz/ybn/collision_materials.py').read_text())

    def set_bounds(bound, v):
        lo=v.min(0);hi=v.max(0)
        bound.bb_min=Vector(lo);bound.bb_max=Vector(hi)
        bound.centroid=Vector((lo+hi)*.5);bound.cg=bound.centroid
        bound.radius_around_centroid=float(np.linalg.norm(hi-lo)*.5)

    def new_collision(name, patch, weights):
        vertices=patch.reshape(-1,3);ny,nx=patch.shape[:2];triangles=faces(ny,nx)
        bound=AssetBoundBvh();bound.margin=.002
        bound.composite_collision_type_flags=CollisionFlags.MAP_TYPE_MOVER|CollisionFlags.MAP_TYPE_VEHICLE|CollisionFlags.MAP_TYPE_WEAPON|CollisionFlags.MAP_TYPE_COVER
        bound.composite_collision_include_flags=CollisionFlags(0xffffffff)
        bound.geometry_vertices=[BoundVertex(Vector(p),None) for p in vertices]
        materials=[CollisionMaterial.from_packed(material_names.index(n)) for n in ['GRASS','SAND_LOOSE','MUD_SOFT','ROCK']]
        g=weights.reshape(-1,4)[:,1].astype(np.float32)/255;b=weights.reshape(-1,4)[:,2].astype(np.float32)/255
        mixture=np.stack([(1-g)*(1-b),(1-g)*b,g*(1-b),g*b],-1)
        dominant=mixture[triangles].mean(1).argmax(-1)
        bound.geometry_primitives=[BoundPrimitive.new_triangle(*(int(i) for i in t),materials[m]) for t,m in zip(triangles,dominant)]
        set_bounds(bound,vertices);composite=AssetBoundComposite(children=[bound]);set_bounds(composite,vertices)
        save_asset(composite,target,STREAM,name)

    for tile in complete_tiles(grid):
        name = tile['name']
        x0, y0, x1, y1 = tile['grid_bounds']
        patch = grid[y0:y1+1, x0:x1+1]
        center = np.array([(patch[0,0,0]+patch[-1,-1,0])*.5, (patch[0,0,1]+patch[-1,-1,1])*.5, 0], np.float32)
        drawable = AssetDrawable(name=name, shader_group=ShaderGroup([copy.deepcopy(shader)], {}))
        counts = {}
        for lod, step in zip(lods, [1,2,4,8]):
            g = patch[::step, ::step]
            ny, nx = g.shape[:2]
            buffer = np.zeros(ny*nx, dtype)
            buffer['Position'] = g.reshape(-1,3) - center
            buffer['Normal'] = normals[y0:y1+1:step, x0:x1+1:step].reshape(-1,3)
            buffer['Tangent'][:,:3] = tangents[y0:y1+1:step, x0:x1+1:step].reshape(-1,3)
            # Match the handedness used by the validated native pilot exporter.
            buffer['Tangent'][:,3] = 1
            buffer['Colour0'] = [255,255,255,255]
            buffer['Colour1'] = mask[y0:y1+1:step, x0:x1+1:step].reshape(-1,4)
            buffer['TexCoord0'] = g[:,:,:2].reshape(-1,2) / 6
            buffer['TexCoord0'][:,1] = 1-buffer['TexCoord0'][:,1]
            tri = faces(ny, nx)
            geom = Geometry(VertexDataType.DEFAULT, buffer, tri.ravel(), np.array([],np.uint16), 0)
            drawable.models[lod] = [Model(0, [geom], 1, False, 0, 0)]
            counts[lod.name] = len(tri)
        drawable.lod_thresholds = dict(zip(lods, [420.,850.,1800.,6500.]))
        drawable.bounds = None
        save_asset(drawable, target, STREAM, name)
        arch = next((t for t in typ.archetypes if str(t.name) == name),None)
        if arch is None:
            arch=copy.deepcopy(next(t for t in typ.archetypes if str(t.name)=='ti_terreno_01_05'))
            arch.name=name;arch.asset_name=name;arch.physics_dictionary=name
            v=patch.reshape(-1,3)-center;lo=v.min(0);hi=v.max(0)
            arch.bb_min=Vector(lo);arch.bb_max=Vector(hi);arch.bs_center=Vector((lo+hi)*.5)
            arch.bs_radius=float(np.linalg.norm(hi-lo)*.5);typ.archetypes.append(arch)
            new_collision(name,patch,mask[y0:y1+1,x0:x1+1])
            entity=Entity(name,Vector(center),Quaternion((1,0,0,0)),1,1,EntityFlags.IS_STATIC,0,-1,6500,0,EntityLodLevel.ORPHANHD,EntityPriorityLevel.REQUIRED,0,255,255,0,[])
            mapname=name+'_map'
            save_asset(AssetMapData(name=mapname,content_flags=MapContentFlags.HAS_ENTITIES_HD|MapContentFlags.HAS_PHYSICS,entities=[entity],physics_dictionaries=[name],streaming_extents=(Vector(center+lo-6500),Vector(center+hi+6500)),entities_extents=(Vector(center+lo-.01),Vector(center+hi+.01))),target,STREAM,mapname)
        # Positions and bounding boxes still match the original mesh. Only the
        # texture dictionary changes; maps and collision remain untouched.
        arch.texture_dictionary = TXDNAME
        rows.append({'name':name, 'grid_bounds':tile['grid_bounds'], 'center':center.tolist(), 'lod_triangles':counts,'new_sector':tile['new_sector']})
        print('TERRAIN_QUALITY_NATIVE', name, flush=True)
    save_asset(typ, target, STREAM, 'teste_ilha')
    report = {
        'revision':'solo-ilha-20261009-qualidade-1', 'sectors':rows,
        'shader':'terrain_cb_4lyr.sps', 'layers':LAYERS, 'texture_dictionary':TXDNAME,
        'tile_metres':6, 'normal_source':'global terrain derivatives; identical shared-border normals',
        'collision_policy':'existing 42 YBN files untouched; one new beach YBN matches the current full grid',
        'terrain_npz_sha256':sha(O/'dados/terreno.npz'),
        'collision_sha256':{t['name']:sha(R/'server-data/resources/teste_ilha/stream'/(t['name']+'.ybn')) for t in TILE_ROWS},
        'elapsed_s':round(time.time()-start,2), 'in_game_verified':False,
    }
    (DATA/'terrain_quality.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    (DATA/'setores_solo.json').write_text(json.dumps(rows,indent=2),encoding='utf8')
    validate()


def validate():
    from szio.gta5 import try_load_asset, LodLevel
    lods = [LodLevel.HIGH,LodLevel.MEDIUM,LodLevel.LOW,LodLevel.VERYLOW]
    report = json.loads((DATA/'terrain_quality.json').read_text(encoding='utf8'))
    dictionary = try_load_asset(STREAM/(TXDNAME+'.ytd'))
    typ = try_load_asset(STREAM/'teste_ilha.ytyp')
    checks = []

    def check(name, passed, **details):
        checks.append(dict(name=name,passed=bool(passed),**details))
        if not passed:
            raise AssertionError(name)

    grid=np.load(O/'dados/terreno.npz')['terrain']
    expected=complete_tiles(grid)
    check('all_land_sectors', {r['name'] for r in report['sectors']} == {r['name'] for r in expected})
    check('existing_42_preserved', len(TILE_ROWS)==42 and EXISTING_TILE_NAMES.issubset({r['name'] for r in report['sectors']}))
    coverage=np.zeros(grid.shape[:2],bool)
    edges = {}
    for row in report['sectors']:
        name = row['name']
        x0,y0,x1,y1=row['grid_bounds'];coverage[y0:y1+1,x0:x1+1]=True
        drawable = try_load_asset(STREAM/(name+'.ydr'))
        check('shader_'+name, [s.preset_filename for s in drawable.shader_group.shaders] == ['terrain_cb_4lyr.sps'])
        references = [p.value for p in drawable.shader_group.shaders[0].parameters if isinstance(p.value,str)]
        check('textures_'+name, len(references)==8 and all(n in dictionary.textures for n in references))
        arch = next(t for t in typ.archetypes if str(t.name)==name)
        check('dictionary_'+name, str(arch.texture_dictionary)==TXDNAME)
        for lod in lods:
            ge = drawable.models[lod][0].geometries[0]
            v = ge.vertex_buffer
            check('layout_'+name+'_'+lod.name, set(v.dtype.names)=={'Position','Normal','Colour0','Colour1','TexCoord0','Tangent'})
            check('buffer_'+name+'_'+lod.name, len(ge.index_buffer)%3==0 and ge.index_buffer.max()<len(v) and np.isfinite(v['Position']).all() and np.isfinite(v['TexCoord0']).all())
            check('normal_'+name+'_'+lod.name, np.allclose(np.linalg.norm(v['Normal'],axis=1),1,atol=1e-4))
            check('tangent_'+name+'_'+lod.name, np.allclose(np.linalg.norm(v['Tangent'][:,:3],axis=1),1,atol=1e-4) and np.max(abs(np.sum(v['Normal']*v['Tangent'][:,:3],axis=1)))<1e-4)
            check('triangles_'+name+'_'+lod.name, len(ge.index_buffer)//3==row['lod_triangles'][lod.name])
            if lod==LodLevel.HIGH:
                x0,y0,x1,y1=row['grid_bounds'];n=x1-x0+1
                for j,i in [(j,0) for j in range(n)]+[(j,n-1) for j in range(n)]+[(0,i) for i in range(n)]+[(n-1,i) for i in range(n)]:
                    q=v[j*n+i];key=(x0+i,y0+j)
                    sample=(q['Normal'],q['Colour1'],q['TexCoord0'])
                    if key in edges:
                        old=edges[key]
                        check('border_'+name+'_'+str(key), all(np.array_equal(a,b) for a,b in zip(sample,old)))
                    else:
                        edges[key]=sample
        if not row['new_sector']:
            check('collision_unchanged_'+name, sha(R/'server-data/resources/teste_ilha/stream'/(name+'.ybn'))==report['collision_sha256'][name])
            check('no_existing_collision_output_'+name,not (STREAM/(name+'.ybn')).exists())
        else:
            collision=try_load_asset(STREAM/(name+'.ybn')).children[0]
            vertices=np.array([list(v.co) for v in collision.geometry_vertices]);patch=grid[y0:y1+1,x0:x1+1].reshape(-1,3)
            # Native YBN spatial packing quantizes world-space values slightly.
            check('new_collision_matches_grid_'+name,vertices.shape==patch.shape and np.max(abs(vertices-patch))<.012)
            check('new_collision_full_resolution_'+name,len(collision.geometry_primitives)==18432)
            mapdata=try_load_asset(STREAM/(name+'_map.ymap'))
            check('new_map_physics_'+name,mapdata.physics_dictionaries==[name] and len(mapdata.entities)==1 and str(mapdata.entities[0].archetype_name)==name and str(arch.physics_dictionary)==name)
    check('every_positive_land_vertex_covered',not np.any((grid[:,:,2]>0)&~coverage))
    result={'passed':True,'checks':checks,'models':len(report['sectors']),'textures':len(dictionary.textures),'in_game_verified':False}
    (DATA/'validacao_terreno.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    print('TERRAIN_QUALITY_VALIDATED', len(checks), flush=True)


def blender_scene(grid, normals, mask):
    import bpy
    from mathutils import Matrix
    bpy.ops.wm.open_mainfile(filepath=str(O/'ilha_porto_esperanca.blend'))
    mat=bpy.data.materials.new('Solo ilha | grama areia barro rocha | nativo HD')
    mat.use_nodes=True
    mat['native_shader']='terrain_cb_4lyr.sps'
    mat['native_texture_dictionary']=TXDNAME
    nodes=mat.node_tree.nodes; links=mat.node_tree.links
    bs=nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.92
    bs.inputs['Specular IOR Level'].default_value=.05
    attribute=nodes.new('ShaderNodeAttribute');attribute.attribute_name='Solo_Mistura'
    separate=nodes.new('ShaderNodeSeparateColor');links.new(attribute.outputs['Color'],separate.inputs['Color'])
    uv=nodes.new('ShaderNodeUVMap');uv.uv_map='UVMap 0'
    images=[];nimages=[]
    for layer in LAYERS:
        for channel,arr in [('diffuse',images),('normal',nimages)]:
            im=bpy.data.images.load(str(TEXTURES/(layer[channel]+'.dds')),check_existing=True)
            if channel=='normal':im.colorspace_settings.name='Non-Color'
            im.pack();tx=nodes.new('ShaderNodeTexImage');tx.image=im;links.new(uv.outputs['UV'],tx.inputs['Vector']);arr.append(tx)
    def mix_layers(arr):
        pairs=[]
        for a,b in [(0,1),(2,3)]:
            node=nodes.new('ShaderNodeMixRGB');links.new(separate.outputs['Blue'],node.inputs[0]);links.new(arr[a].outputs['Color'],node.inputs[1]);links.new(arr[b].outputs['Color'],node.inputs[2]);pairs.append(node)
        node=nodes.new('ShaderNodeMixRGB');links.new(separate.outputs['Green'],node.inputs[0]);links.new(pairs[0].outputs['Color'],node.inputs[1]);links.new(pairs[1].outputs['Color'],node.inputs[2]);return node
    links.new(mix_layers(images).outputs['Color'],bs.inputs['Base Color'])
    nm=nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=1;links.new(mix_layers(nimages).outputs['Color'],nm.inputs['Color']);links.new(nm.outputs['Normal'],bs.inputs['Normal'])
    for tile in complete_tiles(grid):
        x0,y0,x1,y1=tile['grid_bounds']
        for suffix,step in [('',1),('_MED',2),('_LOW',4),('_VLOW',8)]:
            obj=bpy.data.objects.get(tile['name']+suffix)
            if obj is None:
                prototype=bpy.data.objects['ti_terreno_01_05'+suffix]
                obj=prototype.copy();obj.name=tile['name']+suffix;prototype.users_collection[0].objects.link(obj)
            g=grid[y0:y1+1:step,x0:x1+1:step];ny,nx=g.shape[:2]
            mesh=bpy.data.meshes.new(obj.name+' | acabamento solo')
            mesh.from_pydata(g.reshape(-1,3).tolist(),[],faces(ny,nx).tolist());mesh.update()
            mesh.materials.append(mat)
            nrm=normals[y0:y1+1:step,x0:x1+1:step].reshape(-1,3)
            for p in mesh.polygons:p.use_smooth=True
            mesh.normals_split_custom_set_from_vertices(nrm.tolist())
            vertex_indices=np.empty(len(mesh.loops),np.int32);mesh.loops.foreach_get('vertex_index',vertex_indices)
            uv=mesh.uv_layers.new(name='UVMap 0');uv.data.foreach_set('uv',(g[:,:,:2].reshape(-1,2)[vertex_indices]/6).ravel())
            colors=mask[y0:y1+1:step,x0:x1+1:step].reshape(-1,4)/255
            # These are linear blend weights, rather than display colours.
            # FLOAT_COLOR avoids sRGB decoding the native byte masks in preview.
            attr=mesh.color_attributes.new(name='Solo_Mistura',type='FLOAT_COLOR',domain='CORNER');attr.data.foreach_set('color',colors[vertex_indices].ravel())
            obj.data=mesh;obj.matrix_world=Matrix.Identity(4)
        print('TERRAIN_QUALITY_BLENDER',tile['name'],flush=True)
    bpy.context.scene['solo_qualidade']='43 setores; textura nativa e normal; misturas contínuas de grama areia barro rocha; praia leste completa'
    destination=O/'ilha_porto_esperanca_qualidade.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(destination),compress=True)
    print('TERRAIN_QUALITY_BLENDER_SAVED',str(destination),flush=True)


if __name__=='__main__':
    if '--validate' in sys.argv:
        validate()
    else:
        grid,normals,tangents,mask,shore=fields()
        land=grid[:,:,2]>.3
        g=mask[...,1].astype(np.float32)/255;b=mask[...,2].astype(np.float32)/255
        mixture=np.stack([(1-g)*(1-b),(1-g)*b,g*(1-b),g*b],-1)
        summary={'land_vertices':int(land.sum()),'layer_mean':{name:float(mixture[:,:,i][land].mean()) for i,name in enumerate(LAYERNAMES)},'dominant_vertices':{name:int(((mixture.argmax(-1)==i)&land).sum()) for i,name in enumerate(LAYERNAMES)},'all_sectors':len(complete_tiles(grid))}
        (DATA/'misturas_solo.json').write_text(json.dumps(summary,indent=2),encoding='utf8')
        print('TERRAIN_QUALITY_FIELDS',summary,flush=True)
        if '--blender' in sys.argv:
            blender_scene(grid,normals,mask)
        else:
            native_export(grid,normals,tangents,mask)
