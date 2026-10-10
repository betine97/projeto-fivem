"""Export the prepared prone study without modifying the kneeling resource."""
import bpy,sys,json
from pathlib import Path
root=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(root/'work'))
from export_orientation import forward_action
sys.path[:0]=[r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps',r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\sollumz']
import addon_utils
addon_utils.enable('Sollumz',default_set=True)
bpy.ops.wm.open_mainfile(filepath=str(root/'deitado_tiro.blend'))
from Sollumz.ycd.ycdimport import create_clip_dictionary_template,create_anim_obj
from Sollumz.ycd.ycdexport import export_ycd
from Sollumz.sollumz_properties import SollumType
from szio.gta5.cwxml.clipdictionary import YCD
rig=bpy.data.objects['GTA_Personagem_Rig']
dictionary,clips,animations=create_clip_dictionary_template('cidade_deitado_tiro_v4')
for name,action in [('deitado_mira','DEITADO_mira'),('deitado_disparo','DEITADO_disparo'),('levantar_deitado','DEITADO_levantar')]:
 animation=create_anim_obj(SollumType.ANIMATION);animation.name=name+'_anim';animation.parent=animations
 animation.animation_properties.hash=name+'_anim'
 # Assign target BEFORE action to avoid retargeting an already authored rig.
 animation.animation_properties.target_id=rig.data
 animation.animation_properties.action=forward_action(rig,bpy.data.actions[action])
 clip=create_anim_obj(SollumType.CLIP);clip.name=name;clip.parent=clips
 last=int(bpy.data.actions[action].frame_range[1])
 clip.clip_properties.hash=name;clip.clip_properties.name=name;clip.clip_properties.duration=(last-1)/(60 if name=='levantar_deitado' else 30)
 item=clip.clip_properties.animations.add();item.animation=animation;item.start_frame=1;item.end_frame=last
path=root/'exports/cidade_deitado_tiro_v4.ycd.xml'
assert export_ycd(dictionary,str(path))
result=YCD.from_xml_file(str(path))
assert len(result.clips)==3 and len(result.animations)==3
(root/'exports/validacao_deitado.json').write_text(json.dumps({'xml_roundtrip':True,'clips':3,'animations':3,'binary_ycd':False,'game_tested':False},indent=2))
print('PRONE EXPORT PASS: 3 clips / 3 animations')
