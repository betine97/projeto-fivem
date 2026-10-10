"""Runtime regressions with native mocks. Never starts FiveM or changes assets.

Exercises repeated physical C/Z transitions and injected stale bone poses even
when the native animation task still reports playing. Not a visual game test.
"""
import ast
import hashlib
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'personagens/calca_tatica/test_deps'))
from lupa.lua54 import LuaRuntime

# Reuse the asynchronous native stub, without running the old test/report.
tree = ast.parse((HERE / 'test_runtime_v6.py').read_text(encoding='utf8'))
bootstrap = next(ast.literal_eval(node.value.args[0]) for node in tree.body
                 if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
                 and isinstance(node.value.func, ast.Attribute)
                 and node.value.func.attr == 'execute')
lua = LuaRuntime(unpack_returned_tuples=True)
lua.execute(bootstrap)

def encode(value):
    def convert(v):
        if hasattr(v, 'items'):
            return {str(k): convert(item) for k, item in v.items()}
        return v
    return json.dumps(convert(value), separators=(',', ':'))

lua.globals().encode_json = encode
lua.execute(r'''
json={encode=encode_json}
CidadeCover=false
S.pitch=0;S.forceUpdates=0;S.unloads=0;S.clearSecondary=0;S.clearLook=0
function TriggerEvent(n,...)if S.events[n] then S.events[n](...) end end
function GetEntityModel()return 123 end
function GetCurrentResourceName()return 'cidade_core' end
function GetEntityAnimCurrentTime()return S.anim and S.anim.phase or 0 end
function TaskClearLookAt()S.clearLook=S.clearLook+1 end
function ClearPedSecondaryTask()S.clearSecondary=S.clearSecondary+1 end
function SetPedCanHeadIk(_,b)S.ik.head=b end
function SetPedCanPlayAmbientAnims(_,b)S.ik.ambient=b end
function SetPedCanPlayAmbientBaseAnims(_,b)S.ik.ambientBase=b end
function SetPedCanPlayGestureAnims(_,b)S.ik.gesture=b end
function ForcePedAiAndAnimationUpdate(_,preCamera,zeroTime)
 assert(preCamera==false and zeroTime==true)
 S.forceUpdates=S.forceUpdates+1
 if not S.stubborn then S.pitch=0 end
end
function RemoveAnimDict()S.unloads=S.unloads+1 end
CidadeCombatWeapon.inspect=function()return {barrelPitch=S.pitch,worldBarrelPitch=S.pitch,basisLength=1} end
-- Only real, explicitly permitted native stubs. Unknown globals are errors;
-- the previous permissive fallback concealed ClearPedLookAt's absence.
ClearPedLookAt=nil
local allowed={}
for name in string.gmatch([[
GetGameplayCamFov RegisterKeyMapping RequestAnimDict RequestWeaponAsset
RequestNamedPtfxAsset RemoveNamedPtfxAsset BeginTextCommandThefeedPost
AddTextComponentSubstringPlayerName EndTextCommandThefeedPostTicker
DisableControlAction DisablePlayerFiring RenderScriptCams DestroyCam
SetGameplayCamRelativeHeading SetGameplayCamRelativePitch SetCamNearClip
SetCamFov SetCamCoord SetCamRot SetEntityHeading SetPedEnableWeaponBlocking
DrawRect ShakeCam UseParticleFxAsset StartParticleFxNonLoopedOnPedBone
TaskGoStraightToCoord IsPauseMenuActive IsNuiFocused IsEntityDead
IsPedInAnyVehicle IsEntityInAir IsPedRagdoll IsPedSwimming
IsPedCurrentWeaponSilenced IsPedShooting IsPlayerFreeAiming
HasAnimDictLoaded HasWeaponAssetLoaded HasNamedPtfxAssetLoaded
]],'%S+')do allowed[name]=true end
setmetatable(_G,{__index=function(_,name)
 if not allowed[name] then error('Unknown native/global: '..name) end
 if name:match('^Is')then return function()return false end end
 if name:match('^Has')then return function()return true end end
 if name=='GetGameplayCamFov'then return function()return 60 end end
 return function()end
end})
''')
source = ROOT / 'server-data/resources/cidade_core/prone.lua'
lua.execute(source.read_text(encoding='utf8'))
lua.execute('step(0)')
S = lua.globals().S

