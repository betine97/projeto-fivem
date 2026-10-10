from pathlib import Path
p=Path(__file__).with_name('build_interior.py')
s=p.read_text(encoding='utf-8')
s=s.split('# Workbench overview')[0]+s[s.index('# Default editable viewport'):]
exec(compile(s,str(p),'exec'),{'__file__':str(p),'__name__':'__main__'})
