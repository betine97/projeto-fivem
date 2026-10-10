import bpy,json
from pathlib import Path
OUT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(OUT/'castelo_rockford.blend'))
col=bpy.data.collections['00_IMPLANTACAO'];mat=bpy.data.materials['Cantaria esculpida / marfim']
def cube(name,loc,size):
 x,y,z=[a/2 for a in size];v=[(-x,-y,-z),(x,-y,-z),(x,y,-z),(-x,y,-z),(-x,-y,z),(x,-y,z),(x,y,z),(-x,y,z)]
 d=bpy.data.meshes.new(name);d.from_pydata(v,[],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(3,7,6,2),(0,4,7,3),(1,2,6,5)]);d.update();o=bpy.data.objects.new(name,d);col.objects.link(o);o.location=loc;o.data.materials.append(mat)
if 'Patamar chegada porta principal' not in bpy.data.objects:
 cube('Patamar chegada porta principal',(0,-10.35,.35),(8,.9,.7))
 for i in range(4):
  h=.7-i*.175;cube('Escada acesso funcionarios fundos',(0,10.16+i*.32,h/2),(3.4,.32,h))
s=bpy.context.scene;s.camera=bpy.data.objects['CAM Fachada'];s.render.resolution_x=1400;s.render.resolution_y=1050
for o in bpy.data.objects:
 if o.type=='FONT':o.hide_set(True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'castelo_rockford.blend'))
s.render.filepath=str(OUT/'castelo_exterior.png');bpy.ops.render.render(write_still=True)
data=json.loads((OUT/'projeto_medidas.json').read_text(encoding='utf-8'))
data['objects']=len(bpy.data.objects);data['mesh_objects']=sum(o.type=='MESH' for o in bpy.data.objects);data['triangles']=0
for o in bpy.data.objects:
 if o.type=='MESH':o.data.calc_loop_triangles();data['triangles']+=len(o.data.loop_triangles)
data['entrance_landings_connected']=True;data['rear_staff_entry_steps']=4
(OUT/'projeto_medidas.json').write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8')
print('FINAL_MODEL_SAVED',flush=True)
