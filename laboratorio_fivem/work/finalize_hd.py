import sys,json,subprocess,struct
from pathlib import Path
sys.path.insert(0,r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
from szio.gta5 import *
from szio.types import DataSource,Vector
W=Path(__file__).resolve().parents[1];out=W/'exports_hd';mips=W/'mips_hd';mips.mkdir(exist_ok=True)
report=json.loads((W/'export_report_hd.json').read_text());target=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
for model in report['models']:
 name=model['name'];a=try_load_asset(out/(name+'.ydr'))
 for key,tex in a.shader_group.embedded_textures.items():
  png=W/'bakes_hd'/(key+'.png')
  if not png.exists():raise RuntimeError(str(png))
  index=int(key[len(name)+1:].split('_')[0]);info=next(x for i,x in enumerate(model['materials']) if i==index)
  size=4 if key.endswith('_spec') else min(tex.width,info['resolution'])
  if key.endswith('_normal'):size=min(size,2048)
  dest=mips/(key+'.dds')
  if not dest.exists():
   subprocess.run([str(W.parent/'.downloads/texconv.exe'),'-y','-nologo','-f','BC3_UNORM','-m','0','-w',str(size),'-h',str(size),'-o',str(mips),str(png)],check=True,stdout=subprocess.DEVNULL)
  data=dest.read_bytes();tex.width=struct.unpack_from('<I',data,16)[0];tex.height=struct.unpack_from('<I',data,12)[0];tex.data=DataSource.create(data)
 for shader in a.shader_group.shaders:
  for par in shader.parameters:
   if par.name=='emissiveMultiplier':par.value=Vector((3,0,0,0))
   if par.name=='specularFalloffMult':par.value=Vector((28,0,0,0))
   if par.name=='specularFresnel':par.value=Vector((.3,0,0,0))
 save_asset(a,target,out,name);print('MIPS_HD',name,flush=True)
