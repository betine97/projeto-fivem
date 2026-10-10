"""Verify real jeans exports and independent combination/restoration of both Lua commands."""
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'personagens/pipeline_roupas'), str(ROOT / 'laboratorio_fivem/work/test_deps')]
import pipeline as p
import package_addon as package
from lupa.lua54 import LuaRuntime
JOB = ROOT / 'personagens/pipeline_roupas/jobs/jeans_washed/r001'
SHIRT = ROOT / 'personagens/pipeline_roupas/jobs/west_texas/r002'


class Jeans(unittest.TestCase):
    def test_original_and_addon_round_trips(self):
        report = p.build(JOB)
        self.assertTrue(report['original_geometry_unchanged'])
        self.assertTrue(report['native_materials_and_skeleton_unchanged'])
        self.assertTrue(report['diffuse_sampler_verified'])
        self.assertEqual(report['extra_triangles_high'], 0)
        self.assertEqual(report['lods'], [0,1,2])
        package.verify_ymt(JOB / 'qa/addon.roundtrip.xml', 'cidade_jeans_washed_r001', 4, 1)
        for file, sha in p.read(JOB / 'qa/package.json')['files'].items():
            self.assertEqual(p.digest(JOB / 'package/resource' / file), sha)

    def test_shirt_and_jeans_combine_and_restore_independently(self):
        lua = LuaRuntime()
        lua.execute('''
commands={}; handlers={}; changes={}; model=1; collectionAvailable=true
parts={}; for i=0,11 do parts[i]={drawable=100+i,texture=i,palette=2} end
function joaat(_) return 1 end
function PlayerPedId() return 10 end
function GetEntityModel(_) return model end
function RegisterCommand(name,fn) commands[name]=fn end
function AddEventHandler(name,fn) handlers[name]=fn end
function GetPedCollectionsCount(_) return collectionAvailable and 2 or 0 end
function GetPedCollectionName(_,i) return i==0 and 'cidade_west_texas_r002' or 'cidade_jeans_washed_r001' end
function IsPedCollectionComponentVariationValid(...) return true end
function GetPedDrawableVariation(_,s) return parts[s].drawable end
function GetPedTextureVariation(_,s) return parts[s].texture end
function GetPedPaletteVariation(_,s) return parts[s].palette end
function SetPedComponentVariation(_,s,d,t,p) parts[s]={drawable=d,texture=t,palette=p}; changes[#changes+1]=s end
function SetPedCollectionComponentVariation(ped,s,_,d,t,p) SetPedComponentVariation(ped,s,d,t,p) end
function print(...) end
''')
        lua.execute((SHIRT / 'package/resource/client.lua').read_text(encoding='utf-8'))
        lua.execute((JOB / 'package/resource/client.lua').read_text(encoding='utf-8'))
        lua.execute('''
collectionAvailable=false; commands.calcajeans(); assert(#changes==0)
collectionAvailable=true; model=2; commands.calcajeans(); assert(#changes==0)
model=1; commands.camisetatexas(); commands.calcajeans(); commands.calcajeans()
for _,s in ipairs(changes) do assert(s==3 or s==8 or s==11 or s==4) end
assert(parts[4].drawable==0 and parts[11].drawable==0)
commands.jeansanterior(); assert(parts[4].drawable==104 and parts[4].texture==4 and parts[4].palette==2)
assert(parts[11].drawable==0)
commands.roupastexasanterior()
for i=0,11 do assert(parts[i].drawable==100+i and parts[i].texture==i and parts[i].palette==2) end
''')


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Jeans))
    p.write(JOB / 'qa/tests.json', {'ok': result.wasSuccessful(), 'tests': result.testsRun,
            'failures': len(result.failures), 'errors': len(result.errors), 'real_game_test': 'pending'})
    raise SystemExit(0 if result.wasSuccessful() else 1)
