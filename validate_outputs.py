"""Check original inputs, GEE coefficients, GLMM diagnostics, derived report & figures.

Tests verify internal coherence, NOT causal validity or frequentist coverage.
"""
from pathlib import Path
import hashlib
import numpy as np
import pandas as pd
from PIL import Image as PILImage
import pymupdf as fitz
import sys
SMOKE='--smoke' in sys.argv
ROOT=Path(__file__).resolve().parents[1]

def must(path):
    p=ROOT/path
    assert p.is_file() and p.stat().st_size>0, f'Missing/empty output: {path}'
    return p

def close(actual, expected, atol=1e-10):
    assert np.isfinite(float(actual)) and abs(float(actual)-float(expected))<atol,(actual,expected)

for line in (ROOT/'SHA256_SOURCE_FILES.txt').read_text().splitlines():
    hashed,rel=line.split(maxsplit=1)
    actual=hashlib.sha256(must(rel).read_bytes()).hexdigest()
    assert hashed==actual,f'Changed source CSV: {rel}'

raw_r=pd.read_csv(must('data/data_Rouault_2019.csv'))
raw_a=pd.read_csv(must('data/data_AguilarLleyda_2018.csv'))
raw_k=pd.read_csv(must('data/data_Konishi_2019.csv'))
assert len(raw_r)==26280 and len(raw_a)==11200 and len(raw_k)==66960
assert raw_r.Subj_idx.nunique()==73 and raw_a.Subj_idx.nunique()==28 and raw_k.Subj_idx.nunique()==93

r=ROOT/'results/generated/rouault'
a=ROOT/'results/generated/aguilarlleyda'
k=ROOT/'results/generated/konishi'
rgee=pd.read_csv(must('results/generated/rouault/rouault_gee_coefficients.csv'),index_col=0)
rsub=pd.read_csv(must('results/generated/rouault/rouault_participant_summary.csv'))
close(rgee.loc['within_10pp','estimate'],.395674085365657,1e-6)
close(rgee.loc['between_10pp','estimate'],.046299566567112,1e-6)
rsens=pd.read_csv(must('results/generated/rouault/rouault_sensitivity.csv'))
assert rsens.participants.tolist()==[72,71,59,54]
assert rsub.n_trials.sum()==12960 and len(rsub)==72
rcontr=pd.read_csv(must('results/generated/rouault/rouault_gee_within_between_contrast.csv')).iloc[0]
close(rcontr.within_minus_between,rgee.loc['within_10pp','estimate']-rgee.loc['between_10pp','estimate'])

glmm=pd.read_csv(must('results/generated/rouault/rouault_glmm_summary.csv')).set_index('term')
meta=pd.read_csv(must('results/generated/rouault/rouault_glmm_diagnostics.csv')).iloc[0]
draws=pd.read_csv(must('results/generated/rouault/rouault_glmm_bootstrap_draws.csv'))
assert len(draws)==int(meta.bootstrap_valid)==int(meta.bootstrap_requested)
assert meta.quadrature_nodes>=12
if not SMOKE:assert meta.bootstrap_requested>=500,'A 20-resample smoke test must not be treated as final' 
assert .14 < glmm.loc['between_10pp','mle_estimate'] < .17
for term in glmm.index:
    assert term in draws.columns
    lo,hi=np.quantile(draws[term],[.025,.975])
    close(glmm.loc[term,'cluster_boot_ci_025'],lo)
    close(glmm.loc[term,'cluster_boot_ci_975'],hi)

ag=pd.read_csv(must('results/generated/aguilarlleyda/results_summary.csv'))
agsub=pd.read_csv(must('results/generated/aguilarlleyda/subject_summary_col.csv'))
acboot=pd.read_csv(must('results/generated/aguilarlleyda/color_cluster_bootstrap_intervals.csv'))
acdraw=pd.read_csv(must('results/generated/aguilarlleyda/color_cluster_bootstrap_draws.csv'))
assert len(agsub)==28 and agsub.n.sum()==11200
assert len(acdraw)==acboot.bootstrap_valid.iloc[0]
assert len(acdraw)>=0.9*acboot.bootstrap_requested.iloc[0]
if not SMOKE:assert acboot.bootstrap_requested.iloc[0]>=300,'A 30-resample smoke test must not be treated as final'
for _,row in acboot.iterrows():
    low,high=np.quantile(acdraw[row.term],[.025,.975])
    close(row.ci_lower,low);close(row.ci_upper,high)
