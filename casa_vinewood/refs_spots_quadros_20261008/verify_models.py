"""Verify real native files: cavities, placement, UVs, texture mips, LODs and physics."""
import sys,json,struct,io,hashlib
from pathlib import Path
from collections import Counter
P=Path(__file__).resolve().parent;R=P.parents[1]
OUT=R/'server-data/resources/cidade_mansao/stream' if '--installed' in sys.argv else P/'stream'
D=Path(json.loads((P/'baseline.json').read_text())['backup'])/'resource/stream'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from PIL import Image
from szio.gta5 import try_load_asset,LodLevel
pack=json.loads((P/'package.json').read_text());modeling=json.loads((P/'modeling_report.json').read_text());result={}
def load(p):
    a=try_load_asset(p);assert a is not None,p;return a
def geometries(a,lod=LodLevel.HIGH):return [g for m in a.models[lod] for g in m.geometries]
def triangles(a):return np.concatenate([g.vertex_buffer['Position'][g.index_buffer.reshape(-1,3)] for g in geometries(a)])
def ray(tris,origin,direction,maximum=100):
    origin=np.array(origin);direction=np.array(direction);e1=tris[:,1]-tris[:,0];e2=tris[:,2]-tris[:,0]
    h=np.cross(direction,e2);det=np.einsum('ij,ij->i',e1,h);ok=abs(det)>1e-10
    inv=np.divide(1,det,out=np.zeros_like(det),where=ok);s=origin-tris[:,0]
    u=inv*np.einsum('ij,ij->i',s,h);q=np.cross(s,e1);v=inv*(q@direction);t=inv*np.einsum('ij,ij->i',e2,q)
    ok&=(u>=-1e-6)&(v>=-1e-6)&(u+v<=1+1e-6)&(t>1e-6)&(t<=maximum)
    ids=np.flatnonzero(ok)
    if len(ids)==0:return None
    i=ids[np.argmin(t[ids])];return float(t[i]),int(i)
def collision(a):
    rows=[]
    if a.bounds is None:return Counter()
    for b in a.bounds.children:
        v=np.array([v.co for v in b.geometry_vertices])
        for t in b.geometry_primitives:
            coords=v[list(t.vertices)];canonical=min(tuple(np.round(np.roll(coords,i,axis=0).ravel(),4)) for i in range(len(coords)))
            rows.append((t.primitive_type.value,int(t.material.to_packed()),canonical,t.radius,
                         int(b.composite_collision_type_flags),int(b.composite_collision_include_flags)))
    return Counter(rows)
def shader_signature(s):
    return s.preset_filename,s.render_bucket,[(p.name,str(p.value)) for p in s.parameters]
def mem(path):
    head=path.read_bytes()[:16];assert head[:4]==b'RSC7';_,_,sysflag,gfxflag=struct.unpack('<IIII',head)
    def size(f):
        count=((f>>27)&1)+((f>>26)&1)*2+((f>>25)&1)*4+((f>>24)&1)*8+((f>>17)&127)*16+((f>>11)&63)*32+((f>>7)&15)*64+((f>>5)&3)*128+((f>>4)&1)*256
        return (512<<(f&15))*count
    return {'system_mib':size(sysflag)/1048576,'graphics_mib':size(gfxflag)/1048576,'disk_mib':path.stat().st_size/1048576}
