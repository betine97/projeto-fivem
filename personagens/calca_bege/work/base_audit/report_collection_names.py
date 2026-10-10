import hashlib,json,re,zlib
from pathlib import Path
out=Path(__file__).resolve().parent
rows=[]
for pack,file,archive,nested in [
 ('mpheist','mp_m_freemode_01_male_heist.ymt',r'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V\update\x64\dlcpacks\mpheist\dlc.rpf','x64/models/cdimages/mpheist_streamedpeds.rpf'),
 ('mpapartment','mp_m_freemode_01_male_apt01.ymt',r'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V\update\x64\dlcpacks\mpapartment\dlc.rpf','x64/models/cdimages/mpapt01.rpf')]:
 path=out/(pack+'__'+file);data=path.read_bytes();decoded=zlib.decompress(data[16:],-15)
 exact=[{'value':m.group().decode('ascii'),'offset_decompressed':m.start()} for m in re.finditer(rb'[\x20-\x7e]{4,}',decoded) if b'Male_' in m.group()]
 rows.append({'pack':pack,'source_archive':archive,'nested_archive':nested,'source_entry':file,'extracted_file':str(path.resolve()),'sha256':hashlib.sha256(data).hexdigest(),'rsc7_payload_compression':'raw DEFLATE beginning at byte 16','decompressed_size':len(decoded),'exact_collection_name_strings':exact})
report={'investigation':'Lua collection lookup previously compared lowercase strings case-sensitively. Use lower(name) only for matching and retain native returned name for component calls.','sources':rows,'client_evidence':{'log':r'C:\Users\erons\AppData\Local\FiveM\FiveM.app\logs\CitizenFX_log_2026-10-05T062336.log','loaded_heist_line':537,'loaded_apartment_line':548,'old_failure_line':661,'game_build':3258},'safe_fallback':'If enumeration cannot find a collection, test candidate native collection names through IsPedCollectionComponentVariationValid before applying; otherwise abort without arbitrary global drawable guesses.'}
(out/'collection_names.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(rows,indent=2))
