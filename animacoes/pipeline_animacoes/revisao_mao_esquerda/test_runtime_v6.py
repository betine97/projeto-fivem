"""Controller regression with asynchronous tasks, legacy task lockout and IK reset.

Mocks test state transitions, not FiveM rendering/physics. No live game touched.
"""
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'personagens/calca_tatica/test_deps'))
from lupa.lua54 import LuaRuntime
lua=LuaRuntime(unpack_returned_tuples=True)
lua.execute(r'''
S={now=0,weapon=101,clip=30,total=2000,pressed={},commands={},events={},tasks={},raw={},logs={},clear=0,projectiles=0,ik={}}
CidadeTurret=false
local mt={}
mt.__add=function(a,b)return vector3(a.x+b.x,a.y+b.y,a.z+b.z)end
mt.__sub=function(a,b)return vector3(a.x-b.x,a.y-b.y,a.z-b.z)end
mt.__mul=function(a,b)if type(a)=='number'then a,b=b,a end return vector3(a.x*b,a.y*b,a.z*b)end
function vector3(x,y,z)return setmetatable({x=x,y=y,z=z},mt)end
function print(x)table.insert(S.logs,x)end
function joaat(s)if s=='WEAPON_ASSAULTRIFLE'then return 101 elseif s=='WEAPON_CARBINERIFLE'then return 102 end return 900 end
function GetGameTimer()return S.now end
function Wait()coroutine.yield()end
function CreateThread(f)S.thread=coroutine.create(f)end
function RegisterCommand(n,f)S.commands[n]=f end
function AddEventHandler(n,f)S.events[n]=f end
function PlayerPedId()return 1 end
function PlayerId()return 0 end
function DoesEntityExist(p)return p==1 or p==2 end
function GetSelectedPedWeapon()return S.weapon end
function GetResourceState()return 'stopped'end
function GetEntityCoords()return vector3(0,0,1)end
function GetGameplayCamCoord()return vector3(0,-1,1.5)end
function GetGameplayCamRot()return vector3(0,0,0)end
function GetEntityHeading()return 0 end
function GetPedBoneCoords()return vector3(0,0,1)end
function IsUsingKeyboard()return true end
function GetFrameTime()return .016 end
function GetDisabledControlNormal()return 0 end
function CreateCam()return 4 end
function StartExpensiveSynchronousShapeTestLosProbe()return 1 end
function GetShapeTestResult()return 2,false,vector3(0,200,1)end
function GetCamCoord()return vector3(0,-1,1.5)end
function GetCamRot()return vector3(0,0,0)end
function GetDisabledRawKeyDown()return false end
function IsDisabledRawKeyDown(k)return S.raw[k] or false end
function IsDisabledControlPressed(_,k)return S.pressed[k] or false end
function IsDisabledControlJustPressed(_,k)return S.just==k end
function IsControlJustPressed(_,k)return S.just==k end
function IsControlPressed()return false end
function IsPedReloading()return S.nativeReload or false end
function ClearPedTasksImmediately()S.clear=S.clear+1;S.anim=nil;S.pending=nil;S.nativeReload=false end
function ClearPedTasks()S.anim=nil;S.pending=nil end
function ClearPedSecondaryTask()end
function StopAnimTask(_,d,c)if S.anim and S.anim.dict==d and S.anim.clip==c then S.anim=nil end;S.pending=nil end
function TaskPlayAnim(_,d,c,bi,bo,duration,flags,rate)
 local task={dict=d,clip=c,flags=flags,phase=0,speed=rate}
 table.insert(S.tasks,task)
 -- Reproduce native lockout: flag 8 holds the previous full-body pose.
 if S.anim and S.anim.flags&8~=0 and flags&131072==0 then return end
 S.pending=task;S.ready=S.now+30
end
function IsEntityPlayingAnim(_,d,c)
 if S.pending and S.now>=S.ready then S.anim=S.pending;S.pending=nil end
 return S.anim~=nil and S.anim.dict==d and S.anim.clip==c
end
function SetEntityAnimCurrentTime(_,d,c,t)
 if S.anim and S.anim.dict==d and S.anim.clip==c then S.anim.phase=t end
end
function SetEntityAnimSpeed(_,d,c,s)
 if S.anim and S.anim.dict==d and S.anim.clip==c then S.anim.speed=s end
end
function SetPedCanArmIk(_,b)S.ik.arm=b end
function SetPedCanTorsoIk(_,b)S.ik.torso=b end
function SetPedCanTorsoReactIk(_,b)S.ik.react=b end
function SetWeaponsNoAutoreload(b)S.noAuto=b end
function GetAmmoInClip()return true,S.clip end
function GetAmmoInPedWeapon()return S.total end
function GetMaxAmmoInClip()return 30 end
function SetAmmoInClip(_,_,n)S.clip=n end
function SetPedAmmo(_,_,n)S.total=n;S.ik.arm=true;S.ik.torso=true end
function GetWeaponTimeBetweenShots()return .1 end
function GetWeaponDamage()return 30 end
function GetEntityBoneIndexByName()return 0 end
function GetWorldPositionOfEntityBone()return vector3(0,0,1)end
function ShootSingleBulletBetweenCoords()S.projectiles=S.projectiles+1 end
CidadeCombatWeapon={entity=function()return 2 end,create=function()return true end,update=function()return true end,destroy=function()end}
function step(ms)
 S.now=S.now+ms
 if S.pending and S.now>=S.ready then S.anim=S.pending;S.pending=nil end
 local ok,err=coroutine.resume(S.thread);assert(ok,err)
 S.just=nil
end
setmetatable(_G,{__index=function(_,k)
 if k:match('^Is')then return function()return false end end
 if k:match('^Has')then return function()return true end end
 return function()end
end})
''')
source=ROOT/'server-data/resources/cidade_core/prone.lua'
lua.execute(source.read_text(encoding='utf8'))
lua.execute('step(0)') # Start coroutine at its first frame wait.
state=lua.globals().S
step=lua.globals().step
def tick(ms=16):
    step(ms)
