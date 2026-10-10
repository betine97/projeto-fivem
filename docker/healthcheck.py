import json
import os
import urllib.request

for port, path in ((os.environ.get('PANEL_PORT','8887'), '/health'),
                   (os.environ.get('CAPTURE_PORT','8888'), '/health'),
                   (os.environ.get('ISLAND_PORT','30220'), '/info.json'),
                   (os.environ.get('CITY_PORT','30221'), '/info.json')):
    with urllib.request.urlopen(f'http://127.0.0.1:{port}{path}', timeout=2) as response:
        result = json.load(response)
        if path == '/health' and not result.get('ok'):
            raise SystemExit(1)
