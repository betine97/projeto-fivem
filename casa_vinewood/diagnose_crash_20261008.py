import struct,json,os,sys
from pathlib import Path
p=Path(os.environ['LOCALAPPDATA'])/'FiveM/FiveM.app/crashes'
f=p/sys.argv[1] if len(sys.argv)>1 else max(p.glob('*.dmp'),key=lambda f:f.stat().st_mtime);d=f.read_bytes()
u32=lambda off:struct.unpack_from('<I',d,off)[0]
u64=lambda off:struct.unpack_from('<Q',d,off)[0]
streams={u32(u32(12)+12*i):(u32(u32(12)+12*i+4),u32(u32(12)+12*i+8)) for i in range(u32(8))}
mods=[]
if 4 in streams:
    _,r=streams[4]
    for i in range(u32(r)):
        a=r+4+108*i;n=u32(a+20);name=d[n+4:n+4+u32(n)].decode('utf-16le',errors='replace')
        mods.append((u64(a),u32(a+8),Path(name).name))
regions=[]
if 5 in streams:
    _,r=streams[5]
    for i in range(u32(r)):
        a=r+4+16*i;regions.append((u64(a),u32(a+8),u32(a+12)))
if 9 in streams:
    _,r=streams[9];off=u64(r+8)
    for i in range(u64(r)):
        a=r+16+16*i;size=u64(a+8);regions.append((u64(a),size,off));off+=size
def mem(addr,size):
    for a,n,r in regions:
        if a<=addr and addr+size<=a+n:return d[r+addr-a:r+addr-a+size]
    return b''
def sym(addr):
    for a,n,name in mods:
        if a<=addr<a+n:return name+'+'+hex(addr-a)
    return hex(addr)
_,r=streams[6];cx=u32(r+164)
regs={name:u64(cx+off) for name,off in [('rax',120),('rcx',128),('rdx',136),('rbx',144),('rsp',152),('rbp',160),('rsi',168),('rdi',176),('r8',184),('r9',192),('r10',200),('r11',208),('r12',216),('r13',224),('r14',232),('r15',240),('rip',248)]}
stack=mem(regs['rsp'],4096)
trace=[]
for i in range(0,len(stack),8):
    addr=struct.unpack_from('<Q',stack,i)[0];s=sym(addr)
    if '+' in s and any(x in s for x in ['GTA5','GTAProcess','extra-natives','gta-']):trace.append([i,s])
report={'dump':f.name,'code':hex(u32(r+8)),'address':sym(u64(r+24)),
    'parameters':[hex(u64(r+40+8*i)) for i in range(min(15,u32(r+32)))],
    'registers':{k:hex(v) for k,v in regs.items()},'stack_candidates':trace[:45],
    'register_memory':{k:mem(v,64).hex() for k,v in regs.items() if k not in ['rip','rsp']}}
report['code_bytes']=mem(regs['rip']-48,128).hex()
report['stack_raw']=[{'offset':i,'value':hex(struct.unpack_from('<Q',stack,i)[0]),'symbol':sym(struct.unpack_from('<Q',stack,i)[0]),'pointee':mem(struct.unpack_from('<Q',stack,i)[0],64).hex()} for i in range(0,min(728,len(stack)),8)]
def jenk(s):
    h=0
    for c in s.lower().encode():
        h=(h+c)&0xffffffff;h=(h+(h<<10))&0xffffffff;h^=h>>6
    h=(h+(h<<3))&0xffffffff;h^=h>>11;return (h+(h<<15))&0xffffffff
names=['mansao_teto','cidade_mansao','mansao_paredes','mansao_pisos','mansao_escada','mansao_vidros','mansao_pendentes','mansao_bar_referencia']
report['mansion_hashes_in_register_memory']=[]
block=mem(regs['r14'],64)
if block:
    report['possible_entity_definition']={'archetype_hash':hex(struct.unpack_from('<I',block,0)[0]),'position':list(struct.unpack_from('<3f',block,16))}
for reg,addr in regs.items():
    block=mem(addr,2048) or mem(addr,512) or mem(addr,64)
    for name in names:
        pat=struct.pack('<I',jenk(name));off=block.find(pat)
        if off>=0:report['mansion_hashes_in_register_memory'].append({'register':reg,'offset':off,'model':name})
(Path(__file__).parent/('crash_20261008_'+f.stem+'.json')).write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k not in ['register_memory','stack_raw','stack_candidates']},indent=2))
