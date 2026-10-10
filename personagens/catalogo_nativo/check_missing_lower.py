import inventory as inv
from szio.rpf import open_rpf
for name in ('mpbattle','mpheist4'):
 a=open_rpf(inv.GAME/'update/x64/dlcpacks'/name/'dlc.rpf')
 print(name,a.list_dir(''))
 for path in ('x64','x64/models','x64/models/cdimages'):
  try: print(path,a.list_dir(path))
  except Exception as e: print(str(e))
