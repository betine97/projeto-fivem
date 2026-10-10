import bpy, sys, json, addon_utils
from pathlib import Path
import numpy as np
from mathutils.kdtree import KDTree
sys.path[:0] = [r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps', r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\sollumz']
addon_utils.enable('Sollumz', default_set=True)
bpy.ops.wm.open_mainfile(filepath=str(Path('personagens/traje_guarda/GUARDA_ESQUELETO_GTA.blend').resolve()))
source = bpy.data.objects['GUARDA_MALHA_ORIGINAL']
tree = KDTree(len(source.data.vertices))
for v in source.data.vertices: tree.insert(source.matrix_world @ v.co, v.index)
tree.balance()
uvs_by_vertex = {}
for loop in source.data.loops:
 uvs_by_vertex.setdefault(loop.vertex_index, []).append(tuple(source.data.uv_layers[0].data[loop.index].uv))
native = np.load(Path(__file__).parent/'native_guard_uv.npz')
positions = native['positions']; uvs = native['uvs']
uv_err = []; position_err = []
for i in np.random.default_rng(1).choice(len(positions), size=2000, replace=False):
 matches = tree.find_n(positions[i], 16)
 dist = matches[0][2]
 position_err.append(dist)
 candidate_ids = [index for co, index, candidate_dist in matches if candidate_dist <= max(dist+1e-6, 1e-6)]
 uv = uvs[i].copy(); uv[1] = 1-uv[1]
 uv_err.append(min(np.linalg.norm(uv-np.array(candidate)) for index in candidate_ids for candidate in uvs_by_vertex[index]))
report = {'samples': 2000, 'max_position_error_metres': max(position_err), 'max_uv_error_after_native_v_flip': float(max(uv_err)), 'mean_uv_error_after_native_v_flip': float(np.mean(uv_err)), 'color_attribute_names_original': [a.name for a in source.data.color_attributes]}
(Path(__file__).parent/'audit_uv.json').write_text(json.dumps(report, indent=2))
print('AUDIT_UV', json.dumps(report))
