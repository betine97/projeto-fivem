import bpy,sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(W/'work/pydeps')]
from shapely.geometry import Polygon,box
from shapely import constrained_delaunay_triangles
bpy.ops.wm.open_mainfile(filepath=str(W/'mansao_encaixada.blend'))
col=next(c for c in bpy.data.collections if c.name.startswith('04_'));col.hide_viewport=False
mat=bpy.data.materials['Escada | madeira'];spec=json.loads((W/'encaixe_fachada.json').read_text())
def prism(name,p,top,depth):
 vs=[];fs=[]
 for t in constrained_delaunay_triangles(p).geoms:
  coords=list(t.exterior.coords)[:-1]
  a,b,c=coords
  if (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])<0:coords.reverse()
  i=len(vs);vs.extend((x,y,top) for x,y in coords);fs.append((i,i+1,i+2))
  i=len(vs);vs.extend((x,y,top-depth) for x,y in reversed(coords));fs.append((i,i+1,i+2))
 for ring in [p.exterior,*p.interiors]:
  coords=list(ring.coords)
  for a,b in zip(coords,coords[1:]):
   i=len(vs);vs.extend([(a[0],a[1],top-depth),(b[0],b[1],top-depth),(b[0],b[1],top),(a[0],a[1],top)]);fs.append((i,i+1,i+2,i+3))
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.materials.append(mat);me.update();o=bpy.data.objects.new(name,me);col.objects.link(o)
for o in list(col.objects):
 if o.name.startswith(('Piso terreo contorno','Laje superior contorno','Piso continuo Portao')):bpy.data.objects.remove(o,do_unlink=True)
g=Polygon(spec['ground_polygon']).buffer(-.025,join_style=2)
u=Polygon(spec['upper_polygon']).buffer(-.025,join_style=2).difference(box(-9.30,-13.3,6.40,-3.85)).difference(box(-.30,1.65,2.50,5.70))
prism('Piso terreo contorno nativo',g,-.8,.25);prism('Laje superior contorno nativo',u,2.808,.25)
# Continuous threshold across the removed gate's narrow collision cut.
prism('Piso continuo Portao da rua',box(1.10,7.05,3.61,7.59),-.8,.25)
bpy.context.scene['status']='Pisos triangulados com restricoes; acesso do portao e limpezas nativas em fivem. Teste no jogo pendente.'
bpy.ops.wm.save_as_mainfile(filepath=str(W/'mansao_encaixada.blend'))
print('FLOORS_REPAIRED_WITH_CONSTRAINED_TRIANGULATION',flush=True)