for task in ('Color','Letter'):
    i=ag.query('task==@task').set_index('term')
    close(i.loc['within_minus_between','coef'],i.loc['centered10','coef']-i.loc['mean10','coef'])
    assert i.loc['centered10','ci_lower']>0

ko=pd.read_csv(must('results/generated/konishi/konishi_results_summary.csv'))
ks=pd.read_csv(must('results/generated/konishi/konishi_session_centering_sensitivity.csv'))
k1=ko.query("subset=='motion_motion'").iloc[0]
assert int(k1.n_unique_participants)==93 and int(k1.n_rows)==22320
assert ks.n_participants.eq(93).all() and ks.n_participant_sessions.gt(93).all()
assert ks.query("term=='within_10pp'").ci_lower.iloc[0]>0

summ=pd.read_csv(must('results/cross_study_primary_summary.csv'))
assert len(summ)==3 and summ.participants.tolist()==[72,28,93]
assert summ.rated_decisions.tolist()==[12960,11200,22320]
close(summ.iloc[0].within_coef,rgee.loc['within_10pp','estimate'])
close(summ.iloc[0].between_coef,rgee.loc['between_10pp','estimate'])
a1=ag.query("task=='Color' and term=='centered10'").iloc[0]
a2=ag.query("task=='Color' and term=='mean10'").iloc[0]
close(summ.iloc[1].within_coef,a1.coef)
close(summ.iloc[1].between_coef,a2.coef)
close(summ.iloc[2].within_coef,k1.within_10pp_logodds)
close(summ.iloc[2].between_coef,k1.between_10pp_logodds)

for path in ['figures/three_study_within_effects.png','figures/rouault_sensitivity.png',
             'figures/rouault_participants.png','figures/aguilarlleyda_calibration.png',
             'figures/konishi_motion_calibration.png','figures/konishi_within_effects.png']:
    p=must(path)
    with PILImage.open(p) as im:assert im.width>=650 and im.height>=350

pdf=fitz.open(must('report/Confidence_Paradox_Research_Report_CORRECTED.pdf'))
assert len(pdf)==4,f'Report unexpectedly has {len(pdf)} pages'
text=' '.join(' '.join(page.get_text().split()) for page in pdf)
for value in [f'{row.within_coef:+.3f}' for row in summ.itertuples(index=False)]:
    assert value in text,f'Primary within coefficient not printed in report: {value}'
for value in [f'{row.between_coef:+.3f}' for row in summ.itertuples(index=False)]:
    assert value in text,f'Primary between coefficient not printed in report: {value}'
assert f"{glmm.loc['between_10pp','mle_estimate']:+.3f}" in text
assert f"{ks.query('term==\'within_10pp\'').estimate.iloc[0]:+.3f}" in text
assert 'Kimia Pasandideh' in text
if SMOKE:assert 'PRELIMINARY / SMOKE-TEST' in text
else:assert 'PRELIMINARY / SMOKE-TEST' not in text
for phrase in ('variational-Bayes','not peer-reviewed','multiple','GEE','GLMM'):
    assert phrase.lower() in text.lower(),phrase
pdf.close()

readme=must('README.md').read_text()
for row in summ.itertuples(index=False):
    assert f'{row.within_coef:+.3f}' in readme
print(('PASS (SMOKE ONLY):' if SMOKE else 'PASS (FULL OUTPUTS):')+' source hashes, 3 studies, contrasts, exclusions, cluster resampling, session sensitivity, six figures, four-page PDF and README checked.')
