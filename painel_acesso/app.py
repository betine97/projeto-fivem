"""Local administration panel and private FiveM admission bridge; no dependencies."""
import argparse, base64, hashlib, hmac, json, os, re, secrets, sqlite3, threading, time, urllib.parse, urllib.request, webbrowser
from http.cookies import SimpleCookie
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATUSES = {'pending', 'approved', 'blocked'}

class Store:
    def __init__(self, directory=ROOT / 'data'):
        self.directory = Path(directory); self.directory.mkdir(parents=True, exist_ok=True)
        self.path = self.directory / 'usuarios.sqlite3'
        with self.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    identifier TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','approved','blocked')),
                    created_at REAL NOT NULL, last_seen REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS sessions (identifier TEXT PRIMARY KEY, seen_at REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS server_sessions (identifier TEXT NOT NULL, server TEXT NOT NULL, seen_at REAL NOT NULL, PRIMARY KEY(identifier,server));
            ''')
    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10); db.row_factory = sqlite3.Row
        try:
            db.execute('PRAGMA journal_mode=WAL')
            with db: yield db
        finally: db.close()
    @staticmethod
    def identity(identifiers):
        if not isinstance(identifiers, list): raise ValueError('Identificação FiveM ausente.')
        for prefix in ('license:', 'license2:', 'fivem:'):
            for value in identifiers:
                if isinstance(value, str) and re.fullmatch(re.escape(prefix) + r'[a-zA-Z0-9]{1,128}', value): return value
        raise ValueError('Não foi possível identificar sua conta FiveM.')
    @staticmethod
    def name(value):
        if not isinstance(value, str): raise ValueError('Informe um nome.')
        value = ''.join(c for c in value.strip() if c.isprintable())[:64]
        if not value: raise ValueError('Informe um nome.')
        return value
    def check(self, identifiers, name):
        identity = self.identity(identifiers); name = self.name(name); now = time.time()
        with self.connect() as db:
            db.execute('INSERT INTO users(identifier,name,created_at,last_seen) VALUES(?,?,?,?) ON CONFLICT(identifier) DO UPDATE SET last_seen=excluded.last_seen', (identity,name,now,now))
            row = db.execute('SELECT id,name,status FROM users WHERE identifier=?', (identity,)).fetchone()
        return dict(row)
    def update(self, user_id, body):
        values = {}; 
        if 'name' in body: values['name'] = self.name(body['name'])
        if 'status' in body:
            if body['status'] not in STATUSES: raise ValueError('Situação inválida.')
            values['status'] = body['status']
        if not values: raise ValueError('Nenhuma alteração informada.')
        with self.connect() as db:
            cur = db.execute('UPDATE users SET '+','.join(k+'=?' for k in values)+' WHERE id=?', (*values.values(), user_id))
            if cur.rowcount != 1: raise KeyError('Jogador não encontrado.')
    def list(self, query='', status='all'):
        with self.connect() as db:
            rows = [dict(r) for r in db.execute('SELECT u.id,u.name,u.status,CASE WHEN EXISTS(SELECT 1 FROM server_sessions s WHERE s.identifier=u.identifier AND s.seen_at>?) THEN 1 ELSE 0 END AS online FROM users u ORDER BY CASE u.status WHEN \'pending\' THEN 0 WHEN \'approved\' THEN 1 ELSE 2 END,u.id', (time.time()-20,))]
        counts = {s:sum(r['status']==s for r in rows) for s in STATUSES}; counts['total'] = len(rows)
        counts['online'] = sum(r['online'] for r in rows)
        rows = [r for r in rows if (status=='all' or r['status']==status) and (query.casefold() in r['name'].casefold() or query in str(r['id']))]
        return {'users':rows, 'counts':counts}
    def heartbeat(self, players, server='principal'):
        # FiveM's JSON encoder may serialize an empty Lua table as an object.
        if players == {}: players = []
        if not isinstance(players, list) or len(players)>128: raise ValueError('Lista inválida.')
        if not isinstance(server,str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,40}',server): raise ValueError('Servidor inválido.')
        result=[]; now=time.time()
        for p in players:
            if not isinstance(p,dict): raise ValueError('Jogador inválido.')
            sid=int(p['source']); row=self.check(p.get('identifiers'),p.get('name'))
            result.append({'source':sid,**row})
        with self.connect() as db:
            db.execute('DELETE FROM server_sessions WHERE server=? OR seen_at<?',(server,now-60))
            for p,row in zip(players,result):
                if row['status']=='approved': db.execute('INSERT INTO server_sessions VALUES(?,?,?) ON CONFLICT(identifier,server) DO UPDATE SET seen_at=excluded.seen_at',(self.identity(p['identifiers']),server,now))
        return result

class App:
    def __init__(self, store, settings):
        self.store=store; self.settings=settings; self.sessions={}; self.used_links={}; self.lock=threading.Lock(); self.bridge_seen=0; self.failures=[]
    def issue_session(self):
        token=secrets.token_urlsafe(32); csrf=secrets.token_urlsafe(24)
        with self.lock:
            self.sessions={k:v for k,v in self.sessions.items() if v['until']>time.time()}
            self.sessions[token]={'csrf':csrf,'until':time.time()+43200}
        return token,csrf
    def session(self, cookie):
        jar=SimpleCookie()
        try: jar.load(cookie or ''); token=jar['cidade_admin'].value if 'cidade_admin' in jar else ''
        except Exception: return None
        value=self.sessions.get(token)
        return value if value and value['until']>time.time() else None
    def verify_link(self, value):
        try:
            payload, signature=value.split('.'); expected=hmac.new(self.settings['admin_secret'].encode(),payload.encode(),hashlib.sha256).hexdigest()
            if not hmac.compare_digest(signature,expected): return False
            data=json.loads(base64.urlsafe_b64decode(payload+'='*(-len(payload)%4)))
            if not time.time()-5<data['until']<time.time()+120: return False
            with self.lock:
                self.used_links={k:v for k,v in self.used_links.items() if v>time.time()}
                if data['nonce'] in self.used_links: return False
                self.used_links[data['nonce']]=data['until']
            return True
        except (ValueError,KeyError,TypeError): return False

def load_settings():
    data=ROOT/'data'; data.mkdir(exist_ok=True); path=data/'config.json'
    if not path.exists():
        settings={'port':8787,'api_key':secrets.token_urlsafe(40),'admin_secret':secrets.token_urlsafe(40),'admin_password':secrets.token_urlsafe(16),'addresses':{'vpn':'','lan':'127.0.0.1:30120'}}
        path.write_text(json.dumps(settings,indent=2),encoding='utf-8')
    settings=json.loads(path.read_text(encoding='utf-8'))
    settings['port']=int(os.environ.get('PANEL_PORT',settings['port']))
    return settings

def local_link(settings):
    payload=base64.urlsafe_b64encode(json.dumps({'until':time.time()+60,'nonce':secrets.token_urlsafe(20)},separators=(',',':')).encode()).decode().rstrip('=')
    signature=hmac.new(settings['admin_secret'].encode(),payload.encode(),hashlib.sha256).hexdigest()
    return f"http://127.0.0.1:{settings['port']}/auth/local?token={payload}.{signature}"

def handler(app):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args): pass
        def send(self, status, value, mime='application/json; charset=utf-8', headers=None):
            raw=json.dumps(value,ensure_ascii=False).encode() if isinstance(value,(dict,list)) else value if isinstance(value,bytes) else value.encode()
            self.send_response(status); self.send_header('Content-Type',mime); self.send_header('Content-Length',str(len(raw)))
            self.send_header('Cache-Control','no-store'); self.send_header('X-Content-Type-Options','nosniff'); self.send_header('Referrer-Policy','no-referrer')
            self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
            for k,v in (headers or {}).items(): self.send_header(k,v)
            self.end_headers(); self.wfile.write(raw)
        def valid_host(self):
            return self.headers.get('Host') in (f"127.0.0.1:{app.settings['port']}",f"localhost:{app.settings['port']}")
        def session(self): return app.session(self.headers.get('Cookie'))
        def do_GET(self):
            if not self.valid_host(): return self.send(403,{'error':'Host não permitido.'})
            url=urllib.parse.urlsplit(self.path); query=urllib.parse.parse_qs(url.query)
            if url.path=='/health': return self.send(200,{'ok':True,'app':'cidade_acesso'})
            if url.path=='/auth/local':
                if not app.verify_link(query.get('token',[''])[0]): return self.send(403,{'error':'Link expirado. Abra iniciar-painel.cmd novamente.'})
                token,_=app.issue_session()
                return self.send(303,b'',headers={'Location':'/','Set-Cookie':f'cidade_admin={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=43200'})
            if url.path in ('/','/app.js','/style.css'):
                name={'/':'index.html','/app.js':'app.js','/style.css':'style.css'}[url.path]
                mime={'/':'text/html; charset=utf-8','/app.js':'text/javascript; charset=utf-8','/style.css':'text/css; charset=utf-8'}[url.path]
                return self.send(200,(ROOT/'web'/name).read_bytes(),mime)
            if url.path.startswith('/api/'):
                session=self.session()
                if not session: return self.send(401,{'error':'Entre no painel.'})
                if url.path=='/api/session': return self.send(200,{'csrf':session['csrf']})
                if url.path=='/api/users': return self.send(200,app.store.list(query.get('q',[''])[0][:64],query.get('status',['all'])[0]))
                if url.path=='/api/status': return self.send(200,{'connected':time.time()-app.bridge_seen<20,'addresses':app.settings['addresses'],'model':'a_m_y_business_01','slots':16})
            return self.send(404,{'error':'Não encontrado.'})
        def do_POST(self):
            if not self.valid_host(): return self.send(403,{'error':'Host não permitido.'})
            url=urllib.parse.urlsplit(self.path)
            try:
                size=int(self.headers.get('Content-Length','0'))
                if not 0<size<=65536: return self.send(413,{'error':'Requisição inválida.'})
                if self.headers.get('Content-Type','').split(';')[0]!='application/json': return self.send(415,{'error':'Use JSON.'})
                body=json.loads(self.rfile.read(size));
                if not isinstance(body,dict): raise ValueError('Corpo inválido.')
                if url.path.startswith('/bridge/'):
                    if not hmac.compare_digest(self.headers.get('X-Cidade-Key',''),app.settings['api_key']): return self.send(401,{'error':'Não autorizado.'})
                    if url.path=='/bridge/check': return self.send(200,app.store.check(body.get('identifiers'),body.get('name')))
                    if url.path=='/bridge/heartbeat':
                        result=app.store.heartbeat(body.get('players'),body.get('server','principal'));app.bridge_seen=time.time();return self.send(200,{'players':result})
                    return self.send(404,{'error':'Não encontrado.'})
                origin=self.headers.get('Origin')
                if origin not in (f"http://127.0.0.1:{app.settings['port']}",f"http://localhost:{app.settings['port']}"): return self.send(403,{'error':'Origem não permitida.'})
                if url.path=='/api/login':
                    now=time.time(); app.failures=[t for t in app.failures if t>now-60]
                    if len(app.failures)>=10: return self.send(429,{'error':'Aguarde um minuto e tente novamente.'})
                    if not hmac.compare_digest(str(body.get('password','')),app.settings['admin_password']):
                        app.failures.append(now);return self.send(401,{'error':'Senha incorreta.'})
                    token,csrf=app.issue_session();return self.send(200,{'csrf':csrf},headers={'Set-Cookie':f'cidade_admin={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=43200'})
                session=self.session()
                if not session: return self.send(401,{'error':'Entre no painel.'})
                if not hmac.compare_digest(self.headers.get('X-CSRF-Token',''),session['csrf']): return self.send(403,{'error':'Atualize o painel e tente novamente.'})
                match=re.fullmatch(r'/api/users/(\d+)',url.path)
                if match: app.store.update(int(match[1]),body);return self.send(200,{'ok':True})
                if url.path=='/api/logout':
                    session['until']=0;return self.send(200,{'ok':True},headers={'Set-Cookie':'cidade_admin=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0'})
                return self.send(404,{'error':'Não encontrado.'})
            except (ValueError,TypeError,json.JSONDecodeError): return self.send(400,{'error':'Dados inválidos. Confira o nome e a situação.'})
            except KeyError: return self.send(404,{'error':'Jogador não encontrado.'})
            except sqlite3.Error: return self.send(503,{'error':'Banco ocupado. Tente novamente.'})
    return Handler

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--open',action='store_true');parser.add_argument('--setup',action='store_true');args=parser.parse_args()
    settings=load_settings()
    if args.setup:
        Store(); private=ROOT.parent/'server-data/acesso.cfg'
        private.write_text(f'set cidade_acesso_url "http://127.0.0.1:{settings["port"]}"\nset cidade_acesso_key "{settings["api_key"]}"\n',encoding='utf-8')
        print('Banco SQLite e configuração privada preparados.');return
    if args.open:
        with urllib.request.urlopen(f'http://127.0.0.1:{settings["port"]}/health',timeout=2) as r: assert json.load(r)['app']=='cidade_acesso'
        webbrowser.open(local_link(settings));return
    server=ThreadingHTTPServer(('127.0.0.1',settings['port']),handler(App(Store(),settings)))
    print(f'Painel local: http://127.0.0.1:{settings["port"]}',flush=True)
    server.serve_forever()

if __name__=='__main__': main()
