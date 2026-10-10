import json
from pathlib import Path
OUT=Path(__file__).resolve().parent
rows={r['model']:r for r in json.loads((OUT/'candidatos_renderizados.json').read_text(encoding='utf-8'))}
choices=[
    ('cs1_05_house_03','Casa com arcos e telhas','Paleto Bay','Alvenaria rebocada, grades, entrada em arco e telhas cerâmicas. É a opção que mais aproxima o conjunto do estilo pedido.','verso',True),
    ('cs1_05_house_01','Casa com varanda e telhas','Paleto Bay','Paredes rebocadas, telhado cerâmico, varanda e trecho de muro incluído no modelo.','verso',True),
    ('cs1_05_house_02','Casa térrea de alvenaria','Paleto Bay','Casa baixa, entrada com degraus e telhado de várias águas. Fachada simples e compacta.','verso',False),
    ('cs2_01_deshous_2','Casa térrea com varanda','Grapeseed','Paredes em tom claro, janelas com grades e cobertura baixa. Corpo compacto, sem um lote grande anexado.','frente',False),
    ('cs2_01_deshous1','Casa rural com lote','Grapeseed','Alvenaria clara, varanda coberta e trecho de muro. O modelo inclui parte do lote, exigindo mais espaço.','frente',False),
    ('cs2_01_house5','Casa rural com duas varandas','Grapeseed','Casa simples do interior, com partes rebocadas e de madeira. Alternativa para áreas rurais da ilha.','verso',False),
]
selected=[]
for model,title,region,description,first,recommended in choices:
    r=rows[model]
    assert not r.get('error') and not r['missing_diffuse'] and r['placements']
    for label in ['frente','verso']: assert (OUT/r['image_'+label]).is_file()
    r.update(title=title,region=region,description=description,first_view=first,recommended=recommended,
             visually_reviewed=True,classification='exterior em um drawable; nenhuma montagem de várias peças visuais',
             readiness='seleção visual; colocação, colisão e funcionamento no FiveM pendentes')
    selected.append(r)
