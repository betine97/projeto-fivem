import bpy
from pathlib import Path
p=Path(__file__).resolve().parent.parent
t=bpy.data.texts['LEIA-ME | INTERIOR INICIAL']
s=t.as_string().replace('Shift acelera, roda do mouse ajusta velocidade, Esc encerra.','Roda do mouse ajusta velocidade; Shift reduz para precisao. Enter confirma; Esc cancela.')
t.clear();t.write(s)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'mansao_interior_inicial.blend'))
