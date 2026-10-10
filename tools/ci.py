"""Fast checks: no GTA, Blender, FXServer, secrets or LFS downloads required."""
import ast
from pathlib import Path
import subprocess
import sys
import yaml

ROOT=Path(__file__).resolve().parents[1]
def run(*command):
    print('Executando: '+' '.join(command),flush=True)
    subprocess.run(command,cwd=ROOT,check=True)

def main():
    for directory in ('painel_acesso','captura_los_santos','docker','tools'):
        for path in (ROOT/directory).rglob('*.py'):
            if '__pycache__' not in path.parts:
                ast.parse(path.read_text(encoding='utf-8-sig'),filename=str(path))
    for path in [*ROOT.glob('compose*.yaml'),*ROOT.glob('.github/workflows/*.yml')]:
        with path.open(encoding='utf-8') as stream:
            assert isinstance(yaml.safe_load(stream),dict),path
    for test in ('painel_acesso/tests/test_access.py','painel_acesso/tests/test_fivem_bridge.py',
                 'captura_los_santos/test_capture.py','painel_adm_20261009/test_panel.py',
                 'painel_adm_20261009/test_island.py','tests/test_environments.py'):
        run(sys.executable,test)
    for test in ('tests/drone-audio.test.cjs','tests/acervo-tags.test.cjs','tests/wardrobe-ui.test.cjs'):
        run('node',test)
    for path in (ROOT/'server-data/resources').rglob('*.js'):
        if 'node_modules' not in path.parts:
            run('node','--check',str(path.relative_to(ROOT)))
    print('CI_OK: serviços, editor, UI e configurações validados.',flush=True)
if __name__=='__main__': main()
