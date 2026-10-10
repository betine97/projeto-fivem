import json, shutil, sys
from pathlib import Path
R=Path(__file__).resolve().parents[3]; P=R/'teste-ilha/cayo_perico'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
from szio.rpf import open_rpf
stream=P/'fivem/stream'; stream.mkdir(parents=True,exist_ok=True)
for f in (P/'originais/assets').iterdir(): shutil.copy2(f,stream/f.name)
rows=json.loads((P/'catalogo.json').read_text()); archives={q['archive'] for q in json.loads((P/'proveniencia.json').read_text())}; cache={}
out=P/'originais/manifestos'; out.mkdir(exist_ok=True)
for q in rows:
    if q['archive'] not in archives or not q['file'].endswith('.ymf'): continue
    parts=q['archive'].split('|')
    if q['archive'] not in cache:
        a=open_rpf(parts[0])
        for s in parts[1:]:a=a.open_nested(s)
        cache[q['archive']]=a
    (out/(Path(parts[-1]).stem+'.ymf')).write_bytes(cache[q['archive']].read_bytes(q['file']))
print('ASSETS_COPIADOS',len(list((P/'originais/assets').iterdir())),'MANIFESTOS',len(list(out.iterdir())),flush=True)
