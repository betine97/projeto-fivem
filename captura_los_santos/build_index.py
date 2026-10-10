"""Resolve native model hashes, archetypes and original RPF locations locally."""
from pathlib import Path
import json,sys,os
ROOT=Path(__file__).resolve().parent.parent
sys.path[:0]=[str(ROOT/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
from szio.rpf import open_rpf
from szio.gta5 import try_load_asset
GTA=Path(os.environ.get('GTA_ROOT',r'C:/Program Files (x86)/Steam/steamapps/common/Grand Theft Auto V'))
OUT=ROOT/'captura_los_santos';CACHE=OUT/'cache';CACHE.mkdir(exist_ok=True)
def joaat(name):
    h=0
    for b in name.lower().encode():
        h=(h+b)&0xffffffff;h=(h+(h<<10))&0xffffffff;h^=h>>6
    h=(h+(h<<3))&0xffffffff;h^=h>>11;return (h+(h<<15))&0xffffffff
def main():
    files=json.loads((ROOT/'painel_adm_20261009/cayo_thumbnails/native_index.json').read_text())
    paths=(ROOT/'laboratorio_fivem/work/assets_index.txt').read_text().splitlines()
    for p in paths:files.setdefault(p.rsplit('|',1)[-1].rsplit('/',1)[-1].lower(),p)
    models={}
    for name,path in files.items():
        if name.endswith(('.ydr','.yft')):
            model=Path(name).stem
            models[str(joaat(model))]={'model':model,'asset':model,'file':path,'kind':'drawable' if name.endswith('.ydr') else 'fragment'}
    arcs={};failures=[];n=0
    for path in paths:
        if not path.endswith('.ytyp') or '/destruction/' in path:continue
        try:
            parts=path.split('|');key='|'.join(parts[:-1])
            if key not in arcs:
                a=open_rpf(GTA/parts[0])
                for part in parts[1:-1]:a=a.open_nested(part)
                arcs[key]=a
            p=CACHE/'index-archetypes.ytyp';p.write_bytes(arcs[key].read_bytes(parts[-1]))
            (CACHE/'index-progress.txt').write_text(path,encoding='utf8')
            asset=try_load_asset(p)
            if not asset:continue
            for t in asset.archetypes:
                name=str(t.name)
                if name.startswith('hash_'):continue
                model={'model':name,'asset':str(t.asset_name),'textureDictionary':str(t.texture_dictionary),'drawableDictionary':str(t.drawable_dictionary),'bbMin':list(t.bb_min),'bbMax':list(t.bb_max),'archetypeFile':path,'mlo':'Mlo' in type(t).__name__}
                model['file']=files.get(model['asset']+'.ydr') or files.get(model['asset']+'.yft') or files.get(model['drawableDictionary']+'.ydd')
                models[str(joaat(name))]=model;n+=1
        except Exception as e:failures.append({'path':path,'error':str(e)[:140]})
    (OUT/'data/model_index.json').write_text(json.dumps({'models':models,'files':files},ensure_ascii=False),encoding='utf8')
    (OUT/'data/index_report.json').write_text(json.dumps({'modelCount':len(models),'archetypes':n,'failures':failures},indent=2),encoding='utf8')
    print('MODELOS_INDEXADOS',len(models),'ARQUETIPOS',n,'FALHAS',len(failures),flush=True)
if __name__=='__main__':main()
