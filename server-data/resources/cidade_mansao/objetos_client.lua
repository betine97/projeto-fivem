local resource=GetCurrentResourceName()
local M=CidadeObjetos
local catalog=json.decode(LoadResourceFile(resource,'objetos_catalogo.json'))
local definitions,poses,owners,entities,byEntity,hidden,requests={},{},{},{},{},{},{}
local targets={}
local protected={}
for _,name in ipairs(catalog.protectedModels) do protected[GetHashKey(name)]=true end
local running,ready,enabled,pending=true,false,false,false
local selected,candidate,requestAt,lastScan,lastSend,lastOutline=nil,nil,0,0,0,nil
local function notice(msg)
    print('[OBJETOS] '..msg)
    BeginTextCommandThefeedPost('STRING'); AddTextComponentSubstringPlayerName(msg); EndTextCommandThefeedPostTicker(false,false)
end
local function array(v) return {v.x,v.y,v.z} end
local function hash(d) return type(d.model)=='number' and d.model or GetHashKey(d.model) end
local function setPose(id,p)
    local e=entities[id]; if not e or not DoesEntityExist(e) then return end
    local d=definitions[id]; local f,r,u=M.basis(d,p.h); local s=d.s
    -- Set coordinates before the matrix: the ordinary transform native resets scale.
    SetEntityCoordsNoOffset(e,p.p[1],p.p[2],p.p[3],false,false,false)
    SetEntityMatrix(e,f[1]*s[2],f[2]*s[2],f[3]*s[2],r[1]*s[1],r[2]*s[1],r[3]*s[1],u[1]*s[3],u[2]*s[3],u[3]*s[3],p.p[1],p.p[2],p.p[3])
end
local function collision(id)
    local e=entities[id]; if e and DoesEntityExist(e) then SetEntityCollision(e,not owners[id],true) end
end
local function remove(id)
    local e=entities[id]; if e then
        byEntity[e]=nil; if DoesEntityExist(e) then SetEntityDrawOutline(e,false); DeleteEntity(e) end
    end
    entities[id],targets[id],requests[id]=nil,nil,nil
end
local function hideOriginal(d)
    if not d.generic or hidden[d.id] then return end
    local c=M.center(d,d)
    CreateModelHideExcludingScriptObjects(c[1],c[2],c[3],0.03,hash(d),true)
    hidden[d.id]=c
end
local function stopSelection()
    if selected then
        local e=entities[selected.id]; if e then SetEntityDrawOutline(e,false) end
    end
    selected,pending=nil,false
end
local function finish(commit)
    if not selected or pending then return end
    pending=true
    TriggerServerEvent('cidade:objetos:finish',selected.id,selected.token,selected.pose,commit==true)
