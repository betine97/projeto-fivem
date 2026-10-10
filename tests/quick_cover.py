"""Quick cover Lua controller + asynchronous synthetic collision regression.

No FiveM/server launch. Native locomotion/animations are mocked, not rendered.
"""
import hashlib
import json
import math
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'personagens/calca_tatica/test_deps'))
from lupa.lua54 import LuaRuntime

BOOT=r'''
S={now=10000,ped=1,position={x=0,y=0,z=1},weapon=101,threads={},commands={},events={},
 logs={},controls={},tasks={},pool={},inCover=false,going=false,peeking=false,clear=0}
function vector3(x,y,z)return {x=x,y=y,z=z}end
function GetGameTimer()return S.now end
function Wait()coroutine.yield()end
function CreateThread(f)table.insert(S.threads,coroutine.create(f))end
function RegisterCommand(n,f)S.commands[n]=f end
function RegisterKeyMapping(n,_,_,key)S.mapping=key end
function AddEventHandler(n,f)
 S.events[n]=S.events[n] or {};table.insert(S.events[n],f)
end
function TriggerEvent(n,...)for _,f in ipairs(S.events[n] or {})do f(...)end end
function print(line)table.insert(S.logs,line)end
function PlayerPedId()return S.ped end
function PlayerId()return 0 end
function DoesEntityExist(p)return p~=nil and p>0 end
function GetEntityCoords(p)
 if p==2 then return vector3(0,-12,1) end
 if p==100 then return S.carPosition or vector3(0,3.5,.75) end
 return S.position
end
function GetEntityType(p)return p==100 and 2 or 1 end
function GetEntitySpeed()return S.carSpeed or 0 end
function GetSelectedPedWeapon()return S.weapon end
function GetGameplayCamRot()return {z=0,x=0}end
function GetGamePool()return S.pool end
function IsPedInCombat()return S.attacker or false end
function HasEntityBeenDamagedByEntity()return false end
function IsEntityDead()return S.dead or false end
function IsPedInAnyVehicle()return S.vehicle or false end
function IsPedRagdoll()return S.ragdoll or false end
function IsPedSwimming()return false end
function IsEntityInAir()return S.air or false end
function GetEntityCollisionDisabled()return S.flight or false end
function IsPauseMenuActive()return S.pause or false end
function IsNuiFocused()return false end
function GetResourceState()return S.drone and 'started' or 'stopped' end
exports={fpv_drone_runtime={isPiloting=function()return S.drone end}}
function IsPedInCover()return S.inCover end
function IsPedAimingFromCover()return S.peeking end
function IsPedGoingIntoCover()return S.going end
function IsDisabledControlJustPressed(_,k)return S.just==k end
function DisableControlAction(_,k)S.controls[k]=true end
function DisablePlayerFiring()S.firingBlocked=true end
function BeginTextCommandThefeedPost()end
function AddTextComponentSubstringPlayerName(text)S.message=text end
function EndTextCommandThefeedPostTicker()end
function GetCurrentResourceName()return 'cidade_core' end
function ClearPedTasks()S.clear=S.clear+1;S.inCover=false;S.going=false;S.peeking=false end
function ForcePedAiAndAnimationUpdate()S.air=false end
function TaskFollowNavMeshToCoord(p,x,y,z,speed,timeout,radius,flags,heading)
 assert(speed==3 and timeout==6500 and flags==32)
 table.insert(S.tasks,{name='route',x=x,y=y,z=z})
 S.destination={x=x,y=y,z=z};S.routeAt=S.now
end
function TaskGoStraightToCoord(p,x,y,z,speed,timeout,heading,slide)
 assert(speed==3 and timeout==-1)
 table.insert(S.tasks,{name='straight',x=x,y=y,z=z})
 S.destination={x=x,y=y,z=z};S.routeAt=S.now
end
function RequestAnimSet()end
function HasAnimSetLoaded()return not S.missingClipset end
function RemoveAnimSet()S.removedSets=(S.removedSets or 0)+1 end
function SetEntityHeading(_,heading)S.heading=heading end
function SetPedMovementClipset(_,clip)assert(clip=='move_ped_crouched');S.crouch=clip end
function SetPedStrafeClipset(_,clip)
 if S.failStrafe then error('injected clipset exception') end
 S.strafe=clip
end
function ResetPedMovementClipset()S.crouch=nil;S.resetCrouch=(S.resetCrouch or 0)+1 end
function ResetPedStrafeClipset()S.strafe=nil end
function TaskSeekCoverToCoords(p,x,y,z,tx,ty,tz,time,peek)
 assert(time==4000 and peek==true)
 table.insert(S.tasks,{name='cover',x=x,y=y,z=z,enemyY=ty})
 S.going=true;S.enterAt=S.now
end
function GetSafeCoordForPed(x,y,z,_,flags)
 assert(flags==8)
 if S.noNav then return false,vector3(0,0,0) end
 if S.badNav then return true,vector3(x,y+1.3,z) end
 if S.coarseNav then return true,vector3(x+1.2,y,z+.8) end
 return true,vector3(x,y,z)
end
function step(ms)
 S.now=S.now+ms;S.controls={};S.firingBlocked=false
 if S.routeAt and not S.stuck and S.now-S.routeAt>250 then S.position=vector3(S.destination.x,S.destination.y,S.destination.z+1);S.routeAt=nil end
 if S.enterAt and not S.rejectCover and S.now-S.enterAt>250 then S.inCover=true;S.going=false;S.enterAt=nil end
 for _,thread in ipairs(S.threads)do
  if coroutine.status(thread)~='dead' then local ok,err=coroutine.resume(thread);assert(ok,err)end
 end
 S.just=nil
end
'''

