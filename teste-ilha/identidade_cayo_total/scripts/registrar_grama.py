from common import *
import copy,collections
from szio.gta5 import *
from szio.gta5.archetypes import ArchetypeAssetType
S=O/'stream';target=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
rows=(R/'laboratorio_fivem/work/assets_index.txt').read_text().splitlines();index={Path(q.split('|')[-1]).name:q for q in rows};archives={}
def extract(name):
    q=index.get(name)
    if not q:return None
    parts=q.split('|');key='|'.join(parts[:-1])
    if key not in archives:
        a=open_rpf(G/parts[0])
        for part in parts[1:-1]:a=a.open_nested(part)
        archives[key]=a
    return archives[key].read_bytes(parts[-1])
types={}
for name in ['v_proc1','v_proc2','v_proc3']:
    data=extract(name+'.ytyp')
    if data:
        path=O/'fontes'/(name+'.ytyp');path.write_bytes(data)
        for t in try_load_asset(path).archetypes:types[str(t.name)]=t
grass=read(O/'dados/rasteira.json');nature=try_load_asset(S/'natureza_integrada.ytyp');aliases={}
for name in grass['source_counts']:
    if name.startswith('h4_'):continue
    t=copy.deepcopy(types[name]);alias='ni_inst_'+name;aliases[name]=alias;t.name=alias;t.asset_name=alias;t.drawable_dictionary='';t.physics_dictionary='';t.asset_type=ArchetypeAssetType.DRAWABLE
    data=extract(name+'.ydr');assert data,name
    (S/(alias+'.ydr')).write_bytes(data)
    for suffix in ['', '+hi']:
        filename=str(t.texture_dictionary)+suffix+'.ytd';data=extract(filename)
        if data:(S/filename).write_bytes(data)
    nature.archetypes=[a for a in nature.archetypes if str(a.name)!=alias]+[t]
save_asset(nature,target,S,'natureza_integrada')
for path in S.glob('ni_rasteira_*.ymap'):
    a=try_load_asset(path)
    for batch in a.grass_instance_lists:
        old=str(batch.archetype_name)
        if old in aliases:batch.archetype_name=aliases[old]
    save_asset(a,target,S,path.stem)
grass['alias_map']=aliases;write(O/'dados/rasteira.json',grass)
print('GRASS_REGISTERED',len(aliases),flush=True)
