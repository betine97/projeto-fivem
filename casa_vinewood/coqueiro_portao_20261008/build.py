from diagnose import *
import copy,hashlib,shutil
from szio.types import Vector
import pymateria.gta5.gen8 as g8
P.mkdir(exist_ok=True);O=P/'package';(O/'stream').mkdir(parents=True,exist_ok=True)
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
if not (P/'baseline.json').exists():
 (P/'baseline.json').write_text(json.dumps({f.relative_to(D).as_posix():sha(f) for f in D.rglob('*') if f.is_file()},indent=2))
target=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
f=S/'mansao_portao_subsolo.ydr';a=try_load_asset(f);raw=g8.Drawable.import_rsc(f).result
high=copy.deepcopy(a.models[LodLevel.HIGH])
for m in high:
 for g in m.geometries:
  # Decorative horizontal strips had only 2 mm clearance from the panel.
  # Increase it to 10 mm without changing the hinge or physical leaf.
  material=a.shader_group.shaders[g.shader_index]
  if any(p.value=='fach_cimento' for p in material.parameters if isinstance(p.value,str)):
   g.vertex_buffer['Position'][:,1]+=.008
  ids=g.index_buffer.reshape(-1,3);ps=g.vertex_buffer['Position'];keep=[];seen=set()
  for tri in ids:
   t=ps[tri];key=tuple(sorted(tuple(np.round(p,5)) for p in t))
   if key not in seen and np.linalg.norm(np.cross(t[1]-t[0],t[2]-t[0]))>1e-9:seen.add(key);keep.append(tri)
  g.index_buffer=np.array(keep,dtype=np.uint16).reshape(-1)
a.models={lod:copy.deepcopy(high) for lod in [LodLevel.HIGH,LodLevel.MEDIUM,LodLevel.LOW,LodLevel.VERYLOW]}
points=np.concatenate([g.vertex_buffer['Position'] for m in high for g in m.geometries]);lo=points.min(0)-.015;hi=points.max(0)+.015
# Expand only the broad-phase envelope; actual collision primitives unchanged.
a.bounds.bb_min=Vector(lo);a.bounds.bb_max=Vector(hi);a.bounds.centroid=Vector((lo+hi)/2);a.bounds.cg=a.bounds.centroid;a.bounds.radius_around_centroid=float(np.linalg.norm(hi-lo)/2)
save_asset(a,target,O/'stream',f.stem)
out=g8.Drawable.import_rsc(O/'stream'/f.name).result
for s,old in zip(out.shader_group.shaders,raw.shader_group.shaders):s.basis_shader=old.basis_shader;s.basis_material=old.basis_material
out.lights=raw.lights;g8.Drawable.export_rsc(out,O/'stream'/f.name)
typ=try_load_asset(S/'mansao_acesso_garagem.ytyp');t=next(t for t in typ.archetypes if str(t.name)=='mansao_portao_subsolo')
t.bb_min=Vector(lo);t.bb_max=Vector(hi);t.bs_center=Vector((lo+hi)/2);t.bs_radius=float(np.linalg.norm(hi-lo)/2)
save_asset(typ,target,O/'stream','mansao_acesso_garagem')
code=(D/'garagem_client.lua').read_text()
code=code.replace('opened = state == true', '''local desired = state == true
    -- A snapshot answering another load must not snap an ongoing movement.
    if instant and transition and desired == opened then return end
    opened = desired''',1)
at='SetEntityAsMissionEntity(leaf, true, true)'
assert code.count(at)==1
code=code.replace(at,at+'''\n                    SetEntityLodDist(leaf,220)
                    SetEntityAlwaysPrerender(leaf,true)''')
code+='''
-- Read-only diagnostics for the streamed movable gate.
RegisterCommand('garagemdebug',function()
    local info={loaded=leaf~=nil,opened=opened,angle=angle,moving=transition~=nil}
    if leaf and DoesEntityExist(leaf) then
        info.visible=IsEntityVisible(leaf);info.onScreen=IsEntityOnScreen(leaf)
        info.occluded=IsEntityOccluded(leaf)
    end
    print('[GARAGEM] '..json.encode(info))
end,false)
'''
(O/'garagem_client.lua').write_text(code,encoding='utf-8')
code=(D/'garagem_server.lua').read_text();code=code.replace('local origin, opened, lastToggle = config.origin, false, {}','local origin, opened, lastToggle = config.origin, false, {}\nlocal movingUntil = 0')
code=code.replace('local player, now = source, GetGameTimer()','local player, now = source, GetGameTimer()\n    if now < movingUntil then return end')
code=code.replace('lastToggle[player] = now','lastToggle[player] = now\n    movingUntil = now + 1900')
(O/'garagem_server.lua').write_text(code,encoding='utf-8')
manifest=(D/'fxmanifest.lua').read_text();manifest+="\n-- Targeted removal of the palm in both original and relocated map positions.\nclient_script 'exterior_remocoes.lua'\n"
(O/'fxmanifest.lua').write_text(manifest,encoding='utf-8')
print('GATE_BUILT',len(points),'vertices, same geometry at every LOD')
