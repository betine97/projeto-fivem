-- Native locomotion owns translation and collision. No teleports, disabled
-- ped collision, gravity overrides or scripted displacement in this module.
CidadePostureMovement={active=false,pending=false,crawling=false,holdingC=false,revision='v12-rastejo-posicao-fisica'}
local M=CidadePostureMovement
local crouchPed,token=nil,0
local crouchWeapon,crouchRefresh=nil,0
local crawl,probe,fastCrouch=nil,nil,nil
local CROUCH,STRAFE,CRAWL='move_ped_crouched','move_ped_crouched_strafing','cidade_deitado_move_v11'
local FAST='cidade_agachado_move_v11'
-- A mover must advance the physical entity and retain its position when its
-- task ends. Extraction alone does not request kinematic physics or retention
-- of the exit position. Keep collision/gravity enabled (no flags 512/1024/2048).
local MOVER_FLAGS=1+4+131072+262144+524288 -- loop, reposition, force, kinematic, extraction
local crawlHistory,crawlDebug,afterCrawl={},true,nil
local function crawlTrace(event,p,data)
    if not crawlDebug or not p or not DoesEntityExist(p) then return end
    local at=GetEntityCoords(p)
    data=data or {};data.event=event;data.ms=GetGameTimer();data.revision=M.revision
    data.position={at.x,at.y,at.z};data.route=M.route
    crawlHistory[#crawlHistory+1]=data
    if #crawlHistory>80 then table.remove(crawlHistory,1) end
    print('[Rastejo] '..json.encode(data))
end
local function sampleCrawl(p)
    if not crawl or not IsEntityPlayingAnim(p,CRAWL,crawl.clip,3) then return end
    local at=GetEntityCoords(p);local now=GetGameTimer()
    local phase=GetEntityAnimCurrentTime(p,CRAWL,crawl.clip)
    local progress=(at.x-crawl.origin.x)*crawl.dx+(at.y-crawl.origin.y)*crawl.dy
    local backwards=(at.x-crawl.last.x)*crawl.dx+(at.y-crawl.last.y)*crawl.dy
    crawl.progress=progress
    if backwards<-.08 and now-crawl.sampleAt<=200 and now-crawl.warningAt>=1000 then
        crawl.warningAt=now
        crawlTrace('retorno_detectado',p,{clip=crawl.clip,phase=phase,delta=backwards,progress=progress})
    end
    if crawl.phase and phase<crawl.phase-.5 then
        crawl.cycles=crawl.cycles+1
        crawlTrace('ciclo',p,{clip=crawl.clip,cycles=crawl.cycles,progress=progress,
            cycleProgress=progress-crawl.cycleProgress,elapsed=now-crawl.issuedAt})
        crawl.cycleProgress=progress
    end
    crawl.phase=phase;crawl.last={x=at.x,y=at.y};crawl.sampleAt=now
end
local function sampleAfterCrawl(p)
    if not afterCrawl then return end
    if afterCrawl.ped~=p or not DoesEntityExist(p) then afterCrawl=nil;return end
    local now=GetGameTimer()
    if now-afterCrawl.at<250 then return end
    local at=GetEntityCoords(p)
    local delta=(at.x-afterCrawl.position.x)*afterCrawl.dx+(at.y-afterCrawl.position.y)*afterCrawl.dy
    crawlTrace(delta<-.08 and 'retorno_apos_parar' or 'posicao_apos_parar',p,
        {clip=afterCrawl.clip,delta=delta,elapsed=now-afterCrawl.at})
    afterCrawl=nil
end
local pathClear,stopFastCrouch
local function movementInput()
    -- Keyboard movement follows held keys, not a cached axis left behind by
    -- GTA's scripted animation task. Controller sticks retain analog input.
    local function held(k)return IsControlPressed(0,k) or IsDisabledControlPressed(0,k) end
    if IsUsingKeyboard(0) then
        return (held(35) and 1 or 0)-(held(34) and 1 or 0),
               (held(32) and 1 or 0)-(held(33) and 1 or 0)
    end
    return GetDisabledControlNormal(0,30),-GetDisabledControlNormal(0,31)
end
local function directionFor(x,y)
    if x*x+y*y<.01 then return nil end
    if math.abs(y)>=math.abs(x) then return y>0 and 'fwd' or 'bwd',0,y>0 and 1 or -1 end
    return x>0 and 'right' or 'left',x>0 and 1 or -1,0
end
local function hit(value)return value==true or value==1 end
local function invalid(p)
    return not DoesEntityExist(p) or p~=PlayerPedId() or IsEntityDead(p) or
        IsPedInAnyVehicle(p,false) or IsPedRagdoll(p) or IsPedSwimming(p) or
        GetEntityCollisionDisabled(p) or (CidadeTurret and CidadeTurret.active) or
        (GetResourceState('fpv_drone_runtime')=='started' and exports.fpv_drone_runtime:isPiloting())
end
local function applyCrouch(p)
    SetPedStealthMovement(p,false,'DEFAULT_ACTION')
    SetPedUsingActionMode(p,false,-1,'DEFAULT_ACTION')
    SetPedMovementClipset(p,CROUCH,0.15)
    SetPedStrafeClipset(p,STRAFE)
    SetPedWeaponMovementClipset(p,CROUCH)
    crouchWeapon=GetSelectedPedWeapon(p);crouchRefresh=GetGameTimer()+500
end
-- Selecting the already equipped weapon can still reset GTA's movement
-- clipsets. Refresh on inventory commands even when the weapon hash is equal.
function M.refreshCrouch()
    if M.active and crouchPed and not invalid(crouchPed) then applyCrouch(crouchPed) end
end
function M.stopCrouch()
    token=token+1;M.pending=false
    local p,owned=crouchPed,M.active
    if stopFastCrouch then stopFastCrouch(p) end
    M.active=false;M.holdingC=false;crouchPed=nil;crouchWeapon=nil;crouchRefresh=0
    if owned and p and DoesEntityExist(p) then
        pcall(ResetPedMovementClipset,p,0.2);pcall(ResetPedStrafeClipset,p)
        pcall(ResetPedWeaponMovementClipset,p)
        pcall(SetPedMaxMoveBlendRatio,p,3.0)
        pcall(SetPedMoveRateOverride,p,1.0)
    end
end
function M.startCrouch(groundedTransition,held)
    if M.active or M.pending then return end
    local p=PlayerPedId()
    if invalid(p) or (not groundedTransition and IsEntityInAir(p)) or IsPauseMenuActive() or IsNuiFocused() then return end
    TriggerEvent('cidade:preparePilot')
    M.holdingC=held==true
    local request=token
    M.pending=true
    RequestAnimSet(CROUCH);RequestAnimSet(STRAFE);RequestAnimDict(FAST)
    local deadline=GetGameTimer()+5000
    while token==request and GetGameTimer()<deadline and
        (not HasAnimSetLoaded(CROUCH) or not HasAnimSetLoaded(STRAFE) or not HasAnimDictLoaded(FAST)) do Wait(20) end
    if token~=request then return end
    if invalid(p) or IsPauseMenuActive() or IsNuiFocused() or not HasAnimSetLoaded(CROUCH) or not HasAnimSetLoaded(STRAFE) or not HasAnimDictLoaded(FAST) then M.stopCrouch();return end
    M.pending=false;M.active=true;crouchPed=p
    applyCrouch(p)
    print('[Combate] Revisao '..M.revision..'; agachado com locomocao direcional e Shift rapido.')
    -- Keep GTA's native weapon IK, aim, shooting and reload while crouch-walking.
end
function M.tick()
    if not M.active and not M.pending then return end
    if (crouchPed and invalid(crouchPed)) or IsPauseMenuActive() or IsNuiFocused() or IsControlJustPressed(0,194) then
        M.stopCrouch();return
    end
    if not M.active then return end
    for group=0,2 do
        DisableControlAction(group,21,true);DisableControlAction(group,22,true)
        DisableControlAction(group,36,true)
    end
    -- Changing/holstering a weapon and its action mode must not restore a
    -- standing gait. Reload/aim/fire and the weapon wheel remain native.
    if GetSelectedPedWeapon(crouchPed)~=crouchWeapon or GetGameTimer()>=crouchRefresh then applyCrouch(crouchPed) end
    SetPedUsingActionMode(crouchPed,false,-1,'DEFAULT_ACTION')
    local fast=IsDisabledControlPressed(0,21) or IsControlPressed(0,21)
    -- Leave the native reload task uninterrupted; resume the fast gait only
    -- after it completes, if Shift and a movement key are still held.
    if IsPedReloading(crouchPed) then fast=false end
    local x,y=movementInput()
    local direction,mx,my=directionFor(x,y)
    -- The previous blend/rate-only change stayed in GTA's slow crouch gait.
    -- An authored mover track now supplies the faster step, at playback 1.0.
    SetPedMaxMoveBlendRatio(crouchPed,1.0)
    SetPedMoveRateOverride(crouchPed,1.0)
    if fast and direction then
        DisableControlAction(0,30,true);DisableControlAction(0,31,true)
        for _,k in ipairs({32,33,34,35}) do DisableControlAction(0,k,true) end
        local unarmed=GetSelectedPedWeapon(crouchPed)==joaat('WEAPON_UNARMED')
        local clip='rapido_'..(unarmed and 'livre_' or 'armado_')..direction
        if fastCrouch and fastCrouch.clip~=clip then stopFastCrouch(crouchPed) end
        local now=GetGameTimer()
        if not fastCrouch or probe or now>=fastCrouch.checkAt then
            local route=pathClear(crouchPed,'crouch_'..direction,mx,my,false)
            if route=='blocked' then stopFastCrouch(crouchPed);return end
            if route=='pending' and (not fastCrouch or now-fastCrouch.clearAt>=150) then
                stopFastCrouch(crouchPed,true);return
            end
            if route=='clear' and fastCrouch then fastCrouch.clearAt=now;fastCrouch.checkAt=now+80 end
        end
        if not fastCrouch then
            TaskPlayAnim(crouchPed,FAST,clip,8.0,-8.0,-1,MOVER_FLAGS,1.0,false,false,false)
            fastCrouch={clip=clip,issuedAt=now,checkAt=now+80,clearAt=now}
        elseif not IsEntityPlayingAnim(crouchPed,FAST,clip,3) and now-fastCrouch.issuedAt>150 then
            -- Native aim/reload may interrupt the task. Reacquire locomotion
            -- without clearing those weapon tasks or changing the posture.
            stopFastCrouch(crouchPed)
        end
    else stopFastCrouch(crouchPed) end
end
stopFastCrouch=function(p,keepProbe)
    if fastCrouch and p and DoesEntityExist(p) then StopAnimTask(p,FAST,fastCrouch.clip,1000.0) end
    fastCrouch=nil;if not keepProbe then probe=nil end
end
function M.stopCrawl(p,keepProbe,reason)
    if crawl and p and DoesEntityExist(p) then
        sampleCrawl(p)
        local at=GetEntityCoords(p)
        afterCrawl={ped=p,position={x=at.x,y=at.y},dx=crawl.dx,dy=crawl.dy,at=GetGameTimer(),clip=crawl.clip}
        crawlTrace('parar',p,{clip=crawl.clip,reason=reason or 'transicao_de_postura',
            progress=crawl.progress,cycles=crawl.cycles})
        StopAnimTask(p,CRAWL,crawl.clip,1000.0)
    end
    crawl=nil;if not keepProbe then probe=nil end;M.crawling=false;M.crawlClip=nil;M.crawlDirection=nil
end
-- A capsule can return pending (1). Poll on following frames and fail closed,
-- instead of starting a new pending query every frame or treating it as clear.
pathClear=function(p,direction,mx,my,prone)
    local now=GetGameTimer()
    if probe then
        local valid=probe.direction==direction
        local remaining={}
        for _,handle in ipairs(probe.handles) do
            local status,blocked=GetShapeTestResult(handle)
            if status==1 and now-probe.at<150 then remaining[#remaining+1]=handle
            elseif status~=2 or hit(blocked) then valid=false end
        end
        -- Completed handles are invalid after this read. Keep only pending
        -- handles; head/torso/feet may finish on different game frames.
        if valid and #remaining>0 then probe.handles=remaining;return 'pending' end
        probe=nil
        M.route=valid and 'clear' or 'obstacle_or_failed_probe'
        return valid and 'clear' or 'blocked'
    end
    local at=GetEntityCoords(p)
    local yaw=math.rad(GetEntityHeading(p));local fx,fy=-math.sin(yaw),math.cos(yaw)
    local dx,dy=math.cos(yaw)*mx+fx*my,math.sin(yaw)*mx+fy*my
    -- Inspect the ground under both ends of the body, including the next step.
    -- This also rejects an unsupported floor, large step or ledge before moving.
    local floors={}
    for _,sample in ipairs(prone and {{-.65,0},{1.25,0},{-.65,.5},{1.25,.5}} or {{0,0},{0,.8}}) do
        local x,y=at.x+fx*sample[1]+dx*sample[2],at.y+fy*sample[1]+dy*sample[2]
        local ray=StartExpensiveSynchronousShapeTestLosProbe(x,y,at.z+0.3,x,y,at.z-2.2,17,p,4)
        local status,found,point,normal=GetShapeTestResult(ray)
        if status~=2 or not hit(found) or not normal or normal.z<0.75 then M.route='unsupported_or_steep_floor';return 'blocked' end
        floors[#floors+1]=point.z
    end
    local low,high=math.min(table.unpack(floors)),math.max(table.unpack(floors))
    if high-low>0.32 then M.route='step_or_ledge';return 'blocked' end
    local z=high+(prone and .38 or .75)
    local handles={}
    -- Sweep head, torso and feet when moving sideways. A center-only capsule
    -- missed walls intersecting the ends of a prone body.
    for _,offset in ipairs(prone and {-.65,0,.95} or {0}) do
        local x,y=at.x+fx*offset,at.y+fy*offset
        handles[#handles+1]=StartShapeTestCapsule(x-dx*.15,y-dy*.15,z,
            x+dx*(prone and .8 or .9),y+dy*(prone and .8 or .9),z,prone and .28 or .32,83,p,4)
    end
    probe={handles=handles,at=now,direction=direction}
    -- World, vehicles, objects and glass; leaves/ragdolls and the non-colliding
    -- visual rifle are not walls. GTA still keeps normal ped physics/collision.
    return 'pending'
end
function M.updateCrawl(p,allowed)
    sampleAfterCrawl(p);sampleCrawl(p)
    if not allowed then M.stopCrawl(p,false,'movimento_nao_permitido');return false,0 end
    local x,y=movementInput()
    M.forward=y;M.side=x;M.turn=0
    local direction,mx,my=directionFor(x,y)
    if not direction then M.stopCrawl(p,false,'teclas_soltas');return false,0 end
    local now=GetGameTimer()
    if crawl and crawl.direction~=direction then M.stopCrawl(p,false,'troca_de_direcao') end
    -- Validate the route before steering or advancing. Continue native collision
    -- during an active step; recheck each completed cycle before the next one.
    if not crawl or probe or now>=crawl.checkAt then
        local route=pathClear(p,'prone_'..direction,mx,my,true)
        if route=='blocked' then M.stopCrawl(p,false,M.route);return false,0 end
        if route=='pending' and (not crawl or now-crawl.clearAt>=150) then
            M.stopCrawl(p,true,'consulta_pendente');return false,0
        end
        if route=='clear' and crawl then crawl.clearAt=now;crawl.checkAt=now+80 end
        if route=='pending' and not crawl then return false,0 end
    end
    if not crawl then
        local clip='rastejar_'..direction
        local duration=GetAnimDuration(CRAWL,clip)*1000
        if duration<=0 then M.stopCrawl(p);return false,0 end
        local at=GetEntityCoords(p);local yaw=math.rad(GetEntityHeading(p))
        afterCrawl=nil
        TaskPlayAnim(p,CRAWL,clip,8.0,-8.0,-1,MOVER_FLAGS,1.0,false,false,false)
        crawl={direction=direction,clip=clip,checkAt=now+80,clearAt=now,issuedAt=now,
            origin={x=at.x,y=at.y},last={x=at.x,y=at.y},sampleAt=now,warningAt=now-1000,
            dx=math.cos(yaw)*mx-math.sin(yaw)*my,dy=math.sin(yaw)*mx+math.cos(yaw)*my,
            cycles=0,cycleProgress=0,progress=0}
        crawlTrace('iniciar',p,{clip=clip,flags=MOVER_FLAGS,duration=duration,direction=direction})
    elseif not IsEntityPlayingAnim(p,CRAWL,crawl.clip,3) and now-crawl.issuedAt>150 then
        M.stopCrawl(p,false,'animacao_interrompida');return false,0
    end
    M.crawling=true
    M.crawlClip=crawl.clip;M.crawlDirection=direction;M.crawlDictionary=CRAWL
    return true,0
end
function M.snapshot(p)
    local at=GetEntityCoords(p)
    return {crouched=M.active,crawling=M.crawling,clip=M.crawlClip,route=M.route,
        forward=M.forward,side=M.side,turn=M.turn,fastCrouch=fastCrouch and fastCrouch.clip,
        holdingC=M.holdingC,position={at.x,at.y,at.z},speed=GetEntitySpeed(p),
        crawlPhase=crawl and crawl.phase,crawlProgress=crawl and crawl.progress,
        crawlCycles=crawl and crawl.cycles}
end
RegisterCommand('rastejodebug',function(_,args)
    if args[1]=='off' or args[1]=='0' then crawlDebug=false;print('[Rastejo] Logs desativados.')
    elseif args[1]=='on' or args[1]=='1' then crawlDebug=true;print('[Rastejo] Logs ativados.')
    else
        print('[Rastejo] '..json.encode(M.snapshot(PlayerPedId())))
        for i=math.max(1,#crawlHistory-11),#crawlHistory do print('[Rastejo historico] '..json.encode(crawlHistory[i])) end
    end
end,false)
AddEventHandler('cidade:preparePilot',M.stopCrouch)
AddEventHandler('cidade:weaponChanged',M.refreshCrouch)
AddEventHandler('cidade:stopProne',M.stopCrouch)
AddEventHandler('onResourceStop',function(name)
    if name==GetCurrentResourceName() then M.stopCrouch();M.stopCrawl(PlayerPedId()) end
end)
RegisterCommand('agachar',function()
    local ok,err=xpcall(function()
        if M.active or M.pending then M.stopCrouch() else M.startCrouch() end
    end,debug.traceback)
    if not ok then M.stopCrouch();print('[Combate] Erro no agachamento; controles restaurados: '..tostring(err)) end
end,false)
