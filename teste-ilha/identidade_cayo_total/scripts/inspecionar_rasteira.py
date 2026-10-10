from common import *
import dataclasses, collections, struct
from PIL import Image
from szio.gta5 import LodLevel
S=O/'stream'
a=try_load_asset(next(S.glob('ni_rasteira_*.ymap')))
print('GRASS_MAP',a.streaming_extents,a.entities_extents)
for b in a.grass_instance_lists[:5]:
    print('BATCH',str(b.archetype_name),{f.name:getattr(b,f.name) for f in dataclasses.fields(b) if f.name!='instances'},'INSTANCE',b.instances.dtype,b.instances[:2])
atlas=try_load_asset(S/'ni_canopy_atlas.ytd')
for key,t in atlas.textures.items():
    print('ATLAS',key,repr(t))
    d=t.data.read_bytes();print('DDS_HEADER',len(d),struct.unpack_from('<7I',d,4))
n=read(O/'dados/implantacao.json')
for name,m in list(n['models'].items()):
    if m['family']!='bush':continue
    d=try_load_asset(S/(n['alias_map'][name]+'.ydr'))
    print('BUSH',name,'ARCHLOD',m.get('lod'),'DRAWABLELOD',d.lod_thresholds,'MODELS',[(str(k),sum(len(g.vertex_buffer) for model in v for g in model.geometries)) for k,v in d.models.items()])
F=dict(np.load(O/'dados/biomas.npz'));mask=F['mask'];g=mask[...,1]/255;b=mask[...,2]/255
mix=np.stack([(1-g)*(1-b),(1-g)*b,g*(1-b),g*b],-1)
land=F['identity']&~F['water']&(z>1.5)
print('GROUND_WEIGHTS',mix[land].mean(0),'AREA',land.sum()*dx*dy,'GRID',grid.shape,dx,dy)

