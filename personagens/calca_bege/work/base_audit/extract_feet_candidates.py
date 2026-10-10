import sys,json
from pathlib import Path
sys.path.insert(0,r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
from szio.rpf import open_rpf
out=Path(__file__).resolve().parent
for item in json.loads((out/'barefoot_candidates.json').read_text()):
 r=open_rpf(item['archive']).open_nested(item['nested']);d=item['dir'];f=item['file']
 (out/(d+'^'+f)).write_bytes(r.read_bytes(d+'/'+f))
 for td in r.list_dir(d):
  if td.startswith('feet_diff_'+f[5:8]) and '_a_' in td and td.endswith('.ytd'):
   (out/(d+'^'+td)).write_bytes(r.read_bytes(d+'/'+td))
print('EXTRACTED',len(list(out.glob('mp*^feet*.ydd'))))
