"""Copiar e inventariar o segundo lote sem alterar as imagens."""
import sys, json, hashlib, shutil
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parents[1]/'laboratorio_fivem/work/pydeps'))
from PIL import Image
items=[
 ('13_18_14-1','11_mangueira','lote01_03','Casca reutilizada provisoriamente; não foi recebido tronco exclusivo de mangueira.'),
 ('13_18_14-2','12_bananeira','lote02_04','Pseudocaules verdes, imagem própria.'),
 ('13_18_15-3','13_mangue','lote02_07','Associação pela sequência e aparência; raízes de suporte preservadas em 3D.'),
 ('13_18_16-4','14_arbusto_costeiro','lote02_08','Troncos e ramos de arbusto.'),
 ('13_18_17-5','15_palmeira_ana','lote02_06','Touceira de palmeira anã.'),
 ('13_18_18-6','16_palma_azul','lote02_03','Palmeira de folhas em leque azuladas.'),
 ('13_18_19-7','17_yucca','lote02_05','Caules múltiplos de yucca.'),
 ('13_18_20-8','18_cerca_viva','lote02_08','Casca de arbusto reutilizada na cerca viva.')]
dest=P/'texturas/folhas/lote02';dest.mkdir(parents=True,exist_ok=True)
rows=[]
for n,(suffix,key,trunk,note) in enumerate(items,11):
 src=Path('C:/Users/erons/Downloads')/('Imagem do ChatGPT 9 de out. de 2026, '+suffix+'.png')
 out=dest/f'folhas_{n:02d}.png';shutil.copy2(src,out)
 with Image.open(out) as im:
  meta=dict(largura=im.width,altura=im.height,modo=im.mode,canal_alpha='A' in im.getbands(),alpha_min_max=im.getchannel('A').getextrema())
 rows.append(dict(id=f'folhas_{n:02d}',arquivo=out.relative_to(P).as_posix(),origem=str(src),nome_original=src.name,sha256=hashlib.sha256(src.read_bytes()).hexdigest(),bytes=src.stat().st_size,imagem=meta,modelo_inicial=key,tronco=trunk,nota=note,associacao='inicial_pela_sequencia_e_aparencia; validacao_visual_pendente'))
manifest=dict(revisao='folhas-20261009-lote02-1',quantidade=8,imagens_alteradas=False,arquivos=rows)
(dest/'manifesto.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('OITO_ORIGINAIS_COPIADOS_E_INVENTARIADOS',flush=True)
