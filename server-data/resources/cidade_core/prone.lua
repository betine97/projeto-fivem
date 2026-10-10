-- Stationary combat for the LOCAL single-player sandbox. Static poses do not
-- support GTA's normal aim task: it replaces them and stands the ped up.
-- Block that task and fire native projectiles from the actual weapon muzzle.
local active,pending,ped,weapon,mode=false,false,nil,nil,nil
local generation,nextShot,reloadAt=0,0,nil
local reloadStartedAt=nil
local combatRevision='v12-rastejo-posicao-fisica'
local recoilUntil=0
local recoilStartedAt=0
local playingClip,clipIssuedAt=nil,0
local playingDict,playingLayer,lastPhase=nil,nil,nil
local pitchLimits={ajoelharteste={-45,45},deitadotiro={-8,35}}
local pitchDicts={ajoelharteste={'cidade_mira_v9_ajoelhado_ar','cidade_mira_v9_ajoelhado_ak'},
    deitadotiro={'cidade_mira_v9_deitado_ar','cidade_mira_v9_deitado_ak'}}
local sampleAimPose -- defined after the animation sampler
local clipConfirmed=false
local postureStartedAt=0
local lastTraceAt,lastWatchAt,badPitchAt,lastRepairAt=0,0,nil,0
local repairWindowAt,repairCount=0,0
local lastPoseSample=nil
local tracing=true
local history,historyIndex,historyCount={},0,0
local traceState=nil
local function trace(event,details,important)
    local item=traceState and traceState() or {}
    item.event=event;item.ms=GetGameTimer();item.revision=combatRevision;item.generation=generation
    if details then for key,value in pairs(details) do item[key]=value end end
    historyIndex=historyIndex%200+1;history[historyIndex]=item;historyCount=math.min(200,historyCount+1)
    if tracing or important then print('[Combate trace] '..json.encode(item)) end
end
local exitAt=nil
local weaponPoseLocked=false
local function weaponPoseLock(p,locked)
    SetWeaponsNoAutoreload(locked)
    SetPedCanArmIk(p,not locked)
    SetPedCanTorsoIk(p,not locked)
    SetPedCanTorsoReactIk(p,not locked)
    SetPedCanHeadIk(p,not locked)
    SetPedEnableWeaponBlocking(p,not locked)
    SetPedCanPlayGestureAnims(p,not locked)
    SetPedCanPlayAmbientAnims(p,not locked)
    SetPedCanPlayAmbientBaseAnims(p,not locked)
    weaponPoseLocked=locked
end
local aimCam,aimYaw,aimPitch=nil,0,0
local posedPitch=0
local function rifleEquipped()
    return weapon==joaat('WEAPON_CARBINERIFLE') or weapon==joaat('WEAPON_ASSAULTRIFLE')
end
local function verticalAim()
    return rifleEquipped() and pitchLimits[mode]~=nil and not reloadAt and not exitAt
end
local function kick(now)
    if not verticalAim() or now>=recoilUntil then return 0 end
    return 1.4*math.sin(math.pi*math.max(0,math.min(1,(now-recoilStartedAt)/400)))
end
local aimHeadingOffset=0
local freeLook=false
local heldPosture=false
local pendingMode=nil
local poseHeadingOffset=0

local nextSmoke=0
local lookCam,lookPed,lookOrigin,lookOffset,lookRotation,lookHeading,lookMoveAt
local lookOwnsMovement=false
local function closeLook()
    if not lookCam then return end
    RenderScriptCams(false,true,180,true,true)
    DestroyCam(lookCam,false); lookCam=nil
    if lookOwnsMovement and DoesEntityExist(lookPed) then ClearPedTasks(lookPed) end
    lookOwnsMovement=false
end
local function closeAim(previousPed)
    if not aimCam then return end
    RenderScriptCams(false,false,0,true,true)
    DestroyCam(aimCam,false); aimCam=nil
    local actor=previousPed or ped
    if actor and DoesEntityExist(actor) then
        SetGameplayCamRelativeHeading((aimYaw-GetEntityHeading(actor)+180)%360-180)
        SetGameplayCamRelativePitch(aimPitch,1.0)
    end
