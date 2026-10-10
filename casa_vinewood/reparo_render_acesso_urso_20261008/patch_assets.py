"""Close the native cuts, remove one palm at HD/LOD, and repair rug bounds."""
import sys,json,copy,hashlib,collections
from pathlib import Path
P=Path(__file__).resolve().parent;W=P.parent;R=W.parent;B=P/'baseline/stream';O=P/'stream';F=W/'fachada_garagem_20261008'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(W/'work/pydeps'),str(R/'laboratorio_fivem/work'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from szio.gta5 import *
from szio.gta5.bounds import *
from szio.types import Vector
import pymateria.gta5.gen8 as g8
from shapely.geometry import Polygon,LineString
from shapely.ops import unary_union,triangulate
spec=json.loads((P/'spec.json').read_text());origin=np.array(spec['origin']);target=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
report={'native_render':[],'native_collision':[],'occlusion':[],'palm':[],'rug':{}}
source=(F/'patch_site.py').read_text().split('entities=json.loads')[0]
env={'__file__':str(F/'patch_site.py')};exec(compile(source,str(F/'patch_site.py'),'exec'),env)
env['O']=O;env['source']=lambda name:B/name;env['report']={'render':[],'occlusion':[]}
axis=[(np.array(a),np.array(b)) for a,b in spec['earth_cuts'][:3]]
axis.append((np.array([3.30,11.65,-.74]),np.array([6.26,15.50,1.65])))
env['cuts']=axis

def clip(poly,boxes=None):
 pieces=[np.asarray(poly,dtype=float)];hit=False
 for lo,hi in (axis if boxes is None else boxes):
  skew=.173 if lo[1]>9.5 and hi[1]>16 else 0
  planes=[([-1,0,0],-lo[0]),([1,0,0],hi[0]),([0,-1,0],-lo[1]),([-skew,1,0],16.255 if skew else hi[1]),([0,0,-1],-lo[2]),([0,0,1],hi[2])]
  result=[]
  for part in pieces:
   remaining=list(part);out=[];h=True
   for normal,limit in planes:
    inside=[];outside=[];normal=np.array(normal)
    for v,w in zip(remaining,remaining[1:]+remaining[:1]):
     dv=np.dot(normal,v[:3])-limit;dw=np.dot(normal,w[:3])-limit;iv=dv<=1e-7;iw=dw<=1e-7
     (inside if iv else outside).append(v)
     if iv!=iw:q=v+(w-v)*(dv/(dv-dw));inside.append(q);outside.append(q)
    if len(outside)>=3:out.append(outside)
    remaining=inside
    if len(remaining)<3:out=[list(part)];h=False;break
   hit|=h;result.extend(np.array(q) for q in out)
  pieces=result
 return pieces,hit
env['clip']=clip
rows=json.loads((W/'work/near_house_entities.json').read_text())
for name in ['ch2_09b_hs05','ch2_09b_hs05_details','ch2_09b_l2']:
 row=next(e for e in rows if e['name']==name);env['drawable'](name,np.array(row['pos'])-origin,axis)
 if (O/(name+'.ydr')).exists():
  old=g8.Drawable.import_rsc(B/(name+'.ydr')).result;new=g8.Drawable.import_rsc(O/(name+'.ydr')).result
  new.lights=old.lights;g8.Drawable.export_rsc(new,O/(name+'.ydr'))
report['native_render']=env['report']['render']
for f in B.glob('*ch2_09b_[0-3].ybn'):
 a=try_load_asset(f);count=env['cut_bound'](a,-origin,axis)
 if count:save_asset(a,target,O,f.stem);report['native_collision'].append({'file':f.name,'primitives_cut':count})
occl=(F/'patch_site.py').read_text().split('# Native occlusion planes')[1].split("(P/'site_patch_report.json')")[0]
exec(compile('# Native occlusion planes'+occl,str(F/'patch_site.py'),'exec'),env)
report['occlusion']=env['report']['occlusion']

# Remove the single palm and its unique LOD entity. Keep all remaining child
# links pointing to the same parent objects after the index shifts by one.
parent=try_load_asset(B/'ch2_roads.ymap')
victims=[i for i,e in enumerate(parent.entities) if str(e.archetype_name)=='ch2_props_combo0126_11_lod' and np.linalg.norm((np.array(e.position)-origin)[:2]-[14.03,15.90])<.02]
assert len(victims)==1;victim=victims[0];removed_hd=0
for f in B.glob('ch2_roads*.ymap'):
 a=try_load_asset(f)
 if a.parent_name!='ch2_roads':continue
 keep=[];removed=[];changed=0
 for i,e in enumerate(a.entities):
  if e.parent_index==victim:
   assert str(e.archetype_name)=='prop_palm_sm_01d' and e.num_children==0 and np.linalg.norm((np.array(e.position)-origin)[:2]-[14.03,15.90])<.02
   removed.append({'index':i,'model':str(e.archetype_name),'position':list(e.position)});removed_hd+=1;continue
  if e.parent_index>victim:e.parent_index-=1;changed+=1
  keep.append(e)
 if removed or changed:
  a.entities=keep;save_asset(a,target,O,f.stem);report['palm'].append({'file':f.name,'removed':removed,'parent_links_reindexed':changed})
assert removed_hd==1
parent.entities=[e for i,e in enumerate(parent.entities) if i!=victim]
save_asset(parent,target,O,'ch2_roads');report['palm'].append({'file':'ch2_roads.ymap','removed_lod_index':victim})

# The head collider alone gives a misleadingly small physical envelope. Give
# the flat hide its real silhouette and a 9 mm walkable thickness, preserving
# the sculpted head collider and every visual vertex/texture/UV unchanged.
f=B/'mansao_tapete_urso.ydr';a=try_load_asset(f);oldraw=g8.Drawable.import_rsc(f).result
points=np.concatenate([g.vertex_buffer['Position'] for ms in a.models.values() for m in ms for g in m.geometries]);lo=points.min(0);hi=points.max(0)
bottom=[]
for m in a.models[LodLevel.HIGH]:
 for g in m.geometries:
  ts=g.vertex_buffer['Position'][g.index_buffer.reshape(-1,3)]
  keep=np.all(abs(ts[:,:,2]-.003)<1e-5,axis=1)
  bottom.extend(Polygon(t[:,:2]) for t in ts[keep] if Polygon(t[:,:2]).area>1e-10)
footprint=unary_union(bottom);assert footprint.geom_type=='Polygon' and footprint.is_valid
outline=footprint.simplify(.003,preserve_topology=True);assert abs(outline.area-footprint.area)<.015
xy=np.array(outline.exterior.coords[:-1]);v=[];faces=[];lookup={tuple(q):i for i,q in enumerate(xy)};n=len(xy)
v.extend([x,y,z] for z in [.003,.012] for x,y in xy)
for t in triangulate(outline):
 if not outline.covers(t.representative_point()):continue
 ids=[lookup[tuple(q)] for q in t.exterior.coords[:-1]]
 faces.extend([tuple(reversed(ids)),tuple(i+n for i in ids)])
for i in range(n):j=(i+1)%n;faces.extend([(i,j,j+n),(i,j+n,i+n)])
flat=copy.deepcopy(a.bounds.children[0]);flat.geometry_vertices=[BoundVertex(Vector(p),None) for p in v]
material=flat.geometry_primitives[0].material;flat.geometry_primitives=[BoundPrimitive.new_triangle(*t,material) for t in faces]
def bounds(b,low,high):
 b.bb_min=Vector(low);b.bb_max=Vector(high);b.centroid=Vector((low+high)/2);b.cg=b.centroid;b.radius_around_centroid=float(np.linalg.norm(high-low)/2)
bounds(flat,np.min(v,0),np.max(v,0));a.bounds.children.append(flat)
bounds(a.bounds,np.minimum(lo,np.min(v,0)),np.maximum(hi,np.max(v,0)))
save_asset(a,target,O,'mansao_tapete_urso')
newraw=g8.Drawable.import_rsc(O/'mansao_tapete_urso.ydr').result
for s,old in zip(newraw.shader_group.shaders,oldraw.shader_group.shaders):s.basis_shader=old.basis_shader;s.basis_material=old.basis_material
newraw.lights=oldraw.lights;g8.Drawable.export_rsc(newraw,O/'mansao_tapete_urso.ydr')
typ=try_load_asset(B/'mansao_piano_tapetes.ytyp');t=next(t for t in typ.archetypes if t.name=='mansao_tapete_urso')
low=lo-.015;high=hi+.015;t.bb_min=Vector(low);t.bb_max=Vector(high);t.bs_center=Vector((low+high)/2);t.bs_radius=float(np.linalg.norm(high-low)/2);t.lod_dist=220.;t.hd_texture_dist=220.
save_asset(typ,target,O,'mansao_piano_tapetes')
catalog=json.loads((P/'baseline/objetos_catalogo.json').read_text());entry=next(d for d in catalog['objects'] if d['model']=='mansao_tapete_urso')
entry['stableRender']=True;entry['lod']=220.;entry['lo']=low.tolist();entry['hi']=high.tolist()
(P/'objetos_catalogo.json').write_text(json.dumps(catalog,indent=2,ensure_ascii=False),encoding='utf-8')
code=(P/'baseline/objetos_client.lua').read_text()
at='SetEntityLodDist(e,math.floor(math.max(120,d.lod or 120))); setPose(id,t); collision(id)'
assert code.count(at)==1
code=code.replace(at,at+"\n                                if d.stableRender then SetEntityAlwaysPrerender(e,true) end")
at="RegisterCommand('objetosdebug',function()"
debug="""-- Targeted rendering diagnostics; no per-frame logs and no world-wide changes.
RegisterCommand('tapeteursodebug',function()
    for id,d in pairs(definitions) do
        if d.model=='mansao_tapete_urso' then
            local e=entities[id]; local exists=e and DoesEntityExist(e)
            local info={id=id,loaded=HasModelLoaded(hash(d)),entity=exists and e or 0,pose=poses[id],stableRender=d.stableRender==true}
            if exists then
                info.distance=M.distance(array(GetEntityCoords(PlayerPedId())),M.center(d,poses[id]))
                info.visible=IsEntityVisible(e);info.onScreen=IsEntityOnScreen(e);info.occluded=IsEntityOccluded(e);info.alpha=GetEntityAlpha(e)
                local lo,hi=GetModelDimensions(hash(d));info.modelLo=array(lo);info.modelHi=array(hi)
            end
            print('[TAPETE_URSO] '..json.encode(info))
        end
    end
end,false)
"""
assert code.count(at)==1;code=code.replace(at,debug+at)
(P/'objetos_client.lua').write_text(code,encoding='utf-8')
report['rug']={'visual_bounds':[lo.tolist(),hi.tolist()],'physical_bounds_before':[list(try_load_asset(f).bounds.bb_min),list(try_load_asset(f).bounds.bb_max)],'silhouette_area':float(outline.area),'flat_collider_triangles':len(faces),'flat_collider_height':.012,'targeted_prerender':True,'distance':220,'visual_mesh_and_materials_unchanged':True}
(P/'patch_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('RENDER_REPAIR_READY',report['palm'],report['rug'],flush=True)
