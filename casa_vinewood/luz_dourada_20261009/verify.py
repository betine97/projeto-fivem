import sys,json,ast as pyast,math,hashlib
from pathlib import Path
from collections import Counter
from dataclasses import fields,is_dataclass
from enum import Enum
P=Path(__file__).resolve().parent;R=P.parents[1];B=P/'backup';O=P/'package'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(R/'casa_vinewood/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps',str(R/'casa_vinewood/work/lua_syntax_deps')]
import numpy as np
from PIL import Image
from szio.gta5 import *
from szio.gta5.bounds import AssetBoundComposite,AssetBoundBvh
from szio.gta5.drawables import LightType,LightFlashiness
import pymateria.gta5 as pm
from shapely.geometry import Polygon,Point
from luaparser import ast
from lupa import LuaRuntime
def import_helpers(path,names):
 tree=pyast.parse(path.read_text());body=[n for n in tree.body if isinstance(n,pyast.FunctionDef) and n.name in names];exec(compile(pyast.Module(body=body,type_ignores=[]),'helpers','exec'),globals())
import_helpers(R/'casa_vinewood/luminarias_cor_alcance_20261008/verify.py',['equal','collision'])
import_helpers(R/'casa_vinewood/luz_referencia_quente_20261008/verify.py',['evaluate'])
cfg=json.loads((O/'iluminacao_ambiente.json').read_text());old=json.loads((B/'iluminacao_ambiente.json').read_text());project=json.loads((P/'project.json').read_text())
native=[];assets=[]
for name in ['mansao_teto','mansao_pendentes','mansao_tv','mansao_spot_embutido']:
 a=try_load_asset(B/'stream'/(name+'.ydr'));b=try_load_asset(O/'stream'/(name+'.ydr'))
 assert equal(a.models,b.models) and equal(a.skeleton,b.skeleton) and equal(a.lod_thresholds,b.lod_thresholds)
 collision(a.bounds,b.bounds)
 assert len(a.lights)==len(b.lights)
 for x,y in zip(a.lights,b.lights):
  assert x.light_hash==y.light_hash and x.light_type==y.light_type
  assert y.time_flags==0xffffff and y.flashiness==LightFlashiness.CONSTANT
  assert y.flags&pm.LightFlags.NO_SPECULAR.value
  assert y.volume_intensity==y.volume_outer_intensity==y.corona_intensity==y.corona_size==0
  assert 0<y.intensity<2 and np.isfinite(y.position).all()
  assert not y.flags&pm.LightFlags.CAST_HIGHER_RES_SHADOWS.value
  if not equal(x.position,y.position):
   assert name=='mansao_teto' and y.light_type==LightType.CAPSULE
   assert math.isclose(y.culling_plane_offset,y.position[2]+.8+.03,abs_tol=1e-5)
 for x,y in zip(a.shader_group.shaders,b.shader_group.shaders):
  assert x.name==y.name and x.preset_filename==y.preset_filename
  for u,v in zip(x.parameters,y.parameters):
   assert u.name==v.name
   if u.name!='emissivemultiplier':assert equal(u.value,v.value)
 assert a.shader_group.embedded_textures.keys()==b.shader_group.embedded_textures.keys()
 for k,tx in a.shader_group.embedded_textures.items():
  nt=b.shader_group.embedded_textures[k]
  if name=='mansao_spot_embutido' and k=='spot_lente':
   assert nt.width==nt.height==4 and tx.data.read_bytes()!=nt.data.read_bytes()
  else:assert tx.data.read_bytes()==nt.data.read_bytes() and tx.width==nt.width and tx.height==nt.height
 native+=b.lights;assets.append(dict(model=name,native_lights=len(b.lights),geometry_collision_other_textures_preserved=True))
