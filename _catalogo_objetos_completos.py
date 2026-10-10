import bpy
import json
import html
import zipfile
from pathlib import Path
from mathutils import Vector

BASE = Path(__file__).resolve().parent
OUT = BASE / 'catalogo_objetos_completos'
OUT.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(BASE / 'warehouse_stage7_validado.blend'))
objects = [o for o in bpy.data.collections['ENV_WAREHOUSE_STAGE7'].all_objects if o.type in ('MESH', 'CURVE')]
groups = []
def add(slug, title, predicate, direction=(5,-8,5)):
    selected = [o for o in objects if predicate(o.name)]
    assert selected, slug
    groups.append((slug, title, selected, direction))

add('01_barril', 'Barril completo', lambda n:n.startswith('STORAGE_DRUM_LEFT_') and not any(t in n for t in ('BOX_LID','CONNECTION_BOX')))
add('02_tanque_azul', 'Tanque azul completo', lambda n:n.startswith('TECH_BLUE_TANK_'))
add('03_planta_com_vaso', 'Planta com vaso — placeholder atual', lambda n:n.startswith('PLACEHOLDER_LEFT_00_00_'))
add('04_cabos_superiores', 'Cabos superiores com bandeja', lambda n:n.startswith('SERVICE_LEFT_') and any(t in n for t in ('CABLE_BUNDLE','TRAY_','CABLE_DROP')), (8,-3,5))
add('05_cabos_mangueiras_chao', 'Cabos e mangueiras do chão — conjunto de um lado', lambda n:n.startswith('FLOOR_HOSE_LEFT_'), (7,-4,8))
add('06_piso', 'Piso completo com juntas', lambda n:n.startswith('FLOOR_') and not n.startswith('FLOOR_HOSE_'), (4,-6,10))
add('07_paredes', 'Paredes do galpão com acabamentos', lambda n:n.startswith(('WALL_','TOP_BAND_','BASEBOARD_','CORNER_GUARD_')), (9,-14,16))
add('08_ventilador_parede', 'Ventilador lateral completo', lambda n:n.startswith('SIDE_FAN_LEFT_00_'), (9,-3,3))
add('09_porta', 'Porta completa com batente e maçaneta', lambda n:n.startswith(('DOOR_BACK_','BACK_DOOR_FRAME_')) or n=='THRESHOLD_BACK_DOOR', (3,-9,3))
add('10_mesa', 'Bancada metálica completa', lambda n:n.startswith('TECH_BENCH_') and not n.startswith('TECH_BENCH_CASE_'))
add('11_estante', 'Estante completa', lambda n:n.startswith('TECH_SHELF_') and not n.startswith('TECH_SHELF_CASE_'))
add('12_armario', 'Armário técnico completo', lambda n:n.startswith('TECH_CABINET_'))
add('13_painel_eletrico', 'Painel elétrico completo', lambda n:n.startswith('MAIN_ELECTRICAL_PANEL_'), (3,-9,3))
add('14_recipiente', 'Recipiente fechado completo', lambda n:n.startswith('TECH_BENCH_CASE_A_'))
add('15_balde', 'Balde completo com alça e tampa', lambda n:n.startswith('TECH_BUCKET_'))
add('16_rack', 'Rack completo de três módulos', lambda n:n.startswith('RACK_LEFT_'), (8,-10,7))
add('17_luminaria', 'Luminária LED completa', lambda n:n.startswith('LIGHT_FIXTURE_00_00_'), (4,-6,-5))
add('18_duto_teto', 'Duto do teto com três ventilações e suportes', lambda n:n.startswith(('CEILING_DUCT_','CEILING_VENT_')), (8,-7,-7))
add('19_duto_fundo', 'Tubulação grande do fundo', lambda n:n.startswith('DUCT_'))
add('20_exaustor_fundo', 'Exaustor traseiro completo', lambda n:n.startswith('EXHAUST_FAN_LEFT_'), (3,-9,3))
add('21_tubulacoes_parede', 'Tubulações e caixas da parede — conjunto de um lado', lambda n:n.startswith('SERVICE_LEFT_') and not any(t in n for t in ('CABLE_','TRAY_')), (8,-4,5))
add('22_canaleta', 'Canaleta central com grelhas', lambda n:n.startswith('DRAIN_'), (7,-3,9))
add('23_teto', 'Laje do teto', lambda n:n=='CEILING_SLAB', (5,-8,10))
add('24_caixa_conexao', 'Caixa de conexão das mangueiras', lambda n:n in ('STORAGE_DRUM_LEFT_CONNECTION_BOX','STORAGE_DRUM_LEFT_BOX_LID'))

