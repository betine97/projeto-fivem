"""Verificação por reabertura, movimento avaliado, contato e integridade dos originais."""
import bpy,bmesh,json,hashlib,math,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];r=json.loads((P/'dados/preparacao_vegetacao_vento.json').read_text(encoding='utf8'))
base=json.loads((P/'dados/implantacao.json').read_text(encoding='utf8'));checks=[];measures=[]
def check(name,ok,details=None):checks.append(dict(nome=name,ok=bool(ok),detalhes=details))
def coords(o,dg):
    ev=o.evaluated_get(dg);me=ev.to_mesh();a=np.empty(len(me.vertices)*3,np.float32);me.vertices.foreach_get('co',a);ev.to_mesh_clear();return a.reshape(-1,3)
bpy.ops.wm.open_mainfile(filepath=str(P/r['arquivo']))
check('dezoito_modelos_preparados',len(r['vento'])==18 and len(r['modelos_lote02'])==8)
check('arquivo_anterior_preservado',(P/'porto_esperanca_texturas_lote01.blend').is_file() and (P/'porto_esperanca.blend').is_file())
check('sem_instalacao',not r['instalado_fivem'] and not r['vento_nativo_validado'])
check('terreno_e_lotes_preservados',len(bpy.data.collections['01_TERRENO'].objects)==16 and sum('id_lote' in o for o in bpy.data.collections['05_RESERVAS_E_IDENTIFICACAO'].objects)==25)
for item in base['modelos']:
    objects=[o for o in bpy.data.collections['04_VEGETACAO'].objects if o.get('modelo')==item['id']]
    check('contagem_'+item['id'],len(objects)==base['contagens_vegetacao'][item['id']])
    if item['id'] not in [w['id'] for w in r['vento']]:check('especie_procedural_preservada_'+item['id'],len(bpy.data.objects[item['id']].data.polygons)==item['poligonos'])
pos=json.loads((P/'dados/vegetacao_posicoes.json').read_text(encoding='utf8'))
expected=sorted((p['modelo'],p['x'],p['y'],p['z'],p['escala']) for p in pos if p['modelo']!='capim')
actual=sorted((o.get('modelo'),*o.location[:],o.scale.x) for o in bpy.data.collections['04_VEGETACAO'].objects if o.get('modelo'))
check('posicoes_escalas_preservadas',len(actual)==len(expected) and all(a[0]==b[0] and all(abs(x-y)<.001 for x,y in zip(a[1:],b[1:])) for a,b in zip(actual,expected)))
cols=bpy.data.collections['11_COLISAO_VEGETACAO_IMPLANTACAO'].objects
check('colisores_implantados',len(cols)==r['colisores_implantados'])
check('colisores_alinhados',all(max(abs(c.matrix_world[i][j]-bpy.data.objects[c['origem_visual']].matrix_world[i][j]) for i in range(4) for j in range(4))<1e-6 for c in cols))
check('grama_pedras_preservadas',sum(o.name.startswith('CAPIM') for o in bpy.data.collections['04_VEGETACAO'].objects)==base['tufos_grama'] and len(bpy.data.collections['06_PEDRAS'].objects)==base['pedras'])
for manifest in [P/'texturas/troncos/manifesto.json',P/'texturas/folhas/lote01/manifesto.json',P/'texturas/folhas/lote02/manifesto.json']:
    m=json.loads(manifest.read_text(encoding='utf8'));check('originais_intactos_'+manifest.parent.name,all(hashlib.sha256((P/i['arquivo']).read_bytes()).hexdigest()==i['sha256'] for i in m['arquivos']))