def runtime(boxes):
    lua=LuaRuntime(unpack_returned_tuples=True);lua.execute(BOOT)
    S=lua.globals().S;V=lua.globals().vector3
    probes={};counter=0
    def encode(table):
        def convert(v):return {str(k):convert(w) for k,w in v.items()} if hasattr(v,'items') else v
        return json.dumps(convert(table))
    lua.globals().json=lua.table_from({'encode':encode})
    def begin(now,ax,ay,az,bx,by,bz,*rest):
        nonlocal counter
        radius=float(rest[0]) if len(rest)==4 else 0
        counter+=1;probes[counter]=(now,(ax,ay,az),(bx,by,bz),radius)
        return counter
    def result(handle,now,pending):
        if pending:return 1,False,0,0,0,0,0,0,0
        started,a,b,radius=probes[handle]
        if now<=started:return 1,False,0,0,0,0,0,0,0
        hits=[]
        # Ground plane, only downward rays/capsules.
        if b[2]<a[2] and a[2]>=radius and b[2]<=radius:
            t=(radius-a[2])/(b[2]-a[2]);hits.append((t,(0,0,1),0))
        for box in boxes:
            # Slab intersection with an expanded AABB for capsule clearance.
            low=[box[i]-radius for i in range(3)]
            high=[box[i+3]+radius for i in range(3)]
            near,far=0.,1.;normal=(0,0,0);valid=True
            for axis in range(3):
                delta=b[axis]-a[axis]
                if abs(delta)<1e-9:
                    if not low[axis]<=a[axis]<=high[axis]:valid=False;break
                    continue
                t1,t2=(low[axis]-a[axis])/delta,(high[axis]-a[axis])/delta
                sign=-1 if delta>0 else 1
                if t1>t2:t1,t2=t2,t1
                if t1>near:
                    near=t1;normal=tuple(sign if j==axis else 0 for j in range(3))
                far=min(far,t2)
                if near>far:valid=False;break
            entity=box[6] if len(box)>6 else 0
            if entity==100 and len(box)>7 and normal[2]==0:
                normal=tuple(c*.9165 for c in normal[:2])+(box[7],)
            if valid and 0<=near<=1:hits.append((near,normal,entity))
        if hits:
            t,normal,entity=min(hits,key=lambda item:item[0])
            point=[a[i]+t*(b[i]-a[i]) for i in range(3)]
            return 2,True,*point,*normal,entity
        return 2,False,*b,0,0,0,0
    lua.globals().start_shape=begin
    lua.globals().shape_result=result
    # Pass scalars into Python; do not re-enter Lua getters from its coroutine.
    lua.execute(r'''
    function StartShapeTestLosProbe(...)return start_shape(S.now,...)end
    function StartShapeTestCapsule(...)return start_shape(S.now,...)end
    function GetShapeTestResult(h)
      local status,hit,x,y,z,nx,ny,nz,e=shape_result(h,S.now,S.pendingForever)
      return status,hit,vector3(x,y,z),vector3(nx,ny,nz),e
    end
    ''')
    source=ROOT/'server-data/resources/cidade_core/cover.lua'
    lua.execute(source.read_text(encoding='utf8'));lua.globals().step(0)
    def tick(ms=16):lua.globals().step(ms)
    def settle(ms):
        for _ in range(math.ceil(ms/16)):tick()
    def start():S.commands.cidade_cobertura()
    def event(n,*args):lua.globals().TriggerEvent(n,*args)
    def assert_clean():
        assert not lua.globals().CidadeCover.active,list(S.logs.values())[-5:]
        assert not any('"erro"' in line for line in S.logs.values()),list(S.logs.values())[-5:]
    return lua,S,tick,settle,start,event,assert_clean

