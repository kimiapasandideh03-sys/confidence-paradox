"""Compile cross-study GEE estimates AND sample sizes from generated results."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from plot_style import TEAL, GREY
root=Path(__file__).resolve().parents[1]
res=root/'results'/'generated'
r=pd.read_csv(res/'rouault'/'rouault_gee_coefficients.csv',index_col=0)
rp=pd.read_csv(res/'rouault'/'rouault_participant_summary.csv')
a=pd.read_csv(res/'aguilarlleyda'/'results_summary.csv')
ap=pd.read_csv(res/'aguilarlleyda'/'subject_summary_col.csv')
k=pd.read_csv(res/'konishi'/'konishi_results_summary.csv')
a1=a.query("task == 'Color' and term == 'centered10'").iloc[0]
a2=a.query("task == 'Color' and term == 'mean10'").iloc[0]
k1=k.query("subset == 'motion_motion'").iloc[0]
rows=[
 dict(dataset='Rouault 2019',task='Dot numerosity',participants=len(rp),rated_decisions=int(rp.n_trials.sum()),
    within_coef=r.loc['within_10pp','estimate'],within_low=r.loc['within_10pp','ci_025'],within_high=r.loc['within_10pp','ci_975'],
    between_coef=r.loc['between_10pp','estimate'],between_low=r.loc['between_10pp','ci_025'],between_high=r.loc['between_10pp','ci_975']),
 dict(dataset='Aguilar-Lleyda 2018',task='Color discrimination',participants=len(ap),rated_decisions=int(ap.n.sum()),
    within_coef=a1.coef,within_low=a1.ci_lower,within_high=a1.ci_upper,
    between_coef=a2.coef,between_low=a2.ci_lower,between_high=a2.ci_upper),
 dict(dataset='Konishi 2019',task='Single-task motion',participants=int(k1.n_unique_participants),rated_decisions=int(k1.n_rows),
    within_coef=k1.within_10pp_logodds,within_low=k1.within_10pp_ci_lower,within_high=k1.within_10pp_ci_upper,
    between_coef=k1.between_10pp_logodds,between_low=k1.between_10pp_ci_lower,between_high=k1.between_10pp_ci_upper),
]
s=pd.DataFrame(rows)
assert (s.participants>2).all() and (s.rated_decisions>s.participants).all()
(root/'results').mkdir(exist_ok=True)
s.to_csv(root/'results'/'cross_study_primary_summary.csv',index=False)
(root/'figures').mkdir(exist_ok=True)
fig,ax=plt.subplots(figsize=(9.2,4.1));y=np.arange(len(s))[::-1]
v=s.within_coef.to_numpy();lo=s.within_low.to_numpy();hi=s.within_high.to_numpy()
ax.errorbar(v,y,xerr=[v-lo,hi-v],fmt='o',capsize=4,color=TEAL,markersize=7,elinewidth=1.7)
ax.axvline(0,color=GREY,linestyle='--',linewidth=1)
ax.set_yticks(y,['Rouault | dots','Aguilar-Lleyda | color','Konishi | motion'])
ax.set_xlabel('Within-person GEE log-odds per +10 pp confidence (95% robust CI)')
ax.set_title('Within-person confidence tracks accuracy in all three tasks')
ax.grid(axis='x',alpha=.16);fig.tight_layout()
fig.savefig(root/'figures'/'three_study_within_effects.png',dpi=220);plt.close(fig)
print('Generated cross-study summary from model result files:',len(s),'primary tasks')