reasons={
    'cs1_05_house_04':'Aparência predominantemente de madeira; menos próxima da seleção de alvenaria.',
    'cs2_01_deshous4':'Lote extenso e muro grande; menos prático para iniciar.',
    'cs4_04_desert_house':'Peças soltas visíveis no mesmo drawable; exige limpeza antes de usar.',
    'cs4_06_smallhouse':'Trailer; estilo fora do pedido e duas texturas ausentes na prévia.',
    'cs3_04_house01':'Modelo incompleto: painéis e muros sem o corpo completo da casa.',
    'cs3_04_house02':'Modelo incompleto: painéis e cercas sem o corpo completo da casa.',
}
(OUT/'selecao.json').write_text(json.dumps({'selected':selected,'excluded':reasons,'game_installed':False},ensure_ascii=False,indent=2),encoding='utf-8')
template='''<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Casas do norte · Seleção 01</title>
<style>
:root{font-family:Segoe UI,Arial,sans-serif;color:#e8eeeb;background:#101814;color-scheme:dark}*{box-sizing:border-box}body{margin:0}main{max-width:1500px;margin:auto;padding:42px 44px 28px}.eyebrow{color:#9bd7b3;letter-spacing:2px;font-size:11px;font-weight:700}header{display:flex;justify-content:space-between;gap:28px;align-items:center;margin-bottom:26px}h1{font-size:36px;letter-spacing:-1px;margin:10px 0}header p{max-width:740px;color:#aebeb5;font-size:14px;line-height:1.65;margin:0}.summary{padding:18px 24px;background:#1b2d22;border:1px solid #34533d;border-radius:12px;min-width:170px;text-align:center}.summary strong{display:block;color:#a9e8bb;font-size:30px}.summary span{font-size:12px;color:#b2c5b8}.info{padding:12px 16px;border:1px solid #314239;border-radius:9px;background:#16221a;margin-bottom:24px;font-size:12px;color:#b6c9bd;line-height:1.65}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:20px}.card{background:#1a241e;border:1px solid #344238;border-radius:14px;overflow:hidden}.card.chosen{border-color:#9ee9b9;box-shadow:0 0 0 1px #9ee9b9}.media{position:relative;background:#727a7b}.media img{display:block;width:100%;aspect-ratio:900/650;object-fit:contain}.number{position:absolute;top:13px;left:13px;color:#d8f4e0;background:#101a15d9;border:1px solid #778e7e;border-radius:6px;padding:5px 8px;font-size:12px}.recommended{position:absolute;top:13px;right:13px;color:#203b2a;background:#b7e4c2;border-radius:5px;padding:5px 8px;font-size:10px;font-weight:700}.card-body{padding:18px}.region{font-size:10px;text-transform:uppercase;color:#98bd9f;letter-spacing:1px}h2{font-size:19px;margin:7px 0 9px;letter-spacing:-.3px}.description{font-size:12px;line-height:1.65;min-height:60px;margin:0 0 14px;color:#aab8af}.metrics{font-size:10px;color:#aebeb5;padding-top:12px;border-top:1px solid #334037}.controls{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-top:14px}button{font:inherit;cursor:pointer;border:1px solid #536c5b;border-radius:7px;background:#25382c;color:#e3f1e7;padding:9px 12px;font-size:12px}button:hover{background:#365241}button:focus-visible{outline:2px solid #bcf1cc;outline-offset:3px}.choose{background:#b4e5c2;color:#193824;border-color:#b4e5c2;font-weight:650}.chosen .choose{background:#244d32;color:#c4f3d1}.model{margin-top:12px;font-size:10px;color:#8d9e92;word-break:break-all}footer{display:flex;justify-content:space-between;align-items:center;gap:20px;color:#a6b9ac;font-size:12px;line-height:1.6;padding:26px 0 10px}#selection{color:#c5efd1}#export:disabled{opacity:.4;cursor:default}@media(max-width:1050px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}main{padding:24px}h1{font-size:30px}}@media(max-width:650px){.grid{grid-template-columns:1fr}header{display:block}.summary{margin-top:20px}footer{align-items:flex-start;flex-direction:column}}@media print{button,.summary{display:none}.grid{grid-template-columns:repeat(2,1fr)}.card{break-inside:avoid}body{background:white;color:black}}
</style></head><body><main>
<header><div><div class="eyebrow">MODELOS ORIGINAIS DO GTA V · SELEÇÃO 01</div><h1>Casas do norte</h1><p>Seis exteriores de Paleto Bay e Grapeseed. Prioridade para casas baixas, alvenaria, varandas e telhas que se aproximam do visual latino-americano pedido.</p></div><div class="summary"><strong>6</strong><span>modelos selecionados</span></div></header>
<div class="info">Imagens dos modelos reais, renderizadas no Blender com suas texturas originais. Cada opção usa um único modelo visual. <strong>Esta galeria permite escolher os modelos; a colocação e a colisão no FiveM ainda precisam ser integradas e testadas.</strong></div>
<section class="grid" id="grid" aria-label="Casas selecionadas"></section>
<footer><div><span id="selection">Nenhuma casa escolhida.</span><br>As duas primeiras opções são as mais próximas do estilo pedido.</div><button id="export" disabled>Baixar minha seleção</button></footer>
</main><script>
const rows=__DATA__, chosen=new Set(), grid=document.getElementById('grid');
for(const [index,row] of rows.entries()){
 const card=document.createElement('article');card.className='card';
 const region=document.createElement('span');region.className='region';region.textContent=row.region;
 const media=document.createElement('div');media.className='media';
 const img=document.createElement('img');let view=row.first_view;img.src=row['image_'+view];img.alt=row.title+' — vista '+(view==='frente'?'1':'2');
 const number=document.createElement('span');number.className='number';number.textContent=String(index+1).padStart(2,'0');media.append(img,number);
 if(row.recommended){const rec=document.createElement('span');rec.className='recommended';rec.textContent='MAIS PRÓXIMA DO ESTILO';media.append(rec);}
 const body=document.createElement('div');body.className='card-body';
 const title=document.createElement('h2');title.textContent=row.title;
 const description=document.createElement('p');description.className='description';description.textContent=row.description;
 const metrics=document.createElement('div');metrics.className='metrics';metrics.textContent=row.dimensions_m.map(n=>n.toLocaleString('pt-BR',{maximumFractionDigits:1})).join(' × ')+' m · conjunto visual';
 const controls=document.createElement('div');controls.className='controls';
 const angle=document.createElement('button');angle.textContent='Ver outro ângulo';angle.onclick=()=>{view=view==='frente'?'verso':'frente';img.src=row['image_'+view];img.alt=row.title+' — vista '+(view==='frente'?'1':'2');};
 const choose=document.createElement('button');choose.className='choose';choose.textContent='Escolher';choose.setAttribute('aria-pressed','false');choose.onclick=()=>{if(chosen.has(row.model))chosen.delete(row.model);else chosen.add(row.model);const yes=chosen.has(row.model);card.classList.toggle('chosen',yes);choose.textContent=yes?'✓ Escolhida':'Escolher';choose.setAttribute('aria-pressed',String(yes));update();};
 const model=document.createElement('div');model.className='model';model.textContent=row.model;
 controls.append(angle,choose);body.append(region,title,description,metrics,controls,model);card.append(media,body);grid.append(card);
}
function update(){document.getElementById('selection').textContent=chosen.size?chosen.size+' casa(s) escolhida(s): '+rows.filter(r=>chosen.has(r.model)).map(r=>r.title).join(' · '):'Nenhuma casa escolhida.';document.getElementById('export').disabled=!chosen.size;}
document.getElementById('export').onclick=()=>{const data={version:1,selected:rows.filter(r=>chosen.has(r.model)),placement_in_game:false};const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='minhas_casas_do_norte.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
</script></body></html>'''
(OUT/'index.html').write_text(template.replace('__DATA__',json.dumps(selected,ensure_ascii=False).replace('</','<\\/')),encoding='utf-8')
print('GALLERY_READY',len(selected))
