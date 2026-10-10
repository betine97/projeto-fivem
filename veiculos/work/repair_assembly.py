import bpy,sys,math,bmesh
from pathlib import Path
root=Path(__file__).resolve().parent.parent
sys.path[:0]=[r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps',r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\sollumz']
import addon_utils
addon_utils.enable('Sollumz',default_set=True)
from Sollumz.sollumz_properties import LODLevel
from Sollumz.tools.meshhelper import mesh_add_missing_uv_maps,mesh_add_missing_color_attrs
from szio.rpf import open_rpf
from szio.gta5 import try_load_asset

def recover_images():
    archive=open_rpf(r'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V\x64e.rpf').open_nested('levels/gta5/vehicles.rpf')
    candidates=[n for n in archive.list_dir('') if n.endswith('.ytd') and any(s in n for s in ['vehshare','bobcat','rebel','vehinterior'])]
    print('TEXTURE_DICTIONARIES',candidates)
    for name in candidates:
        path=root/'work/assets'/name
        path.write_bytes(archive.read_bytes(name))
        txd=try_load_asset(path)
        for name,t in txd.textures.items():
            if t.data:
                with t.data.open() as data:(root/'work'/(name+'.dds')).write_bytes(data.read())
        print('RECOVERED_TEXTURES',path.name,len(txd.textures))

def repair_assembly():
    rig=bpy.data.objects['sertao']
    for c in rig.pose.bones['boot'].constraints:
        if c.type=='LIMIT_ROTATION':c.min_x=0;c.max_x=math.pi/2
    for name in ['taillight_l','taillight_r','indicator_lr','indicator_rr']:
        lamp=bpy.data.objects.get(name)
        if not lamp or lamp.get('rear_repaired'):continue
        visited=set()
        for level in LODLevel:
            mesh=lamp.sz_lods.get_lod(level).mesh
            if mesh is None or mesh.name in visited:continue
            visited.add(mesh.name)
            for v in mesh.vertices:v.co.y-=.085
            for i in range(len(mesh.materials)):mesh.materials[i]=bpy.data.materials.get('sabreturbo_lights_glass') or mesh.materials[i]
        lamp['rear_repaired']=True
    for side in [-1,1]:
        name='BED_WHEEL_TUB_'+str(side)
        if bpy.data.objects.get(name):continue
        template=bpy.data.objects['BED_FRONT_WALL']
        mesh=bpy.data.meshes.new(name)
        bm=bmesh.new();bmesh.ops.create_cube(bm,size=1)
        for v in bm.verts:
            v.co.x=v.co.x*.25+side*.69;v.co.y=v.co.y*1.08-1.307;v.co.z=v.co.z*.205+.4525
        bm.to_mesh(mesh);bm.free()
        mesh.materials.append(template.data.materials[0])
        o=template.copy();o.name=name;o.data=mesh;bpy.context.collection.objects.link(o)
        mesh_add_missing_uv_maps(mesh);mesh_add_missing_color_attrs(mesh)
        if not mesh.uv_layers.get('UVMap 0'):mesh.uv_layers.new(name='UVMap 0')
        for layer in mesh.color_attributes:
            for d in layer.data:d.color=(1,1,1,1)
        for p in mesh.polygons:
            axes=[i for i in range(3) if i!=max(range(3),key=lambda j:abs(p.normal[j]))]
            for li in p.loop_indices:
                co=mesh.vertices[mesh.loops[li].vertex_index].co
                mesh.uv_layers['UVMap 0'].data[li].uv=(co[axes[0]]*.68+.137,co[axes[1]]*.68+.271)
        o.vertex_groups.clear();g=o.vertex_groups.new(name='chassis');g.add(list(range(len(mesh.vertices))),1,'REPLACE')
        bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
        mod=o.modifiers.new('Wheel tub rolled corner','BEVEL');mod.width=.035;mod.segments=3;bpy.ops.object.modifier_apply(modifier=mod.name)
        for level in [LODLevel.VERYHIGH,LODLevel.HIGH,LODLevel.MEDIUM,LODLevel.LOW]:o.sz_lods.get_lod(level).mesh=o.data
    for img in bpy.data.images:
        filename=Path(bpy.path.abspath(img.filepath)).name
        candidate=root/'work'/filename
        if candidate.exists() and img.source=='FILE':img.filepath=str(candidate);img.reload()
        elif img.name.startswith('script_rt_dials'):
            # Game supplies the runtime dial render target; use a neutral studio fallback.
            img.filepath=str(root/'work/black.dds');img.reload()
    print('ASSEMBLY_REPAIRED')

if __name__=='__main__':
    recover_images()
    for file in ['sertao.blend','sertao_studio.blend']:
        bpy.ops.wm.open_mainfile(filepath=str(root/file));repair_assembly();bpy.ops.wm.save_as_mainfile(filepath=str(root/file))
