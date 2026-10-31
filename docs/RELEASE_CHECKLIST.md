# Publication checklist (verify before citing in a CV)

- [ ] From a fresh clone, create a new Python environment and install `requirements.txt`.
- [ ] Run `python run_all.py` with **no** shortened Bootstrap arguments; keep the terminal completion log.
- [ ] Check `results/generated/rouault/rouault_glmm_diagnostics.csv`: 500 requested, valid fits recorded; check Aguilar bootstrap `bootstrap_requested=300`, `bootstrap_valid` recorded.
- [ ] Run `python tests/validate_outputs.py` (not `--smoke`) and confirm PASS.
- [ ] Verify `report/Confidence_Paradox_Research_Report.pdf` matches the README, including all reported caveats.
- [ ] Check repository root includes only a concise README, entrypoint and dependencies; supporting docs are under `docs/`.
- [ ] Use the clean public URL: https://github.com/kimiapasandideh03-sys/confidence-paradox
- [ ] Do not submit the superseded seven-page PDF containing outdated VB-only limitations.
- [ ] Ensure student name and university are correct and acceptable to display publicly.

The code/data claims here are exploratory, observational and not externally peer reviewed.
