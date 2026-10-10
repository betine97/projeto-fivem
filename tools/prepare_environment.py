"""Build a small, secret-free deployment kit for an immutable runtime image."""
import argparse
from pathlib import Path
import re
import shutil

ROOT=Path(__file__).resolve().parents[1]
def prepare(environment, image, output):
    if environment not in ('dev','prod') or not re.fullmatch(r'ghcr\.io/[a-z0-9_.-]+/[a-z0-9_.-]+:[a-z0-9_.-]+',image):
        raise ValueError('Ambiente ou imagem inválidos.')
    output=Path(output); output.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(ROOT/'compose.yaml',output/'compose.yaml')
    overlay=(ROOT/'compose.prod.yaml').read_text(encoding='utf-8').replace('APP_ENV: prod','APP_ENV: '+environment)
    (output/'compose.environment.yaml').write_text(overlay,encoding='utf-8')
    env=(ROOT/'.env.example').read_text(encoding='utf-8').replace('APP_ENV=dev','APP_ENV='+environment).replace('COMPOSE_PROJECT_NAME=cidade-dev','COMPOSE_PROJECT_NAME=cidade-'+environment).replace('CITY_IMAGE=cidade-fivem:local','CITY_IMAGE='+image)
    if environment=='prod':
        for key, old, new in (('ISLAND_PORT','30220','30120'),('CITY_PORT','30221','30121'),('PANEL_PORT','8887','8787'),('CAPTURE_PORT','8888','8788')):
            env=env.replace(f'{key}={old}',f'{key}={new}')
    (output/'.env.example').write_text(env,encoding='utf-8')
    shutil.copyfile(ROOT/'docs/EXECUTAR.md',output/'EXECUTAR.md')
    (output/'LEIA-ME.txt').write_text(f'Ambiente: {environment}\nImagem: {image}\nCopie .env.example para .env e preencha credenciais próprias.\nCrie a pasta vazia .state/gta, ou configure GTA_HOST_PATH com uma instalação GTA.\nUse docker compose --env-file .env -f compose.yaml -f compose.environment.yaml up -d --no-build\nO kit não inicia nem modifica servidores automaticamente.\n',encoding='utf-8')
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--environment',choices=['dev','prod'],required=True);parser.add_argument('--image',required=True);parser.add_argument('--output',required=True)
    args=parser.parse_args();prepare(args.environment,args.image,args.output)
