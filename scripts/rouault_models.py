"""Rouault 2019: reproducible GEE, participant bootstrap, sensitivity, and GLMM.

All analyses exploratory. The original Rouault authors' comprehension-question
exclusions cannot be reproduced from these public data.

The GLMM is a NORMAL random-intercept logistic GLMM, with its participant-level
random effect integrated by adaptive Gauss-Hermite quadrature. Its intervals below use a
nonparametric participant-cluster bootstrap (not variational Bayes).

Usage: python scripts/rouault_models.py --input data/data_Rouault_2019.csv
       --outdir results/generated/rouault --figdir figures --bootstrap-reps 500
"""
from __future__ import annotations
import argparse
from pathlib import Path
import warnings
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy.special import expit, logsumexp
from scipy.optimize import minimize
from numpy.polynomial.hermite import hermgauss
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from plot_style import NAVY, TEAL, ORANGE, GREY


def load_data(path):
    raw=pd.read_csv(path)
    needed={'Subj_idx','Confidence','Accuracy','DotDiff'}
    if not needed.issubset(raw): raise ValueError(f'Missing columns: {needed-set(raw)}')
    rated=raw.dropna(subset=list(needed)).copy()
    if not rated.Accuracy.isin([0,1]).all(): raise ValueError('Accuracy must be 0 or 1')
    if not rated.Confidence.between(.5,1).all(): raise ValueError('Confidence expected in [0.5,1]')
    if not rated.DotDiff.isin([24,60]).all(): raise ValueError('Difficulty values unexpected')
    mean=rated.groupby('Subj_idx').Confidence.transform('mean')
    rated['within_10pp']=(rated.Confidence-mean)/.1
    rated['between_10pp']=(mean-mean.mean())/.1
    rated['easy']=(rated.DotDiff==60).astype(float)
    return raw,rated


def gee_fit(rated):
    model=smf.gee('Accuracy ~ within_10pp + between_10pp + easy',
        groups='Subj_idx', data=rated, cov_struct=sm.cov_struct.Exchangeable(),
        family=sm.families.Binomial())
    fit=model.fit(maxiter=200)
    if not np.all(np.isfinite(fit.params.to_numpy())):raise ValueError('GEE nonfinite coefficients')
    ci=fit.conf_int()
    tab=pd.DataFrame({'estimate':fit.params,'robust_se':fit.bse,
        'ci_025':ci.iloc[:,0], 'ci_975':ci.iloc[:,1], 'p_value':fit.pvalues,
        'odds_ratio':np.exp(fit.params)})
    terms=list(fit.params.index)
    contrast=np.zeros(len(terms));contrast[terms.index('within_10pp')]=1;contrast[terms.index('between_10pp')]=-1
    diff=fit.t_test(contrast)
    return fit,tab,{'within_minus_between':float(np.asarray(diff.effect).ravel()[0]),
        'ci_025':float(np.asarray(diff.conf_int())[0,0]),
        'ci_975':float(np.asarray(diff.conf_int())[0,1])}


def participant_corr(rated,nrep=5000,seed=2026):
    summary=rated.groupby('Subj_idx').agg(mean_confidence=('Confidence','mean'),mean_accuracy=('Accuracy','mean'),n_trials=('Accuracy','size'))
    xy=summary[['mean_confidence','mean_accuracy']].to_numpy()
    point=float(np.corrcoef(xy[:,0],xy[:,1])[0,1]);rng=np.random.default_rng(seed)
    draws=[]
    for _ in range(nrep):
        sample=xy[rng.integers(len(xy),size=len(xy))]
        if sample[:,0].std()>1e-10 and sample[:,1].std()>1e-10:
            draws.append(float(np.corrcoef(sample[:,0],sample[:,1])[0,1]))
    return summary,point,np.quantile(draws,[.025,.975]),np.asarray(draws)


