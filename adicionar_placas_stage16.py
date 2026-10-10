import bpy,math,json
from pathlib import Path
from mathutils import Vector
BASE=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(BASE/'warehouse_stage15_projeto_completo.blend'))
col=bpy.data.collections.new('PLACAS_Sinalizacao');bpy.context.scene.collection.children.link(col)
back=bpy.data.materials.new('PLACAS_Metal_Bordas');back.use_nodes=True
p=back.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.08,.045,.022,1);p.inputs['Metallic'].default_value=.65;p.inputs['Roughness'].default_value=.7
# Image bounds exclude the empty margins; original images remain unchanged.
specs=[('reservatorio',(-3.08,4.515,1.30),.70,(.004,.145,.995,.81)),
 ('emergencia',(.91,5.968,1.55),.42,(.035,.052,.962,.962)),
 ('acesso',(0,5.962,1.56),.64,(.025,.048,.975,.95)),
 ('ventilacao',(2.05,5.97,2.12),.68,(.03,.043,.97,.949)),
 ('alta_tensao',(-1.55,5.79,2.42),.57,(.03,.055,.97,.943))]
for name,pos,width,bounds in specs:
    img=bpy.data.images.load(str(BASE/'placas'/(name+'.png')));img.pack()
    u0,v0,u1,v1=bounds;height=width*(img.size[1]*(v1-v0))/(img.size[0]*(u1-u0))
    mat=bpy.data.materials.new('PLACA_'+name);mat.use_nodes=True;t=mat.node_tree;p=t.nodes.get('Principled BSDF')
    tex=t.nodes.new('ShaderNodeTexImage');tex.image=img;tex.extension='EXTEND'
    t.links.new(tex.outputs['Color'],p.inputs['Base Color']);p.inputs['Roughness'].default_value=.72;p.inputs['Metallic'].default_value=.15
    # A thin physical backing plus a correctly oriented printed face.
    bpy.ops.mesh.primitive_cube_add(size=1,location=pos);o=bpy.context.object;o.name='PLACA_'+name+'_CHAPA';o.dimensions=(width,.012,height)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    for c in list(o.users_collection):c.objects.unlink(o)
    col.objects.link(o);o.data.materials.append(back)
    bevel=o.modifiers.new('Cantos','BEVEL');bevel.width=.009;bevel.segments=3
    x,y,z=pos
    mesh=bpy.data.meshes.new(name+'_face');mesh.from_pydata([(x-width/2,y-.007,z-height/2),(x+width/2,y-.007,z-height/2),(x+width/2,y-.007,z+height/2),(x-width/2,y-.007,z+height/2)],[],[(0,1,2,3)])
    face=bpy.data.objects.new('PLACA_'+name+'_IMPRESSAO',mesh);col.objects.link(face);mesh.materials.append(mat)
    uv=mesh.uv_layers.new();coords=[(u0,v0),(u1,v0),(u1,v1),(u0,v1)]
    for li in mesh.polygons[0].loop_indices:uv.data[li].uv=coords[mesh.loops[li].vertex_index]
s=bpy.context.scene;s.render.filepath=str(BASE/'warehouse_stage16_projeto_completo.png');s.cycles.samples=80
bpy.ops.wm.save_as_mainfile(filepath=str(BASE/'warehouse_stage16_projeto_completo.blend'))
bpy.ops.render.render(write_still=True)
# Unobstructed close view of the rear signage, for review only.
for o in bpy.data.objects:
    if o.name.startswith(('RACK_','LIGHT_FIXTURE_','PLACEHOLDER_','CEILING_DUCT_','CEILING_VENT_','FLOOR_HOSE_')):o.hide_render=True
cam=s.camera;target=Vector((0,5.5,1.7));cam.location=(0,1,2.0);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=8.3
data=bpy.data.lights.new('REVIEW_PLACAS','AREA');data.energy=650;data.size=5
o=bpy.data.objects.new(data.name,data);s.collection.objects.link(o);o.location=(0,2.5,3);o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
s.render.resolution_x=1800;s.render.resolution_y=850;s.cycles.samples=64;s.render.filepath=str(BASE/'warehouse_stage16_placas_detalhe.png');bpy.ops.render.render(write_still=True)
print('STAGE16 OK 5 placas')
