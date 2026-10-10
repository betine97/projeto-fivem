"""Validate actual exports plus distinct front/back flame placement in final renders."""
import unittest
from pathlib import Path
from pants_variations import Pants, p


class JeansArt(Pants):
    batch_filename='jeans_arte_batch.json'

    def test_front_flames_are_taller_than_back(self):
        p.native(p.config())
        from PIL import Image
        job=p.HERE/'jobs/jeans_chamas/r001'
        data=p.read(job/'job.json')
        self.assertNotEqual(p.digest(job/'inputs'/data['flame_art']['front']),
                            p.digest(job/'inputs'/data['flame_art']['back']))
        tops={}
        for view in ('front','back'):
            im=Image.open(job/'qa'/f'{view}.png').convert('RGBA')
            points=[(x,y) for y in range(im.height) for x in range(im.width)
                    if (lambda c:c[3]>200 and c[0]>100 and c[0]>c[1]*1.15 and c[0]>c[2]*2)(im.getpixel((x,y)))]
            self.assertGreater(len(points),2000,view+' must contain visible flame artwork')
            tops[view]=min(y for x,y in points)
        self.assertLess(tops['front']+35,tops['back'],
                        'The front artwork must visibly reach higher up the legs')
        qa=p.read(job/'qa/art_projection.json')
        self.assertEqual(qa['flame_art']['back'],'chamas_costas.png')
        p.write(job/'qa/flame_placement_test.json',{'flame_top_pixels':tops,
                'front_taller_than_back':True,'in_game_verified':False})


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(JeansArt))
    p.write(p.HERE/'jobs/jeans_arte_tests.json',{'ok':result.wasSuccessful(),
            'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
            'real_game_test':'pending'})
    raise SystemExit(0 if result.wasSuccessful() else 1)
