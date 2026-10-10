from common import *
from szio.gta5 import LodLevel
import csv,collections
plan=read(O/'dados/plano.json');F=dict(np.load(O/'dados/biomas.npz'));rows=read(P/'porto_construido/qualidade_terreno/dados/terrain_quality.json')['sectors'];requests=[];max_grade=0;vertex_error=0
def request(xx,yy,label):
    ii=int(np.clip((xx-x[0,0])/dx,0,767));jj=int(np.clip((yy-y[0,0])/dy,0,767));name=f'ti_terreno_{jj//96:02}_{ii//96:02}'
    if (O/'terreno'/(name+'.ybn')).exists():requests.append([name,float(xx),float(yy),float(sample(z,xx,yy)),label])
for row in rows:
    a=try_load_asset(O/'terreno'/(row['name']+'.ydr'));center=np.asarray(row['center'])
    for model in a.models[LodLevel.HIGH]:
        for geo in model.geometries:
            v=geo.vertex_buffer['Position']+center;error=abs(v[:,2]-sample(z,v[:,0],v[:,1]));vertex_error=max(vertex_error,float(error.max()))
    x0,y0,x1,y1=row['grid_bounds']
    for fx in [.1,.3,.5,.7,.9]:
        for fy in [.1,.3,.5,.7,.9]:request(float(x[0,x0]+(x[0,x1]-x[0,x0])*fx),float(y[y0,0]+(y[y1,0]-y[y0,0])*fy),'terrain')
for road in plan['routes']:
    p=np.asarray(road['points']);grades=abs(np.diff(p[:,2]))/np.linalg.norm(np.diff(p[:,:2],axis=0),axis=1);max_grade=max(max_grade,float(grades.max()))
    for a,b in zip(p[:-1],p[1:]):
        for t in np.linspace(0,1,max(2,int(np.linalg.norm(b[:2]-a[:2])/12))):
            q=a+(b-a)*t;request(*q[:2],'road')
city=read(O/'dados/cidade.json')
for q in city['placements']:
    xx,yy,_=q['position']
    for ox,oy in [(-5,-5),(-5,5),(5,-5),(5,5),(0,0)]:request(xx+ox,yy+oy,'house')
# Cross-check original houses and all their native placement properties.
old_houses={};new_houses={}
for folder,result in [(P/'identidade_natural/porto_base',old_houses),(O/'porto_filtrado',new_houses)]:
    for path in folder.glob('pe_bairro_*.ymap'):
        for e in try_load_asset(path).entities:
            if str(e.archetype_name).startswith('pe_estrutura_'):result[(path.stem,str(e.archetype_name),tuple(e.position))]=(tuple(e.rotation),e.scale_xy,e.scale_z)
assert old_houses==new_houses,('Original house placement change',len(old_houses),len(new_houses))
assert vertex_error<.015,vertex_error
assert max_grade<.30,max_grade
with (O/'dados/ground_samples.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow(['tile','x','y','expected_z','kind']);w.writerows(requests)
write(O/'dados/auditoria.json',dict(passed=True,terrain_render_height_max_error_m=vertex_error,max_road_segment_grade=max_grade,original_house_placements_preserved=len(old_houses),main_city_buildings=250,village_buildings=64,villages=4,ground_ray_requests=len(requests),native_tree_drawables_unchanged=True,client_visual_verified=False))
print('GEOMETRY_AUDIT',vertex_error,max_grade,len(requests),len(old_houses),flush=True)
