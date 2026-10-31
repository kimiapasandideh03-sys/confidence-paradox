# Statistical discrepancy audit — Rouault 2019

## Why the old Variational Bayes finding is not publication-ready

The earlier statsmodels variational-Bayes random-intercept GLMM yielded a
between-person estimate **+0.151**, with approximate posterior interval
**[+0.112, +0.190]**, excluding zero. This interval is suspiciously narrow:
its reported posterior SD (~0.0198) nearly duplicates the within-person SD
(~0.0198), despite having only 72 independent person-level means to inform
the between-person relationship. Matching SDs do **not** alone prove an error,
but demand an independent uncertainty check.

## Independently refitted results (identical 12,960 rated decisions; 72 people)

| Analysis | Between-person coefficient, per +10pp confidence | Reported interval | Scale / uncertainty |
|---|---:|---|---|
| GEE, exchangeable + cluster-robust sandwich | +0.046 | [-0.031, +0.124] | Population-averaged log-odds; 95% robust CI |
| **GLMM: marginal maximum likelihood, adaptive Gauss-Hermite** | **+0.151** | **[+0.002, +0.297]** | Subject-specific log-odds; 95% participant-bootstrap CI (500 valid samples) |
| Previous VB GLMM (diagnostic only; not reproduced by this release) | +0.151 | [+0.112, +0.190] | Approximate posterior interval, **not reliable for a significance claim** |

GLMM within-person: +0.458
with participant-bootstrap interval
[+0.397, +0.530].
For the GLMM, the participant random intercept has estimated SD
0.658.

### Method check

- The GLMM integrates the normal participant-specific random intercept via
  **adaptive 15-node Gauss-Hermite quadrature**, using likelihood maximization.
  Objective and estimates were independently checked for stability using
  10, 12, 15, 20 and 30 adaptive integration nodes.
- **500 resamples of participants with replacement**; all 500 fits valid, fixed RNG seed 2026.
  Bootstrap duplicates whole participant response clusters, not single trials.
- The random intercept is assumed normally distributed and independent of
  predictors; the bootstrap does not eliminate all possible model biases.
- GLMM coefficients condition on participant-specific random effects; GEE
  coefficients are population-averaged. **Their point estimates need not agree**,
  so the difference in coefficient size is not itself a fitting error.
- The corrected participant-bootstrap GLMM interval **barely excludes zero** (lower bound ~+0.002), while the GEE interval includes zero; this is borderline and method-sensitive.
  The safe cross-method conclusion is that the data do not robustly establish
  the between-person effect's sign. VB significance is withdrawn.

**Scope:** Exploratory secondary-data analysis, not a preregistered study or
reproduction of the 46-person original Rouault exclusion sample.

## Additional checks for the publication-readiness revision (26 October 2026)

The model summaries above refer to **results**, not proof of a causal relationship. More checks were added without replacing primary specifications:

1. **Aguilar-Lleyda, 28 independent persons.** A 300-attempt participant-cluster percentile bootstrap was conducted on the color GEE; **298 valid fits**. The within-person 95% interval is **[+0.233, +0.322]**, between-person interval **[-0.043, +0.114]**, and within-minus-between interval **[+0.144, +0.347]**. These are descriptive robustness checks with only 28 independent clusters; they do not eliminate small-sample inference concerns. All numeric limits are read from `results/generated/aguilarlleyda/color_cluster_bootstrap_intervals.csv`.
2. **Konishi session-level centering sensitivity.** Centering confidence by `(Subj_idx, exp)` and clustering uncertainty by `Subj_idx` gives within slope **+0.456 [0.421, 0.491]**, closely matching participant-level centering +0.457 [0.421, 0.493]. Between-session centering addresses a **different estimand**, so its between coefficient should not replace the primary between-person one. These values are in `results/generated/konishi/konishi_session_centering_sensitivity.csv`.
3. **Joint Within-minus-Between GEE contrasts.** Estimated using each model's complete covariance matrix (not by comparing separate significance tests). Results are stored in the corresponding Rouault, Aguilar, and Konishi outputs and generated into the PDF; interpretations remain exploratory across models.
4. **Automated number checks.** The report builder now loads all primary coefficients, sample sizes, Rouault GLMM values, bootstrap intervals and differences from generated CSVs. Validation includes the raw-data hashes and PDF text. This reduces the risk of silently retaining out-of-date numbers.
5. **Reproducibility evidence.** An earlier full Rouault GLMM 500-bootstrap run was completed and recorded in the corrected project. During this revision the new Aguilar-Lleyda 300-attempt participant bootstrap and Konishi analysis ran. A clean-directory end-to-end smoke test passed with 20 and 30 resamples, explicitly marked as **preliminary**, while an attempted full rerun in this revision exceeded the environment's execution time limit. Therefore **a new uninterrupted full 500+300 run in a fresh directory is not verified in this revision**. The packaged 500 GLMM draws are the previously verified results generated by the unchanged GLMM fitting code; newly added analyses and current manuscript derive from those plus the new full Aguilar draws. Anyone publishing these results should run the full default command locally as an independent check.

**Bottom line:** Consistent positive within-person effects survived the explored variations. Inference about the between-person GLMM effect remains fragile and must not be presented as a robust confirmation. No correction or supplementary analysis is a substitute for prospective preregistration or external validation.
