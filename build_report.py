"""Build a four-page research report ONLY from generated CSV/figure outputs.

Never hard-code model estimates: if an analysis changes, the report changes.
"""
from pathlib import Path
from xml.sax.saxutils import escape
import numpy as np
import pandas as pd
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from matplotlib import font_manager

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'report'/'Confidence_Paradox_Research_Report_CORRECTED.pdf'
OUT.parent.mkdir(exist_ok=True)
S=pd.read_csv(ROOT/'results'/'cross_study_primary_summary.csv')
assert len(S)==3, 'Require three primary study results'
R=ROOT/'results'/'generated'/'rouault'
A=ROOT/'results'/'generated'/'aguilarlleyda'
K=ROOT/'results'/'generated'/'konishi'
GEE=pd.read_csv(R/'rouault_gee_coefficients.csv',index_col=0)
GLMM=pd.read_csv(R/'rouault_glmm_summary.csv').set_index('term')
GLMM_META=pd.read_csv(R/'rouault_glmm_diagnostics.csv').iloc[0]
SENS=pd.read_csv(R/'rouault_sensitivity.csv')
K_SUM=pd.read_csv(K/'konishi_results_summary.csv')
A_RES=pd.read_csv(A/'results_summary.csv')
K_SESS=pd.read_csv(K/'konishi_session_centering_sensitivity.csv')
A_BOOT=pd.read_csv(A/'color_cluster_bootstrap_intervals.csv')
PRELIMINARY=int(GLMM_META.bootstrap_requested)<500 or int(A_BOOT.bootstrap_requested.iloc[0])<300
R_CONTR=pd.read_csv(R/'rouault_gee_within_between_contrast.csv').iloc[0]
K_PRIMARY=K_SUM.query("subset == 'motion_motion'").iloc[0]
A_CONTR=A_RES.query("task == 'Color' and term == 'within_minus_between'").iloc[0]

REG_FONT = font_manager.findfont('DejaVu Serif')
BOLD_FONT = font_manager.findfont(
    font_manager.FontProperties(family='DejaVu Serif', weight='bold')
)
SANS_FONT = font_manager.findfont('DejaVu Sans')
pdfmetrics.registerFont(TTFont('ReportSerif',str(REG_FONT)))
pdfmetrics.registerFont(TTFont('ReportSerifBold',str(BOLD_FONT)))
pdfmetrics.registerFont(TTFont('ReportSans',str(SANS_FONT)))
NAVY=HexColor('#334E68'); TEAL=HexColor('#5B7F84'); ORANGE=HexColor('#A06A5B')
INK=HexColor('#111111'); MUTED=HexColor('#111111'); LIGHT=HexColor('#F2F4F6'); RULE=HexColor('#D6DADF')
T={
 'title':ParagraphStyle('title',fontName='ReportSerifBold',fontSize=19,leading=24,textColor=INK,spaceAfter=8),
 'subtitle':ParagraphStyle('subtitle',fontName='ReportSerif',fontSize=10.2,leading=14,textColor=INK,spaceAfter=10),
 'section':ParagraphStyle('section',fontName='ReportSerifBold',fontSize=11.5,leading=15,textColor=INK,spaceBefore=11,spaceAfter=5),
 'body':ParagraphStyle('body',fontName='ReportSerif',fontSize=8.8,leading=12.8,textColor=INK,spaceAfter=7),
 'small':ParagraphStyle('small',fontName='ReportSerif',fontSize=7.9,leading=11.2,textColor=INK,spaceAfter=4),
 'caption':ParagraphStyle('caption',fontName='ReportSerif',fontSize=7.5,leading=10.1,textColor=INK,spaceAfter=5),
 'th':ParagraphStyle('th',fontName='ReportSerifBold',fontSize=7.35,leading=10,textColor=INK),
 'td':ParagraphStyle('td',fontName='ReportSerif',fontSize=7.25,leading=10.4,textColor=INK),
}
def P(msg,sty='body'):return Paragraph(str(msg),T[sty])
def sign(value):return f'{float(value):+.3f}'
def interval(lo,hi):return f'[{float(lo):+.3f}, {float(hi):+.3f}]'
def prettyrow(row,prefix):
    return f"{sign(getattr(row,prefix+'coef'))} {interval(getattr(row,prefix+'low'),getattr(row,prefix+'high'))}"
