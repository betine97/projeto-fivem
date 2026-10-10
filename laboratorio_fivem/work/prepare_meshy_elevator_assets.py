"""Prepare the two user-supplied Meshy elevator GLBs for Blender and GTA.

Run with Blender 5.2 in background against warehouse_stage18_preparacao.blend.
The exported NPZ vertices use the laboratory elevator entity's local space:
its origin is at world Y=5.33, with the front at local Y=-0.68.
"""

from __future__ import annotations

import json
import shutil
import struct
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "laboratorio_fivem" / "elevator_source"
BLEND = ROOT / "preparacao_fivem_stage18" / "warehouse_stage18_preparacao.blend"
INPUT_GLBS = {
    "3901": Path(r"C:\Users\erons\Downloads\Meshy_AI_industrial_elevator_c_1004203901_image-to-3d-texture.glb"),
    "4234": Path(r"C:\Users\erons\Downloads\Meshy_AI_industrial_elevator_c_1004204234_image-to-3d-texture.glb"),
}
ASSETS = ROOT / "laboratorio_fivem" / "source_assets"
GLBS = {key: ASSETS / f"Meshy_industrial_elevator_{key}_original.glb" for key in INPUT_GLBS}


def extract_original_albedo(key: str) -> Path:
    """Copy every embedded PBR JPEG; return the base-color path."""
    data = GLBS[key].read_bytes()
    assert data[:4] == b"glTF"
    json_length = struct.unpack_from("<I", data, 12)[0]
    gltf = json.loads(data[20 : 20 + json_length])
    material = gltf["materials"][0]
    binary_start = 20 + json_length + 8
    texture_indices = {
        "albedo": material["pbrMetallicRoughness"]["baseColorTexture"]["index"],
        "normal": material["normalTexture"]["index"],
        "metallic_roughness": material["pbrMetallicRoughness"]["metallicRoughnessTexture"]["index"],
    }
    for kind, tex_index in texture_indices.items():
        image_index = gltf["textures"][tex_index]["source"]
        image = gltf["images"][image_index]
        assert image["mimeType"] == "image/jpeg"
        view = gltf["bufferViews"][image["bufferView"]]
        start = binary_start + view["byteOffset"]
        out = SOURCE / f"elevator_{key}_{kind}.jpg"
        out.write_bytes(data[start : start + view["byteLength"]])
    return SOURCE / f"elevator_{key}_albedo.jpg"


def import_mesh(key: str) -> bpy.types.Object:
    existing = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(GLBS[key]))
    meshes = [o for o in bpy.data.objects if o not in existing and o.type == "MESH"]
    assert len(meshes) == 1, (key, len(meshes))
    obj = meshes[0]
    assert obj.data.uv_layers.active is not None
    print("IMPORTED_MATRIX", key, [list(row) for row in obj.matrix_world], flush=True)
    # glTF importer currently bakes the Y-up conversion into vertices, but do
    # not rely on that if the source node gains a transform in a later export.
    obj.data.transform(obj.matrix_world)
    obj.matrix_world.identity()
    for material in obj.data.materials:
        if material and material.use_nodes:
            for node in material.node_tree.nodes:
                if node.type == "TEX_IMAGE" and node.image and not node.image.packed_file:
                    node.image.pack()
    return obj


def decimate(obj: bpy.types.Object, target_triangles: int) -> None:
    count = len(obj.data.polygons)
    modifier = obj.modifiers.new("Meshy game mesh reduction", "DECIMATE")
    modifier.ratio = min(1.0, target_triangles / count)
    modifier.use_collapse_triangulate = True
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    tri = obj.modifiers.new("Meshy triangles", "TRIANGULATE")
    bpy.ops.object.modifier_apply(modifier=tri.name)
    print("DECIMATED", obj.name, count, "->", len(obj.data.polygons), flush=True)


def triangle_data(obj: bpy.types.Object) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    mesh = obj.data
    mesh.calc_loop_triangles()
    vertices = np.empty((len(mesh.vertices), 3), dtype=np.float32)
    mesh.vertices.foreach_get("co", vertices.ravel())
    loop_vertices = np.empty(len(mesh.loops), dtype=np.int32)
    mesh.loops.foreach_get("vertex_index", loop_vertices)
    triangle_loops = np.empty((len(mesh.loop_triangles), 3), dtype=np.int32)
    mesh.loop_triangles.foreach_get("loops", triangle_loops.ravel())
    uv = np.empty((len(mesh.loops), 2), dtype=np.float32)
    mesh.uv_layers.active.data.foreach_get("uv", uv.ravel())
    corner_normals = np.empty((len(mesh.loops), 3), dtype=np.float32)
    mesh.corner_normals.foreach_get("vector", corner_normals.ravel())
    return vertices[loop_vertices[triangle_loops]], corner_normals[triangle_loops], uv[triangle_loops]


