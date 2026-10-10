"""Restore only this installation's four prior files before retrying its checksum check."""
import json,hashlib,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood';SERVER=R/'server-data/resources/cidade_mansao';OUT=W/'cozinha_fivem'
spec=json.loads((W/'cozinha_completa.json').read_text());backup=max(W.glob('backup_antes_cozinha_completa_*'),key=lambda p:p.stat().st_mtime)
for rel,sha in spec['baseline_hashes'].items():
 assert hashlib.sha256((backup/rel).read_bytes()).hexdigest()==sha,rel
 assert hashlib.sha256((SERVER/rel).read_bytes()).hexdigest()==hashlib.sha256((OUT/Path(rel).name).read_bytes()).hexdigest(),rel
assert "'stream/mansao_cozinha_completa.ytyp'" not in (backup/'fxmanifest.lua').read_text()
for rel in [*spec['baseline_hashes'],'fxmanifest.lua']:shutil.copy2(backup/rel,SERVER/rel)
print('SCOPED_INSTALL_RETRY_PREPARED',backup.name,flush=True)
