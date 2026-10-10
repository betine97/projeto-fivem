"""Complete requested categories, including small props and alternate visible textures."""
import json,hashlib,math,shutil,collections
from pathlib import Path
import render_catalog as r
PARTS=('feet','p_head','p_eyes','p_ears','p_lwrist','p_rwrist','accs','task','hand')
path=r.OUT/'catalog.json';base=Path(__file__).parent
backup=base/'catalog_before_remaining_categories.json'
if not backup.exists():shutil.copy2(path,backup)
catalog=json.loads(path.read_text(encoding='utf-8'));items={i['id']:i for i in catalog['items']}
candidates=sorted((m for m in r.DATA['models'] if m['part'] in PARTS),key=lambda m:(m['part'],m['sex'],m['collection'],m['index']))
accepted=[];skips=[];recovered=0
def save():
    catalog['items']=list(items.values());catalog['selection']='all-renderable-native-categories'
    temp=path.with_suffix('.tmp');temp.write_text(json.dumps(catalog,ensure_ascii=False),encoding='utf-8');temp.replace(path)
for n,row in enumerate(candidates,1):
    ident=hashlib.sha1((row['collection']+row['part']+str(row['index'])).encode()).hexdigest()[:12]
    key=(row['sex'],row['collection'],row['part'],row['index']);variations=r.texgroups[key]
    ordered=sorted(variations,key=lambda t:t['variant']);error='no diffuse';succeeded=False
    for index,texture in enumerate(ordered):
        pieces=[]
        try:
            r.texgroups[key]=[texture];flip=r.ImageOps.flip
            try:
                r.ImageOps.flip=lambda image:image
                pieces,center,extent,triangles,_,selected=r.prep(row,min_extent=.0001,min_indices=3)
            finally:r.ImageOps.flip=flip
            r.render(pieces,center,extent,.15,r.OUT/'previews'/f'{ident}.webp')
            r.render(pieces,center,extent,math.pi+.15,r.OUT/'previews'/f'{ident}-back.webp')
            items[ident]={'id':ident,'sex':row['sex'],'category':row['part'],'title':r.CATEGORIES[row['part']],
              'collection':row['collection'],'collectionLabel':r.collection_label(row['collection']),'index':row['index'],
              'file':row['path'].split('/')[-1],'textureCount':len(variations),'textureFile':selected['path'].split('/')[-1],
              'triangles':triangles,'image':f'previews/{ident}.webp','back':f'previews/{ident}-back.webp'}
            accepted.append(ident);succeeded=True
            if index:recovered+=1
            break
        except Exception as e:
            error=str(e)
            # Only invisible/degenerate variations justify trying another diffuse.
            if error not in ('empty model','empty variant'):break
        finally:
            r.texgroups[key]=variations
            for piece in pieces:
                for obj in piece:obj.release()
    if not succeeded:
        asset=r.try_load_asset(r.vpath(row['path']))
        native_triangles=sum(len(g.index_buffer)//3 for d in asset.drawables.values() for m in d.models[min(d.models)] for g in m.geometries)
        skips.append({'model':row,'reason':error,'nativeTriangles':native_triangles})
        print('SKIP',row['part'],row['sex'],row['index'],error[:100],flush=True)
    if n%25==0:save();print('PROGRESS',n,'/',len(candidates),'rendered',len(accepted),flush=True)
catalog['completeCategories']=list(r.CATEGORIES)
save()
report={'candidates':len(candidates),'rendered':len(accepted),'counts':dict(collections.Counter(items[i]['sex']+'_'+items[i]['category'] for i in accepted)),
  'catalogTotal':len(items),'previewImages':len(accepted)*2,'recoveredWithAlternateDiffuse':recovered,'skipped':skips}
(base/'remaining_expansion_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
assert len(accepted)+len(skips)==len(candidates) and len(accepted)==len(set(accepted))
print('COMPLETE',json.dumps({k:v for k,v in report.items() if k!='skipped'}),'skipped',len(skips),flush=True)
