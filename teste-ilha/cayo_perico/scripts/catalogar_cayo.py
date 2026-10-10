import json, sys
from pathlib import Path
R = Path(__file__).resolve().parents[3]
P = R / 'teste-ilha/cayo_perico'
sys.path[:0] = [str(R/'laboratorio_fivem/work/pydeps'), r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
from szio.rpf import open_rpf
game = Path(r'C:/Program Files (x86)/Steam/steamapps/common/Grand Theft Auto V/update/x64/dlcpacks/mpheist4')
out = P/'originais'; out.mkdir(parents=True, exist_ok=True)
rows=[]
def walk(a, folder='', prefix='', depth=0):
    for name in a.list_dir(folder):
        f = folder+'/'+name if folder else name
        if a.is_dir(f): walk(a,f,prefix,depth)
        elif f.endswith('.rpf'):
            walk(a.open_nested(f),'',prefix+'|'+f,depth+1)
        else:
            rows.append({'file':f,'archive':prefix})
            if f in ('content.xml','setup2.xml') or any(k in f.lower() for k in ['islandhopper','water_heist','waterheight']):
                target=out/(Path(prefix.split('|')[0]).stem+'_'+Path(f).name)
                target.write_bytes(a.read_bytes(f))
for f in game.glob('*.rpf'):
    walk(open_rpf(f),prefix=str(f))
(P/'catalogo.json').write_text(json.dumps(rows,indent=2))
from collections import Counter
print('CATALOGO',len(rows),Counter(Path(x['file']).suffix for x in rows),flush=True)
print('ARQUIVOS_CONFIG', [x.name for x in out.iterdir()],flush=True)
