"""Reproduce all THREE primary study analyses + Rouault sensitivity and GLMM.

Usage: python run_all.py
       python run_all.py --glmm-bootstrap 100  # fast smoke test
"""
from pathlib import Path
import argparse,subprocess,sys,time,shutil
ROOT=Path(__file__).resolve().parent
p=argparse.ArgumentParser()
p.add_argument('--glmm-bootstrap',type=int,default=500)
p.add_argument('--aguilar-bootstrap',type=int,default=300)
a=p.parse_args()
preliminary=a.glmm_bootstrap<500 or a.aguilar_bootstrap<300
if preliminary:
    print('WARNING: PRELIMINARY SMOKE TEST; short-bootstrap PDF must NOT be cited. Run defaults for full report.',flush=True)
commands=[
  ('Rouault GEE + participant bootstrap + exclusions + integrated GLMM',
     ['scripts/rouault_models.py','--input','data/data_Rouault_2019.csv',
      '--outdir','results/generated/rouault','--figdir','figures','--bootstrap-reps',str(a.glmm_bootstrap)]),
  ('Aguilar-Lleyda GEE (color/letter)',
     ['scripts/aguilarlleyda_gee.py','--input','data/data_AguilarLleyda_2018.csv','--outdir','results/generated/aguilarlleyda','--cluster-bootstrap-reps',str(a.aguilar_bootstrap)]),
  ('Konishi GEE (primary motion and sensitivity conditions)',
     ['scripts/konishi_gee.py','--input','data/data_Konishi_2019.csv','--out','results/generated/konishi']),
]
for title,command in commands:
    print('\n###',title,flush=True)
    t=time.monotonic()
    subprocess.run([sys.executable,*command],cwd=ROOT,check=True)
    print(f'Completed in {time.monotonic()-t:.1f} s',flush=True)
# Sync supplementary figures from their freshly generated locations so the
# README's canonical figures/ folder can never contain stale images.
figure_map = {
    'results/generated/aguilarlleyda/calibration_col.png': 'figures/aguilarlleyda_calibration.png',
    'results/generated/konishi/konishi_motion_calibration.png': 'figures/konishi_motion_calibration.png',
    'results/generated/konishi/konishi_within_effects.png': 'figures/konishi_within_effects.png',
}
for generated, canonical in figure_map.items():
    src, dst = ROOT/generated, ROOT/canonical
    if not src.is_file():
        raise FileNotFoundError(f'Required newly generated figure is missing: {src}')
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)

subprocess.run([sys.executable,'scripts/summarize_studies.py'],cwd=ROOT,check=True)
subprocess.run([sys.executable,'scripts/build_report.py'],cwd=ROOT,check=True)
# Fail loudly when outputs are missing, inconsistent, or malformed.
subprocess.run([sys.executable,'tests/validate_outputs.py']+(['--smoke'] if preliminary else []),cwd=ROOT,check=True)
print('\nALL PRIMARY ANALYSES, ROUAULT SUPPLEMENTS, FIGURES, REPORT AND VALIDATION SUCCEEDED.',flush=True)
