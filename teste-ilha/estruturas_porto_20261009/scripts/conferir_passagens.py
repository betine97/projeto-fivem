"""Fecha o telhado sob as telhas e corrige acesso de varanda/galpao."""
import bpy,json,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def correct_geometry(mod):
    sc=bpy.context.scene
    if sc.get('passagens_conferidas'):return
    w=mod.C['w'];d=mod.C['d'];h=mod.C['H']
    # Corner returns conceal the exposed edge of the facade modules.
    for x in (-w/2+.08,w/2-.08):
        for y in (-d/2+.08,d/2-.08):mod.box('Retorno_canto',(x,y,h/2),(.25,.25,h),mod.M['Aco' if mod.BUILDID==10 else 'Pedra'],'Arquitetura')
    # The roof covering remains continuous between individually curved tiles.
    for o in list(bpy.data.objects):
        if not o.name.startswith('Telhas_ceramicas_'):continue
        canopy=mod.BUILDID==9 and abs(o.location.y)>1
        rw,rd,rh,rise=(18.72,12.22,4.78,2.0) if canopy else (w+.72,d+.72,h+.18,min(w+.72,d+.72)*.22)
        z=rh-.035;rr=max(.20,(rw-rd)*.50)
        A=(-rw/2,-rd/2,z);B=(rw/2,-rd/2,z);C=(rw/2,rd/2,z);D=(-rw/2,rd/2,z);E=(-rr,0,z+rise);F=(rr,0,z+rise)
        planes={'frente':[A,B,F,E],'direita':[B,C,F],'tras':[C,D,E,F],'esquerda':[D,A,E]}
        label=o.name.split('Telhas_ceramicas_')[1].split('.')[0];pts=planes[label]
        base=mod.mesh('Base_continua_telhas',pts,[tuple(range(len(pts)))],mod.M['Terracota'],'Cobertura');base.location=o.location.copy()
    if mod.BUILDID==1:
        wall=bpy.data.materials.get('Usuario_Reboco_creme') or mod.M['Reboco']
        for x in (w*.44-w/2,w*.89-w/2):
            o=mod.box('Retorno_parede_varanda',(x,-d/2+.825,1.5),(.20,1.65,3.0),wall,'Arquitetura')
            uv=o.data.uv_layers.new(name='UV_varanda') if not o.data.uv_layers else o.data.uv_layers.active
            for p in o.data.polygons:
                for li in p.loop_indices:
                    v=o.data.vertices[o.data.loops[li].vertex_index].co;uv.data[li].uv=(v.y+.5,v.z+.5)
            coll=o.copy();coll.data=o.data;coll.name='COL_'+o.name;mod.COL['Colisao_preparada'].objects.link(coll);coll['native_ybn']=False
        for o in bpy.data.objects:
            if o.name.startswith(('Portal_pedra','Portal_verga','Lanterna_','Suporte_luminaria')):o.location.y+=1.65
    if mod.BUILDID==10:
        # The concrete plinth must not cross the roll-up gate passage.
        for o in list(bpy.data.objects):
            if o.name.startswith('Rodape_concreto_galpao') and o.scale.x>1:bpy.data.objects.remove(o,do_unlink=True)
        gate=6.1;seg=(w-gate)/2
        for x in (-(gate+seg)/2,(gate+seg)/2):mod.box('Rodape_concreto_lateral_portao',(x,-d/2-.05,.52),(seg,.05,1.04),mod.M['Concreto'],'Esquadrias')
        x0=-w/2+.3;x1=-w/2+1.64;y0=d/2-3.7;z=2.84
        mod.tube('Guarda_mezanino',[(x1,y0,z+1.0),(w/2-.3,y0,z+1.0)],.035,mod.M['Ferro'],'Interior_1')
        for j in range(10):
            x=x1+(w/2-.3-x1)*j/9;mod.tube('Montante_guarda_mezanino',[(x,y0,z),(x,y0,z+1)],.025,mod.M['Ferro'],'Interior_1')
        for dx in (-.65,.65):mod.tube('Corrimao_mezanino',[(x0+.65+dx,d/2-5.65,1.0),(x0+.65+dx,6.65,z+1.0)],.030,mod.M['Ferro'],'Interior_1')
    if mod.BUILDID in (6,7,8):
        positions=(w*.26,) if mod.BUILDID==7 else (-w*.31,w*.31)
        for x in positions:mod.shelf(x,-d/2+.65,0,'Interior_1',1.55,pharma=mod.BUILDID==7)
    sc['passagens_conferidas']=True

def update():
    spec=importlib.util.spec_from_file_location('modelagem',ROOT/'scripts'/'modelar_estruturas.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    for path in sorted((ROOT/'modelos').glob('[0-9][0-9]_*.blend')):
        bpy.ops.wm.open_mainfile(filepath=str(path));id=int(path.stem[:2]);mod.BUILDID=id;mod.C=dict(mod.CFG[id]);mod.C.update(story=3.2,H=mod.C.get('h',mod.C['n']*3.2))
        mod.COL={c.name:c for c in bpy.data.collections};mod.M={m.name:m for m in bpy.data.materials};mod.MATCACHE={}
        correct_geometry(mod);mod.camera();bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)
        mod.render(ROOT/'previews'/f'{id:02}_exterior.png')
        if id in (1,6,7,8,10):mod.render(ROOT/'previews'/f'{id:02}_interior.png',True)
        jf=ROOT/'dados'/f'{id:02}_modelo.json';data=json.loads(jf.read_text(encoding='utf-8'));data['passagens_conferidas']=True;jf.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
        print('PASSAGENS_CORRIGIDAS',id,flush=True)
    print('PASSAGENS_CONCLUIDAS',flush=True)

if __name__=='__main__':update()
