"""Add every renderable native male/female top and undershirt to the local catalog."""
import json,hashlib,math,shutil,collections
from pathlib import Path
import render_catalog as r

path=r.OUT/'catalog.json'
backup=Path(__file__).parent/'catalog_before_all_tops.json'
if not backup.exists():shutil.copy2(path,backup)
catalog=json.loads(path.read_text(encoding='utf-8'))
items={i['id']:i for i in catalog['items']}
candidates=sorted((m for m in r.DATA['models'] if m['part'] in ('jbib','teef')),key=lambda m:(m['sex'],m['collection'],m['index']))
accepted=[];skips=[]
def save():
    catalog['items']=list(items.values())
    catalog['selection']='all-renderable-tops-lower-and-masks'
    catalog['completeCategories']=list(dict.fromkeys(catalog.get('completeCategories',[])+['jbib','teef']))
    temp=path.with_suffix('.tmp');temp.write_text(json.dumps(catalog,ensure_ascii=False),encoding='utf-8');temp.replace(path)
for n,row in enumerate(candidates,1):
    ident=hashlib.sha1((row['collection']+row['part']+str(row['index'])).encode()).hexdigest()[:12]
    pieces=[]
    try:
        # GTA native UV V increases downward; framebuffer readback still needs its own flip.
        original_flip=r.ImageOps.flip
        try:
            r.ImageOps.flip=lambda image:image
            pieces,center,extent,triangles,variations,selected=r.prep(row)
        finally:r.ImageOps.flip=original_flip
        r.render(pieces,center,extent,.15,r.OUT/'previews'/f'{ident}.webp')
        r.render(pieces,center,extent,math.pi+.15,r.OUT/'previews'/f'{ident}-back.webp')
        items[ident]={'id':ident,'sex':row['sex'],'category':row['part'],'title':r.CATEGORIES[row['part']],
          'collection':row['collection'],'collectionLabel':r.collection_label(row['collection']),
          'index':row['index'],'file':row['path'].split('/')[-1],'textureCount':len(variations),
          'textureFile':selected['path'].split('/')[-1],'triangles':triangles,
          'image':f'previews/{ident}.webp','back':f'previews/{ident}-back.webp'}
        accepted.append(ident)
    except Exception as e:
        skips.append({'model':row,'reason':str(e)})
        print('SKIP',row['sex'],row['collection'],row['index'],str(e)[:100],flush=True)
    finally:
        for piece in pieces:
            for obj in piece:obj.release()
    if n%20==0:
        save();print('PROGRESS',n,'/',len(candidates),'rendered',len(accepted),flush=True)
save()
report={'candidates':len(candidates),'rendered':len(accepted),
        'counts':dict(collections.Counter(items[i]['sex']+'_'+items[i]['category'] for i in accepted)),
        'catalogTotal':len(items),'previewImages':len(accepted)*2,'skipped':skips}
(Path(__file__).parent/'tops_expansion_report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
assert len(accepted)+len(skips)==len(candidates)
assert len(accepted)==len(set(accepted))
print('COMPLETE',json.dumps({k:v for k,v in report.items() if k!='skipped'}),'skipped',len(skips),flush=True)
