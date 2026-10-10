exec(compile((__import__('pathlib').Path(__file__).parent/'probe.py').read_text().split('names=')[0],__file__,'exec'))
for name in ['head_000_r','uppr_015_r','lowr_014_r','feet_005_r']:
 bpy.ops.sollumz.import_assets(directory=str(root/'source'),files=[{'name':name+'.ydd'}],use_custom_settings=True,dwd_import_external_skeleton='FROM_DIR')
for o in bpy.data.objects:
 print('OBJ',o.name,o.type,'parent',o.parent.name if o.parent else None)
 if o.type=='MESH':
  print(' LODS',str(o.sz_lods),[(p.identifier,str(getattr(o.sz_lods,p.identifier))[:400]) for p in o.sz_lods.bl_rna.properties if p.identifier!='rna_type'])
  print(' MODS',[(m.type,m.object.name if m.type=='ARMATURE' and m.object else '') for m in o.modifiers])
 if o.type=='ARMATURE':print('RIG',len(o.data.bones),[(b.name,list(b.head_local)) for b in o.data.bones if b.name.startswith('SKEL_')])
for m in bpy.data.materials:
 if m.node_tree:
  print('MAT',m.name,[(n.name,n.image.name if n.image else None) for n in m.node_tree.nodes if n.type=='TEX_IMAGE'])
from szio.gta5 import try_load_asset
for pattern in ['head_diff_000_a*','uppr_diff_015_a*','lowr_diff_014_a*','feet_diff_005_a*']:
 for p in (root/'source').glob(pattern):
  a=try_load_asset(p);print('YTD',p.name,list(a.textures))
bpy.ops.wm.save_as_mainfile(filepath=str(root/'work/imported.blend'))
