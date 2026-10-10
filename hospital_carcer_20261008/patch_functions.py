def area(t):return float(np.linalg.norm(np.cross(t[1][:3]-t[0][:3],t[2][:3]-t[0][:3]))*.5)
def tris(poly):
 for i in range(1,len(poly)-1):
  t=np.array([poly[0],poly[i],poly[i+1]])
  if area(t)>1e-7:yield t
def split_plane(poly,n,k):
 inside=[];out=[]
 for a,b in zip(poly,poly[1:]+poly[:1]):
  da=float(n@a[:3]-k);db=float(n@b[:3]-k);ia=da<=1e-7;ib=db<=1e-7
  (inside if ia else out).append(a)
  if ia!=ib:q=a+(b-a)*da/(da-db);inside.append(q);out.append(q)
 return inside,out
def cut(poly):
 xyz=np.array(poly)[:,:3]
 if np.any(xyz.max(0)<lo) or np.any(xyz.min(0)>hi):return [poly],False
 pieces=[poly];changed=False
 for c0,c1,pp in planes:
  new=[]
  for p in pieces:
   xyz=np.array(p)[:,:3]
   if np.any(xyz.max(0)<c0) or np.any(xyz.min(0)>c1):new.append(p);continue
   rem=p;outside=[]
   for n,k in pp:
    rem,out=split_plane(rem,n,k)
    if len(out)>=3:outside.append(out)
    if len(rem)<3:break
   if len(rem)>=3 and sum(area(t) for t in tris(rem))>1e-7:new.extend(outside);changed=True
   else:new.append(p)
  pieces=new
 return pieces,changed
def canonical(a):
 for s in a.shader_group.shaders:s.name=Path(s.preset_filename).stem
def patch_drawable(a,offset,force=False,main=False):
 changed=0;before=0
 for ms in a.models.values():
  for m in ms:
   geoms=[]
   for g in m.geometries:
    vb=g.vertex_buffer;names=vb.dtype.names;oldtri=g.index_buffer.reshape(-1,3);before+=len(oldtri);extra=[];idx=[]
    # Exclusive castle/garage materials include all trim, windows and roof.
    exclusive=force or (main and g.shader_index in [14,16,18,19,20,22])
    for ids in oldtri:
     if exclusive:changed+=1;continue
     poly=[np.r_[row['Position'].astype(float)+offset,np.concatenate([np.asarray(row[n]).reshape(-1).astype(float) for n in names if n!='Position'])] for row in vb[ids]]
     parts,hit=cut(poly)
     if not hit:idx.extend(map(int,ids));continue
     changed+=1
     for p in parts:
      for t in tris(p):
       start=len(vb)+len(extra)
       for v in t:
        row=np.zeros((),dtype=vb.dtype);row['Position']=v[:3]-offset;k=3
        for n in names:
         if n=='Position':continue
         dst=np.asarray(row[n]);q=v[k:k+dst.size];k+=dst.size
         if np.issubdtype(dst.dtype,np.integer):q=np.clip(np.rint(q),0,np.iinfo(dst.dtype).max)
         if n=='Normal' and np.linalg.norm(q)>0:q/=np.linalg.norm(q)
         row[n]=q.reshape(dst.shape)
        extra.append(row)
       idx.extend([start,start+1,start+2])
    if idx:
     # Compact unused vertices after the cut, keeping indices inside 16 bits.
     allvb=np.concatenate([vb,np.asarray(extra,dtype=vb.dtype)]) if extra else vb
     used,inv=np.unique(idx,return_inverse=True);assert len(used)<65535
     g.vertex_buffer=allvb[used];g.index_buffer=inv.astype(np.uint16);geoms.append(g)
   m.geometries=geoms
 a.models={lod:[m for m in ms if m.geometries] for lod,ms in a.models.items() if any(m.geometries for m in ms)}
 if changed:canonical(a)
 return changed,before
