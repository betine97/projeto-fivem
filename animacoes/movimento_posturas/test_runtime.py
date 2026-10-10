"""Strict native mocks: transitions, input ownership, pitch, ammo and route gates.

These checks do not claim to exercise FiveM rendering or its physics engine.
"""
import ast,json,math,sys,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
CORE=ROOT/'server-data/resources/cidade_core'
sys.path.insert(0,str(ROOT/'personagens/calca_tatica/test_deps'))
from lupa.lua54 import LuaRuntime
tree=ast.parse((HERE.parent/'pipeline_animacoes/revisao_mao_esquerda/test_runtime_v6.py').read_text(encoding='utf8'))
bootstrap=next(ast.literal_eval(n.value.args[0]) for n in tree.body if isinstance(n,ast.Expr)
               and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Attribute) and n.value.func.attr=='execute')
def encode(v):
    def conv(x):return {str(k):conv(y) for k,y in x.items()} if hasattr(x,'items') else x
    return json.dumps(conv(v))
def setup():
    lua=LuaRuntime(unpack_returned_tuples=True);lua.execute(bootstrap)
    lua.globals().encode_json=encode
    lua.execute(r'''
json={encode=encode_json};CidadeCover=false
S.actor=1;S.heading=0;S.normal={};S.pitch=0;S.viewPitch=0;S.disabled={};S.eventLists={}
S.primary=nil;S.secondary=nil;S.queue={};S.ammoReads=0;S.forceUpdates=0;S.capsules=0;S.rays={};S.nextRay=10
S.creates=0;S.maxBlend=3;S.moveRate=1;S.dictionaryRequests={};S.animSetRequests={};S.threads={};S.mappings={}
function CreateThread(f)table.insert(S.threads,coroutine.create(f))end
function RegisterKeyMapping(command,description,device,key)S.mappings[command]=key end
function joaat(n)if n=='WEAPON_ASSAULTRIFLE'then return 101 elseif n=='WEAPON_CARBINERIFLE'then return 102 elseif n=='WEAPON_UNARMED'then return 103 end return 900 end
function PlayerPedId()return S.actor end
function DoesEntityExist(p)return p==1 or p==2 or p==3 end
function GetEntityHeading()return S.heading end
function SetEntityHeading(_,h)S.heading=h end
function GetDisabledControlNormal(_,k)return S.normal[k] or 0 end
function GetControlNormal(_,k)return S.normal[k] or 0 end
function GetEntitySpeed()return 0 end -- No simulated physical translation claim.
function IsControlPressed(_,k)return S.pressed[k] or false end
function GetGameplayCamRot()return vector3(S.viewPitch,0,0)end
function GetCurrentResourceName()return 'cidade_core'end
function GetEntityModel()return 123 end
function GetAnimDuration(_,clip)return clip=='onfront_fwd' and .9 or 1.0333334 end
function AddEventHandler(n,f)S.eventLists[n]=S.eventLists[n] or {};table.insert(S.eventLists[n],f)end
function TriggerEvent(n,...)for _,f in ipairs(S.eventLists[n] or {})do f(...)end end
function HasAnimDictLoaded(n)return n~=S.missingDict end
function RequestAnimDict(n)S.dictionaryRequests[n]=true end
function RequestAnimSet(n)S.animSetRequests[n]=true end
function HasAnimSetLoaded()return not S.missingSet end
function SetPedMovementClipset(_,n,t)S.movement=n end
function SetPedStrafeClipset(_,n)S.strafe=n end
function ResetPedMovementClipset()S.movement=nil end
function ResetPedStrafeClipset()S.strafe=nil end
function SetPedMaxMoveBlendRatio(_,v)S.maxBlend=v end
function SetPedMoveRateOverride(_,v)S.moveRate=v end
function SetPedDesiredMoveBlendRatio(_,v)S.desiredBlend=v end
function SetPedWeaponMovementClipset(_,n)S.weaponMovement=n end
function ResetPedWeaponMovementClipset()S.weaponMovement=nil end
function SetPedStealthMovement(_,v)S.stealth=v end
function SetPedUsingActionMode(_,v)S.actionMode=v end
function IsWeaponValid(w)return w==101 or w==102 end
function GiveWeaponToPed(_,w,ammo)S.weapon=w;S.total=ammo;S.clip=math.min(30,ammo)end
function SetCurrentPedWeapon(_,w)S.weapon=w;S.movement=nil;S.weaponMovement=nil end
function RemoveAllPedWeapons()S.weapon=103;S.total=0;S.clip=0 end
function GetEntityCollisionDisabled()return S.noclip or false end
function IsEntityDead()return S.dead or false end
function IsPedInAnyVehicle()return S.vehicle or false end
function IsPedRagdoll()return S.ragdoll or false end
function IsPedSwimming()return S.swimming or false end
function IsEntityInAir()return S.airborne or false end
function IsPauseMenuActive()return S.paused or false end
function IsNuiFocused()return S.nui or false end
function DisableControlAction(g,k)S.disabled[g..':'..k]=true end
function ClearPedTasksImmediately()S.clear=S.clear+1;S.primary=nil;S.secondary=nil;S.queue={};S.nativeReload=false end
function ClearPedTasks()S.primary=nil;S.secondary=nil;S.queue={}end
function ClearPedSecondaryTask()S.secondary=nil;S.queue.secondary=nil end
function TaskClearLookAt()end
function StopAnimTask(_,d,c)
 for _,slot in ipairs({'primary','secondary'})do
  if S[slot] and S[slot].dict==d and S[slot].clip==c then S[slot]=nil end
  if S.queue[slot] and S.queue[slot].dict==d and S.queue[slot].clip==c then S.queue[slot]=nil end
 end
end
function TaskPlayAnim(_,d,c,bi,bo,duration,flags,rate)
 local t={dict=d,clip=c,flags=flags,phase=0,speed=rate,ready=S.now+30,started=S.now}
 table.insert(S.tasks,t);S.queue[(flags&32~=0) and 'secondary' or 'primary']=t
end
local function commit()
 for slot,t in pairs(S.queue)do if S.now>=t.ready then S[slot]=t;S.queue[slot]=nil end end
 local t=S.primary
 if t and t.dict=='move_crawl' and t.flags&524288~=0 then t.phase=((S.now-t.started)/(GetAnimDuration(t.dict,t.clip)*1000))%1 end
end
local function task(d,c)
 commit();for _,slot in ipairs({'primary','secondary'})do local t=S[slot];if t and t.dict==d and t.clip==c then return t end end
end
function IsEntityPlayingAnim(_,d,c)return task(d,c)~=nil end
function GetEntityAnimCurrentTime(_,d,c)local t=task(d,c);return t and t.phase or 0 end
function SetEntityAnimCurrentTime(_,d,c,v)local t=task(d,c);if t then t.phase=v end end
function SetEntityAnimSpeed(_,d,c,v)local t=task(d,c);if t then t.speed=v end end
function ForcePedAiAndAnimationUpdate(_,a,b)
 assert(a==false and b==true);S.forceUpdates=S.forceUpdates+1
 local t=S.secondary or S.primary
 -- Reproduce the report: a zero-speed evaluator can expose the desired phase
 -- while its bones retain an earlier blend. It is not a reliable aim sampler.
 if t and t.speed==0 then return end
 if t and t.clip=='mira_vertical'then
  local low,high=-45,45;if t.dict:find('deitado')then low,high=-8,35 end
  S.pitch=low+(high-low)*t.phase
 elseif t and t.clip:find('mira_rastejar')then
  local rows=t.clip=='mira_rastejar_fwd' and 28 or 32
  S.pitch=(t.phase*(rows*44-1))%44-8
 elseif t then S.pitch=0 end
end
function SetPedCanHeadIk(_,v)S.ik.head=v end
function SetPedCanPlayAmbientAnims(_,v)S.ik.ambient=v end
function SetPedCanPlayAmbientBaseAnims(_,v)S.ik.ambientBase=v end
function SetPedCanPlayGestureAnims(_,v)S.ik.gesture=v end
function StartExpensiveSynchronousShapeTestLosProbe(x,y,z,xx,yy,zz)
 S.nextRay=S.nextRay+1
 local floor=math.abs(x-xx)<.001 and math.abs(y-yy)<.001
 S.rays[S.nextRay]={floor=floor,y=yy};return S.nextRay
end
function StartShapeTestCapsule(...)
 S.capsules=S.capsules+1;S.nextRay=S.nextRay+1;S.rays[S.nextRay]={capsule=true,at=S.now};return S.nextRay
end
function GetShapeTestResult(handle)
 local r=S.rays[handle];assert(r,'Unknown probe')
 if r.capsule then
  if S.probeInvalid then return 0,false,vector3(0,0,0),vector3(0,0,1)end
  if S.probeStuck or S.now-r.at<16 then return 1,false,vector3(0,0,0),vector3(0,0,1)end
  return 2,S.wall and 1 or false,vector3(0,0,.38),vector3(0,0,1)
 elseif r.floor then
  return 2,not S.noFloor,vector3(0,r.y,(S.stepFloor and r.y>0) and 1 or 0),vector3(0,0,S.slope and .5 or 1)
 end
 return 2,false,vector3(0,200,1),vector3(0,0,1)
end
function SetCamCoord(_,x,y,z)S.camAt=vector3(x,y,z)end
function SetCamRot(_,x,y,z)S.camRot=vector3(x,y,z)end
function GetCamCoord()return S.camAt or vector3(0,-1,1.5)end
function GetCamRot()return S.camRot or vector3(0,0,0)end
function GetAmmoInClip()S.ammoReads=S.ammoReads+1;return true,S.clip end
function GetAmmoInPedWeapon()S.ammoReads=S.ammoReads+1;return S.total end
function ShootSingleBulletBetweenCoords(x,y,z,xx,yy,zz,...)
 S.projectiles=S.projectiles+1;S.bullet=vector3(xx-x,yy-y,zz-z)
end
CidadeCombatWeapon.create=function()S.creates=S.creates+1;S.visual=true;return not S.createFails end
CidadeCombatWeapon.destroy=function()S.visual=false end
CidadeCombatWeapon.inspect=function()return S.visual and {barrelPitch=S.pitch,worldBarrelPitch=S.pitch} or nil end
function step(ms)
 S.now=S.now+ms;commit()
 if S.commandThread and coroutine.status(S.commandThread)~='dead'then local ok,e=coroutine.resume(S.commandThread);assert(ok,e)end
 for _,thread in ipairs(S.threads)do
  if coroutine.status(thread)~='dead'then local ok,e=coroutine.resume(thread);assert(ok,e)end
 end
 S.just=nil
end
local allowed={}
for name in string.gmatch([[
GetGameplayCamFov RegisterKeyMapping RequestWeaponAsset HasWeaponAssetLoaded
RequestNamedPtfxAsset RemoveNamedPtfxAsset RemoveAnimDict BeginTextCommandThefeedPost
AddTextComponentSubstringPlayerName EndTextCommandThefeedPostTicker DisablePlayerFiring
RenderScriptCams DestroyCam SetGameplayCamRelativeHeading SetGameplayCamRelativePitch
SetCamNearClip SetCamFov SetPedEnableWeaponBlocking DrawRect ShakeCam UseParticleFxAsset
StartParticleFxNonLoopedOnPedBone TaskGoStraightToCoord IsPedCurrentWeaponSilenced
IsPedShooting IsPlayerFreeAiming HasNamedPtfxAssetLoaded
]],'%S+')do allowed[name]=true end
setmetatable(_G,{__index=function(_,n)
 if not allowed[n]then error('Unknown native/global: '..n)end
 if n:match('^Is')then return function()return false end end
 if n:match('^Has')then return function()return true end end
 if n=='GetGameplayCamFov'then return function()return 60 end end
 return function()end
end})
''')
    lua.execute((CORE/'posture_movement.lua').read_text(encoding='utf8'))
    lua.execute((CORE/'prone.lua').read_text(encoding='utf8'))
    lua.execute((CORE/'sandbox.lua').read_text(encoding='utf8'))
    lua.execute((CORE/'cover.lua').read_text(encoding='utf8'))
    lua.globals().step(0)
    return lua,lua.globals().S,lua.globals().CidadePostureMovement