cases=[]
for height in (.95,2.5):
    for weapon in (101,0):
        lua,S,tick,settle,start,event,clean=runtime([(-5,3,0,5,3.3,height)])
        S.weapon=weapon;start();settle(2000)
        assert lua.globals().CidadeCover.phase=='covered',list(S.logs.values())[-8:]
        assert S.weapon==weapon and S.mapping=='Q'
        assert S.tasks[1].name=='route' and S.tasks[2].name=='cover'
        assert S.destination.y<3 and S.destination.y>2
        entry=next(json.loads(x.split('] ',1)[1]) for x in S.logs.values() if '"correr_para_barreira"' in x)
        assert entry['height']==('baixa' if height<1.5 else 'alta')
        tick();assert not S.firingBlocked and not S.controls[24] and not S.controls[45]
        # Peeking may temporarily report only aiming-from-cover.
        S.inCover=False;S.peeking=True;settle(1000)
        assert lua.globals().CidadeCover.phase=='covered'
        start();clean();assert S.clear==1
        cases.append('armed' if weapon else 'unarmed')

for label,boxes,setup in (
    ('open_ground',[],None),
    ('narrow_pole',[(-.1,3,0,.1,3.3,2.5)],None),
    ('too_short',[(-5,3,0,5,3.3,.3)],None),
    ('async_timeout',[(-5,3,0,5,3.3,2.5)],'pendingForever'),
):
    lua,S,tick,settle,start,event,clean=runtime(boxes)
    if setup:S[setup]=True
    start();settle(3000);clean();assert len(S.tasks)==0,label
    cases.append(label)

# Navigation spawn coordinates are not exact cover sockets. Keep the checked
# raw point, including when only a directly walkable approach is available.
for mode in ('noNav','badNav','coarseNav'):
    lua,S,tick,settle,start,event,clean=runtime([(-5,3,0,5,3.3,1.3)])
    S[mode]=True;start();settle(2200)
    assert lua.globals().CidadeCover.phase=='covered',list(S.logs.values())[-8:]
    assert abs(S.destination.x)<.01 and abs(S.destination.y-2.38)<.01
    assert S.tasks[1].name==('route' if mode=='coarseNav' else 'straight')
    start();clean();cases.append('spawn_coordinate_'+mode)

