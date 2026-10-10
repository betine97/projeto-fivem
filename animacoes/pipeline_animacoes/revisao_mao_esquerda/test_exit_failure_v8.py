"""Reproduce the logged v7 failure, then exercise v8 with cleanup exceptions."""
import ast
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'personagens/calca_tatica/test_deps'))
from lupa.lua54 import LuaRuntime

def setup_block(path):
    tree = ast.parse(path.read_text(encoding='utf8'))
    return next(ast.literal_eval(n.value.args[0]) for n in tree.body
                if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)
                and isinstance(n.value.func, ast.Attribute)
                and n.value.func.attr == 'execute'
                and isinstance(n.value.args[0], ast.Constant))

def runtime(path):
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute(setup_block(HERE / 'test_runtime_v6.py'))
    lua.globals().encode_json = lambda _: '{}'
    lua.execute(setup_block(HERE / 'test_runtime_v8.py'))
    lua.execute(path.read_text(encoding='utf8'))
    lua.globals().step(0)
    return lua, lua.globals().S

# The old code MUST fail with the exact missing native recorded by FiveM.
old, state = runtime(HERE.parent / 'backup_v7_pose/prone.lua')
state.raw[0x43] = True
state.commands['+cidade_ajoelhar']()
for _ in range(5): old.globals().step(16)
state.raw[0x43] = False
try:
    old.globals().step(16)  # physical C release executes stop outside xpcall
except Exception as exc:
    assert 'ClearPedLookAt' in str(exc), str(exc)
else:
    raise AssertionError('Old missing native was concealed by the mock')
assert old.eval('coroutine.status(S.thread)') == 'dead'
assert state.ik.arm is False  # original cleanup never restored native IK

new, state = runtime(ROOT / 'server-data/resources/cidade_core/prone.lua')
new.execute('function TaskClearLookAt() if S.failLook then error("injected look cleanup failure") end S.clearLook=S.clearLook+1 end')
for cycle in range(60):
    state.clip=30;state.total=10000
    state.raw[0x43]=True;state.commands['+cidade_ajoelhar']()
    state.pressed[25]=True;state.pressed[24]=True
    for _ in range(20): new.globals().step(16)
    assert state.anim and 'ajoelhado' in state.anim.dict
    state.pressed[24]=False;state.raw[0x43]=False
    state.failLook = cycle % 2 == 0
    new.globals().step(16)
    assert state.anim is None and state.pending is None
    assert all(state.ik[k] is True for k in ('arm','torso','react','head','ambient','ambientBase','gesture'))
    assert new.eval('coroutine.status(S.thread)') == 'suspended'
    state.failLook=False
    state.raw[0x43]=True;state.commands['+cidade_ajoelhar']()
    for _ in range(5): new.globals().step(16)
    assert state.anim and 'ajoelhado' in state.anim.dict
    state.commands['cidade_deitar']()
    for _ in range(5): new.globals().step(16)
    assert state.anim and 'deitado' in state.anim.dict and state.pitch==0
    state.raw[0x43]=False;state.commands['-cidade_ajoelhar']()
    state.commands['cidade_deitar']()
    for _ in range(110): new.globals().step(16)
    assert state.anim is None
    state.pressed[25]=False
assert sum('injected look cleanup failure' in s for s in state.logs.values()) == 30
report={'mock_only':True,'game_tested':False,'old_v7_coroutine_crash_reproduced':True,
        'shoot_kneel_stand_reenter_prone_cycles':60,'cleanup_exceptions_survived':30,
        'native_ik_restored':True,'unknown_native_stubs_forbidden':True}
(HERE/'exit_failure_v8_checks.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print('V8_EXIT_TESTS_OK',json.dumps(report))
