"""Install a validated package into its own resource, preserving existing files."""
import argparse
import shutil
from pathlib import Path
import pipeline as p


def install(job):
    job,data=p.load_job(job)
    report=p.read(job/'qa/package.json')
    if report['status']!='addon_packaged' or not report['metadata']['round_trip_verified']:
        raise ValueError('Validated package required.')
    source=job/'package/resource'
    for name,sha in report['files'].items():
        if p.digest(source/name)!=sha:raise ValueError('Package changed: '+name)
    name='cidade_'+data['name']
    target=p.ROOT/'server-data/resources'/name
    if target.exists():
        if not all((target/file).is_file() and p.digest(target/file)==sha for file,sha in report['files'].items()):
            raise ValueError('An existing resource differs. Preserve it and install a distinct variation.')
    else:
        shutil.copytree(source,target)
    for file,sha in report['files'].items():
        if p.digest(target/file)!=sha:raise ValueError('Installation differs: '+file)
    cfg=p.ROOT/'server-data/server.cfg'
    text=cfg.read_text(encoding='utf-8-sig')
    if 'ensure '+name not in [line.strip() for line in text.splitlines()]:
        with cfg.open('a',encoding='utf-8') as output:output.write('\nensure '+name+'\n')
    result={'resource':name,'installed':True,'files_verified':report['files'],
            'server_reload_required':True,'in_game_verified':False}
    p.write(job/'qa/install.json',result)
    return target,result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--job',required=True)
    args=parser.parse_args()
    folder,report=install(args.job)
    print(folder)
