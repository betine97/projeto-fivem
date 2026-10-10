"""Index native map bounds so static buildings can be identified from a click."""
from pathlib import Path
import json,sqlite3,sys,itertools,os
ROOT=Path(__file__).resolve().parent.parent
sys.path[:0]=[str(ROOT/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
from szio.rpf import open_rpf
from szio.gta5 import try_load_asset
import numpy as np
from build_index import joaat
GTA=Path(os.environ.get('GTA_ROOT',r'C:/Program Files (x86)/Steam/steamapps/common/Grand Theft Auto V'))
def main():
    home=ROOT/'captura_los_santos';index=json.loads((home/'data/model_index.json').read_text(encoding='utf8'))
    db=sqlite3.connect(home/'data/world_index.sqlite3')
    db.executescript('CREATE TABLE IF NOT EXISTS maps(path TEXT PRIMARY KEY); CREATE TABLE IF NOT EXISTS entities(id INTEGER PRIMARY KEY,hash INTEGER,pos TEXT,rotation TEXT,sxy REAL,sz REAL,map TEXT); CREATE VIRTUAL TABLE IF NOT EXISTS bounds USING rtree(id,minX,maxX,minY,maxY,minZ,maxZ);')
    arcs={};count=0
    done={r[0] for r in db.execute('SELECT path FROM maps')}
    for name,path in index['files'].items():
        if not name.endswith('.ymap') or path in done or any(s in name for s in ('_lod','_slod','_occl','_distant','_light','_long')):continue
        try:
            parts=path.split('|');key='|'.join(parts[:-1])
            if key not in arcs:
                arc=open_rpf(GTA/parts[0])
                for part in parts[1:-1]:arc=arc.open_nested(part)
                arcs[key]=arc
            temp=home/'cache/world-index.ymap';temp.write_bytes(arcs[key].read_bytes(parts[-1]))
            asset=try_load_asset(temp)
            if not asset:continue
            with db:
                for e in asset.entities:
                    h=joaat(str(e.archetype_name));meta=index['models'].get(str(h))
                    if not meta or not meta.get('bbMin') or not meta.get('bbMax'):continue
                    if any(s in meta['model'] for s in ('_lod','_slod','_occl','_shadow')):continue
                    lo,hi=meta['bbMin'],meta['bbMax'];pos=list(e.position);q=list(e.rotation)
                    w,x,y,z=q
                    rot=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
                    corners=np.array(list(itertools.product(*zip(lo,hi))))*np.array([e.scale_xy,e.scale_xy,e.scale_z])
                    # Include both quaternion conventions; exact geometry resolves overlap.
                    points=np.concatenate([corners@rot.T,corners@rot])+pos
                    low,high=points.min(0),points.max(0)
                    cur=db.execute('INSERT INTO entities(hash,pos,rotation,sxy,sz,map) VALUES(?,?,?,?,?,?)',(h,json.dumps(pos),json.dumps(q),float(e.scale_xy),float(e.scale_z),path))
                    db.execute('INSERT INTO bounds VALUES(?,?,?,?,?,?,?)',(cur.lastrowid,*[float(v) for pair in zip(low,high) for v in pair]))
                db.execute('INSERT INTO maps VALUES(?)',(path,))
            count+=1
            if count%100==0:print('MAPAS_INDEXADOS',count,flush=True)
        except Exception as error:print('MAPA_IGNORADO',name,str(error)[:120],flush=True)
    print('INDICE_MUNDO_PRONTO',db.execute('SELECT COUNT(*) FROM entities').fetchone()[0],flush=True)
if __name__=='__main__':main()
