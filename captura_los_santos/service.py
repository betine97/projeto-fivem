"""Private local bridge: durable selections, native asset resolution and live catalogue."""
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import base64,hmac,json,math,os,queue,re,subprocess,threading,time,socket,sys,tempfile,shutil
ROOT=Path(__file__).resolve().parent.parent;HOME=ROOT/'captura_los_santos'
CAPTURE_PORT=int(os.environ.get('CAPTURE_PORT','8788'))
CATEGORIES={'Objetos de Los Santos','Árvores e palmeiras','Arbustos, grama e plantas','Pedras e rochas','Água e infraestrutura','Cercas e barreiras','Construções','Estradas e iluminação','Objetos e decoração'}
def atomic(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w',encoding='utf8',dir=path.parent,prefix=path.stem+'-',suffix='.tmp',delete=False)as stream:
        json.dump(data,stream,ensure_ascii=False,indent=2);temp=Path(stream.name)
    try:
        for attempt in range(60):
            try:os.replace(temp,path);return
            except PermissionError:
                if attempt==59:raise
                # Windows readers/OneDrive can briefly deny replacing an open file.
                time.sleep(.1)
    finally:
        if temp.exists():temp.unlink()
def vector(v,limit=20000):
    if not isinstance(v,dict) or any(type(v.get(k)) not in (int,float) or not math.isfinite(v[k]) or abs(v[k])>limit for k in ('x','y','z')):raise ValueError('Coordenadas inválidas.')
    return {k:v[k] for k in ('x','y','z')}
def category(name):
    if any(x in name for x in ('tree','palm','palmeto')):return 'Árvores e palmeiras'
    if any(x in name for x in ('grass','fern','weed','bush','plant')):return 'Arbustos, grama e plantas'
    if any(x in name for x in ('rock','stone','boulder')):return 'Pedras e rochas'
    if any(x in name for x in ('tank','water','pipe','pump')):return 'Água e infraestrutura'
    if any(x in name for x in ('fence','gate','barrier','wall')):return 'Cercas e barreiras'
    if any(x in name for x in ('house','hut','shed','building')):return 'Construções'
    if any(x in name for x in ('lamp','light','sign','road')):return 'Estradas e iluminação'
    return 'Objetos de Los Santos'
def label(name):
    words={'bench':'Banco','bin':'Lixeira','dumpster':'Caçamba','tree':'Árvore','palm':'Palmeira','bush':'Arbusto','plant':'Planta','rock':'Rocha','barrel':'Barril','chair':'Cadeira','table':'Mesa','lamp':'Luminária','light':'Luz','fence':'Cerca','gate':'Portão','wall':'Parede','sign':'Placa','tank':'Tanque','water':'Água','house':'Casa','hut':'Cabana','shed':'Galpão','road':'Estrada','box':'Caixa','crate':'Caixote','grass':'Grama','fern':'Samambaia','cone':'Cone','bollard':'Balizador','busstop':'Ponto de ônibus','firehydrant':'Hidrante','streetlight':'Poste de luz'}
    tokens=name.split('_');known=[words[t] for t in tokens if t in words]
    return (' / '.join(known) if known else 'Objeto de Los Santos')+' · '+name
class CaptureStore:
    def __init__(self,root=ROOT,index=None,render=True):
        self.root=Path(root);self.home=self.root/'captura_los_santos';self.lock=threading.RLock();self.jobs=queue.PriorityQueue();self.render=render
        self.index=index or json.loads((self.home/'data/model_index.json').read_text(encoding='utf8'))
        self.path=self.home/'data/capturas.json';self.catalogPath=self.root/'server-data/resources/cidade_admin/data/catalogo_capturado.json'
        self.state=json.loads(self.path.read_text(encoding='utf8')) if self.path.exists() else {'revision':0,'nextId':1,'captures':[]}
        self.catalog=json.loads(self.catalogPath.read_text(encoding='utf8')) if self.catalogPath.exists() else {'revision':0,'objects':[]}
        for item in self.catalog['objects']:
            item['captured']=True
            original=next((r for r in self.state['captures'] if r.get('model')==item['model']),{})
            rotation=original.get('rotation') or {}
            item['defaultPitch']=rotation.get('x',0);item['defaultRoll']=rotation.get('y',0)
        self.publish()
        if not self.catalogPath.exists():atomic(self.catalogPath,self.catalog)
        if render:
            self.workerThread=threading.Thread(target=self.worker,daemon=True);self.workerThread.start()
            for row in self.state['captures']:
                if row['status']=='preparando imagem' or row['status']=='imagem pendente' and row.get('retryCount',0)<3 or row['status']=='aguardando análise' and not row.get('analysisAttempted') and (self.home/'data/world_index.sqlite3').exists():self.jobs.put((0 if row['kind']=='object' else 10,row['id']))
    def publish(self):
        self.catalog['marks']=[{k:r.get(k) for k in ('id','name','model','status')} for r in self.state['captures'] if r['status']!='disponível no catálogo']
        self.catalog['revision']=max(self.catalog['revision']+1,self.state['revision'])
        self.catalog['type']='capturedCatalog'
        atomic(self.catalogPath,self.catalog)
        # Gameplay only needs small model metadata. The browser reads images
        # directly from the full JSON, avoiding expensive Lua image decoding.
        index={**self.catalog,'objects':[{k:v for k,v in row.items() if k!='image'} for row in self.catalog['objects']]}
        atomic(self.catalogPath.with_name('catalogo_capturado_indice.json'),index)
    def resolve(self,body):
        position=vector(body.get('position'));kind=body.get('kind')
        if kind=='surface':return {'kind':'surface','name':'Trecho do mapa original','category':'Objetos de Los Santos','position':position,'details':'Este trecho não expôs um objeto separado. A marcação será guardada para localizar a peça do mapa; não será inserida como objeto quebrado.'}
        modelHash=body.get('hash')
        if type(modelHash)is not int or not 0<modelHash<=4294967295:raise ValueError('Identificação de modelo inválida.')
        meta=self.index['models'].get(str(modelHash))
        if not meta:
            return {'kind':'surface','hash':modelHash,'name':'Modelo a identificar','category':'Objetos de Los Santos','position':position,'details':'O modelo ainda não está no índice local. Salve a marcação para localizar seus arquivos antes de incluí-lo no catálogo.'}
        name=meta['model']
        if not re.fullmatch('[a-zA-Z0-9_]{1,64}',name):raise ValueError('Nome de modelo inválido.')
        lo=meta.get('bbMin') or [vector(body.get('bbMin'),1000)[k] for k in ('x','y','z')]
        hi=meta.get('bbMax') or [vector(body.get('bbMax'),1000)[k] for k in ('x','y','z')]
        if any(not math.isfinite(x) for x in lo+hi) or any(hi[i]<lo[i] for i in range(3)):raise ValueError('Dimensões inválidas.')
        grouped=meta.get('mlo') or any(hi[i]-lo[i]>180 for i in range(3)) or re.search(r'(^hash_|_lod|_slod|_occl|_shadow)',name)
        return {'kind':'surface' if grouped else 'object','hash':modelHash,'model':name,'name':label(name)[:80],'category':category(name),'bbMin':lo,'bbMax':hi,'position':position,'details':('Peça agrupada ou interior: a marcação será guardada para análise antes de reutilizar.' if grouped else 'Modelo original identificado. Você pode mudar o nome; a imagem será preparada e o item ficará disponível no editor da ilha.'),'source':meta}
    def capture(self,body):
        resolved=self.resolve(body);name=body.get('name')
        rotation=vector(body['rotation'],360) if body.get('rotation') is not None else None
        if not isinstance(name,str) or not 1<=len(name.strip())<=80 or any(not c.isprintable() for c in name):raise ValueError('Use um nome de 1 a 80 caracteres.')
        cat=body.get('category')
        if cat not in CATEGORIES:raise ValueError('Categoria inválida.')
        author=body.get('author')
        if not isinstance(author,dict) or type(author.get('id'))is not int or author['id']<1:raise ValueError('ADM ausente.')
        with self.lock:
            if len(self.state['captures'])>=3000:raise ValueError('Limite de 3.000 marcações atingido.')
            row={**resolved,'id':self.state['nextId'],'name':name.strip(),'category':cat,'author':author,'createdAt':time.time(),'rotation':rotation,'origin':body.get('origin','Los Santos'),'status':'aguardando análise' if resolved['kind']=='surface' else 'preparando imagem'}
            duplicate=next((o for o in self.catalog['objects'] if o['model']==resolved.get('model')),None)
            if duplicate:row['status']='disponível no catálogo'
            self.state['captures'].append(row);self.state['nextId']+=1;self.state['revision']+=1;atomic(self.path,self.state)
            self.publish()
            if row['status']=='preparando imagem' or row['status']=='aguardando análise' and (self.home/'data/world_index.sqlite3').exists():self.jobs.put((0 if row['kind']=='object' else 10,row['id']))
            message='Trecho salvo. Vou identificar a geometria original e mostrar o resultado em Meus itens capturados.' if resolved['kind']=='surface' else ('Esse modelo já está em Meus itens capturados no editorilha.' if duplicate else 'Objeto marcado. A imagem aparecerá em Meus itens capturados no editorilha.')
            print('CAPTURA_SALVA',row['id'],row.get('model','superfície'),flush=True)
            return {'ok':True,'message':message,'id':row['id']}
    def list(self):
        with self.lock:
            rows=[{k:r.get(k) for k in ('id','name','model','status')} for r in self.state['captures'][-50:]]
            return {'ok':True,'message':f"{len(self.state['captures'])} marcações salvas; {len(self.catalog['objects'])} modelos disponíveis no catálogo da ilha.",'rows':rows}
    def worker(self):
        import sys
        sys.path[:0]=[str(ROOT/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
        from PIL import Image
        while True:
            _,ident=self.jobs.get()
            try:
                with self.lock:row=next(r.copy() for r in self.state['captures'] if r['id']==ident)
                if row['kind']=='surface':
                    if row.get('model') or row.get('hash'):continue
                    folder=self.home/'cache'/('marcacao-'+str(ident));folder.mkdir(parents=True,exist_ok=True)
                    hit=folder/'hit.json';atomic(hit,{'position':row['position'],'origin':row.get('origin','Los Santos')})
                    env=os.environ.copy();env['PYTHONPATH']=os.pathsep.join(sys.path[:2])
                    with (folder/'locate.log').open('wb')as log:
                        proc=subprocess.run([sys.executable,str(self.home/'locate_surface.py'),str(hit)],stdout=log,stderr=subprocess.STDOUT,timeout=240,env=env,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                    answer=json.loads(hit.with_suffix('.resolved.json').read_text(encoding='utf8')) if proc.returncode==0 and hit.with_suffix('.resolved.json').exists() else {}
                    with self.lock:
                        current=next(r for r in self.state['captures'] if r['id']==ident);current['analysisAttempted']=True
                        if not answer.get('found'):
                            current['status']='aguardando análise';current.pop('error',None)
                            current['details']='Sem peça HD independente confirmada neste ponto. A marcação foi preservada para análise.'
                            atomic(self.path,self.state);self.publish();continue
                        meta=self.index['models'][str(answer['best']['hash'])]
                        current.update(kind='object',model=meta['model'],hash=answer['best']['hash'],bbMin=meta['bbMin'],bbMax=meta['bbMax'],source=meta,status='preparando imagem',resolvedMap=answer['best']['map'])
                        if current['name'] in ('Trecho do mapa original','Modelo a identificar'):current['name']=label(meta['model'])[:80]
                        if current['category']=='Objetos de Los Santos':current['category']=category(meta['model'])
                        row=current.copy();atomic(self.path,self.state);self.publish()
                    print('TRECHO_IDENTIFICADO',ident,row['model'],flush=True)
                folder=self.home/'cache'/row['model'];folder.mkdir(parents=True,exist_ok=True);atomic(folder/'source.json',row['source'])
                # Native binary readers run separately so a malformed asset cannot stop capture.
                environment=os.environ.copy();environment['PYTHONPATH']=os.pathsep.join([str(ROOT/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps'])
                if not (folder/'model.json').exists():
                    with (folder/'extraction.log').open('wb')as log:
                        run=subprocess.run([sys.executable,str(self.home/'assets.py'),str(folder)],stdout=log,stderr=subprocess.STDOUT,timeout=120,env=environment,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                    if run.returncode!=0 or not (folder/'model.json').exists():raise ValueError('Falha ao ler a peça nativa; veja extraction.log.')
                blender=Path(os.environ.get('BLENDER_BIN') or shutil.which('blender') or r'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe')
                if not (folder/'preview.png').exists():
                    with (folder/'render.log').open('wb') as log:
                        run=subprocess.run([str(blender),'-b','--python',str(self.home/'render_model.py'),'--',str(folder)],stdout=log,stderr=subprocess.STDOUT,timeout=180,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                    if run.returncode!=0 or not (folder/'preview.png').exists():raise ValueError('Falha ao renderizar a imagem; veja render.log.')
                import io
                image=Image.open(folder/'preview.png');image.thumbnail((192,192));buffer=io.BytesIO();image.save(buffer,format='WEBP',quality=82,method=6)
                encoded='data:image/webp;base64,'+base64.b64encode(buffer.getvalue()).decode()
                with self.lock:
                    current=next(r for r in self.state['captures'] if r['id']==ident)
                    if not any(o['model']==row['model'] for o in self.catalog['objects']):
                        if len(self.catalog['objects'])>=300:raise ValueError('Limite de 300 modelos capturados no catálogo atingido.')
                        self.catalog['objects'].append({k:row[k] for k in ('model','hash','name','category','bbMin','bbMax') }|{'image':encoded,'drawDistance':3000 if row['category']=='Árvores e palmeiras' else 1800,'origin':row.get('origin','Los Santos'),'captured':True})
                        self.catalog['objects'][-1].update(defaultPitch=(row.get('rotation') or {}).get('x',0),defaultRoll=(row.get('rotation') or {}).get('y',0))
                    current['status']='disponível no catálogo';self.state['revision']+=1;atomic(self.path,self.state)
                    self.publish()
                print('CATALOGO_ATUALIZADO',row['model'],flush=True)
            except Exception as e:
                with self.lock:
                    current=next(r for r in self.state['captures'] if r['id']==ident);current['status']='imagem pendente';current['error']=str(e);current['retryCount']=current.get('retryCount',0)+1
                    try:atomic(self.path,self.state);self.publish()
                    except OSError as error:print('GRAVACAO_PENDENTE',str(error),flush=True)
                print('CAPTURA_PENDENTE',ident,str(e),flush=True)
            finally:self.jobs.task_done()
def handler(store,key):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def send(self,status,data):
            raw=json.dumps(data,ensure_ascii=False).encode();self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(raw)
        def do_GET(self):
            if self.path=='/health':self.send(200,{'app':'captura_los_santos','ok':store.workerThread.is_alive(),'revision':'captura-20261010-2','pid':os.getpid(),'queue':store.jobs.qsize()});return
            self.send(404,{'ok':False})
        def do_POST(self):
            if self.headers.get('Host')not in (f'127.0.0.1:{CAPTURE_PORT}',f'localhost:{CAPTURE_PORT}') or not hmac.compare_digest(self.headers.get('X-Cidade-Key',''),key):self.send(401,{'ok':False,'message':'Não autorizado.'});return
            try:
                size=int(self.headers.get('Content-Length','0'))
                if not 0<size<=12000:raise ValueError('Requisição inválida.')
                body=json.loads(self.rfile.read(size))
                if not isinstance(body,dict):raise ValueError('Pedido inválido.')
                if self.path=='/resolve':result={'ok':True,'data':store.resolve(body)}
                elif self.path=='/capture':result=store.capture(body)
                elif self.path=='/list':result=store.list()
                else:self.send(404,{'ok':False});return
                self.send(200,result)
            except (ValueError,TypeError,KeyError)as e:self.send(200,{'ok':False,'message':str(e)})
            except OSError:self.send(503,{'ok':False,'message':'Não foi possível gravar a marcação.'})
    return Handler
def main():
    settings=json.loads((ROOT/'painel_acesso/data/config.json').read_text(encoding='utf8'))
    # Reserve the port exclusively BEFORE opening the data or starting workers.
    server=ThreadingHTTPServer(('127.0.0.1',CAPTURE_PORT),BaseHTTPRequestHandler,bind_and_activate=False)
    server.allow_reuse_address=False
    if hasattr(socket,'SO_EXCLUSIVEADDRUSE'):server.socket.setsockopt(socket.SOL_SOCKET,socket.SO_EXCLUSIVEADDRUSE,1)
    server.server_bind();server.server_activate()
    store=CaptureStore();server.RequestHandlerClass=handler(store,settings['api_key'])
    print(f'CAPTURA_PRONTA http://127.0.0.1:{CAPTURE_PORT}',flush=True);server.serve_forever()
if __name__=='__main__':main()