for label,wall,position in (
    ('wall_beside_camera',(3,-5,0,3.3,5,1.3),None),
    ('wall_behind_camera',(-5,-3.3,0,5,-3,1.3),None),
    ('already_touching_wall',(-5,.35,0,5,.65,1.3),(0,.10,1)),
):
    lua,S,tick,settle,start,event,clean=runtime([wall])
    if position:S.position=lua.globals().vector3(*position)
    start();settle(2200)
    assert lua.globals().CidadeCover.phase=='covered',list(S.logs.values())[-8:]
    start();clean();cases.append(label)

# Vehicle body sides can be curved, and car collision need not have a native
# cover node. Armed/unarmed fallback crouches without claiming native cover.
for weapon in (101,0):
    for kind in ('parked_car','low_wall'):
        wall=(-2,3,0,2,4,1.35,100,.40) if kind=='parked_car' else (-5,3,0,5,3.3,1.3)
        lua,S,tick,settle,start,event,clean=runtime([wall])
        S.weapon=weapon;S.rejectCover=True;S.noNav=kind=='parked_car'
        start();settle(3500)
        assert lua.globals().CidadeCover.phase=='crouched',list(S.logs.values())[-10:]
        assert not S.inCover and S.crouch=='move_ped_crouched' and S.strafe
        assert S.weapon==weapon and not S.firingBlocked and not S.controls[45]
        if kind=='parked_car':
            entry=next(json.loads(x.split('] ',1)[1]) for x in S.logs.values() if '"correr_para_barreira"' in x)
            assert entry['barrier']=='veiculo'
        start();clean();assert S.crouch is None and S.strafe is None
        cases.append(kind+('_armed' if weapon else '_unarmed'))

lua,S,tick,settle,start,event,clean=runtime([(-2,3,0,2,4,1.35,100)])
S.carSpeed=2;start();settle(3000);clean();assert len(S.tasks)==0
assert any('veiculo_em_movimento' in x for x in S.logs.values())
cases.append('moving_vehicle_rejected')
for when in ('moving','crouched'):
    lua,S,tick,settle,start,event,clean=runtime([(-2,3,0,2,4,1.35,100)])
    S.rejectCover=True;start();settle(300 if when=='moving' else 3500)
    assert lua.globals().CidadeCover.phase==when
    S.carPosition=lua.globals().vector3(0,5,.75);tick();clean()
    assert S.crouch is None;cases.append('vehicle_displaced_'+when)

# An actual attacker still vetoes cover on the exposed side.
lua,S,tick,settle,start,event,clean=runtime([(-5,3,0,5,3.3,1.3)])
S.pool=lua.table_from([2]);S.attacker=True;start();settle(3000);clean()
assert len(S.tasks)==0 and any('lado_exposto_ao_atacante' in x for x in S.logs.values())
cases.append('wall_on_exposed_side_of_attacker')

for label,action in (
    ('crouch_cancel_for_pose',lambda lua,S,event:event('cidade:preparePilot')),
    ('crouch_death',lambda lua,S,event:setattr(S,'dead',True)),
    ('crouch_walk_out',lambda lua,S,event:setattr(S,'position',lua.globals().vector3(0,0,1))),
    ('crouch_resource_stop',lambda lua,S,event:event('onResourceStop','cidade_core')),
):
    lua,S,tick,settle,start,event,clean=runtime([(-5,3,0,5,3.3,1.3)])
    S.rejectCover=True;start();settle(3500)
    assert lua.globals().CidadeCover.phase=='crouched'
    action(lua,S,event);settle(200);clean();assert S.crouch is None and S.strafe is None
    if label=='crouch_resource_stop':assert S.removedSets==2
    cases.append(label)

lua,S,tick,settle,start,event,clean=runtime([(-5,3,0,5,3.3,1.3)])
S.rejectCover=True;S.missingClipset=True;start();settle(7000);clean()
assert S.crouch is None;cases.append('crouch_set_load_failure')

