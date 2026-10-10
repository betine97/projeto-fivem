import bpy
import numpy as np
import hashlib
import json
import re
import shutil
import time
from pathlib import Path
from mathutils import Vector, Matrix

BASE = Path(__file__).resolve().parent
OUT = BASE / 'catalogo_componentes_stage7'
OUT.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(BASE / 'warehouse_stage7_validado.blend'))
original = bpy.context.scene
root = bpy.data.collections['ENV_WAREHOUSE_STAGE7']
objects = sorted(root.all_objects, key=lambda o: (o.users_collection[0].name, o.name))
depsgraph = bpy.context.evaluated_depsgraph_get()
render_scene = bpy.data.scenes.new('CATALOG_STUDIO_TEMP')
render_scene.render.engine = 'BLENDER_WORKBENCH'
render_scene.render.resolution_x = 768
render_scene.render.resolution_y = 768
render_scene.render.resolution_percentage = 100
render_scene.render.image_settings.file_format = 'PNG'
render_scene.render.image_settings.color_mode = 'RGBA'
render_scene.render.film_transparent = False
render_scene.render.use_compositing = False
shade = render_scene.display.shading
shade.light = 'STUDIO'
shade.color_type = 'MATERIAL'
shade.background_type = 'VIEWPORT'
shade.background_color = (0.18, 0.18, 0.18)
shade.show_shadows = True
shade.show_cavity = True
shade.cavity_type = 'BOTH'
shade.show_specular_highlight = True
shade.show_object_outline = True
render_scene.display.render_aa = '16'
render_scene.view_settings.view_transform = 'Standard'
camera_data = bpy.data.cameras.new('CATALOG_CAMERA_TEMP')
camera = bpy.data.objects.new('CATALOG_CAMERA_TEMP', camera_data)
render_scene.collection.objects.link(camera)
render_scene.camera = camera
camera_data.type = 'ORTHO'
camera_data.clip_start = 0.001
camera_data.clip_end = 1000
records, nonvisual, cache = [], [], {}
start = time.time()


def safe_name(value):
    return re.sub(r'[^A-Za-z0-9_.-]', '_', value)


for index, obj in enumerate(objects):
    collections = sorted(c.name for c in obj.users_collection)
    record = {'object': obj.name, 'type': obj.type, 'collections': collections,
              'materials': [m.name if m else None for m in getattr(obj.data, 'materials', [])],
              'dimensions_m': [round(float(v), 6) for v in obj.dimensions],
              'location_world_m': [round(float(v), 6) for v in obj.matrix_world.translation]}
    if obj.type not in ('MESH', 'CURVE', 'SURFACE', 'FONT', 'META'):
        nonvisual.append(record)
        continue
    evaluated = obj.evaluated_get(depsgraph)
    mesh = bpy.data.meshes.new_from_object(evaluated, depsgraph=depsgraph)
    if not mesh.vertices:
        nonvisual.append(record)
        bpy.data.meshes.remove(mesh)
        continue
    coords = np.empty(len(mesh.vertices) * 3, dtype=np.float64)
    mesh.vertices.foreach_get('co', coords)
    coords = coords.reshape(-1, 3)
    # Principal axes face the largest visible surfaces toward the camera.
    centered = coords - (coords.min(axis=0) + coords.max(axis=0)) / 2
    _, axes = np.linalg.eigh(centered.T @ centered)
    basis = axes[:, ::-1].copy()
    for axis in range(3):
        pivot = np.argmax(np.abs(basis[:, axis]))
        if basis[pivot, axis] < 0:
            basis[:, axis] *= -1
    if np.linalg.det(basis) < 0:
        basis[:, 2] *= -1
    local = centered @ basis
    longest = max(float(np.ptp(local, axis=0).max()), 1e-6)
    normalized = local / longest * 2.0
    mesh.vertices.foreach_set('co', normalized.ravel())
    mesh.update()
    # Share only exact matching evaluated geometry and material assignments.
    digest = hashlib.sha256()
    digest.update(np.round(normalized, 6).tobytes())
    loops = np.empty(len(mesh.loops), dtype=np.int32)
    mesh.loops.foreach_get('vertex_index', loops)
    digest.update(loops.tobytes())
    mat_indices = np.empty(len(mesh.polygons), dtype=np.int32)
    mesh.polygons.foreach_get('material_index', mat_indices)
    digest.update(mat_indices.tobytes())
    digest.update(json.dumps(record['materials']).encode())
    key = digest.hexdigest()
    directory = OUT / 'imagens' / safe_name(collections[0])
    directory.mkdir(parents=True, exist_ok=True)
    filename = directory / (safe_name(obj.name) + '.png')
    record['image'] = filename.relative_to(OUT).as_posix()
    record['reference_render'] = 'isolated neutral studio; original material preview color'
    if key in cache:
        shutil.copyfile(cache[key]['file'], filename)
        record['same_geometry_as'] = cache[key]['object']
    else:
        item = bpy.data.objects.new('CATALOG_ITEM_TEMP', mesh)
        render_scene.collection.objects.link(item)
        direction = Vector((0.18, -0.28, 1.0)).normalized()
        camera.location = direction * 8
        camera.rotation_euler = (-direction).to_track_quat('-Z', 'Y').to_euler()
        rotation = camera.rotation_euler.to_matrix().transposed()
        projected = np.asarray([tuple(rotation @ Vector(p)) for p in normalized])
        span = np.ptp(projected[:, :2], axis=0)
        camera_data.ortho_scale = float(max(span)) * 1.20
        center2 = (projected[:, :2].min(axis=0) + projected[:, :2].max(axis=0)) * 0.5
        camera.location += camera.rotation_euler.to_matrix() @ Vector((float(center2[0]), float(center2[1]), 0))
        render_scene.render.filepath = str(filename)
        bpy.ops.render.render(write_still=True, scene=render_scene.name)
        cache[key] = {'file': filename, 'object': obj.name}
        bpy.data.objects.remove(item, do_unlink=True)
    bpy.data.meshes.remove(mesh)
    records.append(record)
    (OUT / 'progresso.json').write_text(json.dumps({'processed': index + 1, 'total': len(objects),
        'images': len(records), 'distinct_renders': len(cache), 'elapsed_s': round(time.time() - start)}), encoding='utf-8')
    if len(records) % 100 == 0:
        print('CATALOG_PROGRESS', len(records), '/', len(objects), flush=True)

manifest = {'source_blend': 'warehouse_stage7_validado.blend',
            'image_resolution': [768, 768], 'objects': records, 'nonvisual_objects': nonvisual,
            'count_images': len(records), 'count_distinct_renders': len(cache),
            'elapsed_s': round(time.time() - start)}
(OUT / 'manifesto.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
print('CATALOG_COMPLETE', len(records), len(cache), flush=True)
