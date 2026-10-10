import sys, shutil, json, io, struct
from pathlib import Path
P=Path(__file__).resolve().parent;W=P.parent;R=W.parent
sys.path.insert(0,str(R/'laboratorio_fivem/work/pydeps'))
from PIL import Image
T=P/'textures';T.mkdir(exist_ok=True);(P/'stream').mkdir(exist_ok=True)
def dds(im,name):
    im=im.convert('RGBA');levels=[]
    while True:
        b=io.BytesIO();im.save(b,format='DDS',pixel_format='DXT5' if im.getextrema()[3][0]<255 else 'DXT1');levels.append(b.getvalue())
        if im.size==(1,1):break
        im=im.resize((max(1,im.width//2),max(1,im.height//2)),Image.Resampling.BOX)
    h=bytearray(levels[0][:128]);struct.pack_into('<I',h,8,struct.unpack_from('<I',h,8)[0]|0x20000);struct.pack_into('<I',h,28,len(levels));struct.pack_into('<I',h,108,0x1000|8|0x400000)
    (T/(name+'.dds')).write_bytes(bytes(h)+b''.join(x[128:] for x in levels))
source=Path('C:/Users/erons/.codex/generated_images/01a11caa-4763-75e1-8cc8-55bb16a016c0/exec-3ddeffcb-2252-4c6d-ad7d-9700dac24d87.png')
shutil.copy2(source,P/'telas_referencia.png')
im=Image.open(source)
for i in range(2):dds(im.crop((i*im.width//2,0,(i+1)*im.width//2,im.height)).resize((512,1024),Image.Resampling.LANCZOS),'apar_arte'+str(i+1))
for key in ['madeira','madeira_n','preto','bronze','ceramica','folha','led','normal','spec','spec_fosco','spec_metal']:
    shutil.copy2(W/'bar_referencia_20261008/textures'/('bar_'+key+'.dds'),T/('apar_'+key+'.dds'))
dds(Image.new('RGB',(4,4),(234,227,210)),'apar_creme')
dds(Image.new('RGBA',(4,4),(47,49,46,115)),'apar_vidro_transparente')
spec={'model':'mansao_parede_aparador','door_model':'mansao_porta_vidro_aparador','collection':'26_PAREDE_APARADOR_REFERENCIA',
      'origin':json.loads((W/'medidas_estudo.json').read_text())['native_origin'],
      'placement':{'x':14.168,'y':-.98,'z':-.8},'wall':{'x':14.186,'ceiling_z':2.358,'left_y':-.95,'right_y':-6.582},
      'opening':{'u0':3.64,'u1':4.74,'z0':0,'z1':2.5},
      'door_hinge_local':[4.696,0,.015],'door_width':1.012,'door_height':2.427,
      'collision_boxes':[],'door_collision_boxes':[], 'in_game_verified':False}
(P/'spec.json').write_text(json.dumps(spec,indent=2),encoding='utf-8')
# Reuse only the existing modelling helpers, not their scene/build/install steps.
src=(W/'bar_referencia_20261008/build.py').read_text(encoding='utf-8').split('L=4.38;')[0]
src=src.replace("'24_BAR_PAREDE_REFERENCIA'","spec['collection']")
src=src.replace("['madeira','marmore','arte','preto','bronze','creme','ceramica','vidro','vinho','rotulo','folha','led','vidro_transparente']","['madeira','arte1','arte2','preto','bronze','creme','ceramica','folha','led','vidro_transparente']")
src=src.replace('bar_','apar_').replace("if family in ['madeira','arte']:","if family in ['madeira','arte1','arte2']:")
src=src.replace("['arte','folha','rotulo','creme','ceramica']","['arte1','arte2','folha','creme','ceramica']")
# The edit-safe helpers keep normals, real bevels, complete UV/color layers.
(P/'build.py').write_text(src+(P/'model_body.py').read_text(encoding='utf-8'),encoding='utf-8')
print('APARADOR_MATERIALS_READY',flush=True)