# Partial native failure must restore movement and allow a new Q attempt.
lua,S,tick,settle,start,event,clean=runtime([(-5,3,0,5,3.3,1.3)])
S.rejectCover=True;S.failStrafe=True;start();settle(3500)
assert not lua.globals().CidadeCover.active and S.crouch is None and S.strafe is None
assert any('injected clipset exception' in x for x in S.logs.values())
S.failStrafe=False;start();settle(3500)
assert lua.globals().CidadeCover.phase=='crouched';start()
assert S.crouch is None;cases.append('partial_clipset_exception_and_retry')

# A real attacker behind the ped overrides the camera direction.
lua,S,tick,settle,start,event,clean=runtime([(-5,-3.3,0,5,-3,1)])
S.pool=lua.table_from([2]);S.attacker=True;start();settle(2000)
assert lua.globals().CidadeCover.phase=='covered'
assert S.tasks[2].enemyY<0;start();clean();cases.append('attacker_direction')

for label,setup in (('stuck_route','stuck'),('native_cover_rejected','rejectCover')):
    lua,S,tick,settle,start,event,clean=runtime([(-5,3,0,5,3.3,1)])
    S[setup]=True;start();settle(7000);clean();assert S.clear==1
    cases.append(label)

# Stop during an asynchronous scan; old generation cannot start locomotion.
lua,S,tick,settle,start,event,clean=runtime([(-5,3,0,5,3.3,1)])
start();tick();start();settle(3000);clean();assert len(S.tasks)==0
cases.append('cancel_pending_search')
for name in ('cidade:preparePilot','cidade:stopProne','onResourceStop'):
    lua,S,tick,settle,start,event,clean=runtime([(-5,3,0,5,3.3,1)])
    start();settle(2000);assert lua.globals().CidadeCover.active
    event(name,'cidade_core');clean();assert S.clear==1
    cases.append(name)

for mode in ('dead','vehicle','flight','drone','pause'):
    lua,S,tick,settle,start,event,clean=runtime([(-5,3,0,5,3.3,1)])
    S[mode]=True;start();settle(100);clean();assert len(S.tasks)==0
    if mode in ('vehicle','flight','drone'):assert not S.controls[44],mode
    cases.append('reject_'+mode)

# Death/character swap aborts moving; natural manual cover exit keeps user's task.
lua,S,tick,settle,start,event,clean=runtime([(-5,3,0,5,3.3,1)])
start();settle(2000);S.inCover=False;S.going=False;settle(600);clean();assert S.clear==0
cases.append('manual_exit_preserves_task')
lua,S,tick,settle,start,event,clean=runtime([(-5,3,0,5,3.3,1)])
start();settle(2000);S.ped=3;tick();clean()
cases.append('character_swap')

# Starting cover from a custom prone pose restores normal native locomotion.
lua,S,tick,settle,start,event,clean=runtime([(-5,3,0,5,3.3,1)])
lua.execute('CidadeCombatWeapon={inspect=function()return {barrelPitch=0}end}')
S.air=True;start();settle(2000);assert lua.globals().CidadeCover.phase=='covered'
start();clean();cases.append('authored_prone_to_native_cover')

# Death aborts entry; Q cancellation remains safe across repeated generations.
lua,S,tick,settle,start,event,clean=runtime([(-5,3,0,5,3.3,1)])
S.stuck=True;start();settle(400);S.dead=True;tick();clean()
cases.append('death_during_route')
lua,S,tick,settle,start,event,clean=runtime([(-5,3,0,5,3.3,1)])
for cycle in range(30):
    start();tick();start();settle(100);clean()
assert len(S.tasks)==0
cases.append('30_repeated_scan_cancellations')

source=ROOT/'server-data/resources/cidade_core/cover.lua'
out=ROOT/'animacoes/cobertura_rapida'
out.mkdir(exist_ok=True)
report={'revision':'cobertura-v2-carros-muros','game_tested':False,'mock_only':True,
        'scenarios_passed':len(cases),'scenarios':cases,
        'synthetic_collision':True,'async_shape_tests':True,
        'native_animations_not_rendered':True,
        'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest()}
(out/'test_results.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print('QUICK_COVER_TESTS_OK',json.dumps(report))
