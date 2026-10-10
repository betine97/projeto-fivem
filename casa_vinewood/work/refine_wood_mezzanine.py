"""Keep wood only inside the outlined mezzanine, ending at room thresholds."""
import bpy,bmesh,json
from pathlib import Path
W=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(W/'mansao_encaixada.blend'))
ob=bpy.data.objects['Laje superior contorno nativo']
wood=next(i for i,m in enumerate(ob.data.materials) if m.get('finish_family','wood')=='wood')
marble=next(i for i,m in enumerate(ob.data.materials) if m.get('finish_family')=='marble')
bm=bmesh.new();bm.from_mesh(ob.data)
bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=(0,1.65,0),plane_no=(0,1,0),dist=1e-6,clear_inner=False,clear_outer=False)
bm.normal_update();hall=[-.8,6.4,-3.85,1.65];areas={'wood':0.,'marble':0.}
for f in bm.faces:
 if f.normal.z<.9:continue
 c=f.calc_center_median();inside=hall[0]-1e-6<c.x<hall[1]+1e-6 and hall[2]-1e-6<c.y<hall[3]+1e-6
 f.material_index=wood if inside else marble;areas['wood' if inside else 'marble']+=f.calc_area()
assert all(e.is_manifold for e in bm.edges)
bm.to_mesh(ob.data);bm.free();ob.data.update()
p=W/'aplicacao_materiais_sofa.json';r=json.loads(p.read_text());r.update(upper_wood_hall_bounds=hall,upper_floor_surface_m2=areas);p.write_text(json.dumps(r,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(W/'mansao_encaixada.blend'));print('MARKED_MEZZANINE_ONLY',hall,areas,flush=True)
