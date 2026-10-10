"""Clear the workbench, add native office props, and match extractor metal."""
import sys,json,math,numpy as np
from pathlib import Path
sys.path.insert(0,r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
from szio.gta5 import try_load_asset,save_asset,AssetTarget,AssetFormat,AssetVersion
from szio.gta5.entities import Entity,EntityFlags,EntityLodLevel,EntityPriorityLevel
from szio.types import Vector,Quaternion
root=Path(__file__).resolve().parents[2];lab=root/'laboratorio_fivem'
stream=root/'server-data/resources/cidade_laboratorio/stream'
out=lab/'office_fix';out.mkdir(exist_ok=True)
target=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)

# The two small containers occupy the entire rear half of the metal table.
# Keep the lower storage container and free the tabletop for the computer.
equipment=try_load_asset(stream/'lab_equipamentos.ydr');removed=0
for models in equipment.models.values():
 for model in models:
  for g in model.geometries:
   key=next(k for k in g.vertex_buffer.dtype.names if k.lower()=='position')
   p=g.vertex_buffer[key];t=g.index_buffer.reshape(-1,3);v=p[t]
   upper=np.all((v[:,:,0]>=1.00)&(v[:,:,0]<=1.98)&(v[:,:,1]>=5.0)&(v[:,:,1]<=5.51)&(v[:,:,2]>.995),axis=1)
   removed+=int(upper.sum())
   if upper.any():g.index_buffer=t[~upper].ravel().astype(g.index_buffer.dtype)
assert removed>=600,removed
save_asset(equipment,target,out,'lab_equipamentos')

vent=try_load_asset(stream/'lab_ventilacao.ydr');reassigned=0
for models in vent.models.values():
 for model in models:
  for g in model.geometries:
   if g.shader_index in (2,3,4,6):g.shader_index=1;reassigned+=1
assert reassigned>=4,reassigned
save_asset(vent,target,out,'lab_ventilacao')

placement=json.loads((lab/'placement.json').read_text());o=np.array(placement['origin']);basis=np.array(placement['basis']);heading=math.radians(placement['heading'])
def entity(name,loc,theta=0):
 ang=-(heading+theta)/2
 return Entity(name,Vector(o+basis@np.array(loc)),Quaternion((math.cos(ang),0,0,math.sin(ang))),1,1,EntityFlags.IS_STATIC,0,-1,100,0,EntityLodLevel.ORPHANHD,EntityPriorityLevel.REQUIRED,0,255,255,0,[])
office=[
 ('prop_off_chair_04b',[1.67,4.31,.06],math.pi),
 ('prop_off_phone_01',[1.08,5.32,.995],0),
 ('prop_monitor_01c',[1.60,5.47,.995],0),
 ('prop_keyboard_01a',[1.58,5.10,.995],0),
 ('prop_mouse_01a',[2.06,5.10,.995],0),
 ('prop_pc_01a',[2.27,5.26,.26],0),
]
ymap=try_load_asset(stream/'cidade_laboratorio.ymap')
names={x[0] for x in office};ymap.entities=[e for e in ymap.entities if e.archetype_name not in names]
ymap.entities.extend(entity(*x) for x in office)
save_asset(ymap,target,out,'cidade_laboratorio')

for f in ('lab_equipamentos.ydr','lab_ventilacao.ydr','cidade_laboratorio.ymap'):
 assert try_load_asset(out/f) is not None,f
assert len(try_load_asset(out/'cidade_laboratorio.ymap').entities)==67
(lab/'office_fix_report.json').write_text(json.dumps({'native_office_props':[x[0] for x in office],'tabletop_triangles_removed':removed,'vent_geometries_matched':reassigned,'entities':67},indent=2))
print('OFFICE_FIX_OK',removed,reassigned,len(ymap.entities),flush=True)
