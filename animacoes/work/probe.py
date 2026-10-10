import bpy,sys
sys.path[:0]=[r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps',r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\sollumz']
import addon_utils
addon_utils.enable('Sollumz',default_set=True)
print('BLENDER',bpy.app.version_string,'SOLLUMZ',hasattr(bpy.types.Object,'sollum_type'))
from szio.rpf import open_rpf
r=open_rpf(r'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V\x64e.rpf')
print('ROOT',list(r.list_dir('')))
print('MODELS',list(r.list_dir('models')))

print('ARCHIVES',list(r.list_dir('models/cdimages')))
n=r.open_nested('models/cdimages/componentpeds_comp_peds.rpf')
print('PEDS',[x for x in n.list_dir('') if 'business' in x])
w=r.open_nested('models/cdimages/weapons.rpf')
print('WEAPON',[x for x in w.list_dir('') if 'carbine' in x])
from pathlib import Path
out=Path(__file__).resolve().parent/'assets';out.mkdir(exist_ok=True)
for fname in ['w_ar_carbinerifle.ydr','w_ar_carbinerifle.ytd']:
 (out/fname).write_bytes(w.read_bytes(fname))
v=open_rpf(r'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V\x64v.rpf')
print('V',list(v.list_dir('models/cdimages')))
for archive in v.list_dir('models/cdimages'):
 if 'a_m_y' in archive:
  a=v.open_nested('models/cdimages/'+archive)
  print('MATCH',archive,[x for x in a.list_dir('') if 'business_01' in x])
  for name in a.list_dir(''):
   if name.startswith('a_m_y_business_01.'):
    (out/name).write_bytes(a.read_bytes(name));print('EXTRACTED',name)
import pymateria
print('MATERIA',[x for x in dir(pymateria) if not x.startswith('_')])
