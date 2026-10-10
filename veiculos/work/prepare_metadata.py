import sys,xml.etree.ElementTree as ET,json,bpy
from pathlib import Path
root=Path(__file__).resolve().parent.parent;game=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V')
sys.path.insert(0,r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
from szio.rpf import open_rpf
archive=open_rpf(game/'update/update.rpf')
data=archive.read_bytes('common/data/levels/gta5/vehicles.meta');tree=ET.fromstring(data)
item=next(i for i in tree.find('InitDatas') if i.findtext('modelName')=='rebel2')
print('VEHICLE_METADATA',ET.tostring(item,encoding='unicode'))
for n in ['modelName','txdName']:item.find(n).text='sertao'
item.find('gameName').text='SERTAO';item.find('vehicleMakeName').text='CIDADE'
item.find('audioNameHash').text='REBEL2'
out=root.parent/'server-data/resources/cidade_core/data';out.mkdir(exist_ok=True)
new=ET.Element('CVehicleModelInfo__InitDataList');ET.SubElement(new,'residentTxd').text='vehshare'
ET.SubElement(new,'residentAnims');ET.SubElement(new,'InitDatas').append(item)
rels=ET.SubElement(new,'txdRelationships');rel=ET.SubElement(rels,'Item');ET.SubElement(rel,'parent').text='vehshare';ET.SubElement(rel,'child').text='sertao'
ET.indent(new);ET.ElementTree(new).write(out/'sertao_vehicles.meta',encoding='utf-8',xml_declaration=True)
bpy.ops.wm.open_mainfile(filepath=str(root/'work/donor.blend'))
from mathutils import Vector
for name in ['bodyshell','bonnet','boot','door_dside_f','windscreen','windscreen_r','chassis','wing_lf']:
 o=bpy.data.objects[name];pts=[o.matrix_world@Vector(v) for v in o.bound_box]
 print('BOUNDS',name,[tuple(round(f(v[i] for v in pts),3) for i in range(3)) for f in (min,max)])