assert len(native)==129 and len({li.light_hash for li in native})==129
assert Counter(li.light_type.name for li in native)==Counter(SPOT=97,POINT=21,CAPSULE=11)
shadow_count=sum(bool(li.flags&pm.LightFlags.CAST_SHADOWS.value) for li in native)
assert shadow_count==5 and cfg['native_shadow_count']==5
assert cfg['native_count']==149 and len(cfg['native_lights'])==125 and len(cfg['decorative_native_lights'])==24
assert cfg['max_lights']==0 and cfg['lights']==[] and cfg['native_always_on']
assert cfg['clean_postfx']['variables']==old['clean_postfx']['variables']
assert cfg['clean_postfx']['interior_polygons']==old['clean_postfx']['interior_polygons']
code=(O/'iluminacao_decorativa.lua').read_text();ast.parse(code)
normalized=code.replace('PERFIL v9','PERFIL v8').replace('Perfil v9','Perfil v8').replace('destaques dourados, paredes e sombras locais.','potencia e brilho especular reduzidos.')
assert normalized==(B/'iluminacao_decorativa.lua').read_text()
# Execute the existing meaningful optical lifecycle tests against this package,
# with its new config and diagnostic text; no source from another task is run.
test=pyast.parse((R/'casa_vinewood/luz_contraste_20261008/verify.py').read_text())
start=next(i for i,n in enumerate(test.body) if isinstance(n,pyast.Assign) and any(isinstance(t,pyast.Name) and t.id=='cases' for t in n.targets))
end=next(i for i,n in enumerate(test.body) if isinstance(n,pyast.Assign) and any(isinstance(t,pyast.Name) and t.id=='report' for t in n.targets))
exec(compile(pyast.Module(body=test.body[start:end],type_ignores=[]),'optical_lifecycle_tests','exec'))
analysis=[]
regions=json.loads((R/'casa_vinewood/luz_permanente_20261008/projeto_luminotecnico.json').read_text())['regions']
for region in regions[:3]:
 poly=Polygon(region['polygon']).buffer(-.2);x0,y0,x1,y1=poly.bounds
 points=np.array([[x,y,-.79] for x in np.arange(x0,x1,.2) for y in np.arange(y0,y1,.2) if poly.contains(Point(x,y))]);normals=np.tile([0,0,1],(len(points),1))
 before=evaluate(old['native_lights'],points,normals,-.8);after=evaluate(cfg['native_lights'],points,normals,-.8)
 ratio=float(np.median(after@np.array([.2126,.7152,.0722]))/np.median(before@np.array([.2126,.7152,.0722])))
 assert .65<ratio<1.4 and after.min()>=0
 assert np.median(after[:,1]/np.maximum(after[:,0],1e-8))<np.median(before[:,1]/np.maximum(before[:,0],1e-8))
 analysis.append(dict(room=region['name'],samples=len(points),relative_diffuse_floor_luminance=ratio))
walls=np.array([[6.49,-2.65,z] for z in np.linspace(-.2,2.3,20)]+[[11.80,-.94,z] for z in np.linspace(-.2,2.3,20)])
normals=np.array([[1,0,0]]*20+[[0,-1,0]]*20)
before=evaluate(old['native_lights'],walls,normals,-.8);after=evaluate(cfg['native_lights'],walls,normals,-.8)
wall_ratio=float(np.median(after[:,0])/max(1e-8,np.median(before[:,0])));assert wall_ratio>1.1
report=dict(passed=True,assets=assets,native_sources_unchanged=True,native_shadows=shadow_count,whole_house_light_availability_preserved=True,optical_cleanup_preserved=True,lua_lifecycle_cases=cases,floor_distribution_proxy=analysis,target_wall_red_median_ratio=wall_ratio,visual_match_verified=False,sha256={t:hashlib.sha256((O/t).read_bytes()).hexdigest() for t in project['targets']})
(P/'verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(dict(passed=True,floor=analysis,wall_ratio=wall_ratio,shadows=shadow_count,lua_cases=len(cases)),indent=2))
