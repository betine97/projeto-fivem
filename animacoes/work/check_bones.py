import bpy
bpy.ops.wm.open_mainfile(filepath=r'C:\Users\erons\OneDrive\Imagens\Documentos\ChatGPT\cidade fivem\animacoes\combate_base.blend')
a=bpy.data.objects['a_m_y_business_01'];h=bpy.data.objects['hash_976FBF04']
print('MISSING',[(b.name,b.parent.name if b.parent else None) for b in h.data.bones if b.name not in a.data.bones])
print('GUN',[(b.name,tuple(b.head_local)) for b in bpy.data.objects['w_ar_carbinerifle'].data.bones])
