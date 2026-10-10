import bpy,sys,json
from pathlib import Path
sys.path.insert(0,r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
from szio.gta5 import try_load_asset
root=Path(__file__).parent
for p in [root.parent/'animacoes/work/assets/a_m_y_business_01.ydd',root/'exports/cartelking.ydd']:
 a=try_load_asset(p)
 for name,d in a.drawables.items():
  print('DRAW',p.name,name,[(s.preset_filename,[(p.name,str(p.value)) for p in s.parameters if 'Sampler' in p.name]) for s in d.shader_group.shaders])
t=try_load_asset(root.parent/'animacoes/work/assets/a_m_y_business_01.ytd');print('DONOR_TEXTURES',list(t.textures))
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=r'C:\Users\erons\Downloads\Meshy_AI_The_Cartel_King_1002201832_texture.glb')
for o in bpy.context.scene.objects:
 print('GLB',o.name,o.type,tuple(o.dimensions),len(o.data.vertices) if o.type=='MESH' else '',len(o.data.bones) if o.type=='ARMATURE' else '')
 if o.type=='MESH':print('MATERIALS',[(m.name,[(n.name,n.image.name,tuple(n.image.size)) for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image]) for m in o.data.materials])
bpy.ops.wm.save_as_mainfile(filepath=str(root/'glb_source.blend'))