end
local function updateLook()
    local p=PlayerPedId()
    if not lookCam then
        lookPed=p; lookOrigin=GetEntityCoords(p)
        local c=GetGameplayCamCoord(); local r=GetGameplayCamRot(2)
        lookOffset={x=c.x-lookOrigin.x,y=c.y-lookOrigin.y,z=c.z-lookOrigin.z}
        lookRotation={x=r.x,z=r.z}; lookHeading=r.z; lookMoveAt=0
        lookCam=CreateCam('DEFAULT_SCRIPTED_CAMERA',true)
        SetCamNearClip(lookCam,0.05); SetCamFov(lookCam,GetGameplayCamFov())
        SetCamCoord(lookCam,c.x,c.y,c.z); SetCamRot(lookCam,r.x,0.0,r.z,2)
        RenderScriptCams(true,false,0,true,true)
    end
    DisableControlAction(0,1,true); DisableControlAction(0,2,true)
    DisableControlAction(0,24,true); DisableControlAction(0,25,true)
    DisablePlayerFiring(PlayerId(),true)
    local scale=IsUsingKeyboard(0) and 8.0 or 120.0*math.min(GetFrameTime(),0.05)
    local yaw=-GetDisabledControlNormal(0,1)*scale
    local pitch=math.max(-65,math.min(65,lookRotation.x-GetDisabledControlNormal(0,2)*scale))
    -- Rotate the original camera around a chest-height pivot, preserving its
    -- distance/FOV. Position also follows the ped while walking under Alt.
    local delta=math.rad(yaw)
    local x=lookOffset.x*math.cos(delta)-lookOffset.y*math.sin(delta)
    local y=lookOffset.x*math.sin(delta)+lookOffset.y*math.cos(delta)
    local distance=math.sqrt(x*x+y*y+(lookOffset.z-0.8)^2)
    local horizontal=math.sqrt(x*x+y*y)
    local elevation=math.atan(lookOffset.z-0.8,horizontal)-math.rad(pitch-lookRotation.x)
    if horizontal>0.001 then
        local ratio=distance*math.cos(elevation)/horizontal; x=x*ratio; y=y*ratio
    end
    lookOffset={x=x,y=y,z=0.8+distance*math.sin(elevation)}
    lookRotation.x=pitch; lookRotation.z=(lookRotation.z+yaw)%360
    local origin=GetEntityCoords(p)
    local cx,cy,cz=origin.x+x,origin.y+y,origin.z+lookOffset.z
    local ray=StartExpensiveSynchronousShapeTestLosProbe(origin.x,origin.y,origin.z+0.8,cx,cy,cz,511,p,7)
    local status,hit,point=GetShapeTestResult(ray)
    if status==2 and (hit==true or hit==1) then
        cx,cy,cz=point.x+(origin.x-point.x)*0.12,point.y+(origin.y-point.y)*0.12,point.z+(origin.z+0.8-point.z)*0.12
    end
    SetCamCoord(lookCam,cx,cy,cz); SetCamRot(lookCam,pitch,0.0,lookRotation.z,2)
    if not active and not CidadePostureMovement.active then
        -- Explicit movement relative to the direction BEFORE free look, so
        -- turning the camera cannot steer a held W into a different direction.
        DisableControlAction(0,30,true); DisableControlAction(0,31,true)
        local mx,my=GetDisabledControlNormal(0,30),-GetDisabledControlNormal(0,31)
        if mx*mx+my*my>0.01 then
            if GetGameTimer()>=lookMoveAt then
                local a=math.rad(lookHeading)
                local dx,dy=math.cos(a)*mx-math.sin(a)*my,math.sin(a)*mx+math.cos(a)*my
                local speed=IsControlPressed(0,21) and 3.0 or 1.5
                TaskGoStraightToCoord(p,origin.x+dx*8,origin.y+dy*8,origin.z,speed,250,
                    math.deg(math.atan(-dx,dy)),0.1)
                lookOwnsMovement=true; lookMoveAt=GetGameTimer()+100
            end
        elseif lookOwnsMovement then
            ClearPedTasks(p); lookOwnsMovement=false; lookMoveAt=0
        end
    end
end
local function updateAim()
    local fresh=not aimCam
    if fresh then
        local heading=GetEntityHeading(ped)
        local view=GetGameplayCamRot(2)
        aimYaw=view.z; aimPitch=view.x; aimHeadingOffset=poseHeadingOffset
        -- Legacy poses need a barrel offset. The Blender clip preserves the
        -- imported rest-space orientation; do not sample its entry blend.
        local gun=CidadeCombatWeapon.entity(ped)
        if mode~='ajoelharteste' and mode~='deitadotiro' and mode~='sentadotiro' and gun~=0 and DoesEntityExist(gun) then
            local muzzleBone=GetEntityBoneIndexByName(gun,'gun_muzzle')
            local gripBone=GetEntityBoneIndexByName(gun,'gun_gripr')
            if muzzleBone>=0 and gripBone>=0 then
                local muzzle=GetWorldPositionOfEntityBone(gun,muzzleBone)
                local grip=GetWorldPositionOfEntityBone(gun,gripBone)
                local dx,dy=muzzle.x-grip.x,muzzle.y-grip.y
                if dx*dx+dy*dy>0.0001 then
                    aimHeadingOffset=(math.deg(math.atan(-dx,dy))-heading+180)%360-180
                end
            end
        end
        aimCam=CreateCam('DEFAULT_SCRIPTED_CAMERA',true)
        SetCamNearClip(aimCam,0.05)
    end
    DisableControlAction(0,1,true); DisableControlAction(0,2,true)
    -- Accumulate input independently: never feed the follow-camera yaw back
    -- into the ped heading, which creates continuous orbiting.
    local scale=IsUsingKeyboard(0) and 8.0 or 120.0*math.min(GetFrameTime(),0.05)
    local dx,dy=GetDisabledControlNormal(0,1)*scale,GetDisabledControlNormal(0,2)*scale
    aimYaw=(aimYaw-dx)%360
    local limits=pitchLimits[mode] or {-55,55}
    aimPitch=math.max(limits[1],math.min(limits[2],aimPitch-dy))
    SetEntityHeading(ped,(aimYaw-aimHeadingOffset)%360)
    posedPitch=math.max(limits[1],math.min(limits[2],aimPitch+kick(GetGameTimer())))
    sampleAimPose()
    local head=GetPedBoneCoords(ped,31086,0.0,0.0,0.0)
    local viewYaw,viewPitch=aimYaw,posedPitch
    local yaw,pitch=math.rad(viewYaw),math.rad(viewPitch)
    local fx,fy,fz=-math.sin(yaw)*math.cos(pitch),math.cos(yaw)*math.cos(pitch),math.sin(pitch)
    local x,y,z=head.x-fx*0.85+math.cos(yaw)*0.28,head.y-fy*0.85+math.sin(yaw)*0.28,head.z-fz*0.85+0.08
    local ray=StartExpensiveSynchronousShapeTestLosProbe(head.x,head.y,head.z,x,y,z,511,ped,7)
    local status,hit,point=GetShapeTestResult(ray)
    if status==2 and (hit==true or hit==1) then
        x,y,z=point.x+(head.x-point.x)*0.12,point.y+(head.y-point.y)*0.12,point.z+(head.z-point.z)*0.12
    end
    SetCamCoord(aimCam,x,y,z); SetCamRot(aimCam,viewPitch,0.0,viewYaw,2)
    SetCamFov(aimCam,42.0)
    if fresh then RenderScriptCams(true,true,150,true,true) end
