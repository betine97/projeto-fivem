"""Regression checks for clothing provenance, isolation, placement and native round trips."""
import copy
import json
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'personagens/pipeline_roupas'))
import pipeline as p


class FakeBackend:
    calls = 0

    def extract(self, item, folder):
        self.calls += 1
        source = folder / 'source/base.ydd'
        source.parent.mkdir(exist_ok=True)
        source.write_bytes(b'unchanged native geometry')
        return {'paths': {'model': 'source/base.ydd'}, 'archives': {}, 'geometry': []}


class Workflow(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.here = self.root / 'pipeline'
        self.here.mkdir()
        for name in ('pipeline.py', 'native_backend.py'):
            shutil.copy2(p.HERE / name, self.here / name)
        self.item = {'id': 'approved01', 'sex': 'male', 'category': 'lowr',
                     'collection': 'native', 'index': 1, 'file': 'lowr_001_r.ydd',
                     'textureFile': 'lowr_diff_001_a_whi.ytd'}
        self.cfg = {'catalog': 'catalog.json', 'tags': 'tags.json', 'inventory': 'inventory.json',
                    'limits': {'max_relief_mm': 25}}
        p.write(self.root / 'catalog.json', {'items': [self.item, {**self.item, 'id': 'rejected01'}]})
        p.write(self.root / 'tags.json', {'items': {'approved01': ['OK'], 'rejected01': ['DEFEITO NA TEXTURA']}})
        p.write(self.root / 'inventory.json', {})
        self.backend = FakeBackend()
        self.patches = [patch.object(p, 'ROOT', self.root), patch.object(p, 'HERE', self.here),
                        patch.object(p, 'native', return_value=self.backend)]
        for mock in self.patches:
            mock.start()

    def tearDown(self):
        for mock in reversed(self.patches):
            mock.stop()
        self.tmp.cleanup()

    def test_only_current_OK_bases(self):
        self.assertEqual([i['id'] for i in p.approved(self.cfg)], ['approved01'])
        with self.assertRaises(ValueError):
            p.cached('rejected01', self.cfg)
        p.cached('approved01', self.cfg)
        p.write(self.root / 'tags.json', {'items': {}})
        with self.assertRaises(ValueError):
            p.cached('approved01', self.cfg)

    def test_cache_reuse_tamper_and_versioning(self):
        folder, manifest, hit = p.cached('approved01', self.cfg)
        self.assertFalse(hit)
        self.assertTrue(p.cached('approved01', self.cfg)[2])
        self.assertEqual(self.backend.calls, 1)
        (folder / 'source/base.ydd').write_bytes(b'tampered')
        with self.assertRaises(ValueError):
            p.cached('approved01', self.cfg)
        (folder / 'source/base.ydd').write_bytes(b'unchanged native geometry')
        (self.here / 'native_backend.py').write_bytes(b'new adapter version')
        revised, _, hit = p.cached('approved01', self.cfg)
        self.assertNotEqual(folder, revised)
        self.assertFalse(hit)
        self.assertTrue((folder / 'base.json').is_file())

    def test_independent_revisions_and_missing_art(self):
        first = p.new_job('minha_calca', 'approved01', cfg=self.cfg)
        second = p.new_job('minha_calca', 'approved01', cfg=self.cfg)
        self.assertEqual((first.name, second.name), ('r001', 'r002'))
        a, b = p.read(first / 'job.json'), p.read(second / 'job.json')
        self.assertNotEqual(a['target']['prefix'], b['target']['prefix'])
        self.assertEqual(a['target']['mode'], 'addon')
        report = p.preflight(first, self.cfg)[2]
        self.assertFalse(report['ok'])
        self.assertEqual(len(report['errors']), 2)  # Reference and UV atlas are both mandatory.

    def test_escape_prefix_and_unbuilt_motion_are_blocked(self):
        job = p.new_job('seguranca', 'approved01', cfg=self.cfg)
        with self.assertRaises(ValueError):
            p.input_path(job, '../../catalog.json')
        with self.assertRaises(ValueError):
            p.load_job(self.root / 'catalog.json')
        data = p.read(job / 'job.json')
        data['target']['prefix'] = '../../native'
        data['components'] = [{'id': 'fita', 'kind': 'secondary_prop'}]
        p.write(job / 'job.json', data)
        errors = p.preflight(job, self.cfg)[2]['errors']
        self.assertTrue(any('Prefixo' in s for s in errors))
        self.assertTrue(any('YDR' in s for s in errors))


class NativeRoundTrip(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = p.config()
        cls.backend = p.native(cls.cfg)
        import native_backend as n
        cls.n = n
        cls.base, cls.meta, _ = p.cached('ec240957694f', cls.cfg)

    def test_semantic_errors_and_ambiguous_UV(self):
        n = self.n
        source = n.try_load_asset(self.base / self.meta['paths']['model'])
        g = next(iter(source.drawables.values())).models[0][0].geometries[0]
        row = n.sample(g, (.745, .218))
        self.assertFalse(n.region_errors(row, {'side': 'left', 'face': 'outer'}))
        self.assertTrue(n.region_errors(row, {'side': 'right', 'face': 'outer'}))
        self.assertTrue(n.region_errors(row, {'side': 'left', 'face': 'inner'}))
        self.assertTrue(n.region_errors(row, {'side': 'left', 'face': 'outer', 'z_range_m': [1, 2]}))
        self.assertEqual(row['BlendWeights'].sum(), 255)
        with self.assertRaises(ValueError):
            n.sample(g, (10, 10))
        ambiguous = copy.deepcopy(g)
        vertices = g.vertex_buffer.copy()
        vertices['Position'][:, 2] += 1
        ambiguous.vertex_buffer = n.np.concatenate((g.vertex_buffer, vertices))
        ambiguous.index_buffer = n.np.concatenate((g.index_buffer, g.index_buffer + len(vertices)))
        with self.assertRaisesRegex(ValueError, 'ambíguo'):
            n.sample(ambiguous, (.745, .218))

    def test_export_base_materials_LODs_and_build_cache(self):
        from PIL import Image, ImageDraw
        with tempfile.TemporaryDirectory() as temp:
            work = Path(temp)
            for name in ('pipeline.py', 'native_backend.py'):
                shutil.copy2(p.HERE / name, work / name)
            reference = work / 'reference.png'
            Image.new('RGB', (32, 32), 'gray').save(reference)
            with patch.object(p, 'HERE', work), patch.object(p, 'cached', return_value=(self.base, self.meta, True)):
                job = p.new_job('qa_native', 'ec240957694f', reference, self.cfg)
                data = p.read(job / 'job.json')
                atlas = self.base / 'source/textures/lowr_diff_001_a_whi.dds'
                Image.open(atlas).convert('RGBA').save(job / 'inputs/atlas.png')
                overlay = Image.new('RGBA', (64, 64))
                ImageDraw.Draw(overlay).rounded_rectangle((2, 2, 61, 61), radius=6, fill=(60, 70, 30, 255))
                overlay.save(job / 'inputs/pocket.png')
                part = p.read(ROOT / 'personagens/pipeline_roupas/templates/component.json')
                part['image'] = 'pocket.png'
                data['material']['albedo_atlas'] = 'atlas.png'
                data['components'] = [part]
                p.write(job / 'job.json', data)
                self.assertTrue(p.preflight(job, self.cfg)[2]['ok'])
                incorrect = copy.deepcopy(data)
                incorrect['components'][0]['region']['face'] = 'inner'
                p.write(job / 'job.json', incorrect)
                self.assertFalse(p.preflight(job, self.cfg)[2]['ok'])
                with self.assertRaises(ValueError):
                    p.build(job, self.cfg)
                p.write(job / 'job.json', data)
                result = p.build(job, self.cfg)
                self.assertFalse(result['deployable'])
                self.assertTrue(result['original_geometry_unchanged'])
                self.assertTrue(result['native_materials_and_skeleton_unchanged'])
                self.assertTrue(result['diffuse_sampler_verified'])
                self.assertEqual(result['extra_triangles_high'], 128)
                self.assertTrue(p.build(job, self.cfg)['cache_hit'])
                for name, sha in result['files'].items():
                    self.assertEqual(p.digest(job / name), sha)
                self.assertEqual(set(result['lods']), {0, 1, 2})
                NativeRoundTrip.build_result = result


if __name__ == '__main__':
    started = time.perf_counter()
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {'ok': result.wasSuccessful(), 'tests': result.testsRun,
              'seconds': round(time.perf_counter() - started, 3),
              'failures': len(result.failures), 'errors': len(result.errors),
              'native_round_trip': getattr(NativeRoundTrip, 'build_result', None),
              'in_game_test': 'pending for future variation'}
    p.write(ROOT / 'personagens/pipeline_roupas/validation.json', report)
    raise SystemExit(0 if result.wasSuccessful() else 1)
