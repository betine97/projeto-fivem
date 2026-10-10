"""Reabrir arquivos e verificar imagens incorporadas, UV e implantação preservada."""
import bpy,json,math,hashlib
from pathlib import Path
P=Path(__file__).resolve().parents[1]
report=json.loads((P/'dados/aplicacao_texturas_lote01.json').read_text(encoding='utf8'))
base=json.loads((P/'dados/implantacao.json').read_text(encoding='utf8'))
checks=[]
def check(name,ok,details=None):checks.append(dict(nome=name,ok=bool(ok),detalhes=details))
bpy.ops.wm.open_mainfile(filepath=str(P/report['arquivo']))
porto=bpy.data.scenes['Porto Esperanca']
check('arquivo_separado_do_original',report['arquivo']!='porto_esperanca.blend' and (P/'porto_esperanca.blend').is_file())
check('dez_modelos_aplicados',len(report['modelos'])==10)
check('sem_instalacao_fivem',not report['instalado_fivem'] and not porto['exportacao_fivem'])
check('terreno_preservado',len(bpy.data.collections['01_TERRENO'].objects)==16)
check('reservas_preservadas',sum('id_lote' in o for o in bpy.data.collections['05_RESERVAS_E_IDENTIFICACAO'].objects)==25)
check('amostra_com_dez_modelos',sum(o.name.startswith('AMOSTRA_') for o in bpy.data.scenes['Amostra texturas lote01'].objects)==10)
for model in base['modelos']:
    objects=[o for o in bpy.data.collections['04_VEGETACAO'].objects if o.get('modelo')==model['id']]
    check('implantacao_'+model['id'],len(objects)==base['contagens_vegetacao'][model['id']],len(objects))
    if model['id'] not in [r['id'] for r in report['modelos']]:
        check('modelo_anterior_preservado_'+model['id'],len(bpy.data.objects[model['id']].data.polygons)==model['poligonos'])
positions=json.loads((P/'dados/vegetacao_posicoes.json').read_text(encoding='utf8'))
expected=sorted((p['modelo'],round(p['x'],4),round(p['y'],4),round(p['z'],4),round(p['escala'],4)) for p in positions if p['modelo']!='capim')
actual=sorted((o.get('modelo'),round(o.location.x,4),round(o.location.y,4),round(o.location.z,4),round(o.scale.x,4)) for o in bpy.data.collections['04_VEGETACAO'].objects if o.get('modelo'))
check('posicoes_e_escalas_preservadas',len(actual)==len(expected) and all(a[0]==b[0] and all(abs(x-y)<.001 for x,y in zip(a[1:],b[1:])) for a,b in zip(actual,expected)))
check('grama_preservada',sum(o.name.startswith('CAPIM') for o in bpy.data.collections['04_VEGETACAO'].objects)==base['tufos_grama'])
check('pedras_preservadas',len(bpy.data.collections['06_PEDRAS'].objects)==base['pedras'])
for item in report['modelos']:
    key=item['id'];o=bpy.data.objects[key];me=o.data
    check('malha_com_uv_'+key,'UV_Textura' in me.uv_layers and len(me.polygons)==item['poligonos'])
    check('coordenadas_finitas_'+key,all(math.isfinite(c) for v in me.vertices for c in v.co) and all(math.isfinite(c) for v in me.uv_layers['UV_Textura'].data for c in v.uv))
    for kind,field in [('Casca','tronco'),('Folhagem','folhas')]:
        mat=bpy.data.materials[kind+' imagem | '+key]
        tex=[n for n in mat.node_tree.nodes if n.type=='TEX_IMAGE']
        check('imagem_incorporada_'+kind+'_'+key,len(tex)==1 and tex[0].image.packed_file is not None and Path(bpy.path.abspath(tex[0].image.filepath)).resolve()==(P/item[field]).resolve())
    users=[o for o in bpy.data.collections['04_VEGETACAO'].objects if o.get('modelo')==key]
    check('instancias_compartilham_malha_'+key,all(o.data==me for o in users))
for manifest in [P/'texturas/folhas/lote01/manifesto.json',P/'texturas/troncos/manifesto.json']:
    md=json.loads(manifest.read_text(encoding='utf8'))
    check('originais_intactos_'+manifest.parent.name,all(hashlib.sha256((P/i['arquivo']).read_bytes()).hexdigest()==i['sha256'] for i in md['arquivos']))
for fn in ['catalogo_texturas.png','arvore_sombra_detalhe.png','arvore_sombra_outro_angulo.png','porto_texturas.png']:
    check('previa_'+fn,(P/'previews/texturas_lote01'/fn).is_file())
for item in report['modelos']:
    key=item['id'];bpy.ops.wm.open_mainfile(filepath=str(P/'modelos/texturas_lote01'/(key+'.blend')))
    s=bpy.context.scene;objs=[o for o in s.objects if o.type=='MESH']
    check('projeto_individual_'+key,s.get('modelo')==key and s.camera is not None and len(objs)==1 and len(objs[0].data.polygons)==item['poligonos'])
    imgs={n.image for m in objs[0].data.materials if m and ' imagem | ' in m.name for n in m.node_tree.nodes if n.type=='TEX_IMAGE'} if objs else set()
    check('texturas_individuais_incorporadas_'+key,len(imgs)==2 and all(im.packed_file is not None for im in imgs))
result=dict(revisao=report['revisao'],aprovado=all(c['ok'] for c in checks),verificacoes=checks,validacao_fivem=False,aprovacao_visual_usuario='pendente')
(P/'dados/verificacao_texturas_lote01.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('VERIFICACAO_TEXTURAS_LOTE01',len(checks),'PASSOU' if result['aprovado'] else 'FALHOU',flush=True)
if not result['aprovado']:raise RuntimeError([c for c in checks if not c['ok']])
