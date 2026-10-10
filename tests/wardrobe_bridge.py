"""Validate the local favorites API without changing the user's selection."""
import importlib.util
import json
import tempfile
import threading
import unittest
from html.parser import HTMLParser
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('bridge', ROOT/'catalogo_roupas_web/server.py')
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)

class BridgeTest(unittest.TestCase):
    def test_native_appearance_assets_and_filters(self):
        resource = ROOT/'server-data/resources/cidade_acervo'
        class Filters(HTMLParser):
            select = None
            categories = []
            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if tag == 'select': self.select = attrs.get('id')
                if tag == 'option' and self.select == 'category': self.categories.append(attrs['value'])
            def handle_endtag(self, tag):
                if tag == 'select': self.select = None
        parser = Filters()
        html = (resource/'ui/index.html').read_text(encoding='utf-8')
        parser.feed(html)
        self.assertEqual(len(parser.categories), 18)
        self.assertTrue({'exclusive','jbib','teef','lowr','feet','p_head','hair','beard','tattoo'}.issubset(parser.categories))
        self.assertIn('Seu próximo visual.', html)
        self.assertNotIn('SEU PERSONAGEM', html)
        self.assertNotIn('preview-note', html)
        self.assertIn('role="slider"', html)
        hairs = json.loads((resource/'hair.json').read_text(encoding='utf-8'))['items']
        self.assertTrue(hairs)
        self.assertTrue(all((resource/'ui'/i['image']).is_file() for i in hairs))
        tattoos = json.loads((resource/'tattoos.json').read_text(encoding='utf-8'))['items']
        self.assertEqual(len({i['id'] for i in tattoos}), len(tattoos))
        self.assertTrue(all(i['sex'] in ('male','female') and i['collection'] and i['overlay'] and i['zone'] in ('head','torso','leftArm','rightArm','leftLeg','rightLeg') for i in tattoos))

    def test_sync_and_validation(self):
        with tempfile.TemporaryDirectory() as folder:
            bridge.DIST = Path(folder)/'web'; bridge.DIST.mkdir()
            bridge.RESOURCE = Path(folder)/'resource'; bridge.RESOURCE.mkdir()
            bridge.FAVORITES = bridge.RESOURCE/'favorites.json'
            catalog = {'items': [{'id':'male', 'sex':'male','category':'jbib'}, {'id':'female', 'sex':'female','category':'jbib'}, {'id':'shoeM','sex':'male','category':'feet'}, {'id':'shoeF','sex':'female','category':'feet'}]}
            for path in (bridge.DIST, bridge.RESOURCE):
                (path/'catalog.json').write_text(json.dumps(catalog))
            for name in ('hair', 'tattoos'):
                (bridge.RESOURCE/f'{name}.json').write_text(json.dumps({'items':[{'id':name}]}))
            http = ThreadingHTTPServer(('127.0.0.1',0),partial(bridge.Handler,directory=str(bridge.DIST)))
            worker = threading.Thread(target=http.serve_forever,daemon=True); worker.start()
            url = f'http://127.0.0.1:{http.server_port}'
            def post(value, origin='http://127.0.0.1:8766', endpoint='/api/favorites'):
                request = Request(url+endpoint,data=json.dumps(value).encode(),headers={'Content-Type':'application/json','Origin':origin})
                return json.load(urlopen(request))
            try:
                self.assertEqual(post({'ids':['male','male','female']}),{'count':2})
                self.assertEqual(json.load(urlopen(url+'/api/favorites')),{'ids':['male','female']})
                wardrobe = json.load(urlopen(url+'/api/wardrobe'))
                self.assertEqual(wardrobe, [])
                self.assertEqual(json.load(urlopen(url+'/api/tags')),{'items':{}})
                self.assertTrue(post({'id':'male','tags':['OK']},endpoint='/api/tags')['ok'])
                self.assertTrue(post({'id':'shoeM','tags':['PEÇA INCORRETA','DEFEITO NA TEXTURA']},endpoint='/api/tags')['ok'])
                expected = {'male':['OK'],'shoeM':['PEÇA INCORRETA','DEFEITO NA TEXTURA']}
                self.assertEqual(json.load(urlopen(url+'/api/tags'))['items'],expected)
                self.assertEqual(json.loads((bridge.RESOURCE/'tags.json').read_text(encoding='utf-8'))['items'],expected)
                self.assertEqual([i['id'] for i in json.load(urlopen(url+'/api/wardrobe'))], ['male'])
                # Approval is independent of favorites; shoes also require OK.
                post({'id':'shoeF','tags':['OK']},endpoint='/api/tags')
                expected['shoeF']=['OK']
                wardrobe=json.load(urlopen(url+'/api/wardrobe'))
                self.assertEqual({i['id'] for i in wardrobe}, {'male','shoeF'})
                self.assertFalse(next(i for i in wardrobe if i['id']=='shoeF')['favorite'])
                for invalid in ({'id':'unknown','tags':['OK']},{'id':'male','tags':['OK','DEFEITO NA TEXTURA']},{'id':'male','tags':['unknown']}):
                    with self.assertRaises(HTTPError) as error:post(invalid,endpoint='/api/tags')
                    self.assertEqual(error.exception.code,400)
                self.assertEqual(json.load(urlopen(url+'/api/tags'))['items'],expected)
                self.assertTrue(post({'id':'male','tags':[]},endpoint='/api/tags')['ok'])
                self.assertEqual(json.load(urlopen(url+'/api/tags'))['items'],{'shoeM':expected['shoeM'],'shoeF':['OK']})
                self.assertEqual([i['id'] for i in json.load(urlopen(url+'/api/wardrobe'))], ['shoeF'])
                self.assertEqual(json.load(urlopen(url+'/api/appearance')),{'hair':[{'id':'hair'}],'tattoos':[{'id':'tattoos'}]})
                with self.assertRaises(HTTPError) as error:post({'ids':['unknown']})
                self.assertEqual(error.exception.code,400)
                with self.assertRaises(HTTPError) as error:post({'ids':[]},'https://example.com')
                self.assertEqual(error.exception.code,403)
                self.assertEqual(json.load(urlopen(url+'/api/favorites')),{'ids':['male','female']})
                self.assertEqual(post({'ids':[]}),{'count':0})
                self.assertEqual({i['id'] for i in json.load(urlopen(url+'/api/wardrobe'))},{'shoeF'})
                self.assertEqual(json.load(urlopen(url+'/api/tags'))['items'],{'shoeM':expected['shoeM'],'shoeF':['OK']})
                # Exclusive variations are listed without approving native bases or
                # changing favorites, and share the same review/favorites bridge.
                exclusive={'id':'exclusive-shirt','sex':'male','category':'jbib','exclusive':True,'image':'previews/custom.png','back':'previews/custom-back.png'}
                (bridge.RESOURCE/'exclusives.json').write_text(json.dumps({'items':[exclusive]}),encoding='utf-8')
                self.assertEqual({i['id'] for i in json.load(urlopen(url+'/api/wardrobe'))},{'shoeF','exclusive-shirt'})
                web_catalog=json.load(urlopen(url+'/catalog.json'))
                custom=next(i for i in web_catalog['items'] if i['id']=='exclusive-shirt')
                self.assertEqual(custom['image'],'/tablet/previews/custom.png')
                self.assertEqual(json.load(urlopen(url+'/api/favorites')),{'ids':[]})
                self.assertNotIn('exclusive-shirt',json.load(urlopen(url+'/api/tags'))['items'])
                self.assertTrue(post({'id':'exclusive-shirt','tags':['DEFEITO NA TEXTURA']},endpoint='/api/tags')['ok'])
                self.assertEqual(json.load(urlopen(url+'/api/tags'))['items']['exclusive-shirt'],['DEFEITO NA TEXTURA'])
                self.assertEqual(post({'ids':['exclusive-shirt']}),{'count':1})
                self.assertTrue(next(i for i in json.load(urlopen(url+'/api/wardrobe')) if i['id']=='exclusive-shirt')['favorite'])
            finally:
                http.shutdown();http.server_close();worker.join()

if __name__=='__main__':unittest.main()
