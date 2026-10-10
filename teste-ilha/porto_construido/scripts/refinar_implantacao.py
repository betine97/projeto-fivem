import bpy,numpy as np,json,random,math
from pathlib import Path
from mathutils import Vector
O=Path(__file__).resolve().parents[1];P=O.parent
bpy.ops.wm.open_mainfile(filepath=str(O/'ilha_porto_esperanca.blend'));s=bpy.context.scene
for c in bpy.data.collections:
    if c.name=='02_RIO_LAGO_MAR':
        for o in c.all_objects:
            if any(k in o.name.lower() for k in ['rio','lago']):o.hide_render=True;o.hide_viewport=True
for o in bpy.data.objects:
    if o.name.startswith('COL_'):o.hide_render=True
    for m in o.modifiers:
        if m.type=='NODES':m.show_render=False
bc=bpy.data.collections['10_CASAS_TEXTURIZADAS_E_COMERCIOS'];libs=[next(c for c in bpy.data.collections if c.name.startswith(f'Estrutura {id:02}_')) for id in range(1,11)]
rows=json.loads((O/'dados/implantacao_casas.json').read_text());extra=[]
for row in list(rows):
    if not row.get('label','').startswith('U') or 'quintal' in row['label']:continue
    id=int(row['name'][-2:]);x,y,z=row['position'];loty=y+6
    # Six separate plots for small residences, with service yards and accessible alleys.
    positions=[(-11,-8),(11,-8),(-11,9),(0,9),(11,9)] if id in [1,2,3] else [(-8,11),(8,11)]
    for j,(dx,dy) in enumerate(positions):
        if any(abs(p['position'][0]-(x+dx))<8 and abs(p['position'][1]-(loty+dy))<7 for p in rows+extra):continue
        cid=1+(j%3);o=bpy.data.objects.new(row['label'][:3]+' moradia '+str(j),None);o.instance_type='COLLECTION';o.instance_collection=libs[cid-1];bc.objects.link(o);o.location=(x+dx,loty+dy,z);o.rotation_euler[2]=0
        extra.append(dict(name=f'pe_estrutura_{cid:02}',position=list(o.location),heading=0,scale=1,label=o.name))
rows+=extra;(O/'dados/implantacao_casas.json').write_text(json.dumps(rows,indent=2))
# More natural ground color, without changing any of the user's photographs.
tex=O/'fontes/pe_solo_grama.png';im=bpy.data.images.load(str(tex),check_existing=True);im.pack()
for m in bpy.data.materials:
    if m.name.startswith('Solo nativo cs_rsn_sl_agrgrass_02'):
        tx=next(n for n in m.node_tree.nodes if n.type=='TEX_IMAGE');tx.image=im
sectors=json.loads((O/'dados/setores_alterados.json').read_text())
for row in sectors:row['materials'][0]=dict(texture='pe_solo_grama',file=str(tex))
(O/'dados/setores_alterados.json').write_text(json.dumps(sectors,indent=2))
grid=np.load(O/'dados/terreno.npz')['terrain'];rng=random.Random(202610091)
def sample(x,y):
    ix=(x-grid[0,0,0])/(grid[0,1,0]-grid[0,0,0]);iy=(y-grid[0,0,1])/(grid[1,0,1]-grid[0,0,1]);i,j=int(ix),int(iy);u,v=ix-i,iy-j
    return float((1-u)*(1-v)*grid[j,i,2]+u*(1-v)*grid[j,i+1,2]+(1-u)*v*grid[j+1,i,2]+u*v*grid[j+1,i+1,2])
co=bpy.data.collections.new('13_MATAS_DO_RESTANTE_DA_ILHA');s.collection.children.link(co);forest=[];occupied=set();keys=['03_caneleira','04_amendoeira','11_mangueira','06_arvore_rua','10_castanhola'];protos={k:next(o for o in bpy.data.objects if o.type=='MESH' and o.get('modelo')==k) for k in keys}
for a in range(80000):
    if len(forest)>=5200:break
    x=rng.uniform(-1070,1110);y=rng.uniform(-1260,1210)
    if -380<x<880 and -1160<y<70:continue
    if -850<x<-25 and -180<y<0:continue
    if -850<x<-590 and -345<y<-115:continue # Existing validation sample preserved.
    k=(int(x/14),int(y/14))
    if k in occupied:continue
    z=sample(x,y)
    if z<7 or z>285:continue
    sl=math.hypot(sample(x+2,y)-sample(x-2,y),sample(x,y+2)-sample(x,y-2))/4
    if sl>.95:continue
    key=rng.choice(keys);src=protos[key];o=bpy.data.objects.new('Mata '+key,src.data);co.objects.link(o);o.location=(x,y,z-.03);scale=rng.uniform(.76,1.18);o.scale=(scale,)*3;angle=rng.uniform(0,360);o.rotation_euler[2]=math.radians(angle)
    forest.append(dict(name='pe_veg_'+key,position=list(o.location),heading=angle,scale=scale));occupied.add(k)
(O/'dados/floresta.json').write_text(json.dumps(forest,indent=2))
rep=json.loads((O/'dados/construcao.json').read_text());rep.update(casas_instancias=len(rows),arvores_adicionadas_resto_ilha=len(forest));(O/'dados/construcao.json').write_text(json.dumps(rep,indent=2))
s.camera=bpy.data.objects['Porto construido | panorama'];s.frame_set(40);s['implantacao_refinada']=True
bpy.ops.wm.save_as_mainfile(filepath=str(O/'ilha_porto_esperanca.blend'),compress=True);print('PORT_REFINED',len(rows),len(forest),flush=True)
