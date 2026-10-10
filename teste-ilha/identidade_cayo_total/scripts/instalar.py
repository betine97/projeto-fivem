from common import *
import shutil,datetime,collections,math
from szio.gta5 import *
plan=read(O/'dados/plano.json');nature=read(O/'dados/implantacao.json');grass=read(O/'dados/rasteira.json');soil=read(O/'dados/solo.json')
assert read(O/'dados/validacao_codewalker.json')['passed']
assert read(O/'dados/validacao_rasteira_distante.json')['passed']
assert read(O/'dados/validacao_limites_render.json')['passed']
assert read(O/'dados/validacao_streaming.json')['passed']
assert read(O/'dados/validacao_orcamento_render.json')['passed']
assert plan['cayo_fraction']==1.0 and len(soil['sectors'])==43
for alias,digest in nature['original_drawables_sha256'].items():assert sha(O/'stream'/(alias+'.ydr'))==digest,alias
qs=read(O/'dados/posicoes.json');counts=collections.Counter(q['family'] for q in qs);assert dict(counts)==nature['counts']
F=dict(np.load(O/'dados/biomas.npz'));identity_float=F['identity'].astype(float);violations=[]
for q in qs:
    if q['source'].startswith('Cayo') and sample(identity_float,*q['position'][:2])<.99:violations.append(q)
assert not violations
grades=[]
for r in plan['routes']:
    points=np.asarray(r['points']);height=points[:,2] if points.shape[1]==3 else sample(z,points[:,0],points[:,1]);d=np.diff(points[:,:2],axis=0);grades.extend(abs(np.diff(height))/np.linalg.norm(d,axis=1))
assert max(grades)<.30
stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S');backup=R/'server-data/backups'/('identidade-natural-'+stamp);backup.mkdir(parents=True)
dest=R/'server-data/resources/natureza_integrada';dest.mkdir(exist_ok=True)
(dest/'stream').mkdir(exist_ok=True);(dest/'data').mkdir(exist_ok=True)
installed=[]
def copy(src,target):
    if target.exists():
        back=backup/target.relative_to(R/'server-data');back.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(target,back)
    target.parent.mkdir(exist_ok=True,parents=True);shutil.copy2(src,target);installed.append(dict(path=str(target.relative_to(R)),sha256=sha(target)))
active_maps={m['name'] for m in nature['maps']} | {m['name'] for m in grass['maps']}
for old_map in (dest/'stream').glob('ni_*.ymap'):
    if old_map.stem not in active_maps:
        assert old_map.resolve().parent==(dest/'stream').resolve()
        back=backup/old_map.relative_to(R/'server-data');back.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(old_map,back);old_map.unlink()
