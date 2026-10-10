"""Build the offline NUI catalogue from official Cfx.re model references.
Only writes cidade_admin/ui and this feature's own backup/build output.
"""
from pathlib import Path
import concurrent.futures, html, json, re, shutil, urllib.request, time

ROOT = Path(__file__).resolve().parent.parent
RESOURCE = ROOT / 'server-data/resources/cidade_admin'
WORK = ROOT / 'painel_adm_20261009'
UI = RESOURCE / 'ui'
RAW = 'https://raw.githubusercontent.com/citizenfx/fivem-docs/master/'
HOST = 'https://docs-backend.fivem.net'

def fetch(url):
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=25) as response:
                return response.read()
        except Exception:
            if attempt == 2: raise
            time.sleep(.3 * (attempt + 1))

def build():
    backup = WORK / 'backup/cidade_admin'
    if not backup.exists():
        shutil.copytree(RESOURCE, backup)
    UI.mkdir(parents=True, exist_ok=True)
    categories = {
        'compacts':'Compactos','sedans':'Sedãs','suvs':'SUVs','coupes':'Cupês',
        'muscle':'Muscle','sports-classic':'Clássicos','sports-classics':'Clássicos',
        'sports':'Esportivos','super':'Superesportivos','motorcycles':'Motos',
        'off-road':'Off-road','industrial':'Industrial','utility':'Utilitários',
        'vans':'Vans','cycles':'Bicicletas','boats':'Barcos','helicopters':'Helicópteros',
        'planes':'Aviões','service':'Serviço','emergency':'Emergência','military':'Militares',
        'commercial':'Carga','trains':'Trens','open-wheel':'Fórmula',
        'handguns':'Pistolas','smg':'Submetralhadoras','shotguns':'Escopetas',
        'assault-rifles':'Fuzis','machine-guns':'Metralhadoras','sniper-rifles':'Precisão',
        'heavy':'Pesadas','throwables':'Arremessáveis','melee':'Corpo a corpo','misc':'Outras',
        'Ambient female':'Civis • mulheres','Ambient male':'Civis • homens',
        'Animals':'Animais','Cutscene':'Personagens • cenas','Gang female':'Gangues • mulheres',
        'Gang male':'Gangues • homens','Multiplayer':'Multiplayer','Scenario female':'Profissões • mulheres',
        'Scenario male':'Profissões • homens','Story':'Personagens da história',
    }
    data = {'vehicles':[], 'weapons':[], 'npcs':[]}
    sources = {}
    for kind, path in [('vehicles','vehicle-references/vehicle-models'),('weapons','weapon-models'),('npcs','ped-models')]:
        url = RAW + 'content/docs/game-references/' + path + '.md'
        text = fetch(url).decode()
        sources[kind] = url
        tag = 'model' if kind == 'npcs' else kind[:-1]
        sections = re.split(r'(<div class="category" id="[^"]+">|^## [^\n]+)', text, flags=re.M)
        category = 'Outros'
        seen = set()
        for section in sections:
            if section.startswith('<div class="category"'):
                category = re.search(r'id="([^"]+)"', section)[1]
            elif section.startswith('## '): category = section[3:].strip()
            for match in re.finditer(r'<div class="'+tag+r'">.*?<img src="([^"]+)"[^>]*alt="([^"]+)"', section, re.S):
                src, label = match.groups()
                model = Path(src).stem.lower()
                if model in seen: continue
                seen.add(model)
                data[kind].append({'model':model,'name':html.unescape(label),'category':categories.get(category,category.replace('-',' ').title()),'image':src.lstrip('/')})
    # Friendly labels/aliases already used by this city.
    old = (RESOURCE / 'catalogo.lua').read_text(encoding='utf-8-sig')
    aliases = {('weapon_'+m.lower()):(alias,label) for alias,m,label in re.findall(r"\{'([^']+)','([^']+)','([^']+)'\}",old)}
    for item in data['weapons']:
        if item['model'] in aliases:
            item['alias'],item['name'] = aliases[item['model']]
    for kind,model,label,original in [
        ('vehicles','sertao','Sertão','veiculos/sertao_previa.png'),
        ('vehicles','jeepmilitar','Jeep militar','veiculos/jeepmilitar_previa.png'),
        ('npcs','cartelking','Cartel King','personagens/cartelking_preview.png'),
    ]:
        folder = UI / ('peds' if kind=='npcs' else kind)
        folder.mkdir(exist_ok=True)
        target = folder / (model+'.png')
        shutil.copyfile(ROOT / original, target)
        data[kind].insert(0,{'model':model,'name':label,'category':'Personalizados da cidade','image':str(target.relative_to(UI)).replace('\\','/')})

    # Commands from installed city resources. Runtime enumeration supplements this
    # snapshot (including commands dynamically registered by aliases/loops).
    commands = {}
    for file in (ROOT/'server-data/resources').rglob('*.lua'):
        resource = file.relative_to(ROOT/'server-data/resources').parts[0]
        if not (resource.startswith('cidade_') or resource in ['teste_ilha','fpv_drone_runtime']): continue
        text = file.read_text(encoding='utf-8-sig')
        for name in re.findall(r"RegisterCommand\(\s*['\"]([^'\"]+)['\"]\s*[,)]",text):
            if name.startswith(('+','-')): continue
            commands.setdefault(name,{'name':name,'resource':resource,'usage':name,'description':'Comando do recurso '+resource+'.','category':'Outros'})
    for name,resource in [('encontrar','cidade_acesso'),('chamar','cidade_acesso'),('onde','cidade_admin'),('localizar','cidade_admin'),('rastrear','cidade_admin')]:
        commands[name]={'name':name,'resource':resource,'usage':name+' ID','description':'','category':'Jogadores e IDs'}
    for usage,desc in re.findall(r"\{'([^']+)', '([^']+)'\}",old.split('armas =')[0]):
        for part in usage.split(' | '):
            name=part.split()[0]
            if name in commands: commands[name].update(usage=part,description=desc)
    details = {
        'painel':('painel adm','Abre este painel de administração.','Painel'),
        'paineladm':('paineladm','Atalho para abrir este painel.','Painel'),
        'npc':('npc MODELO','Cria um NPC específico perto de você. Exemplo: npc s_m_y_cop_01.','NPCs'),
        'npcs':('npcs','Abre o catálogo de NPCs do painel.','NPCs'),
        'jogadores':('jogadores','Lista os jogadores online com os IDs permanentes.','Jogadores e IDs'),
        'id':('id','Mostra seu ID permanente.','Jogadores e IDs'),
        'onde':('onde ID','Localiza e marca o jogador no mapa; mostra coordenadas e distância no F8.','Jogadores e IDs'),
        'localizar':('localizar ID','Localiza e marca no mapa o jogador com esse ID permanente.','Jogadores e IDs'),
        'rastrear':('rastrear ID','Atualiza a posição do jogador no mapa a cada 2 segundos.','Jogadores e IDs'),
        'pararrastreio':('pararrastreio','Encerra o rastreamento e limpa o marcador.','Jogadores e IDs'),
        'encontrar':('encontrar ID','Teletransporta você até o jogador.','Jogadores e IDs'),
        'chamar':('chamar ID','Traz o jogador para perto de você.','Jogadores e IDs'),
        'editarobjetos':('editarobjetos','Ativa o editor de objetos da mansão; CAPS pega/salva, setas giram, Page Up/Down mudam a altura, HOME restaura a origem e Backspace cancela.','Objetos e mapas'),
        'moverobjetos':('moverobjetos','Atalho para editarobjetos. O editor atual atua nos objetos definidos pela mansão.','Objetos e mapas'),
        'objetosajuda':('objetosajuda','Exibe os controles de movimentação e salvamento de objetos no F8.','Objetos e mapas'),
        'restaurarobjeto':('restaurarobjeto','Restaura o objeto selecionado no editor da mansão para a posição original.','Objetos e mapas'),
        'hora':('hora HORA [MINUTO]','Define a hora local. Exemplo: hora 14 30.','Ambiente'),
        'clima':('clima TIPO','Define o clima local: CLEAR, EXTRASUNNY, CLOUDS, OVERCAST, RAIN, THUNDER, FOGGY, SMOG, XMAS ou SNOWLIGHT.','Ambiente'),
        'tempo':('tempo TIPO','Atalho para clima TIPO.','Ambiente'),
        'dronesom':('dronesom VOLUME','Ajusta o volume do drone de 0 a 100. Exemplo: dronesom 80.','Drone'),
        'dronerpm':('dronerpm MOTOR RPM','Testa o motor FL, FR, RL ou RR. Exemplo: dronerpm FL 3000.','Drone'),
    }
    for name,(usage,desc,category) in details.items():
        if name not in commands: commands[name]={'name':name,'resource':'cidade_admin'}
        commands[name].update(usage=usage,description=desc,category=category)
    for item in commands.values():
        if item['category']!='Outros':continue
        n=item['name'];res=item['resource']
        item['category']=('Drone' if res=='fpv_drone_runtime' else 'Objetos e mapas' if res in ['teste_ilha','cidade_mansao','cidade_laboratorio','cidade_hospital_carcer','cidade_castelo_previa'] else 'Roupas e personagem' if any(x in n for x in ['roupa','camisa','calca','jeans','person','traje','macacao','cartel','guardavermelho','crachadea']) else 'Veículos' if n in ['veiculo','car','carro','dv','sertao','jeepmilitar','veiculos','sertaoinfo','sertaoteste'] else 'Armas' if n in ['arma','armas','desarmar'] else 'Ambiente' if n in ['dia','tarde','noite','tempolivre'] else 'Movimento e combate')
    data['commands']=sorted(commands.values(),key=lambda x:x['name'])
    (UI/'catalog.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    jobs = [item for kind in ['vehicles','weapons','npcs'] for item in data[kind] if not item['image'].endswith('.png') or kind=='weapons']
    def download(item):
        target=UI/item['image'];target.parent.mkdir(exist_ok=True)
        if target.exists() and target.stat().st_size: return None
        try: target.write_bytes(fetch(HOST+'/'+item['image']))
        except Exception as e:return {'model':item['model'],'error':str(e)}
    failures=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        for index,result in enumerate(pool.map(download,jobs),1):
            if result:failures.append(result)
            if index%150==0:print('THUMBNAILS',index,'/',len(jobs),flush=True)
    (WORK/'catalog-build.json').write_text(json.dumps({'counts':{k:len(v) for k,v in data.items()},'sources':sources,'failed_images':failures},ensure_ascii=False,indent=2),encoding='utf-8')
    (UI/'SOURCES.md').write_text('Model thumbnails: official Cfx.re/FiveM references. Downloaded for offline use.\n\n'+'\n'.join(sources.values())+'\n\nCustom vehicle/Cartel King previews: existing assets of this city.\n',encoding='utf-8')
    print('CATALOG_BUILT',json.dumps({k:len(v) for k,v in data.items()}),'FAILED_IMAGES',len(failures),flush=True)

if __name__=='__main__':build()
