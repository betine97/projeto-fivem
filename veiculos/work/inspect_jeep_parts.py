import bpy,sys,addon_utils
sys.path[:0]=[r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps',r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\sollumz']
addon_utils.enable('Sollumz',default_set=True)
from pathlib import Path
root=Path(__file__).resolve().parent.parent
bpy.ops.wm.open_mainfile(filepath=str(root/'work/donor.blend'))
for o in bpy.data.objects:
 if o.type=='MESH' and (o.name=='wheel_lf.child' or 'steer' in o.name):
  print('DONOR',o.name,len(o.data.vertices),[tuple(round(c,3) for c in x) for x in o.bound_box],[(m.name, getattr(m.shader_properties,'filename','')) for m in o.data.materials])
for m in bpy.data.materials:
 print('MAT',m.name,m.shader_properties.filename)
 if 'mirror' in m.name.lower():print('MIRROR',m.name,m.shader_properties.filename)
bpy.ops.wm.open_mainfile(filepath=str(root/'jeepmilitar.blend'))
o=bpy.data.objects['bodyshell'];m=o.data
adj={v.index:set() for v in m.vertices}
for e in m.edges:
 a,b=e.vertices;adj[a].add(b);adj[b].add(a)
seen=set()
for v in m.vertices:
 if v.index in seen:continue
 stack=[v.index];seen.add(v.index);ids=[]
 while stack:
  i=stack.pop();ids.append(i)
  for j in adj[i]-seen:seen.add(j);stack.append(j)
 if len(ids)>5:
  coords=[m.vertices[i].co for i in ids]
  print('PART',len(ids),[tuple(round(f(c[k] for c in coords),3) for k in range(3)) for f in [min,max]])
from mathutils import Vector
for ob in bpy.data.objects:
 if ob.type=='MESH' and ob!=o:ob.hide_render=True
sc=bpy.context.scene
d=bpy.data.cameras.new('inspect');cam=bpy.data.objects.new('inspect',d);sc.collection.objects.link(cam)
cam.location=(-3,-3,2.7);target=Vector((-.35,.2,.65));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=1.6;sc.camera=cam
ld=bpy.data.lights.new('light','AREA');lo=bpy.data.objects.new('light',ld);sc.collection.objects.link(lo);lo.location=(-2,-1,4);ld.energy=500;ld.size=3
sc.render.engine='CYCLES';sc.cycles.samples=16;sc.render.resolution_x=900;sc.render.resolution_y=900;sc.render.resolution_percentage=100;sc.render.filepath=str(root/'work/jeep_detail.png');bpy.ops.render.render(write_still=True)
