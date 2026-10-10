import sys,addon_utils
sys.path[:0]=[r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps',r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\sollumz']
addon_utils.enable('Sollumz',default_set=True)
import bpy
bpy.ops.wm.open_mainfile(filepath=r'C:\Users\erons\OneDrive\Imagens\Documentos\ChatGPT\cidade fivem\personagens\traje_guarda\GUARDA_FIVEM.blend')
for m in bpy.data.materials:
 if m.name.startswith('GUARDA_'):
  print('M',m.name,[(n.name,n.sollumz_texture_name,n.image.name,list(n.image.size),n.image.filepath,n.texture_properties.embedded,len(n.image.packed_file.data) if n.image.packed_file else 0) for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image])
