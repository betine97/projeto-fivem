import bpy

scene = bpy.context.scene
scene.cycles.use_preview_denoising = True
scene.cycles.preview_samples = 128
scene.cycles.preview_denoising_start_sample = 16
scene.cycles.use_denoising = True
scene.cycles.samples = 128
if hasattr(scene.cycles, 'preview_adaptive_threshold'):
    scene.cycles.preview_adaptive_threshold = 0.03
print('Preview: 128 amostras e denoise ativado. Materiais preservados.')
