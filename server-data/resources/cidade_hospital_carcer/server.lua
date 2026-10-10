local cfg=json.decode(LoadResourceFile(GetCurrentResourceName(),'hospital.json'))
local states,busy={},{}
local origin=vector3(table.unpack(cfg.origin))
local function occupied(d)
    local p=origin+vector3(table.unpack(d.pos))
    for _,id in ipairs(GetPlayers()) do
        local ped=GetPlayerPed(id)
        if ped~=0 then
            local v=GetEntityCoords(ped)
            if v.x>p.x-.35 and v.x<p.x+d.width+.35 and math.abs(v.y-p.y)<.40 and v.z>p.z-.2 and v.z<p.z+d.height+.2 then return true end
        end
    end
end
RegisterNetEvent('cidade_hospital:states',function()TriggerClientEvent('cidade_hospital:snapshot',source,states) end)
RegisterNetEvent('cidade_hospital:toggle',function(id)
    local player=tonumber(source)
    if type(id)~='number' or id%1~=0 or not cfg.doors[id] then return end
    local d=cfg.doors[id];local ped=GetPlayerPed(player)
    if ped==0 or not DoesEntityExist(ped) or not IsPlayerAceAllowed(player,'cidade.admin') then return end
    local center=origin+vector3(d.pos[1]+d.width/2,d.pos[2],d.pos[3]+1)
    if #(GetEntityCoords(ped)-center)>4 then return end
    local now=GetGameTimer();if busy[id] and now<busy[id] then return end
    if states[id] and occupied(d) then TriggerClientEvent('cidade_acesso:notice',player,'Afaste-se do vao para fechar a porta.');return end
    states[id]=not states[id];busy[id]=now+750
    TriggerClientEvent('cidade_hospital:door',-1,id,states[id])
end)
