"""Reproduce entrance/interior blockers with all installed DLC collision layers."""
from pathlib import Path
import json,sys
source=Path(__file__).with_name('verify_fit.py').read_text()
exec(source.split('routes={}')[0])
probes={
 'porta_principal':[[x,-12.9,-.8] for x in np.linspace(5.85,7.1,18)],
 'porta_sala_deck':[[-5.53,y,-.8] for y in np.linspace(-12.4,-13.6,18)],
 'sala_interna':[[-6.35,y,-.8] for y in np.linspace(-12.6,-5.8,35)],
 'cozinha_interna':[[11.35,y,-.8] for y in np.linspace(-10,-5.8,25)],
 'quarto_superior':[[10.5,y,2.808] for y in np.linspace(-12.5,-8,25)]
}
report={}
for name,points in probes.items():
 hits=[{'point':p,'objects':blockers(np.array(p))} for p in points]
 hits=[p for p in hits if p['objects']]
 report[name]={'sample_count':len(points),'blocked_samples':hits,'passed':not hits}
 print('DLC_PROBE',name,len(hits),'blocked;',hits[:2],flush=True)
stage='depois' if '--after' in sys.argv else 'antes'
(W/f'diagnostico_colisoes_dlc_{stage}.json').write_text(json.dumps({'probes':report,'files':len(list((W/'work/native').glob('*ch2_09b_[0-3].ybn')))},indent=2))
if stage=='depois':assert all(r['passed'] for r in report.values())
