"""Bake local geometric ambient occlusion into native mesh caches, without changing albedo.

Run with Blender --background --python this_file -- [--model pe_estrutura_06].
The same high-detail occluder is used for each LOD.  This is ambient contact
shading, independent of sunlight, and does not paint shadows into source PNGs.
"""
from pathlib import Path
import json, math, sys, time
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

O = Path(__file__).resolve().parents[1]
C = O / 'cache'
REPORT = O / 'dados/qualidade_oclusao.json'
SAMPLES = 12
RADIUS = 1.25
BIAS = .018


def basis(normal):
    n = Vector(normal)
    t = n.cross(Vector((0, 0, 1)) if abs(n.z) < .9 else Vector((0, 1, 0)))
    t.normalize()
    return n, t, n.cross(t)


def process(row):
    name = row['name']
    start = time.monotonic()
    hi = np.load(C / (name + '.npz'))
    positions = hi['position']
    # Exclude glass from the occluder. Transparent panes must let ambient light through.
    transparent = {i for i, m in enumerate(row['materials'])
                   if any(s in m.get('name', '').lower() for s in ('vidro', 'glass'))}
    tri = np.arange(len(positions)).reshape(-1, 3)
    mask = ~np.isin(hi['material'][tri[:, 0]], list(transparent))
    vertices, inverse = np.unique(positions, axis=0, return_inverse=True)
    triangles = inverse[tri[mask]]
    bvh = BVHTree.FromPolygons(vertices.tolist(), triangles.tolist(), all_triangles=True)
    hemisphere = []
    for sample in range(SAMPLES):
        # Cosine-weighted hemisphere with a deterministic golden-angle sequence.
        u = (sample + .5) / SAMPLES
        phi = sample * 2.399963229728653
        hemisphere.append((math.sqrt(u) * math.cos(phi), math.sqrt(u) * math.sin(phi), math.sqrt(1-u)))
    output = []
    memo = {}
    for path in [C / (name + '.npz')] + [C / f'{name}_LOD{i}.npz' for i in range(1, 4)]:
        if not path.exists():
            continue
        source = np.load(path)
        arrays = {k: source[k].copy() for k in source.files}
        points = arrays['position']
        normals = arrays['normal']
        # Rounding merges duplicated corners; normals stay distinct at sharp edges.
        unique, remap = np.unique(np.round(np.c_[points, normals], 4), axis=0, return_inverse=True)
        values = np.ones(len(unique), np.float32)
        for index, q in enumerate(unique):
            key = tuple(q)
            if key in memo:
                values[index] = memo[key]
                continue
            n, t, bitangent = basis(q[3:])
            origin = Vector(q[:3]) + n * BIAS
            blocked = 0.
            for x, y, z in hemisphere:
                direction = t*x + bitangent*y + n*z
                _, _, _, distance = bvh.ray_cast(origin, direction, RADIUS)
                if distance is not None:
                    blocked += 1 - (distance / RADIUS) ** .65
            # No hard black; distant cavities retain some sky fill. Direct light stays dynamic.
            value = float(np.clip(1 - .68 * blocked / SAMPLES, .32, 1))
            memo[key] = value
            values[index] = value
        arrays['ao'] = values[remap]
        arrays['ao'][np.isin(arrays['material'], list(transparent))] = 1
        np.savez_compressed(path, **arrays)
        output.append(dict(cache=path.name,vertices=len(points),unique_corners=len(unique),
                           min=float(arrays['ao'].min()),mean=float(arrays['ao'].mean()),
                           occluded=int(np.count_nonzero(arrays['ao'] < .97))))
        print('AO_READY', path.name, output[-1], flush=True)
    return dict(name=name,seconds=round(time.monotonic()-start,2),samples=SAMPLES,
                radius_m=RADIUS,lods=output)


if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    selected = args[args.index('--model')+1] if '--model' in args else None
    rows_data = (json.loads((O/'dados/arvores.json').read_text()) if '--trees' in args
                 else json.loads((O/'dados/casas.json').read_text()))
    rows = [process(row) for row in rows_data if selected is None or row['name'] == selected]
    old = json.loads(REPORT.read_text()) if REPORT.exists() else {'models': []}
    merged = {r['name']: r for r in old['models']}
    merged.update({r['name']: r for r in rows})
    REPORT.write_text(json.dumps(dict(models=list(merged.values()),source='geometric_BVH',
                                     albedo_unchanged=True),indent=2))
    print('AO_COMPLETE', len(rows), flush=True)
