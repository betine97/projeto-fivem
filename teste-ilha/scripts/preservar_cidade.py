from pathlib import Path
import shutil,sqlite3,json,hashlib
from datetime import datetime
P=Path(__file__).resolve().parents[1];R=P.parent;D=P/'cidade-original-preservada';D.mkdir(exist_ok=True)
report=[]
def copy(source,target):
 target.parent.mkdir(parents=True,exist_ok=True)
 if not target.exists():shutil.copy2(source,target)
 report.append({'original':str(source.relative_to(R)),'backup':str(target.relative_to(P)),'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
for f in (R/'server-data/resources').rglob('*'):
 if f.is_file():copy(f,D/f.relative_to(R))
for f in (R/'server-data').glob('*.cfg'):copy(f,D/'server-data'/f.name)
for f in (R/'painel_acesso').rglob('*'):
 if f.is_file() and '__pycache__' not in f.parts and f.suffix not in ['.sqlite3','.db'] and not f.name.endswith(('-wal','-shm')):copy(f,D/f.relative_to(R))
db=R/'painel_acesso/data/usuarios.sqlite3';out=D/'painel_acesso/data/usuarios.sqlite3'
if db.exists() and not out.exists():
 out.parent.mkdir(parents=True,exist_ok=True)
 with sqlite3.connect(f'file:{db.as_posix()}?mode=ro',uri=True) as src,sqlite3.connect(out) as dst:src.backup(dst)
(D/'inventario.json').write_text(json.dumps({'created_at':datetime.now().astimezone().isoformat(),'source_city':str(R),'server_was_not_restarted':True,'files':report,'sqlite_consistent_backup':True},indent=2),encoding='utf-8')
(D/'LEIA-ME.md').write_text('# Cidade original preservada\n\nCópia dos recursos, configurações e painel da cidade atual, incluindo um backup consistente do banco de jogadores. A cidade original continua no diretório pai, sem alterações deste projeto. A instalação do FXServer permanece em `.runtime` no diretório pai; este backup não duplica o executável do servidor.\n',encoding='utf-8')
print('CITY_PRESERVED',len(report),sum(f['bytes'] for f in report),flush=True)
