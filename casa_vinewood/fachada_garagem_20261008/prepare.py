import sys,json,hashlib,shutil,io,struct
from pathlib import Path
P=Path(__file__).resolve().parent;W=P.parent;R=W.parent;D=R/'server-data/resources/cidade_mansao'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
from PIL import Image
import numpy as np
for n in ['stream','textures','baseline/stream','native']:(P/n).mkdir(parents=True,exist_ok=True)
original={}
for f in D.rglob('*'):
    if f.is_file():
        key=f.relative_to(D).as_posix();original[key]=hashlib.sha256(f.read_bytes()).hexdigest()
        if f.suffix in ['.ydr','.ybn','.ymap','.lua','.json'] or f.name=='fxmanifest.lua':
            t=P/'baseline'/key;t.parent.mkdir(parents=True,exist_ok=True);t.write_bytes(f.read_bytes())
(P/'baseline_hashes.json').write_text(json.dumps(original,indent=2))
origin=json.loads((W/'medidas_estudo.json').read_text())['native_origin']
spec={'origin':origin,'collection':'70_FACHADA_ENTRADA_E_GARAGEM_20261008','models':['mansao_fachada_entrada','mansao_garagem_subsolo','mansao_porta_principal_nova','mansao_portao_subsolo'],
 'door_hinge':[3.98,7.45,-.785],'door_width':1.33,'door_height':2.96,'door_opening':[[3.90,7.19,-.825],[5.43,7.71,2.27]],
 'garage_floor':-4.20,'garage_ceiling':-1.28,'garage_inner':[6.40,12.80,-1.70,9.38],
 'gate_hinge':[9.6,9.44,-1.43],'gate_width':6.32,'gate_height':2.72,
 'ramp_x':[6.40,12.80],'ramp_y':[9.55,19.22],
 'earth_cuts':[
 [[6.10,-1.97,-4.45],[13.08,9.58,-1.096]],
 [[6.145,9.53,-4.45],[13.055,19.23,1.60]],
 [[3.62,14.52,-3.34],[5.87,19.23,-.58]]],
 'brick_extension':[[1.055,5.945,-.805],[3.645,7.60,2.14]],
 'protected_rooms':['Escritorio','Lavabo','Escada existente'],'garage_spaces':2,'in_game_verified':False}
(P/'spec.json').write_text(json.dumps(spec,indent=2))
# Reuse the actual facade texture, keeping the brick pattern continuous.
for name in ['im_wall_brick_32','im_wall_brick_32_n','im_wall_brick_32_s','im_wall32','im_wall32_n','im_wall32_s']:
    shutil.copy2(W/'work/textures'/(name+'.dds'),P/'textures'/(name+'.dds'))
for name in ['madeira','preto','bronze','vidro_transparente','normal','spec','spec_metal']:
    shutil.copy2(W/'parede_aparador_20261008/textures'/('apar_'+name+'.dds'),P/'textures'/('fach_'+name+'.dds'))
for name,color in [('fach_creme',(184,173,151,255)),('fach_cimento',(126,124,117,255)),('fach_sinal',(229,213,161,255)),('fach_led',(255,224,165,255)),('fach_led_branco',(255,247,224,255))]:
    im=Image.new('RGBA',(32,32),color);levels=[]
    while True:
        buf=io.BytesIO();im.save(buf,format='DDS',pixel_format='DXT1');levels.append(buf.getvalue())
        if im.size==(1,1):break
        im=im.resize((max(1,im.width//2),max(1,im.height//2)))
    h=bytearray(levels[0][:128]);struct.pack_into('<I',h,8,struct.unpack_from('<I',h,8)[0]|0x20000);struct.pack_into('<I',h,28,len(levels));struct.pack_into('<I',h,108,0x1000|8|0x400000)
    (P/'textures'/(name+'.dds')).write_bytes(bytes(h)+b''.join(x[128:] for x in levels))
print('FACADE_BASELINE_READY',len(original),flush=True)
