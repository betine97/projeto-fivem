import bpy,sys,json
from pathlib import Path
from mathutils import Vector,Quaternion
root=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(root/'CONJUNTO_COMPLETO.blend'))
def smooth(a,b,x):
 t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
shoes=bpy.data.objects['MOCASSINS_MARRONS'];pants=bpy.data.objects['CALCA_BEGE']
for v in shoes.data.vertices:
 x,y,z=v.co;front=1-smooth(-.05,.045,y);toe=1-smooth(-.12,-.04,y);center=.16 if x>0 else -.16
 v.co.x=center+(x-center)*(1+.23*toe)
 arch=smooth(-.075,-.025,y)*(1-smooth(.045,.090,y))
 v.co.z=z+.020*smooth(-.998,-.980,z)*(1-smooth(-.948,-.865,z))*front-.026*arch*(1-smooth(-.983,-.952,z))
for v in pants.data.vertices:
 x,y,z=v.co;t=1-smooth(-.90,-.75,z);center=.155 if x>0 else -.155
 v.co.y=.04+(y-.04)*(1+.80*t)
 v.co.x=center+(x-center)*(1+.08*t)
 upper=1-smooth(-.78,-.68,z)
 v.co.x=center+(v.co.x-center)*(1+.15*upper)
 v.co.y=.04+(v.co.y-.04)*(1+.15*upper)
for filename in [root/'CONJUNTO_COMPLETO.blend',root.parent/'camisa_estampada/PERSONAGEM_COM_CAMISA.blend',root.parent/'calca_bege/PERSONAGEM_COM_CALCA_BEGE.blend']:
 bpy.ops.wm.save_as_mainfile(filepath=str(filename))
print('SMOOTH_FOOT_FIT_OK',flush=True)
sc=bpy.context.scene;sc.cycles.samples=16;cam=sc.camera;cam.location=(2,-3,-.83);cam.rotation_euler=(Vector((0,-.025,-.91))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.46
sc.render.resolution_x=800;sc.render.resolution_y=600;sc.render.filepath=str(root/'pes_revisao3.png');bpy.ops.render.render(write_still=True)