def tab(rows,widths):
    cells=[[P(escape(str(x)),'th' if k==0 else 'td') for x in row] for k,row in enumerate(rows)]
    t=Table(cells,colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([
      ('BACKGROUND',(0,0),(-1,0),LIGHT),('TEXTCOLOR',(0,0),(-1,0),INK),
      ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,HexColor('#FAFBFC')]),
      ('GRID',(0,0),(-1,-1),0.35,RULE),
      ('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,0),7),('BOTTOMPADDING',(0,0),(-1,0),7),
      ('TOPPADDING',(0,1),(-1,-1),5),('BOTTOMPADDING',(0,1),(-1,-1),5),
      ('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7)
    ]))
    return t

def footer(canvas,doc):
    w,h=A4
    canvas.saveState()
    canvas.setStrokeColor(RULE);canvas.line(43,42,w-43,42)
    canvas.setFont('ReportSans',7);canvas.setFillColor(INK)
    canvas.drawString(45,29,'THE CONFIDENCE PARADOX  |  '+('SMOKE TEST — NOT FOR CITATION' if PRELIMINARY else 'EXPLORATORY SECONDARY-DATA ANALYSIS'))
    canvas.drawRightString(w-45,29,f'{doc.page}')
    canvas.restoreState()

s=[]
# 1 - PI can assess within 10 seconds
s.extend([
 P('The Confidence Paradox','title'),
 P('Confidence tracks correctness within people more consistently than average confidence distinguishes between people.','subtitle'),
 P('<b>Kimia Pasandideh</b> | Computer Science &amp; Mathematics, Université Paris-Saclay | 26 October 2026','small'),
 *( [P('<b>PRELIMINARY / SMOKE-TEST OUTPUT — DO NOT QUOTE THE INTERVALS.</b>','section')] if PRELIMINARY else [] ),
 P('KEY RESULT  |  THREE PERCEPTUAL-DECISION DATASETS','section'),
 P('In three selected visual tasks, logistic population-averaged GEE models found <b>positive within-person confidence–accuracy associations</b>. All three corresponding between-person 95% robust confidence intervals spanned zero. These are <b>exploratory observational associations</b>, not causal findings or a prospective preregistration.'),
 Image(str(ROOT/'figures'/'three_study_within_effects.png'),width=484,height=216),
 P('Figure 1. Each point is a GEE log-odds coefficient for a +10 percentage-point rise in confidence relative to the same individual’s mean; whiskers are participant-cluster robust 95% confidence intervals.','caption'),
 P('Research question','section'),
 P('Is an individual more likely to be correct when unusually confident in a particular answer, and is this distinct from the relationship between different individuals’ average confidence and accuracy?'),
 P('Scope and contribution','section'),
 P('We re-analyze open perceptual-decision data from Rouault, Aguilar-Lleyda and Konishi. The contribution is a transparent separation of <b>within-person</b> and <b>between-person</b> levels, with clustering, sensitivity checks and a reproducible pipeline—not a claim that the confidence–accuracy relationship is newly discovered.'),
 P('<b>Scientific status:</b> independent student exploratory re-analysis; existing data; hypotheses were not publicly preregistered; not peer-reviewed. Analytical coding and report preparation included AI assistance, with reproducible source and documented limitations.','caption'),
 PageBreak()
])
# 2 - method
s.extend([P('1  Data and methods','title'),
 P('Data origin','section'),
 P('All three CSVs and their contributor READMEs originate in The Confidence Database (Rahnev et al., 2020; OSF: https://osf.io/s46pr/). Each decision has objective correctness coded 0/1; reported confidence is 50–100% (Rouault stores its equivalent as 0.5–1.0). No new participants were recruited for this project.'),
 tab([['Primary study','People','Rated decisions','Primary task']]+[[row.dataset,int(row.participants),f'{int(row.rated_decisions):,}',row.task] for row in S.itertuples(index=False)],[165,54,89,194]),
 P('Model specification','section'),
 P('The primary models use logistic GEE with participant-cluster robust standard errors. We enter <b>trial confidence minus participant mean</b> (within-person) and <b>participant mean minus grand mean</b> (between-person), each measured in 10 percentage-point units, with an adjustment for trial difficulty. Rouault and Aguilar-Lleyda use exchangeable working correlation; Konishi uses independence working correlation with robust clustering and experimental-condition fixed effects.'),
 P('The unit of independent clustering is the <b>person</b>, not the repeated decision. Konishi contains repeat study sessions for some participants; they retain the same person ID. Aguilar-Lleyda records color and letter choices in the same trial: primary color is analyzed alone and letter is supplementary. No task or subject is treated as randomly assigned to another study.'),
 P('Sensitivity and uncertainty','section'),
 P('Rouault includes exploratory participant-quality exclusions because the original article’s final 46-person selection cannot be fully reconstructed from public comprehension-question data; '+str(int(S.iloc[0].participants))+' people with confidence reports enter this re-analysis. Konishi within-session person-mean centering was also checked. Aguilar-Lleyda adds a participant-cluster bootstrap because only '+str(int(S.iloc[1].participants))+' participants contribute to that study; such small-cluster inference is still exploratory.'),
 P('Rouault additionally compares GEE to a conditional random-intercept logistic GLMM fitted by adaptive Gauss-Hermite marginal likelihood and resampling complete participant clusters. This method replaces the previous, over-precise variational-Bayes interval; the two model families target different marginal/conditional associations.'),
 P('Interpretive boundaries','section'),
 P('A positive coefficient predicts larger <i>odds</i> of correctness, not an equal change in the probability or an effect of manipulating confidence. A bin of average confidence versus average accuracy illustrates average calibration but does not estimate a trial-level calibration curve or metacognitive sensitivity in the signal-detection sense.'),
 PageBreak()])
