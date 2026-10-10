import bpy
from pathlib import Path

root=Path(__file__).resolve().parents[2]
bpy.ops.import_scene.gltf(filepath=r'C:\Users\erons\Downloads\Meshy_AI_cleanroom_containment_1004173529_image-to-3d-texture.glb')
out=root/'laboratorio_fivem/containment_source';out.mkdir(exist_ok=True)
for name in ('Image_0','Image_1','Image_2'):
 image=bpy.data.images[name]
 image.filepath_raw=str(out/(name+'.png'))
 image.file_format='PNG'
 image.save()
 print('EXTRACTED',name,tuple(image.size),flush=True)
for link in bpy.data.materials['Material_0'].node_tree.links:
 print('LINK',link.from_node.name,link.from_socket.name,'->',link.to_node.name,link.to_socket.name,flush=True)