def sensitivity_analysis(raw,rated,outdir,figdir):
    all_s=raw.groupby('Subj_idx').agg(all_accuracy=('Accuracy','mean'),n_all=('Accuracy','size'))
    rated_s=rated.groupby('Subj_idx').agg(n_rated=('Accuracy','size'),n_unique_conf=('Confidence','nunique'))
    participants=all_s.join(rated_s,how='left').fillna({'n_rated':0,'n_unique_conf':0})
    participants[['n_rated','n_unique_conf']]=participants[['n_rated','n_unique_conf']].astype(int)
    participants.to_csv(outdir/'participant_quality_metrics.csv')
    conditions={
      'all_rated':(participants.n_rated>0),
      'exclude_constant_ratings':(participants.n_rated>0)&(participants.n_unique_conf>1),
      'nonconstant_and_accuracy_gt_55pct':(participants.n_rated>0)&(participants.n_unique_conf>1)&(participants.all_accuracy>.55),
      'nonconstant_and_accuracy_gt_60pct':(participants.n_rated>0)&(participants.n_unique_conf>1)&(participants.all_accuracy>.60),
    }
    rows=[]
    for name,condition in conditions.items():
        sub=rated.loc[rated.Subj_idx.isin(participants.index[condition])].copy()
        # Re-center participant averages using the current analysis sample.
        means=sub.groupby('Subj_idx').Confidence.transform('mean')
        sub['between_10pp']=(means-means.mean())/.1
        sub['within_10pp']=(sub.Confidence-means)/.1
        fit,tab,_=gee_fit(sub)
        rows.append({'filter':name,'participants':sub.Subj_idx.nunique(),'trials':len(sub),
            'within_estimate':tab.loc['within_10pp','estimate'],
            'within_ci_025':tab.loc['within_10pp','ci_025'],
            'within_ci_975':tab.loc['within_10pp','ci_975'],
            'between_estimate':tab.loc['between_10pp','estimate'],
            'between_ci_025':tab.loc['between_10pp','ci_025'],
            'between_ci_975':tab.loc['between_10pp','ci_975']})
    output=pd.DataFrame(rows);output.to_csv(outdir/'rouault_sensitivity.csv',index=False)
    fig,ax=plt.subplots(figsize=(9,4.5)); y=np.arange(len(output))[::-1]
    for i,r in output.iterrows():
        ax.errorbar(r.within_estimate,y[i]+.1,xerr=[[r.within_estimate-r.within_ci_025],[r.within_ci_975-r.within_estimate]],fmt='o',capsize=3,color=TEAL)
        ax.errorbar(r.between_estimate,y[i]-.1,xerr=[[r.between_estimate-r.between_ci_025],[r.between_ci_975-r.between_estimate]],fmt='s',capsize=3,color=ORANGE)
    ax.axvline(0,ls='--',color='gray',lw=1)
    ax.set_yticks(y,[f'{int(z.participants)} participants' for _,z in output.iterrows()])
    ax.set_xlabel('GEE log-odds coefficient per 10 percentage points confidence')
    ax.set_title('Within-person estimates remain positive across screening choices')
    ax.plot([],[],'o',color=TEAL,label='Within');ax.plot([],[],'s',color=ORANGE,label='Between');ax.legend()
    ax.grid(axis='x',alpha=.12);fig.tight_layout();fig.savefig(figdir/'rouault_sensitivity.png',dpi=190);plt.close(fig)
    return output


