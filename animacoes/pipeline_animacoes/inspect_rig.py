"""Read existing studies and extract a local rifle reference for the new pipeline."""
import bpy, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DEPS = Path(r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
SOLLUMZ = DEPS.parent / 'sollumz'
sys.path[:0] = [str(DEPS), str(SOLLUMZ)]
import addon_utils
addon_utils.enable('Sollumz', default_set=True)
from szio.rpf import open_rpf

assets = HERE / 'assets'
assets.mkdir(parents=True, exist_ok=True)
archive = open_rpf(r'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V\x64e.rpf')
weapons = archive.open_nested('models/cdimages/weapons.rpf')
for name in ('w_ar_assaultrifle.ydr', 'w_ar_assaultrifle.ytd'):
    (assets / name).write_bytes(weapons.read_bytes(name))

report = {}
for filename, action in [('ajoelhado_refinado.blend', 'ESTUDO_ajoelhar_mira'), ('deitado_tiro.blend', 'DEITADO_mira')]:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT / filename))
    rig = bpy.data.objects['GTA_Personagem_Rig']
    rig.animation_data.action = bpy.data.actions[action]
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()
    gun = bpy.data.objects['w_ar_carbinerifle']
    report[filename] = {
        'rigs': {o.name: len(o.data.bones) for o in bpy.data.objects if o.type == 'ARMATURE'},
        'joints': {b.name: list(rig.matrix_world @ b.head) for b in rig.pose.bones if b.name.startswith('SKEL_') and 'Finger' not in b.name},
        'gun_contacts': {b.name: list(gun.matrix_world @ b.head_local) for b in gun.data.bones},
        'gun_matrix': [list(row) for row in gun.matrix_world],
        'bones': [{'name': b.name, 'parent': b.parent.name if b.parent else None, 'tag': b.bone_properties.tag} for b in rig.data.bones],
        'visible_meshes': [{'name': o.name, 'parent': o.parent.name if o.parent else None,
            'modifiers': [(m.type, m.object.name if m.type == 'ARMATURE' and m.object else None) for m in o.modifiers]}
            for o in bpy.data.objects if o.type == 'MESH' and not o.hide_render],
    }
bpy.ops.sollumz.import_assets(directory=str(assets), files=[{'name': 'w_ar_assaultrifle.ydr'}], use_custom_settings=True)
gun = bpy.data.objects['w_ar_assaultrifle']
report['assault_contacts'] = {b.name: list(b.head_local) for b in gun.data.bones}
(HERE / 'inspection.json').write_text(json.dumps(report, indent=2), encoding='utf8')
print('PIPELINE_INSPECT_OK', HERE / 'inspection.json')
