import json, math
from pathlib import Path
def jenk(s):
    h=0
    for c in s.lower().encode():
        h=(h+c)&0xffffffff;h=(h+(h<<10))&0xffffffff;h^=h>>6
    h=(h+(h<<3))&0xffffffff;h^=h>>11;return (h+(h<<15))&0xffffffff
target=0x163243f9
point=(-960.8260498046875,367.928955078125,131.67041015625)
def visit(x, filename):
    if isinstance(x,dict):
        name=x.get('name') or x.get('archetype_name')
        pos=x.get('pos') or x.get('position')
        match=isinstance(name,str) and jenk(name)==target
        near=isinstance(pos,list) and len(pos)==3 and all(isinstance(v,(float,int)) for v in pos) and math.dist(point,pos)<2
        if match or near: print(json.dumps({'file':str(filename),'entry':x,'hash_match':match,'position_match':near}))
        for v in x.values():visit(v,filename)
    elif isinstance(x,list):
        for v in x:visit(v,filename)
for root in ['casa_vinewood/work','laboratorio_fivem/work']:
    for f in Path(root).glob('*.json'):
        try:visit(json.loads(f.read_text(encoding='utf-8-sig')),f)
        except (ValueError,UnicodeDecodeError):pass
