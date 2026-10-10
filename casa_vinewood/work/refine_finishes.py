"""Thicken the accepted slabs downward and split opaque window returns from panes."""
import bpy,bmesh,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps')]
import numpy as np
bpy.ops.wm.open_mainfile(filepath=str(W/'backup_antes_acabamentos_camera/mansao_encaixada.blend'))
cols={k:next(c for c in bpy.data.collections if c.name.startswith(p)) for k,p in [('outer','01_'),('slabs','04_'),('stairs','05_')]}
changed=[]
for ob in [*cols['slabs'].objects,*cols['stairs'].objects,*cols['outer'].objects]:
 if ob.type!='MESH' or ob.name not in ('Laje superior contorno nativo','Escada chegada superior','Escada patamar intermediario','Fechamento borda mezanino','Fechamento borda quarto sobre sala'):continue
 ps=[ob.matrix_world@v.co for v in ob.data.vertices];low=min(p.z for p in ps);top=max(p.z for p in ps)
 # The finished walking level and every door threshold remain at their accepted elevation.
 target=.45 if top>2.7 else .35;new_low=top-target
 for v in ob.data.vertices:
  p=ob.matrix_world@v.co
  if abs(p.z-low)<.0001:p.z=new_low;v.co=ob.matrix_world.inverted()@p
 changed.append(dict(name=ob.name,old_depth_m=top-low,new_depth_m=target,walking_level_z=top))
glass=next(o for o in cols['outer'].objects if o.name.startswith('Vidros'))
glass.data.calc_loop_triangles();pane=[];returns=[]
for t in glass.data.loop_triangles:
 p=np.array([glass.matrix_world@glass.data.vertices[i].co for i in t.vertices]);n=np.cross(p[1]-p[0],p[2]-p[0]);length=np.linalg.norm(n)
 if length<1e-7:continue
 axis=int(np.argmax(abs(n)));axes=[i for i in range(3) if i!=axis]
 (pane if abs(n[2]/length)<.2 and np.ptp(p[:,axes],axis=0).min()>=.15 else returns).append(p.tolist())
def make(name,tris,mat):
 me=bpy.data.meshes.new(name);me.from_pydata([v for t in tris for v in t],[],[(i,i+1,i+2) for i in range(0,3*len(tris),3)]);me.update();me.materials.append(mat)
 ob=bpy.data.objects.new(name,me);cols['outer'].objects.link(ob);return ob
material=glass.data.materials[0]
frame=bpy.data.materials.get('Caixilho solido das janelas') or bpy.data.materials.new('Caixilho solido das janelas');frame.diffuse_color=(.72,.72,.68,1)
make('Vidros nos vaos nativos',pane,material)
make('Caixilhos solidos das janelas',returns,frame)
bpy.data.objects.remove(glass,do_unlink=True)
assert len(pane)==174 and len(returns)==1224
for c in cols.values():c.hide_viewport=False
bpy.context.scene['status']='Acabamentos: laje superior 45cm, patamar 35cm e caixilhos opacos; vidro preservado.'
(W/'acabamentos_geometria.json').write_text(json.dumps({'slabs':changed,'transparent_pane_triangles':len(pane),'opaque_window_return_triangles':len(returns),'floor_elevations_preserved':True},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(W/'mansao_encaixada.blend'))
print('FINISHING_GEOMETRY_OK',changed,flush=True)
