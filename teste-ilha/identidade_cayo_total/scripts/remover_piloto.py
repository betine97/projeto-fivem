from common import *
from szio.gta5 import *
from szio.gta5.maps import MapContentFlags
import shutil,datetime,re
base=R/'server-data/resources/teste_ilha';stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S');backup=R/'server-data/backups'/('remocao-piloto-'+stamp);backup.mkdir(parents=True)
path=base/'stream/ti_amostra_natural.ymap';shutil.copy2(path,backup/path.name);a=try_load_asset(path);removed=len(a.entities);a.entities=[];a.grass_instance_lists=[];a.physics_dictionaries=[];a.content_flags=MapContentFlags(0);save_asset(a,(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),),path.parent,path.stem)
client=base/'client.lua';shutil.copy2(client,backup/client.name);s=client.read_text(encoding='utf8')
s=s.replace("clearOriginalMaps();RequestIpl('ti_amostra_natural')","clearOriginalMaps();RemoveIpl('ti_amostra_natural')")
s=re.sub(r"RegisterCommand\('amostrailha',function\(\).*?end,false\)","RegisterCommand('amostrailha',function() ExecuteCommand('natureza') end,false)",s,flags=re.S)
s=re.sub(r"RegisterCommand\('amostradiag',function\(\).*?end,false\)","RegisterCommand('amostradiag',function() ExecuteCommand('naturezadiag') end,false)",s,flags=re.S)
client.write_text(s,encoding='utf8');write(O/'dados/remocao_piloto.json',dict(removed_duplicate_native_pilot_entities=removed,backup=str(backup),pilot_maps_empty=True))
print('PILOT_REMOVED',removed,flush=True)
