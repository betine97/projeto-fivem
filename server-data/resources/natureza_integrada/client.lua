local resource=GetCurrentResourceName()
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
