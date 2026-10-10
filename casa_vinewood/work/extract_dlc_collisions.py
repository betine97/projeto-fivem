"""Extract the newest DLC variants, preferring update.rpf patches."""
import sys,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
from szio.rpf import open_rpf
G=Path(r'C:/Program Files (x86)/Steam/steamapps/common/Grand Theft Auto V')
sources=(W/'work/dlc_collision_sources.txt').read_text().splitlines();seen=set();cache={};report=[]
for source in sources:
 parts=source.split('|');name=Path(parts[-1]).name
 if 'ch2_09b_' not in name or name in seen:continue
 seen.add(name);key='|'.join(parts[:-1])
 if key not in cache:
  a=open_rpf(G/parts[0])
  for sub in parts[1:-1]:a=a.open_nested(sub)
  cache[key]=a
 data=cache[key].read_bytes(parts[-1]);f=W/'work/native'/name
 f.write_bytes(data);report.append({'file':name,'source':source,'sha256':hashlib.sha256(data).hexdigest()})
(W/'work/dlc_collision_extraction.json').write_text(json.dumps(report,indent=2))
assert len(report)==16
print('EXTRACTED',len(report),'DLC collision files, including update.rpf patches')