def fit(
    positions: np.ndarray,
    normals: np.ndarray,
    scales: np.ndarray,
    translation: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    fitted = positions * scales + translation
    fitted_normals = normals / scales
    fitted_normals /= np.maximum(np.linalg.norm(fitted_normals, axis=-1, keepdims=True), 1e-8)
    return fitted.astype(np.float32), fitted_normals.astype(np.float32)


def write_npz(name: str, p: np.ndarray, n: np.ndarray, uv: np.ndarray) -> Path:
    path = SOURCE / name
    assert p.shape[0] == n.shape[0] == uv.shape[0]
    assert p.shape[1:] == (3, 3) and n.shape[1:] == (3, 3) and uv.shape[1:] == (3, 2)
    np.savez_compressed(path, position=p.reshape(-1, 3), normal=n.reshape(-1, 3), uv=uv.reshape(-1, 2))
    print("EXPORTED", path.name, "triangles", len(p), "bbox", p.min(axis=(0, 1)).tolist(), p.max(axis=(0, 1)).tolist(), flush=True)
    return path


def mesh_from_triangles(name: str, p: np.ndarray, n: np.ndarray, uv: np.ndarray, material: bpy.types.Material) -> bpy.types.Mesh:
    # Separate corners retain the original image atlas UV and split normals.
    positions = np.ascontiguousarray(p.reshape(-1, 3), dtype=np.float32)
    normals = np.ascontiguousarray(n.reshape(-1, 3), dtype=np.float32)
    coords = np.ascontiguousarray(uv.reshape(-1, 2), dtype=np.float32)
    mesh = bpy.data.meshes.new(name + "_MESH")
    mesh.vertices.add(len(positions))
    mesh.loops.add(len(positions))
    mesh.polygons.add(len(p))
    mesh.vertices.foreach_set("co", positions.ravel())
    mesh.loops.foreach_set("vertex_index", np.arange(len(positions), dtype=np.int32))
    mesh.polygons.foreach_set("loop_start", np.arange(len(p), dtype=np.int32) * 3)
    mesh.polygons.foreach_set("loop_total", np.full(len(p), 3, dtype=np.int32))
    mesh.update(calc_edges=True)
    layer = mesh.uv_layers.new(name="UVMap")
    layer.data.foreach_set("uv", coords.ravel())
    mesh.polygons.foreach_set("use_smooth", np.ones(len(p), dtype=np.bool_))
    mesh.normals_split_custom_set(normals.tolist())
    mesh.materials.append(material)
    return mesh


def add_instance(collection: bpy.types.Collection, name: str, mesh: bpy.types.Mesh, location: tuple[float, float, float]) -> bpy.types.Object:
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    obj.location = location
    return obj


def preview(collection: bpy.types.Collection, objs: list[bpy.types.Object], doors: list[bpy.types.Object]) -> None:
    hidden = {obj: obj.hide_render for obj in bpy.data.objects}
    for obj in bpy.data.objects:
        obj.hide_render = obj not in objs
    floor_mat = bpy.data.materials.new("MESHI_PREVIEW_FLOOR")
    floor_mat.diffuse_color = (0.2, 0.2, 0.2, 1)
    bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 5.4, -0.025))
    floor = bpy.context.object
    floor.data.materials.append(floor_mat)
    lights = []
    for loc, power, size in (((-3, 1, 5), 700, 5), ((3, 7, 4), 450, 4)):
        data = bpy.data.lights.new("MESHI_PREVIEW_LIGHT", "AREA")
        data.energy = power
        data.shape = "DISK"
        data.size = size
        lamp = bpy.data.objects.new("MESHI_PREVIEW_LIGHT", data)
        bpy.context.scene.collection.objects.link(lamp)
        lamp.location = loc
        lamp.rotation_euler = (Vector((0, 5.5, 1.2)) - lamp.location).to_track_quat("-Z", "Y").to_euler()
        lights.append(lamp)
    cam_data = bpy.data.cameras.new("MESHI_PREVIEW_CAMERA")
    cam = bpy.data.objects.new("MESHI_PREVIEW_CAMERA", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = (3.25, -0.1, 2.85)
    cam.rotation_euler = (Vector((0, 5.25, 1.25)) - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = 4.35
    scene = bpy.context.scene
    old_camera = scene.camera
    old_engine = scene.render.engine
    old_resolution = (scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage)
    scene.camera = cam
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 16
    scene.cycles.use_denoising = True
    scene.render.resolution_x = scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    for state, offset in (("closed", 0.0), ("open", 0.85)):
        doors[0].location.x = -0.52 - offset
        doors[1].location.x = 0.52 + offset
        scene.render.filepath = str(SOURCE / f"elevator_meshy_{state}_preview.png")
        bpy.ops.render.render(write_still=True)
        print("PREVIEW", scene.render.filepath, flush=True)
    doors[0].location.x, doors[1].location.x = -0.52, 0.52
    scene.camera = old_camera
    scene.render.engine = old_engine
    scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = old_resolution
    for obj in [cam, floor, *lights]:
        bpy.data.objects.remove(obj, do_unlink=True)
    for obj, previous in hidden.items():
        obj.hide_render = previous


def main() -> None:
    SOURCE.mkdir(parents=True, exist_ok=True)
    ASSETS.mkdir(parents=True, exist_ok=True)
    for key, retained in GLBS.items():
        if not retained.exists():
            shutil.copy2(INPUT_GLBS[key], retained)
        if INPUT_GLBS[key].exists():
            assert retained.stat().st_size == INPUT_GLBS[key].stat().st_size
    collection = bpy.data.collections["LAB_ELEVATOR"]
    backup = BLEND.with_name("warehouse_stage18_preparacao_before_meshy.blend")
    if not backup.exists():
        shutil.copy2(BLEND, backup)
    for obj in list(collection.objects):
        if obj.name.startswith("LAB_ELEVATOR_MESHY_"):
            bpy.data.objects.remove(obj, do_unlink=True)
    albedos = {key: extract_original_albedo(key) for key in GLBS}
    print("ALBEDOS", *(str(p) for p in albedos.values()), flush=True)

    cabin = import_mesh("3901")
    decimate(cabin, 60_000)
    cp0, cn0, cuv = triangle_data(cabin)
    cmin = cp0.min(axis=(0, 1)); cmax = cp0.max(axis=(0, 1))
    cscale = np.array((1.904 / (cmax[0] - cmin[0]), 2.55 / (cmax[1] - cmin[1]), 2.48 / (cmax[2] - cmin[2])), dtype=np.float32)
    cshift = np.array((-(cmax[0] + cmin[0]) * cscale[0] / 2, -0.68 - cmin[1] * cscale[1], -cmin[2] * cscale[2]), dtype=np.float32)
    cp, cn = fit(cp0, cn0, cscale, cshift)
    write_npz("elevator_3901_cabin.npz", cp, cn, cuv)
    for coll in list(cabin.users_collection):
        coll.objects.unlink(cabin)
    collection.objects.link(cabin)
    cabin.name = "LAB_ELEVATOR_MESHY_CABIN_0"
    cabin.location = (float(cshift[0]), 5.33 + float(cshift[1]), float(cshift[2]))
    cabin.scale = tuple(float(x) for x in cscale)
    cabin_low = cabin.copy()
    cabin_low.data = cabin.data
    collection.objects.link(cabin_low)
    cabin_low.name = "LAB_ELEVATOR_MESHY_CABIN_MINUS_1"
    cabin_low.location.z -= 8.0

    facade = import_mesh("4234")
    material = facade.data.materials[0]
    decimate(facade, 50_000)
    fp0, fn0, fuv = triangle_data(facade)
    fmin = fp0.min(axis=(0, 1)); fmax = fp0.max(axis=(0, 1))
    fscale = np.array((2.04 / (fmax[0] - fmin[0]), 1.0, 2.48 / (fmax[2] - fmin[2])), dtype=np.float32)
    fshift = np.array((-(fmax[0] + fmin[0]) * fscale[0] / 2, -0.68 - fmin[1] * fscale[1], -fmin[2] * fscale[2]), dtype=np.float32)
    fp, fn = fit(fp0, fn0, fscale, fshift)

    # The closed front is a single Meshy mesh. Its two leaves are the recessed
    # panels between the jambs, below the lintel. The center seam is X=-0.075
    # in source coordinates; frame and buttons are outside this bounded region.
    center = fp0.mean(axis=1)
    per_triangle_min = fp0.min(axis=1)
    per_triangle_max = fp0.max(axis=1)
    door = (
        (center[:, 0] > -0.555) & (center[:, 0] < 0.435)
        & (center[:, 1] > -0.05) & (center[:, 1] < 0.08)
        & (center[:, 2] > 0.034) & (center[:, 2] < 1.74)
        & (per_triangle_min[:, 1] > -0.05) & (per_triangle_max[:, 1] < 0.08)
        & (per_triangle_min[:, 2] > 0.034) & (per_triangle_max[:, 2] < 1.74)
    )
    left = door & (center[:, 0] < -0.075)
    right = door & ~left
    static = ~door
    assert min(static.sum(), left.sum(), right.sum()) > 1000
    # The two door NPZs have their own pivot space, matching existing entity
    # positions (x=+/-0.52, local y=-0.68, local z=1.14).
    left_pivot = np.array((-0.52, -0.68, 1.14), dtype=np.float32)
    right_pivot = np.array((0.52, -0.68, 1.14), dtype=np.float32)
    left_p = fp[left] - left_pivot
    right_p = fp[right] - right_pivot
    write_npz("elevator_4234_facade.npz", fp[static], fn[static], fuv[static])
    write_npz("elevator_4234_door_left.npz", left_p, fn[left], fuv[left])
    write_npz("elevator_4234_door_right.npz", right_p, fn[right], fuv[right])
    report = {
        "front_axis_blender": "-Y",
        "cabin_scales_xyz": cscale.tolist(),
        "cabin_translation_xyz": cshift.tolist(),
        "facade_scales_xyz": fscale.tolist(),
        "facade_translation_xyz": fshift.tolist(),
        "door_source_cut": {"x_min": -0.555, "x_seam": -0.075, "x_max": 0.435, "y_min": -0.05, "y_max": 0.08, "z_min": 0.034, "z_max": 1.74},
        "triangle_counts": {"cabin": int(len(cp)), "facade": int(static.sum()), "door_left": int(left.sum()), "door_right": int(right.sum())},
        "door_pivots_local": {"left": left_pivot.tolist(), "right": right_pivot.tolist()},
        "doors_closed_bbox_entity_local": {
            "left": [fp[left].min(axis=(0, 1)).tolist(), fp[left].max(axis=(0, 1)).tolist()],
            "right": [fp[right].min(axis=(0, 1)).tolist(), fp[right].max(axis=(0, 1)).tolist()],
        },
    }
    (SOURCE / "elevator_meshy_fit_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    bpy.data.objects.remove(facade, do_unlink=True)

    static_mesh = mesh_from_triangles("LAB_ELEVATOR_MESHY_FACADE", fp[static], fn[static], fuv[static], material)
    left_mesh = mesh_from_triangles("LAB_ELEVATOR_MESHY_DOOR_LEFT", left_p, fn[left], fuv[left], material)
    right_mesh = mesh_from_triangles("LAB_ELEVATOR_MESHY_DOOR_RIGHT", right_p, fn[right], fuv[right], material)
    objects_zero = [cabin]
    doors_zero = []
    for suffix, dz in (("0", 0.0), ("MINUS_1", -8.0)):
        static_obj = add_instance(collection, f"LAB_ELEVATOR_MESHY_FACADE_{suffix}", static_mesh, (0, 5.33, dz))
        left_obj = add_instance(collection, f"LAB_ELEVATOR_MESHY_DOOR_{suffix}_L", left_mesh, (-0.52, 4.65, 1.14 + dz))
        right_obj = add_instance(collection, f"LAB_ELEVATOR_MESHY_DOOR_{suffix}_R", right_mesh, (0.52, 4.65, 1.14 + dz))
        left_obj["door_direction"] = -1
        right_obj["door_direction"] = 1
        left_obj["slide_open_distance"] = 0.85
        right_obj["slide_open_distance"] = 0.85
        if dz == 0:
            objects_zero.extend((static_obj, left_obj, right_obj))
            doors_zero.extend((left_obj, right_obj))
    # Retain the earlier lift as hidden backup while the Meshy assembly is active.
    # Its two floor-number plates are still useful: enlarge and position them
    # directly over the "1" baked into both Meshy source models.
    floor_number_objects = []
    for suffix, dz, label in (("0", 0.0, "0"), ("MINUS_1", -8.0, "-1")):
        display = bpy.data.objects[f"LAB_ELEVATOR_DISPLAY_{suffix}"]
        number = bpy.data.objects[f"LAB_ELEVATOR_NUMBER_{suffix}"]
        display.location = (0, 4.61, 2.35 + dz)
        display.dimensions = (0.86, 0.035, 0.24)
        number.location = (0, 4.58, 2.35 + dz)
        number.data.body = label
        number.data.size = 0.30
        floor_number_objects.extend((display, number))
    for obj in collection.objects:
        if obj.name.startswith("LAB_ELEVATOR_") and not obj.name.startswith("LAB_ELEVATOR_MESHY_") and obj not in floor_number_objects:
            obj.hide_render = True
            obj.hide_set(True)
    for obj in floor_number_objects:
        obj.hide_render = False
        obj.hide_set(False)
    for suffix, dz in (("0",0), ("MINUS_1",-8)):
        light_data=bpy.data.lights.new("LAB_ELEVATOR_CABIN_LIGHT_"+suffix,"POINT")
        light_data.energy=160
        light_data.shadow_soft_size=.35
        lamp=bpy.data.objects.new("LAB_ELEVATOR_MESHY_LIGHT_"+suffix,light_data)
        collection.objects.link(lamp)
        lamp.location=(0,6.30,2.12+dz)
        if dz==0:objects_zero.append(lamp)
    preview(collection, objects_zero + floor_number_objects[:2], doors_zero)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    print("MESHI_ELEVATOR_READY", flush=True)


if __name__ == "__main__":
    main()
