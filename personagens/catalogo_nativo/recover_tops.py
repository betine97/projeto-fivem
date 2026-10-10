"""Retry real meshes whose first diffuse is invisible using remaining native variations."""
import json,hashlib,math,collections
from pathlib import Path
import render_catalog as r
reportpath=Path(__file__).parent/'tops_expansion_report.json'
report=json.loads(reportpath.read_text(encoding='utf-8'))
catalogpath=r.OUT/'catalog.json';catalog=json.loads(catalogpath.read_text(encoding='utf-8'))
recovered=[]
for entry in report['skipped']:
    if entry['reason']!='empty model' or entry['nativeTriangles']<=2:continue
    row=entry['model'];key=(row['sex'],row['collection'],row['part'],row['index'])
    variations=r.texgroups[key];pieces=[]
    for texture in sorted(variations,key=lambda t:t['variant'])[1:]:
        try:
            r.texgroups[key]=[texture];flip=r.ImageOps.flip
            try:
                r.ImageOps.flip=lambda image:image
                pieces,center,extent,triangles,_,selected=r.prep(row)
            finally:r.ImageOps.flip=flip
            ident=hashlib.sha1((row['collection']+row['part']+str(row['index'])).encode()).hexdigest()[:12]
            r.render(pieces,center,extent,.15,r.OUT/'previews'/f'{ident}.webp')
            r.render(pieces,center,extent,math.pi+.15,r.OUT/'previews'/f'{ident}-back.webp')
            catalog['items'].append({'id':ident,'sex':row['sex'],'category':row['part'],'title':r.CATEGORIES[row['part']],
              'collection':row['collection'],'collectionLabel':r.collection_label(row['collection']),'index':row['index'],
              'file':row['path'].split('/')[-1],'textureCount':len(variations),'textureFile':selected['path'].split('/')[-1],
              'triangles':triangles,'image':f'previews/{ident}.webp','back':f'previews/{ident}-back.webp'})
            recovered.append(entry);print('RECOVERED',row,selected['variant'],flush=True);break
        except ValueError:pass
        finally:
            r.texgroups[key]=variations
            for piece in pieces:
                for obj in piece:obj.release()
            pieces=[]
    if entry not in recovered:entry['reason']='all diffuse variations invisible'
report['skipped']=[e for e in report['skipped'] if e not in recovered]
report['rendered']+=len(recovered);report['previewImages']=report['rendered']*2
report['counts']=dict(collections.Counter(i['sex']+'_'+i['category'] for i in catalog['items'] if i['category'] in ('jbib','teef')))
report['catalogTotal']=len(catalog['items'])
report['recoveredWithAlternateDiffuse']=len(recovered)
reportpath.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
temp=catalogpath.with_suffix('.tmp');temp.write_text(json.dumps(catalog,ensure_ascii=False),encoding='utf-8');temp.replace(catalogpath)
print('RECOVERY_DONE',len(recovered),'catalogTotal',len(catalog['items']),flush=True)
