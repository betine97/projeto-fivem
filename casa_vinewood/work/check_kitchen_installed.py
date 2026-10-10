import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood';D=R/'server-data/resources/cidade_mansao'
q=json.loads((W/'verificacao_cozinha_completa.json').read_text());assert json.loads((W/'instalacao_cozinha_completa.json').read_text())['passed']
for name,sha in q['files'].items():
 p=D/('stream/'+name if Path(name).suffix in ('.ydr','.ymap','.ytyp') else name)
 assert hashlib.sha256(p.read_bytes()).hexdigest()==sha,name
assert (D/'fxmanifest.lua').read_text().count("data_file 'DLC_ITYP_REQUEST' 'stream/mansao_cozinha_completa.ytyp'")==1
print('POST_INSTALL_HASHES_AND_REGISTRATION_OK')
