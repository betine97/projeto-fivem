"""Make a native rest-skeleton working copy with non-exported IK controls."""
import bpy, json, sys
from pathlib import Path
from mathutils import Matrix

HERE=Path(__file__).resolve().parent
DEPS=Path(r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
sys.path[:0]=[str(DEPS),str(DEPS.parent/'sollumz')]
import addon_utils
addon_utils.enable('Sollumz',default_set=True)
bpy.ops.wm.open_mainfile(filepath=str(HERE/'sources/ajoelhado_ar.blend'))
rig=bpy.data.objects['GTA_Personagem_Rig']
rig.animation_data_clear()
for b in rig.pose.bones:
    b.matrix_basis=Matrix.Identity(4)
rig.data.pose_position='POSE'
bpy.context.view_layer.update()
controls=bpy.data.collections.new('CONTROLES_IK_NAO_EXPORTAR')
bpy.context.scene.collection.children.link(controls)

def control(name,matrix,shape='SPHERE',size=.075):
    obj=bpy.data.objects.new(name,None)
    controls.objects.link(obj)
    obj.matrix_world=matrix
    obj.empty_display_type=shape
    obj.empty_display_size=size
    obj.show_in_front=True
    obj['export']=False
    return obj

root=rig.pose.bones['SKEL_ROOT']
root_control=control('CTRL_ROOT',rig.matrix_world@root.matrix,'CUBE',.13)
c=root.constraints.new('COPY_TRANSFORMS');c.name='Controle root (bake antes de exportar)';c.target=root_control
c.owner_space='WORLD';c.target_space='WORLD'
chest=rig.pose.bones['SKEL_Spine2']
chest_control=control('CTRL_TORAX',rig.matrix_world@chest.matrix,'CIRCLE',.16)
c=chest.constraints.new('COPY_ROTATION');c.target=chest_control;c.owner_space='WORLD';c.target_space='WORLD'
for side in ('L','R'):
    for kind,parts in [('HAND',('UpperArm','Forearm','Hand')),('FOOT',('Thigh','Calf','Foot'))]:
        upper,lower,end=[rig.pose.bones[f'SKEL_{side}_{p}'] for p in parts]
        target=control(f'CTRL_{side}_{kind}',rig.matrix_world@end.matrix,'CUBE')
        target['IK']=0.0
        target.id_properties_ui('IK').update(min=0.0,max=1.0,description='0=FK nativo; 1=controle IK auxiliar')
        lower_world=rig.matrix_world@lower.head
        direction=(lower.head-upper.head).cross(end.head-lower.head)
        # Straight rest limbs need a deliberate, editable pole direction.
        pole_matrix=Matrix.Translation(lower_world)
        pole_matrix.translation.y-=.40 if kind=='FOOT' else .25
        pole=control(f'POLE_{side}_{kind}',pole_matrix,'SPHERE',.045)
        # GTA native axes/tails do not describe a Blender IK chain. Solve with
        # separate bones aligned to the physical joints, then correct rest axes.
        data=bpy.data.armatures.new(f'SOLVER_{side}_{kind}')
        solver=bpy.data.objects.new(data.name,data);controls.objects.link(solver)
        solver.matrix_world=rig.matrix_world;solver.show_in_front=True
        solver.hide_render=True;solver['export']=False
        bpy.ops.object.select_all(action='DESELECT');solver.select_set(True);bpy.context.view_layer.objects.active=solver
        bpy.ops.object.mode_set(mode='EDIT')
        a=data.edit_bones.new('upper');a.head=upper.head;a.tail=lower.head
        b=data.edit_bones.new('lower');b.head=lower.head;b.tail=end.head;b.parent=a;b.use_connect=True
        bpy.ops.object.mode_set(mode='OBJECT');bpy.context.view_layer.update()
        parent=rig.pose.bones['SKEL_'+side+'_Clavicle' if kind=='HAND' else 'SKEL_Pelvis']
        anchor=solver.constraints.new('CHILD_OF');anchor.target=rig;anchor.subtarget=parent.name
        anchor.inverse_matrix=(rig.matrix_world@parent.matrix).inverted()
        bpy.context.view_layer.update()
        for native,proxyname in [(upper,'upper'),(lower,'lower')]:
            proxy=solver.pose.bones[proxyname]
            helper=control(f'AXIS_{side}_{native.name}',rig.matrix_world@native.matrix,'PLAIN_AXES',.025)
            follow=helper.constraints.new('CHILD_OF');follow.target=solver;follow.subtarget=proxyname
            follow.inverse_matrix=(solver.matrix_world@proxy.matrix).inverted()
            c=native.constraints.new('COPY_ROTATION');c.name='IK auxiliar - eixos GTA';c.target=helper;c.owner_space='WORLD';c.target_space='WORLD'
            driver=c.driver_add('influence').driver
            variable=driver.variables.new();variable.name='ik';variable.type='SINGLE_PROP';variable.targets[0].id=target;variable.targets[0].data_path='["IK"]';driver.expression='ik'
        c=solver.pose.bones['lower'].constraints.new('IK');c.target=target;c.pole_target=pole;c.chain_count=2;c.use_stretch=False
        c=end.constraints.new('COPY_ROTATION');c.name='Orientacao alvo';c.target=target;c.owner_space='WORLD';c.target_space='WORLD'
        driver=c.driver_add('influence').driver
        variable=driver.variables.new();variable.name='ik';variable.type='SINGLE_PROP';variable.targets[0].id=target;variable.targets[0].data_path='["IK"]';driver.expression='ik'
        bpy.context.view_layer.update()
rig['pipeline']='Controle por IK opcional; FK/dedos/face preservados; exportar somente o rig nativo com bake visual'
rig['native_rest_preserved']=True
note=bpy.data.texts.get('LEIA-ME') or bpy.data.texts.new('LEIA-ME')
note.clear()
note.write('COPIA DE TRABALHO DO ESQUELETO GTA - 98 ossos nativos.\nNao alterar nomes, tags, parentesco, escala ou rest pose.\nCTRL_ROOT move o corpo; CTRL_TORAX orienta o torax.\nIK de maos/pes: propriedade personalizada IK no controle. 0=FK; 1=IK auxiliar. Ajustar pole conforme a pose.\nSOLVER_* calcula IK nos eixos Blender, AXIS_* converte para os eixos GTA sem mudar os ossos originais.\nDedos e face usam FK. O exportador faz bake visual para um rig separado; controles nao entram no YCD.\nEsta copia nao substitui o personagem dentro do jogo.\n')
bpy.context.scene.frame_start=1;bpy.context.scene.frame_end=67
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':
        area.spaces.active.region_3d.view_perspective='PERSP'
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'esqueleto_trabalho.blend'))
audit={'native_bones':[{'name':b.name,'tag':b.bone_properties.tag,'parent':b.parent.name if b.parent else None,'rest':[list(row) for row in b.matrix_local]} for b in rig.data.bones],
       'controls':[o.name for o in controls.objects], 'native_rest_preserved':True, 'game_tested':False}
(HERE/'reports/skeleton.json').write_text(json.dumps(audit,indent=2),encoding='utf8')
print('NATIVE_RIG_TEMPLATE_OK',len(rig.data.bones))
