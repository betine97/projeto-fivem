import bpy,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
DEPS=Path('C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps')
sys.path[:0]=[str(DEPS),str(DEPS.parent/'sollumz')]
from szio.gta5.cwxml.clipdictionary import YCD
from Sollumz.ycd.ycdimport import combine_sequences_and_build_action_data
for path,wanted in [(HERE.parent/'exports/native_move_crawl.xml',['onfront_fwd','onfront_bwd']),
                    (HERE/'move_aim_strafe_crouch_2h.xml',['run_fwd_0_loop','run_bwd_180_loop','run_fwd_90_loop','run_bwd_-90_loop']),
                    (HERE/'move_crouch_proto.xml',['run'])]:
    d=YCD.from_xml_file(str(path));anims={a.hash:a for a in d.animations}
    for clip in d.clips:
        if clip.name.removeprefix('pack:/').removesuffix('.clip') not in wanted:continue
        bindings=clip.animations or [clip]
        print('CLIP',path.name,clip.name,flush=True)
        for binding in bindings:
            a=anims[binding.animation_hash];data=combine_sequences_and_build_action_data(a)
            start=round(binding.start_time/a.duration*(a.frame_count-1))
            end=round(binding.end_time/a.duration*(a.frame_count-1))
            print('RANGE',start,end,binding.start_time,binding.end_time,'ROOT',
                  {int(k):[list(v[start]),list(v[end])] for k,v in data.get(0,{}).items() if k in (0,1,5,6)},flush=True)
