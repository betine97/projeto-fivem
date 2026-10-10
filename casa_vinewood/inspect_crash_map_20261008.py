import sys,json
from pathlib import Path
sys.path[:0]=['laboratorio_fivem/work/pydeps',r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps','casa_vinewood/work/crash_deps']
from szio.gta5 import try_load_asset
from szio.gta5.entities import EntityMloInstance
from capstone import *
r=json.loads(Path('casa_vinewood/crash_20261008_4f1afc18-abaa-4821-b293-bae77286b967.json').read_text())
c=Cs(CS_ARCH_X86,CS_MODE_64)
# Exception bytes start two bytes into the first instruction. Start at +2.
for i in c.disasm(bytes.fromhex(r['code_bytes'])[2:],0x93419f-46):
    print(hex(i.address),i.mnemonic,i.op_str)
def vec(x):return list(x)
for p in Path('server-data/resources/cidade_mansao/stream').glob('*.ymap'):
    a=try_load_asset(p)
    if p.stem=='cidade_mansao' or any(isinstance(e,EntityMloInstance) for e in a.entities):
        print('MAP',p.name, 'extents',a.streaming_extents,'flags',a.flags,'content',a.content_flags)
        for e in a.entities: print('ENTITY',str(e.archetype_name),type(e).__name__,vec(e.position),e.flags,e.lod_level)
for p in Path('server-data/resources/cidade_mansao/stream').glob('*.ytyp'):
    a=try_load_asset(p)
    for ar in a.archetypes:
        if str(ar.name)=='mansao_teto':print('ARCHETYPE',str(ar.name),ar.type,ar.flags,ar.physics_dictionary,'rooms',len(ar.rooms),'portals',len(ar.portals))
