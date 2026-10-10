"""Actual addon metadata/material round trips and test-command lifecycle checks."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'personagens/pipeline_roupas'), str(ROOT / 'laboratorio_fivem/work/test_deps')]
import pipeline as p
import package_addon as package
from lupa.lua54 import LuaRuntime

JOB = ROOT / 'personagens/pipeline_roupas/jobs/west_texas/r002'


class WestTexas(unittest.TestCase):
    def test_native_and_metadata(self):
        report = p.build(JOB)
        self.assertTrue(report['original_geometry_unchanged'])
        self.assertTrue(report['native_normal_specular_and_skeleton_preserved'])
        self.assertTrue(report['diffuse_sampler_verified'])
        self.assertEqual(report['shader_changes'], [
            {'from': 'ped_palette.sps', 'to': 'ped.sps'},
            {'from': 'ped_default_palette.sps', 'to': 'ped_default.sps'}])
        self.assertEqual(set(report['lods']), {0, 1, 2})
        self.assertEqual(report['extra_triangles_high'], 0)
        package.verify_ymt(JOB / 'qa/addon.roundtrip.xml', 'cidade_west_texas_r002', 11, 0)
        for file, sha in p.read(JOB / 'qa/package.json')['files'].items():
            self.assertEqual(p.digest(JOB / 'package/resource' / file), sha)

    def test_command_preserves_outfit_and_restores_first_snapshot(self):
        lua = LuaRuntime()
        lua.execute('''
commands={}; handlers={}; changes={}; currentModel=1; collectionAvailable=true
parts={}; for i=0,11 do parts[i]={drawable=100+i,texture=i,palette=2} end
function joaat(_) return 1 end
function PlayerPedId() return 10 end
function GetEntityModel(_) return currentModel end
function RegisterCommand(name,fn) commands[name]=fn end
function AddEventHandler(name,fn) handlers[name]=fn end
function GetCurrentResourceName() return 'cidade_west_texas' end
function GetPedCollectionsCount(_) return collectionAvailable and 1 or 0 end
function GetPedCollectionName(_,_) return 'cidade_west_texas_r002' end
function IsPedCollectionComponentVariationValid(...) return true end
function GetPedDrawableVariation(_,slot) return parts[slot].drawable end
function GetPedTextureVariation(_,slot) return parts[slot].texture end
function GetPedPaletteVariation(_,slot) return parts[slot].palette end
function SetPedComponentVariation(_,slot,d,t,p)
 parts[slot]={drawable=d,texture=t,palette=p}; changes[#changes+1]=slot
end
function SetPedCollectionComponentVariation(ped,slot,_,d,t,p)
 SetPedComponentVariation(ped,slot,d,t,p)
end
function GetPedCollectionNameFromDrawable(...) return 'cidade_west_texas_r002' end
function print(...) end
''')
        lua.execute((JOB / 'package/resource/client.lua').read_text())
        lua.execute('collectionAvailable=false; commands.camisetatexas(); assert(#changes==0)')
        lua.execute('collectionAvailable=true; currentModel=2; commands.camisetatexas(); assert(#changes==0)')
        lua.execute('currentModel=1; commands.camisetatexas(); commands.camisetatexas()')
        lua.execute('''
for i=0,11 do
 if i~=3 and i~=8 and i~=11 then
  assert(parts[i].drawable==100+i and parts[i].texture==i and parts[i].palette==2)
 end
end
commands.roupastexasanterior()
for i=0,11 do assert(parts[i].drawable==100+i and parts[i].texture==i and parts[i].palette==2) end
commands.camisetatexas(); handlers.onResourceStop('cidade_west_texas')
for i=0,11 do assert(parts[i].drawable==100+i) end
''')


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(WestTexas)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    p.write(JOB / 'qa/tests.json', {'ok': result.wasSuccessful(), 'tests': result.testsRun,
            'failures': len(result.failures), 'errors': len(result.errors), 'real_game_test': 'pending'})
    raise SystemExit(0 if result.wasSuccessful() else 1)
