from pathlib import Path
import sys
O=Path(__file__).resolve().parents[1];sys.path.insert(0,str(O.parent.parent/'laboratorio_fivem/work/pydeps'))
import numpy as np
for path in sorted((O/'cache').glob('pe_estrutura_[0-9][0-9].npz')):
    c=np.load(path);a={k:c[k] for k in c.files};t=a['collision_triangles'];used=np.unique(t)
    a['collision_vertices']=a['collision_vertices'][used];a['collision_triangles']=np.searchsorted(used,t).astype(np.int32)
    assert len(used)<32767
    np.savez_compressed(path,**a);print(path.stem,'COLLISION_VERTICES',len(used),flush=True)
