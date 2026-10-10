"""Local catalog and favorites bridge to the FiveM wardrobe resource."""
import json
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE = Path(__file__).resolve().parent
DIST = BASE / 'dist'
RESOURCE = BASE.parent / 'server-data/resources/cidade_acervo'
FAVORITES = RESOURCE / 'favorites.json'
LOCK = threading.Lock()
TAG_LABELS = ('OK', 'PEÇA INCORRETA', 'DEFEITO NA TEXTURA')

def read_tags():
    path = RESOURCE / 'tags.json'
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {'items': {}}

def read_catalog(path):
    catalog = json.loads(path.read_text(encoding='utf-8'))
    exclusive_path = RESOURCE / 'exclusives.json'
    exclusive_items = json.loads(exclusive_path.read_text(encoding='utf-8'))['items'] if exclusive_path.exists() else []
    known = {item['id'] for item in catalog['items']}
    for item in exclusive_items:
        if item.get('exclusive') is True and item['id'] not in known:
            catalog['items'].append(item)
            known.add(item['id'])
    return catalog

class Handler(SimpleHTTPRequestHandler):
    def reply(self, status, value):
        body = json.dumps(value, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.split('?', 1)[0] == '/catalog.json':
            catalog = read_catalog(DIST / 'catalog.json')
            for item in catalog['items']:
                if item.get('exclusive') is True:
                    for key in ('image', 'back'):
                        if item.get(key): item[key] = '/tablet/' + item[key]
            return self.reply(200, catalog)
        if self.path == '/api/tags':
            with LOCK:
                return self.reply(200, read_tags())
        if self.path == '/api/appearance':
            return self.reply(200, {
                'hair': json.loads((RESOURCE / 'hair.json').read_text(encoding='utf-8'))['items'],
                'tattoos': json.loads((RESOURCE / 'tattoos.json').read_text(encoding='utf-8'))['items'],
            })
        if self.path == '/api/wardrobe':
            with LOCK:
                favorites = json.loads(FAVORITES.read_text(encoding='utf-8')) if FAVORITES.exists() else {'ids': []}
                tags = read_tags()['items']
            catalog = read_catalog(RESOURCE / 'catalog.json')
            ids = set(favorites['ids'])
            return self.reply(200, [dict(item, favorite=item['id'] in ids) for item in catalog['items'] if item.get('exclusive') is True or 'OK' in tags.get(item['id'], [])])
        if self.path == '/api/favorites':
            with LOCK:
                value = json.loads(FAVORITES.read_text(encoding='utf-8')) if FAVORITES.exists() else {'ids': []}
            return self.reply(200, value)
        # Browser preview of the actual tablet UI; the ped itself exists only in FiveM.
        if self.path.startswith('/tablet/'):
            self.path = self.path.replace('/tablet/', '/', 1)
            original = self.directory
            self.directory = str(RESOURCE / 'ui')
            try:
                return super().do_GET()
            finally:
                self.directory = original
        return super().do_GET()

    def do_POST(self):
        if self.path not in ('/api/favorites', '/api/tags'):
            return self.reply(404, {'error': 'Endpoint inexistente'})
        if self.headers.get('Origin') not in (None, 'http://127.0.0.1:8766', 'http://localhost:8766'):
            return self.reply(403, {'error': 'Origem inválida'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 100000:
                raise ValueError('Tamanho inválido')
            if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
                raise ValueError('Envie JSON')
            value = json.loads(self.rfile.read(length))
            if self.path == '/api/tags':
                if not isinstance(value, dict) or not isinstance(value.get('id'), str) or not isinstance(value.get('tags'), list):
                    raise ValueError('Tags inválidas')
                catalog = read_catalog(RESOURCE / 'catalog.json')
                if value['id'] not in {i['id'] for i in catalog['items']}:
                    raise ValueError('Peça fora do acervo')
                if len(value['tags']) > len(TAG_LABELS) or any(tag not in TAG_LABELS for tag in value['tags']):
                    raise ValueError('Tag inválida')
                tags = list(dict.fromkeys(value['tags']))
                if 'OK' in tags and len(tags) > 1:
                    raise ValueError('OK não pode ser combinado com tags de defeito')
                with LOCK:
                    saved = read_tags()
                    if tags: saved['items'][value['id']] = tags
                    else: saved['items'].pop(value['id'], None)
                    path = RESOURCE / 'tags.json'
                    temporary = path.with_suffix('.tmp')
                    temporary.write_text(json.dumps(saved, ensure_ascii=False), encoding='utf-8')
                    temporary.replace(path)
                return self.reply(200, {'ok': True, 'id': value['id'], 'tags': tags})
            ids = value.get('ids') if isinstance(value, dict) else None
            if not isinstance(ids, list) or any(not isinstance(i, str) for i in ids):
                raise ValueError('Seleção inválida')
            catalog = read_catalog(DIST / 'catalog.json')
            known = {i['id'] for i in catalog['items']}
            if any(i not in known for i in ids):
                raise ValueError('Peça fora do acervo')
            result = {'ids': list(dict.fromkeys(ids))}
            with LOCK:
                RESOURCE.mkdir(parents=True, exist_ok=True)
                temporary = FAVORITES.with_suffix('.tmp')
                temporary.write_text(json.dumps(result), encoding='utf-8')
                temporary.replace(FAVORITES)
            return self.reply(200, {'count': len(result['ids'])})
        except (ValueError, TypeError) as error:
            return self.reply(400, {'error': str(error)})
        except OSError:
            return self.reply(500, {'error': 'Não foi possível salvar no acervo'})

if __name__ == '__main__':
    ThreadingHTTPServer(('127.0.0.1', 8766), partial(Handler, directory=str(DIST))).serve_forever()
