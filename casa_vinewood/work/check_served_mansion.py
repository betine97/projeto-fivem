"""Read the local HTTP stream and compare it with the installed files."""
import urllib.request,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];D=R/'server-data/resources/cidade_mansao/stream';W=R/'casa_vinewood';rows=[]
for name in ('mansao_paredes.ydr','mansao_pisos.ydr','mansao_escada.ydr','cidade_mansao.ybn'):
 p=D/name
 try:
  b=urllib.request.urlopen('http://127.0.0.1:30120/files/cidade_mansao/'+name,timeout=3).read()
  local=p.read_bytes();diff=[i for i,(a,c) in enumerate(zip(b,local)) if a!=c]
  row=dict(file=name,http_bytes=len(b),disk_bytes=p.stat().st_size,http_sha256=hashlib.sha256(b).hexdigest(),disk_sha256=hashlib.sha256(local).hexdigest(),matches_disk=b==local,different_bytes=len(diff),difference_locations=diff[:30],http_header=list(b[:16]),disk_header=list(local[:16]),payload_after_header_matches=b[16:]==local[16:])
 except Exception as e:row=dict(file=name,error=str(e))
 rows.append(row);print(row,flush=True)
(W/'audit_arquivos_servidos.json').write_text(json.dumps(rows,indent=2))
