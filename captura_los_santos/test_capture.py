import copy,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
HOME=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('capture_service',HOME/'service.py');service=importlib.util.module_from_spec(spec);spec.loader.exec_module(service)
META={'model':'prop_bench_01a','asset':'prop_bench_01a','bbMin':[-1,-.5,0],'bbMax':[1,.5,1]}
class CaptureTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
  self.store=service.CaptureStore(self.root,{'models':{'123':copy.deepcopy(META)},'files':{}},render=False)
  self.body={'kind':'object','hash':123,'position':{'x':200,'y':-900,'z':30},'name':'Banco da praça','category':'Objetos de Los Santos','author':{'id':1,'name':'ADM'}}
 def tearDown(self):self.temp.cleanup()
 def test_capture_persists_and_preserves_model(self):
  result=self.store.capture(self.body);self.assertTrue(result['ok']);self.assertEqual(result['id'],1)
  data=json.loads(self.store.path.read_text());self.assertEqual(data['captures'][0]['model'],'prop_bench_01a');self.assertEqual(data['captures'][0]['bbMin'],[-1,-.5,0])
  again=service.CaptureStore(self.root,self.store.index,render=False);self.assertEqual(again.state['nextId'],2);self.assertEqual(len(again.state['captures']),1)
 def test_unknown_and_grouped_are_marked_without_broken_catalogue_entry(self):
  self.body['hash']=999;self.store.capture(self.body);self.assertEqual(self.store.state['captures'][0]['kind'],'surface');self.assertEqual(self.store.catalog['objects'],[])
  self.body['hash']=123;self.store.index['models']['123']['mlo']=True;self.assertEqual(self.store.resolve(self.body)['kind'],'surface')
 def test_rejects_invalid_fields(self):
  for change in ({'name':'../'+'x'*80},{'author':{}},{'hash':True},{'position':{'x':float('nan'),'y':0,'z':0}},{'category':'Inexistente'}):
   with self.subTest(change=change),self.assertRaises(ValueError):self.store.capture({**self.body,**change})
 def test_repeated_model_reuses_catalogue(self):
  self.store.catalog['objects']=[{**META,'hash':123}]
  self.store.capture(self.body);self.assertEqual(self.store.jobs.qsize(),0);self.assertEqual(self.store.state['captures'][0]['status'],'disponível no catálogo')
 def test_cayo_capture_uses_shared_catalogue_and_preserves_origin(self):
  self.body['origin']='Cayo Perico';self.store.capture(self.body)
  self.assertEqual(self.store.state['captures'][0]['origin'],'Cayo Perico')
  catalog=json.loads(self.store.catalogPath.read_text(encoding='utf8'))
  self.assertEqual(catalog['marks'][0]['model'],'prop_bench_01a')
  self.assertGreater(catalog['revision'],0)
 def test_pending_marks_remain_visible_after_restart(self):
  self.body['hash']=999;self.store.capture(self.body)
  again=service.CaptureStore(self.root,self.store.index,render=False)
  self.assertEqual(again.catalog['marks'][0]['status'],'aguardando análise')
  self.assertEqual(again.catalog['objects'],[])
 def test_gameplay_index_excludes_images_without_removing_browser_thumbnails(self):
  self.store.catalog['objects']=[{**META,'hash':123,'image':'data:image/webp;base64,'+'a'*500000}]
  self.store.capture(self.body)
  metadata=json.loads(self.store.catalogPath.with_name('catalogo_capturado_indice.json').read_text(encoding='utf8'))
  full=json.loads(self.store.catalogPath.read_text(encoding='utf8'))
  self.assertNotIn('image',metadata['objects'][0]);self.assertEqual(metadata['revision'],full['revision'])
  self.assertEqual(full['type'],'capturedCatalog');self.assertEqual(full['objects'][0]['image'],self.store.catalog['objects'][0]['image'])
  self.assertLess(self.store.catalogPath.with_name('catalogo_capturado_indice.json').stat().st_size,2000)
if __name__=='__main__':unittest.main()