def tick(ms=16):
    lua.globals().step(ms)

def settle(ms):
    for _ in range(math.ceil(ms / 16)):
        tick()

def command(name, *args):
    S.commands[name](*args)

def events():
    return [json.loads(line.split('] ', 1)[1]) for line in S.logs.values()
            if line.startswith('[Combate trace] ')]

def count_event(name):
    return sum(item['event'] == name for item in events())

def assert_pose(clip):
    assert S.anim and S.anim.clip == clip, list(S.logs.values())[-10:]
    assert S.anim.flags & 8 == 0
    assert S.anim.flags & 131072
    assert S.anim.speed == 1
    assert all(S.ik[key] is False for key in ('arm','torso','react','head','ambient','ambientBase','gesture'))
    assert S.noAuto

def assert_standing():
    assert S.anim is None and S.pending is None
    assert all(S.ik[key] is True for key in ('arm','torso','react','head','ambient','ambientBase','gesture'))
    assert S.noAuto is False

# Original reload interruption coverage, retaining all three supported poses.
reload_cycles = 0
for weapon in (101, 102):
    for mode in ('ajoelharteste', 'deitadotiro', 'sentadotiro'):
        S.weapon=weapon;S.total=2000;S.clip=30
        command(mode);settle(80);assert_pose('mira')
        for _ in range(12):
            S.pressed[25]=True;S.pressed[24]=True
            shots=S.projectiles;settle(320)
            assert S.projectiles >= shots+2
            assert_pose('recuo')
            S.pressed[24]=False;settle(500);assert_pose('mira')
            assert S.anim.phase == 0
            S.just=45;tick();settle(80);assert_pose('recarga')
            shots=S.projectiles;S.pressed[24]=True;settle(400)
            assert S.projectiles == shots
            S.pressed[24]=False
            S.anim=None;S.pending=None;S.nativeReload=True
            S.ik.arm=True;S.ik.torso=True
            tick();settle(80);assert_pose('recarga')
            assert S.anim.phase > .2
            settle(1850);assert_pose('mira');assert S.anim.phase == 0
            assert S.clip == 30
            reload_cycles += 1
        S.just=194;tick();assert_standing();S.pressed[25]=False

# Repeat actual held-C and Z bindings while aiming. Includes C release after
# kneel -> prone, immediate C stand-up and timed Z stand-up.
transition_cycles = 0
for weapon in (101, 102):
    S.weapon=weapon;S.total=10000;S.clip=30;S.pressed[25]=True
    for cycle in range(40):
        S.raw[0x43]=True;command('+cidade_ajoelhar');settle(80);assert_pose('mira')
        S.pressed[24]=True;settle(160);S.pressed[24]=False
        S.just=45;tick();settle(2300);assert_pose('mira')
        assert S.clip == 30
        command('cidade_deitar');settle(80);assert_pose('mira')
        assert 'deitado' in S.anim.dict
        S.raw[0x43]=False;command('-cidade_ajoelhar');tick();assert_pose('mira')
        S.pressed[24]=True;settle(160);S.pressed[24]=False
        S.just=45;tick();settle(2300);assert_pose('mira')
        if cycle % 2:
            # Abort reload while leaving prone, then re-enter with held C.
            S.clip=10;S.just=45;tick();settle(100)
            S.raw[0x43]=True;command('+cidade_ajoelhar');assert_standing()
            command('-cidade_ajoelhar');S.raw[0x43]=False;tick()
        else:
            command('cidade_deitar');settle(80)
            assert S.anim.clip == 'levantar_deitado'
            settle(1520);assert_standing()
        transition_cycles += 1
    S.pressed[25]=False
assert S.unloads == 0, 'Dictionary unloaded while repeatedly changing poses'

