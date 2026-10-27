"""Confidence Paradox: Aguilar-Lleyda et al. 2018, exploratory study-2 analysis.
Run: python analyze_study2.py --input data_AguilarLleyda_2018.csv
No claims of preregistration; focus on within/between effects with clustered inference.
"""
from pathlib import Path
import argparse
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.genmod.cov_struct import Exchangeable
from statsmodels.genmod.families import Binomial
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from plot_style import NAVY, TEAL, ORANGE, GREY

p = argparse.ArgumentParser()
p.add_argument('--input', type=Path, default=Path('data_AguilarLleyda_2018.csv'))
p.add_argument('--outdir', type=Path, default=Path('results'))
p.add_argument('--cluster-bootstrap-reps', type=int, default=300, help='Color GEE participant-cluster bootstrap; 0 skips')
args = p.parse_args()
args.outdir.mkdir(parents=True, exist_ok=True)
df = pd.read_csv(args.input)
assert df['Subj_idx'].nunique()==28
assert (df.groupby('Subj_idx').size()==400).all()

rng = np.random.default_rng(2026)
results=[]
for task, code in [('Color','col'),('Letter','let')]:
    data=df[['Subj_idx',f'Confidence_{code}',f'Accuracy_{code}',f'Difficulty_{code}']].copy()
    data.columns=['participant','confidence','accuracy','difficulty']
    data=data.dropna().copy()
    assert data['accuracy'].isin([0,1]).all()
    assert data['difficulty'].isin([60,90]).all()
    means=data.groupby('participant')['confidence'].transform('mean')
    data['centered10']=(data['confidence']-means)/10
    data['mean10']=(means-data['confidence'].mean())/10
    data['easy']=(data['difficulty']==90).astype(int)
    sub=data.groupby('participant').agg(mean_confidence=('confidence','mean'),mean_accuracy=('accuracy','mean'),n=('accuracy','size'))
    r=sub['mean_confidence'].corr(sub['mean_accuracy'])
    xy=sub[['mean_confidence','mean_accuracy']].to_numpy()
    bs=[]
    for i in range(5000):
        tmp=xy[rng.integers(len(xy),size=len(xy))]
        if tmp[:,0].std()>1e-12 and tmp[:,1].std()>1e-12:
            bs.append(np.corrcoef(tmp[:,0],tmp[:,1])[0,1])
    bounds=np.percentile(bs,[2.5,97.5])
    x=sm.add_constant(data[['centered10','mean10','easy']])
    mod=sm.GEE(data['accuracy'],x,groups=data['participant'],family=Binomial(),cov_struct=Exchangeable())
    fit=mod.fit(maxiter=100)
    ci=fit.conf_int()
    print(f'\n{task}: n={len(data)}, n_participants={len(sub)}, confmean={data.confidence.mean():.4f}, accuracy={data.accuracy.mean():.4f}')
    print(f'Between Pearson r={r:.4f} bootstrap percentile 95% [{bounds[0]:.4f},{bounds[1]:.4f}]')
    print('GEE log odds coefficients (per +10 confidence pts for within/between):')
    print(pd.DataFrame({'coef':fit.params,'lower':ci[0],'upper':ci[1],'p':fit.pvalues}).round(5).to_string())
    for term in ['centered10','mean10','easy']:
        results.append({'task':task,'model':'GEE logistic clustered by participant','term':term,'coef':fit.params[term], 'ci_lower':ci.loc[term,0],'ci_upper':ci.loc[term,1], 'p_value':fit.pvalues[term], 'odds_ratio':np.exp(fit.params[term])})
    results.append({'task':task,'model':'Between-person Pearson + participant bootstrap','term':'r','coef':r,'ci_lower':bounds[0],'ci_upper':bounds[1],'p_value':np.nan,'odds_ratio':np.nan})
    # The difference is assessed in the SAME GEE with the full coefficient covariance.
    contrast=np.zeros(len(fit.params)); names=list(fit.params.index)
    contrast[names.index('centered10')]=1
    contrast[names.index('mean10')]=-1
    contrast_test=fit.t_test(contrast)
    ci_diff=np.asarray(contrast_test.conf_int()).ravel()
    results.append({'task':task,'model':'GEE within-minus-between joint contrast','term':'within_minus_between',
        'coef':float(np.asarray(contrast_test.effect).ravel()[0]),
        'ci_lower':ci_diff[0],'ci_upper':ci_diff[1],
        'p_value':float(np.asarray(contrast_test.pvalue).ravel()[0]),'odds_ratio':np.nan})
    sub.to_csv(args.outdir/f'subject_summary_{code}.csv')
    if code=='col' and args.cluster_bootstrap_reps:
        # Whole participants resampled WITH replacement; duplicates must have new
        # cluster identifiers (otherwise a participant copied twice is merged).
        cluster_ids=np.array(sorted(data.participant.unique()))
        source={pid:data[data.participant==pid].copy() for pid in cluster_ids}
        bootstrap_rng=np.random.default_rng(20261026)
        draws=[]
        for rep in range(args.cluster_bootstrap_reps):
            ids=bootstrap_rng.choice(cluster_ids,size=len(cluster_ids),replace=True)
            pieces=[]
            for new_id,old_id in enumerate(ids):
                part=source[old_id].copy()
                part['participant']=new_id
                pieces.append(part)
            sample=pd.concat(pieces,ignore_index=True)
            # Within-person predictor retains each selected original participant's
            # person mean; between-person slope is invariant to grand-mean shift.
            xboot=sm.add_constant(sample[['centered10','mean10','easy']])
            try:
                fitb=sm.GEE(sample.accuracy,xboot,groups=sample.participant,
                            family=Binomial(),cov_struct=Exchangeable()).fit(maxiter=100)
                if np.isfinite(fitb.params[['centered10','mean10']]).all():
                    draws.append({'within_10pp':fitb.params['centered10'],
                                  'between_10pp':fitb.params['mean10'],
                                  'within_minus_between':fitb.params['centered10']-fitb.params['mean10']})
            except (ValueError, np.linalg.LinAlgError):
                continue
        draws=pd.DataFrame(draws)
        draws.to_csv(args.outdir/'color_cluster_bootstrap_draws.csv',index=False)
        if len(draws)<0.9*args.cluster_bootstrap_reps:
            raise RuntimeError(f'Only {len(draws)}/{args.cluster_bootstrap_reps} valid Aguilar cluster resamples')
        intervals=[]
        for term in draws.columns:
            limits=np.quantile(draws[term],[.025,.975])
            intervals.append({'term':term,'bootstrap_requested':args.cluster_bootstrap_reps,
                              'bootstrap_valid':len(draws),'ci_lower':limits[0],
                              'ci_upper':limits[1], 'method':'Percentile participant bootstrap; exploratory; 28 clusters'})
        pd.DataFrame(intervals).to_csv(args.outdir/'color_cluster_bootstrap_intervals.csv',index=False)
    # scatter shows means in percentages, calibration line of equality
    fig,ax=plt.subplots(figsize=(7.6,5.4))
    over=sub.mean_confidence>100*sub.mean_accuracy
    ax.scatter(sub.loc[over,'mean_confidence'],100*sub.loc[over,'mean_accuracy'],label='Overconfident',color=ORANGE,s=37,alpha=.8)
    ax.scatter(sub.loc[~over,'mean_confidence'],100*sub.loc[~over,'mean_accuracy'],label='Under / equal',color=TEAL,s=37,alpha=.8)
    ax.plot([50,100],[50,100],'k--',lw=1.3,label='Perfect calibration')
    ax.set(xlabel='Mean reported confidence (%)',ylabel='Mean accuracy (%)',title=f'{task}: many participants report greater confidence than accuracy')
    ax.set_xlim(49,101)
    ax.set_ylim(35,101)
    ax.grid(alpha=.18)
    ax.legend()
    fig.tight_layout()
    fig.savefig(args.outdir/f'calibration_{code}.png',dpi=180)
    plt.close(fig)

pd.DataFrame(results).to_csv(args.outdir/'results_summary.csv',index=False)
print('\nSaved outputs to',args.outdir)
