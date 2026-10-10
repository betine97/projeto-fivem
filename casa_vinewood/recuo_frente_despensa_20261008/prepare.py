"""Stage this revision independently of other chats and preserve the live baseline."""
import json, hashlib, shutil
from pathlib import Path
P = Path(__file__).resolve().parent
W = P.parent
R = W.parent
F = W / 'fachada_garagem_20261008'
D = R / 'server-data/resources/cidade_mansao'
for part in ['stream', 'baseline/stream', 'textures']:
    (P / part).mkdir(parents=True, exist_ok=True)
hashes = {}
for f in D.rglob('*'):
    if f.is_file():
        key = f.relative_to(D).as_posix()
        hashes[key] = hashlib.sha256(f.read_bytes()).hexdigest()
(P / 'baseline_hashes.json').write_text(json.dumps(hashes, indent=2))
for f in (D / 'stream').iterdir():
    if f.is_file() and (f.name.startswith(('ch2_', 'apa_ch2_', 'hei_ch2_')) or f.name in ['mansao_paredes.ydr', 'cidade_mansao.ybn', 'mansao_acesso_garagem.ybn', 'mansao_acesso_garagem.ytyp', 'mansao_acesso_garagem.ymap'] or f.name.startswith(('mansao_fachada_entrada.', 'mansao_garagem_subsolo.'))):
        shutil.copy2(f, P / 'baseline/stream' / f.name)
for n in ['portas_madeira.json', 'portas_client.lua', 'portas_server.lua']:
    shutil.copy2(D / n, P / 'baseline' / n)
for f in (F / 'textures').iterdir():
    shutil.copy2(f, P / 'textures' / f.name)