class RandomInterceptLogitAGHQ:
    """Logistic random-intercept GLMM by adaptive adaptive Gauss-Hermite quadrature.

    This integrates participant random effects around their *conditional mode*
    (not around zero), which is crucial for clusters of ~180 Bernoulli trials.
    Participants are the independent top-level sampling unit.
    """
    def __init__(self,rated,quadrature_nodes=15):
        ordered=rated.sort_values('Subj_idx')
        counts=ordered.groupby('Subj_idx').size().to_numpy()
        if not np.all(counts==counts[0]):raise ValueError('This fast implementation assumes equal rated trials per subject')
        n=len(counts);m=int(counts[0]);self.n=n
        self.X=np.column_stack([np.ones(len(ordered)),ordered.within_10pp,ordered.between_10pp,ordered.easy]).reshape(n,m,4)
        self.Y=ordered.Accuracy.to_numpy(float).reshape(n,m)
        self.nodes,self.weights=hermgauss(quadrature_nodes)
        self.logweights=np.log(self.weights)
        self.terms=['Intercept','within_10pp','between_10pp','easy','log_sd_random_intercept']

    def loss_and_jac(self,theta,cluster_weights=None):
        betas=theta[:4];sigma=np.exp(theta[4]);eta=self.X@betas
        # Locate each participant's conditional random-intercept mode via Newton.
        u=np.zeros(self.n)
        for _ in range(25):
            ps=expit(eta+u[:,None])
            grad_u=(self.Y-ps).sum(axis=1)-u/sigma**2
            curvature=(ps*(1-ps)).sum(axis=1)+1/sigma**2
            step=grad_u/curvature
            u+=step
            if np.max(np.abs(step))<2e-12:break
        ps=expit(eta+u[:,None])
        curvature=(ps*(1-ps)).sum(axis=1)+1/sigma**2
        scale=np.sqrt(2/curvature)
        random_nodes=u[:,None]+scale[:,None]*self.nodes[None,:]
        z=eta[:,None,:]+random_nodes[:,:,None]
        loglik=(self.Y[:,None,:]*z-np.logaddexp(0.,z)).sum(axis=2)
        # Normal random-effect density is part of the integrand (not a penalty
        # tacked on after integration).
        logprior=-.5*(random_nodes/sigma)**2-np.log(sigma)-.5*np.log(2*np.pi)
        # Recover integral after GH exp(-x^2) weighting and adaptive change of variables.
        logterms=loglik+logprior+self.nodes[None,:]**2+self.logweights[None,:]
        normalizer=logsumexp(logterms,axis=1)
        group_log_integral=.5*np.log(2/curvature)+normalizer
        posterior_weights=np.exp(logterms-normalizer[:,None])
        # Fisher's identity: marginal scores are posterior-averaged complete-data scores.
        residual=self.Y[:,None,:]-expit(z)
        beta_grad=np.einsum('ik,ikt,itp->ip',posterior_weights,residual,self.X)
        sigma_grad=(posterior_weights*(-1+random_nodes**2/sigma**2)).sum(axis=1)
        gradients=np.column_stack([beta_grad,sigma_grad])
        if cluster_weights is None:cluster_weights=np.ones(self.n)
        loss=-float(cluster_weights@group_log_integral)
        grad=-(cluster_weights[:,None]*gradients).sum(axis=0)
        return loss,grad

    def fit(self,start=None,cluster_weights=None,method='BFGS'):
        if start is None:start=np.array([.8,.4,.1,.6,np.log(.6)])
        kwargs=dict(jac=True,options={'gtol':1e-4,'maxiter':140})
        if method=='L-BFGS-B':
            kwargs={'jac':True,'bounds':[(None,None)]*4+[(-4,2)],'options':{'maxiter':110,'ftol':1e-11,'gtol':1e-4}}
        return minimize(lambda th:self.loss_and_jac(th,cluster_weights),np.array(start),method=method,**kwargs)


def fit_glmm(rated,outdir,bootstrap_reps=500,nodes=30,seed=2026):
    model=RandomInterceptLogitAGHQ(rated,nodes)
    mle=model.fit()
    if not mle.success and np.linalg.norm(mle.jac)>1e-3:
        raise RuntimeError(f'GLMM main MLE did not converge: {mle.message}, norm jac {np.linalg.norm(mle.jac)}')
    rng=np.random.default_rng(seed)
    draws=[];not_converged=0
    for i in range(bootstrap_reps):
        sample=rng.integers(model.n,size=model.n)
        weights=np.bincount(sample,minlength=model.n)
        fit=model.fit(mle.x,weights,method='L-BFGS-B')
        if not fit.success and np.linalg.norm(fit.jac)>1e-2:
            not_converged+=1
            continue
        draws.append(fit.x)
    draws=np.asarray(draws)
    if len(draws)<bootstrap_reps*.95:
        raise RuntimeError(f'Too many bootstrap fits failed: {not_converged}/{bootstrap_reps}')
    frame=pd.DataFrame(draws,columns=model.terms)
    frame.to_csv(outdir/'rouault_glmm_bootstrap_draws.csv',index=False)
    lo,hi=np.quantile(draws,[.025,.975],axis=0)
    summary=pd.DataFrame({'term':model.terms,'mle_estimate':mle.x,
        'cluster_boot_ci_025':lo,'cluster_boot_ci_975':hi,
        'method':'Normal random-intercept GLMM; adaptive GH marginal ML; participant bootstrap'})
    summary.to_csv(outdir/'rouault_glmm_summary.csv',index=False)
    meta=pd.DataFrame([{'n_participants':model.n,'n_trials':len(rated),
       'bootstrap_requested':bootstrap_reps,'bootstrap_valid':len(draws),
       'bootstrap_seed':seed,'quadrature_nodes':nodes,
       'mle_converged':mle.success,'mle_gradient_norm':np.linalg.norm(mle.jac),
       'mle_loglik':-mle.fun,'random_intercept_sd':np.exp(mle.x[-1])}])
    meta.to_csv(outdir/'rouault_glmm_diagnostics.csv',index=False)
    return summary,meta