shared=load(OUT/'mansao_quadros_refs.ytd').textures
for name in pack['installed_files']:
    a=load(OUT/name)
    if not name.endswith('.ydr'):result[name]={'native_reload':True,**mem(OUT/name)}
    if not name.endswith('.ydr'):continue
    for lod in a.models:
        for g in geometries(a,lod):
            for field in g.vertex_buffer.dtype.names:assert np.isfinite(g.vertex_buffer[field]).all(),(name,lod,field)
            assert len(g.index_buffer)%3==0 and g.index_buffer.max()<len(g.vertex_buffer)
            assert 0<=g.shader_index<len(a.shader_group.shaders)
            pts=g.vertex_buffer['Position'][g.index_buffer.reshape(-1,3)]
            assert np.min(np.linalg.norm(np.cross(pts[:,1]-pts[:,0],pts[:,2]-pts[:,0]),axis=1))>1e-12,(name,lod,'Degenerate triangles')
    textures=dict(shared);textures.update(a.shader_group.embedded_textures)
    for s in a.shader_group.shaders:
        for p in s.parameters:
            if isinstance(p.value,str):assert p.value in textures,(name,p.value,'Texture missing')
    result[name]={'native_reload':True,**mem(OUT/name)}
for key,t in shared.items():
    data=t.data.read_bytes();im=Image.open(io.BytesIO(data));assert im.size==(t.width,t.height)
    # Gen8 supports compressed mips down to 4 texels on the shorter axis.
    count=struct.unpack_from('<I',data,28)[0];assert count==max(1,int(np.log2(min(t.width,t.height)))-1),(key,count)
    if data[84:88]==b'DXT1':assert im.convert('RGBA').getchannel('A').getextrema()==(255,255)
    source=(P/'textures'/(key+'.dds')).read_bytes()
    assert data[128:]==source[128:128+len(data)-128],(key,'Compressed texels altered')
result['shared_art_textures']={'count':len(shared),'complete_gen8_mip_chains':True,'opaque_colours':True}
for name in ['mansao_pisos','mansao_teto']:
    a=load(OUT/(name+'.ydr'));old=load(D/(name+'.ydr'))
    assert collision(a)==collision(old),(name,'Walking/camera collision changed')
    assert [shader_signature(s) for s in a.shader_group.shaders]==[shader_signature(s) for s in old.shader_group.shaders]
    assert {k:t.data.read_bytes() for k,t in a.shader_group.embedded_textures.items()}=={k:t.data.read_bytes() for k,t in old.shader_group.embedded_textures.items()}
    result[name+'.ydr'].update(preserved_physics=True,preserved_shader_values=True,preserved_texture_bytes=True)
oldceil=triangles(load(D/'mansao_teto.ydr'));oldfloor=triangles(load(D/'mansao_pisos.ydr'))
newceil=triangles(load(OUT/'mansao_teto.ydr'));newfloor=triangles(load(OUT/'mansao_pisos.ydr'))
allold=np.concatenate([oldceil,oldfloor]);allnew=np.concatenate([newceil,newfloor]);recess_errors=[]
for row in modeling['spots']:
    x,y,z=row['position'];source=(x,y,z-.03);old=ray(allold,source,(0,0,1),.1);new=ray(allnew,source,(0,0,1),.1)
    assert old and abs(old[0]-.03)<.002,(row['id'],'Original ceiling')
    assert new and abs(new[0]-.078)<.001,(row['id'],'Recess blocked',new)
    rim=ray(allnew,(x+.075,y,z-.03),(0,0,1),.1);assert rim and abs(rim[0]-.03)<.002,(row['id'],'Ceiling around fixture missing')
    recess_errors.append(abs(new[0]-.078))
    if row['ceiling_object'].startswith('Laje'):
        oldtop=ray(oldfloor,(x,y,3.05),(0,0,-1),1);newtop=ray(newfloor,(x,y,3.05),(0,0,-1),1)
        assert oldtop and newtop and abs(oldtop[0]-newtop[0])<.00002,(row['id'],'Upper floor top changed')
