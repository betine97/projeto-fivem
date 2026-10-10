from pathlib import Path
import json,sys,math,copy,xml.etree.ElementTree as E
P=Path(__file__).resolve().parents[1];R=P.parent
sys.path.insert(0,str(R/'laboratorio_fivem/work/pydeps'))
import numpy as np
F=P/'fivem';(F/'data').mkdir(parents=True,exist_ok=True)
E.register_namespace('xi','http://www.w3.org/2001/XInclude')
root=E.fromstring((P/'referencia_tecnica/base_gta5.meta').read_text().replace('<CDataFileMgr__ContentsOfDataFileXml>','<CDataFileMgr__ContentsOfDataFileXml xmlns:xi="http://www.w3.org/2001/XInclude">'))
removed=[]
# Keep gameplay, weather and rendering definitions; exclude the original world.
worldtypes={'IPL_FILE','ZONEBIND_FILE','NAVMESH_INDEXREMAPPING_FILE','JUNCTION_TEMPLATES_FILE','JUNCTION_TEMPLATES_PSO_FILE','PATH_ZONES_FILE','TRAINTRACK_FILE','DISTANT_LIGHTS_FILE','DISTANT_LIGHTS_HD_FILE','SCENARIO_POINTS_PSO_FILE','SLOWNESS_ZONES_FILE','MAPZONES_FILE','WORLD_HEIGHTMAP_FILE','WORLD_WATERHEIGHT_FILE','STREET_VEHICLE_ASSOCIATION_FILE','VEHGEN_MARKUP_FILE'}
files=root.find('dataFiles')
for item in list(files):
 t=item.findtext('fileType');f=item.findtext('filename','');is_world=t in worldtypes or t=='PERMANENT_ITYP_FILE' and any(s in f.lower() for s in ['/_city','/_country','/destruction/','/interiors/'])
 if is_world:removed.append({'type':t,'file':f});files.remove(item)
images=E.fromstring((P/'referencia_tecnica/base_images.meta').read_text());removedimages=[]
for item in list(images):
 f=item.findtext('filename','')
 localworld='/levels/gta5/' in f.lower() and not any(v in f.lower() for v in ['/vehicles','/vehiclemods/','/props/','/generic/','/cloudhats/'])
 if localworld or item.findtext('contents')=='CONTENTS_MAP' and '/cloudhats/' not in f.lower():removedimages.append(f);images.remove(item)
for node in root.find('includedXmlFiles').iter():
 if node.tag.endswith('include') and node.get('href','').endswith('/images.meta'):node.set('href','resources:/teste_ilha/data/images.meta')
# This is loaded with the level, before any client Lua runs. The resource URI
# must match the mounted packfile, not an unregistered custom device name.
for item in files:
 if item.findtext('fileType')=='WATER_FILE':item.find('filename').text='resources:/teste_ilha/data/water.xml'
def save_xml(path,r):
 E.indent(r,space='  ')
 path.write_bytes(b'<?xml version="1.0" encoding="UTF-8"?>\r\n'+E.tostring(r,encoding='utf-8').replace(b'\n',b'\r\n'))
save_xml(F/'data/images.meta',images);save_xml(F/'ilha.meta',root)
# Ocean at sea level. River/lake cells are bounded, level native water patches
# clipped by the terrain, permitting swimming without solid water collision.
d=np.load(P/'dados/terreno.npz');pts=d['river_points'];heights=d['river_z'];widths=d['river_halfwidth'];g=d['terrain'];step=8
water=E.Element('WaterData');quads=E.SubElement(water,'WaterQuads');entries={}
def quad(bounds,z):
 x0,y0,x1,y1=bounds;it=E.SubElement(quads,'Item')
 values={'minX':int(x0),'maxX':int(x1),'minY':int(y0),'maxY':int(y1),'Type':0,'IsInvisible':'false','HasLimitedDepth':'false','z':round(float(z),3),'a1':26,'a2':26,'a3':26,'a4':26,'NoStencil':'false'}
 for k,v in values.items():E.SubElement(it,k,{'value':str(v)})
# Higher water is entered first, and the ocean last, avoiding a river lookup
# resolving to the base ocean rectangle before the local river water.
for i in range(len(pts)-1):
 a,b=pts[i],pts[i+1];delta=b-a
 lo=np.floor((np.minimum(a,b)-max(widths[i:i+2])-step)/step).astype(int);hi=np.ceil((np.maximum(a,b)+max(widths[i:i+2])+step)/step).astype(int)
 for ix in range(lo[0],hi[0]+1):
  for iy in range(lo[1],hi[1]+1):
   p=np.array([(ix+.5)*step,(iy+.5)*step]);t=float(np.clip((p-a)@delta/(delta@delta),0,1));dist=np.linalg.norm(p-a-t*delta);w=widths[i]+t*(widths[i+1]-widths[i])
   if dist<=w:
    h=float(heights[i]+t*(heights[i+1]-heights[i]));key=(ix,iy)
    if key not in entries or dist<entries[key][0]:entries[key]=(dist,h)
center=d['lakecenter'];radii=d['lake_radii'];h=float(d['lakeheight'])
for ix in range(math.floor((center[0]-radii[0])/step),math.ceil((center[0]+radii[0])/step)+1):
 for iy in range(math.floor((center[1]-radii[1])/step),math.ceil((center[1]+radii[1])/step)+1):
  p=np.array([(ix+.5)*step,(iy+.5)*step])
  if np.sum(((p-center)/radii)**2)<=1:entries[(ix,iy)]=(0,h)
# Coalesce neighboring X cells with equal water levels at each Y row. Water
# slopes are quantized to 25 cm, retaining a bounded number of native quads.
rows={}
for (ix,iy),(_,h) in entries.items():rows.setdefault(iy,[]).append((ix,round(h*4)/4))
for iy,cells in rows.items():
 cells.sort();a=last=cells[0][0];z=cells[0][1]
 for ix,h in cells[1:]+[(10**8,-1)]:
  if ix==last+1 and h==z:last=ix;continue
  quad([a*step,iy*step,(last+1)*step,(iy+1)*step],z);a=last=ix;z=h
quad([-8192,-8192,8192,8192],0)
E.SubElement(water,'CalmingQuads');E.SubElement(water,'WaveQuads');save_xml(F/'data/water.xml',water)
meta=json.loads((P/'dados/medidas.json').read_text());cx,cy=meta['runway']['center_m'];spawn={'x':cx,'y':cy,'z':19.15,'heading':90.0,'model':'a_m_y_business_01'}
cfg={'spawn':spawn,'sea_level':0,'limits':{'minX':-1450,'maxX':1450,'minY':-1700,'maxY':1700},'water_quads':len(quads),'revision':'ilha-20261009-isolamento-2'}
(F/'data/config.json').write_text(json.dumps(cfg,indent=2));(P/'nativo/mundo.json').write_text(json.dumps({'original_world_removed_files':removed,'original_world_removed_archives':removedimages,'water_quads':len(quads),'spawn':spawn},indent=2));print('ISLAND_WORLD_BUILT',len(removedimages),len(quads),flush=True)
