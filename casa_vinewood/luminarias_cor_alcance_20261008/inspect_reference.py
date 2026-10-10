import sys,json
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1]
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
from szio.rpf import open_rpf
from szio.gta5 import try_load_asset
from dataclasses import asdict
from PIL import Image
from io import BytesIO
game=Path(r'C:/Program Files (x86)/Steam/steamapps/common/Grand Theft Auto V')
archive=open_rpf(game/'x64c.rpf').open_nested('levels/gta5/interiors/int_props/int_residential.rpf')
for n in ['v_res_fh_floorlamp','v_res_fh_lampa_on','v_res_fa_lamp1on']:
    dest=P/(n+'.ydr');dest.write_bytes(archive.read_bytes(n+'.ydr'))
    a=try_load_asset(dest)
    for l in a.lights:print(n,l.light_type.name,tuple(l.position),'power',l.intensity,'range',l.falloff,'exponent',l.falloff_exponent,'angles',l.cone_inner_angle,l.cone_outer_angle,'flags',l.flags)
D=R/'server-data/resources/cidade_mansao/stream'
for n,tx in [('mansao_spot_embutido','spot_lente'),('mansao_pendentes','mansao_led_quente')]:
    a=try_load_asset(D/(n+'.ydr'));im=Image.open(BytesIO(a.shader_group.embedded_textures[tx].data.read_bytes()));print(n,'led pixel',im.getpixel((0,0)))
print('spot heights',__import__('collections').Counter(round(p['position'][2],2) for p in json.loads((P/'spots_instalados.json').read_text())))
