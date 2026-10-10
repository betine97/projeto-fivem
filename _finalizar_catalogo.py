import html
import json
import shutil
import struct
import zipfile
from pathlib import Path

BASE = Path(__file__).resolve().parent
OUT = BASE / 'catalogo_componentes_stage7'
data = json.loads((OUT / 'manifesto.json').read_text(encoding='utf-8'))
records = data['objects']
for record in records:
    path = OUT / record['image']
    with path.open('rb') as f:
        header = f.read(24)
    assert header[:8] == b'\x89PNG\r\n\x1a\n' and struct.unpack('>II', header[16:24]) == (768, 768), path
assert len({r['image'] for r in records}) == len(records)
groups = sorted({r['collections'][0] for r in records})
options = ''.join(f'<option value="{html.escape(g)}">{html.escape(g.removeprefix("ENV_"))}</option>' for g in groups)
payload = json.dumps(records, ensure_ascii=False).replace('</', '<\\/')
page = '''<!doctype html><html lang="pt-BR"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Stage 7 — catálogo de componentes</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#15191e;color:#e8edf1;font:15px system-ui,sans-serif}
header{padding:32px 4vw 18px;border-bottom:1px solid #3b424b;background:#1d242c}h1{font-size:30px;margin:0 0 10px}
p{max-width:1000px;line-height:1.55;color:#b9c5ce}a{color:#99d9ff}label{display:inline-block;margin:0 18px 12px 0}
input,select,button{padding:10px;border:1px solid #596778;background:#202a35;color:#fff;border-radius:6px}input[type=search]{width:340px;max-width:90vw}
#status{margin:20px 4vw}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:18px;padding:0 4vw 30px}
article{border:1px solid #3e4753;border-radius:10px;overflow:hidden;background:#202832}article img{width:100%;aspect-ratio:1;object-fit:contain;background:#767676;display:block}
article div{padding:14px}h2{font-size:13px;word-break:break-word;margin:0 0 10px}.meta{font-size:12px;color:#adbbc8;line-height:1.6;word-break:break-word}
nav{padding:18px 4vw;display:flex;gap:15px;align-items:center}.note{color:#e0c48b}button{cursor:pointer}
</style><header><h1>Stage 7 · Componentes isolados</h1>
<p>__COUNT__ imagens individuais, em 768 × 768 px. Cada arquivo corresponde ao nome exato do objeto no Blender. Peças geometricamente idênticas mantêm arquivos próprios e podem compartilhar a mesma referência de render.</p>
<p class="note">Estas imagens são referências de forma e material, não mapas UV. Para gerar texturas, consulte <a href="COMO_PEDIR_TEXTURAS.md">as orientações</a>. Luz rosa e bloom foram retirados somente destas fotos para facilitar a leitura dos materiais.</p>
<label>Buscar peça<br><input id="search" type="search" placeholder="Parede: WALL · cabo: CABLE · mangueira: HOSE"></label>
<label>Coleção<br><select id="group"><option value="">Todas</option>__OPTIONS__</select></label>
<label><input id="unique" type="checkbox"> Mostrar só geometrias distintas</label>
<p><a href="manifesto.json">Manifesto completo</a> · <a href="LISTA_OBJETOS.txt">Lista de objetos</a></p></header>
<div id="status"></div><div id="grid" class="grid"></div><nav><button id="prev">Anterior</button><span id="page"></span><button id="next">Próxima</button></nav>
<script>const all=__DATA__;let page=0;const size=60;const $=id=>document.getElementById(id);
function draw(){const q=$('search').value.toLowerCase();const g=$('group').value;const only=$('unique').checked;
const rows=all.filter(r=>(!q||[r.object,...r.materials,...r.collections].join(' ').toLowerCase().includes(q))&&(!g||r.collections.includes(g))&&(!only||!r.same_geometry_as));
const pages=Math.max(1,Math.ceil(rows.length/size));page=Math.min(page,pages-1);$('status').textContent=rows.length+' componentes encontrados';$('grid').replaceChildren();
for(const r of rows.slice(page*size,(page+1)*size)){const card=document.createElement('article');const link=document.createElement('a');link.href=r.image;link.target='_blank';
const im=document.createElement('img');im.src=r.image;im.loading='lazy';im.alt=r.object;link.append(im);card.append(link);const body=document.createElement('div');const title=document.createElement('h2');title.textContent=r.object;body.append(title);
const meta=document.createElement('div');meta.className='meta';meta.textContent=r.collections.join(' / ')+' · '+r.dimensions_m.map(v=>v.toFixed(3)).join(' × ')+' m';body.append(meta);
const mats=document.createElement('div');mats.className='meta';mats.textContent='Materiais: '+r.materials.join(', ');body.append(mats);
const download=document.createElement('a');download.href=r.image;download.download=r.object+'.png';download.textContent='Salvar imagem';body.append(download);card.append(body);$('grid').append(card);}
$('page').textContent='Página '+(page+1)+' de '+pages;$('prev').disabled=page===0;$('next').disabled=page===pages-1;}
for(const id of ['search','group','unique'])$(id).addEventListener('input',()=>{page=0;draw()});$('prev').onclick=()=>{page--;draw();window.scrollTo(0,0)};$('next').onclick=()=>{page++;draw();window.scrollTo(0,0)};draw();</script></html>'''
page = page.replace('__COUNT__', str(len(records))).replace('__OPTIONS__', options).replace('__DATA__', payload)
(OUT / 'index.html').write_text(page, encoding='utf-8')
(OUT / 'LISTA_OBJETOS.txt').write_text('\n'.join(f"{r['object']}\t{r['image']}" for r in records), encoding='utf-8')
instructions = '''# Como usar o catálogo para gerar texturas

Abra index.html em um navegador. Use a busca por nome e o filtro de coleção. Cada PNG contém apenas uma peça, enquadrada automaticamente, com fundo neutro e sem a iluminação rosa do cenário. A posição e escala da câmera variam por objeto para mostrar melhor a sua forma; as medidas originais estão no índice e no manifesto.

Os nomes foram preservados para vincular as texturas de volta ao Blender. O arquivo original warehouse_stage7_validado.blend não foi alterado. Luzes, câmeras e objetos de organização sem superfície não recebem fotos de textura; os objetos não visuais do ambiente estão registrados no manifesto.

## O que enviar à outra IA

Envie o PNG da peça e descreva o acabamento que deseja: concreto, metal galvanizado, borracha, plástico, pintura, desgaste etc. Use o filtro “Mostrar só geometrias distintas” para evitar pedidos repetidos. Instâncias repetidas também possuem arquivos individuais para rastreabilidade.

As fotos não são texturas prontas nem um mapa UV. Não peça apenas para pintar a foto com sombras: isso gera outra imagem da peça, que não se encaixa automaticamente no modelo. Para paredes e superfícies repetidas, peça uma textura plana e repetível. Para marcas localizadas, rótulos ou detalhes que precisam cair em posições específicas, será necessário preparar o UV da peça antes da aplicação.

## Pedido sugerido

“Use esta imagem apenas como referência de material. Gere uma textura de superfície plana, vista de frente, sem perspectiva, sem fundo de estúdio, sem sombras projetadas, sem luz rosa, sem brilho de iluminação incorporado e sem texto ou logotipo. Material desejado: [descreva aqui]. Imagem quadrada de 2048 × 2048 pixels. Para superfícies contínuas, as bordas devem se repetir sem emendas. Entregue primeiro o mapa de cor base (Base Color/Albedo).”

Mapas Roughness, Normal e Metallic precisam corresponder à mesma superfície. Se a outra ferramenta não gerar mapas PBR coerentes, envie somente a cor base; podemos preparar o restante na etapa de aplicação.

## Como devolver os arquivos

Preserve o nome do objeto como prefixo. Exemplos:

- WALL_RIGHT_basecolor.png
- FLOOR_HOSE_LEFT_MAIN_basecolor.png
- STORAGE_DRUM_LEFT_BODY_basecolor.png

Caso uma textura sirva para várias peças, informe os nomes ou o material compartilhado. Os materiais atuais aparecem no índice e no manifesto. Para uma peça com mais de um material, indique qual superfície deve receber a textura.

As imagens deste catálogo servem para preparar texturas. A aplicação e a conferência visual no Blender serão feitas depois que as texturas retornarem.
'''
(OUT / 'COMO_PEDIR_TEXTURAS.md').write_text(instructions, encoding='utf-8')
archive = BASE / 'catalogo_componentes_stage7.zip'
with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for path in sorted(OUT.rglob('*')):
        if path.is_file() and path.name != 'progresso.json':
            z.write(path, path.relative_to(BASE))
download = Path(r'C:\Users\erons\Downloads') / archive.name
shutil.copy2(archive, download)
print(json.dumps({'images': len(records), 'distinct_renders': data['count_distinct_renders'],
                  'collections': len(groups), 'nonvisual': len(data['nonvisual_objects']),
                  'zip_mb': round(archive.stat().st_size/1048576, 2), 'zip': str(download)}, ensure_ascii=False))