def tick(lua,ms=16):lua.globals().step(ms)
def settle(lua,ms):
    for _ in range(math.ceil(ms/16)):tick(lua)
def command(lua,S,name,args=()):
    lua.globals().commandName=name
    lua.globals().commandArgs=lua.table_from(args)
    lua.execute('S.commandThread=coroutine.create(function()S.commands[commandName](0,commandArgs)end);local ok,e=coroutine.resume(S.commandThread);assert(ok,e)')
def logs(S):return list(S.logs.values())
def check_errors(S):assert not any('Erro na postura' in x or 'Unknown native' in x for x in logs(S)),logs(S)[-8:]
def pose(S,clip='mira_vertical',upper=False):
    t=S.secondary if upper else S.primary
    assert t and t.clip==clip,(clip,logs(S)[-8:]);assert t.flags&8==0
    return t
def standing(S,M):
    assert S.primary is None and S.secondary is None and not M.active and not M.pending
    assert not S.noAuto and S.ik.arm and S.ik.torso

checks=[]
# C is a toggle: actual command callbacks must work even if raw C reports false.
# Execute the existing arma/desarmar commands, not just a simulated weapon field.
for w in (101,102,103,900):
    lua,S,M=setup();S.weapon=w
    command(lua,S,'+cidade_ajoelhar');settle(lua,80)
    command(lua,S,'-cidade_ajoelhar');settle(lua,80)
    assert M.active and S.movement=='move_ped_crouched' and S.weaponMovement=='move_ped_crouched'
    assert S.maxBlend==1 and S.creates==0 and S.ammoReads==0
    for k in (30,31,24,25,37,45):assert not S.disabled[f'0:{k}'],k
    S.normal[31]=-1;S.pressed[21]=True;settle(lua,80)
    assert S.maxBlend>1 and S.desiredBlend>1 and S.moveRate>1 and M.active
    S.pressed[21]=False;settle(lua,80);assert S.maxBlend==1 and S.moveRate==1
    for name,args in [('arma',('carabina','120')),('desarmar',()),('arma',('fuzil','120'))]:
        command(lua,S,name,args);settle(lua,80)
        assert M.active and S.movement=='move_ped_crouched' and S.weaponMovement=='move_ped_crouched'
        assert S.creates==0
    # Native aim/reload keep locomotion ownership and their controls enabled.
    S.nativeReload=True;S.pressed[25]=True;settle(lua,700);assert M.active
    command(lua,S,'+cidade_ajoelhar');settle(lua,16)
    assert not M.active and S.movement is None and S.weaponMovement is None and S.maxBlend==3 and S.moveRate==1
    check_errors(S)
