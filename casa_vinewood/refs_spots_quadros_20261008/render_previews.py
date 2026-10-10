"""Blender visual QA only; native FiveM lighting is kept unchanged."""
import bpy,json,math,sys
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parent;W=P.parent
bpy.ops.wm.open_mainfile(filepath=str(W/'mansao_spots_quadros.blend'));s=bpy.context.scene
product_only='--product-only' in sys.argv
# Preview roughness is independent of the exported native shader parameters.
for m in bpy.data.materials:
    if not m.use_nodes or not m.get('ref_style'):continue
    for node in m.node_tree.nodes:
        if node.type=='BSDF_PRINCIPLED':
            for link in list(node.inputs['Roughness'].links):m.node_tree.links.remove(link)
            node.inputs['Roughness'].default_value=.28 if m['ref_style'] in ['reflector','prism','inlay'] else .75
s.render.engine='CYCLES';s.cycles.samples=16;s.cycles.use_denoising=True
s.render.resolution_x=1100;s.render.resolution_y=850;s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG';s.view_settings.view_transform='AgX'
s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.04
preview=bpy.data.collections.new('95_PREVIAS_REFERENCIAS');s.collection.children.link(preview);preview['preview_only']=True
for o in list(bpy.data.objects):
    if o.type=='CAMERA':bpy.data.objects.remove(o,do_unlink=True)
camera_data=bpy.data.cameras.new('Camera detalhes referencia');cam=bpy.data.objects.new(camera_data.name,camera_data);preview.objects.link(cam);s.camera=cam;cam.data.clip_start=.002
def view(position,target,lens):
    cam.location=position;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens
def area(name,position,target,power,size):
    light=bpy.data.lights.new(name,'AREA');light.energy=power;light.shape='DISK';light.size=size
    obj=bpy.data.objects.new(name,light);preview.objects.link(obj);obj.location=position
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler();return obj
def render(name):
    s.render.filepath=str(P/(name+'.png'));bpy.ops.render.render(write_still=True);print('PREVIEW_SAVED',name,flush=True)
areas=[]
for name,pos,target,energy,size in [
    ('Previa escritorio',(-4.5,4,2.0),(-4.65,2.461,.95),160,2),
    ('Previa jogos',(8,5.7,2),(5.82,5.6,.95),180,2),
    ('Previa hall',(10,-.2,2),(10,2.24,.9),230,2.5)]:areas.append(area(name,pos,target,energy,size))
if not product_only:
    view((10,.60,1.05),(10,2.239,.95),23);render('previa_quadros_hall')
    view((-4.55,5.7,1.10),(-4.65,2.461,.95),48);render('previa_quadro_escritorio')
    view((9.4,5.8,1.1),(5.82,5.6,.95),48);render('previa_quadro_jogos')
for obj in areas:obj.hide_render=True
# Keep an immediately useful room camera and all authored models editable.
view((10,.60,1.05),(10,2.239,.95),23)
bpy.ops.wm.save_as_mainfile(filepath=str(W/'mansao_spots_quadros.blend'),compress=True)

# Isolate one REAL installed fixture and its REAL ceiling recess for close QA.
for c in bpy.data.collections:
    if c!=preview:c.hide_render=True
local=bpy.data.collections.new('Produto spot em corte real');s.collection.children.link(local)
cfg=json.loads((P/'modeling_report.json').read_text());row=next(r for r in cfg['spots'] if r['ceiling_object'].startswith('Laje'))
x,y,z=row['position'];parent=bpy.data.objects['Spot referencia '+str(row['id'])]
for obj in parent.children:
    clone=obj.copy();clone.data=obj.data.copy();local.objects.link(clone);clone.parent=None;clone.location=(0,0,0);clone.rotation_euler=(0,0,0)
ceiling=bpy.data.objects[row['ceiling_object']]
# Crop ceiling triangles around the selected fixture without altering the source.
ceiling.data.calc_loop_triangles();verts=[];faces=[]
for tri in ceiling.data.loop_triangles:
    points=[ceiling.matrix_world@ceiling.data.vertices[i].co for i in tri.vertices]
    # Include the true cavity walls/back and local underside. Large underside
    # triangles retain their original endpoints outside the photographic view.
    centroid=sum(points,Vector())/3
    inside=all(abs(v.x-x)<.22 and abs(v.y-y)<.22 and z-.002<=v.z<=z+.052 for v in points)
    if inside:
        start=len(verts);verts.extend((v.x-x,v.y-y,v.z-z) for v in points);faces.append((start,start+1,start+2))
mesh=bpy.data.meshes.new('Cavidade real recortada');mesh.from_pydata(verts,[],faces);mesh.update()
obj=bpy.data.objects.new(mesh.name,mesh);local.objects.link(obj)
mat=bpy.data.materials.new('Acabamento teto da previa');mat.use_nodes=True;mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.84,.82,.77,1);mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.7;mesh.materials.append(mat)
area('Previa detalhe spot',(.15,-.25,-.28),(0,0,.02),3,.3)
area('Previa reflexo spot',(-.18,.06,-.18),(0,0,.02),2,.2)
s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.12
view((.10,-.18,-.22),(0,0,.005),55);render('previa_spot_embutido')
print('BLENDER_VISUAL_QA_READY',flush=True)
