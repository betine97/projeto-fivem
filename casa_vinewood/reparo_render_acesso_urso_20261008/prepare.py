"""Snapshot only this repair's targets; never rebuild from a stale live baseline."""
from pathlib import Path
import shutil,json,hashlib
P=Path(__file__).resolve().parent; R=P.parents[1]; W=P.parent
D=R/'server-data/resources/cidade_mansao'; B=P/'baseline'; O=P/'stream'
old=W/'recuo_frente_despensa_20261008'
O.mkdir(exist_ok=True); (B/'stream').mkdir(parents=True,exist_ok=True)
files=['objetos_client.lua','objetos_catalogo.json']
files += ['stream/'+n for n in ['mansao_fachada_entrada.ydr','mansao_garagem_subsolo.ydr','mansao_acesso_garagem.ytyp','mansao_acesso_garagem.ymap','mansao_acesso_garagem.ybn','mansao_tapete_urso.ydr','mansao_piano_tapetes.ytyp','ch2_09b_hs05.ydr','ch2_09b_hs05_details.ydr','ch2_09b_l2.ydr','ch2_occl_02.ymap','apa_ch2_occl_02.ymap']]
files += ['stream/'+f.name for f in (W/'work/native').glob('*ch2_09b_[0-3].ybn')]
files += ['stream/'+f.name for f in (W/'work/native').glob('ch2_roads*.ymap')]
hashes={}
for n in sorted(set(files)):
 f=D/n; dst=B/n; src=f if f.exists() else W/'work/native'/Path(n).name
 hashes[n]=hashlib.sha256(f.read_bytes()).hexdigest() if f.exists() else None
 if src.exists(): dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
(P/'baseline_hashes.json').write_text(json.dumps(hashes,indent=2))
shutil.copytree(old/'textures',P/'textures',dirs_exist_ok=True)
spec=json.loads((old/'spec.json').read_text());spec['collection']='72_REPARO_CONTENCAO_RENDER_URSO'
spec['earth_cuts'][2][0][0]=3.47;spec['earth_cuts'][2][1][0]=6.145
spec['earth_cuts'][2][0][2]=-3.45
spec['earth_cuts'][1][0][0]=6.13;spec['earth_cuts'][1][1][0]=13.08
(P/'spec.json').write_text(json.dumps(spec,indent=2))
code=(old/'build_models.py').read_text()
start=code.index('for x in [3.62,5.85]:');end=code.index('# The garage has actual room',start)
code=code[:start]+'''# Closed retaining cheeks follow the same diagonal as the treads. Their tops
# retain the existing garden grade instead of falling below it at the street.
for x0,x1 in [(3.47,3.64),(5.85,6.145)]:
    for j in range(13):
        t=(j+1)/13
        y1=lambda x,j=j:edge(x)-.30-j*.30
        y0=lambda x,j=j:y1(x)-.30
        z0=max(street(x0)*(1-t)-.8*t+.20,-1.22)
        z1=max(street(x1)*(1-t)-.8*t+.20,-1.22)
        top=[(x0,y0(x0),z0),(x1,y0(x1),z1),(x1,y1(x1),z1),(x0,y1(x0),z0)]
        mesh('Contencao fechada escada %02d'%j,[(x,y,-3.45) for x,y,z in top]+top,faces,'reboco',True)
        quad_slab('Capa contencao escada %02d'%j,x0,x1,y0,y1,z0+.028,z1+.028,z0+.028,z1+.028,'creme',True,.028)
    quad_slab('Fecho chegada contencao escada',x0,x1,lambda x:12.39,lambda x:edge(x)-4.20,-.60,-.60,-.60,-.60,'reboco',True,2.85)
    quad_slab('Capa chegada contencao escada',x0,x1,lambda x:12.39,lambda x:edge(x)-4.20,-.572,-.572,-.572,-.572,'creme',True,.028)
    # Seal the apron side up to the boundary without extending into traffic.
    quad_slab('Fecho inferior contencao escada',x0,x1,lambda x:edge(x)-.30,edge,-1.22,-1.22,-1.22,-1.22,'reboco',True,2.23)
    quad_slab('Capa inferior contencao escada',x0,x1,lambda x:edge(x)-.30,edge,-1.192,-1.192,-1.192,-1.192,'creme',True,.028)
''' +code[end:]
code=code.replace("[(6.145,6.40),(12.80,13.055)]","[(6.13,6.40),(12.80,13.08)]")
code=code.replace("def top(x,t):return rampz(x,t)+(.0 if t==1 else (1-t)*(-.47+4.2))","def top(x,t):return -.47-.775*t")
needle="mesh('Muro contencao rampa %02d'%j,verts,faces,'reboco',True)"
code=code.replace(needle,needle+"\n        quad_slab('Capa contencao rampa %02d'%j,x0,x1,lambda x:ry(x,t0),lambda x:ry(x,t1),top(x0,t0)+.035,top(x1,t0)+.035,top(x0,t1)+.035,top(x1,t1)+.035,'creme',True,.035)")
(P/'build_models.py').write_text(code)
code=(old/'package_models.py').read_text()
start=code.index('    # Follow the moved stair/retaining-wall fixtures');end=code.index('    for shader in a.shader_group.shaders:',start)
code=code[:start]+code[end:] # Already moved in the live baseline; keep light locations.
(P/'package_models.py').write_text(code)
print('REPAIR_SNAPSHOT_READY',len(hashes),flush=True)