result['recesses']={'count':len(recess_errors),'max_error_m':float(max(recess_errors)),'upper_floor_top_preserved':True}
spot=load(OUT/'mansao_spot_embutido.ydr')
counts={l.name:sum(len(g.index_buffer)//3 for g in geometries(spot,l)) for l in spot.models}
assert counts==pack['spot_lod_triangles'];assert all(counts[a]>counts[b] for a,b in [('HIGH','MEDIUM'),('MEDIUM','LOW'),('LOW','VERYLOW')])
assert spot.bounds is None
result['spot_lods']=counts
walls=triangles(load(D/'mansao_paredes.ydr'));placement={}
for art in pack['artworks']:
    h=art['heading'];rot=np.array([[np.cos(h),-np.sin(h),0],[np.sin(h),np.cos(h),0],[0,0,1]])
    p=np.array(art['position']);back=rot@np.array([0,1,0]);gaps=[]
    for x in [-art['width_m']/2,0,art['width_m']/2]:
        for z in [-art['height_m']/2,0,art['height_m']/2]:
            hit=ray(walls,p+rot@np.array([x,0,z]),back,.05)
            assert hit,(art['name'],x,z,'Not backed by a wall')
            assert .004<hit[0]<.025,(art['name'],'Touching/intersecting wall',hit)
            gaps.append(hit[0])
    a=load(OUT/(art['model']+'.ydr'));canvas=[]
    for g in geometries(a):
        s=a.shader_group.shaders[g.shader_index]
        if any(isinstance(t.value,str) and t.value==f"quadro_{art['print']}_cor" for t in s.parameters):
            vb=g.vertex_buffer;sel=vb['Normal'][:,1]<-.9;pts=vb['Position'][sel];uv=vb['TexCoord0'][sel]
            expected=np.stack([pts[:,0]/art['canvas_width_m']+.5,.5-pts[:,2]/art['canvas_height_m']],axis=1)
            assert np.allclose(uv,expected,atol=2e-5),(art['model'],'Canvas flipped or stretched')
            canvas.append(len(pts))
    assert canvas and not a.shader_group.embedded_textures
    assert sum(collision(a).values())==12
    placement[art['name']]={'wall_clearance_m':[min(gaps),max(gaps)],'height_from_floor_center_m':p[2]+.8,'correct_front_uv':True}
result['artwork_placement']=placement
typ=load(OUT/'mansao_referencias.ytyp');mp=load(OUT/'mansao_referencias.ymap')
assert len(typ.archetypes)==5 and len(mp.entities)==92
entity_counts=Counter(str(e.archetype_name) for e in mp.entities)
assert entity_counts['mansao_spot_embutido']==88
for art in pack['artworks']:assert entity_counts[art['model']]==1
for ar in typ.archetypes:
    if str(ar.name).startswith('mansao_quadro'):assert str(ar.texture_dictionary)=='mansao_quadros_refs'
oldtyp=load(D/'mansao_decoracao.ytyp');newtyp=load(OUT/'mansao_decoracao.ytyp')
assert len(oldtyp.archetypes)==len(newtyp.archetypes)
for a,b in zip(oldtyp.archetypes,newtyp.archetypes):
    if str(a.name)=='mansao_spots_led':continue
    assert str(a.name)==str(b.name) and np.allclose(a.bb_min,b.bb_min) and np.allclose(a.bb_max,b.bb_max)
stair=load(OUT/'mansao_spots_led.ydr');assert sum(len(g.index_buffer)//3 for g in geometries(stair))==480 and stair.bounds is None
result['map']={'ceiling_spots':88,'new_artworks':4,'existing_decor_preserved':True}
old_totals={'graphics_mib':0.,'system_mib':0.,'disk_mib':0.};new_totals={k:0. for k in old_totals}
for name in pack['installed_files']:
    new=mem(OUT/name)
    for k in new_totals:new_totals[k]+=new[k]
    if (D/name).exists():
        old=mem(D/name)
        for k in old_totals:old_totals[k]+=old[k]
result['allocation_delta']={k:round(new_totals[k]-old_totals[k],6) for k in new_totals}
result['allocation_note']='RSC7 declared allocation, not measured FPS/VRAM.'
result['passed']=True
result['verified_location']=str(OUT)
result['in_game_verified']=False
(P/'verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('NATIVE_QA_PASSED 88 real recesses; 4 wall-supported canvases; physics/shaders/textures preserved; 4 spot LODs',flush=True)
