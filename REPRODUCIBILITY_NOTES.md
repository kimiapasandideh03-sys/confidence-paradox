# Provenance, versions, and methodological notes

- Dataset origin: [The Confidence Database](https://osf.io/s46pr/) (Rahnev et al., 2020); project CC0 1.0 data. Cite database AND original studies. The contributing README files describe their designs and relevant exclusions.
- Dataset SHA-256 digests are in `SHA256_SOURCE_FILES.txt`; all original CSVs are preserved unchanged.
- Do not equate the old **VB** posterior interval with a frequentist 95% confidence interval; that output was withdrawn from primary inference.
- Numerical random-intercept GLMM: adaptive Gauss-Hermite quadrature, participant-cluster percentile bootstrap. Bootstrap resamples keep observed within-person centering fixed; they do not remedy all model or selection biases. Random-intercept normality and conditional independence are assumptions.
- We do not claim a comparison of GEE and GLMM is a formal test of a common population estimand: conditional and population-average log-odds are different.
- Aguilar-Lleyda: only 28 independent participants. Participant-cluster bootstrap is exploratory and cannot eliminate all small-cluster issues; all bootstrapped duplicates receive new cluster IDs.
- Konishi: session-centered sensitivity computes confidence deviation relative to **each (person, experiment) session**, but uncertainty remains clustered by **person**. Between-session slope from that sensitivity is **not the same estimand** as the primary between-person slope.
- Regression adjustment for trial difficulty does not address every potential confounder (order, fatigue, feedback, learning). No preregistration; multiplicity remains.
- Some original Rouault exclusion information is unavailable; the four alternative thresholds are **not** reconstructions of the original final 46-person sample.
- The secondary random-slope predictive model comparison previously explored is **not included in this validated pipeline**; claims from those older exploratory files should not be put in a CV.

## Tested environment (reference only)

| Component | Tested version |
|---|---|
| Python | 3.13 |
| numpy | 2.3.5 |
| pandas | 2.2.3 |
| scipy | 1.17.0 |
| statsmodels | 0.14.6 |
| matplotlib | 3.10.8 |
| reportlab | 4.4.9 |

`requirements.txt` uses compatible version ranges; the versions above record a verified environment, not a guarantee of bit-identical results on any platform. Run `python run_all.py` to regenerate numeric results; fixed seeds provide more stable stochastic resampling, but small cross-platform differences can occur.
