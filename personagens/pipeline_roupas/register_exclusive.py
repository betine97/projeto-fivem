"""Register a reviewed and already installed variation in the wardrobe tablet.

This explicit publication step touches only the custom manifest and preview
files. It never approves a variant, overwrites a native catalog or edits tags.
"""
import argparse
import re
import shutil
from pathlib import Path
import pipeline as p


def register(job, title=None, resource_name=None):
    job, data = p.load_job(job)
    if not data['review']['positions'] or not data['review']['appearance']:
        raise ValueError('Inspect the variation before registering it.')
    package = p.read(job/'qa/package.json')
    if package['status']!='addon_packaged' or not package['metadata']['round_trip_verified']:
        raise ValueError('A validated addon package is required.')
    resource_name = resource_name or 'cidade_'+data['name']
    if not re.fullmatch(r'[a-z][a-z0-9_]+',resource_name):
        raise ValueError('Invalid resource name.')
    resource = p.ROOT/'server-data/resources'/resource_name
    for name,sha in package['files'].items():
        if not (resource/name).is_file() or p.digest(resource/name)!=sha:
            raise ValueError('Installed package differs: '+name)
    base, source, _ = p.cached(data['base_id'])
    if p.digest(base/'base.json')!=package['base_manifest_sha256']:
        raise ValueError('Source manifest changed.')
    item=dict(source['item'])
    if item['category'] not in ('jbib','lowr') or item['sex']!='male':
        raise ValueError('A validated wardrobe compatibility profile is required.')
    metadata=package['metadata']
    if metadata['component']!=({'jbib':11,'lowr':4}[item['category']]):
        raise ValueError('Collection component differs from the base.')
    item.update(id='exclusive-'+data['name'],title=title or data.get('display_title',data['name']),
                exclusive=True,sourceId=data['base_id'],resource=resource_name,
                collection=metadata['collection'],collectionLabel='Exclusivas da cidade',
                index=0,textureIndex=0,textureCount=1)
    item['file']=next((resource/'stream').glob('*.ydd')).name.split('^')[1]
    item['textureFile']=next((resource/'stream').glob('*.ytd')).name.split('^')[1]
    if item['category']=='jbib':item['compatibleArmsIndex']=0
    acervo=p.ROOT/'server-data/resources/cidade_acervo'
    for view,key in [('front','image'),('back','back')]:
        path=job/'qa'/f'{view}.png'
        if not path.is_file():raise ValueError('Missing rendered preview: '+view)
        filename=item['id']+('-back' if view=='back' else '')+'.png'
        shutil.copy2(path,acervo/'ui/previews'/filename)
        item[key]='previews/'+filename
    manifest=acervo/'exclusives.json'
    saved=p.read(manifest) if manifest.exists() else {'items':[]}
    saved['items']=[i for i in saved['items'] if i['id']!=item['id']]+[item]
    p.write(manifest,saved)
    p.write(job/'qa/wardrobe.json',{'item':item,'base_preserved':True,
            'user_tags_modified':False,'server_reload_required':True,'web_reload_required':True,
            'in_game_verified':data['review']['in_game']})
    return item


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--job',required=True)
    parser.add_argument('--title')
    parser.add_argument('--resource')
    args=parser.parse_args()
    print(register(args.job,args.title,args.resource))
