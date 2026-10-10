"""Add only this reference-wall ensemble to the current resource, with backups."""
import sys,json,hashlib,copy,os
from pathlib import Path
from datetime import datetime
P=Path(__file__).resolve().parent;W=P.parent;R=W.parent;D=R/'server-data/resources/cidade_mansao'
sys.path.insert(0,str(W/'work/lua_syntax_deps'))
from luaparser import ast
spec=json.loads((P/'spec.json').read_text());verification=json.loads((P/'verification.json').read_text())
assert verification['passed'] and verification['native_roundtrip']
def digest(data):return hashlib.sha256(data).hexdigest()
def current(p):return p.read_bytes() if p.exists() else None
def snapshot():return {f.relative_to(D).as_posix():digest(f.read_bytes()) for f in D.rglob('*') if f.is_file()}
baseline=snapshot();targets={}
for name,h in verification['files'].items():
    data=(P/'stream'/name).read_bytes();assert digest(data)==h
    path=D/'stream'/name;before=current(path);assert before is None or before==data
    targets[path]=(before,data)
manifest_path=D/'fxmanifest.lua';manifest_before=manifest_path.read_bytes();manifest=manifest_before.decode('utf-8');newline='\r\n' if '\r\n' in manifest else '\n'
registration="data_file 'DLC_ITYP_REQUEST' 'stream/mansao_parede_aparador.ytyp'"
if registration not in manifest:manifest=manifest.rstrip('\r\n')+newline*2+"files { 'stream/mansao_parede_aparador.ytyp' }"+newline+registration+newline
ast.parse(manifest);targets[manifest_path]=(manifest_before,manifest.encode('utf-8'))
cfg_path=D/'portas_madeira.json';cfg_before=cfg_path.read_bytes();old=json.loads(cfg_before);cfg=copy.deepcopy(old)
existing=next((d for d in cfg['doors'] if d['model']==spec['door_model']),None)
if existing is None:
    ident=len(cfg['doors'])+1
    assert [d['id'] for d in cfg['doors']]==list(range(1,ident))
    cfg['doors'].append({'id':ident,'name':'Sacada da cozinha','model':spec['door_model'],'hinge':spec['door_hinge_house'],'closed_heading':-90,'open_heading':5,'width_m':spec['door_width'],'height_m':spec['door_height'],'leaf_thickness_m':.045,'opening_center':[14.168,-5.17,.25],'opening_bounds':[14.108,14.436,-5.72,-4.62,-.8,1.7]})
    cfg['prototypes'].append({'name':spec['door_model'],'width_m':spec['door_width'],'height_m':spec['door_height'],'thickness_m':.045})
    assert cfg['doors'][:-1]==old['doors'] and cfg['prototypes'][:-1]==old['prototypes']
    restore=copy.deepcopy(cfg);restore['doors']=old['doors'];restore['prototypes']=old['prototypes'];assert restore==old
else:assert existing['hinge']==spec['door_hinge_house']
targets[cfg_path]=(cfg_before,(json.dumps(cfg,indent=2,ensure_ascii=False)+'\n').encode('utf-8'))
cat_path=D/'objetos_catalogo.json';cat_before=cat_path.read_bytes();oldcat=json.loads(cat_before);cat=copy.deepcopy(oldcat)
for name in [spec['model'],spec['door_model']]:
    if name not in cat['protectedModels']:cat['protectedModels'].append(name)
restored=copy.deepcopy(cat);restored['protectedModels']=oldcat['protectedModels'];assert restored==oldcat
targets[cat_path]=(cat_before,(json.dumps(cat,indent=2,ensure_ascii=False)+'\n').encode('utf-8'))
backup=P/'backup_preinstall'/datetime.now().strftime('%Y%m%d_%H%M%S_%f');backup.mkdir(parents=True)
for path,(before,data) in targets.items():assert current(path)==before,f'Concurrent update: {path}'
installed=[]
for path,(before,data) in targets.items():
    assert current(path)==before,f'Concurrent update: {path}'
    if before!=data:
        if before is not None:
            q=backup/path.relative_to(D);q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(before)
        temp=path.with_name(path.name+'.aparador.tmp')
        try:
            temp.write_bytes(data);assert current(path)==before;os.replace(temp,path)
        finally:
            if temp.exists():temp.unlink()
    assert path.read_bytes()==data;installed.append(path.relative_to(D).as_posix())
after=snapshot();target_names=set(installed)
concurrent=[name for name,h in baseline.items() if name not in target_names and after.get(name)!=h]
assert not concurrent,concurrent
assert json.loads(cfg_path.read_bytes())==cfg
assert json.loads(cat_path.read_bytes())==cat
for script in ['portas_client.lua','portas_server.lua']:ast.parse((D/script).read_text(encoding='utf-8'))
report={'installed_files':{name:after[name] for name in installed},'backup':str(backup),'unrelated_files_unchanged':len(baseline)-len(target_names.intersection(baseline)),'saved_positions_unchanged':after.get('objetos_posicoes.json')==baseline.get('objetos_posicoes.json'),'previous_door_entries_preserved':True,'catalog_object_positions_preserved':True,'general_illumination_files_unchanged':all(after.get(n)==baseline.get(n) for n in ['iluminacao_decorativa.lua','iluminacao_ambiente.json','luzes_pendentes.lua','stream/mansao_teto.ydr']),'requires_resource_reload':True,'in_game_verified':False,'installed_at':datetime.now().astimezone().isoformat()}
(P/'installation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('INSTALLED',len(installed),'files; untouched',report['unrelated_files_unchanged'],'other files; door opens with E',flush=True)
