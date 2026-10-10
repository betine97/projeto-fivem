"""Extract native tattoo metadata and render native hair; never change favorites."""
import json, re, sys, hashlib, xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import render_catalog as rc

RESOURCE = ROOT / 'server-data/resources/cidade_acervo'
OUT = RESOURCE / 'ui/previews'
records, errors, shop = {}, [], {}
zones = {'ZONE_TORSO': 'torso', 'ZONE_HEAD': 'head', 'ZONE_LEFT_ARM': 'leftArm',
         'ZONE_RIGHT_ARM': 'rightArm', 'ZONE_LEFT_LEG': 'leftLeg', 'ZONE_RIGHT_LEG': 'rightLeg'}

def inspect(archive, source, path=''):
    for name in archive.list_dir(path):
        full = path + '/' + name if path else name
        if archive.is_dir(full):
            inspect(archive, source, full)
        elif name.lower() == 'shop_tattoo.meta':
            try:
                tree = ET.fromstring(archive.read_bytes(full))
                for item in tree.findall('.//TattooShopItems/Item'):
                    if item.findtext('updateGroup') == 'torsoDecal': continue
                    key = (item.findtext('collection', '').lower(), item.findtext('preset', '').lower())
                    shop[key] = item.findtext('textLabel', '')
            except Exception as error: errors.append({'source': source + '/' + full, 'error': str(error)})
        elif name.lower().endswith('.xml') and ('overlay' in name.lower()):
            try:
                tree = ET.fromstring(archive.read_bytes(full))
                if tree.tag != 'PedDecorationCollection': continue
                collection = Path(name).stem
                for item in tree.findall('./presets/Item'):
                    overlay = item.findtext('nameHash', '')
                    zone, gender = item.findtext('zone'), item.findtext('gender')
                    if item.findtext('type') != 'TYPE_TATTOO' or item.findtext('faction') != 'FM' or zone not in zones: continue
                    if any(part in overlay.lower() for part in ['hair', 'fuzz', 'beard', 'makeup']): continue
                    sexes = ['male','female'] if gender == 'GENDER_DONTCARE' else ['male'] if gender == 'GENDER_MALE' else ['female'] if gender == 'GENDER_FEMALE' else []
                    for sex in sexes:
                        ident = hashlib.sha1((collection.lower()+overlay.lower()+sex).encode()).hexdigest()[:16]
                        records[ident] = {'id': ident, 'collection': collection, 'overlay': overlay, 'sex': sex,
                                         'zone': zones[zone], 'source': source + '/' + full}
            except Exception as error: errors.append({'source': source + '/' + full, 'error': str(error)})

def main():
    legacy = rc.open_rpf(rc.GAME / 'x64w.rpf')
    dlcs = ET.fromstring((HERE/'active_dlclist.xml').read_bytes())
    for entry in dlcs.iter('Item'):
        match = re.search(r'dlcpacks:?/([^/]+)', (entry.text or '').replace('\\','/'), re.I)
        if not match: continue
        name = match[1].lower()
        p = rc.GAME / 'update/x64/dlcpacks' / name / 'dlc.rpf'
        if p.exists():
            archive = rc.open_rpf(p)
        elif legacy.exists('dlcpacks/'+name+'/dlc.rpf'):
            archive = legacy.open_nested('dlcpacks/'+name+'/dlc.rpf')
        else: continue
        inspect(archive, name); archive.close()
    update = rc.open_rpf(next(Path(r'C:\Users\erons\AppData\Local\FiveM\FiveM.app\data\game-storage').glob('update+update.rpf_*')), filename='update.rpf')
    inspect(update, 'active-update'); update.close(); legacy.close()
    tattoos = sorted(records.values(), key=lambda i: (i['zone'],i['collection'],i['overlay'],i['sex']))
    for i in tattoos:
        i['label'] = shop.get((i['collection'].lower(),i['overlay'].lower()), '')
    (RESOURCE/'tattoos.json').write_text(json.dumps({'build':3258,'items':tattoos},ensure_ascii=False), encoding='utf-8')
    # Hair diffuse RGB contains a palette mask, not the final game hair color.
    # Render a neutral brown tint for thumbnails; FiveM applies the chosen palette live.
    renderer = Path(rc.__file__).read_text(encoding='utf-8')
    vertex = re.search(r"vertex_shader='''(.*?)'''", renderer, re.S).group(1)
    rc.prog = rc.ctx.program(vertex_shader=vertex, fragment_shader='''#version 330
in vec3 n;in vec2 texcoord;uniform sampler2D albedo;out vec4 color;
void main(){vec4 t=texture(albedo,texcoord);if(t.a<.15)discard;
float light=.58+.32*max(dot(normalize(n),normalize(vec3(-.5,-1,1))),0.)+.1*max(dot(normalize(n),vec3(1,0,0)),0.);
float mask=.35+.65*dot(t.rgb,vec3(.2126,.7152,.0722));
color=vec4(vec3(.25,.17,.11)*mask*light,1.0);}
''')
    hairs=[]
    for row in rc.DATA['models']:
        if row['part']!='hair' or 'g9ec' in row['collection']: continue
        pieces=[]
        try:
            pieces,center,extent,_,_,_=rc.prep(row,min_extent=.0001,min_indices=3)
            ident=hashlib.sha1((row['collection']+'hair'+str(row['index'])).encode()).hexdigest()[:12]
            rc.render(pieces,center,extent,.15,OUT/f'hair-{ident}.webp')
            hairs.append({'sex':row['sex'],'collection':row['collection'],'index':row['index'],'image':f'previews/hair-{ident}.webp'})
        except Exception as error: errors.append({'hair':row['path'],'error':str(error)})
        finally:
            for piece in pieces:
                for obj in piece: obj.release()
    (RESOURCE/'hair.json').write_text(json.dumps({'items':hairs},ensure_ascii=False),encoding='utf-8')
    (HERE/'wardrobe_appearance_report.json').write_text(json.dumps({'tattoos':len(tattoos),'hair':len(hairs),'errors':errors},indent=2),encoding='utf-8')
    print('Extracted',len(tattoos),'native tattoos;',len(hairs),'hair previews;',len(errors),'skipped assets',flush=True)

if __name__=='__main__': main()
