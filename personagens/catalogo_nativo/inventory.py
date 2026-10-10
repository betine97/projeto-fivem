"""Read-only inventory of Freemode assets in local GTA archives."""
import sys,re,json,csv,collections
from pathlib import Path
import xml.etree.ElementTree as ET
sys.path.insert(0,r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'laboratorio_fivem/work/pydeps'))
from szio.rpf import open_rpf

GAME=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V')
CACHE=Path(r'C:\Users\erons\AppData\Local\FiveM\FiveM.app\data\game-storage')
OUT=Path(__file__).resolve().parent
MODELS={};TEXTURES={};ERRORS=[];SCANNED=[]
PAT=re.compile(r'^(?P<part>(?:p_)?[a-z]+)_(?P<num>\d+)(?:_[a-z]+)?\.ydd$',re.I)
TPAT=re.compile(r'^(?P<part>(?:p_)?[a-z]+)_diff_(?P<num>\d+)_(?P<variant>.+)\.ytd$',re.I)

def walk(archive,origin,path='',depth=0):
    for name in archive.list_dir(path):
        full=(path+'/' if path else '')+name
        if archive.is_dir(full):
            walk(archive,origin,full,depth)
        elif name.lower().endswith('.rpf') and depth<5:
            # Avoid unrelated nested vehicle, audio, map and texture archives.
            if not any(s in (origin+'/'+full).lower() for s in ['cdimages','dlcpacks','patch','streamedped','pedprops']):continue
            try:
                nested=archive.open_nested(full)
                walk(nested,origin+'!/'+full,'',depth+1)
                nested.close()
            except Exception as e:ERRORS.append({'archive':origin+'!/'+full,'error':str(e)})
        elif name.lower().endswith(('.ydd','.ytd')):
            entire=origin+'!/'+full
            folders=re.findall(r'mp_[mf]_freemode_01[^/!]*',entire.lower())
            if not folders:continue
            collection=folders[-1]
            # Collection directory identifies the ped; filenames may include ^.
            if collection.endswith(('.ydd','.ytd')):collection=collection.split('^')[0]
            clean=name.split('^')[-1].lower()
            match=PAT.match(clean);texture=TPAT.match(clean)
            if not match and not texture:continue
            match=match or texture
            part=match['part'];num=int(match['num']);sex='male' if collection.startswith('mp_m_') else 'female'
            key=(sex,collection,part,num)
            if texture:
                key=key+(texture['variant'],)
                TEXTURES[key]={'sex':sex,'collection':collection,'part':part,'index':num,'variant':texture['variant'],'path':entire}
            else:
                MODELS[key]={'sex':sex,'collection':collection,'part':part,'index':num,'path':entire}

def run():
    # The cached update archive belongs to the locally active FiveM build.
    updates=list(CACHE.glob('update+update.rpf_*'))
    assert len(updates)==1, 'Ambiguous cached build; choose its update.rpf explicitly'
    update=open_rpf(updates[0],filename='update.rpf')
    dlcxml=update.read_bytes('common/data/dlclist.xml')
    (OUT/'active_dlclist.xml').write_bytes(dlcxml)
    dlcs=[e.text.strip().replace('\\','/') for e in ET.fromstring(dlcxml).iter() if e.tag.lower()=='item' and e.text]
    print('ACTIVE_DLC_LIST',len(dlcs),flush=True)
    archives=[('base',GAME/'x64v.rpf')]
    legacy=open_rpf(GAME/'x64w.rpf')
    for dlc in dlcs:
        match=re.search(r'dlcpacks:?/([^/]+)',dlc,re.I)
        if not match:continue
        folder=match[1].lower()
        installed=GAME/'update/x64/dlcpacks'/folder/'dlc.rpf'
        if installed.exists():archives.append((folder,installed))
        elif legacy.exists('dlcpacks/'+folder+'/dlc.rpf'):
            nested=legacy.open_nested('dlcpacks/'+folder+'/dlc.rpf')
            walk(nested,'x64w.rpf!/'+folder);nested.close();SCANNED.append(folder)
        else:ERRORS.append({'archive':folder,'error':'Not installed'})
    # Scan base and DLCs, then update overrides last to deduplicate patched files.
    for label,path in archives:
        try:
            a=open_rpf(path);walk(a,label);a.close();SCANNED.append(label)
        except Exception as e:ERRORS.append({'archive':str(path),'error':str(e)})
    walk(update,'update.rpf');update.close();legacy.close()
    summary={}
    for sex in ['male','female']:
        parts=sorted({k[2] for k in MODELS if k[0]==sex})
        summary[sex]={p:{'drawable_indices':sum(k[0]==sex and k[2]==p for k in MODELS),'diffuse_files':sum(k[0]==sex and k[2]==p for k in TEXTURES)} for p in parts}
    result={'scope':'Freemode assets in installed DLC archives referenced by cached FiveM update dlclist; not runtime selectable counts or unique silhouettes','server_build':3258,'cached_update':str(updates[0]),'scanned':SCANNED,'errors':ERRORS,'summary':summary,'models':list(MODELS.values()),'textures':list(TEXTURES.values())}
    (OUT/'inventory.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    with (OUT/'resumo.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(['personagem','categoria','modelos_indices','arquivos_textura'])
        for sex,parts in summary.items():
            for p,c in parts.items():w.writerow([sex,p,c['drawable_indices'],c['diffuse_files']])
    print(json.dumps({'summary':summary,'errors':ERRORS,'scanned_count':len(SCANNED)},indent=2),flush=True)

if __name__=='__main__':run()