checks.append('C works unarmed/armed without raw-key hold; release preserves posture; Shift accelerates; actual draw/holster commands preserve crouch')
# Cancel loading with a second C; no delayed command may restore a stopped pose.
lua,S,M=setup();S.missingSet=True;command(lua,S,'+cidade_ajoelhar');assert M.pending
pending=S.commandThread;lua.globals().pendingCommand=pending
lua.execute('S.commands["+cidade_ajoelhar"]()');assert not M.pending
S.missingSet=False;lua.execute('local ok,e=coroutine.resume(pendingCommand);assert(ok,e)');settle(lua,80)
assert not M.active
for reason in ('dead','vehicle','ragdoll','swimming','paused','nui','noclip','ped_changed','stop','resource'):
    lua,S,M=setup();command(lua,S,'agachar');settle(lua,50);assert M.active
    if reason=='ped_changed':S.actor=3
    elif reason in ('stop','resource'):
        lua.globals().TriggerEvent('cidade:stopProne' if reason=='stop' else 'onResourceStop','cidade_core')
    else:S[reason]=True
    tick(lua);assert not M.active and S.movement is None and S.weaponMovement is None
    check_errors(S)
checks.append('pending C cancellation and ten exit conditions restore native movement/weapon gait')
# Include a stale-bone model: speed 0 does not commit the requested animation pose.
reload_cycles=0
for w in (101,102):
  for mode,limits in (('deitadotiro',(-8,35)),('ajoelharteste',(-45,45)),('sentadotiro',None)):
    lua,S,M=setup();S.weapon=w;command(lua,S,mode);settle(lua,80);pose(S,'mira')
    for initial in (-80,-5,0,20,80):
      if not limits:break
      S.pitch=52;S.viewPitch=initial;S.pressed[25]=True;settle(lua,80)
      expectedPitch=max(limits[0],min(limits[1],initial))
      assert abs(S.pitch-expectedPitch)<1e-5 and abs(S.camRot.x-expectedPitch)<1e-5
      assert pose(S).speed==1
      updates=S.forceUpdates;S.pitch=52;settle(lua,32)
      assert S.forceUpdates>updates and abs(S.pitch-expectedPitch)<1e-5
      S.pressed[25]=False;settle(lua,80);pose(S,'mira')
    S.pressed[25]=True;settle(lua,80)
    expected='mira_vertical' if limits else 'mira'
    for cycle in range(4):
      S.pressed[24]=True;before=S.projectiles;total=S.total;clip=S.clip;settle(lua,350)
      shots=S.projectiles-before;assert 3<=shots<=4 and S.total==total-shots and S.clip==clip-shots
      S.pressed[24]=False;settle(lua,500);pose(S,expected)
      S.just=45;tick(lua);settle(lua,80);pose(S,'recarga')
      before=S.projectiles;S.pressed[24]=True;settle(lua,400);assert S.projectiles==before
      S.primary=None;S.queue.primary=None;S.nativeReload=True;tick(lua);settle(lua,80)
      assert pose(S,'recarga').phase>.2
      S.pressed[24]=False;settle(lua,1840);pose(S,expected);assert S.clip==30
      reload_cycles+=1
    S.just=194;tick(lua);standing(S,M);check_errors(S)
