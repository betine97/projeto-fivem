"""Read back the two actual native pants exports and their tablet registrations."""
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'personagens/pipeline_roupas'))
import pipeline as p
import package_addon as package


class Pants(unittest.TestCase):
    batch_filename='calcas_estampadas_batch.json'
    def test_exports_and_registration(self):
        batch=p.read(p.HERE/'jobs'/self.batch_filename)['jobs']
        acervo=ROOT/'server-data/resources/cidade_acervo'
        entries={i['id']:i for i in p.read(acervo/'exclusives.json')['items']}
        tag_hash=p.digest(acervo/'tags.json')
        favorite_hash=p.digest(acervo/'favorites.json')
        self.assertEqual(len(batch),2)
        for entry in batch:
            job=Path(entry['job']);data=p.read(job/'job.json')
            with self.subTest(name=data['name']):
                build=p.build(job)
                self.assertTrue(build['original_geometry_unchanged'])
                self.assertTrue(build['native_normal_specular_and_skeleton_preserved'])
                self.assertTrue(build['diffuse_sampler_verified'])
                self.assertEqual(build['extra_triangles_high'],0)
                self.assertEqual(build['lods'],[0,1,2])
                self.assertTrue(build['native_materials_and_skeleton_unchanged'])
                package.verify_ymt(job/'qa/addon.roundtrip.xml',data['target']['collection'],4,1)
                item=entries['exclusive-'+data['name']]
                self.assertEqual(item['collection'],data['target']['collection'])
                self.assertEqual(item['sourceId'],'8552b45e2ad8')
                self.assertNotIn('compatibleArmsIndex',item)
                self.assertEqual(item['category'],'lowr')
                self.assertEqual(item['textureIndex'],0)
                resource=ROOT/'server-data/resources'/item['resource']
                for filename,sha in p.read(job/'qa/package.json')['files'].items():
                    self.assertEqual(p.digest(resource/filename),sha)
                self.assertEqual(p.digest(acervo/'ui'/item['image']),p.digest(job/'qa/front.png'))
                self.assertEqual(p.digest(acervo/'ui'/item['back']),p.digest(job/'qa/back.png'))
                self.assertFalse(data['review']['in_game'])
        self.assertEqual(p.digest(acervo/'tags.json'),tag_hash)
        self.assertEqual(p.digest(acervo/'favorites.json'),favorite_hash)


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Pants))
    p.write(p.HERE/'jobs/calcas_estampadas_tests.json',{'ok':result.wasSuccessful(),
            'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'real_game_test':'pending'})
    raise SystemExit(0 if result.wasSuccessful() else 1)
