#!/usr/bin/env python3
"""
reproduce_v9.py — One-command reproduction of the Kassanjee v9 manuscript
load-bearing statistics and figures from raw AIDSVu surveillance data.

Usage:
    python reproduce_v9.py                  # full pipeline + verification (~3 min)
    python reproduce_v9.py --skip-figures   # numbers only, ~5x faster
    python reproduce_v9.py --no-verify      # skip verification step

Pipeline stages, each writes into a single timestamped directory runs/<TS>/:

    Stage 1/4: build_xlxs.py
        raw AIDSVu .xlsx → aidsvu_combined_2014_2023_FULL.xlsx
                          + Stratum_Aggregates.csv, MSA_Panel.csv,
                            State_Panel.csv, CDC_220_VanHandel.csv,
                            Statistics_Summary.csv, run_metadata.txt

    Stage 2/4: rebuild_figures.py
        Figure_2_stratum_trajectories.{png,pdf}
        Figure_3_covid_counterfactual.{png,pdf}

    Stage 3/4: compute_covid_deficit.py
        covid_deficit_per_stratum.csv (§S8.5.1)
        covid_deficit_summary.txt
        fig_covid_counterfactual.{png,pdf}

    Stage 4/4: verify_v9.py
        Statistics_Summary.csv vs expected_v9_statistics.csv → PASS/FAIL

Exits 0 on full pass, non-zero on any failure. Designed to be invoked by a
JAIDS reviewer with no prior context — see REPRODUCE.md for environment setup.

Operator: Dr. A.C. Demidont, DO
"""
import argparse
import re
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent

REQUIRED_INPUTS = [
    'cdc_220_counties.csv',
    'expected_v9_statistics.csv',
]
REQUIRED_AIDSVU_GLOBS = [
    'AIDSVu_County_NewDX_*.xlsx',
    'AIDSVu_State_NewDX_*.xlsx',
]
REQUIRED_SCRIPTS = [
    'build_xlxs.py',
    'rebuild_figures.py',
    'compute_covid_deficit.py',
    'verify_v9.py',
]


def check_prerequisites():
    missing = []
    for f in REQUIRED_INPUTS + REQUIRED_SCRIPTS:
        if not (REPO_ROOT / f).exists():
            missing.append(f)
    for pattern in REQUIRED_AIDSVU_GLOBS:
        if not list(REPO_ROOT.glob(pattern)):
            missing.append(f'{pattern} (no matching files)')
    return missing


def run_stage(name, cmd, cwd=None, capture=True):
    """Run a subprocess stage. Streams stdout if capture=False, captures otherwise.
    Exits the entire orchestrator on non-zero return code."""
    print()
    print('-' * 72)
    print(f'STAGE: {name}')
    display_cmd = ' '.join(str(c) for c in cmd)
    print(f'  $ {display_cmd}')
    if cwd:
        print(f'  cwd: {cwd}')
    print('-' * 72)
    t0 = time.time()
    result = subprocess.run(cmd, capture_output=capture, text=True, cwd=cwd or REPO_ROOT)
    elapsed = time.time() - t0
    if capture:
        print(result.stdout, end='' if result.stdout.endswith('\n') else '\n')
        if result.stderr:
            print('STDERR:', result.stderr, file=sys.stderr)
    print(f'  ({elapsed:.1f}s)')
    if result.returncode != 0:
        print(f'\nSTAGE FAILED: {name} (exit code {result.returncode})')
        sys.exit(result.returncode)
    return result


def parse_run_dir(stdout):
    """build_xlxs.py prints 'Output directory: <abs_path>' in its opening banner."""
    m = re.search(r'Output directory:\s*(\S+)', stdout)
    if not m:
        print('ERROR: could not parse run directory from build_xlxs.py output.')
        print('       Expected a line matching "Output directory: <path>".')
        sys.exit(2)
    return Path(m.group(1))