end
local function shotEffects(gun,muzzleBone,now)
    if not HasNamedPtfxAssetLoaded('core') then RequestNamedPtfxAsset('core'); return end
    local function emit(name,bone,scale)
        if bone<0 then return end
        UseParticleFxAsset('core')
        StartParticleFxNonLoopedOnPedBone(name,gun,0.0,0.0,0.0,0.0,0.0,0.0,bone,scale,false,false,false)
    end
    if not IsPedCurrentWeaponSilenced(ped) then emit('muz_assault_rifle',muzzleBone,1.0) end
    emit('eject_auto',GetEntityBoneIndexByName(gun,'gun_vfx_eject'),1.0)
    if now>=nextSmoke then emit('env_gunsmoke',muzzleBone,0.12); nextSmoke=now+300 end
end
local lastDiagnostic,lastDiagnosticAt,requestedShots=nil,0,0
local function diagnostic(message)
    local now=GetGameTimer()
    if message~=lastDiagnostic or now-lastDiagnosticAt>=3000 then
        print('[Combate diagnostico] '..message)
        lastDiagnostic=message; lastDiagnosticAt=now
    end
end
local poses={
    ajoelharteste={'cidade_ajoelhado_v5_ar','mira','recuo','recarga'},
    deitadotiro={'cidade_deitado_v5_ar','mira','recuo','recarga'},
    sentadotiro={'cidade_sentado_v5_ar','mira','recuo','recarga'}
}
local assaultPoses={
    ajoelharteste={'cidade_ajoelhado_v6_ak','mira','recuo','recarga'},
    deitadotiro={'cidade_deitado_v6_ak','mira','recuo','recarga'},
    sentadotiro={'cidade_sentado_v6_ak','mira','recuo','recarga'}
}
local function currentPose(name,w)
    return w==joaat('WEAPON_ASSAULTRIFLE') and assaultPoses[name] or poses[name]
end
local aliases={ajoelhar='ajoelharteste',ajoelhar2='ajoelharteste',prone='deitadotiro'}
-- Rifle poses: do not silently apply rifle grip to pistols, launchers or shotguns.
local supported={[joaat('WEAPON_CARBINERIFLE')]=true,[joaat('WEAPON_ASSAULTRIFLE')]=true}
local function say(text)
    print('[Combate] '..text)
    BeginTextCommandThefeedPost('STRING'); AddTextComponentSubstringPlayerName(text)
    EndTextCommandThefeedPostTicker(false,false)
end
local function droneActive()
    return GetResourceState('fpv_drone_runtime')=='started' and exports.fpv_drone_runtime:isPiloting()
end
local function invalid(p,entering)
    if CidadeTurret and CidadeTurret.active then return 'operando torre' end
    if not DoesEntityExist(p) or p~=PlayerPedId() then return 'personagem alterado' end
    if IsEntityDead(p) then return 'personagem morto' end
    if IsPedInAnyVehicle(p,false) then return 'entrou em veiculo' end
    -- Custom root poses may report airborne while their feet leave the ground.
    -- Use this check ONLY before starting, not as a reason to erase the pose.
    if entering and IsEntityInAir(p) then return 'fora do chao' end
    if IsPedRagdoll(p) then return 'queda/ragdoll' end
    if IsPedSwimming(p) then return 'na agua' end
    if GetEntityCollisionDisabled(p) then return 'voo/colisao desativada' end
    if droneActive() then return 'pilotagem do drone' end
end
local function stop(reason)
    if active or pending then pcall(trace,'postura_saida',{reason=type(reason)=='string' and reason or 'comando/troca'}) end
    local wasActive,oldPed,oldOffset,wasLocked=active,ped,poseHeadingOffset,weaponPoseLocked
    -- Release ownership before native cleanup. An error must never latch the
    -- old active/held flags or let a pending entry use an obsolete generation.
    generation=generation+1;pending=false;pendingMode=nil;active=false;heldPosture=false
    ped=nil;weapon=nil;mode=nil;reloadAt=nil;reloadStartedAt=nil;recoilUntil=0
    playingClip=nil;playingDict=nil;playingLayer=nil;lastPhase=nil;posedPitch=0;clipIssuedAt=0;recoilStartedAt=0
    clipConfirmed=false;badPitchAt=nil;lastPoseSample=nil;poseHeadingOffset=0
    weaponPoseLocked=false
    exitAt=nil
    freeLook=false
    local function cleanup(label,fn,...)
        local ok,err=pcall(fn,...)
        if not ok then print('[Combate] Falha ao limpar '..label..': '..tostring(err)) end
    end
    cleanup('arma visual',CidadeCombatWeapon.destroy)
    cleanup('camera de olhar',closeLook)
    cleanup('camera de mira',closeAim,oldPed)
    cleanup('rastejar',CidadePostureMovement.stopCrawl,oldPed)
    if wasActive then print('[Combate] Postura encerrada: '..(type(reason)=='string' and reason or 'comando ou troca de modo')) end
    if wasActive and oldPed and DoesEntityExist(oldPed) then
        local view=GetGameplayCamRot(2)
        local facing=(GetEntityHeading(oldPed)+oldOffset)%360
        -- A blending-out task can keep a frozen rifle/torso pose after the next
        -- C/Z entry. End both primary and secondary tasks before restoring IK.
        cleanup('tarefa principal',ClearPedTasksImmediately,oldPed)
        cleanup('tarefa secundaria',ClearPedSecondaryTask,oldPed)
        cleanup('olhar',TaskClearLookAt,oldPed)
        if oldOffset~=0 then
            SetEntityHeading(oldPed,facing)
            SetGameplayCamRelativeHeading((view.z-facing+180)%360-180)
            SetGameplayCamRelativePitch(view.x,1.0)
        end
    end
    if wasLocked then cleanup('IK',weaponPoseLock,oldPed or PlayerPedId(),false) end
    -- Keep these small dictionaries loaded across rapid posture changes. Only
    -- unload after every task has been canceled on resource shutdown.
    cleanup('efeitos',RemoveNamedPtfxAsset,'core')
