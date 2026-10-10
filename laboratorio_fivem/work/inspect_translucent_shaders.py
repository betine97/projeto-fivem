import sys
from pathlib import Path
sys.path.insert(0,r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
from szio.rpf import open_rpf
from szio.gta5 import try_load_asset

base=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V')
work=Path(__file__).parent
out=work/'translucent_shader_samples';out.mkdir(exist_ok=True)
names={'v_ilev_prop_fib_glass','prop_showroom_glass_1b','v_31a_jh_tun_plastic',
       'v_34_curtain01','cs2_02_plastic_01','v_med_curtains'}
cache={}
for line in (work/'assets_index.txt').read_text().splitlines():
 parts=line.split('|')
 if len(parts)!=3 or Path(parts[2]).stem not in names:continue
 key=tuple(parts[:2])
 try:
  if key not in cache:cache[key]=open_rpf(base/parts[0]).open_nested(parts[1])
  path=out/parts[2];path.write_bytes(cache[key].read_bytes(parts[2]));a=try_load_asset(path)
  print('SAMPLE',path.name,'size',path.stat().st_size,'shaders',len(a.shader_group.shaders),'textures',list(a.shader_group.embedded_textures),flush=True)
  for i,s in enumerate(a.shader_group.shaders):
   print('SHADER',i,s.name,s.preset_filename,s.render_bucket,
         [(p.name,str(p.value)[:40]) for p in s.parameters if 'sampler' in p.name.lower()],flush=True)
 except Exception as e:print('ERROR',parts[2],repr(e),flush=True)