def main():
    parser = argparse.ArgumentParser(
        description='One-command reproduction of the Kassanjee v9 manuscript.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split('\n', 1)[1] if __doc__ else '',
    )
    parser.add_argument('--skip-figures', action='store_true',
                        help='Skip figure regeneration (Stages 2-3); ~5x faster')
    parser.add_argument('--no-verify', action='store_true',
                        help='Skip verification (Stage 4); useful for debugging')
    args = parser.parse_args()

    banner = '=' * 72
    print(banner)
    print('Kassanjee v9 manuscript — reproduction suite')
    print(f'Repo root: {REPO_ROOT}')
    print(banner)

    # Prerequisite check
    missing = check_prerequisites()
    if missing:
        print('\nERROR: missing required files:')
        for f in missing:
            print(f'  - {f}')
        print('\nSee REPRODUCE.md for environment setup.')
        sys.exit(2)
    print(f'\nPrerequisites OK: {len(REQUIRED_INPUTS + REQUIRED_SCRIPTS)} files'
          f' + AIDSVu xlsx files present.')

    # Stage 1: build_xlxs.py — emits its own timestamped run directory
    r1 = run_stage('1/4 — Ingest AIDSVu, build panels and stratum aggregates',
                   [sys.executable, 'build_xlxs.py'])
    run_dir = parse_run_dir(r1.stdout)
    if not run_dir.is_absolute():
        run_dir = REPO_ROOT / run_dir
    print(f'\nRun directory parsed: {run_dir}')

    xlsx_path = run_dir / 'aidsvu_combined_2014_2023_FULL.xlsx'
    stats_csv = run_dir / 'Statistics_Summary.csv'
    if not xlsx_path.exists():
        print(f'ERROR: expected workbook missing: {xlsx_path}')
        sys.exit(2)
    if not stats_csv.exists():
        print(f'ERROR: expected statistics CSV missing: {stats_csv}')
        sys.exit(2)

    # Stages 2 + 3: figures + COVID deficit
    if not args.skip_figures:
        # rebuild_figures.py writes Figure_2 / Figure_3 to its cwd; run it
        # with cwd = run_dir so outputs colocate with everything else.
        run_stage('2/4 — Rebuild manuscript figures (Fig 2 + Fig 3)',
                  [sys.executable, str(REPO_ROOT / 'rebuild_figures.py'),
                   '--input-xlsx', str(xlsx_path)],
                  cwd=run_dir)

        # compute_covid_deficit.py exposes explicit output args; point all into run_dir.
        run_stage('3/4 — Compute COVID counterfactual deficits',
                  [sys.executable, 'compute_covid_deficit.py',
                   '--input-xlsx', str(xlsx_path),
                   '--output-csv', str(run_dir / 'covid_deficit_per_stratum.csv'),
                   '--output-txt', str(run_dir / 'covid_deficit_summary.txt'),
                   '--figure', str(run_dir / 'fig_covid_counterfactual.png')])
    else:
        print('\nSKIPPED: Stages 2-3 (--skip-figures)')

    # Stage 4: verify against manuscript reference values
    if not args.no_verify:
        run_stage('4/4 — Verify Statistics_Summary against v9 reference values',
                  [sys.executable, 'verify_v9.py',
                   '--statistics-csv', str(stats_csv),
                   '--expected-csv', 'expected_v9_statistics.csv'])
    else:
        print('\nSKIPPED: Stage 4 (--no-verify)')

    print()
    print(banner)
    print('REPRODUCTION COMPLETE')
    print(f'Run directory:  {run_dir}')
    print(f'Key outputs:')
    print(f'  - {run_dir / "aidsvu_combined_2014_2023_FULL.xlsx"}')
    print(f'  - {run_dir / "Stratum_Aggregates.csv"}  (deposit-ready)')
    print(f'  - {run_dir / "Statistics_Summary.csv"}  (verification target)')
    if not args.skip_figures:
        print(f'  - {run_dir / "Figure_2_stratum_trajectories.pdf"}')
        print(f'  - {run_dir / "Figure_3_covid_counterfactual.pdf"}')
        print(f'  - {run_dir / "covid_deficit_per_stratum.csv"}')
    print(f'  - {run_dir / "run_metadata.txt"}  (provenance)')
    print(banner)


if __name__ == '__main__':
    main()
