import numpy as np
# Clip a polygon (arbitrary attributes), using its first three values as position.
def split(poly,axis,bound,keep_less):
 inside=[];outside=[]
 if len(poly)<3:return [],[]
 def dist(p):return (p[axis]-bound)*(1 if keep_less else -1)
 for a,b in zip(poly,poly[1:]+poly[:1]):
  da,db=dist(a),dist(b);ia=da<=1e-7;ib=db<=1e-7
  (inside if ia else outside).append(a)
  if ia!=ib:
   q=a+(b-a)*(da/(da-db));inside.append(q);outside.append(q)
 return inside,outside

def subtract_box(poly,lo,hi):
 p=np.array(poly)
 if np.any(p[:,:3].max(0)<lo) or np.any(p[:,:3].min(0)>hi):return [poly],False
 remaining=poly;result=[]
 for axis in range(3):
  for bound,less in [(lo[axis],False),(hi[axis],True)]:
   remaining,out=split(remaining,axis,bound,less)
   if len(out)>=3:result.append(out)
   if len(remaining)<3:return [poly],False
 return result,True
