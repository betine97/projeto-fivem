local resource=GetCurrentResourceName()
local habitats=json.decode(LoadResourceFile(resource,'habitats.json'))
local animals,cooldowns={},{}
local function remove(key)
    local a=animals[key];if a and DoesEntityExist(a.ped) then DeleteEntity(a.ped) end;animals[key]=nil
end
local function players()
    local result={}
    for _,id in ipairs(GetPlayers()) do
        local p=GetPlayerPed(id)
        if p~=0 and GetPlayerRoutingBucket(id)==0 and GetEntityHealth(p)>0 then result[#result+1]={id=tonumber(id),ped=p,pos=GetEntityCoords(p)} end
    end
    return result
end
local function nearest(list,pos)
    local best,d=nil,math.huge
    for _,p in ipairs(list) do local n=#(p.pos-pos);if n<d then best=p;d=n end end
    return best,d
end
CreateThread(function()
    while true do
        Wait(1500)
        local people=players();local changed=false;local count=0
        for key,a in pairs(animals) do
            if not DoesEntityExist(a.ped) or GetEntityHealth(a.ped)<=0 then
                remove(key);cooldowns[key]=GetGameTimer()+600000;changed=true
            else
                local _,d=nearest(people,GetEntityCoords(a.ped))
                if d>FaunaPolicy.removeDistance then remove(key);changed=true else count=count+1 end
            end
        end
        for _,h in ipairs(habitats) do
            for index,p in ipairs(h.points) do
                local key=h.id..':'..index
                local _,d=nearest(people,vector3(p[1],p[2],p[3]))
                if not animals[key] and count<FaunaPolicy.maxAnimals and d<FaunaPolicy.spawnDistance and (cooldowns[key] or 0)<GetGameTimer() then
                    local model=h.species=='onca_parda' and 'a_c_mtlion' or 'a_c_chimp'
                    local ped=CreatePed(28,GetHashKey(model),p[1],p[2],p[3]+.4,0,true,true)
                    if ped~=0 then
                        SetEntityOrphanMode(ped,2);SetEntityRoutingBucket(ped,0)
                        animals[key]={ped=ped,group=h.id,species=h.species,home=p,mode='roam'};count=count+1;changed=true
                    end
                end
            end
        end
        local packet={}
        for key,a in pairs(animals) do
            local pos=GetEntityCoords(a.ped);local target,d=nearest(people,pos);local members=0
            for _,other in pairs(animals) do
                if other.group==a.group and GetEntityHealth(other.ped)>0 and #(GetEntityCoords(other.ped)-pos)<28 then members=members+1 end
            end
            local home=vector3(a.home[1],a.home[2],a.home[3])
            a.mode=target and FaunaPolicy.behavior(a.species,members,d,math.abs(pos.z-target.pos.z),a.mode=='attack') or 'roam'
            if #(pos-home)>65 then a.mode='return' end
            packet[#packet+1]={id=NetworkGetNetworkIdFromEntity(a.ped),species=a.species,mode=a.mode,target=target and target.id or nil,home=a.home}
        end
        -- Server owns population and target decisions; the entity owner executes AI.
        TriggerClientEvent('fauna_ilha:update',-1,packet)
        if changed then print(('[Fauna Ilha] animais ativos=%d, limite=%d'):format(#packet,FaunaPolicy.maxAnimals)) end
    end
end)
AddEventHandler('onResourceStop',function(name)if name==resource then for key in pairs(animals) do remove(key) end end end)
