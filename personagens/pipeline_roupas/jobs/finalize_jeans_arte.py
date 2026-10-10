"""Package and register the two visually reviewed pants variations."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pipeline as p
import package_addon
import install_addon
import register_exclusive

acervo = p.ROOT / 'server-data/resources/cidade_acervo'
snapshot = {name: p.digest(acervo / name) for name in ('tags.json', 'favorites.json')}
p.write(p.HERE / 'jobs/jeans_arte_user_state_before.json', snapshot)
for entry in p.read(p.HERE / 'jobs/jeans_arte_batch.json')['jobs']:
    job = Path(entry['job'])
    data = p.read(job / 'job.json')
    data['review'].update(positions=True, appearance=True, in_game=False)
    p.write(job / 'job.json', data)
    for name in ('art_projection', 'pose'):
        report = p.read(job / f'qa/{name}.json')
        report['visual_review'] = 'reviewed: front/back/sides and flexion renders'
        report['limitations'] = ['Native silhouette retained; back cloth inferred from supplied fabric; FiveM validation pending.']
        p.write(job / f'qa/{name}.json', report)
    package_addon.package(job)
    install_addon.install(job)
    item = register_exclusive.register(job, entry['title'])
    special = ('Rasgos visuais na textura; a malha nativa nao foi recortada.' if data['name'] == 'jeans_rasgado'
               else 'Chamas maiores na frente e menores nas costas, usando as duas artes independentes fornecidas.')
    (job / 'LEIA-ME.md').write_text(
        f"# {entry['title']}\n\nBase preservada: lowr_001_r.ydd / lowr_diff_001_a_whi.ytd, masculino.\n\n"
        f"Variacao independente: {item['resource']}; colecao {item['collection']}, componente 4, indice local 0, textura 0.\n\n"
        f"{special}\n\nRenders estaticos e flexao revisados. Exportacao nativa verificada. Validacao visual dentro do FiveM pendente.\n\n"
        "Disponivel no cadastro de roupas > Masculino > Exclusivas. Reiniciar servidor e reconectar para carregar o recurso.\n",
        encoding='utf-8')
    print('INSTALLED', data['name'], flush=True)
assert snapshot == {name: p.digest(acervo / name) for name in snapshot}
