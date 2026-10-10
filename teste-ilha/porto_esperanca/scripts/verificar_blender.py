"""Conferencia do artefato salvo, incluindo a abertura dos 24 arquivos individuais."""
import bpy,json,math
from pathlib import Path
P=Path(__file__).resolve().parents[1]
info=json.loads((P/'dados/implantacao.json').read_text(encoding='utf8'))
checks=[]
def check(name,ok,details=None):checks.append(dict(nome=name,ok=bool(ok),detalhes=details))
bpy.ops.wm.open_mainfile(filepath=str(P/'porto_esperanca.blend'))
check('cena_principal', 'Porto Esperanca' in bpy.data.scenes)
check('catalogos', all(s in bpy.data.scenes for s in ['Catalogo 01','Catalogo 02']))
check('terreno_16_setores', len(bpy.data.collections['01_TERRENO'].objects)==16)
check('reservas_25', sum('id_lote' in o for o in bpy.data.collections['05_RESERVAS_E_IDENTIFICACAO'].objects)==25)
check('sem_edificios', info['edificios_gerados']==0)
check('agua_apenas_visual', info['agua_apenas_visual'])
check('fora_do_servidor', not info['instalado_fivem'])
check('colisao_referencia_separada', len(bpy.data.collections['07_COLISAO_REFERENCIA'].objects)==16)
check('24_modelos',len(info['modelos'])==24)
for model in info['modelos']:
    objects=[o for o in bpy.data.collections['04_VEGETACAO'].objects if o.get('modelo')==model['id']]
    check('disposto_'+model['id'],len(objects)>0,len(objects))
check('malhas_finitas', all(all(math.isfinite(c) for c in v.co) for me in bpy.data.meshes for v in me.vertices))
check('exclusao_areas',info['exclusoes_validas'] and not info['violacoes'])
check('vegetacao_registrada',len(json.loads((P/'dados/vegetacao_posicoes.json').read_text(encoding='utf8')))==sum(info['contagens_vegetacao'].values())+info['tufos_grama'])
check('pedras_registradas',len(json.loads((P/'dados/pedras_posicoes.json').read_text()))==info['pedras'])
for filename in ['porto_vegetacao.png','praca_reservada.png','foz_vegetacao.png','implantacao_areas.png','catalogo_01.png','catalogo_02.png']:
    check('previa_'+filename,(P/'previews'/filename).exists())
for model in info['modelos']:
    bpy.ops.wm.open_mainfile(filepath=str(P/model['arquivo']))
    scenes=[s for s in bpy.data.scenes if s.get('modelo')==model['id']]
    ok=len(scenes)==1 and scenes[0].camera is not None
    objs=[o for o in scenes[0].objects if o.type=='MESH'] if scenes else []
    check('arquivo_individual_'+model['id'],ok and len(objs)==1 and len(objs[0].data.polygons)==model['poligonos'])
result=dict(revisao=info['revisao'],verificacoes=checks,aprovado=all(c['ok'] for c in checks),verificado_fivem=False)
(P/'dados/verificacao_blender.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print('VERIFICACAO_BLENDER',len(checks),'PASSOU' if result['aprovado'] else 'FALHOU',flush=True)
if not result['aprovado']:raise RuntimeError([c for c in checks if not c['ok']])
