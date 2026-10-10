"""Derive client probes, revised native water and check authored walkable surfaces."""
from pathlib import Path
import sys,json,ast,copy,hashlib,xml.etree.ElementTree as ET
O=Path(__file__).resolve().parents[1];P=O.parent;R=P.parent
sys.path.insert(0,str(R/'laboratorio_fivem/work/pydeps'))
import numpy as np
def read(name):return json.loads((O/'dados'/name).read_text(encoding='utf8'))
report=read('pacote_nativo.json');port=read('porto.json');sectors=read('setores_alterados.json')
grid=np.load(O/'dados/terreno.npz')['terrain'];original=np.load(P/'dados/terreno.npz')['terrain']
checks=[]
def check(name,condition,**details):
    checks.append(dict(name=name,passed=bool(condition),**details))
    if not condition:raise AssertionError(name)
def heights(v,t,x,y):
    a=v[t];lo=a[:,:,:2].min(1);hi=a[:,:,:2].max(1)
    a=a[(lo[:,0]<=x)&(hi[:,0]>=x)&(lo[:,1]<=y)&(hi[:,1]>=y)]
    if not len(a):return []
    e=a[:,1,:2]-a[:,0,:2];f=a[:,2,:2]-a[:,0,:2];q=np.array([x,y])-a[:,0,:2]
    den=e[:,0]*f[:,1]-e[:,1]*f[:,0];ok=abs(den)>1e-8
    u=np.divide(q[:,0]*f[:,1]-q[:,1]*f[:,0],den,out=np.zeros(len(a)),where=ok)
    w=np.divide(e[:,0]*q[:,1]-e[:,1]*q[:,0],den,out=np.zeros(len(a)),where=ok)
    inside=ok&(u>=-1e-6)&(w>=-1e-6)&(u+w<=1+1e-6)
    z=a[:,0,2]+u*(a[:,1,2]-a[:,0,2])+w*(a[:,2,2]-a[:,0,2])
    return z[inside].tolist()
pc=[]
for row in port:
    c=np.load(O/'cache'/(row['name']+'.npz'));v=c['position'];pc.append((v,np.arange(len(v)).reshape(-1,3)))
def surface(x,y):
    z=[]
    for v,t in pc:z+=heights(v,t,x,y)
    return max(z) if z else None
def blocked(v,t,start,end):
    a=v[t];direction=np.array(end)-start;e1=a[:,1]-a[:,0];e2=a[:,2]-a[:,0];h=np.cross(direction,e2);det=(e1*h).sum(1);valid=abs(det)>1e-8
    inv=np.divide(1,det,out=np.zeros(len(a)),where=valid);s=np.array(start)-a[:,0];u=inv*(s*h).sum(1);q=np.cross(s,e1);w=inv*(direction*q).sum(1);distance=inv*(e2*q).sum(1)
    return bool(np.any(valid&(u>=0)&(w>=0)&(u+w<=1)&(distance>=0)&(distance<=1)))
points=[('praca',242,-738,4.83),('cais_pescadores',105,-855,4.4),('pier',60,-910,4.4),('cobertura_terminal',240,-785,None),('patio_cargas',530,-802,4.59),('ponte',-3.5,-681,None)]
probes=[]
for name,x,y,expected in points:
    hit=surface(x,y);check('piso_'+name,hit is not None and (expected is None or abs(hit-expected)<.03),height=hit,expected=expected)
    probes.append(dict(name=name,x=x,y=y,z=hit+1.15,expected=round(hit,3)))
# Shared sector edges come directly from the same grid and full resolution collision.
for row in sectors:
    c=np.load(O/'cache'/(row['name']+'_1.npz'));x0,y0,x1,y1=row['grid_bounds'];v=grid[y0:y1+1,x0:x1+1].reshape(-1,3)
    check('colisao_terreno_'+row['name'],np.array_equal(c['collision_vertices'],v) and c['collision_triangles'].max()<len(v))
