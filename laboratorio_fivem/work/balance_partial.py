import sys,subprocess,struct,json
from pathlib import Path
sys.path.insert(0,r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
from szio.gta5 import *
from szio.types import DataSource
W=Path('laboratorio_fivem').resolve();dest=W.parent/'server-data/resources/cidade_laboratorio/stream';cache=W/'runtime_balanced';cache.mkdir(exist_ok=True)
names=json.loads((W/'implantacao_parcial_hd.json').read_text())['installed_models']
for n in names:
 a=try_load_asset(dest/(n+'.ydr'))
 for key,t in a.shader_group.embedded_textures.items():
  png=W/'bakes_hd'/(key+'.png');limit=1024 if n=='lab_equipamentos' else 2048
  if key.endswith('_normal'):limit=512
  if key.endswith('_spec'):limit=4
  size=min(t.width,limit);fmt='BC3_UNORM' if key.endswith('_normal') else 'BC1_UNORM'
  subprocess.run([str(W.parent/'.downloads/texconv.exe'),'-y','-nologo','-f',fmt,'-m','0','-w',str(size),'-h',str(size),'-o',str(cache),str(png)],check=True,stdout=subprocess.DEVNULL)
  data=(cache/(key+'.dds')).read_bytes();t.width=size;t.height=size;t.data=DataSource.create(data)
 save_asset(a,(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),),dest,n);assert try_load_asset(dest/(n+'.ydr')) is not None
 print('BALANCED',n,flush=True)
