import sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood'
exec((W/'work/audit_vegetation_visual.py').read_text().split("if __name__=='__main__':")[0])
from szio.rpf import open_rpf
entities=json.loads((W/'work/entities.json').read_text())+json.loads((W/'work/dlc_near_house_props.json').read_text())
plants=[e for e in entities if any(k in e['name'] for k in ['plant','bush','pot','tree']) and np.linalg.norm((np.array(e['pos'])-origin)[:2])<35 and -12<(np.array(e['pos'])-origin)[2]<12]
needed={e['name'] for e in plants};cache={};game=Path(r'C:/Program Files (x86)/Steam/steamapps/common/Grand Theft Auto V')
for line in (R/'laboratorio_fivem/work/assets_index.txt').read_text().splitlines():
 ps=line.split('|');name=Path(ps[-1]).stem
 if not ps[-1].endswith('.ydr') or name not in needed or (N/(name+'.ydr')).exists():continue
 key='|'.join(ps[:-1])
 if key not in cache:
  r=open_rpf(game/ps[0])
  for nested in ps[1:-1]:r=r.open_nested(nested)
  cache[key]=r
 (N/(name+'.ydr')).write_bytes(cache[key].read_bytes(ps[-1]))
report=[]
for e0 in plants:
 e=mapped(e0);ts=visual_points(e)
 if not len(ts):raise AssertionError('Missing visual '+e['name'])
 vs=np.array(ts).reshape(-1,3)
 if np.any(vs.max(0)<[-9.3,-16,-.81]) or np.any(vs.min(0)>[14.45,9.85,6.51]):area,count=0.,0
 else:area,count=intrusion_area(ts)
 row=dict(original=e0,installed=e,visual_lo=vs.min(0).tolist(),visual_hi=vs.max(0).tolist(),inside_area_m2=area,inside_triangles=count);report.append(row)
 if area>1e-5:print('INTRUSION',e['map'],e['name'],np.round(np.array(e['pos'])-origin,3).tolist(),'scale',e['scale'],'area',round(area,4),flush=True)
(W/'audit_vegetacao_todas_camadas.json').write_text(json.dumps({'instances':report,'intruding_instances':int(sum(r['inside_area_m2']>1e-5 for r in report))},indent=2))
print('PLANT_INSTANCES_AUDITED',len(report),flush=True)
