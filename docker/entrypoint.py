"""Start the access bridge, capture worker and two isolated FXServers."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tarfile
import time
import urllib.request

APP = Path('/app')
STATE = Path('/state')

def required(name, minimum=1):
    value = os.environ.get(name, '')
    if len(value) < minimum or any(c in value for c in '\r\n"'):
        raise ValueError(f'Preencha {name} corretamente no arquivo .env do ambiente.')
    return value

def prepare():
    mode = os.environ.get('APP_ENV', 'dev')
    if mode not in ('dev', 'prod'):
        raise ValueError('APP_ENV deve ser dev ou prod.')
    license_key = required('FIVEM_LICENSE_KEY')
    if not re.fullmatch(r'cfxk_[A-Za-z0-9_+/=-]+', license_key):
        raise ValueError('FIVEM_LICENSE_KEY deve ser uma chave Cfx.re válida.')
    settings = {'port': int(os.environ.get('PANEL_PORT', '8887')),
                'api_key': required('CITY_API_KEY', 32),
                'admin_secret': required('PANEL_ADMIN_SECRET', 32),
                'admin_password': required('PANEL_ADMIN_PASSWORD', 16),
                'addresses': {}}
    capture_port = int(os.environ.get('CAPTURE_PORT', '8888'))
    ports = [settings['port'], capture_port, int(os.environ.get('ISLAND_PORT','30220')),
             int(os.environ.get('CITY_PORT','30221'))]
    if len(set(ports)) != 4 or any(not 1024 <= p <= 65535 for p in ports):
        raise ValueError('Defina quatro portas diferentes entre 1024 e 65535.')
    for folder in ('painel_acesso/data', 'captura_los_santos/data', 'captura_los_santos/cache',
                   'server-data/resources/cidade_admin/data'):
        (APP / folder).mkdir(parents=True, exist_ok=True)
    config = APP / 'painel_acesso/data/config.json'
    config.write_text(json.dumps(settings), encoding='utf-8'); config.chmod(0o600)
    index = APP / 'captura_los_santos/data/model_index.json'
    indexed = index.exists() and bool(json.loads(index.read_text(encoding='utf-8')).get('models'))
    if os.environ.get('ENABLE_CAPTURE_INDEX') == '1' and not indexed:
        gta = Path(os.environ.get('GTA_ROOT', '/gta'))
        if not (gta / 'update/update.rpf').is_file():
            raise ValueError('Monte a instalação GTA V Legacy em GTA_HOST_PATH para indexar a captura.')
        for script in ('build_index.py','build_world_index.py'):
            subprocess.run([sys.executable,str(APP/'captura_los_santos'/script)],cwd=APP,check=True)
    elif not index.exists():
        index.write_text(json.dumps({'models': {}, 'files': {}}), encoding='utf-8')
        print('Captura sem índice nativo: monte GTA e execute a indexação para resolver novos modelos.', flush=True)
    # The original source configurations and private local installation are untouched.
    for label, source, port in (('ilha','server-data/server-ilha.cfg',ports[2]),
                                ('cidade','servidor-los-santos/server.cfg',ports[3])):
        folder = STATE / label; folder.mkdir(parents=True, exist_ok=True)
        resources = folder / 'resources'
        if not resources.exists():
            resources.symlink_to(APP/'server-data/resources', target_is_directory=True)
        contents = (APP/source).read_text(encoding='utf-8')
        contents = '\n'.join(line for line in contents.splitlines()
                             if not line.strip().startswith(('endpoint_add_tcp','endpoint_add_udp')))
        contents += f'\nendpoint_add_tcp "0.0.0.0:{port}"\nendpoint_add_udp "0.0.0.0:{port}"\n'
        (folder/'server.cfg').write_text(contents, encoding='utf-8')
        (folder/'secrets.cfg').write_text(f'sv_licenseKey "{license_key}"\n', encoding='utf-8')
        (folder/'secrets.cfg').chmod(0o600)
        (folder/'acesso.cfg').write_text(
            f'set cidade_acesso_url "http://127.0.0.1:{settings["port"]}"\n'
            f'set cidade_acesso_key "{settings["api_key"]}"\n'
            f'set cidade_captura_url "http://127.0.0.1:{capture_port}"\n',encoding='utf-8')
        (folder/'acesso.cfg').chmod(0o600)
        shutil.copyfile(APP/'server-data/permissoes-amigos.cfg',folder/'permissoes-amigos.cfg')
    return mode

def install_fxserver(mode):
    url = required('FXSERVER_ARTIFACT_URL')
    if not re.fullmatch(r'https://runtime\.fivem\.net/artifacts/fivem/build_proot_linux/master/[A-Za-z0-9_-]+/fx\.tar\.xz',url):
        raise ValueError('Use a URL HTTPS do fx.tar.xz Linux oficial de runtime.fivem.net.')
    expected = os.environ.get('FXSERVER_ARTIFACT_SHA256','').lower()
    if expected and not re.fullmatch('[0-9a-f]{64}',expected):
        raise ValueError('FXSERVER_ARTIFACT_SHA256 deve conter 64 dígitos hexadecimais.')
    if mode == 'prod' and not expected:
        raise ValueError('Produção exige FXSERVER_ARTIFACT_SHA256 fixo.')
    runtime = STATE/'fxserver'; marker = runtime/'cidade-artifact.json'
    identity = {'url':url,'sha256':expected}
    if marker.exists() and json.loads(marker.read_text()) == identity and (runtime/'run.sh').exists():
        return runtime
    destination = STATE/('fxserver-'+hashlib.sha256(url.encode()).hexdigest()[:16])
    archive = STATE/'fx-download.tar.xz'
    digest = hashlib.sha256()
    request = urllib.request.Request(url,headers={'User-Agent':'MinhaCidade/1.0'})
    with urllib.request.urlopen(request,timeout=120) as response, archive.open('wb') as stream:
        while block := response.read(1024*1024):
            digest.update(block); stream.write(block)
    if expected and digest.hexdigest() != expected:
        archive.unlink(); raise ValueError('Checksum do FXServer divergente. Download recusado.')
    destination.mkdir(parents=True,exist_ok=True)
    with tarfile.open(archive,'r:xz') as package:
        # Python's data filter rejects traversal and links outside the runtime.
        package.extractall(destination, filter='data')
    archive.unlink()
    if not (destination/'run.sh').is_file():
        raise ValueError('Artifact sem run.sh.')
    if runtime.is_symlink(): runtime.unlink()
    elif runtime.exists(): raise ValueError('Diretório fxserver inesperado; preserve-o antes de trocar de versão.')
    runtime.symlink_to(destination,target_is_directory=True)
    (runtime/'cidade-artifact.json').write_text(json.dumps(identity))
    return runtime

def supervise(runtime):
    commands = [([sys.executable,'-u',str(APP/'painel_acesso/app.py')],APP),
                ([sys.executable,'-u',str(APP/'captura_los_santos/service.py')],APP),
                (['bash',str(runtime/'run.sh'),'+exec','server.cfg'],STATE/'ilha'),
                (['bash',str(runtime/'run.sh'),'+exec','server.cfg'],STATE/'cidade')]
    children = []
    stopped = False
    def stop(signum, frame):
        nonlocal stopped
        stopped = True
    signal.signal(signal.SIGTERM,stop); signal.signal(signal.SIGINT,stop)
    status = 0
    try:
        for command, cwd in commands:
            children.append(subprocess.Popen(command,cwd=cwd,start_new_session=True))
        while not stopped:
            for child in children:
                if child.poll() is not None:
                    status = child.returncode or 1; stopped = True; break
            time.sleep(.5)
    finally:
        for child in children:
            if child.poll() is None: os.killpg(child.pid,signal.SIGTERM)
        deadline = time.monotonic()+30
        while time.monotonic()<deadline and any(child.poll() is None for child in children): time.sleep(.2)
        for child in children:
            if child.poll() is None: os.killpg(child.pid,signal.SIGKILL)
        for child in children: child.wait()
    return status

if __name__ == '__main__':
    os.umask(0o077)
    try:
        mode = prepare()
        raise SystemExit(supervise(install_fxserver(mode)))
    except (ValueError,OSError,subprocess.CalledProcessError) as error:
        print(f'Inicialização recusada: {error}',file=sys.stderr)
        raise SystemExit(1)
