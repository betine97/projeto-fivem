from pathlib import Path

source = Path(__file__).resolve().parent.parent / 'modelo' / 'verificar_blender.py'
code = source.read_text(encoding='utf-8').replace("'castelo_rockford.blend'", "'castelo_rockford_evoluido.blend'")
exec(compile(code, str(source), 'exec'))