runway=(grid[:,:,0]>-820)&(grid[:,:,0]<-60)&(grid[:,:,1]>-143)&(grid[:,:,1]<-36)
check('pista_preservada',np.array_equal(grid[runway],original[runway]))
houses=read('implantacao_casas.json');house_names={f'pe_estrutura_{i:02}' for i in range(1,11)}
check('dez_modelos_corretos_91_instancias',len(houses)==91 and {r['name'] for r in houses}==house_names)
for row in read('casas.json'):
    c=np.load(O/'cache'/(row['name']+'.npz'));floor=heights(c['collision_vertices'],c['collision_triangles'],0,0)
    check('piso_interior_'+row['name'],any(abs(h)<.01 for h in floor),heights=sorted(set(round(h,3) for h in floor)))
    supplied=[m for m in row['materials'] if m.get('texture')]
    check('texturas_usuario_'+row['name'],bool(supplied) and all(m['texture'] in next(s for s in report['models'] if s['name']==row['name'])['texture_names'] for m in supplied))
    info=json.loads((P/'estruturas_porto_20261009/dados'/(row['name'][-2:]+'_modelo.json')).read_text());width,depth=info['dimensoes'][:2]
    check('cobertura_solida_'+row['name'],any(h>info['dimensoes'][2]-.25 for h in floor))
    doors=[d for d in info['aberturas'] if d['tipo']=='porta' and d['face']=='frente' and d['z']==0]
    if not doors:doors=[dict(u=width/2,z=0,largura=2)]
    for door in doors:
        for dx in [-.25,0,.25]:
            x=door['u']-width/2+dx
            for z in [1,1.8]:check('passagem_'+row['name']+'_'+str(dx)+'_'+str(z),not blocked(c['collision_vertices'],c['collision_triangles'],[x,-depth/2-.6,z],[x,-depth/2+.6,z]))
for row in read('arvores.json'):
    c=np.load(O/'cache'/(row['name']+'.npz'));w=c['weight'];z=c['position'][:,2]
    stats=next(s for s in report['models'] if s['name']==row['name'])
    check('vento_colisao_'+row['name'],np.any(w>.001) and np.all(w[z<.05]==0) and stats['wind_shaders']>0 and stats['collision'])
cfg=dict(revision='porto-20261009-construido-1',spawn=read('construcao.json')['spawn'],ground_z=4.83,maps=[m['name'] for m in report['maps']],probe_models=sorted(house_names)+[r['name'] for r in read('arvores.json')]+['pe_porto_00','pe_porto_01','pe_porto_05'],ground_probes=probes)
(O/'fivem/data').mkdir(exist_ok=True);(O/'fivem/data/config.json').write_text(json.dumps(cfg,indent=2))
# Preserve the stock clipping grid. Replace only water regions intersecting the reshaped coast.
original_water=O/'fontes/water_original.xml'
if not original_water.exists():original_water.write_bytes((P/'fivem/data/water.xml').read_bytes())
src=ET.parse(original_water);root=src.getroot();quads=root.find('WaterQuads');removed=0
for item in list(quads):
    vals={k:float(item.find(k).attrib['value']) for k in ['minX','maxX','minY','maxY','z']}
    if vals['z']!=0 and vals['maxX']>-380 and vals['minX']<880 and vals['maxY']>-1160 and vals['minY']<70:quads.remove(item);removed+=1
source=P/'porto_esperanca/scripts/criar_porto_blender.py';tree=ast.parse(source.read_text(encoding='utf8'));ns={'np':np}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='riverx'],type_ignores=[]),str(source),'exec'),ns)
template=copy.deepcopy(quads[0]);added=0
for y in range(184,776,8):
    cy=y+4;cx=float(ns['riverx'](cy));half=10+8*np.exp(-((cy-55)/150)**2);level=round(max(0,(cy-185)*.035)*4)/4
    xmin=int(np.ceil((cx-half)/8)*8);xmax=int(np.floor((cx+half)/8)*8)
    if xmax<=xmin:continue
    item=copy.deepcopy(template)
    for k,val in dict(minX=xmin+250,maxX=xmax+250,minY=y-850,maxY=y+8-850,z=level).items():item.find(k).set('value',str(val))
    quads.insert(0,item);added+=1
check('agua_limites_int16',all(-32768<=float(e.attrib['value'])<=32767 for item in quads for e in item if e.tag in ['minX','maxX','minY','maxY']))
ET.indent(src,space='  ');(O/'exportados/data').mkdir(exist_ok=True)
(O/'exportados/data/water.xml').write_bytes(b'<?xml version="1.0" encoding="UTF-8"?>\r\n'+ET.tostring(root,encoding='utf-8').replace(b'\n',b'\r\n'))
basecfg=json.loads((P/'fivem/data/config.json').read_text());basecfg.update(revision='ilha-20261009-porto-entrada-2',water_quads=len(quads),porto=cfg['spawn'])
(O/'exportados/data/config.json').write_text(json.dumps(basecfg,indent=2))
validation=dict(passed=True,checks=checks,water=dict(removed=removed,added=added,quads=len(quads),in_game_verified=False),collision_source_checked=True,in_game_verified=False)
(O/'dados/validacao_integracao.json').write_text(json.dumps(validation,indent=2))
print(json.dumps(dict(passed=True,checks=len(checks),probes=probes,water=validation['water']),indent=2))
