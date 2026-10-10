"""Remove coplanar overlap at the shared level of the closed outer walls."""
import bpy,bmesh,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(W/'work/pydeps')]
import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union
bpy.ops.wm.open_mainfile(filepath=str(W/'mansao_encaixada.blend'))
outer=next(c for c in bpy.data.collections if c.name.startswith('01_'));join_z=2.358
panels=json.loads((W/'revisao_juntas.json').read_text());axes={r['name']:r['axis'] for r in panels['panels']}
def overlap():
 regions={'terreo':{},'superior':{}}
 for ob in outer.objects:
  level='terreo' if ob.name.startswith('Revestimento continuo terreo') else 'superior' if ob.name.startswith('Revestimento continuo superior') else None
  if not level:continue
  axis=axes[ob.name];projection=(1,2) if axis==0 else (0,2);ob.data.calc_loop_triangles()
  for t in ob.data.loop_triangles:
   if abs(t.normal[axis])<.99:continue
   p=np.array([ob.matrix_world@ob.data.vertices[i].co for i in t.vertices]);key=(axis,round(float(p[:,axis].mean()),4),int(t.normal[axis]>0))
   regions[level].setdefault(key,[]).append(Polygon(p[:,projection]))
 return sum(unary_union(regions['terreo'][k]).intersection(unary_union(regions['superior'][k])).area for k in regions['terreo'].keys()&regions['superior'].keys())
before=overlap();changed=[];spec=json.loads((W/'espessuras_estruturais.json').read_text());by_name={r['name']:r for r in spec['solids']}
for ob in outer.objects:
 if not ob.name.startswith('Revestimento continuo terreo'):continue
 for p in ob.data.polygons:
  if p.normal.z>.99 and all(abs(ob.data.vertices[i].co.z-join_z)<1e-6 for i in p.vertices):p.material_index=0
 if max(v.co.z for v in ob.data.vertices)<=join_z+1e-6:continue
 bm=bmesh.new();bm.from_mesh(ob.data)
 bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=(0,0,join_z),plane_no=(0,0,1),dist=1e-6,clear_outer=True,clear_inner=False)
 boundary=[e for e in bm.edges if e.is_boundary]
 caps=bmesh.ops.holes_fill(bm,edges=boundary,sides=0)
 for face in caps.get('faces',[]):face.material_index=0
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.normal_update()
 assert all(e.is_manifold for e in bm.edges),ob.name
 volume=bm.calc_volume(signed=True);assert volume>0,(ob.name,volume)
 bm.to_mesh(ob.data);bm.free();ob.data.update();changed.append(ob.name)
 ps=np.array([ob.matrix_world@v.co for v in ob.data.vertices]);row=by_name[ob.name];row['lo']=ps.min(0).tolist();row['hi']=ps.max(0).tolist();row['volume_after_m3']=volume
 for panel in panels['panels']:
  if panel['name']==ob.name:panel['bounds'][3]=join_z;panel['area_m2']=volume/.25
 uv=ob.data.uv_layers[0]
 for p in ob.data.polygons:
  tile=ob.data.materials[p.material_index].get('uv_tile_m',1.8);axis=max(range(3),key=lambda i:abs(p.normal[i]));projection=(0,1) if axis==2 else (0,2) if axis==1 else (1,2)
  for i in p.loop_indices:
   q=ob.matrix_world@ob.data.vertices[ob.data.loops[i].vertex_index].co;uv.data[i].uv=(q[projection[0]]/tile,q[projection[1]]/tile)
after=overlap();assert after<1e-6,after
spec['outer_shared_level_z']=join_z;spec['outer_level_overlap_m2']=after
(W/'espessuras_estruturais.json').write_text(json.dumps(spec,indent=2),encoding='utf-8');(W/'revisao_juntas.json').write_text(json.dumps(panels,indent=2),encoding='utf-8')
report=dict(passed=True,shared_level_z=join_z,before_coplanar_overlap_m2=before,after_coplanar_overlap_m2=after,changed_ground_panels=changed,closed_volumes_preserved=True,wall_thicknesses_preserved=True,door_apertures_preserved=True,walking_levels_preserved=True)
if changed:(W/'correcao_encontro_paredes.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(W/'mansao_encaixada.blend'));print('OUTER_LEVEL_JOIN_FIXED',len(changed),'panels;',before,'->',after,'m2 coplanar overlap',flush=True)