# 3 - findings
mainrows=[['Primary task','Within (95% robust CI)','Between (95% robust CI)']]
for row in S.itertuples(index=False):
    mainrows.append([f'{row.dataset.split()[0]}: {row.task}',prettyrow(row,'within_'),prettyrow(row,'between_')])
ci_glmm=interval(GLMM.loc['between_10pp','cluster_boot_ci_025'],GLMM.loc['between_10pp','cluster_boot_ci_975'])
ci_gee=interval(GEE.loc['between_10pp','ci_025'],GEE.loc['between_10pp','ci_975'])
a_boot_with=A_BOOT.query("term == 'within_10pp'").iloc[0]
k_session=K_SESS.query("term == 'within_10pp'").iloc[0]
s.extend([P('2  Results','title'),P('Primary associations','section'),
 tab(mainrows,[150,177,175]),
 P('All effects are GEE log-odds slopes per +10 percentage points confidence. Their intervals are not independent across primary analyses if studies share participants; no formal cross-study meta-analysis was fitted. All three within-person intervals are positive; all three between-person GEE intervals include zero.'),
 P('Within-minus-between contrasts','section'),
 P('Exploratory joint-model contrasts (within slope minus between slope): Rouault '+sign(R_CONTR.within_minus_between)+' '+interval(R_CONTR.ci_025,R_CONTR.ci_975)+'; Aguilar-Lleyda (color) '+sign(A_CONTR.coef)+' '+interval(A_CONTR.ci_lower,A_CONTR.ci_upper)+'; Konishi (single motion) '+sign(K_PRIMARY.within_minus_between_logodds)+' '+interval(K_PRIMARY.difference_ci_lower,K_PRIMARY.difference_ci_upper)+'. These are model-based associations and involve different tasks and participants.'),
 P('Sensitivity checks','section'),
 P('Rouault exploratory screening retained '+', '.join(str(int(x)) for x in SENS.participants)+' people across four conditions, and within-person GEE estimates ranged from '+sign(SENS.within_estimate.min())+' to '+sign(SENS.within_estimate.max())+'. In Konishi, centering within each participant–experiment session yielded a within slope of '+sign(k_session.estimate)+' '+interval(k_session.ci_lower,k_session.ci_upper)+', compared with '+sign(K_PRIMARY.within_10pp_logodds)+' under participant-wide centering.'),
 P('For Aguilar-Lleyda, a '+str(int(a_boot_with.bootstrap_valid))+'-draw participant-cluster percentile bootstrap produced a color-task within-person interval '+interval(a_boot_with.ci_lower,a_boot_with.ci_upper)+'. With only '+str(int(S.iloc[1].participants))+' independent people, confidence limits should not be regarded as conclusive without additional samples.'),
 P('Between-person GLMM versus GEE: unresolved inferential sensitivity','section'),
 P('The previous variational-Bayes interval was judged unreliable and withdrawn as evidence. In Rouault, GEE gave between-person '+sign(GEE.loc['between_10pp','estimate'])+' '+ci_gee+' (marginal), while the numerically integrated GLMM gave '+sign(GLMM.loc['between_10pp','mle_estimate'])+' '+ci_glmm+' (conditional; '+str(int(GLMM_META.bootstrap_valid))+' participant-bootstrap draws). The GLMM lower limit lies very close to zero; conclusions about the between-person effect are <b>method-sensitive and fragile</b>. These two model coefficients are not directly interchangeable.'),
 PageBreak()])
