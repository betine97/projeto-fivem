import sys
from pathlib import Path
sys.path.insert(0,r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
from szio.rpf import open_rpf
from szio.gta5 import try_load_asset
base=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V')
out=Path(__file__).resolve().parent/'base_assets'
name='hei_ch3_08_36.ybn'
archives=[
 ('patch',base/'update/update.rpf','dlc_patch/mpheist/x64/levels/gta5/_hills/cityhills_03/ch3_08.rpf'),
 ('dlc',base/'update/x64/dlcpacks/mpheist/dlc.rpf','x64/levels/gta5/_hills/cityhills_03/ch3_08.rpf'),
]
for label,path,nested in archives:
 r=open_rpf(path).open_nested(nested)
 dest=out/(label+'_'+name);dest.write_bytes(r.read_bytes(name));a=try_load_asset(dest)
 print(label,dest.name,dest.stat().st_size,'valid',a is not None,flush=True)
