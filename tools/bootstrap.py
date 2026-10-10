"""Generate a private environment and check assets without changing an installation."""
import argparse
from pathlib import Path
import secrets

ROOT = Path(__file__).resolve().parents[1]
def create_env(environment):
    path = ROOT/f'.env.{environment}'
    if path.exists():
        raise ValueError(f'{path.name} já existe; as configurações foram preservadas.')
    value = (ROOT/'.env.example').read_text(encoding='utf-8')
    replacements = {'APP_ENV': environment, 'COMPOSE_PROJECT_NAME': 'cidade-'+environment,
                    'PANEL_ADMIN_PASSWORD': secrets.token_urlsafe(24),
                    'CITY_API_KEY': secrets.token_urlsafe(40),
                    'PANEL_ADMIN_SECRET': secrets.token_urlsafe(40)}
    if environment == 'prod':
        replacements.update(ISLAND_PORT='30120',CITY_PORT='30121',PANEL_PORT='8787',CAPTURE_PORT='8788')
    lines = [f'{line.split("=",1)[0]}={replacements[line.split("=",1)[0]]}'
             if '=' in line and line.split('=',1)[0] in replacements else line
             for line in value.splitlines()]
    path.write_text('\n'.join(lines)+'\n',encoding='utf-8'); path.chmod(0o600)
    (ROOT/'.state/gta').mkdir(parents=True,exist_ok=True)
    print(f'{path.name} criado. Preencha a chave Cfx.re e o artifact Linux. As senhas não foram exibidas.')

def check_assets():
    pending = []
    extensions = {'.ydr','.ytd','.ybn','.ymap','.ytyp','.ydd','.yft','.ycd','.png','.jpg','.webp','.mp3','.ogg','.wav'}
    for path in (ROOT/'server-data/resources').rglob('*'):
        if path.is_file() and path.suffix.lower() in extensions:
            with path.open('rb') as stream:
                if stream.read(48).startswith(b'version https://git-lfs.github.com/spec/v1'):
                    pending.append(path.relative_to(ROOT).as_posix())
    if pending:
        raise ValueError(f'{len(pending)} assets ainda são ponteiros. Execute git lfs pull --include="server-data/resources/**".')
    print('Assets do servidor disponíveis localmente.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--environment',choices=['dev','prod'],default='dev')
    parser.add_argument('--write-env',action='store_true')
    parser.add_argument('--check-assets',action='store_true')
    args = parser.parse_args()
    try:
        if args.write_env: create_env(args.environment)
        if args.check_assets: check_assets()
        if not args.write_env and not args.check_assets: parser.print_help()
    except ValueError as error:
        parser.exit(1,str(error)+'\n')
