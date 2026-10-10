import sys,json,subprocess,copy
from pathlib import Path
sys.path.insert(0,r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
from szio.gta5 import *
from szio.gta5.drawables import LodLevel
from szio.types import DataSource,Vector
W=Path(__file__).resolve().parents[1];out=W/'polido';out.mkdir(exist_ok=True);cache=W/'plant_runtime';cache.mkdir(exist_ok=True)
target=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
r=json.loads((W/'export_report_hd.json').read_text())
for m in r['models']:
 n=m['name']
 if not n.startswith('lab_planta') or (out/(n+'.ydr')).exists():continue
 a=try_load_asset(W/'exports_hd'/(n+'.ydr'));old=try_load_asset(W/'exports'/(n+'.ydr'))
 for key,t in a.shader_group.embedded_textures.items():
  size=4 if key.endswith('_spec') else (512 if key.endswith('_normal') else 1024)
  source=W/'bakes_hd'/(key+'.png');dds=cache/(key+'.dds')
  if not dds.exists():subprocess.run([str(W.parent/'.downloads/texconv.exe'),'-y','-nologo','-f','BC3_UNORM' if key.endswith('_normal') else 'BC1_UNORM','-m','0','-w',str(size),'-h',str(size),'-o',str(cache),str(source)],check=True,stdout=subprocess.DEVNULL)
  t.width=size;t.height=size;t.data=DataSource.create(dds.read_bytes())
 for shader in a.shader_group.shaders:
  for p in shader.parameters:
   if p.name=='specularIntensityMult':p.value=Vector((.12,0,0,0))
   if p.name=='bumpiness':p.value=Vector((.25,0,0,0))
   if p.name=='specularFalloffMult':p.value=Vector((12,0,0,0))
 offset=len(a.shader_group.shaders);a.shader_group.shaders.extend(old.shader_group.shaders);a.shader_group.embedded_textures.update(old.shader_group.embedded_textures)
 a.models[LodLevel.MEDIUM]=old.models[LodLevel.HIGH]
 for model in a.models[LodLevel.MEDIUM]:
  for g in model.geometries:
   g.shader_index+=offset
   for field in ('Colour0','Colour1'):
    if field in g.vertex_buffer.dtype.names:g.vertex_buffer[field][:,:3]=114
 a.lod_thresholds[LodLevel.HIGH]=18;a.lod_thresholds[LodLevel.MEDIUM]=100
 save_asset(a,target,out,n);assert try_load_asset(out/(n+'.ydr')) is not None
 print('PLANT_POLISHED',n,flush=True)
