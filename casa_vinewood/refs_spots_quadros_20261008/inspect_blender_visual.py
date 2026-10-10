import bpy
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(P.parent/'mansao_spots_quadros.blend'))
for name in ['ref_art_2','ref_lens','ref_reflector']:
    m=bpy.data.materials[name]
    print('MATERIAL',name)
    for n in m.node_tree.nodes:
        if n.type in ['TEX_IMAGE','BSDF_PRINCIPLED','EMISSION','UVMAP']:print('NODE',n.name,n.type,[(x.name,str(x.default_value)) for x in n.inputs if not x.is_linked],n.image.name if n.type=='TEX_IMAGE' and n.image else '',getattr(n,'uv_map',''))
    print('LINKS',[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in m.node_tree.links])
obj=next(o for o in bpy.data.objects['Quadro geometrico escritorio'].children if 'tela' in o.name);print('CANVAS_UV',[(u.name,len(u.data)) for u in obj.data.uv_layers])
hit,location,normal,index,obj,_=bpy.context.scene.ray_cast(bpy.context.evaluated_depsgraph_get(),Vector((10,-1.5,1.15)),Vector((0,3.739,-.2)).normalized(),distance=4)
print('HALL_CAM_RAY',hit,obj.name if hit else '',location)
