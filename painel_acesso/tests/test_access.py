import importlib.util,json,sys,tempfile,threading,unittest,urllib.request,urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('access_app',ROOT/'app.py');app=importlib.util.module_from_spec(spec);spec.loader.exec_module(app)

class AdmissionTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.store=app.Store(self.temp.name)
 def tearDown(self):self.temp.cleanup()
 def test_pending_stable_id_approval_and_reconnect(self):
  first=self.store.check(['license:abc123'],'Amigo');self.assertEqual(first['status'],'pending')
  self.store.update(first['id'],{'status':'approved','name':'João'})
  again=self.store.check(['license:abc123'],'Outro nome FiveM');self.assertEqual(again,{'id':first['id'],'name':'João','status':'approved'})
  self.assertEqual(app.Store(self.temp.name).check(['license:abc123'],'João')['id'],first['id'])
 def test_block_does_not_create_a_new_id_and_revokes_session(self):
  player={'source':15,'name':'Amigo','identifiers':['license:def456']}
  first=self.store.check(player['identifiers'],player['name']);self.store.update(first['id'],{'status':'approved'})
  self.assertEqual(self.store.heartbeat([player])[0]['status'],'approved');self.assertEqual(self.store.list()['counts']['online'],1)
  self.store.update(first['id'],{'status':'blocked'});self.assertEqual(self.store.heartbeat([player])[0]['status'],'blocked')
  self.assertEqual(self.store.list()['counts']['online'],0);self.assertEqual(self.store.check(player['identifiers'],'Amigo')['id'],first['id'])
 def test_no_identity_no_registration_and_no_ip_identity(self):
  with self.assertRaises(ValueError):self.store.check(['ip:127.0.0.1'],'Anon')
  self.assertEqual(self.store.list()['counts']['total'],0)
 def test_parallel_accounts_and_sql_injection(self):
  one=self.store.check(['license:a123'],"'); DROP TABLE users; --");two=self.store.check(['license:b123'],'Pedro')
  self.assertNotEqual(one['id'],two['id']);self.assertEqual(self.store.list()['counts']['total'],2)
  with self.assertRaises(ValueError):self.store.update(one['id'],{'status':'yes'})
  with self.assertRaises(KeyError):self.store.update(999,{'status':'approved'})
 def test_empty_lua_heartbeat_and_private_identifiers(self):
  self.store.check(['license:private123'],'Maria');self.assertEqual(self.store.heartbeat({}),[])
  self.assertNotIn('identifier',self.store.list()['users'][0]);self.assertNotIn('private123',json.dumps(self.store.list()))
 def test_two_servers_do_not_clear_each_others_online_players(self):
  player={'source':7,'name':'Dono','identifiers':['license:owner123']}
  first=self.store.check(player['identifiers'],player['name']);self.store.update(first['id'],{'status':'approved'})
  self.store.heartbeat([player],'ilhas');self.store.heartbeat([],'los-santos');self.assertEqual(self.store.list()['counts']['online'],1)
  self.store.heartbeat([player],'los-santos');self.store.heartbeat([],'ilhas');self.assertEqual(self.store.list()['counts']['online'],1)
  self.store.heartbeat([],'los-santos');self.assertEqual(self.store.list()['counts']['online'],0)

class HttpTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.settings={'port':0,'api_key':'bridge-private','admin_secret':'secret','admin_password':'password','addresses':{}}
  self.app=app.App(app.Store(self.temp.name),self.settings)
  self.server=app.ThreadingHTTPServer(('127.0.0.1',0),app.handler(self.app));self.settings['port']=self.server.server_address[1]
  self.url='http://127.0.0.1:'+str(self.settings['port']);self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
 def tearDown(self):self.server.shutdown();self.server.server_close();self.thread.join();self.temp.cleanup()
 def request(self,path,body=None,headers=None):
  h=headers or {};raw=json.dumps(body).encode() if body is not None else None
  if raw is not None:h={'Content-Type':'application/json',**h}
  request=urllib.request.Request(self.url+path,data=raw,headers=h)
  try:r=urllib.request.urlopen(request)
  except urllib.error.HTTPError as e:r=e
  with r:return r.status,json.loads(r.read()),r.headers
 def test_api_requires_admin_bridge_requires_key_and_mutations_require_csrf(self):
  self.assertEqual(self.request('/api/users')[0],401)
  self.assertEqual(self.request('/bridge/check',{'identifiers':['license:a123'],'name':'Leo'})[0],401)
  status,record,_=self.request('/bridge/check',{'identifiers':['license:a123'],'name':'Leo'},{'X-Cidade-Key':'bridge-private'});self.assertEqual(status,200)
  token,csrf=self.app.issue_session();headers={'Cookie':'cidade_admin='+token,'Origin':self.url}
  self.assertEqual(self.request('/api/users/1',{'status':'approved'},headers)[0],403)
  headers['X-CSRF-Token']=csrf;self.assertEqual(self.request('/api/users/1',{'status':'approved'},headers)[0],200)
  headers['Origin']='https://attacker.invalid';self.assertEqual(self.request('/api/users/1',{'status':'blocked'},headers)[0],403)
  self.assertEqual(self.app.store.check(['license:a123'],'Leo')['status'],'approved')
 def test_local_sign_in_link_single_use_and_reject_forgery(self):
  value=app.local_link(self.settings).split('token=')[1];self.assertTrue(self.app.verify_link(value));self.assertFalse(self.app.verify_link(value));self.assertFalse(self.app.verify_link('forged'))
 def test_login_cookie_and_local_host_protection(self):
  self.assertEqual(self.request('/api/login',{'password':'bad'},{'Origin':self.url})[0],401)
  status,data,headers=self.request('/api/login',{'password':'password'},{'Origin':self.url});self.assertEqual(status,200)
  self.assertIn('HttpOnly',headers['Set-Cookie']);self.assertIn('SameSite=Strict',headers['Set-Cookie'])
  self.assertEqual(self.request('/api/users',headers={'Host':'attacker.invalid'})[0],403)

if __name__=='__main__':unittest.main(verbosity=2)