end
RegisterNetEvent('cidade:objetos:notice',function(msg) if source==65535 and type(msg)=='string' then notice(msg) end end)
RegisterNetEvent('cidade:objetos:mode',function(active)
    if source~=65535 then return end
    enabled=active==true; if not enabled then stopSelection(); candidate=nil end
    if enabled then notice('Editor ligado. Aproxime-se da peca e pressione CAPS. objetosajuda mostra os controles.')
    else notice('Editor de objetos desligado.') end
end)
RegisterNetEvent('cidade:objetos:snapshot',function(ds,ps,os)
    if source~=65535 or type(ds)~='table' or type(ps)~='table' then return end
    definitions,poses,owners=ds,ps,os or {}; ready=true
    for id in pairs(entities) do if not definitions[id] then remove(id) else setPose(id,poses[id]); collision(id) end end
end)
RegisterNetEvent('cidade:objetos:definition',function(d)
    if source~=65535 or type(d)~='table' then return end
    definitions[d.id],poses[d.id]=d,M.copy(d)
end)
RegisterNetEvent('cidade:objetos:state',function(id,p,owner)
    if source~=65535 or not definitions[id] or not M.pose(p) then return end
    owners[id]=owner or nil
    if selected and selected.id==id then
        if owner~=GetPlayerServerId(PlayerId()) then
            stopSelection(); poses[id]=M.copy(p); targets[id]=nil; setPose(id,p)
        end
    else
        if owner and entities[id] then
            targets[id]={from=M.copy(poses[id]),to=M.copy(p),started=GetGameTimer()}
        else poses[id]=M.copy(p); targets[id]=nil; setPose(id,p) end
    end
    collision(id)
end)
RegisterNetEvent('cidade:objetos:locked',function(id,token,p)
    if source~=65535 or not definitions[id] then return end
    if not enabled then TriggerServerEvent('cidade:objetos:finish',id,token,p,false); return end
    pending=false
    selected={id=id,token=token,pose=M.copy(p),ped=array(GetEntityCoords(PlayerPedId())),seq=0}
    poses[id]=M.copy(p); targets[id]=nil; setPose(id,p)
    notice(definitions[id].label..' selecionado. Ande para arrastar; CAPS salva, BACKSPACE cancela.')
end)
RegisterCommand('editarobjetos',function() TriggerServerEvent('cidade:objetos:toggle',not enabled) end,false)
RegisterCommand('moverobjetos',function() ExecuteCommand('editarobjetos') end,false)
RegisterCommand('objetosajuda',function()
    notice('F8: editarobjetos | CAPS: pegar/salvar | setas esquerda/direita: girar | PAGEUP/PAGEDOWN: altura | HOME: origem | BACKSPACE: cancelar.')
    print('[OBJETOS] Movimentos sao salvos para todos. Modelos unidos, como mesa e cadeiras, movem como um conjunto. Portas controladas e estrutura fixa sao preservadas.')
end,false)
-- Targeted rendering diagnostics; no per-frame logs and no world-wide changes.
RegisterCommand('tapeteursodebug',function()
    for id,d in pairs(definitions) do
        if d.model=='mansao_tapete_urso' then
            local e=entities[id]; local exists=e and DoesEntityExist(e)
            local info={id=id,loaded=HasModelLoaded(hash(d)),entity=exists and e or 0,pose=poses[id],stableRender=d.stableRender==true}
            if exists then
                info.distance=M.distance(array(GetEntityCoords(PlayerPedId())),M.center(d,poses[id]))
                info.visible=IsEntityVisible(e);info.onScreen=IsEntityOnScreen(e);info.occluded=IsEntityOccluded(e);info.alpha=GetEntityAlpha(e)
                local lo,hi=GetModelDimensions(hash(d));info.modelLo=array(lo);info.modelHi=array(hi)
            end
            print('[TAPETE_URSO] '..json.encode(info))
        end
    end
end,false)
RegisterCommand('objetosdebug',function()
    local count=0; for _ in pairs(entities) do count=count+1 end
    print(('[OBJETOS] pronto=%s modo=%s objetos=%d selecionado=%s candidato=%s'):format(tostring(ready),tostring(enabled),count,selected and selected.id or '-',candidate and candidate.id or '-'))
    if selected then print(json.encode({id=selected.id,pose=selected.pose,model=definitions[selected.id].model})) end
end,false)
local function genericDescriptor(e)
    local model=GetEntityModel(e)
    if protected[model] or IsEntityAMissionEntity(e) or NetworkGetEntityIsNetworked(e) then return end
    local lo,hi=GetModelDimensions(model); local f,r,u,p=GetEntityMatrix(e)
    local function unit(v) local length=#v; if length<0.05 then return end; return {v.x/length,v.y/length,v.z/length},length end
    local fu,fs=unit(f); local ru,rs=unit(r); local uu,us=unit(u)
    if not fu or not ru or not uu then return end
    local d={model=model,p=array(p),h=0,lo=array(lo),hi=array(hi),s={rs,fs,us},basis={fu,ru,uu}}
    if not M.generic(d,protected) then return end
    d.id=M.genericId(d); return d
