exec((__import__('pathlib').Path(__file__).parent/'inspect_assets.py').read_text().split('out={}')[0])
from PIL import Image,ImageDraw
a=g8.Drawable.import_rsc(D/'stream/mansao_tv.ydr').result
tx=next(iter(a.shader_group.texture_dictionary.textures.values()))
print('TV textures',[(str(k),v.width,v.height) for k,v in a.shader_group.texture_dictionary.textures.items()])
tvread=try_load_asset(D/'stream/mansao_tv.ydr');sb=tvread.shader_group.shaders[0]
key=next(p.value for p in sb.parameters if p.name=='diffusesampler')
(P/'tv_diffuse.dds').write_bytes(tvread.shader_group.embedded_textures[key].data.read_bytes())
im=np.asarray(Image.open(P/'tv_diffuse.dds').convert('RGB'));h,w=im.shape[:2]
vs=np.concatenate([g.vb.buffer for m in a.lods[pm.LodType.HIGH].models for g in m.geometries])
pos=vs['POSITION'];uv=vs['TEXTURE0'];c=im[(uv[:,1]*h).astype(int)%h,(uv[:,0]*w).astype(int)%w]
plot=Image.new('RGB',(1250,1050),(90,90,90));draw=ImageDraw.Draw(plot)
for y in np.arange(-11.5,-6,.5):
 x=int((y+11.5)*220+20);draw.line((x,10,x,1020),fill=(110,110,110));draw.text((x,1025),f'{y:.1f}',fill='white')
for z in np.arange(-1,3,.5):
 y=int((3-z)*220+20);draw.line((0,y,1250,y),fill=(110,110,110));draw.text((3,y),f'{z:.1f}',fill='white')
for p,color in zip(pos,c):
 x=int((p[1]+11.5)*220+20);y=int((3-p[2])*220+20)
 draw.rectangle((x,y,x+1,y+1),fill=tuple(map(int,color)))
plot.save(P/'tv_front.png')
triangles=[];allq=[]
for m in a.lods[pm.LodType.HIGH].models:
 for g in m.geometries:
  vb=g.vb.buffer;ids=g.ib.indices.reshape(-1,3);tris=vb['POSITION'][ids];tuv=vb['TEXTURE0'][ids].mean(axis=1)
  colors=im[(tuv[:,1]*h).astype(int)%h,(tuv[:,0]*w).astype(int)%w]
  allq.extend(tris[(colors.max(axis=1)<45)&(tris.mean(axis=1)[:,0]>-8.9)&(tris.mean(axis=1)[:,2]>.5)])
  triangles.extend(zip(tris,colors))
for tri,color in sorted(triangles,key=lambda r:r[0][:,0].mean()):
 xy=[(int((p[1]+11.5)*220+20),int((3-p[2])*220+20)) for p in tri];draw.polygon(xy,fill=tuple(map(int,color)))
plot.save(P/'tv_front_solid.png')
print('FRONT BLACK FACES',np.quantile(np.asarray(allq).reshape(-1,3),[0,.01,.05,.5,.95,.99,1],axis=0))
black=(c.max(axis=1)<40)&(pos[:,2]>.6)&(pos[:,1]>-10.5)&(pos[:,1]<-7)
print('Black screen point quantiles',np.quantile(pos[black],[0,.01,.05,.5,.95,.99,1],axis=0))
b=g8.Drawable.import_rsc(D/'stream/mansao_pendentes.ydr').result
caps=json.loads((R/'casa_vinewood/luminarias_cor_alcance_20261008/caps_medidas.json').read_text())
groups=[]
for cap in sorted(caps,key=lambda q:q['center'][1]):
 if not groups or abs(cap['center'][1]-groups[-1][0]['center'][1])>.15:groups.append([])
 groups[-1].append(cap)
rows=[min(group,key=lambda q:q['center'][2]) for group in groups]
print('Cylinder real bottom caps',[(r['center'],r['min'],r['max']) for r in rows])
(P/'bottom_caps.json').write_text(json.dumps(rows,indent=2))