scene = bpy.data.scenes.new('CATALOGO_MONTADO_TEMP')
scene.render.engine = 'BLENDER_WORKBENCH'
scene.render.resolution_x = scene.render.resolution_y = 1200
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.use_compositing = False
shade = scene.display.shading
shade.light = 'STUDIO'
shade.color_type = 'MATERIAL'
shade.background_type = 'VIEWPORT'
shade.background_color = (0.25,0.25,0.25)
shade.show_shadows = True
shade.show_cavity = True
shade.cavity_type = 'BOTH'
scene.display.render_aa = '32'
scene.view_settings.view_transform = 'Standard'
cam_data = bpy.data.cameras.new('CATALOGO_MONTADO_CAMERA')
cam = bpy.data.objects.new('CATALOGO_MONTADO_CAMERA',cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
cam_data.type = 'ORTHO'
cam_data.clip_start = 0.001
cam_data.clip_end = 1000
depsgraph = bpy.context.evaluated_depsgraph_get()
manifest = []
for slug, title, selected, direction in groups:
    copies, points = [], []
    for obj in selected:
        mesh = bpy.data.meshes.new_from_object(obj.evaluated_get(depsgraph), depsgraph=depsgraph)
        duplicate = bpy.data.objects.new(obj.name+'_CATALOG',mesh)
        duplicate.matrix_world = obj.matrix_world.copy()
        scene.collection.objects.link(duplicate)
        copies.append(duplicate)
        points.extend(obj.matrix_world @ v.co for v in mesh.vertices)
    low = Vector(tuple(min(p[i] for p in points) for i in range(3)))
    high = Vector(tuple(max(p[i] for p in points) for i in range(3)))
    center = (low + high) / 2
    normal = Vector(direction).normalized()
    cam.rotation_euler = (-normal).to_track_quat('-Z','Y').to_euler()
    rotation = cam.rotation_euler.to_matrix()
    projected = [rotation.transposed() @ (p-center) for p in points]
    xmin,xmax = min(p.x for p in projected),max(p.x for p in projected)
    ymin,ymax = min(p.y for p in projected),max(p.y for p in projected)
    cam.location = center + normal * max(10, (high-low).length * 2) + rotation @ Vector(((xmin+xmax)/2,(ymin+ymax)/2,0))
    cam_data.ortho_scale = max(xmax-xmin,ymax-ymin) * 1.16
    scene.render.filepath = str(OUT / (slug+'.png'))
    bpy.ops.render.render(write_still=True, scene=scene.name)
    manifest.append({'id':slug,'title':title,'image':slug+'.png','blender_objects':[o.name for o in selected]})
    for obj in copies:
        mesh=obj.data
        bpy.data.objects.remove(obj,do_unlink=True)
        bpy.data.meshes.remove(mesh)
(OUT/'mapeamento_objetos.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
cards=[]
for row in manifest:
    cards.append(f'<article><a href="{row["image"]}" target="_blank"><img src="{row["image"]}" loading="lazy" alt="{html.escape(row["title"])}"></a><h2>{html.escape(row["title"])}</h2><a href="{row["image"]}" download>Salvar imagem</a></article>')
page='''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Objetos completos — Stage 7</title><style>body{background:#171d23;color:#e9edf2;font:16px system-ui;margin:30px}h1{font-size:30px}p{line-height:1.6;max-width:1000px;color:#bdcbd7}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:24px}article{padding:15px;background:#26313c;border-radius:12px}img{width:100%;border-radius:6px}h2{font-size:17px}a{color:#b3ddff}</style><h1>24 objetos e conjuntos completos</h1><p>Uma imagem por tipo de objeto do cenário, mantendo todas as suas peças montadas. As repetições iguais dos dois lados foram representadas por um exemplar. Cabos e tubulações estão agrupados por função. Os nomes dos PNGs identificam os conjuntos para a aplicação das texturas depois.</p><div class="grid">'''+''.join(cards)+'</div></html>'
(OUT/'index.html').write_text(page,encoding='utf-8')
(OUT/'LEIA_ME.txt').write_text('CATÁLOGO POR OBJETOS COMPLETOS\n24 imagens de 1200 x 1200 px. Abra index.html.\nCada foto reúne o objeto completo, não suas peças internas. Um exemplar representa as repetições iguais.\nAs plantas são os placeholders atuais com seus vasos. As LEDs aparecem sem luz rosa de ambiente para facilitar a referência dos materiais.\nDevolva as texturas usando o nome da imagem como prefixo. Exemplo: 01_barril_basecolor.png.\nO mapeamento_objetos.json guarda a relação entre cada conjunto e suas peças no Blender.\nEstas fotos são referências; para texturas, peça imagens planas de superfície, sem sombras ou perspectiva.\n',encoding='utf-8')
archive=Path(r'C:\Users\erons\Downloads\catalogo_objetos_completos_stage7.zip')
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for p in OUT.iterdir():
        if p.is_file():z.write(p,'catalogo_objetos_completos/'+p.name)
print('CATALOG COMPLETE:',len(manifest),'groups;',round(archive.stat().st_size/1048576,1),'MB',flush=True)