checks.append(f'{reload_cycles} interrupted fire/reload cycles; both rifles and three poses; pitch bounds; rest clip and stale evaluation regression')
# Native extraction must own translation, not manual teleport/velocity mocks.
for w in (101,102,103):
    lua,S,M=setup();S.weapon=w;command(lua,S,'cidade_deitar');settle(lua,80)
    S.pressed[32]=True;tick(lua);assert not M.crawling
    settle(lua,80);assert M.crawling and S.primary.dict=='move_crawl' and S.primary.clip=='onfront_fwd'
    assert S.primary.flags&524288 and S.primary.flags&1 and S.primary.speed==1
    nativeCount=lambda:sum(t.dict=='move_crawl' and t.flags&524288!=0 for t in S.tasks.values())
    before=nativeCount();settle(lua,2500)
    assert M.crawling and nativeCount()==before,'Pending probes restarted the primary crawl task'
    if w!=103:
        t=pose(S,'mira_rastejar_fwd',upper=True);assert t.flags&48==48 and t.speed==1
        S.pressed[25]=True;S.pressed[24]=True;before=S.projectiles;settle(lua,160)
        assert S.projectiles>before and M.crawling
        S.pressed[24]=False;S.just=45;tick(lua);settle(lua,80)
        assert not M.crawling;pose(S,'recarga');settle(lua,2300);assert M.crawling
    S.pressed[35]=True;settle(lua,100);assert S.heading!=0
    S.pressed[32]=False;S.pressed[33]=True;settle(lua,80);assert S.primary.clip=='onfront_bwd'
    S.pressed[33]=False;S.pressed[25]=False;settle(lua,80)
    assert not M.crawling and S.secondary is None;pose(S,'onfront_fwd' if w==103 else 'mira')
    command(lua,S,'cidade_deitar');settle(lua,80);pose(S,'levantar_deitado')
    settle(lua,1520);standing(S,M);check_errors(S)
