"""Render actual single drawable candidates using their stock diffuse textures."""
import sys, json, bpy, addon_utils
from pathlib import Path
from mathutils import Vector
OUT = Path(__file__).resolve().parent
sys.path[:0] = [r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps', r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/sollumz']
addon_utils.enable('Sollumz', default_set=True)
from szio.gta5 import try_load_asset, AssetTarget, AssetFormat, AssetVersion
from Sollumz.ydr.ydrimport import create_drawable
from Sollumz.iecontext import ImportContext, ImportSettings, import_context_scope
PREVIEWS = OUT/'previews'; PREVIEWS.mkdir(exist_ok=True)
rows = json.loads((OUT/'candidatos.json').read_text(encoding='utf-8'))
s = bpy.context.scene
s.render.engine = 'BLENDER_WORKBENCH'
s.display.shading.light = 'STUDIO'
s.display.shading.color_type = 'TEXTURE'
s.display.shading.show_shadows = True
s.display.shading.show_cavity = True
s.display.shading.cavity_type = 'BOTH'
s.display.shading.background_type = 'WORLD'
s.world.color = (.16,.18,.19)
s.render.resolution_x = 900; s.render.resolution_y = 650; s.render.resolution_percentage = 100
s.render.image_settings.file_format = 'PNG'
for row in rows:
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    f = OUT/'native'/(row['model']+'.ydr')
    try:
        asset = try_load_asset(f)
        with import_context_scope(ImportContext(f.stem, AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8), OUT/'textures', ImportSettings(False,False,False,False))):
            obj = create_drawable(asset, name=f.stem)
        for m in bpy.data.materials:
            if not m.use_nodes: continue
            for node in m.node_tree.nodes:
                if node.type=='TEX_IMAGE' and node.image:
                    image_name = node.image.name.rsplit('.',1)[0] if node.image.name.rsplit('.',1)[-1].isdigit() else node.image.name
                    p = OUT/'textures'/(image_name+'.dds')
                    if p.exists(): node.image = bpy.data.images.load(str(p),check_existing=True)
        bpy.context.view_layer.update()
        meshes = [x for x in [obj,*obj.children_recursive] if x.type=='MESH']
        verts = [x.matrix_world@v.co for x in meshes for v in x.data.vertices]
        lo = Vector(tuple(min(v[i] for v in verts) for i in range(3)))
        hi = Vector(tuple(max(v[i] for v in verts) for i in range(3)))
        center = (lo+hi)/2; size = max(hi-lo)
        row['dimensions_m'] = [round(x,2) for x in hi-lo]
        row['triangles'] = sum(sum(len(p.vertices)-2 for p in x.data.polygons) for x in meshes)
        for label, direction in [('frente',(1,-1,.65)),('verso',(-1,1,.65))]:
            bpy.ops.object.camera_add(location=center+Vector(direction)*size)
            camera=bpy.context.object; camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler()
            camera.data.type='ORTHO'; camera.data.ortho_scale=size*1.35; s.camera=camera
            target=PREVIEWS/(f.stem+'_'+label+'.png')
            s.render.filepath=str(target); bpy.ops.render.render(write_still=True)
            row['image_'+label] = 'previews/'+target.name
        print('RENDERED', f.stem, row['dimensions_m'], flush=True)
    except Exception as ex:
        row['error'] = str(ex); print('RENDER_ERROR',f.stem,str(ex),flush=True)
(OUT/'candidatos_renderizados.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
print('PREVIEWS_READY',flush=True)