# A 55-degree corrupted wrist while task/phase still appear correct must recover.
S.weapon=101;S.total=1000;S.clip=30
command('deitadotiro');settle(1300);assert_pose('mira')
repairs=count_event('recompor_postura');S.pitch=55
settle(600);assert_pose('mira')
assert count_event('recompor_postura') == repairs+1 and S.pitch == 0
sample=next(item for item in reversed(events()) if item['event']=='recompor_postura')
assert sample['animationPlaying'] and sample['pose']['barrelPitch']==55
assert sample['pose']['ms'] <= sample['ms'] and sample['revision']=='v8-saida-restaurada'

# Recovery during reload preserves the timer/ammo and never fires during reload.
S.clip=10;S.just=45;tick();settle(450);assert_pose('recarga')
phase=S.anim.phase;repairs=count_event('recompor_postura')
S.pitch=60;settle(1100);assert_pose('recarga')
assert count_event('recompor_postura') == repairs+1
assert S.anim.phase > phase and S.clip == 10
settle(800);assert_pose('mira');assert S.clip == 30

# Long bursts seek the same recoil but should not force-update every bullet.
S.pressed[25]=True;S.pressed[24]=True
updates=S.forceUpdates;shots=S.projectiles;settle(1100)
assert S.projectiles-shots >= 9 and S.forceUpdates-updates <= 1
S.pressed[24]=False;settle(500)

# A transient angle clears without repair; persistent errors are rate-limited.
repairs=count_event('recompor_postura');S.pitch=40;settle(110);S.pitch=0;settle(300)
assert count_event('recompor_postura') == repairs
command('deitadotiro');assert_standing()
command('deitadotiro');settle(1300)
S.stubborn=True;S.pitch=60
repairs=count_event('recompor_postura');settle(6500)
assert count_event('recompor_postura')-repairs == 3, 'Recovery not bounded per 10 seconds'
S.stubborn=False;S.pitch=0
command('cidade_deitar');settle(80);assert S.anim.clip=='levantar_deitado'
repairs=count_event('recompor_postura');S.pitch=60;settle(1520)
assert_standing();assert count_event('recompor_postura')==repairs
S.pitch=0;S.pressed[25]=False

# Printing can be disabled, while the ring remains capped and accessible.
command('combatedebug', 0, lua.table_from(['0']))
for _ in range(110):
    command('ajoelharteste');settle(80);command('ajoelharteste')
before=len(S.logs)
command('combatehistorico', 0, lua.table_from(['9999']))
dump=[S.logs[i] for i in range(before+1,len(S.logs)+1)]
assert len(dump)==200 and all(line.startswith('[Combate historico] ') for line in dump)
history=[json.loads(line.split('] ',1)[1]) for line in dump]
assert [item['ms'] for item in history] == sorted(item['ms'] for item in history)
command('combatedebug',0,lua.table_from(['1']))
command('combateinfo')
lua.execute('CidadeCover={active=true}; S.raw[0xA4]=true; S.coverLookMoves=0; function TaskGoStraightToCoord() S.coverLookMoves=S.coverLookMoves+1 end')
settle(100);assert S.coverLookMoves==0, 'Free look took movement from native cover'
lua.execute('CidadeCover=false; S.raw[0xA4]=false')
S.events['onResourceStop']('cidade_core');assert S.unloads==6
assert all('Erro na postura' not in line for line in S.logs.values()), list(S.logs.values())[-20:]
report={
    'revision':'v8-saida-restaurada','game_tested':False,'mock_only':True,
    'repeated_reload_cycles':reload_cycles,'physical_c_z_cycles':transition_cycles,
    'rifles':2,'postures':3,'async_tasks':True,'native_reload_recovery':True,
    'playing_task_bad_bone_recovery':True,'reload_timer_preserved_during_repair':True,
    'recovery_rate_limited':True,'transient_angles_ignored':True,
    'no_per_bullet_force_update':True,'all_ik_restored':True,
    'dictionary_retained_until_shutdown':True,'history_limit':200,
    'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
}
(HERE/'runtime_v8_checks.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print('V8_CONTROLLER_TESTS_OK',json.dumps(report))