end
local function poseClip()
    if not rifleEquipped() then return 'parado' end
    local pose=currentPose(mode,weapon)
    if reloadAt and pose[4] then return pose[4] end
    if mode=='deitadotiro' and CidadePostureMovement.crawling then
        return CidadePostureMovement.crawlDirection=='bwd' and 'mira_rastejar_bwd' or 'mira_rastejar_fwd'
    end
    -- Rest on the approved constant rifle pose. Sample pitch only while aiming,
    -- rather than holding a zero-speed evaluator at a cached entry/crawl blend.
    if pitchLimits[mode] and aimCam then return 'mira_vertical' end
    if pose[3] and GetGameTimer()<recoilUntil then return pose[3] end
    return pose[2]
end
local function clipDict()
    if not rifleEquipped() then return 'cidade_deitado_move_v11' end
    if poseClip():find('mira_rastejar',1,true) then
        return weapon==joaat('WEAPON_ASSAULTRIFLE') and 'cidade_rastejar_v9_ak' or 'cidade_rastejar_v9_ar'
    end
    if poseClip()=='mira_vertical' then
        return pitchDicts[mode][weapon==joaat('WEAPON_ASSAULTRIFLE') and 2 or 1]
    end
    return currentPose(mode,weapon)[1]
end
traceState=function()
    local info={active=active,pending=pending,mode=mode,pendingMode=pendingMode,ped=ped,weapon=weapon,
        reload=reloadAt~=nil,recoil=GetGameTimer()<recoilUntil,exit=exitAt~=nil,playingClip=playingClip,
        shots=requestedShots,held=heldPosture,aimCamera=aimCam~=nil,aimYaw=aimYaw,aimPitch=aimPitch,
        clipConfirmed=clipConfirmed,clipIssuedAt=clipIssuedAt,lastRepairAt=lastRepairAt}
    if active and ped and DoesEntityExist(ped) then
        local pose=currentPose(mode,weapon)
        local clip=poseClip()
        local dict=clipDict()
        info.dictionary=dict;info.wantedClip=clip;info.crawling=CidadePostureMovement.crawling;info.posedPitch=posedPitch
        info.movement=CidadePostureMovement.snapshot(ped)
        info.animationPlaying=IsEntityPlayingAnim(ped,dict,clip,3)
        info.animationPhase=GetEntityAnimCurrentTime(ped,dict,clip)
        info.nativeReload=IsPedReloading(ped);info.nativeShooting=IsPedShooting(ped)
        info.nativeAim=IsPlayerFreeAiming(PlayerId());info.model=GetEntityModel(ped)
        info.heading=GetEntityHeading(ped)
        if rifleEquipped() then
            local ammoOK,clipAmmo=GetAmmoInClip(ped,weapon)
            info.clipAmmo=ammoOK and clipAmmo or nil;info.totalAmmo=GetAmmoInPedWeapon(ped,weapon)
        end
        -- Events need a fresh measurement, especially immediately after a
        -- recovery. Do not label the previous watchdog sample as the new pose.
        info.pose=CidadeCombatWeapon.inspect()
        if info.pose then info.pose.ms=GetGameTimer() end
    end
    return info
end
local function playPose(recover,recoverReason)
    if recover then CidadePostureMovement.stopCrawl(ped) end
    if not rifleEquipped() and CidadePostureMovement.crawling then return end
    local pose=currentPose(mode,weapon)
    local clip=poseClip()
    local dict=clipDict()
    local sampled=clip=='mira_vertical' or clip:find('mira_rastejar',1,true)~=nil
    local layer=CidadePostureMovement.crawling and 'upper' or 'full'
    local now=GetGameTimer()
    local isPlaying=IsEntityPlayingAnim(ped,dict,clip,3)
    if recover or clip~=playingClip or dict~=playingDict or layer~=playingLayer or (not isPlaying and now-clipIssuedAt>=150) then
        -- AF_NOT_INTERRUPTABLE (8) used to keep the old full-body task alive
        -- across reload/recoil/aim. Stop that task before forcing its successor.
        local previous=playingClip
        if recover then
            ClearPedTasksImmediately(ped);ClearPedSecondaryTask(ped);TaskClearLookAt(ped)
            layer='full'
        elseif playingClip then StopAnimTask(ped,playingDict,playingClip,8.0) end
        weaponPoseLock(ped,true)
        local flags=131072+((clip==pose[2] or sampled) and 1 or 2)
        if layer=='upper' then flags=flags+16+32 end -- mask upper body; keep native crawl root/legs
        if not rifleEquipped() then flags=131072+1 end -- sampled idle, no mover extraction
        -- A zero-speed evaluator kept stale blended bones in the actual game,
        -- even when GetEntityAnimCurrentTime reported the requested phase.
        TaskPlayAnim(ped,dict,clip,16.0,-16.0,-1,flags,1.0,false,false,false)
        playingClip=clip;playingDict=dict;playingLayer=layer;lastPhase=nil;clipIssuedAt=now
        clipConfirmed=false
        trace('clipe_enviado',{previousClip=previous,clip=clip,recover=recover==true,flags=flags,
            animationWasPlaying=isPlaying,recoverReason=recoverReason or (recover and 'recuperacao' or
                (previous~=clip and 'clipe_trocado' or 'clipe_ausente'))})
        isPlaying=IsEntityPlayingAnim(ped,dict,clip,3)
    end
    if isPlaying then
        -- Sample each clip from a fixed timer, never from the previous blend's
        -- pose. Interrupted clips resume at elapsed time; bursts rewind recoil.
        local phase=0.0
        if clip==pose[4] and reloadAt then phase=(now-reloadStartedAt)/2200
        elseif clip==pose[3] then phase=(now-recoilStartedAt)/400
        elseif clip=='mira_vertical' then
            local limits=pitchLimits[mode];phase=(posedPitch-limits[1])/(limits[2]-limits[1])
        elseif sampled then
            local rows=clip=='mira_rastejar_fwd' and 28 or 32
            local stride=GetEntityAnimCurrentTime(ped,CidadePostureMovement.crawlDictionary,CidadePostureMovement.crawlClip)
            local row=math.max(0,math.min(rows-1,math.floor(stride*(rows-1)+0.5)))
            phase=(row*44+posedPitch+8)/(rows*44-1)
        elseif not rifleEquipped() then phase=0.0 end -- all idle frames are identical; no mover track
        phase=math.max(0.0,math.min(1.0,phase))
        SetEntityAnimSpeed(ped,dict,clip,1.0)
        SetEntityAnimCurrentTime(ped,dict,clip,phase)
        if not clipConfirmed or sampled or not rifleEquipped() then
            -- Evaluate live pitch/stride samples even if the target is unchanged:
            -- the native parent animation and the task blend continue advancing.
            ForcePedAiAndAnimationUpdate(ped,false,true)
            if not clipConfirmed then trace('clipe_confirmado',{phase=phase}) end
            clipConfirmed=true;lastPhase=phase
        end
    end
