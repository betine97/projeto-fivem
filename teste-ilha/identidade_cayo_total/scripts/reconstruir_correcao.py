"""Build and validate offline; installation is a separate atomic maintenance step."""
from pathlib import Path
import subprocess,sys,time
here=Path(__file__).resolve().parent;out=here.parent
scripts=['solo.py','reparar_limites_render.py','vegetacao.py','povoacoes.py','rasteira.py','registrar_grama.py','lod_hierarquia.py','rasteira_distante.py','otimizar_streaming.py','testar_hierarquia.py','testar_limites_render.py','testar_rasteira_distante.py','testar_orcamento_render.py','auditar.py']
for name in scripts:
    print('START',name,flush=True);start=time.time()
    with (out/('rebuild-'+name+'.log')).open('w',encoding='utf8') as log:
        p=subprocess.run([sys.executable,str(here/name)],stdout=log,stderr=subprocess.STDOUT)
    if p.returncode:
        print((out/('rebuild-'+name+'.log')).read_text(encoding='utf8')[-4000:],flush=True);raise SystemExit(p.returncode)
    print('PASS',name,round(time.time()-start,1),flush=True)
print('OFFLINE_REBUILD_VALIDATED',flush=True)