checks.append('discrete WASD fallback; continuous forward/back mover task across pending probes; turn, shoot, reload, stop and staged exit')
for failure in ('wall','noFloor','stepFloor','slope','probeStuck','probeInvalid'):
    lua,S,M=setup();S.weapon=103;command(lua,S,'cidade_deitar');settle(lua,80)
    S[failure]=True;S.pressed[32]=True;settle(lua,1400)
    assert not M.crawling and not any(t.flags&524288 for t in S.tasks.values()),failure
    check_errors(S)
# Stop an already moving crawl when a wall appears or a query stays pending.
for failure in ('wall','probeStuck','noFloor'):
    lua,S,M=setup();command(lua,S,'cidade_deitar');settle(lua,80)
    S.pressed[32]=True;settle(lua,80);assert M.crawling
    S[failure]=True;settle(lua,350);assert not M.crawling;check_errors(S)
checks.append('six blocked-route conditions and three obstacles arising during movement reject further native steps')
# Holstering while native prone root reports airborne must not trigger re-entry.
for moving in (False,True):
    lua,S,M=setup();S.weapon=103;command(lua,S,'cidade_deitar');settle(lua,80)
    if moving:S.pressed[32]=True;settle(lua,80);assert M.crawling
    S.airborne=True
    for name,args,selected in [('arma',('fuzil','120'),101),('desarmar',(),103),('arma',('carabina','120'),102)]:
        before=S.clear;command(lua,S,name,args);settle(lua,150)
        assert S.weapon==selected and S.clear==before,'Weapon switch re-entered/cleared the posture'
        if moving:assert M.crawling
        else:pose(S,'onfront_fwd' if selected==103 else 'mira')
        assert not any('fora do chao' in x or 'arma trocada' in x for x in logs(S))
    # C changes from prone to crouch even if the old lying root reports airborne.
    command(lua,S,'+cidade_ajoelhar');settle(lua,80);assert M.active
    command(lua,S,'-cidade_ajoelhar');settle(lua,80);assert M.active
    command(lua,S,'+cidade_ajoelhar');settle(lua,16);standing(S,M);check_errors(S)
