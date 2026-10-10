import sys,json,math
from pathlib import Path
from collections import deque
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'laboratorio_fivem'/'work'/'pydeps'))
from PIL import Image,ImageDraw,ImageFont
OUT=Path(__file__).resolve().parent.parent
r=json.loads((OUT/'medidas_estudo.json').read_text(encoding='utf-8'))
W,D=r['dimensions_m'];rise=r['levels_m'][1]
shaft=r['stairs']['upper_floor_opening'];void=[0,15.2,0,9]

# Verify room access with a flood fill at waist height, inside the floor plate.
# This checks partition geometry; it does not claim a FiveM collision test.
STEP=.1
audit={}
for level,z in [('terreo',.95),('superior',rise+.95)]:
 ymin=0 if level=='terreo' else -2.7
 nx,ny=round(W/STEP),round((D-ymin)/STEP)
 walls=[b['bounds'] for b in r['boxes'] if b['key'] in ['outer','ground','upper'] and b['bounds'][4]<z<b['bounds'][5]]
 def floor(x,y):
  if not(0<x<W and ymin<y<D):return False
  if level=='superior':
   if y<0 and x<15.2:return False
   if any(q[0]<x<q[1] and q[2]<y<q[3] for q in [void,shaft]):
    return 10<x<11.2 and 15.7<y<15.8
  return True
 def free(i,j):
  x,y=(i+.5)*STEP,ymin+(j+.5)*STEP
  return floor(x,y) and not any(a<=x<=b and c<=y<=d for a,b,c,d,lo,hi in walls)
 start=(round(12/STEP),round((13.5-ymin)/STEP));seen={start};q=deque([start])
 while q:
  i,j=q.popleft()
  for k,l in [(i-1,j),(i+1,j),(i,j-1),(i,j+1)]:
   if 0<=k<nx and 0<=l<ny and (k,l) not in seen and free(k,l):seen.add((k,l));q.append((k,l))
 checks={}
 for room in r['rooms']:
  if room['level']!=level:continue
  a,b,c,d=room['bounds'];x,y=(a+b)/2,(c+d)/2
  if room['name']=='Escada':x,y=9.2,15.55
  checks[room['name']]=(int(x/STEP),int((y-ymin)/STEP)) in seen
 assert all(checks.values()),(level,checks)
 audit[level]=dict(room_access=checks,reachable_cells=len(seen),grid_m=STEP)
(OUT/'verificacao_circulacao.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')

img=Image.new('RGB',(1500,1030),'#f3f1ea');draw=ImageDraw.Draw(img)
fontpath='C:/Windows/Fonts/arial.ttf';boldpath='C:/Windows/Fonts/arialbd.ttf'
def font(n,bold=False):return ImageFont.truetype(boldpath if bold else fontpath,n)
draw.text((50,30),'MANSÃO — ESTUDO INICIAL DO INTERIOR',fill='#24313b',font=font(30,True))
draw.text((50,76),'Distribuição baseada na planta compatibilizada • medidas do estudo sobre a casa candidata',fill='#5d666e',font=font(18))
S=26;Y=158
colors=['#e6dccc','#ddd7c9','#d5ded8','#e4e2d7','#d9e0e1','#eadfd1']
names={'Sala de estar':'Sala de estar','Sala de jantar':'Sala de jantar','Sala TV Jogos':'TV / Jogos','Hall de entrada':'Hall de entrada','Banheiro da suite':'Banheiro suíte','Sala intima / leitura':'Sala íntima / leitura','Circulacao quartos':'Circulação','Suite master':'Suíte master','Escritorio':'Escritório','Despensa':'Despensa','Lavanderia':'Lavanderia','Escada':'Escada em U','Banheiro social':'Banheiro social'}
for pane,(level,title) in enumerate([('terreo','TÉRREO'),('superior','1º ANDAR')]):
 X=75+pane*740
 draw.text((X,116),title,fill='#24313b',font=font(23,True))
 def point(x,y):return X+x*S,Y+(D-y)*S
 def rect(a,b,c,d):return (*point(a,d),*point(b,c))
 draw.rectangle(rect(0,W,0,D),fill='#e7e5df',outline='#48525a',width=2)
 if level=='superior':draw.rectangle(rect(15.2,W,-2.7,0),fill='#e7e5df',outline='#48525a',width=2)
 for n,room in enumerate(q for q in r['rooms'] if q['level']==level):
  a,b,c,d=room['bounds'];draw.rectangle(rect(a,b,c,d),fill=colors[n%len(colors)])
 if level=='superior':
  for q in [void,shaft]:
   a,b,c,d=q;draw.rectangle(rect(a,b,c,d),fill='#faf9f5',outline='#b5b8b5',width=1)
  x,y=point(7.6,4.5)
  draw.multiline_text((x,y),'VAZIO SOBRE A SALA\nPé-direito duplo',fill='#738087',font=font(18,True),anchor='mm',align='center')
 z=.95 if level=='terreo' else rise+.95
 for q in r['boxes']:
  a,b,c,d,lo,hi=q['bounds']
  if q['key'] in ['outer','ground','upper'] and lo<z<hi:draw.rectangle(rect(a,b,c,d),fill='#36424a')
 # Plan stair treads and mid-landing, aligned to the built geometry.
 draw.rectangle(rect(8.6,11.2,18.5,19.7),fill='#b89671',outline='#685a4a',width=1)
 for x0,x1 in [(8.6,9.8),(10,11.2)]:
  for i in range(9):draw.rectangle(rect(x0,x1,15.8+i*.3,15.8+(i+1)*.3),fill='#c6a784',outline='#786956',width=1)
 for room in (q for q in r['rooms'] if q['level']==level):
  a,b,c,d=room['bounds'];x,y=point((a+b)/2,(c+d)/2)
  label=names.get(room['name'],room['name'])
  if room['name']=='Escada':x,y=point(9.8,15.9);label='Escada'
  if room['name']=='Sala intima / leitura':x,y=point(13.2,17.0);label='Leitura'
  size=16 if b-a>3.3 else 13
  wrapped=[];line=''
  for word in label.split():
   candidate=(line+' '+word).strip()
   if line and draw.textlength(candidate,font=font(size))>(b-a)*S-10:
    wrapped.append(line);line=word
   else:line=candidate
  wrapped.append(line);label='\n'.join(wrapped)
  draw.multiline_text((x,y),label+'\n'+str(room['area_bruta_referencia_m2']).replace('.',',')+' m²',fill='#26353c',font=font(size),anchor='mm',align='center',spacing=4)
 # Overall dimensions are explicitly measured study dimensions, not inferred
 # square meters of the source screenshot.
 x0,y0=point(0,D+.7);x1,y1=point(W,D+.7)
 draw.line((x0,y0,x1,y1),fill='#79858b',width=1)
 for x in [x0,x1]:draw.line((x,y0-6,x,y0+6),fill='#79858b',width=1)
 draw.text(((x0+x1)/2,y0-13),'22,50 m',fill='#49575e',font=font(16),anchor='mm')
 draw.text((X,Y+D*S+88),'Frente / acesso ao deck',fill='#626f75',font=font(16))

