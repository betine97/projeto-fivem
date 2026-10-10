import sys, json, struct, io
from pathlib import Path
root=Path(__file__).resolve().parents[3]
sys.path[:0]=[r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps',str(root/'laboratorio_fivem/work/pydeps')]
import numpy as np
from PIL import Image
from szio.gta5 import try_load_asset
for name,path in [('guard',root/'personagens/traje_guarda/exports/guardalab.ydd'),('donor',root/'animacoes/work/assets/a_m_y_business_01.ydd')]:
 a=try_load_asset(path)
 for k,d in a.drawables.items():
  models=next(iter(d.models.values()));g=models[0].geometries[0]
  print(name,k,d.name,'LODS',[(str(l),sum(len(g.index_buffer)//3 for m in mm for g in m.geometries)) for l,mm in d.models.items()])
  print('model',models[0].bone_index,models[0].has_skin,models[0].matrix_count,models[0].flags,models[0].render_bucket_mask,'dtype',g.vertex_buffer.dtype,'palette',g.bone_ids.tolist(),'bbox',g.vertex_buffer['Position'].min(axis=0).tolist(),g.vertex_buffer['Position'].max(axis=0).tolist())
  if name=='guard' and len(g.index_buffer)>30:
   for s in d.shader_group.shaders:print('shader',s)
  if name=='donor' and d.skeleton:
   print('bones',[(i,b.name,list(b.position),list(b.rotation),b.parent_index) for i,b in enumerate(d.skeleton.bones) if b.name in ['SKEL_ROOT','SKEL_Pelvis','SKEL_L_Foot','SKEL_L_UpperArm','SKEL_Head']])
raw=Path(r'C:\Users\erons\Downloads\Meshy_AI_hazmat_worker_lowpoly_1005172433_texture.glb').read_bytes()
n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n]);binary=raw[28+n:]
v=doc['bufferViews'][doc['images'][0]['bufferView']];im=Image.open(io.BytesIO(binary[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]))
print('IMAGE',im.size,im.mode)
im.thumbnail((1024,1024));im.save(root/'personagens/person2/work/source_texture_preview.png')
