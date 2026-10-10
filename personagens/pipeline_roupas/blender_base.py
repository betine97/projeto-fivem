"""One-time background import; create an editable copy and protect originals."""
import hashlib
import json
import math
import sys
from pathlib import Path

import addon_utils
import bpy
from mathutils import Quaternion

base, config_file, output = map(Path, sys.argv[sys.argv.index('--')+1:])
cfg=json.loads(config_file.read_text(encoding='utf-8'))
root=config_file.parent.parents[1]
sys.path[:0]=[str(root/p) for p in cfg['native_dependencies']]+[cfg['sollumz']]
addon_utils.enable('Sollumz',default_set=True)
source=json.loads((base/'base.json').read_text(encoding='utf-8'))
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.sollumz.import_assets(directory=str(base/'source'),
    files=[{'name':Path(source['paths']['model']).name}],
    use_custom_settings=True,dwd_import_external_skeleton='FROM_DIR')
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
scene.render.fps=30


def collection(name):
    result=bpy.data.collections.new(name);scene.collection.children.link(result);return result


def fingerprint(mesh):
    values=[tuple(v.co) for v in mesh.vertices]
    values += [tuple(p.vertices) for p in mesh.polygons]
    values += [tuple(d.uv) for uv in mesh.uv_layers for d in uv.data]
    values += [tuple((g.group, g.weight) for g in v.groups) for v in mesh.vertices]
    return hashlib.sha256(repr(values).encode()).hexdigest()


def meshes_for(obj):
    if obj.type != 'MESH':return []
    meshes={obj.data}
    if hasattr(obj,'sz_lods'):
        meshes.update(lod.mesh for level in ('high','medium','low','very_low','very_high')
                      if (lod:=getattr(obj.sz_lods,level,None)) is not None and lod.mesh is not None)
    return list(meshes)


original=collection('00_BASE_ORIGINAL_NAO_EDITAR')
variant=collection('10_VARIACAO_TRABALHO')
collection('20_COMPONENTES_FIXOS');collection('30_COMPONENTES_MOVEIS')
collection('90_REFERENCIAS_NAO_EXPORTAR')
imported=list(bpy.data.objects)
original_meshes={mesh:fingerprint(mesh) for o in imported for mesh in meshes_for(o)}
mapped={}
for obj in imported:
    for old in list(obj.users_collection):old.objects.unlink(obj)
    original.objects.link(obj);obj.hide_select=True
    duplicate=obj.copy()
    if obj.data is not None:duplicate.data=obj.data.copy()
    duplicate.name='VAR_'+obj.name;duplicate.hide_select=False
    variant.objects.link(duplicate);mapped[obj]=duplicate
    if obj.type=='MESH' and hasattr(obj,'sz_lods'):
        # Copy all stored LOD meshes, not just the currently visible one.
        for level in ('high','medium','low','very_low','very_high'):
            old=getattr(obj.sz_lods,level,None);new=getattr(duplicate.sz_lods,level,None)
            if old is not None and new is not None and getattr(old,'mesh',None) is not None:
                new.mesh=duplicate.data if old.mesh==obj.data else old.mesh.copy()
for old,new in mapped.items():
    new.parent=mapped.get(old.parent)
    for mod in new.modifiers:
        if mod.type=='ARMATURE' and mod.object in mapped:mod.object=mapped[mod.object]
    if new.type=='MESH':
        for mesh in meshes_for(new):
            for index,material in enumerate(mesh.materials):
                if material:mesh.materials[index]=material.copy()
working_meshes={mesh for o in mapped.values() for mesh in meshes_for(o)}
if working_meshes.intersection(original_meshes):
    raise RuntimeError('A cópia de trabalho ainda compartilha malhas com os originais.')
original.hide_viewport=True;original.hide_render=True

texture_dir=base/'source'/'textures'
unresolved_textures=[]
for material in bpy.data.materials:
    if not material.node_tree:continue
    for node in material.node_tree.nodes:
        if node.type!='TEX_IMAGE':continue
        stem=(node.image.name if node.image else node.name).split('.')[0]
        texture=texture_dir/(stem+'.dds')
        if texture.is_file():
            node.image=bpy.data.images.load(str(texture),check_existing=True)
            node.image.pack()
        elif node.image:
            unresolved_textures.append({'material':material.name,'sampler':node.name,'texture':stem,
                                        'connected_in_preview':any(s.is_linked for s in node.outputs)})
