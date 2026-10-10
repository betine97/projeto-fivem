import bpy,sys,addon_utils
from pathlib import Path
P=Path(__file__).resolve().parent;W=P.parent;R=W.parent
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps',r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/sollumz']
bpy.ops.wm.read_factory_settings(use_empty=True);addon_utils.enable('Sollumz',default_set=True)
from szio.gta5 import try_load_asset,AssetTarget,AssetFormat,AssetVersion
from Sollumz.ydr.ydrimport import create_drawable
from Sollumz.iecontext import ImportContext,ImportSettings,import_context_scope
f=P/'stream/mansao_tapete_urso.ydr'
with import_context_scope(ImportContext(f.stem,AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),W/'work/textures',ImportSettings(False,False,False,False))):root=create_drawable(try_load_asset(f),name=f.stem)
bpy.context.scene['revision']='Tapete: colisao baixa da silhueta inteira e cabeca preservada; malha/UV/texturas originais'
bpy.ops.wm.save_as_mainfile(filepath=str(P/'tapete_urso_render_corrigido.blend'),compress=True)
print('RUG_EDITABLE_READY',flush=True)
