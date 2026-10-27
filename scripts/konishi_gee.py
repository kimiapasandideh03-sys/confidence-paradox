"""The Confidence Paradox — Konishi et al. (2019), held-out third dataset.

Reproduce:
    python analyze_konishi.py --input data_Konishi_2019.csv --out results

Primary analysis: single-task motion (held-out test of positive within-person
confidence–accuracy association). Color single task and the two dual-task
outcomes are additional exploratory/sensitivity analyses.

Models: population-average logistic GEE, working-independent association and
participant-clustered robust (sandwich) SEs. Four experiments are represented
by fixed effects; person IDs are retained across repeat experimental sessions.
This is NOT a random-effects GLMM or a registered preregistration.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from plot_style import NAVY, TEAL, ORANGE, GREY
import statsmodels.api as sm
import statsmodels.formula.api as smf


def prepare(df, condition, dimension):
    dim = 'Motion' if dimension == 'Motion' else 'Color'
    difficulty = 'Coherence_Motion' if dim == 'Motion' else 'Difficulty_Color'
    columns = ['Subj_idx', 'exp', 'task', f'Accuracy_{dim}', f'Confidence_{dim}', difficulty]
    data = df.loc[df.task == condition, columns].copy()
    data = data.rename(columns={f'Accuracy_{dim}':'accuracy', f'Confidence_{dim}':'confidence',difficulty:'difficulty'})
    data = data.dropna(subset=['Subj_idx','exp','accuracy','confidence','difficulty'])
    assert data.accuracy.isin([0,1]).all(), 'Accuracy must be binary'
    assert data.confidence.between(50,100).all(), 'Confidence scale unexpected'
    assert data.Subj_idx.nunique()>2
    # One unit = a ten percentage-point change in confidence.
    person_mean = data.groupby('Subj_idx')['confidence'].transform('mean')
    data['within_10pp'] = (data['confidence']-person_mean)/10.
    data['between_10pp'] = (person_mean-person_mean.mean())/10.
    # Difficulty parameters have different units across experiments; standardize within exp.
    data['difficulty_z'] = data.groupby('exp')['difficulty'].transform(
        lambda v:(v-v.mean())/v.std() if v.std()>1.e-10 else v*0.
    )
    return data


def correlation_ci(participant_summary, rng, reps=5000):
    xy = participant_summary[['mean_confidence','mean_accuracy']].to_numpy()
    point = np.corrcoef(xy[:,0],xy[:,1])[0,1]
    draws = []
    n = len(xy)
    for _ in range(reps):
        boot = xy[rng.integers(0,n,size=n)]
        if boot[:,0].std()>1e-12 and boot[:,1].std()>1e-12:
            draws.append(np.corrcoef(boot[:,0],boot[:,1])[0,1])
    lo,hi = np.percentile(draws,[2.5,97.5])
    return point, lo, hi


def run(df, condition, dimension, rng, outdir):
    data = prepare(df,condition,dimension)
    label = f'{condition}_{dimension.lower()}'
    participants = data.groupby('Subj_idx').agg(
        mean_confidence=('confidence','mean'),
        mean_accuracy=('accuracy','mean'),
        n_trials=('accuracy','size')
    )
    participants['confidence_gap_pp'] = participants.mean_confidence - 100*participants.mean_accuracy
    participants.to_csv(outdir/f'participants_{label}.csv')
    r, low, high = correlation_ci(participants,rng)
    # Working independence is chosen for stable fitting (exchangeable can fail
    # to converge for this dataset). Cluster-robust covariance still accounts
    # for correlated responses belonging to the same participant.
    model=smf.gee('accuracy ~ within_10pp + between_10pp + difficulty_z + C(exp)',
                   groups='Subj_idx', data=data,
                   cov_struct=sm.cov_struct.Independence(),
                   family=sm.families.Binomial())
    fit=model.fit(maxiter=150)
    if not np.isfinite(fit.params.to_numpy()).all():
        raise ValueError(f'Nonfinite fitted coefficients for {label}')
    conf=fit.conf_int()
    coefs=[]
    for term in fit.params.index:
        coefs.append({'subset':label,'term':term,'log_odds_coef':fit.params[term],
                      'ci_lower':conf.loc[term,0],'ci_upper':conf.loc[term,1],
                      'odds_ratio':np.exp(fit.params[term]),
                      'p_value':fit.pvalues[term]})
    # A WITHIN vs BETWEEN contrast is legitimate on the common log-odds scale
    # of the fitted population-average model. Its inferential interpretation
    # is conditional on the model covariates and assumptions.
    contrast=np.zeros(len(fit.params)); names=list(fit.params.index)
    contrast[names.index('within_10pp')]=1
    contrast[names.index('between_10pp')]=-1
    test=fit.t_test(contrast)
    diff=float(np.asarray(test.effect).ravel()[0])
    diff_ci=np.asarray(test.conf_int())[0]
    summary={'subset':label,'status':'primary' if condition=='motion' else 'exploratory',
             'n_rows':len(data),'n_unique_participants':data.Subj_idx.nunique(),
             'n_exp_sessions':data.groupby(['Subj_idx','exp']).ngroups,
             'mean_confidence_pct':data.confidence.mean(),
             'accuracy_pct':100*data.accuracy.mean(),
             'overconfident_participants':int((participants.confidence_gap_pp>0).sum()),
             'underconfident_participants':int((participants.confidence_gap_pp<0).sum()),
             'between_person_r':r,'between_r_ci_lower':low,'between_r_ci_upper':high,
             'within_10pp_logodds':fit.params['within_10pp'],
             'within_10pp_ci_lower':conf.loc['within_10pp',0],
             'within_10pp_ci_upper':conf.loc['within_10pp',1],
             'between_10pp_logodds':fit.params['between_10pp'],
             'between_10pp_ci_lower':conf.loc['between_10pp',0],
             'between_10pp_ci_upper':conf.loc['between_10pp',1],
             'within_minus_between_logodds':diff,
             'difference_ci_lower':diff_ci[0], 'difference_ci_upper':diff_ci[1],
             'difference_p_value':float(np.asarray(test.pvalue).ravel()[0])}
    return summary,coefs,participants


def figures(primary_participants, summary_df, outdir):
    fig,ax=plt.subplots(figsize=(7.4,5.4))
    sub=primary_participants
    is_over=sub.confidence_gap_pp>0
    ax.scatter(sub.loc[is_over,'mean_confidence'],100*sub.loc[is_over,'mean_accuracy'],
               label=f'Overconfident (n={is_over.sum()})',alpha=.73,s=45,color=ORANGE)
    ax.scatter(sub.loc[~is_over,'mean_confidence'],100*sub.loc[~is_over,'mean_accuracy'],
               label=f'Under- / exactly calibrated (n={(~is_over).sum()})',alpha=.73,s=45,color=TEAL)
    ax.plot([50,100],[50,100],ls='--',color='black',label='Equal mean confidence and accuracy')
    ax.set(xlim=(48,102),ylim=(40,102),xlabel='Mean confidence (%)',
           ylabel='Mean accuracy (%)',title='Motion decisions: confidence often exceeds observed accuracy')
    ax.grid(alpha=.20);ax.legend(fontsize=8)
    fig.tight_layout();fig.savefig(outdir/'konishi_motion_calibration.png',dpi=200);plt.close(fig)
    fig,ax=plt.subplots(figsize=(7.7,4.6))
    order=['motion_motion','color_color','dual_motion','dual_color']
    d=summary_df.set_index('subset').loc[order]
    ypos=np.arange(len(d))
    point=d.within_10pp_logodds.to_numpy(); lower=d.within_10pp_ci_lower.to_numpy(); upper=d.within_10pp_ci_upper.to_numpy()
    ax.errorbar(point,ypos,xerr=[point-lower,upper-point],fmt='o',capsize=4,color=TEAL)
    ax.axvline(0,ls='--',color='black',lw=1)
    ax.set_yticks(ypos,labels=['Single: motion (primary)','Single: color','Dual: motion','Dual: color'])
    ax.invert_yaxis()
    ax.set(xlabel='Within-person GEE log-odds effect per +10pp confidence',
           title='Positive within-person association across task conditions')
    ax.grid(axis='x',alpha=.20)
    fig.tight_layout();fig.savefig(outdir/'konishi_within_effects.png',dpi=200);plt.close(fig)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, default=Path(__file__).parent/'data_Konishi_2019.csv')
    parser.add_argument('--out',type=Path,default=Path(__file__).parent/'results')
    args=parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    df=pd.read_csv(args.input)
    assert len(df)==66960
    assert df.Subj_idx.nunique()==93
    rng=np.random.default_rng(2026)
    summaries=[];coefs=[];primary=None
    for condition,dim in [('motion','Motion'),('color','Color'),('dual','Motion'),('dual','Color')]:
        s,c,p=run(df,condition,dim,rng,args.out)
        summaries.append(s);coefs.extend(c)
        if condition=='motion':primary=p
    sdf=pd.DataFrame(summaries)
    sdf.to_csv(args.out/'konishi_results_summary.csv',index=False)
    pd.DataFrame(coefs).to_csv(args.out/'konishi_gee_coefficients.csv',index=False)
    figures(primary,sdf,args.out)
    # Sensitivity: split confidence relative to each participant's mean within
    # their experimental SESSION, rather than across all sessions. Participant
    # IDs (not sessions) remain the inference clusters; repeated participants
    # therefore never masquerade as independent people.
    sess=prepare(df,'motion','Motion').copy()
    sessions=sess.groupby(['Subj_idx','exp'])['confidence'].transform('mean')
    sess['within_10pp']=(sess.confidence-sessions)/10
    sess['between_10pp']=(sessions-sessions.mean())/10
    mod=smf.gee('accuracy ~ within_10pp + between_10pp + difficulty_z + C(exp)',
               groups='Subj_idx',data=sess,cov_struct=sm.cov_struct.Independence(),
               family=sm.families.Binomial())
    fitted=mod.fit(maxiter=150)
    cis=fitted.conf_int()
    sensitivity=pd.DataFrame([{'term':term,'estimate':fitted.params[term],
       'ci_lower':cis.loc[term,0],'ci_upper':cis.loc[term,1],
       'n_participants':sess.Subj_idx.nunique(),
       'n_participant_sessions':sess.groupby(['Subj_idx','exp']).ngroups,
       'method':'Within-(participant,experiment) centering; GEE clustered by participant'}
       for term in ('within_10pp','between_10pp')])
    sensitivity.to_csv(args.out/'konishi_session_centering_sensitivity.csv',index=False)
    print('Session-centered Konishi sensitivity:',sensitivity[['term','estimate','ci_lower','ci_upper']].to_string(index=False))
    pd.set_option('display.max_columns',30)
    print(sdf[['subset','n_rows','n_unique_participants','mean_confidence_pct','accuracy_pct','between_person_r','between_r_ci_lower','between_r_ci_upper','within_10pp_logodds','within_10pp_ci_lower','within_10pp_ci_upper','between_10pp_logodds','between_10pp_ci_lower','between_10pp_ci_upper','within_minus_between_logodds','difference_ci_lower','difference_ci_upper']].round(3).to_string(index=False))
    print('\nSaved reproducible outputs to',args.out)

if __name__ == '__main__':
    main()
