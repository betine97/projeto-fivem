"""Replace the Meshy vinyl artifacts with movable clear strips and permanent puddles."""
import copy
import io
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path[:0] = [
    r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps',
    r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\media_deps',
]
from PIL import Image
from szio.gta5 import AssetFormat, AssetTarget, AssetVersion, save_asset, try_load_asset
from szio.gta5.drawables import LodLevel
from szio.gta5.entities import Entity, EntityFlags, EntityLodLevel, EntityPriorityLevel
from szio.types import DataSource, Quaternion, Vector

root = Path(__file__).resolve().parents[2]
lab = root / 'laboratorio_fivem'
stream = root / 'server-data/resources/cidade_laboratorio/stream'
out = lab / 'moving_curtains_update'
out.mkdir(exist_ok=True)
target = (AssetTarget(AssetFormat.NATIVE, AssetVersion.GEN8),)

placement = json.loads((lab / 'placement.json').read_text())
origin = np.asarray(placement['origin'])
basis = np.asarray(placement['basis'])
heading = math.radians(placement['heading'])

def world_entity(name, position, draw_distance=100):
    rotation = Quaternion((math.cos(-heading/2), 0, 0, math.sin(-heading/2)))
    return Entity(name, Vector(origin + basis @ np.asarray(position)), rotation,
                  1, 1, EntityFlags.IS_STATIC, 0, -1, draw_distance, 0,
                  EntityLodLevel.ORPHANHD, EntityPriorityLevel.REQUIRED,
                  0, 255, 255, 0, [])

def mesh_geometry(template, positions, normals, uvs, shader_index=0):
    assert len(positions) == len(normals) == len(uvs) and len(positions) < 65535
    vertices = np.zeros(len(positions), dtype=template.vertex_buffer.dtype)
    vertices['Position'] = positions
    vertices['Normal'] = normals
    vertices['TexCoord0'] = uvs
    vertices['Colour0'] = (255, 255, 255, 255)
    vertices['Tangent'] = (1, 0, 0, 1)
    result = copy.deepcopy(template)
    result.vertex_buffer = vertices
    result.index_buffer = np.arange(len(positions), dtype=np.uint16)
    result.shader_index = shader_index
    return result

def append_triangle(positions, normals, uvs, vertices, tex):
    a, b, c = [np.asarray(v, dtype=np.float32) for v in vertices]
    n = np.cross(b-a, c-a)
    n /= max(np.linalg.norm(n), 1e-8)
    positions.extend(vertices)
    normals.extend((n, n, n))
    uvs.extend(tex)

def append_box(positions, normals, uvs, center, half):
    x, y, z = center
    a, b, c = half
    corners = np.asarray([(x-a,y-b,z-c),(x+a,y-b,z-c),
                          (x+a,y+b,z-c),(x-a,y+b,z-c),
                          (x-a,y-b,z+c),(x+a,y-b,z+c),
                          (x+a,y+b,z+c),(x-a,y+b,z+c)], dtype=np.float32)
    for face in ((0,3,2,1),(4,5,6,7),(0,1,5,4),
                 (1,2,6,5),(2,3,7,6),(3,0,4,7)):
        for ids in ((0,1,2),(0,2,3)):
            append_triangle(positions,normals,uvs,corners[[face[i] for i in ids]],
                            ((0,0),(1,0),(1,1)) if ids==(0,1,2) else ((0,0),(1,1),(0,1)))

def save_rgba_texture(asset, base_name, new_name, image):
    shader = asset.shader_group.shaders[0]
    old_diffuse = next(parameter.value for parameter in shader.parameters
                       if parameter.name.lower()=='diffusesampler')
    source = asset.shader_group.embedded_textures[old_diffuse]
    texture = copy.deepcopy(source)
    texture.name = new_name
    texture.width, texture.height = image.size
    dds = io.BytesIO()
    image.save(dds, format='DDS', pixel_format='DXT5')
    texture.data = DataSource.create(dds.getvalue())
    asset.shader_group.embedded_textures[new_name] = texture
    asset.shader_group.embedded_textures.pop(old_diffuse,None)
    for parameter in shader.parameters:
        name = parameter.name.lower()
        if name == 'diffusesampler': parameter.value = new_name
        if name in ('reflectivepower','bumpiness','specularintensitymult'):
            parameter.value = Vector((0,0,0,0))
    assert shader.render_bucket.value == 1

# Keep the rack's existing metal and add two narrow tracks over its long sides.
# This is a derived, clean version of the supplied enclosure's upper frame.
rails = try_load_asset(stream / 'lab_racks.ydr')
rails.name = 'lab_containment.#dr'
rail_template = rails.models[LodLevel.HIGH][0].geometries[0]
rp, rn, ru = [], [], []
for x in (-1.072, 1.072):
    append_box(rp,rn,ru,(x,0,2.954),(.048,3.72,.038))
    append_box(rp,rn,ru,(x,0,2.885),(.021,3.72,.015))
for y in (-3.70,):
    append_box(rp,rn,ru,(0,y,2.954),(1.10,.048,.038))
    append_box(rp,rn,ru,(0,y,2.885),(1.10,.021,.015))
rails.models[LodLevel.HIGH][0].geometries = [
    mesh_geometry(rail_template,rp,rn,ru,0)]
for lod in list(rails.models):
    if lod != LodLevel.HIGH: rails.models[lod] = []
save_asset(rails,target,out,'lab_containment')