spec = json.loads((F / 'spec.json').read_text())
spec['collection'] = '71_RECUO_CALCADA_20261008'
spec['curb_end'] = {'y_intercept':16.235, 'slope_x':.173, 'road_edge_intercept':16.195}
spec['earth_cuts'] = [spec['earth_cuts'][0], [[6.145,9.53,-4.45],[13.055,18.52,1.6]], [[3.54,12.39,-3.4],[5.90,17.28,1.6]]]
spec['ramp_y'] = [9.55,18.4494]
spec['removed_wall'] = [[2.599,2.10,-.815],[5.701,2.60,2.577]]
(P / 'spec.json').write_text(json.dumps(spec, indent=2))
code = (F / 'build_models.py').read_text()
a = code.index('# A street-matched apron')
b = code.index('# The garage has actual room')
code = code[:a] + '''# Thirteen full-depth treads, set back to the measured diagonal street edge.
def edge(x): return 16.235 + .173*x
def street(x): return -2.7435 - (x-3.64)*.1145
def quad_slab(name,x0,x1,t0,t1,z00,z10,z01,z11,key,solid=True,depth=.18):
    top=[(x0,t0(x0),z00),(x1,t0(x1),z10),(x1,t1(x1),z11),(x0,t1(x0),z01)]
    return mesh(name,[(x,y,z-depth) for x,y,z in top]+top,faces,key,solid)
for i in range(13):
    t=(i+1)/13
    y1=lambda x,i=i:edge(x)-.30-i*.30
    y0=lambda x,i=i:y1(x)-.30
    zl=street(3.64)*(1-t)-.8*t;zr=street(5.85)*(1-t)-.8*t
    quad_slab('Entrada degrau %02d'%(i+1),3.64,5.85,y0,y1,zl,zr,zl,zr,'creme',True,.18)
    quad_slab('LED degrau %02d'%(i+1),3.68,5.81,lambda x:y1(x)-.012,lambda x:y1(x)-.006,zl-.047,zr-.047,zl-.036,zr-.036,'led',False,.002)
quad_slab('Patamar inferior dentro calcada',3.64,5.85,lambda x:edge(x)-.30,edge,street(3.64),street(5.85),street(3.64),street(5.85),'creme',True,.12)
quad_slab('Patamar chegada entrada',3.63,5.86,lambda x:12.39,lambda x:edge(x)-4.20,-.8,-.8,-.8,-.8,'creme',True,.16)
for x in [3.62,5.85]:
    for j in range(13):
        y1=edge(x)-.30-j*.30;y0=y1-.30;t=(j+1)/13;zt=street(x)*(1-t)-.8*t
        box('Mureta escada externa',(x-.075,y0,-3.38),(x+.025,y1,zt+.20),'reboco',True)
''' + code[b:]
a = code.index('# Grade changes flatten')
b = code.index('for x in [6.70,9.58,12.49]')
code = code[:a] + '''# A diagonal, flush approach; ease the slope without a tall lip in traffic.
def endroad(x):return -3.0606-(x-6.4)*.1126
def rampz(x,t):
    a=.12
    s=t*t/(2*a*(1-a)) if t<a else 1-(1-t)**2/(2*a*(1-a)) if t>1-a else (t-a/2)/(1-a)
    return -4.20+(endroad(x)+4.20)*s
def ry(x,t):return 9.55+(edge(x)-9.55)*t
for j in range(24):
    t0=j/24;t1=(j+1)/24
    quad_slab('Rampa transicao %02d'%j,6.4,12.8,lambda x:ry(x,t0),lambda x:ry(x,t1),rampz(6.4,t0),rampz(12.8,t0),rampz(6.4,t1),rampz(12.8,t1),'cimento',True,.16)
    for x0,x1 in [(6.145,6.40),(12.80,13.055)]:
        def top(x,t):return rampz(x,t)+(.0 if t==1 else (1-t)*(-.47+4.2))
        verts=[(x0,ry(x0,t0),rampz(x0,t0)-.30),(x1,ry(x1,t0),rampz(x1,t0)-.30),(x1,ry(x1,t1),rampz(x1,t1)-.30),(x0,ry(x0,t1),rampz(x0,t1)-.30),(x0,ry(x0,t0),top(x0,t0)),(x1,ry(x1,t0),top(x1,t0)),(x1,ry(x1,t1),top(x1,t1)),(x0,ry(x0,t1),top(x0,t1))]
        mesh('Muro contencao rampa %02d'%j,verts,faces,'reboco',True)
for t in [.023,.975]:
    quad_slab('Grelha drenagem',6.41,12.79,lambda x:ry(x,t),lambda x:ry(x,t+.012),rampz(6.41,t)+.004,rampz(12.79,t)+.004,rampz(6.41,t+.012)+.004,rampz(12.79,t+.012)+.004,'preto',False,.01)
for t in [.18,.42,.66]:
    for x in [6.414,12.781]:
        y=ry(x,t);z=rampz(x,t)+.45
        box('Balizador rampa corpo',(x-.012,y-.12,z-.075),(x+.012,y+.12,z+.075),'preto')
        box('Balizador rampa emissor',(x-.017,y-.09,z-.045),(x+.017,y+.09,z+.045),'led')
''' + code[b:]
code = code.replace("for name,objects in groups.items():\n", "for name,objects in groups.items():\n    if name not in spec['models'][:2]: continue\n")
(P / 'build_models.py').write_text(code, encoding='utf-8')
code = (F / 'package_models.py').read_text()
code = code.replace("enumerate(spec['models'])", "enumerate(spec['models'][:2])")
# New geometry keeps every lighting/material parameter from the current revision.
code = code.replace("    save_asset(a,target,O,name);lo=", "    old=try_load_asset(P/'baseline/stream'/(name+'.ydr'))\n    a.lights=copy.deepcopy(old.lights)\n    for shader in a.shader_group.shaders:\n        prior=next((s for s in old.shader_group.shaders if key(s)==key(shader)),None)\n        if prior: shader.parameters=copy.deepcopy(prior.parameters)\n    save_asset(a,target,O,name);lo=")
code = code.replace("save_asset(AssetMapTypes(name='mansao_acesso_garagem',archetypes=types),target,O,'mansao_acesso_garagem')", "prior=try_load_asset(P/'baseline/stream/mansao_acesso_garagem.ytyp')\nprior.archetypes=[next((t for t in types if t.name==old.name),old) for old in prior.archetypes]\nsave_asset(prior,target,O,'mansao_acesso_garagem')")
(P / 'package_models.py').write_text(code, encoding='utf-8')
print('STAGED_LIVE_BASELINE', len(hashes), flush=True)