for src in (O/'stream').iterdir():copy(src,dest/'stream'/src.name)
for src in (O/'terreno').iterdir():copy(src,R/'server-data/resources/teste_ilha/stream'/src.name)
for src in (O/'porto_filtrado').iterdir():copy(src,R/'server-data/resources/porto_esperanca/stream'/src.name)
copy(O/'dados/water.xml',R/'server-data/resources/teste_ilha/data/water.xml')
# Check the house drawables remain untouched; only selected placement maps were filtered.
houses={p.name:sha(p) for p in (R/'server-data/resources/porto_esperanca/stream').glob('pe_estrutura*.ydr')}
road=plan['routes'][0]['points'];xx,yy,gz=road[len(road)//2];destination=dict(x=float(xx),y=float(yy),z=float(gz)+1.1,ground_z=float(gz),heading=185)
settlements=[dict(name=q['name'],x=q['center'][0]-65 if idx else 370,y=q['center'][1],z=q['center'][2]+1.15,ground_z=q['center'][2],heading=90) for idx,q in enumerate(plan['settlements'])]
groundcover=nature.get('distant_groundcover',{})
groundcover_sentinels=[str(t.name) for t in try_load_asset(O/'stream/ni_groundcover.ytyp').archetypes if str(t.name).startswith('ni_gc_far_')][:3] if groundcover else []
config=dict(revision=plan['revision'],maps=[m['name'] for m in nature['maps']]+[m['name'] for m in grass['maps']],counts=nature['counts'],grass_instances=grass['counts'],distant_canopy=nature['distant_canopy'],distant_groundcover=groundcover,cayo_area_fraction=1.0,dirt_road_length_m=plan['new_road_length_m'],destination=destination,settlements=settlements,sentinels=list(nature['alias_map'].values())+[grass.get('alias_map',{}).get(n,n) for n in grass['source_counts']]+groundcover_sentinels+[f'pe_estrutura_{i:02}' for i in range(1,11)])
write(dest/'data/config.json',config)
(dest/'fxmanifest.lua').write_text("""fx_version 'cerulean'
game 'gta5'
this_is_a_map 'yes'
author 'Minha Cidade'
description 'Identidade Cayo em toda a ilha, cidade principal e quatro vilarejos'
version '1.0.0'
dependencies { 'teste_ilha', 'cayo_vizinha', 'porto_esperanca' }
files { 'data/config.json', 'stream/natureza_integrada.ytyp', 'stream/ni_groundcover.ytyp' }
data_file 'DLC_ITYP_REQUEST' 'stream/natureza_integrada.ytyp'
data_file 'DLC_ITYP_REQUEST' 'stream/ni_groundcover.ytyp'
client_script 'client.lua'
server_script 'server.lua'
""",encoding='utf8')
(dest/'client.lua').write_text("""local resource=GetCurrentResourceName()
local cfg=json.decode(LoadResourceFile(resource,'data/config.json'))
local function requestMaps()
    for _,name in ipairs(cfg.maps) do RequestIpl(name) end
end
local function diagnostic(stage)
    local ped=PlayerPedId();local p=GetEntityCoords(ped)
    local found,height=GetGroundZFor_3dCoord(p.x,p.y,p.z+250.0,false)
    local active=0;local missing={};local lod,slod,cover=0,0,0
    for _,name in ipairs(cfg.maps) do if IsIplActive(name) then active=active+1;if name:find('ni_canopy_lod_') then lod=lod+1 elseif name:find('ni_canopy_slod_') then slod=slod+1 elseif name:find('ni_groundcover_') then cover=cover+1 end end end
    for _,name in ipairs(cfg.sentinels) do if not IsModelInCdimage(GetHashKey(name)) then missing[#missing+1]=name end end
    local camera=GetGameplayCamCoord()
    local report={revision=cfg.revision,stage=stage,position={x=p.x,y=p.y,z=p.z},camera={x=camera.x,y=camera.y,z=camera.z},ground={found=found,z=height},collision=HasCollisionLoadedAroundEntity(ped),active_maps=active,total_maps=#cfg.maps,lod_maps=lod,slod_maps=slod,groundcover_maps=cover,groundcover_patches=cfg.distant_groundcover.patches,groundcover_far_m=cfg.distant_groundcover.far_distance_m,distant_canopy=cfg.distant_canopy,missing_models=missing}
    print('[Natureza Ilha] '..json.encode(report));TriggerServerEvent('natureza_integrada:diagnostic',report)
end
RegisterCommand('naturezadiag',function() diagnostic('manual') end,false)
local function visitSettlement(index)
    requestMaps()
    local target=cfg.settlements[index]
    if target and GetResourceState('teste_ilha')=='started' then
        exports.teste_ilha:visitNatural(target)
        diagnostic('povoacao_'..index)
    end
end
RegisterCommand('cidade',function() visitSettlement(1) end,false)
for i=1,4 do
    local index=i+1
    RegisterCommand('vila'..i,function() visitSettlement(index) end,false)
end
RegisterCommand('natureza',function()
    requestMaps()
    if GetResourceState('teste_ilha')=='started' then
        exports.teste_ilha:visitNatural(cfg.destination)
        diagnostic('visita')
    end
end,false)
CreateThread(function() requestMaps();Wait(12000);diagnostic('inicio') end)
AddEventHandler('onResourceStop',function(name)
    if name~=resource then return end
    for _,imap in ipairs(cfg.maps) do RemoveIpl(imap) end
end)
""",encoding='utf8')
(dest/'server.lua').write_text("""local resource=GetCurrentResourceName()
local cfg=json.decode(LoadResourceFile(resource,'data/config.json'))
RegisterNetEvent('natureza_integrada:diagnostic',function(report)
    if type(report)~='table' then return end
    local text=json.encode(report)
    if #text>3000 then return end
    print(('[Natureza Ilha] jogador=%s %s'):format(source,text))
end)
CreateThread(function()
    print(('[Natureza Ilha] %s | mapas=%d | arvores=%d | rasteira=%d | identidade=100%%'):format(cfg.revision,#cfg.maps,cfg.counts.tree,cfg.grass_instances))
end)
""",encoding='utf8')
client=R/'server-data/resources/teste_ilha/client.lua';text=client.read_text(encoding='utf-8-sig')
if "exports('visitNatural'" not in text:
    copy(client,backup/'client_before_visit.lua')
    text+="\nexports('visitNatural',function(destination)\n    visit(destination,'Natureza nativa: Cayo integrada a ilha. F8: naturezadiag | ilha | porto',false)\nend)\n";client.write_text(text,encoding='utf8')
cfg=R/'server-data/server-ilha.cfg';text=cfg.read_text(encoding='utf-8-sig');copy(cfg,backup/'server-ilha-before.cfg')
if 'ensure natureza_integrada' not in text:text=text.replace('ensure porto_esperanca','ensure porto_esperanca\nensure natureza_integrada');cfg.write_text(text,encoding='utf8')
write(O/'dados/instalacao.json',dict(revision=plan['revision'],backup=str(backup),installed=installed,houses_sha256=houses,counts=dict(counts),grass_instances=grass['counts'],max_road_grade=float(max(grades)),native_source_models_unchanged=True,client_visual_verified=False))
print('NATURE_INSTALLED',len(installed),'files; backup',str(backup),flush=True)