# Cena isolada para medir cada grafo sem avaliar milhares de árvores.
s=bpy.data.scenes.new('VALIDACAO_TEMPORARIA');bpy.context.window.scene=s;s.render.fps=24
for item in r['vento']:
    key=item['id'];o=bpy.data.objects[key];s.collection.objects.link(o);o.hide_set(False);o.hide_viewport=False
    me=o.data;mask=np.empty(len(me.vertices),np.float32);me.attributes['vento_peso'].data.foreach_get('value',mask)
    s.frame_set(1);dg=bpy.context.evaluated_depsgraph_get();a=coords(o,dg)
    s.frame_set(31);dg=bpy.context.evaluated_depsgraph_get();b=coords(o,dg)
    delta=np.linalg.norm(a-b,axis=1);fixed=float(delta[mask==0].max());moving=float(delta[mask>0].max())
    check('vento_mexe_folhas_'+key,moving>.002,round(moving,6));check('bases_e_troncos_fixos_'+key,fixed<1e-6,round(fixed,9))
    check('malha_vento_finita_'+key,np.isfinite(a).all() and np.isfinite(b).all() and len(a)==len(me.vertices))
    bm=bmesh.new();bm.from_mesh(bpy.data.objects['COL_'+key].data);check('colisor_fechado_'+key,all(e.is_manifold for e in bm.edges));bm.free()
    cm=bpy.data.objects['COL_'+key].data
    bv=BVHTree.FromPolygons([v.co for v in cm.vertices],[p.vertices[:] for p in cm.polygons],all_triangles=False)
    probes=[v.co for v in cm.vertices if v.co.z<.25]
    hit=any(bv.ray_cast(Vector((v.x*.999,v.y*.999,-1)),Vector((0,0,1)),100)[0] is not None for v in probes)
    check('raio_encontra_tronco_'+key,hit)
    measures.append(dict(id=key,deslocamento_folhas_entre_quadros_m=moving,deslocamento_vertices_fixos_m=fixed))
    s.collection.objects.unlink(o)

# Rigid bodies ativos contra caules passivos, comparados a queda livre sem obstáculo.
s=bpy.data.scenes['Fisica e vento'];bpy.context.window.scene=s;s.frame_set(1)
for frame in range(1,18):s.frame_set(frame);bpy.context.view_layer.update()
dg=bpy.context.evaluated_depsgraph_get();contacts=[]
for t in r['teste_contato']:
    ball=bpy.data.objects[t['bola']].evaluated_get(dg).matrix_world.translation
    free=bpy.data.objects[t['controle']].evaluated_get(dg).matrix_world.translation
    check('corpo_rigido_contato_'+t['modelo'],ball.z>t['topo_caule_m']-.20 and ball.z>free.z+.35,dict(z_contato=ball.z,z_queda_livre=free.z,topo=t['topo_caule_m']))
    contacts.append(dict(modelo=t['modelo'],z_contato_m=ball.z,z_controle_m=free.z))
for item in r['vento']:
    key=item['id'];bpy.ops.wm.open_mainfile(filepath=str(P/'modelos/vegetacao_vento'/(key+'.blend')));s=bpy.context.scene
    o=bpy.data.objects[key];c=bpy.data.objects['COL_'+key]
    imgs={n.image for m in o.data.materials if m and m.use_nodes for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image}
    check('projeto_individual_'+key,s.get('modelo')==key and s.camera is not None and len(o.modifiers)==1 and o.modifiers[0].type=='NODES')
    check('colisao_passiva_individual_'+key,c.rigid_body is not None and c.rigid_body.type=='PASSIVE' and c.rigid_body.collision_shape=='MESH' and c.hide_render)
    check('imagens_individuais_packed_'+key,len(imgs)==2 and all(im.packed_file is not None for im in imgs),len(imgs))
native=json.loads((P/'dados/colisoes_vegetacao_nativas.json').read_text(encoding='utf8'))
check('dezoito_YBN_reabertos',native['quantidade']==18 and all(i['reaberto'] and (P/i['arquivo']).is_file() for i in native['arquivos']))
for fn in ['catalogo_lote02.png','vento_e_contato.png','vento.mp4']:check('previa_'+fn,(P/'previews/vegetacao_vento'/fn).is_file())
result=dict(revisao=r['revisao'],aprovado=all(c['ok'] for c in checks),verificacoes=checks,medidas_vento=measures,teste_contato=contacts,validacao_fivem=False,aprovacao_visual_usuario='pendente')
(P/'dados/verificacao_vegetacao_vento.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('VERIFICACAO_VEGETACAO_VENTO',len(checks),'PASSOU' if result['aprovado'] else 'FALHOU',flush=True)
if not result['aprovado']:raise RuntimeError([c for c in checks if not c['ok']])
