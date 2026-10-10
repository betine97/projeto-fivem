exec((__import__('pathlib').Path(__file__).parent/'medir_cayo.py').read_text().split('game=')[0])
import re,numpy as np
from PIL import Image,ImageDraw
rows=[]
for f in N.glob('*terrain*.ymap'):
 if not re.fullmatch(r'h4_(?:islandx|mph4)_terrain_\d+\.ymap',f.name):continue
 a=try_load_asset(f)
 for e in a.entities:
  if re.fullmatch(r'h4_mph4_(?:ter(?:01|05)_\d+|ter02_terr_\d+[ab]?|ter02_airstrip_\d+|ter03_ext_\d+|ter04_mp4_ter04_\d+|ter06_(?:drive|trax_01|mnsn_furgrass\d+))',str(e.archetype_name)):rows.append(e)
index=json.loads((N/'indice_cayo.json').read_text());files={Path(q['file']).stem:q for q in index if q['file'].endswith('.ydr')};cache={};triangles=[];used=[]
for e in rows:
 name=str(e.archetype_name);q=files[name];parts=q['archive'].split('|');key=q['archive']
 if key not in cache:
  ar=open_rpf(parts[0])
  for part in parts[1:]:ar=ar.open_nested(part)
  cache[key]=ar
 f=N/(name+'.ydr');f.write_bytes(cache[key].read_bytes(q['file']));a=try_load_asset(f)
 w,x,y,z=e.rotation;rot=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
 for m in a.models[LodLevel.HIGH]:
  for g in m.geometries:
   v=(g.vertex_buffer['Position']*np.array([e.scale_xy,e.scale_xy,e.scale_z]))@rot.T+e.position;t=v[g.index_buffer.reshape(-1,3)];normal=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);triangles.extend(t[(normal[:,2]>1e-8)&(t[:,:,2].max(1)>0)])
 used.append(name)
t=np.asarray(triangles);step=2.;lo=t[:,:,:2].min((0,1));hi=t[:,:,:2].max((0,1));size=np.ceil((hi-lo)/step).astype(int)+3;im=Image.new('1',tuple(size));draw=ImageDraw.Draw(im)
for t in triangles:
 out=[]
 for a,b in zip(t,np.roll(t,-1,axis=0)):
  if a[2]>=0:out.append(a)
  if (a[2]>=0)!=(b[2]>=0):out.append(a+(b-a)*(-a[2])/(b[2]-a[2]))
 if len(out)>=3:draw.polygon([tuple((v[:2]-lo)/step) for v in out],fill=1)
area=int(np.asarray(im).sum())*step**2
im.transpose(Image.Transpose.FLIP_TOP_BOTTOM).convert('L').save(N/'mascara_cayo.png')
result={'reference':'Installed GTA V mpheist4 HIGH terrain meshes above sea level','reference_land_area_m2_estimate':area,'target_area_m2':area*3,'multiplier':3,'raster_resolution_m':step,'method':'Union raster of upward terrain triangles clipped at sea level z=0. Ground patches and artificial structures not included. Approximate footprint, not official Rockstar area.','source_models':used,'land_extent_m':(hi-lo).tolist()}
(N/'medicao_cayo.json').write_text(json.dumps(result,indent=2));print('CAYO_AREA',result,flush=True)
