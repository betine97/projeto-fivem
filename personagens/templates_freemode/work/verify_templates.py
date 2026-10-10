import bpy,sys,addon_utils,json,hashlib,struct
from pathlib import Path
sys.path[:0]=[r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps',r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\sollumz']
addon_utils.enable('Sollumz',default_set=True)
root=Path(__file__).resolve().parents[1]
expected=json.loads((root/'work/validation.json').read_text())
def fingerprint(mesh):
 h=hashlib.sha256()
 for v in mesh.vertices:h.update(struct.pack('<3f',*v.co))
 for p in mesh.polygons:h.update(struct.pack('<'+'I'*len(p.vertices),*p.vertices))
 for uv in mesh.uv_layers:
  for d in uv.data:h.update(struct.pack('<2f',*d.uv))
 return h.hexdigest()
report=[]
for name in ['01_BASE_ROUPAS.blend','02_BASE_ANIMACOES.blend']:
 bpy.ops.wm.open_mainfile(filepath=str(root/name))
 rig=bpy.data.objects['MP_M_FREEMODE_01_RIG'];assert len(rig.data.bones)==128
 meshes=list(bpy.data.collections['01_CORPO_REFERENCIA'].objects);assert len(meshes)==4
 for e in expected['meshes']:
  o=bpy.data.objects[e['object']];assert fingerprint(o.data)==e['geometry_uv_sha256']
  assert next(m.object for m in o.modifiers if m.type=='ARMATURE')==rig
  for v in o.data.vertices:
   assert all(o.vertex_groups[g.group].name in rig.data.bones for g in v.groups if g.weight>0)
  for mat in o.data.materials:
   node=mat.node_tree.nodes.get('DiffuseSampler')
   assert node and node.image and node.image.packed_file and node.image.size[0]>1
 assert bpy.data.collections['00_ORIGINAIS_GTA_NAO_EDITAR'].hide_render
 assert bpy.data.collections['00_ORIGINAIS_GTA_NAO_EDITAR'].hide_viewport
 assert bpy.context.scene.frame_current==1
 assert max(abs(v) for p in rig.pose.bones for row in (p.matrix_basis-__import__('mathutils').Matrix.Identity(4)) for v in row)<0.00001
 if name.startswith('02'):
  assert rig.animation_data.action.name=='NOVA_ANIMACAO'
  assert bpy.data.actions.get('TESTE_FLEXAO')
 report.append({'file':name,'bones':len(rig.data.bones),'mesh_hashes_match':True,'diffuse_textures_packed':True,'rest_pose':True,'bytes':(root/name).stat().st_size})
(root/'work/reopen_validation.json').write_text(json.dumps(report,indent=2))
print('VALIDATION_OK',json.dumps(report))
