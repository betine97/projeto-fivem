import sys,json,copy
from pathlib import Path
sys.path.insert(0,r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
from szio.gta5 import *
W=Path('laboratorio_fivem').resolve();dest=W.parent/'server-data/resources/cidade_laboratorio/stream';backup=W/'backup_pre_hd';backup.mkdir(exist_ok=True)
import shutil
names=['lab_estrutura','lab_piso','lab_equipamentos','lab_ventilacao','lab_leds','lab_vasos','lab_racks']
assets=[]
for n in names:
 a=try_load_asset(W/'exports_hd'/(n+'.ydr'));assert a is not None,n
 old=try_load_asset(dest/(n+'.ydr'));a.bounds=old.bounds
 assets.append((n,a))
for n,a in assets:
 shutil.copy2(dest/(n+'.ydr'),backup/(n+'.ydr'))
 save_asset(a,(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),),dest,n)
 assert try_load_asset(dest/(n+'.ydr')) is not None
 print('INSTALLED_HD',n,flush=True)
(W/'implantacao_parcial_hd.json').write_text(json.dumps({'installed_models':names,'plants':'Previous 54 plants retained; HD conversion paused after partial bake','pending':['remaining HD plants','floor collision verification','rain protection','final visual comparison'],'original_blender_preserved':True},indent=2))