for image in list(bpy.data.images):
    # The importer leaves placeholder image datablocks after actual DDS files are linked.
    if image.users == 0 and not image.packed_file:
        bpy.data.images.remove(image)
print('EXTERNAL_TEXTURE_REFERENCES',json.dumps(unresolved_textures))

rigs=[o for o in mapped.values() if o.type=='ARMATURE']
if not rigs or not any(b.name=='SKEL_Pelvis' for r in rigs for b in r.data.bones):
    raise RuntimeError('Rig externo nativo não foi resolvido. Não aceitar ossos UNK como substituição.')
pose_reports=[]
for rig in rigs:
    rig.animation_data_create();action=bpy.data.actions.new('QA_FLEXAO_'+rig.name);action.use_fake_user=True
    rig.animation_data.action=action
    tests={'SKEL_L_Thigh':(.35,(0,1,0)),'SKEL_R_Thigh':(-.20,(0,1,0)),
           'SKEL_L_Calf':(.65,(0,1,0)),'SKEL_R_Calf':(.35,(0,1,0)),
           'SKEL_L_UpperArm':(.35,(0,1,0)),'SKEL_R_Forearm':(.60,(0,1,0)),
           'SKEL_Spine1':(.15,(1,0,0)),'SKEL_L_Foot':(.25,(0,1,0))}
    for frame in (1,15,30):
        for name,(angle,axis) in tests.items():
            bone=rig.pose.bones.get(name)
            if bone:
                bone.rotation_mode='QUATERNION';bone.rotation_quaternion=Quaternion(axis,angle if frame==15 else 0)
                bone.keyframe_insert(data_path='rotation_quaternion',frame=frame,group=name)
    scene.frame_set(15);bpy.context.view_layer.update()
    graph=bpy.context.evaluated_depsgraph_get();maximum=0
    for obj in mapped.values():
        if obj.type!='MESH':continue
        evaluated=obj.evaluated_get(graph);mesh=evaluated.to_mesh()
        if len(mesh.vertices)==len(obj.data.vertices):
            maximum=max(maximum,max(((a.co-b.co).length for a,b in zip(mesh.vertices,obj.data.vertices)),default=0))
        evaluated.to_mesh_clear()
    pose_reports.append({'rig':rig.name,'bones':len(rig.data.bones),'test_action':action.name,'max_displacement_m':maximum})
    rig.animation_data.action=None
    for bone in rig.pose.bones:bone.matrix_basis.identity()
scene.frame_set(1)
for mesh, original_hash in original_meshes.items():
    if fingerprint(mesh)!=original_hash:
        raise RuntimeError('A malha original foi alterada pela preparação do Blender.')

text=bpy.data.texts.new('LEIA_ME_PIPELINE')
text.write('''Base original preservada e oculta em 00. Crie a variação em 10; componentes fixos em 20 e móveis em 30.
Frente -Y; esquerda do personagem +X; cima +Z; 1 unidade = 1 metro. Não alterar repouso ou estrutura do rig.
QA_FLEXAO fica arquivada. Verifique repouso e flexão; resultado ainda precisa de inspeção visual e teste FiveM.
Copie este arquivo para jobs/<nome>/<revisão>/work antes de editar. Não sobrescreva o cache.
Referências/câmeras/luzes e a coleção 00 não entram na exportação.
''')
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.wm.save_as_mainfile(filepath=str(output/'base.blend'))
(output/'blender.json').write_text(json.dumps({'ok':True,'original_meshes_unchanged':True,
    'original_mesh_count':len(original_meshes),'working_objects':len(mapped),
    'working_mesh_count':len(working_meshes),'all_lod_meshes_independent':True,
    'poses':pose_reports,'unresolved_external_textures':unresolved_textures,
    'in_game_validation':'pending'},indent=2),encoding='utf-8')
print('PIPELINE_BLENDER_BASE_OK',len(mapped),'objects; original mesh preserved')
