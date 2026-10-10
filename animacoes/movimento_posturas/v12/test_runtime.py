"""Regression: consumable asynchronous probes and real-coordinate telemetry.

Includes the previous input/weapon suite. Native physics is NOT emulated or
claimed verified: injected coordinates exercise detection of actual progress
and rollback independently of the task flags.
"""
import hashlib
import json
import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CORE = ROOT / 'server-data/resources/cidade_core'
previous = runpy.run_path(str(HERE.parent / 'v11/test_runtime.py'))
setup, tick, settle, command, check_errors, logs = (
    previous[name] for name in ('setup', 'tick', 'settle', 'command', 'check_errors', 'logs')
)
checks = list(previous['checks'])
directions = {32: 'fwd', 33: 'bwd', 34: 'left', 35: 'right'}

def consumable_probes(lua):
    lua.execute('''
local oldResult=GetShapeTestResult
S.consumed={};S.completed=0
function GetShapeTestResult(h)
 local r=S.rays[h]
 if not r or not r.capsule then return oldResult(h) end
 assert(not S.consumed[h], 'Completed shape-test handle read twice: '..h)
 if S.probeInvalid then S.consumed[h]=true;return 0 end
 if S.probeStuck or S.now-r.at<((h%3)+1)*16 then return 1 end
 S.consumed[h]=true;S.completed=S.completed+1
 return 2,S.wall and true or false,vector3(0,0,.38),vector3(0,0,1)
end
''')

for weapon in (101, 102, 103):
    for key, direction in directions.items():
        lua, S, M = setup()
        consumable_probes(lua)
        S.weapon = weapon
        command(lua, S, 'cidade_deitar')
        settle(lua, 80)
        S.pressed[key] = True
        settle(lua, 120)
        assert M.crawling and M.crawlDirection == direction
        count = len(S.tasks)
        settle(lua, 2200)
        assert M.crawling and len(S.tasks) == count, 'Valid staggered probes restarted the crawl'
        assert S.completed > 12
        flags = S.primary.flags
        assert flags & (262144 | 524288 | 4) == (262144 | 524288 | 4)
        assert flags & (512 | 1024 | 2048) == 0, 'Collision/gravity overridden'
        S.pressed[key] = False
        tick(lua)
        assert not M.crawling
        check_errors(S)
checks.append('12 armed/unarmed directional crawls: staggered consumable probes never reread completed handles or restart a valid task')

for failure in ('wall', 'probeStuck', 'probeInvalid'):
    lua, S, M = setup()
    consumable_probes(lua)
    command(lua, S, 'cidade_deitar')
    settle(lua, 80)
    S.pressed[32] = True
    settle(lua, 120)
    assert M.crawling
    S[failure] = True
    settle(lua, 300)
    assert not M.crawling, failure
    check_errors(S)
checks.append('Active movement stops on obstacle, expired pending query or invalid result; no blind restart')

for key, direction in directions.items():
    lua, S, M = setup()
    consumable_probes(lua)
    lua.execute('''
S.position=vector3(0,0,1);S.velocity=0
function GetEntityCoords() return S.position end
function GetEntitySpeed() return S.velocity end
''')
    command(lua, S, 'cidade_deitar')
    settle(lua, 80)
    S.pressed[key] = True
    settle(lua, 120)
    dx, dy = {'fwd': (0, 1), 'bwd': (0, -1), 'left': (-1, 0), 'right': (1, 0)}[direction]
    # Inject world coordinates, not animation offsets: telemetry must report
    # sustained movement across several loop boundaries.
    for frame in range(160):
        S.position = lua.globals().vector3(dx * (frame + 1) * .01, dy * (frame + 1) * .01, 1)
        tick(lua)
    state = M.snapshot(1)
    assert state.crawlProgress > 1.59 and state.crawlCycles >= 2
    assert not any('[Rastejo]' in line and 'retorno_detectado' in line for line in logs(S))
    # A physics/network correction must be visible even while the clip plays.
    S.position = lua.globals().vector3(dx * 1.35, dy * 1.35, 1)
    tick(lua)
    assert any('retorno_detectado' in line for line in logs(S))
    S.pressed[key] = False
    tick(lua)
    S.position = lua.globals().vector3(dx * 1.1, dy * 1.1, 1)
    settle(lua, 300)
    assert any('retorno_apos_parar' in line for line in logs(S))
    command(lua, S, 'rastejodebug')
    assert any('[Rastejo historico]' in line for line in logs(S))
    check_errors(S)
checks.append('Four directions: telemetry measures sustained world progress, loop boundaries, rollback while moving and rollback after release')

# A direction change needs a fresh route, with no obsolete pending results.
lua, S, M = setup()
consumable_probes(lua)
command(lua, S, 'cidade_deitar')
settle(lua, 80)
for key, direction in directions.items():
    for other in directions:
        S.pressed[other] = other == key
    settle(lua, 140)
    assert M.crawling and M.crawlDirection == direction
check_errors(S)
checks.append('Held direction switches start a fresh validated route and replace only the owned crawl task')

report = {'revision': M.revision, 'game_tested': False, 'strict_native_mocks': True,
          'injected_coordinates_only': True, 'checks': checks,
          'source_sha256': {name: hashlib.sha256((CORE / name).read_bytes()).hexdigest()
                            for name in ('posture_movement.lua', 'prone.lua')}}
(HERE / 'runtime_validation.json').write_text(json.dumps(report, indent=2), encoding='utf8')
print('V12_RUNTIME_OK', json.dumps(checks[-5:], ensure_ascii=False))
