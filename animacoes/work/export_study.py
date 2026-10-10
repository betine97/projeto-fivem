import bpy,sys,json
from pathlib import Path
root=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(root/'work'))
from export_orientation import forward_action
sys.path[:0]=[r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps',r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\sollumz']
import addon_utils
addon_utils.enable('Sollumz',default_set=True)
bpy.ops.wm.open_mainfile(filepath=str(root/'ajoelhado_refinado.blend'))
from Sollumz.ycd.ycdimport import create_clip_dictionary_template,create_anim_obj
from Sollumz.ycd.ycdexport import export_ycd
from Sollumz.sollumz_properties import SollumType
from szio.gta5.cwxml.clipdictionary import YCD
rig=bpy.data.objects['GTA_Personagem_Rig']
d,clips,anims=create_clip_dictionary_template('cidade_combate_frente_v4')
for name,actionname in [('ajoelhar_mira','ESTUDO_ajoelhar_mira'),('recuo','ESTUDO_recuo')]:
 # Preserve the imported skeleton's rest-space convention. Sollumz already
 # converts pose-space rotations on export; adding pi here reversed the ped.
 action=forward_action(rig,bpy.data.actions[actionname])
 a=create_anim_obj(SollumType.ANIMATION);a.name=name+'_anim';a.parent=anims
 a.animation_properties.hash=name+'_anim';a.animation_properties.target_id=rig.data;a.animation_properties.action=action
 c=create_anim_obj(SollumType.CLIP);c.name=name;c.parent=clips;c.clip_properties.hash=name;c.clip_properties.name=name;c.clip_properties.duration=29/30
 ca=c.clip_properties.animations.add();ca.animation=a;ca.start_frame=1;ca.end_frame=30
path=root/'exports'/'cidade_combate_frente_v4.ycd.xml'
assert export_ycd(d,str(path))
y=YCD.from_xml_file(str(path));assert len(y.clips)==2 and len(y.animations)==2
(root/'exports'/'validacao.json').write_text(json.dumps({'xml_roundtrip':True,'clips':len(y.clips),'animations':len(y.animations),'binary_ycd':False,'game_tested':False,'status':'Estudo; empunhadura e root motion ainda precisam de ajustes'},indent=2),encoding='utf8')
rig.animation_data.action=bpy.data.actions['ESTUDO_ajoelhar_mira'];bpy.context.scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(root/'ajoelhado_refinado.blend'))
print('XML ROUNDTRIP OK',len(y.clips),len(y.animations))
