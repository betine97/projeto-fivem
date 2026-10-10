from locate import *
import pymateria.gta5.gen8 as g8
raw=g8.DrawableDictionary.import_rsc(N/'bh1_22_slod1_children.ydd').result;print('draws',list(raw.drawables.keys()))
b=try_load_asset(N/'bh1_lod.ymap')
for e in b.entities:
 if any(k in str(e.archetype_name) for k in ['17_18_22','slod3']):print(str(e.archetype_name),list(e.position))