end
sampleAimPose=playPose
local function watchPose(now)
    if now-lastWatchAt<100 or exitAt then return end
    lastWatchAt=now
    lastPoseSample=rifleEquipped() and CidadeCombatWeapon.inspect() or nil
    if lastPoseSample then lastPoseSample.ms=now end
    if tracing and now-lastTraceAt>=3000 then
        lastTraceAt=now;trace('amostra')
    end
    if not lastPoseSample or lastPoseSample.invalidBasis or CidadePostureMovement.crawling then return end
    -- Compare the barrel to the sampled pitch; reloads remain horizontal.
    -- Ignore entry blends and the staged stand-up, which deliberately tilts.
    if now-postureStartedAt<400 or not clipConfirmed or now-clipIssuedAt<120 then badPitchAt=nil;return end
    local expected=verticalAim() and posedPitch or 0
    if math.abs(lastPoseSample.barrelPitch-expected)<=8.0 then
        if badPitchAt then trace('inclinacao_normalizada') end
        badPitchAt=nil;return
    end
    if not badPitchAt then badPitchAt=now;trace('inclinacao_detectada',nil,true) end
    if now-badPitchAt<180 or now-lastRepairAt<1200 then return end
    if now-repairWindowAt>10000 then repairWindowAt=now;repairCount=0 end
    if repairCount>=3 then return end -- bounded recovery; preserve useful logs
    repairCount=repairCount+1;lastRepairAt=now
    trace('recompor_postura',{attempt=repairCount},true)
    playPose(true,'inclinacao_persistente')
    CidadeCombatWeapon.update()
    badPitchAt=nil