end
local function pick()
    local ped=PlayerPedId(); local p=array(GetEntityCoords(ped)); local cam=GetGameplayCamCoord(); local rot=GetGameplayCamRot(2)
    local z,x=math.rad(rot.z),math.rad(rot.x)
    local dir=vector3(-math.sin(z)*math.cos(x),math.cos(z)*math.cos(x),math.sin(x))
    local hitPoint=cam+dir*15
    local ray=StartExpensiveSynchronousShapeTestLosProbe(cam.x,cam.y,cam.z,hitPoint.x,hitPoint.y,hitPoint.z,17,ped,7)
    local _,hit,_,_,hitEntity=GetShapeTestResult(ray)
    local best,bestScore=nil,math.huge
    for _,e in ipairs(GetGamePool('CObject')) do
        if DoesEntityExist(e) then
            local id=byEntity[e]
            local nearby=id or M.distance(p,array(GetEntityCoords(e)))<20
            local d=nearby and (id and definitions[id] or genericDescriptor(e))
            local t=id and poses[id] or d
            if d and t and not owners[d.id] then
                local distance=M.surfaceDistance(d,t,p)
                if distance<=3.2 then
                    local c=M.center(d,t); local delta=vector3(c[1],c[2],c[3])-cam
                    local facing=#delta<0.1 or (delta.x*dir.x+delta.y*dir.y+delta.z*dir.z)/#delta>0.10
                    local score=distance
                    if (hit==1 or hit==true) and hitEntity==e then score=score-5
                    elseif not facing or not IsEntityOnScreen(e) then score=math.huge
                    else
                        -- Avoid selecting a prop through a room wall. Aim at the nearest
                        -- bounding surface, not at a remote pivot of a combined model.
                        local eyes=GetPedBoneCoords(ped,31086,0,0,0); local closest=M.closest(d,t,array(eyes))
                        local test=StartExpensiveSynchronousShapeTestLosProbe(eyes.x,eyes.y,eyes.z,closest[1],closest[2],closest[3],17,ped,7)
                        local _,blocked,_,_,obstacle=GetShapeTestResult(test)
                        if (blocked==1 or blocked==true) and obstacle~=e then score=math.huge end
                    end
                    if score<bestScore then bestScore=score; best={id=d.id,entity=e,generic=id and nil or d,label=d.label or 'Objeto do mapa'} end
                end
            end
        end
    end
    return best
end
local function caps()
    if not enabled or pending or not ready then return end
    if selected then finish(true); return end
    candidate=pick()
    if not candidate then notice('Nenhum objeto movel ao alcance. Aproxime-se e olhe para a peca.'); return end
    pending=true; requestAt=GetGameTimer()
    TriggerServerEvent('cidade:objetos:lock',candidate.id,candidate.generic)
end
RegisterCommand('+cidade_objeto_caps',caps,false)
RegisterCommand('-cidade_objeto_caps',function() end,false)
RegisterKeyMapping('+cidade_objeto_caps','Editor ADM: selecionar/confirmar objeto','keyboard','CAPITAL')
local keys={left=false,right=false,up=false,down=false}
for _,k in ipairs({{'left','LEFT'},{'right','RIGHT'},{'up','PRIOR'},{'down','NEXT'}}) do
    local name,key=k[1],k[2]
    RegisterCommand('+cidade_objeto_'..name,function() keys[name]=true end,false)
    RegisterCommand('-cidade_objeto_'..name,function() keys[name]=false end,false)
    RegisterKeyMapping('+cidade_objeto_'..name,'Editor ADM: '..name,'keyboard',key)
end
RegisterCommand('+cidade_objeto_cancel',function() if enabled then finish(false) end end,false)
RegisterCommand('-cidade_objeto_cancel',function() end,false)
RegisterKeyMapping('+cidade_objeto_cancel','Editor ADM: cancelar movimento','keyboard','BACK')
RegisterCommand('+cidade_objeto_home',function()
    if selected and not pending then
        selected.pose=M.copy(definitions[selected.id]); selected.ped=array(GetEntityCoords(PlayerPedId())); poses[selected.id]=selected.pose; setPose(selected.id,selected.pose)
    end
end,false)
RegisterCommand('-cidade_objeto_home',function() end,false)
RegisterKeyMapping('+cidade_objeto_home','Editor ADM: voltar a origem','keyboard','HOME')
CreateThread(function()
    while running do
        if ready then
            local p=array(GetEntityCoords(PlayerPedId())); local now=GetGameTimer()
            for id,d in pairs(definitions) do
                local distance=M.distance(p,M.center(d,poses[id]))
                local originNear=d.generic and M.distance(p,M.center(d,d))<150
                if originNear then hideOriginal(d) end
                if distance<130 then
                    hideOriginal(d)
                    if not entities[id] and now>=(requests[id] or 0) then
                        local model=hash(d); RequestModel(model)
                        if HasModelLoaded(model) then
                            local t=poses[id]; local e=CreateObjectNoOffset(model,t.p[1],t.p[2],t.p[3],false,false,false)
                            if e~=0 then
                                entities[id],byEntity[e]=e,id; SetEntityAsMissionEntity(e,true,true); FreezeEntityPosition(e,true)
                                SetEntityLodDist(e,math.floor(math.max(120,d.lod or 120))); setPose(id,t); collision(id)
                                if d.stableRender then SetEntityAlwaysPrerender(e,true) end
                            else requests[id]=now+5000; print('[OBJETOS] Falha ao criar '..id) end
                            SetModelAsNoLongerNeeded(model)
                        end
                    end
                elseif distance>160 and entities[id] and not (selected and selected.id==id) then remove(id) end
            end
        end
        Wait(250)
    end
end)
local function outline(e)
    if lastOutline and lastOutline~=e and DoesEntityExist(lastOutline) then SetEntityDrawOutline(lastOutline,false) end
    lastOutline=e
    if e and DoesEntityExist(e) then SetEntityDrawOutlineColor(40,210,165,230); SetEntityDrawOutline(e,true) end
