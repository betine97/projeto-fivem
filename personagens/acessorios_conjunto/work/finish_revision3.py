import bpy,bmesh,sys,addon_utils
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
root=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(root/'CONJUNTO_COMPLETO.blend'))
# Only the calf above the ankle is hidden under trousers. Preserve the whole
# foot and the ankle through 7 cm above its native joint.
ankle=bpy.data.objects['PELE_TORNOZELOS_MOCASSINS'];bm=bmesh.new();bm.from_mesh(ankle.data)
bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=.000001,plane_co=(0,0,-.835),plane_no=(0,0,1),clear_outer=True,clear_inner=False);bm.to_mesh(ankle.data);bm.free()
foot=bpy.data.objects['PELE_PES_MOCASSINS'];shoes=bpy.data.objects['MOCASSINS_MARRONS']
if 'FORRO_MOCASSINS' in bpy.data.objects:bpy.data.objects.remove(bpy.data.objects['FORRO_MOCASSINS'],do_unlink=True)
lining=foot.copy();lining.data=foot.data.copy();bpy.context.scene.collection.objects.link(lining);lining.name='FORRO_MOCASSINS';lining.hide_render=False;lining.hide_set(False)
bm=bmesh.new();bm.from_mesh(lining.data)
# Leather below the loafer opening fills small holes in the generated shell.
# The original foot remains underneath this extra shoe layer.
remove=[f for f in bm.faces if f.calc_center_median().z>-.943 or f.calc_center_median().z<-.990]
bmesh.ops.delete(bm,geom=remove,context='FACES');bm.to_mesh(lining.data);bm.free()
for v in lining.data.vertices:
 center=.156 if v.co.x>0 else -.156
 direction=Vector((v.co.x-center,v.co.y-.025,(v.co.z+.979)*2)).normalized()
 v.co+=direction*.006
shoes.data.calc_loop_triangles();tris=[tuple(t.vertices) for t in shoes.data.loop_triangles];pts=[v.co.copy() for v in shoes.data.vertices];bvh=BVHTree.FromPolygons(pts,tris,all_triangles=True)
uv=lining.data.uv_layers[0];suv=shoes.data.uv_layers[0]
for poly in lining.data.polygons:
 for loopidx in poly.loop_indices:
  v=lining.data.vertices[lining.data.loops[loopidx].vertex_index];hit,n,i,d=bvh.find_nearest(v.co);t=shoes.data.loop_triangles[i];a,b,c=[pts[k] for k in t.vertices];ab=b-a;ac=c-a;ap=hit-a
  d00=ab.dot(ab);d01=ab.dot(ac);d11=ac.dot(ac);d20=ap.dot(ab);d21=ap.dot(ac);den=d00*d11-d01*d01
  u=(d11*d20-d01*d21)/den if abs(den)>1e-12 else 0;w=(d00*d21-d01*d20)/den if abs(den)>1e-12 else 0
  uv.data[loopidx].uv=sum((suv.data[l].uv*coef for l,coef in zip(t.loops,[1-u-w,u,w])),Vector((0,0)))
# The lining uses a plain brown area of the unchanged leather atlas. Avoid
# projected UV seams landing on the atlas background in these tiny patches.
image=next(n.image for n in shoes.data.materials[0].node_tree.nodes if n.type=='TEX_IMAGE' and n.image and n.image.colorspace_settings.name=='sRGB')
pixels=np.array(image.pixels[:],np.float32).reshape(image.size[1],image.size[0],4)
sample=pixels[4::8,4::8,:3];target=np.array([.25,.095,.045]);score=((sample-target)**2).sum(2);iy,ix=np.unravel_index(score.argmin(),score.shape)
fixed_uv=((ix*8+4.5)/image.size[0],(iy*8+4.5)/image.size[1])
for datum in lining.data.uv_layers[0].data:datum.uv=fixed_uv
lining.data.materials.clear()
for m in shoes.data.materials:lining.data.materials.append(m)
for p in lining.data.polygons:p.material_index=0
for filename in [root/'CONJUNTO_COMPLETO.blend',root.parent/'camisa_estampada/PERSONAGEM_COM_CAMISA.blend',root.parent/'calca_bege/PERSONAGEM_COM_CALCA_BEGE.blend']:
 bpy.ops.wm.save_as_mainfile(filepath=str(filename))
print('REVISION3_LINING_READY',len(lining.data.polygons),flush=True)
sc=bpy.context.scene;sc.cycles.samples=16;cam=sc.camera;cam.location=(2,-3,-.83);cam.rotation_euler=(Vector((0,-.025,-.91))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.46
sc.render.resolution_x=800;sc.render.resolution_y=600;sc.render.filepath=str(root/'pes_revisao3.png');bpy.ops.render.render(write_still=True)