# 4 - limitations and reproducibility
s.extend([P('3  Interpretation and limitations','title'),
 P('What can be concluded?','section'),
 P('Within the examined perceptual tasks, a person tends to be more accurate when their confidence exceeds their usual level. This pattern was seen in three selected sources under prespecified-in-code but <b>not preregistered</b> analysis choices. It does not establish an intervention effect of increasing confidence, a general human personality trait, or a result extending to economic, emotional, clinical or human–AI decisions.'),
 P('Limitations a PI should inspect','section')])
for bullet in [
 'Only selected visual perceptual tasks were studied, and the sample-selection rationale evolved during exploration. Konishi was held aside during development but there was no formal preregistration.',
 'Rouault original exclusion rules selected 46 of 73; full comprehension-question data are absent, so this archive uses alternative exploratory screens.',
 'Between-person inference uses relatively few independent clusters compared with total decisions; the Aguilar-Lleyda participant bootstrap is sensitive to the limited 28-person pool.',
 'Difficulty is adjusted, but trial order, fatigue, learning and differences in feedback or experimental setting may still confound associations.',
 'Multiple models, outcomes and sensitivity checks create multiplicity concerns; results should not be read as a familywise-confirmatory discovery.',
 'The earlier variational-Bayes model gave a suspiciously narrow interval. Numerical GLMM refitting lessens but does not remove model dependence; calibration and discrimination remain distinct outcomes.'
]: s.append(P('• '+escape(bullet),'small'))
s.extend([P('Reproduce the analysis','section'),
 P('From the supplied Python environment install dependencies with <b>pip install -r requirements.txt</b>, then execute <b>python run_all.py</b>. The runner rebuilds CSV results, plots and this report, then calls validation tests. To inspect the corrected mixed-model conflict, see <b>STATISTICAL_AUDIT.md</b>. The source CSVs are unchanged and are available under the Confidence Database CC0 data release; original source studies must be credited.'),
 P('Research transparency','section'),
 P('This is a student secondary-data project prepared with AI coding assistance. It is not a peer-reviewed publication. A standalone prospective preregistered study, robust replication with new participants, and external-domain data would be needed for stronger generalizability claims.'),
 P('References','section')])
for ref in [
 'Rahnev, D., et al. (2020). The Confidence Database. Nature Human Behaviour 4:317–325. doi:10.1038/s41562-019-0813-1.',
 'Rouault, M., Dayan, P., & Fleming, S. M. (2019). Forming global beliefs about self-performance from local confidence. Nature Communications 10:1141. doi:10.1038/s41467-019-09075-3.',
 'Aguilar-Lleyda, D., Lemarchand, M., & de Gardelle, V. (2018). Confidence as a priority signal. bioRxiv 480350. (See original README.)',
 'Konishi, M., et al. (2019). Metacognition is spared in a dual-task visual paradigm. doi:10.31234/osf.io/xcseh.',
 'Data: https://osf.io/s46pr/; each study’s contributed README is retained in the archive.'
]:s.append(P('• '+escape(ref),'small'))

pdf=SimpleDocTemplate(str(OUT),pagesize=A4,leftMargin=45,rightMargin=45,topMargin=44,bottomMargin=55,
 title='The Confidence Paradox | Reproducible exploratory secondary-data analysis',author='Kimia Pasandideh')
pdf.build(s,onFirstPage=footer,onLaterPages=footer)
print('Generated source-linked report:',OUT)