end
local function help(msg)
    BeginTextCommandDisplayHelp('STRING'); AddTextComponentSubstringPlayerName(msg); EndTextCommandDisplayHelp(0,false,false,-1)
end
CreateThread(function()
    TriggerServerEvent('cidade:objetos:snapshotRequest')
    while running do
        local now=GetGameTimer(); local wait=250
        if not ready and now-lastScan>2500 then lastScan=now; TriggerServerEvent('cidade:objetos:snapshotRequest') end
        for id,t in pairs(targets) do
            local a=math.min(1,(now-t.started)/100); local p={p={},h=0}
            for i=1,3 do p.p[i]=t.from.p[i]+(t.to.p[i]-t.from.p[i])*a end
            local delta=(t.to.h-t.from.h+180)%360-180; p.h=t.from.h+delta*a
            poses[id]=p; setPose(id,p); if a>=1 then targets[id]=nil end
            wait=0
        end
        if enabled then
            wait=0; local ped=PlayerPedId()
            DisableControlAction(0,24,true); DisableControlAction(0,25,true); DisableControlAction(0,37,true)
            DisableControlAction(0,171,true); DisableControlAction(0,217,true)
            if pending and not selected and now-requestAt>3000 then pending=false end
            if selected then
                DisableControlAction(0,174,true); DisableControlAction(0,175,true)
                if IsEntityDead(ped) or IsPedInAnyVehicle(ped,false) then finish(false)
                elseif not pending then
                    local current=array(GetEntityCoords(ped)); local delta=M.distance(current,selected.ped)
                    if delta>10 then finish(false); notice('Teleporte detectado; movimento cancelado.')
                    else
                        local p=selected.pose
                        for i=1,3 do p.p[i]=p.p[i]+current[i]-selected.ped[i] end
                        selected.ped=current
                        local dt=math.min(GetFrameTime(),0.05)
                        local angle=((keys.left and 1 or 0)-(keys.right and 1 or 0))*45*dt
                        if angle~=0 then p=M.turn(definitions[selected.id],p,angle) end
                        p.p[3]=p.p[3]+((keys.up and 1 or 0)-(keys.down and 1 or 0))*0.7*dt
                        selected.pose=p; poses[selected.id]=p; setPose(selected.id,p)
                        if now-lastSend>100 then selected.seq=selected.seq+1; lastSend=now; TriggerServerEvent('cidade:objetos:update',selected.id,selected.token,selected.seq,p) end
                    end
                end
                outline(entities[selected.id]); help('~g~'..definitions[selected.id].label..'~s~ | CAPS salva | BACKSPACE cancela~n~Setas giram | PAGEUP / PAGEDOWN altura | HOME origem')
            else
                if now-lastScan>250 then lastScan=now; candidate=pick() end
                outline(candidate and candidate.entity)
                help(candidate and ('CAPS: mover ~g~'..candidate.label) or 'Editor ADM | aproxime-se e olhe para um objeto | F8: editarobjetos desliga')
            end
        elseif lastOutline then outline(nil) end
        Wait(wait)
    end
end)
AddEventHandler('onResourceStop',function(name)
    if name~=resource then return end
    running=false; outline(nil)
    for id in pairs(entities) do remove(id) end
    for id,c in pairs(hidden) do RemoveModelHide(c[1],c[2],c[3],0.03,hash(definitions[id]),false) end
end)
