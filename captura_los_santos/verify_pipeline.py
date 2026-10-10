"""Exercise real asset -> Blender image -> durable live catalogue in an isolated store."""
from pathlib import Path
import json,sys,tempfile,shutil,time
from service import CaptureStore
ROOT=Path(__file__).resolve().parent.parent;HOME=ROOT/'captura_los_santos'
index=json.loads((HOME/'data/model_index.json').read_text(encoding='utf8'))
key=next(k for k,v in index['models'].items()if v['model']=='prop_bench_01a')
with tempfile.TemporaryDirectory(prefix='cidade-captura-')as temp:
    root=Path(temp);home=root/'captura_los_santos';(home/'data').mkdir(parents=True)
    for name in ('assets.py','render_model.py'):shutil.copy2(HOME/name,home/name)
    (home/'data/model_index.json').write_text(json.dumps(index),encoding='utf8')
    store=CaptureStore(root,index=index)
    result=store.capture({'kind':'object','hash':int(key),'position':{'x':200,'y':-900,'z':30},'name':'Banco da praça','category':'Objetos de Los Santos','author':{'id':1,'name':'Verificação'}})
    deadline=time.time()+180
    while store.jobs.unfinished_tasks and time.time()<deadline:time.sleep(.5)
    if store.jobs.unfinished_tasks:raise RuntimeError('Pipeline excedeu o prazo de verificação.')
    row=store.state['captures'][0]
    if row['status']!='disponível no catálogo':
        for name in ('extraction.log','render.log'):
            p=home/'cache/prop_bench_01a'/name
            if p.exists():print(p.read_text(errors='replace')[-2500:])
        raise RuntimeError(row.get('error',row['status']))
    assert store.catalog['objects'][0]['image'].startswith('data:image/webp;base64,')
    assert store.catalog['objects'][0]['hash']==int(key)
    report=json.loads((home/'cache/prop_bench_01a/model.json').read_text())
    assert any(x['diffuse']for x in report['materials']),'Imagem sem texturas nativas'
    target=HOME/'cache/verificacao-banco.png';shutil.copy2(home/'cache/prop_bench_01a/preview.png',target)
    (HOME/'data/pipeline_verification.json').write_text(json.dumps({'ok':True,'model':'prop_bench_01a','hash':int(key),'image':str(target),'nativeFile':row['source']['file'],'textureMissing':report['missingTextures'],'catalogueRevision':store.catalog['revision']},indent=2),encoding='utf8')
    print('PIPELINE_VERIFICADO',target,flush=True)
