import bpy,sys,json,math,re
from pathlib import Path
from mathutils import Matrix,Vector
P=Path(__file__).resolve().parent;R=P.parents[1]
sys.path[:0]=[str(R/'casa_vinewood/work/pydeps'),str(R/'laboratorio_fivem/work/pydeps')]
from shapely.geometry import shape,Point,box
from shapely import constrained_delaunay_triangles
import numpy as np
source=R/'castelo_rockford/evolucao_interiores_20261008/castelo_rockford_evoluido.blend'
bpy.ops.wm.open_mainfile(filepath=str(source));s=bpy.context.scene
plan=json.loads((P/'implantacao.json').read_text());anchor=np.array(plan['anchor']);angle=math.radians(plan['rotation'])
rot=np.array([[math.cos(angle),-math.sin(angle)],[math.sin(angle),math.cos(angle)]])
def local(x,y,z):return (*( (np.array([x,y])-anchor[:2])@rot ),z-anchor[2])
remove_prefix=('SUITE ','Equipe E ','Equipe D ','Armario despensa','Banheiro bancada','Cozinha bancada','Ilha cozinha','Tampo ilha','Mesa banquete','Pe mesa banquete','Cadeira banquete','Vaso centro banquete','Bandeja centro banquete','Arranjo mesa','Base microfone','Bloco reuniao','Capsula microfone','Copo agua','Haste microfone','Tela reuniao','Palco modular','Almofada porta','Macaneta bronze','Fonte ','Vaso exterior','Topiaria','Patio de chegada','Via esquerda /','Acesso traseiro /','Visitantes direita','Vaga visitante','Sentido escolta','Visitante','Escolta /','Carro garagem','Pessoa 1,80m')
removed=[]
oldanchor=Vector((-946,207,66.47));newanchor=Vector(anchor);oldrot=Matrix.Rotation(math.radians(60),4,'Z');newrot=Matrix.Rotation(angle,4,'Z')
retainworld=Matrix.Translation(-newanchor)@newrot.inverted()@Matrix.Translation(oldanchor)@oldrot
garage=[]
for o in list(bpy.data.objects):
 if o.type=='MESH' and (o.name.startswith(remove_prefix) or 'porta aberta' in o.name):
  removed.append(o.name);bpy.data.objects.remove(o,do_unlink=True);continue
 if o.type=='MESH' and (o.name.startswith(('Garagem','Piso garagem','Quadra original','Linha perimetro quadra','Rede quadra referencia','Envelope medido'))):
  o.matrix_world=retainworld@o.matrix_world
  if o.name.startswith(('Garagem','Piso garagem')):garage.append(o.name)
road=shape(plan['road']);apron=shape(plan['apron']);affected=shape(plan['affected']);foot=shape(plan['footprint']);approach=shape(plan['approach'])
gradegate=plan['grade_gate'];length=plan['ramp_length_m'];z0=plan['gate_height']+.03
def height(x,y):
 t=max(0,min(1,approach.project(Point(x,y))/length));return z0+(66.5-z0)*t
C=bpy.data.collections['00_IMPLANTACAO']
asphalt=bpy.data.materials['Acesso veicular fosco'];paving=bpy.data.materials['Pavers acesso'];trim=bpy.data.materials['Cantaria esculpida / marfim']
# Fine aggregate and paver relief are authored in metres and baked for GTA.
for m,scale,lo,hi in [(asphalt,95,(.075,.08,.085,1),(.13,.14,.15,1)),(paving,5,(.32,.28,.21,1),(.42,.36,.27,1))]:
 nt=m.node_tree;n=nt.nodes;l=nt.links;p=n.get('Principled BSDF');tex=n.new('ShaderNodeTexCoord');noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=scale;noise.inputs['Detail'].default_value=2
 l.new(tex.outputs['UV'],noise.inputs['Vector']);ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=lo;ramp.color_ramp.elements[1].color=hi;l.new(noise.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs['Color'],p.inputs['Base Color'])
 bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.12;bump.inputs['Distance'].default_value=.006;l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],p.inputs['Normal'])
def mesh(name,verts,faces,mat):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);C.objects.link(o);me.materials.append(mat);uv=me.uv_layers.new(name='UVMap')
 for loop in me.loops:
  v=me.vertices[loop.vertex_index].co;uv.data[loop.index].uv=(v.x,v.y)
 return o
