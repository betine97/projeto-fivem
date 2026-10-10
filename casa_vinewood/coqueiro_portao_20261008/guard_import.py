from pathlib import Path
p=Path(__file__).with_name('diagnose.py');s=p.read_text();head,body=s.split('rows=[]',1)
p.write_text(head+'def run():\n'+''.join(' '+line+'\n' for line in ('rows=[]'+body).splitlines())+'\nif __name__=="__main__":run()\n')