end
local function requestPostureAssets(requested)
    local dictionaries={}
    for _,w in ipairs({joaat('WEAPON_CARBINERIFLE'),joaat('WEAPON_ASSAULTRIFLE')}) do
        dictionaries[#dictionaries+1]=currentPose(requested,w)[1]
        local index=w==joaat('WEAPON_ASSAULTRIFLE') and 2 or 1
        if pitchDicts[requested] then dictionaries[#dictionaries+1]=pitchDicts[requested][index] end
        if requested=='deitadotiro' then
            dictionaries[#dictionaries+1]=index==2 and 'cidade_rastejar_v9_ak' or 'cidade_rastejar_v9_ar'
        end
        RequestWeaponAsset(w,31,0)
    end
    if requested=='deitadotiro' then dictionaries[#dictionaries+1]='cidade_deitado_move_v11' end
    for _,dict in ipairs(dictionaries) do RequestAnimDict(dict) end
    RequestNamedPtfxAsset('core')
    return function()
        for _,dict in ipairs(dictionaries) do if not HasAnimDictLoaded(dict) then return false end end
        return HasWeaponAssetLoaded(joaat('WEAPON_CARBINERIFLE')) and HasWeaponAssetLoaded(joaat('WEAPON_ASSAULTRIFLE'))
    end
end
local function switchWeapon(selected)
    if not supported[selected] and not (mode=='deitadotiro' and selected==joaat('WEAPON_UNARMED')) then
        stop('arma sem animacao compativel');say('A mira deitada autoral aceita carabina/fuzil e desarmado.');return
    end
    trace('arma_trocada_sem_levantar',{previousWeapon=weapon,newWeapon=selected})
    -- Preserve the prone locomotion task and its position. Re-entering through
    -- start() incorrectly rejected the lowered root as "in air" on holstering.
    closeAim();reloadAt=nil;reloadStartedAt=nil;recoilUntil=0;nextShot=0
    if playingClip and not (CidadePostureMovement.crawling and playingDict==CidadePostureMovement.crawlDictionary) then
        StopAnimTask(ped,playingDict,playingClip,16.0)
    end
    ClearPedSecondaryTask(ped)
    CidadeCombatWeapon.destroy()
    weapon=selected;playingClip=nil;playingDict=nil;playingLayer=nil;lastPhase=nil
    clipConfirmed=false;posedPitch=0;badPitchAt=nil;postureStartedAt=GetGameTimer()
    weaponPoseLock(ped,true)
    playPose()
    if rifleEquipped() and not CidadeCombatWeapon.create(ped,weapon) then stop('falha ao trocar arma visual') end
end
local function start(requested,held)
    requested=aliases[requested] or requested
    trace('postura_pedido',{requested=requested,heldRequest=held==true})
    if exitAt then return end
    if pending or (active and mode==requested) then stop(); return end
    local p=PlayerPedId()
    if invalid(p,true) then say('Fique no chao, fora de veiculos/agua e encerre o drone.'); return end
    local w=GetSelectedPedWeapon(p)
    local unarmed=w==joaat('WEAPON_UNARMED') and requested=='deitadotiro'
    if not supported[w] and not unarmed then say('Para esta mira use carabina/fuzil. Z tambem permite rastejar desarmado.'); return end
    TriggerEvent('cidade:preparePilot')
    heldPosture=held==true
    local token=generation
    pending=true; pendingMode=requested
    local pose=currentPose(requested,w)
    -- Preload both supported guns while entering, including an unarmed entry.
    -- Drawing a gun later needs no yielding/restart of the posture controller.
    local loaded=requestPostureAssets(requested)
    local deadline=GetGameTimer()+5000
    while token==generation and GetGameTimer()<deadline and not loaded() do Wait(20) end
    if token~=generation then return end
    pending=false; pendingMode=nil
    if not loaded() then
        stop(); say('Asset nao carregou. Reconecte depois de reiniciar cidade_core.'); return
    end
    if invalid(p,true) or GetSelectedPedWeapon(p)~=w then stop(); return end
    ped=p; weapon=w; mode=requested
    poseHeadingOffset=0
    active=true; nextShot=0; reloadAt=nil; reloadStartedAt=nil; recoilUntil=0; requestedShots=0; lastDiagnostic=nil
    playingClip=nil;playingDict=nil;playingLayer=nil;lastPhase=nil;posedPitch=0;clipIssuedAt=0;recoilStartedAt=0
    clipConfirmed=false;postureStartedAt=GetGameTimer();lastWatchAt=0;badPitchAt=nil
    lastPoseSample=nil;lastRepairAt=0;repairWindowAt=postureStartedAt;repairCount=0
    ClearPedTasksImmediately(ped); weaponPoseLock(ped,true); playPose()
    if rifleEquipped() and not CidadeCombatWeapon.create(ped,weapon) then
        stop('falha ao preparar arma visual');say('Nao foi possivel preparar a arma. Tente novamente.');return
    end
    print('[Combate] Revisao '..combatRevision..'; dicionario='..pose[1])
    trace('postura_entrada')
    if mode=='sentadotiro' then
        say('Sentado no chao: R recarrega sem levantar. Direito mira; esquerdo dispara. sentarcombate ou Backspace levanta.')
    elseif mode=='deitadotiro' then
        say('Deitado: segure W/S para frente/tras e A/D para os lados. Sem tecla, fica parado. Z levanta; segurar C agacha. R recarrega o fuzil.')
    else
        say('Ajoelhado: direito mira; esquerdo dispara; R recarrega. Backspace levanta. C permite andar agachado; Z deita.')
    end
end
local function reload(now)
    if not rifleEquipped() then return end
    local ok,clip=GetAmmoInClip(ped,weapon)
    if not reloadAt and ok and clip<GetMaxAmmoInClip(ped,weapon,true) and GetAmmoInPedWeapon(ped,weapon)>clip then
        reloadStartedAt=now; reloadAt=now+2200; recoilUntil=0
        CidadePostureMovement.stopCrawl(ped)
        posedPitch=0
        trace('recarga_inicio')
        if currentPose(mode,weapon)[4] then
            ClearPedSecondaryTask(ped)
            weaponPoseLock(ped,true)
            playPose()
        end
        say('Recarga iniciada sem levantar (2,2 s).')
    end
end
local function shoot(now)
    if not rifleEquipped() then return end
    if not clipConfirmed then return end -- wait for the new wrist pose before reading its muzzle
    if now<nextShot then return end
    if reloadAt then diagnostic('Disparo bloqueado: recarga em andamento.'); return end
    if not HasWeaponAssetLoaded(weapon) then
        diagnostic('Disparo bloqueado: asset da arma descarregado.')
        RequestWeaponAsset(weapon,31,0); return
    end
    local ok,clip=GetAmmoInClip(ped,weapon)
    local total=GetAmmoInPedWeapon(ped,weapon)
    if not ok then diagnostic('Disparo bloqueado: GetAmmoInClip falhou.'); return end
    if clip<=0 or total<=0 then
        diagnostic(('Sem municao para disparar: pente=%s total=%s'):format(clip,total))
        reload(now); return
    end
    local gun=CidadeCombatWeapon.entity(ped)
    if gun==0 or not DoesEntityExist(gun) then diagnostic('Disparo bloqueado: entidade da arma ausente.'); return end
    local bone=GetEntityBoneIndexByName(gun,'gun_muzzle')
    if bone<0 then diagnostic('Disparo bloqueado: bone gun_muzzle ausente.'); return end
    local muzzle=GetWorldPositionOfEntityBone(gun,bone)
    local cam,rot=GetGameplayCamCoord(),GetGameplayCamRot(2)
    if aimCam then cam,rot=GetCamCoord(aimCam),GetCamRot(aimCam,2) end
    local pitch,yaw=math.rad(rot.x),math.rad(rot.z)
    local target={x=cam.x-math.sin(yaw)*math.cos(pitch)*300.0,
        y=cam.y+math.cos(yaw)*math.cos(pitch)*300.0,z=cam.z+math.sin(pitch)*300.0}
    -- Camera ray selects the target; the actual bullet starts at the barrel,
    -- so nearby cover between the gun and the target still blocks the shot.
    local ray=StartExpensiveSynchronousShapeTestLosProbe(cam.x,cam.y,cam.z,target.x,target.y,target.z,511,ped,7)
    local status,hit,point=GetShapeTestResult(ray)
    if status~=2 then diagnostic('Disparo bloqueado: raycast status='..tostring(status)); return end
    if hit==true or hit==1 then target=point end
    ShootSingleBulletBetweenCoords(muzzle.x,muzzle.y,muzzle.z,target.x,target.y,target.z,
        math.floor(GetWeaponDamage(weapon,0)),true,weapon,ped,true,false,-1.0)
    requestedShots=requestedShots+1
    if requestedShots==1 or requestedShots%10==0 then trace('disparo',{clipAmmo=clip,totalAmmo=total}) end
    diagnostic('Native de projetil chamada; verificar impacto no jogo.')
    SetPedAmmo(ped,weapon,total-1)
    SetAmmoInClip(ped,weapon,clip-1)
    weaponPoseLock(ped,true)
    shotEffects(gun,bone,now)
    nextShot=now+math.max(60,GetWeaponTimeBetweenShots(weapon)*1000)
    local pose=currentPose(mode,weapon)
    if pose[3] then
        -- Rewind the same authored recoil instead of accumulating transforms.
        recoilStartedAt=now
        recoilUntil=now+400
        playPose()
    end
    if aimCam then ShakeCam(aimCam,'SMALL_EXPLOSION_SHAKE',0.025) end
end
local function guarded(fn)
    local ok,err=xpcall(fn,debug.traceback)
    if not ok then CidadePostureMovement.stopCrouch();stop(); print('[Combate] '..tostring(err)); say('Erro na postura; controles restaurados.') end
end
for name in pairs(poses) do
    local command=name
    RegisterCommand(command,function() guarded(function() start(command) end) end,false)
end
for name in pairs(aliases) do
    local command=name
    RegisterCommand(command,function() guarded(function() start(command) end) end,false)
end
AddEventHandler('cidade:stopProne',stop)
RegisterCommand('sentarcombate',function()
    if IsPauseMenuActive() or IsNuiFocused() or exitAt then return end
    guarded(function() start('sentadotiro',false) end)
end,false)
-- Keep saved/remapped bindings; key-down enters and key-up exits. Repeated
-- key-down events are idempotent and release also cancels pending loading.
RegisterCommand('cidade_ajoelhar',function() end,false)
RegisterCommand('+cidade_ajoelhar',function()
    if IsPauseMenuActive() or IsNuiFocused() then return end
    if exitAt then return end
    guarded(function()
        if CidadePostureMovement.active or CidadePostureMovement.pending then return end
        local groundedTransition=active and not invalid(ped,false)
        if active or pending then stop('C: mudar para agachado') end
        CidadePostureMovement.startCrouch(groundedTransition,true)
    end)
end,false)
RegisterCommand('-cidade_ajoelhar',function()
    guarded(function() if CidadePostureMovement.holdingC then CidadePostureMovement.stopCrouch() end end)
end,false)
RegisterKeyMapping('+cidade_ajoelhar','Segurar para agachar; Shift acelera (com ou sem arma)','keyboard','C')
RegisterCommand('cidade_deitar',function()
    if IsPauseMenuActive() or IsNuiFocused() or pending or exitAt then return end
    if active and mode=='deitadotiro' then
        guarded(function()
            closeAim(); closeLook(); freeLook=false; heldPosture=false
            CidadePostureMovement.stopCrawl(ped)
            reloadAt=nil; reloadStartedAt=nil; recoilUntil=0; exitAt=GetGameTimer()+1500
            -- The v4 clip plays all 91 source frames at rate 2, not a truncation.
            if playingClip then StopAnimTask(ped,playingDict,playingClip,8.0) end
            playingClip=nil;playingDict=nil;playingLayer=nil;lastPhase=nil
            clipConfirmed=false
            trace('levantar_inicio')
            TaskPlayAnim(ped,currentPose(mode,weapon)[1],'levantar_deitado',4.0,-4.0,1500,131074,1.0,false,false,false)
        end)
        return
    end
    guarded(function() start('deitadotiro',false) end)
end,false)
RegisterKeyMapping('cidade_deitar','Deitar / levantar passando pelo ajoelhado','keyboard','Z')
RegisterCommand('+cidade_olhar',function()
    if not IsPauseMenuActive() and not IsNuiFocused() then freeLook=true end
end,false)
RegisterCommand('-cidade_olhar',function() freeLook=false end,false)
RegisterKeyMapping('+cidade_olhar','Segurar para olhar ao redor','keyboard','LMENU')
AddEventHandler('cidade:preparePilot',stop)
RegisterCommand('combateinfo',function()
    trace('info_manual',nil,true)
    if CidadePostureMovement.active then print('[Combate diagnostico] Agachado com locomocao/arma nativas.');return end
    if not active then print('[Combate diagnostico] Postura inativa.'); return end
    if not rifleEquipped() then print('[Combate diagnostico] Deitado desarmado; segure W/S/A/D para rastejar. Sem tecla, parado.');return end
    local ok,clip=GetAmmoInClip(ped,weapon)
    local gun=CidadeCombatWeapon.entity(ped)
    local bone=-1
    if gun~=0 and DoesEntityExist(gun) then bone=GetEntityBoneIndexByName(gun,'gun_muzzle') end
    print(('[Combate diagnostico] revisao=%s dict=%s clip=%s modo=%s arma=%s entidade=%s muzzle=%s asset=%s penteOK=%s pente=%s total=%s recarga=%s chamadasProjetil=%s ultimo=%s')
        :format(combatRevision,currentPose(mode,weapon)[1],poseClip(),mode,weapon,gun,bone,tostring(HasWeaponAssetLoaded(weapon)),tostring(ok),tostring(clip),
        GetAmmoInPedWeapon(ped,weapon),tostring(reloadAt~=nil),requestedShots,tostring(lastDiagnostic)))
end,false)
RegisterCommand('combatedebug',function(_,args)
    local option=args and args[1]
    if option=='0' or option=='off' then tracing=false else tracing=true end
    trace('debug_config',{enabled=tracing},true)
end,false)
RegisterCommand('combatehistorico',function(_,args)
    local count=math.max(1,math.min(historyCount,math.floor(tonumber(args and args[1]) or 40)))
    if historyCount==0 then print('[Combate trace] Sem eventos registrados.');return end
    for offset=count-1,0,-1 do
        local index=(historyIndex-offset-1)%200+1
        print('[Combate historico] '..json.encode(history[index]))
    end
end,false)
CreateThread(function()
    while true do
        -- A command can activate between frames: never leave a 100ms window
        -- for native aiming to replace the newly started animation.
        Wait(0)
        guarded(CidadePostureMovement.tick)
        -- Poll the physical Alt as well as its command: old saved mappings and
        -- missed key-up events must not disable or latch free look.
        freeLook=not (CidadeTurret and CidadeTurret.active) and not (CidadeCover and CidadeCover.active) and not exitAt and IsDisabledRawKeyDown(0xA4)
        -- C no longer invokes GTA's look-behind; Alt is reserved for free look.
        if not IsPedInAnyVehicle(PlayerPedId(),false) then
            DisableControlAction(0,26,true)
            DisableControlAction(0,19,true)
            DisableControlAction(0,20,true)
        end
        if IsPauseMenuActive() or IsNuiFocused() or IsEntityDead(PlayerPedId()) or
            IsPedInAnyVehicle(PlayerPedId(),false) or IsPedRagdoll(PlayerPedId()) or
            IsPedSwimming(PlayerPedId()) or droneActive() then
            freeLook=false
            if heldPosture then stop('entrada interrompida') end
        end
        if heldPosture and not IsDisabledRawKeyDown(0x43) then stop('C solto') end
        if freeLook then
            guarded(function() closeAim(); updateLook() end)
        else closeLook() end
        if active then guarded(function()
            local reason=invalid(ped,false)
            if reason then stop(reason); return end
            if GetSelectedPedWeapon(ped)~=weapon then
                switchWeapon(GetSelectedPedWeapon(ped))
                if not active then return end
            end
            -- 177 is CELLPHONE_CANCEL: Backspace, ESC AND right mouse.
            -- 194 is FRONTEND_RRIGHT: Backspace (no right-mouse binding).
            if not IsPauseMenuActive() and not IsNuiFocused() and IsControlJustPressed(0,194) then
                stop('Backspace'); return
            end
            -- Read disabled inputs ourselves. Native aim/fire/reload would replace the pose.
            for group=0,2 do
                for _,control in ipairs({21,22,23,24,25,30,31,32,33,34,35,36,44,45,140,141,142,257,263,264}) do
                    DisableControlAction(group,control,true)
                end
            end
            DisablePlayerFiring(PlayerId(),true)
            -- Reassert while active: native weapon tasks can restore IK during
            -- ammo changes. Hands/torso must remain owned by the authored clip.
            weaponPoseLock(ped,true)
            if exitAt then
                if rifleEquipped() and not CidadeCombatWeapon.update() then stop('arma visual removida');return end
                if GetGameTimer()>=exitAt then stop('transicao para em pe concluida') end
                return
            end
            local pose=currentPose(mode,weapon)
            local paused=IsPauseMenuActive() or IsNuiFocused()
            local wasCrawling=CidadePostureMovement.crawling
            local moving,turned=CidadePostureMovement.updateCrawl(ped,mode=='deitadotiro' and not reloadAt and not paused)
            if aimCam and turned~=0 then aimYaw=(aimYaw+turned)%360 end
            if not rifleEquipped() and moving then
                playingClip=nil;playingDict=nil;playingLayer=nil;lastPhase=nil;clipConfirmed=false
            elseif wasCrawling and not moving then
                if playingClip then StopAnimTask(ped,playingDict,playingClip,8.0) end
                ClearPedSecondaryTask(ped)
                playingClip=nil;playingDict=nil;playingLayer=nil;lastPhase=nil;clipConfirmed=false
            end
            -- A queued native reload or another task must not survive into aim.
            if rifleEquipped() and pose[4] and IsPedReloading(ped) then
                playPose(true,'recarga_nativa')
            end
            if paused then
                playPose();freeLook=false;closeAim()
                if rifleEquipped() and not CidadeCombatWeapon.update() then stop('arma visual removida') end
                return
            end
            local now=GetGameTimer()
            if reloadAt and now>=reloadAt then
                SetAmmoInClip(ped,weapon,math.min(GetMaxAmmoInClip(ped,weapon,true),GetAmmoInPedWeapon(ped,weapon)))
                reloadAt=nil; reloadStartedAt=nil; recoilUntil=0
                if pose[4] then
                    ClearPedSecondaryTask(ped); weaponPoseLock(ped,true); playPose()
                    CidadeCombatWeapon.update()
                end
                local clipOK,loaded=GetAmmoInClip(ped,weapon)
                if clipOK then say(('Recarga concluida: %s no pente; %s na reserva.'):format(loaded,math.max(0,GetAmmoInPedWeapon(ped,weapon)-loaded)))
                else say('Falha ao consultar pente depois da recarga. Veja F8: combateinfo.') end
                trace('recarga_fim',{loaded=loaded})
            end
            if IsDisabledControlJustPressed(0,45) then reload(now) end
            local aiming=rifleEquipped() and IsDisabledControlPressed(0,25)
            if aiming and not freeLook then updateAim() else
                closeAim()
                posedPitch=0;playPose()
            end
            if rifleEquipped() and not CidadeCombatWeapon.update() then stop('arma visual removida');return end
            if aiming and not freeLook then
                DrawRect(0.5,0.5,0.002,0.004,255,255,255,220)
                if IsDisabledControlPressed(0,24) then shoot(now) end
            else
                if IsDisabledControlPressed(0,24) then diagnostic('Botao esquerdo recebido sem mira: segure direito + esquerdo juntos.') end
            end
            watchPose(now)
        end) end
    end
end)
AddEventHandler('onResourceStop',function(name)
    if name==GetCurrentResourceName() then
        stop('recurso encerrado')
        for _,pose in pairs(poses) do RemoveAnimDict(pose[1]) end
        for _,pose in pairs(assaultPoses) do RemoveAnimDict(pose[1]) end
        for _,dicts in pairs(pitchDicts) do for _,dict in ipairs(dicts) do RemoveAnimDict(dict) end end
        RemoveAnimDict('cidade_deitado_move_v11');RemoveAnimDict('cidade_agachado_move_v11')
        RemoveAnimDict('cidade_rastejar_v9_ar');RemoveAnimDict('cidade_rastejar_v9_ak')
    end
end)