def plot_participants(summary,figdir):
    fig,ax=plt.subplots(figsize=(6.8,5.0))
    c=summary.mean_confidence.to_numpy(); a=summary.mean_accuracy.to_numpy()
    over=c>a
    ax.scatter(100*c[over],100*a[over],alpha=.72,color=ORANGE,label=f'Overconfident (n={over.sum()})')
    ax.scatter(100*c[~over],100*a[~over],alpha=.72,color=TEAL,label=f'Under- or exactly calibrated (n={(~over).sum()})')
    ax.plot([50,100],[50,100],'k--',label='Equal mean confidence and accuracy')
    ax.set(xlim=(45,102),ylim=(40,102),xlabel='Mean confidence (%)',ylabel='Mean accuracy (%)',title='Confidence exceeds observed accuracy for many participants')
    ax.legend(fontsize=8);ax.grid(alpha=.18);fig.tight_layout();fig.savefig(figdir/'rouault_participants.png',dpi=190);plt.close(fig)


def main():
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,default=Path('data/data_Rouault_2019.csv'))
    p.add_argument('--outdir',type=Path,default=Path('results/generated/rouault'))
    p.add_argument('--figdir',type=Path,default=Path('figures'))
    p.add_argument('--bootstrap-reps',type=int,default=500);p.add_argument('--quadrature-nodes',type=int,default=15)
    args=p.parse_args();args.outdir.mkdir(parents=True,exist_ok=True);args.figdir.mkdir(parents=True,exist_ok=True)
    raw,rated=load_data(args.input)
    print('Loaded',len(raw),'rows,',len(rated),'rated decisions,',rated.Subj_idx.nunique(),'participants',flush=True)
    gee,gee_tab,gee_contrast=gee_fit(rated);gee_tab.to_csv(args.outdir/'rouault_gee_coefficients.csv')
    pd.DataFrame([gee_contrast]).to_csv(args.outdir/'rouault_gee_within_between_contrast.csv',index=False)
    participants,corr,ci,draws=participant_corr(rated)
    participants.to_csv(args.outdir/'rouault_participant_summary.csv')
    pd.DataFrame([{'pearson_r':corr,'bootstrap_ci_025':ci[0],'bootstrap_ci_975':ci[1],'n':len(participants)}]).to_csv(args.outdir/'rouault_correlation.csv',index=False)
    plot_participants(participants,args.figdir)
    sensitivity=sensitivity_analysis(raw,rated,args.outdir,args.figdir)
    print('GEE:');print(gee_tab.loc[['within_10pp','between_10pp'],['estimate','ci_025','ci_975']].round(4).to_string(),flush=True)
    print('Sensitivity samples',sensitivity.participants.tolist(),flush=True)
    glmm,meta=fit_glmm(rated,args.outdir,args.bootstrap_reps,args.quadrature_nodes)
    print('GLMM marginal likelihood / cluster bootstrap:');print(glmm.round(4).to_string(index=False),flush=True)
    print('Bootstrap valid',int(meta.bootstrap_valid.iloc[0]),'of',args.bootstrap_reps,flush=True)

if __name__=='__main__':main()
