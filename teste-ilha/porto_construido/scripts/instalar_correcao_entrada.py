from pathlib import Path
import json,shutil,xml.etree.ElementTree as ET
O=Path(__file__).resolve().parents[1];P=O.parent;R=P.parent
for name in ['client.lua','server.lua']:
    shutil.copy2(O/'fivem'/name,R/'server-data/resources/porto_esperanca'/name)
# Preserve the established XML declaration/layout of the standalone level.
water=O/'exportados/data/water.xml'
root=ET.fromstring(water.read_bytes());ET.indent(root,space='  ')
payload=b'<?xml version="1.0" encoding="UTF-8"?>\r\n'+ET.tostring(root,encoding='utf-8').replace(b'\n',b'\r\n')
for target in [water,P/'fivem/data/water.xml',R/'server-data/resources/teste_ilha/data/water.xml']:
    target.write_bytes(payload)
for target in [O/'exportados/data/config.json',P/'fivem/data/config.json',R/'server-data/resources/teste_ilha/data/config.json']:
    cfg=json.loads(target.read_text());cfg['revision']='ilha-20261009-porto-entrada-2'
    target.write_text(json.dumps(cfg,indent=2))
assert len(root.find('WaterQuads'))==287
print('ENTRY_FIX_INSTALLED; water regions:',len(root.find('WaterQuads')))
