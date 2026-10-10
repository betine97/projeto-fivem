local commands,events,threads={},{},{}
local view,clock,total,clip=2,1000,60,30
local selected='WEAPON_CARBINERIFLE'
local aim,fire,dead,drone,back,reloading=false,false,false,false,false,false
local shots,poses=0,0
local noAutoReload,armIk,torsoIk,gestures=false,true,true,true
local visualCreated=false
CidadeCombatWeapon={
    destroy=function() visualCreated=false end,
    entity=function() return 2 end,
    update=function() return true end,
    create=function() visualCreated=true;return true end
}
function SetPedEnableWeaponBlocking() end
function SetPedCanTorsoReactIk() end
local recoilRewinds=0
local nativeReload,animPhase,secondaryClears=false,0,0
local primaryClears=0
local activeDict,animFlags
function SetEntityAnimCurrentTime(_,_,name,phase)
    assert(phase>=0 and phase<=1);animPhase=phase
    if name=='recuo' then assert(phase==0);recoilRewinds=recoilRewinds+1 end
end
function IsPedReloading() return nativeReload end
function ClearPedSecondaryTask() nativeReload=false;secondaryClears=secondaryClears+1 end
function SetWeaponsNoAutoreload(value) noAutoReload=value end
function SetPedCanArmIk(_,value) armIk=value end
function SetPedCanTorsoIk(_,value) torsoIk=value end
function SetPedCanPlayGestureAnims(_,value) gestures=value end
local activeClip=nil
local blocked={}
local airborne=false
local camera,heading,mouseX,fxCount=nil,0,0,0
local rawC,rawAlt,moveY=false,false,0
local movementTargets={}
function IsDisabledRawKeyDown(key) return (key==0x43 and rawC) or (key==0xA4 and rawAlt) end
function IsControlPressed() return false end
function GetGameplayCamFov() return 60 end
function TaskGoStraightToCoord(_,x,y,z,speed,duration,h) movementTargets[#movementTargets+1]={x=x,y=y,heading=h} end
function SetGameplayCamRelativePitch() end
local camPosition,camYaw
local mappings={}
function RegisterKeyMapping(command,description,mapper,key) mappings[command]=key end
function CreateCam() camera=9;return camera end
function DestroyCam() camera=nil end
function GetDisabledControlNormal(_,c) return c==1 and mouseX or c==31 and moveY or 0 end
function IsUsingKeyboard() return true end
function GetPedBoneCoords() return {x=0,y=0,z=31} end
function GetCamCoord() return {x=0,y=0,z=31} end
function GetCamRot() return {x=0,z=heading} end
function HasNamedPtfxAssetLoaded() return true end
function IsPedCurrentWeaponSilenced() return false end
function StartParticleFxNonLoopedOnPedBone(_,entity,...) assert(entity==2,'FX must attach to weapon');fxCount=fxCount+1 end
for _,n in ipairs({'RenderScriptCams','SetGameplayCamRelativeHeading','SetCamNearClip','SetCamCoord','SetCamRot','SetCamFov','RequestNamedPtfxAsset','RemoveNamedPtfxAsset','UseParticleFxAsset','ShakeCam'}) do _G[n]=function() end end
function joaat(s) return s end
function RegisterCommand(n,f) commands[n]=f end
function AddEventHandler(n,f) events[n]=f end
function TriggerEvent(n) if events[n] then events[n]() end end
function CreateThread(f) threads[#threads+1]=coroutine.create(f) end
function Wait() coroutine.yield() end
function PlayerPedId() return 1 end
function PlayerId() return 0 end
function GetResourceState() return 'started' end
exports={fpv_drone_runtime={isPiloting=function() return drone end}}
function IsEntityDead() return dead end
function GetSelectedPedWeapon() return selected end
function HasAnimDictLoaded() return true end
function HasWeaponAssetLoaded() return true end
function GetGameTimer() return clock end
function DoesEntityExist() return true end
function GetFollowPedCamViewMode() return view end
function SetFollowPedCamViewMode(v) view=v end
function GetEntityCoords() return {x=0,y=0,z=30} end
function GetEntityHeading() return heading end
function GetGameplayCamRot() return {x=0,z=30} end
function GetGameplayCamCoord() return {x=0,y=-3,z=31} end
function GetFrameTime() return 1/60 end
function TaskPlayAnim(_,dict,clip,blendIn,blendOut,duration,flags) poses=poses+1;activeClip=clip;activeDict=dict;animFlags=flags end
function TaskPlayAnimAdvanced(_,_,clip) poses=poses+1;activeClip=clip end
function TaskAimGunScripted() error('Native aiming must never replace the pose') end
function IsDisabledControlPressed(_,c) return (c==25 and aim) or (c==24 and fire) end
function IsDisabledControlJustPressed(_,c) return c==45 and reloading end
-- Model the actual GTA mapping: RMB also activates cellphone cancel (177).
function IsControlJustPressed(_,c) return (c==177 and (back or aim)) or (c==194 and back) end
function IsEntityPlayingAnim(_,_,clip) return clip==activeClip end
function DisableControlAction(group,c) blocked[c]=true; blocked[group..':'..c]=true end
function GetAmmoInClip() return true,clip end
function GetAmmoInPedWeapon() return total end
function GetMaxAmmoInClip() return 30 end
function SetPedAmmo(_,_,n) total=n end
function SetAmmoInClip(_,_,n) clip=n end
function GetCurrentPedWeaponEntityIndex() return 2 end
function GetEntityBoneIndexByName(_,name) return name=='gun_gripr' and 2 or 1 end
-- Model a custom pose pointing opposite the entity heading (+Y).
function GetWorldPositionOfEntityBone(_,bone) return {x=1,y=bone==2 and 3 or 2,z=3} end
function StartExpensiveSynchronousShapeTestLosProbe(x,y,z,tx,ty,tz)
    return (tx-x)^2+(ty-y)^2+(tz-z)^2>25 and 1 or 2
end
function GetShapeTestResult(ray) return 2,ray==1,{x=10,y=20,z=30} end
function GetWeaponDamage() return 30 end
function GetWeaponTimeBetweenShots() return 0.1 end
function ShootSingleBulletBetweenCoords(x,y,z,tx,ty,tz,damage,_,w,owner)
    assert(x==1 and y==2 and z==3,'Bullet must start at muzzle')
    assert(tx==10 and ty==20 and tz==30,'Must use camera hit point')
    assert(damage==30 and w==selected and owner==1)
    shots=shots+1
end
function IsEntityInAir() return airborne end
for _,n in ipairs({'IsPedInAnyVehicle','IsPedRagdoll','IsPedSwimming','IsPauseMenuActive','IsNuiFocused'}) do _G[n]=function() return false end end
for _,n in ipairs({'BeginTextCommandThefeedPost','AddTextComponentSubstringPlayerName','EndTextCommandThefeedPostTicker','RemoveAnimDict','RequestAnimDict','RequestWeaponAsset','SetEntityHeading','DisablePlayerFiring','ClearPedTasks','ClearPedTasksImmediately','ShakeGameplayCam','DrawRect'}) do _G[n]=function() end end
function GetCurrentResourceName() return 'cidade_core' end
function SetEntityHeading(_,value) heading=value end
function ClearPedTasks() primaryClears=primaryClears+1 end
function ClearPedTasksImmediately() primaryClears=primaryClears+1 end
function SetCamCoord(_,x,y,z) camPosition={x=x,y=y,z=z} end
function SetCamRot(_,_,_,yaw) camYaw=yaw end
dofile('server-data/resources/cidade_core/prone.lua')
local function tick() local ok,err=coroutine.resume(threads[1]); assert(ok,err) end
commands.ajoelhar(); assert(poses==1 and view==2)
assert(noAutoReload and not armIk and not torsoIk and not gestures,'Native reload/IK must not replace the authored grip')
tick(); tick(); assert(blocked[24] and blocked[25] and blocked[45])
assert(camera==nil and heading==0,'Kneeling must not replace native camera or turn ped')
assert(mappings['+cidade_ajoelhar']=='C' and mappings['+cidade_olhar']=='LMENU')
assert(blocked[26] and blocked[19],'Replace native C/Alt actions')
assert(blocked['0:25'] and blocked['1:25'] and blocked['2:25'],'Block aim in every input group')
airborne=true; aim=true; tick(); assert(view==2,'Custom pose airborne flag must not cancel combat')
assert(math.abs(camYaw-30)<0.001,'Aiming must preserve viewing direction')
airborne=false; aim=false
fire=true; tick(); assert(shots==0,'No hip fire')
aim=true; tick(); assert(view==2,'Right mouse must not exit posture via control 177')
assert(shots==1 and total==59 and clip==29)
assert(camera and fxCount>=2,'Aiming camera and attached firing FX required')
local stableHeading=heading
for i=1,20 do tick() end
assert(heading==stableHeading,'No rotation without mouse input')
mouseX=0.2;tick();assert(heading~=stableHeading,'Mouse steers independent camera');mouseX=0
tick(); assert(shots==1,'Enforce cadence')
clock=clock+100; tick(); assert(shots==2)
fire=false; reloading=true; tick(); reloading=false
clock=clock+2100; fire=true; tick(); assert(shots==2,'No shooting during reload')
clock=clock+100; fire=false; tick(); assert(clip==30 and total==58,'Reload must not create ammunition')
clip=0;total=0;fire=true;clock=clock+500;tick();assert(shots==2,'No unlimited ammo')
back=true;tick();assert(view==2);back=false
assert(camera==nil,'Exit must destroy aiming camera')
assert(not noAutoReload and armIk and torsoIk and gestures,'Exit must restore native weapon behavior')
commands.ajoelhar2(); assert(view==2)
selected='WEAPON_RPG';tick();assert(view==2)
selected='WEAPON_CARBINERIFLE';commands.prone();assert(view==2)
TriggerEvent('cidade:preparePilot');assert(view==2)
commands.ajoelhar();dead=true;tick();assert(view==2);dead=false
local count=poses;drone=true;commands.ajoelhar();assert(poses==count);drone=false
commands.ajoelhar();events.onResourceStop('cidade_core');assert(view==2)
count=poses;airborne=true;commands.ajoelhar();assert(poses==count,'Still reject starting while airborne')
airborne=false;clip=30;total=60;aim=true;fire=false
commands.ajoelharteste();assert(activeClip=='mira')
fire=true;clock=clock+1000;tick();assert(activeClip=='recuo','Shot must start recoil clip')
local burstPoses=poses
clock=clock+110;tick();assert(poses==burstPoses and recoilRewinds>0,'Automatic burst must rewind without stacking full-body tasks')
fire=false;clock=clock+450;tick();assert(activeClip=='mira','Release must return to idle')
clip=0;total=0;fire=true;clock=clock+1000;tick();assert(activeClip=='mira','Empty gun must not animate recoil')
events.onResourceStop('cidade_core');assert(view==2)
aim=false;fire=false;clip=30;total=60
rawC=true;commands['+cidade_ajoelhar']();tick();assert(camera==nil and activeClip=='mira')
clock=clock+350;tick()
view=4;tick();assert(view==4 and camera==nil,'User V selection must persist during pose')
local beforeHeading,beforeYaw=heading,camYaw
rawAlt=true;mouseX=0.5;tick()
assert(heading==beforeHeading and camYaw~=beforeYaw,'Alt must orbit without turning character')
local beforeShots=shots;aim=true;fire=true;clock=clock+1000;tick()
assert(shots==beforeShots,'Free look must not shoot toward orbit view')
mouseX=0;fire=false;aim=false;rawAlt=false
for i=1,60 do tick() end
assert(camera==nil,'Releasing Alt returns to native camera')
assert(heading==beforeHeading,'Free look must preserve body direction')
rawC=false;commands['-cidade_ajoelhar']();assert(camera==nil and view==4,'Releasing C must restore normal stance without changing view')
local afterRelease=poses;tick();assert(poses==afterRelease,'Released pose must not restart')
rawC=true;commands['+cidade_ajoelhar']();tick();rawC=false;tick()
afterRelease=poses;tick();assert(poses==afterRelease,'Physical key-up must recover a missing release callback')
rawAlt=true;moveY=-1;mouseX=0.5;clock=clock+1000;tick()
local target=movementTargets[#movementTargets];assert(target,'Alt must also work while walking normally')
clock=clock+200;tick();local target2=movementTargets[#movementTargets]
assert(target.x==target2.x and target.y==target2.y,'Mouse orbit must not steer held W')
rawAlt=false;moveY=0;mouseX=0;tick();assert(camera==nil)
local loaded=true
function HasAnimDictLoaded() return loaded end
loaded=false;rawC=true
local pendingStart=coroutine.create(commands['+cidade_ajoelhar'])
assert(coroutine.resume(pendingStart))
assert(coroutine.status(pendingStart)=='suspended','Simulate asset loading')
rawC=false;commands['-cidade_ajoelhar']();loaded=true
afterRelease=poses;assert(coroutine.resume(pendingStart));tick()
assert(poses==afterRelease and camera==nil,'Release during loading must cancel late activation')
assert(mappings.cidade_deitar=='Z','Z must activate the prepared prone animation')
aim=false;fire=false;rawC=false;clip=30;total=60
commands.cidade_deitar();tick();assert(activeClip=='mira' and camera==nil)
clock=clock+350;tick()
local pronePoses=poses
for i=1,10 do tick() end
assert(activeClip=='mira','Prone must persist without a held key')
aim=true;fire=true;clock=clock+1000;local oldShots=shots;tick()
assert(shots==oldShots+1 and activeClip=='recuo','Prone must shoot and animate its own recoil')
fire=false;clock=clock+450;tick();assert(activeClip=='mira')
rawC=true;pronePoses=poses;commands['+cidade_ajoelhar']();tick()
assert(poses==pronePoses and camera==nil,'C must stand directly without starting kneeling')
commands['+cidade_ajoelhar']();tick();assert(poses==pronePoses,'Holding C after standing must not start kneeling')
rawC=false;commands['-cidade_ajoelhar']();tick()
aim=false;rawC=true;commands['+cidade_ajoelhar']();tick()
assert(activeClip=='mira','A new C press from standing must still kneel')
rawC=false;commands['-cidade_ajoelhar']();tick()
loaded=false;local pendingProne=coroutine.create(commands.cidade_deitar)
assert(coroutine.resume(pendingProne));assert(coroutine.status(pendingProne)=='suspended')
rawC=true;pronePoses=poses;commands['+cidade_ajoelhar']();loaded=true
assert(coroutine.resume(pendingProne));tick()
assert(poses==pronePoses,'C must cancel prone while its asset is still loading')
rawC=false;commands['-cidade_ajoelhar']()
aim=false;fire=false;commands.cidade_deitar();tick()
local beforeTransitionShots=shots
commands.cidade_deitar();tick();assert(activeClip=='levantar_deitado','Second Z must play the staged exit')
local transitionPoses=poses
aim=true;fire=true;commands.cidade_deitar();commands['+cidade_ajoelhar']()
clock=clock+800;tick()
assert(poses==transitionPoses and shots==beforeTransitionShots,'No restarting transition or firing during rise')
assert(noAutoReload,'Posture must remain controlled through kneeling stage')
clock=clock+690;tick();assert(noAutoReload,'Must not finish before 1.5 seconds')
clock=clock+10;tick();assert(not noAutoReload and armIk and camera==nil and not visualCreated,'1.5 second exit must release controls and visual rifle')
aim=false;fire=false
commands.cidade_deitar();commands.cidade_deitar();dead=true;tick()
assert(not noAutoReload,'Death during rise must restore weapon behavior');dead=false
-- Facing is now baked into the clips; runtime must never flip the ped on entry.
for _,command in ipairs({'ajoelharteste','deitadotiro'}) do
    heading=70;aim=false;fire=false;commands[command]()
    assert(heading==70,'Entry must not rotate entity')
    tick();assert(heading==70,'First frame must preserve facing')
    clock=clock+350;tick();assert(heading==70,'No delayed facing correction')
    clock=clock+1000;tick();assert(heading==70,'No accumulated rotation')
    TriggerEvent('cidade:stopProne');assert(heading==70,'Standing facing must remain unchanged')
end
-- Reproduce the reported failure: repeated reload -> release aim -> aim/fire
-- in each low stance, with both native rifle models and a queued reload task.
for _,w in ipairs({'WEAPON_CARBINERIFLE','WEAPON_ASSAULTRIFLE'}) do
    selected=w
    for _,posture in ipairs({'ajoelharteste','deitadotiro','sentadotiro'}) do
        aim=true;fire=false;rawC=false;clock=clock+5000;clip=3;total=240
        commands[posture]();tick()
        assert(activeDict:find(w=='WEAPON_ASSAULTRIFLE' and '_ak' or '_ar',1,true),'Wrong rifle-specific clip')
        local clearCount=primaryClears
        for cycle=1,8 do
            clip=3
            local initialTotal=total
            reloading=true;tick();reloading=false
            assert(activeClip=='recarga' and animFlags==10,'Reload must keep the authored stance, without looping')
            local existingPoses=poses
            reloading=true;tick();reloading=false
            assert(poses==existingPoses,'Repeated R must not restart a reload')
            clock=clock+850;aim=false;tick()
            assert(activeClip=='recarga','Releasing aim must not cancel reload or stand up')
            nativeReload=true;tick()
            assert(not nativeReload and animPhase>.3 and animPhase<.5,'Recover the native task at elapsed reload phase')
            clock=clock+1349;aim=true;fire=true;local beforeShots=shots;tick()
            assert(shots==beforeShots and clip==3,'Do not refill/fire before 2.2 seconds')
            clock=clock+1;fire=false;tick()
            assert(activeClip=='mira' and clip==30 and total==initialTotal,'Return to aim and conserve total ammunition')
            assert(visualCreated and primaryClears==clearCount,'Reload must not recreate the ped or clear the low stance')
            fire=true;clock=clock+150;tick()
            assert(shots==beforeShots+1 and activeClip=='recuo' and total==initialTotal-1 and clip==29,'Fire must resume after every reload')
            fire=false;clock=clock+450;tick()
        end
        clip=1;local canceledTotal=total
        reloading=true;tick();reloading=false
        TriggerEvent('cidade:stopProne');clock=clock+3000;tick()
        assert(clip==1 and total==canceledTotal and not visualCreated,'Canceled reload must not grant ammunition later')
    end
end
selected='WEAPON_CARBINERIFLE';clip=30;total=31;aim=false;fire=false
commands.sentarcombate();tick();reloading=true;local fullPoses=poses;tick();reloading=false
assert(activeClip=='mira' and poses==fullPoses,'A full magazine must not start a seated reload')
commands.sentarcombate();tick();assert(not visualCreated,'Seated toggle must stand and release the rifle')
clip=0;total=7;commands.deitadotiro();tick();reloading=true;tick();reloading=false
clock=clock+2200;tick();assert(clip==7 and total==7,'Load only the remaining reserve')
TriggerEvent('cidade:stopProne')
print('OK: 48 repeated low-stance reloads, both rifles, task recovery, aiming, firing, ammunition and cleanup')
