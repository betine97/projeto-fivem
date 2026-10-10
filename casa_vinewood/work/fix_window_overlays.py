"""Remove the three residual opaque window light planes and install the result."""
import sys, json, shutil, hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[2]; W=R/'casa_vinewood'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
from szio.gta5 import try_load_asset, save_asset, AssetTarget, AssetFormat, AssetVersion
name='ch2_09b_emissive_05.ydr'; package=W/'fivem'/name
installed=R/'server-data/resources/cidade_mansao/stream'/name
backup=W/'backup_antes_janelas'; backup.mkdir(exist_ok=True)
for f in [installed,W/'verificacao_fivem.json',W/'audit_janelas.json',W/'alteracoes_nativas.json']:
 if f.exists() and not (backup/f.name).exists(): shutil.copy2(f,backup/f.name)
a=try_load_asset(backup/name); removed=0
for models in a.models.values():
 for model in models:
  keep=[]
  for g in model.geometries:
   s=a.shader_group.shaders[g.shader_index]
   tex=next((p.value for p in s.parameters if p.name.lower()=='diffusesampler'),'')
   if str(tex).startswith('im_emissive_window_'): removed+=len(g.index_buffer)//3
   else: keep.append(g)
  model.geometries=keep
assert removed==15, removed
# GEN8 supports drawables with no LOD models; keep the named asset as an empty
# replacement so the original map's fake window-light entity renders nothing.
assert all(not m.geometries for ms in a.models.values() for m in ms)
a.models={}
save_asset(a,(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),),package.parent,package.stem)
b=try_load_asset(package); assert b and not b.models
for models in b.models.values():
 for m in models:
  for g in m.geometries:
   assert next((p.value for p in b.shader_group.shaders[g.shader_index].parameters if p.name.lower()=='diffusesampler'),'')!='im_emissive_window_005'
shutil.copy2(package,installed)
digest=hashlib.sha256(package.read_bytes()).hexdigest()
assert hashlib.sha256(installed.read_bytes()).hexdigest()==digest
p=W/'verificacao_fivem.json'; report=json.loads(p.read_text());report['files'][name]={'bytes':package.stat().st_size,'sha256':digest}
report.update(installed_files_match=True,activation_requires_resource_reload=True,in_game_test=False)
for n,data in report['files'].items():
 assert hashlib.sha256((installed.parent/n).read_bytes()).hexdigest()==data['sha256'],n
p.write_text(json.dumps(report,indent=2))
p=W/'alteracoes_nativas.json'; report=json.loads(p.read_text()); report['window_overlay_revision']={'file':name,'removed_triangles':removed,'fully_covered_windows':3,'additional_upper_edge_strips_removed':9,'empty_native_replacement_roundtrip_verified':True,'in_game_verified':False};p.write_text(json.dumps(report,indent=2))
print('INSTALLED_WINDOW_OVERLAY_FIX',removed,'triangles; 3 full window overlays plus edge strips; 19 installed hashes verified')
