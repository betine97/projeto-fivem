"""Repair the one collapsed UV triangle that crossed into a wood atlas island."""
import bpy,json,sys
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood'
sys.path.insert(0,str(R/'laboratorio_fivem/work/pydeps'))
from PIL import Image
bpy.ops.wm.open_mainfile(filepath=str(W/'mansao_encaixada.blend'))
ob=bpy.data.objects['Painel TV rack e decoracao Meshy'];me=ob.data
p=me.polygons[51911]
assert (p.center-__import__('mathutils').Vector((-8.784946,-9.580075,1.240979))).length<.0001
uv=me.uv_layers[0];old=[list(uv.data[i].uv) for i in p.loop_indices]
center=np.mean(old,axis=0)
im=np.array(Image.open(W/'work/materiais/tv_original_albedo.jpg').convert('RGB'))
coords=[center+np.array(o) for o in [(-.00025,-.00025),(.00025,-.00025),(0,.00025)]]
for co in coords:assert max(im[int((1-co[1])*4095),int(co[0]*4095)])<35
for i,co in zip(p.loop_indices,coords):uv.data[i].uv=co
me.update();ob['screen_uv_repaired']=True
report=dict(source_face=p.index,old_uv=old,new_uv=[c.tolist() for c in coords],reason='Collapsed screen triangle sampled the neighboring wooden atlas island.',geometry_unchanged=True)
(W/'work/correcao_uv_tela_tv.json').write_text(json.dumps(report,indent=2))
spec=json.loads((W/'aplicacao_materiais_sofa.json').read_text());spec['tv']['screen_uv_repair']=report
(W/'aplicacao_materiais_sofa.json').write_text(json.dumps(spec,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(W/'mansao_encaixada.blend'))
print('TV_SCREEN_UV_REPAIRED',p.index,flush=True)
