-- Independent visual objects allow secondary motion without altering the ped skeleton.
local definitions = json.decode(LoadResourceFile(GetCurrentResourceName(),'data/ct_straps.json'))
local groups, ready = {}, false
local function destroy(group)
    for _,part in ipairs(group.parts) do
        if DoesEntityExist(part.object) then DeleteEntity(part.object) end
    end
end
local function tactical(ped)
    if not DoesEntityExist(ped) or GetEntityModel(ped)~=joaat('mp_m_freemode_01') then return false end
    local collection=GetPedDrawableVariationCollectionName(ped,4)
    return type(collection)=='string' and collection:lower():find('male_heist',1,true)~=nil
        and GetPedDrawableVariationCollectionLocalIndex(ped,4)==6 and GetPedTextureVariation(ped,4)==0
end
CreateThread(function()
    for _,def in ipairs(definitions) do RequestModel(joaat(def.model)) end
    local deadline=GetGameTimer()+10000
    repeat
        ready=true
        for _,def in ipairs(definitions) do if not HasModelLoaded(joaat(def.model)) then ready=false end end
        if not ready then Wait(50) end
    until ready or GetGameTimer()>deadline
    if not ready then print('[Roupas] Nao foi possivel carregar as fitas taticas. Reconecte apos reiniciar o recurso.');return end
    while true do
        local seen={};local origin=GetEntityCoords(PlayerPedId())
        for _,player in ipairs(GetActivePlayers()) do
            local ped=GetPlayerPed(player)
            if tactical(ped) and #(GetEntityCoords(ped)-origin)<35 then
                seen[ped]=true
                if not groups[ped] then
                    local group={parts={},velocity=GetEntityVelocity(ped),phase=player*.9}
                    for _,def in ipairs(definitions) do
                        local pos=GetEntityCoords(ped)
                        local object=CreateObjectNoOffset(joaat(def.model),pos.x,pos.y,pos.z,false,false,false)
                        if object~=0 then
                            SetEntityAsMissionEntity(object,true,true)
                            SetEntityCollision(object,false,false);FreezeEntityPosition(object,true)
                            SetEntityVisible(object,false,false)
                            group.parts[#group.parts+1]={object=object,def=def,x=0,y=0,vx=0,vy=0}
                        end
                    end
                    groups[ped]=group
                end
            end
        end
        for ped,group in pairs(groups) do
            if not seen[ped] then destroy(group);groups[ped]=nil end
        end
        Wait(500)
    end
end)
local function clamp(v,a,b)return math.max(a,math.min(b,v)) end
local function bonePoint(ped,bone,offset)
    return GetPedBoneCoords(ped,bone,offset[1],offset[2],offset[3])
end
CreateThread(function()
    while true do
        if next(groups)==nil then Wait(150) else
            local dt=math.min(GetFrameTime(),.033)
            for ped,group in pairs(groups) do
                if DoesEntityExist(ped) then
                    local velocity=GetEntityVelocity(ped)
                    local acceleration=(velocity-group.velocity)/math.max(dt,.001)
                    group.velocity=velocity
                    local speed=math.min(#velocity,6)
                    group.phase=group.phase+dt*(3+speed*2.5)
                    for index,part in ipairs(group.parts) do
                        local def=part.def;local pos=bonePoint(ped,def.bone,def.offset)
                        local basis={}
                        for k,axis in ipairs(def.axes) do
                            basis[k]=bonePoint(ped,def.bone,{def.offset[1]+axis[1],def.offset[2]+axis[2],def.offset[3]+axis[3]})-pos
                        end
                        local forceX=clamp(acceleration.x*basis[1].x+acceleration.y*basis[1].y,-10,10)
                        local forceY=clamp(acceleration.x*basis[2].x+acceleration.y*basis[2].y,-10,10)
                        local phase=group.phase+index*.7
                        local targetX=clamp(-forceY*.012+math.sin(phase)*speed*.022,-.24,.24)
                        local targetY=clamp(forceX*.012+math.cos(phase*.8)*speed*.012,-.16,.16)
                        -- Damped spring: inertia settles gradually when the ped stops.
                        part.vx=part.vx+((targetX-part.x)*45-part.vx*10)*dt
                        part.vy=part.vy+((targetY-part.y)*45-part.vy*10)*dt
                        part.x=clamp(part.x+part.vx*dt,-.28,.28)
                        part.y=clamp(part.y+part.vy*dt,-.20,.20)
                        local cx,sx,cy,sy=math.cos(part.x),math.sin(part.x),math.cos(part.y),math.sin(part.y)
                        local right=basis[1]*cy-basis[3]*sy
                        local forward=basis[1]*(sy*sx)+basis[2]*cx+basis[3]*(cy*sx)
                        local up=basis[1]*(sy*cx)-basis[2]*sx+basis[3]*(cy*cx)
                        SetEntityMatrix(part.object,forward.x,forward.y,forward.z,right.x,right.y,right.z,up.x,up.y,up.z,pos.x,pos.y,pos.z)
                        SetEntityVisible(part.object,not IsPedInAnyVehicle(ped,false) and not IsEntityDead(ped),false)
                    end
                end
            end
            Wait(0)
        end
    end
end)
AddEventHandler('onResourceStop',function(resource)
    if resource~=GetCurrentResourceName() then return end
    for _,group in pairs(groups) do destroy(group) end
    for _,def in ipairs(definitions) do SetModelAsNoLongerNeeded(joaat(def.model)) end
end)