draw.rounded_rectangle((50,842,1450,986),radius=14,fill='#fffdf8')
draw.text((75,862),'Paredes e lajes em escala métrica • passagens abertas • escada: 20 espelhos de 18,04 cm',fill='#35434c',font=font(19))
draw.text((75,899),'Corpo principal do estudo: 22,50 × 20,00 m. Áreas brutas: térreo 450,00 m²; superior 321,57 m².',fill='#35434c',font=font(18))
draw.text((75,938),'Sem mobília. A fachada original fica em uma coleção de referência. Esta versão é para avaliar o interior no Blender.',fill='#626d72',font=font(17))
img.save(OUT/'plantas_interior.png')

readme='''# Interior inicial da mansão

Abra `mansao_interior_inicial.blend`. O arquivo começa dentro da sala.

## Explorar

No editor 3D, use **View > Navigation > Fly Navigation**.
Use WASD para mover, E/Q para subir/descer e a roda do mouse para ajustar a velocidade. Shift reduz a velocidade para maior precisão. Enter confirma a posição; Esc cancela a navegação.
As câmeras da sala, do mezanino, da escada e do corte geral estão na coleção 08.

## O que está modelado

Térreo: sala de estar, jantar, cozinha, hall, escritório, lavabo, despensa, sala de TV/jogos e lavanderia.
Superior: suíte master, closet, banheiro da suíte, dois quartos, banheiro social, mezanino e sala íntima/leitura.
Escada em U, patamar, vão real na laje e guarda-corpos. Os cômodos têm passagens abertas. Sem mobília.

As coleções 02 e 03 separam as paredes dos pavimentos; 04 contém as lajes; 05 contém escada e guarda-corpos.
O teto superior está oculto na visualização para facilitar a inspeção: ative a coleção 06 para fechar a casa.
Ative a coleção 07 para exibir os nomes dos cômodos.

## Base e medidas

O candidato escolhido é `ch2_09b_hs05`; a geometria original está preservada e oculta na coleção 90. A envoltória interna é uma proposta simplificada, com aberturas para estudar o espaço. A correspondência exata do candidato com o print ainda não foi confirmada.

A distribuição segue a planta compatibilizada (imagem 3), adaptada ao corpo principal do modelo, com o vazio sobre a sala alinhado à fachada alta. A planta alternativa de 20 × 15 m não foi usada como medida da casa existente.

Dimensões do corpo principal proposto: 22,50 × 20,00 m.
Área bruta da laje térrea: 450,00 m².
Área bruta da laje superior, descontados os vãos da sala e escada e incluindo o volume frontal: 321,57 m².
Total das duas lajes: 771,57 m². São áreas do estudo, sem descontar paredes; não representam a área líquida confirmada da casa do jogo.

Piso térreo na coordenada local nativa Z=-0,800 m; superior Z=2,808 m; teto Z=6,488 m.
Desnível de 3,608 m, 20 espelhos de 18,04 cm, pisos de 30 cm e largura dos lances de 1,20 m.
Há aproximações nas aberturas e na espessura da envoltória. O estudo pode ser alterado antes de produzir o interior definitivo.

## Verificação

A área das lajes foi calculada a partir dos retângulos modelados, e os vãos foram verificados sem laje sobre eles.
A circulação entre hall/mezanino e todos os cômodos foi verificada em uma grade de 10 cm, na altura da cintura.
Renders conferem a sala, o mezanino, a escada e o corte geral.

Esta entrega é um estudo no Blender. Não foi instalada no FiveM e não possui ainda a etapa de exportação, colisões e teste no jogo.
'''
(OUT/'LEIA-ME.md').write_text(readme,encoding='utf-8')
print('CIRCULATION OK',audit)
print('PLAN SAVED',OUT/'plantas_interior.png')