def surface(name,poly,mat,offset=0):
 vs=[];fs=[]
 # A regular tessellation retains the smooth, measured slope at the entrance.
 for x in np.arange(math.floor(poly.bounds[0]),poly.bounds[2],1.25):
  for y in np.arange(math.floor(poly.bounds[1]),poly.bounds[3],1.25):
   cell=poly.intersection(box(x,y,x+1.25,y+1.25))
   if cell.is_empty or cell.area<1e-7:continue
   for tri in constrained_delaunay_triangles(cell).geoms:
    pp=list(tri.exterior.coords)[:3];k=len(vs)
    if np.cross(np.array(pp[1])-pp[0],np.array(pp[2])-pp[0])<0:pp=pp[::-1]
    vs.extend(local(px,py,height(px,py)+offset) for px,py in pp);fs.append((k,k+1,k+2))
 return mesh(name,vs,fs,mat)
surface('Terreno base integrado / suporte',affected,paving,-.04)
surface('Trajeto veicular / pista continua 5m',road,asphalt,0)
surface('Passeio de contorno / acesso pedestres',apron.difference(road),paving,.04)
# Low continuous stone edge, with no step at the vehicle entrance.
outer=road.buffer(.12).difference(road)
outer=outer.difference(Point(*gradegate).buffer(3.3))
surface('Guia baixa trajeto / cantaria',outer,trim,.045)
# Close the sides of the raised platform against the measured original terrain.
# This creates retaining faces rather than leaving a floating pavement edge.
td=np.load(P/'terreno.npz');gt=td['triangles'][np.isin(td['shaders'],[4,6,7,9,19])]
def soil(x,y):
 a=gt[:,0,:2];e=gt[:,1,:2]-a;f=gt[:,2,:2]-a;v=np.array([x,y])-a;det=e[:,0]*f[:,1]-e[:,1]*f[:,0];ok=abs(det)>1e-8;u=np.zeros(len(a));w=u.copy();u[ok]=(v[ok,0]*f[ok,1]-v[ok,1]*f[ok,0])/det[ok];w[ok]=(e[ok,0]*v[ok,1]-e[ok,1]*v[ok,0])/det[ok];valid=ok&(u>=-1e-5)&(w>=-1e-5)&(u+w<=1.00001);zz=gt[:,0,2]+u*(gt[:,1,2]-gt[:,0,2])+w*(gt[:,2,2]-gt[:,0,2]);return float(max(zz[valid])) if valid.any() else height(x,y)-.6
vv=[];ff=[]
for part in affected.geoms if hasattr(affected,'geoms') else [affected]:
 for ring in [part.exterior]+list(part.interiors):
  pp=list(ring.coords)
  for aa,bb in zip(pp,pp[1:]):
   aa=np.array(aa);bb=np.array(bb);length=float(np.linalg.norm(bb-aa));count=max(1,math.ceil(length/.6))
   for j in range(count):
    a=aa+(bb-aa)*j/count;b=aa+(bb-aa)*(j+1)/count;za=height(*a)-.04;zb=height(*b)-.04;ga=soil(*a);gb=soil(*b)
    if max(abs(za-ga),abs(zb-gb))<.09:continue
    k=len(vv);vv.extend([local(*a,min(za,ga)-.05),local(*b,min(zb,gb)-.05),local(*b,max(zb,gb)),local(*a,max(za,ga))]);ff.append((k,k+1,k+2,k+3))
mesh('Terreno base / contencao de borda',vv,ff,trim)
# Remove all door leaves, retain the structural lintels and window glazing.
assert not any('porta aberta' in o.name or o.name.startswith(('Almofada porta','Macaneta bronze')) for o in bpy.data.objects)
assert all(name not in bpy.data.objects for name in removed)
s['gta_anchor_xyz']=plan['anchor'];s['gta_rotation_z_degrees']=plan['rotation'];s['stage']='estrutura_sem_moveis_e_sem_portas'
out=P/'castelo_estrutura.blend';bpy.ops.wm.save_as_mainfile(filepath=str(out))
report={'source':str(source),'result':str(out),'removed_meshes':removed,'removed_count':len(removed),'retained_garage_meshes_world':garage,'only_furniture':'mesas e cadeiras de reuniao','anchor':plan['anchor'],'rotation':plan['rotation'],'road_width_m':5,'doors_removed':True}
(P/'alteracoes_blender.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
print('STRUCTURE_SAVED',len(removed),'removed meshes; garage location preserved; no door leaves',flush=True)