# A strip is an independent game object. Its origin is the slider at the top:
# rotating it produces a pendulum-like motion with no movement at the rail.
glass_sample = lab / 'work/translucent_shader_samples/v_ilev_prop_fib_glass.ydr'
strip = try_load_asset(glass_sample)
strip.name = 'lab_vinyl_strip.#dr'
vinyl = Image.open(lab/'containment_source/vinyl_strip_clear_rgba.png').convert('RGBA')
save_rgba_texture(strip,'unused','lab_vinyl_clear',vinyl)
sp, sn, su = [], [], []
width, length = .375, 2.57
for row in range(10):
    for col in range(2):
        u0,u1 = col/2,(col+1)/2
        v0,v1 = row/10,(row+1)/10
        def vertex(u,v):
            x = (u-.5)*width
            z = -.045-v*length
            y = .006*math.sin(2*math.pi*v+u*math.pi)
            return (x,y,z)
        p00,p10,p11,p01 = vertex(u0,v0),vertex(u1,v0),vertex(u1,v1),vertex(u0,v1)
        for points,uv in (((p00,p10,p11),((u0,v0),(u1,v0),(u1,v1))),
                          ((p00,p11,p01),((u0,v0),(u1,v1),(u0,v1)))):
            append_triangle(sp,sn,su,points,uv)
            append_triangle(sp,sn,su,points[::-1],uv[::-1])
strip.models[LodLevel.HIGH][0].geometries = [
    mesh_geometry(strip.models[LodLevel.HIGH][0].geometries[0],sp,sn,su,0)]
for lod in list(strip.models):
    if lod != LodLevel.HIGH: strip.models[lod] = []
save_asset(strip,target,out,'lab_vinyl_strip')

# The native puddle asset's decal shader is multiplied by game wetness, so it
# disappears in dry weather. Static alpha water patches are weather-independent.
puddle = try_load_asset(glass_sample)
puddle.name = 'lab_pocas.#dr'
size = 256
yy, xx = np.mgrid[:size,:size].astype(np.float32)
rad = np.sqrt(((xx-127.5)/126)**2+((yy-127.5)/126)**2)
noise = 3*np.sin(xx*.17+yy*.034)+2*np.sin(yy*.14)
fade = np.clip((1-rad)/.32,0,1)
glint = 26*np.exp(-((yy-93-5*np.sin(xx*.045))/4)**2)
rgba = np.stack((np.clip(34+noise+glint,0,255),
                 np.clip(43+noise+glint,0,255),
                 np.clip(48+noise+glint,0,255),
                 np.clip((89+glint)*fade,0,125)),axis=-1).astype(np.uint8)
puddle_image = Image.fromarray(rgba,'RGBA')
puddle_image.save(out/'permanent_puddle_preview.png')
save_rgba_texture(puddle,'unused','lab_puddle_always',puddle_image)
pp,pn,pu = [],[],[]
patches = [(-.75,-3.82,.62,.36,.15),(.87,-1.81,.42,.28,1.1),
           (-.72,.20,.58,.37,2.2),(.75,2.33,.51,.32,.8),
           (-.39,4.00,.38,.25,1.7)]
for cx,cy,rx,ry,phase in patches:
    center = (cx,cy,.068)
    for i in range(48):
        points=[];tex=[]
        for t in (i,i+1):
            a=math.tau*t/48
            irregular=1+.10*math.sin(5*a+phase)+.06*math.sin(9*a-2*phase)
            x,y=irregular*math.cos(a),irregular*math.sin(a)
            points.append((cx+rx*x,cy+ry*y,.068))
            tex.append((.5+.49*x,.5+.49*y))
        append_triangle(pp,pn,pu,(center,points[0],points[1]),
                        ((.5,.5),tex[0],tex[1]))
puddle.models[LodLevel.HIGH][0].geometries = [
    mesh_geometry(puddle.models[LodLevel.HIGH][0].geometries[0],pp,pn,pu,0)]
for lod in list(puddle.models):
    if lod != LodLevel.HIGH: puddle.models[lod] = []
save_asset(puddle,target,out,'lab_pocas')

ymap = try_load_asset(stream/'cidade_laboratorio.ymap')
ymap.entities = [e for e in ymap.entities
                 if e.archetype_name not in ('lab_containment','lab_pocas')]
ymap.entities.extend((world_entity('lab_containment',(-2.48,-.8,0)),
                      world_entity('lab_containment',(2.48,-.8,0)),
                      world_entity('lab_pocas',(0,0,0))))
save_asset(ymap,target,out,'cidade_laboratorio')

typ = try_load_asset(stream/'cidade_laboratorio.ytyp')
typ.archetypes = [a for a in typ.archetypes if a.name not in
                  ('lab_containment','lab_vinyl_strip','lab_pocas')]
template_arch = next(a for a in typ.archetypes if a.name=='lab_racks')
for name, asset in (('lab_containment',rails),('lab_vinyl_strip',strip),('lab_pocas',puddle)):
    arch=copy.deepcopy(template_arch)
    arch.name=arch.asset_name=name
    vertices=np.concatenate([g.vertex_buffer['Position']
                             for g in asset.models[LodLevel.HIGH][0].geometries])
    low,high=vertices.min(0),vertices.max(0)
    arch.bb_min=Vector(low);arch.bb_max=Vector(high)
    arch.bs_center=Vector((low+high)/2)
    arch.bs_radius=float(np.linalg.norm(high-low)/2)
    typ.archetypes.append(arch)
save_asset(typ,target,out,'cidade_laboratorio')

for name in ('lab_containment.ydr','lab_vinyl_strip.ydr','lab_pocas.ydr',
             'cidade_laboratorio.ymap','cidade_laboratorio.ytyp'):
    assert try_load_asset(out/name) is not None,name
assert [e.archetype_name for e in ymap.entities].count('lab_pocas')==1
print('MOVING_CURTAINS_OK',len(sp)//3,'strip triangles',len(ymap.entities),
      'entities',flush=True)
