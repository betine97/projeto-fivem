"""Keep game shader highlights restrained, with texture-driven specular variation."""
import bpy,sys
from pathlib import Path
root=Path(__file__).resolve().parent.parent
sys.path[:0]=[r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps',r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\sollumz']
import addon_utils
addon_utils.enable('Sollumz',default_set=True)
from Sollumz.ydr.shader_materials import create_shader

def apply_finish():
    replacements={}
    for name in ['MILITARY_OLIVE_BODY','sertao_grade_textura','sertao_caixa_municao_textura']:
        old=bpy.data.materials.get(name)
        if not old:continue
        new=create_shader('spec.sps');new.name=name+'_GAME_SPEC'
        texture=old.node_tree.nodes['DiffuseSampler'].image
        for slot in ['DiffuseSampler','SpecSampler']:
            node=new.node_tree.nodes.get(slot)
            if node:node.image=texture;node.texture_properties.embedded=True
        for key,value in [('specularIntensityMult',.16),('specularFalloffMult',150.0)]:
            node=new.node_tree.nodes.get(key)
            if node:node.set_float(value)
        replacements[old]=new
    for mesh in bpy.data.meshes:
        for i,mat in enumerate(mesh.materials):
            if mat in replacements:mesh.materials[i]=replacements[mat]
    for mat in bpy.data.materials:
        if not mat.name.startswith('SERTAO_WHEEL_'):continue
        for key,value in [('specularIntensityMult',.06),('specularFalloffMult',90.0)]:
            node=mat.node_tree.nodes.get(key)
            if node:node.set_float(value)
    print('GAME_MATERIAL_FINISH_OK',len(replacements))

if __name__=='__main__':
    bpy.ops.wm.open_mainfile(filepath=str(root/'sertao.blend'))
    apply_finish()
    bpy.ops.wm.save_as_mainfile(filepath=str(root/'sertao.blend'))