def settle(ms):
    for _ in range(ms//16):tick()
def assert_pose(clip):
    assert state.anim and state.anim.clip==clip,(clip,list(state.logs.values())[-5:])
    assert state.anim.flags&8==0, 'Noninterruptible clip'
    assert state.anim.flags&131072, 'Transition does not force start'
    assert not state.ik.arm and not state.ik.torso and not state.ik.react
    assert state.noAuto
cases=0
for weapon in (101,102):
    for mode in ('ajoelharteste','deitadotiro','sentadotiro'):
        state.weapon=weapon;state.total=2000;state.clip=30
        state.commands[mode]()
        settle(80);assert_pose('mira')
        expected=f"cidade_{ {'ajoelharteste':'ajoelhado','deitadotiro':'deitado','sentadotiro':'sentado'}[mode]}_v{6 if weapon==101 else 5}_{'ak' if weapon==101 else 'ar'}"
        assert state.anim.dict==expected
        for cycle in range(12):
            state.pressed[25]=True;state.pressed[24]=True
            shots=state.projectiles
            settle(320)
            assert state.projectiles>=shots+2
            assert_pose('recuo')
            state.pressed[24]=False
            settle(500);assert_pose('mira');assert state.anim.phase==0
            state.just=45;tick();settle(80);assert_pose('recarga')
            shots=state.projectiles
            state.pressed[24]=True
            settle(400);assert state.projectiles==shots,'Fires during reload'
            state.pressed[24]=False
            # Interrupt full-body task and restore native IK midway through reload.
            state.anim=None;state.pending=None;state.nativeReload=True
            state.ik.arm=True;state.ik.torso=True
            tick();settle(80);assert_pose('recarga');assert state.anim.phase>.2
            settle(1850);assert_pose('mira');assert state.anim.phase==0
            assert state.clip==30
            state.pressed[25]=False;tick();state.pressed[25]=True;tick()
            cases+=1
        state.just=194;tick();assert state.anim is None
        assert state.ik.arm and state.ik.torso and state.ik.react and not state.noAuto
        state.pressed[25]=False
# Recovery of a dropped recoil preserves elapsed time instead of resetting it.
state.weapon=101;state.commands['ajoelharteste']();settle(80)
state.pressed[25]=True;state.pressed[24]=True;tick()
state.pressed[24]=False;settle(100)
state.anim=None;state.pending=None;settle(180)
assert_pose('recuo');assert state.anim.phase>.4
settle(220);assert_pose('mira')
# Exit and cancellation restore controls/IK, including the prone stand-up clip.
state.commands['deitadotiro']();settle(80)
state.commands['cidade_deitar']();settle(80)
assert state.anim.clip=='levantar_deitado' and state.anim.speed==1
settle(1520);assert state.anim is None and state.ik.arm
assert all('Erro na postura' not in s for s in state.logs.values()),list(state.logs.values())[-10:]
report={'game_tested':False,'mock_only':True,'repeated_reload_cycles':cases,'rifles':2,'postures':3,'async_tasks':True,'native_reload_recovery':True,'recoil_recovery':True,'noninterruptible_flags_removed':True,'cleanup_and_prone_exit':True}
(Path(__file__).parent/'runtime_v6_checks.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print('V6_CONTROLLER_TESTS_OK',json.dumps(report))
