from pathlib import Path
import shutil,hashlib,json
root=Path(__file__).resolve().parents[2]
work=root/'castelo_rockford';source=work/'package';dest=root/'server-data/resources/cidade_castelo_livre'
assert not dest.exists(), 'Recurso ja existente; revisar antes de sobrescrever'
native=list((source/'stream').iterdir())
assert len(native)==18 and all(p.suffix in ('.ydr','.ydd','.ybn','.ymap') for p in native)
cfg=root/'server-data/server.cfg';before=cfg.read_bytes()
backup=work/'backup';backup.mkdir(exist_ok=True)
assert not (backup/'server.cfg').exists()
shutil.copy2(cfg,backup/'server.cfg')
shutil.copytree(source,dest)
for name in ['medidas.json','alteracoes.json','geometry_verificacao.json','codewalker_verificacao.json','LEIA-ME.md']:
 shutil.copy2(work/name,dest/name)
entry=b'ensure cidade_castelo_livre'
assert entry not in before
assert cfg.read_bytes()==before, 'Configuracao alterada durante instalacao'
cfg.write_bytes(before+(b'' if before.endswith(b'\n') else b'\r\n')+b'\r\n# Terreno do castelo Rockford Hills liberado\r\n'+entry+b'\r\n')
hashes={}
for p in native+[source/'fxmanifest.lua']:
 rel=p.relative_to(source);a=hashlib.sha256(p.read_bytes()).hexdigest();b=hashlib.sha256((dest/rel).read_bytes()).hexdigest();assert a==b;hashes[str(rel)]=a
assert cfg.read_bytes().count(entry)==1
result={'resource':str(dest),'native_files':len(native),'installed_bytes':sum(p.stat().st_size for p in native),'cfg_original_sha256':hashlib.sha256(before).hexdigest(),'files_sha256':hashes,'live_server_activated':False,'in_game_verified':False}
(work/'instalacao.json').write_text(json.dumps(result,indent=2))
print(json.dumps({k:v for k,v in result.items() if k!='files_sha256'},indent=2))
