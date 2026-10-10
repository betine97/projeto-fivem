"""Check private environment generation and reproducible runtime configuration."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
entry=load('container_entrypoint','docker/entrypoint.py')
bootstrap=load('bootstrap','tools/bootstrap.py')
kit=load('environment_kit','tools/prepare_environment.py')

class EnvironmentTests(unittest.TestCase):
    def test_runtime_context_includes_the_real_panel_frontend(self):
        rules=(ROOT/'.dockerignore').read_text()
        self.assertIn('!painel_acesso/web/**',rules)
        self.assertTrue((ROOT/'painel_acesso/web/index.html').is_file())
    def test_configs_isolate_ports_and_do_not_write_secrets_to_sources(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); app=root/'app'; state=root/'state'
            for path in ('server-data','servidor-los-santos'):(app/path).mkdir(parents=True)
            source='exec secrets.cfg\nexec acesso.cfg\nendpoint_add_tcp "0.0.0.0:30120"\nensure cidade_core\n'
            (app/'server-data/server-ilha.cfg').write_text(source)
            (app/'servidor-los-santos/server.cfg').write_text(source)
            (app/'server-data/permissoes-amigos.cfg').write_text('add_ace group.admin cidade.admin allow\n')
            # Config tests also run on Windows without symlink privileges.
            for label in ('ilha','cidade'):(state/label/'resources').mkdir(parents=True)
            env={'APP_ENV':'dev','FIVEM_LICENSE_KEY':'cfxk_test_only','PANEL_ADMIN_PASSWORD':'x'*24,
                 'CITY_API_KEY':'k'*40,'PANEL_ADMIN_SECRET':'s'*40,'ENABLE_CAPTURE_INDEX':'0',
                 'ISLAND_PORT':'30220','CITY_PORT':'30221','PANEL_PORT':'8887','CAPTURE_PORT':'8888'}
            with patch.object(entry,'APP',app),patch.object(entry,'STATE',state),patch.dict(os.environ,env,clear=True):
                self.assertEqual(entry.prepare(),'dev')
                self.assertEqual((app/'server-data/server-ilha.cfg').read_text(),source)
                self.assertFalse((app/'server-data/secrets.cfg').exists())
                self.assertIn('0.0.0.0:30220',(state/'ilha/server.cfg').read_text())
                self.assertNotIn('0.0.0.0:30120',(state/'ilha/server.cfg').read_text())
                self.assertIn('127.0.0.1:8888',(state/'cidade/acesso.cfg').read_text())
                self.assertEqual(json.loads((app/'painel_acesso/data/config.json').read_text())['port'],8887)
                addresses=json.loads((app/'painel_acesso/data/config.json').read_text())['addresses']
                self.assertEqual(addresses['vpn'],'127.0.0.1:30220')
                self.assertEqual(addresses['city'],'127.0.0.1:30221')
                # A nonempty index remains intact when the environment restarts.
                index=app/'captura_los_santos/data/model_index.json'
                index.write_text('{"models":{"123":{"model":"test"}},"files":{}}')
                entry.prepare();self.assertIn('123',json.loads(index.read_text())['models'])
                for host,prefix in [('10.20.30.40','10.20.30.40'),('::1','[::1]')]:
                    with patch.dict(os.environ,{'SERVER_HOST':host}):
                        entry.prepare()
                        endpoints=json.loads((app/'painel_acesso/data/config.json').read_text())['addresses']
                        self.assertEqual(endpoints['vpn'],prefix+':30220')
                        self.assertEqual(endpoints['city'],prefix+':30221')
    def test_invalid_and_duplicate_ports_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder,patch.object(entry,'APP',Path(folder)),patch.dict(os.environ,{
            'FIVEM_LICENSE_KEY':'cfxk_test_only','PANEL_ADMIN_PASSWORD':'x'*24,'CITY_API_KEY':'k'*40,
            'PANEL_ADMIN_SECRET':'s'*40,'ISLAND_PORT':'8887','PANEL_PORT':'8887'},clear=True):
            with self.assertRaises(ValueError):entry.prepare()
    def test_production_requires_pinned_checksum_before_download(self):
        with patch.dict(os.environ,{'FXSERVER_ARTIFACT_URL':'https://runtime.fivem.net/artifacts/fivem/build_proot_linux/master/123-test/fx.tar.xz'},clear=True),patch.object(entry.urllib.request,'urlopen') as network:
            with self.assertRaises(ValueError):entry.install_fxserver('prod')
            network.assert_not_called()
    def test_env_does_not_overwrite_private_keys_and_dev_prod_differ(self):
        with tempfile.TemporaryDirectory() as folder,patch.object(bootstrap,'ROOT',Path(folder)):
            root=Path(folder);(root/'.env.example').write_text((ROOT/'.env.example').read_text())
            bootstrap.create_env('dev');bootstrap.create_env('prod')
            dev=(root/'.env.dev').read_text();prod=(root/'.env.prod').read_text()
            self.assertIn('ISLAND_PORT=30220',dev);self.assertIn('ISLAND_PORT=30120',prod)
            self.assertNotEqual(dev.split('CITY_API_KEY=')[1].splitlines()[0],prod.split('CITY_API_KEY=')[1].splitlines()[0])
            with self.assertRaises(ValueError):bootstrap.create_env('prod')
            self.assertEqual((root/'.env.prod').read_text(),prod)
    def test_deployment_kit_contains_no_live_secret(self):
        with tempfile.TemporaryDirectory() as folder:
            kit.prepare('prod','ghcr.io/betine97/projeto-fivem:prod-test',folder)
            env=(Path(folder)/'.env.example').read_text()
            self.assertIn('APP_ENV=prod',env);self.assertIn('ISLAND_PORT=30120',env)
            self.assertIn('CITY_API_KEY=\n',env)
            self.assertIn('--no-build',(Path(folder)/'LEIA-ME.txt').read_text())
            self.assertIn('APP_ENV: prod',(Path(folder)/'compose.environment.yaml').read_text())
            kit.prepare('dev','ghcr.io/betine97/projeto-fivem:dev-test',folder)
            self.assertIn('APP_ENV: dev',(Path(folder)/'compose.environment.yaml').read_text())

if __name__=='__main__':unittest.main(verbosity=2)
