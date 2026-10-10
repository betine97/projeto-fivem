import bpy, math
from mathutils import Matrix

def forward_action(rig, source):
    """Bake the observed 180-degree facing offset into every exported frame.

    Rotate the complete root transform in armature space, preserving the prone
    root's pitch. Do not replace its quaternion or rotate the ped at runtime.
    """
    rig.animation_data.action=source
    root=rig.pose.bones['SKEL_ROOT']
    turn=Matrix.Rotation(math.pi,4,'Z')
    samples=[]
    last=int(source.frame_range[1])
    for frame in range(1,last+1):
        bpy.context.scene.frame_set(frame);bpy.context.view_layer.update()
        samples.append(turn@root.matrix.copy())
    result=source.copy();result.name=source.name+'_forward_v2'
    rig.animation_data.action=result
    for frame,matrix in enumerate(samples,1):
        bpy.context.scene.frame_set(frame)
        root.matrix=matrix
        root.keyframe_insert(data_path='location',frame=frame)
        root.keyframe_insert(data_path='rotation_quaternion',frame=frame)
    for frame,expected in enumerate(samples,1):
        bpy.context.scene.frame_set(frame);bpy.context.view_layer.update()
        assert max(abs(root.matrix[i][j]-expected[i][j]) for i in range(4) for j in range(4))<0.0001
    return result