checks.append('real draw/holster/rifle switch while prone, moving or still and airborne flag set; C moves prone to crouch without weapon dependency')
# Removed feature: persisted commands must be harmless; native cover is disabled.
lua,S,M=setup();before=len(S.tasks)
for name in ('cidade_cobertura','cobertura','coberturainfo'):command(lua,S,name)
settle(lua,80);assert len(S.tasks)==before and not lua.globals().CidadeCover.active
assert not any(key=='Q' for key in S.mappings.values()) and S.disabled['0:44']
assert 'TaskSeekCover' not in (CORE/'cover.lua').read_text() and 'TaskEnterCover' not in (CORE/'cover.lua').read_text()
check_errors(S)
checks.append('cover scans/tasks/key mapping removed; old cover commands are inert; native cover control disabled on foot')
lua,S,M=setup();S.missingDict='cidade_mira_v9_deitado_ak'
command(lua,S,'cidade_deitar');settle(lua,5100)
assert S.primary is None and S.creates==0
assert any('Asset nao carregou' in x for x in logs(S));check_errors(S)
checks.append('asset timeout cancels entry and restores unlocked state')
report={'revision':'v10-posturas-troca-rastejar','game_tested':False,'strict_native_mocks':True,
        'live_v9_log_reviewed':True,'checks':checks,
        'source_sha256':{n:hashlib.sha256((CORE/n).read_bytes()).hexdigest() for n in ('prone.lua','posture_movement.lua','cover.lua')}}
(HERE/'runtime_validation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print('POSTURE_RUNTIME_OK',json.dumps(checks,ensure_ascii=False))
