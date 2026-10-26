# Changes and verification — 26 October 2026

## Main changes

- Fixed `run_all.py` synchronization of all canonical figure paths and automatic output-validation invocation (accepted in the previous review step).
- Recreated the Rouault GEE and its participant-filter sensitivity from raw CSV; verified previous coefficients in the prior review step.
- Replaced the README front matter with PI-friendly research question, informative figure, GEE table, one-command setup, caveat and provenance.
- Rewrote `scripts/summarize_studies.py` so study sample sizes are extracted from actual generated participant and model outputs, rather than hard-coded.
- Rewrote `scripts/build_report.py` to read GEE, sample sizes, contrasts, GLMM estimates, study-specific sensitivities and bootstrap results from source CSV files. No hand-entered inferential coefficient remains in the PDF generator.
- Applied one typography and muted teal/orange plotting scheme to main figures; titles describe content without suggesting causality.
- Added within-minus-between contrast for both Aguilar-Lleyda tasks using the joint GEE covariance matrix.
- Added Aguilar-Lleyda color participant-cluster bootstrap with 300 attempts (298 fitted); duplicate sampled participants are assigned new cluster IDs.
- Added Konishi primary motion sensitivity to centering within person-and-session while clustering by person.
- Expanded output tests to check source hashes, values across all three datasets, confidence intervals directly against saved bootstrap draws, report text, plots and data-source integrity.
- Added explicit smoke-test output labeling: reduced-bootstrap reports visibly say PRELIMINARY; the full output validator rejects these for full-report certification.
- Added data license, source citations and transparent AI assistance note.

## Execution evidence / limits

- **Clean-directory short-bootstrap end-to-end execution:** PASS. Every study, all plots, PDF regeneration, and automated checks were produced from raw CSVs without relying on pre-existing model results. Short run: Rouault 20 draws / Aguilar 30 attempts, for software integration only; such intervals must not be cited.
- **Rouault full 500-bootstrap results:** preserved from the previous successful numerically integrated GLMM run using the same GLMM fitting code; the new 500-run attempt during this revision hit the environment timeout. The package contains the previous complete full-run CSV draws and diagnostics, and these pass recomputation of their percentile limits.
- **Aguilar full 300-attempt bootstrap:** executed during this revision; 298 numerically valid model refits; participant resamples clustered correctly; percentile limits in CSV match saved draws.
- **Konishi session-centering:** executed during this revision; exact coefficient available in CSV and main PDF.
- **Final report:** four A4 pages; rendered and visually reviewed for clipping and legibility. All included statistical figures and estimates come from saved, traceable outputs.
- **New uninterrupted fresh-directory full 500+300 run:** not independently verified here. Run the default command on the student's machine before public release or CV submission.

## Still open by design, not hidden

- Original Rouault 46-person screening cannot be exactly recreated from available source material.
- The random-slope predictive comparison from early experimental files is *not* in this release; claims about its predictive improvement are withdrawn pending revalidation.
- Stronger causal, out-of-domain or preregistered claims require other data and methods.
- Distinct GEE/GLMM estimands prevent equating their coefficients or treating borderline bootstrap significance as proof.
