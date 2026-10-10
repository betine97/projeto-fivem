import re,json,zlib
from pathlib import Path
out=Path(__file__).resolve().parent
for p in out.glob('mp*__*.ymt'):
 b=zlib.decompress(p.read_bytes()[16:],-15);print(p.name,len(b))
 print([s.decode('ascii') for s in re.findall(rb'[\x20-\x7e]{4,}',b) if b'mp_' in s.lower() or b'heist' in s.lower() or b'apt' in s.lower() or b'male' in s.lower()])
 (out/(p.stem+'.decompressed.bin')).write_bytes(b)
