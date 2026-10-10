import sys,shutil
from pathlib import Path
sys.path.insert(0,r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
from szio.gta5 import *
from szio.types import Vector
W=Path(__file__).resolve().parents[1];src=W.parent/'server-data/resources/cidade_laboratorio/stream';out=W/'polido';out.mkdir(exist_ok=True)
for n in ('lab_ventilacao','lab_equipamentos','lab_vasos','lab_racks','lab_leds'):
 a=try_load_asset(src/(n+'.ydr'))
 for sh in a.shader_group.shaders:
  for p in sh.parameters:
   if p.name=='bumpiness':p.value=Vector((.25 if n=='lab_ventilacao' else .45,0,0,0))
   if p.name=='specularIntensityMult':p.value=Vector((.65 if n=='lab_ventilacao' else .8,0,0,0))
   if p.name=='specularFalloffMult':p.value=Vector((24,0,0,0))
   if p.name=='emissiveMultiplier':p.value=Vector((4,0,0,0))
 save_asset(a,(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),),out,n);assert try_load_asset(out/(n+'.ydr')) is not None
 print('MATERIAL_POLISHED',n,flush=True)
