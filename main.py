#!/usr/bin/env python3
"""Entry point for the Supernova simulation GUI or headless batch mode.

Run:
  python main.py --help
"""
from __future__ import annotations
import argparse
import sys
import json
import csv
from pathlib import Path
from supernova_sim import SupernovaSimulation
# NOTE: PyQt5 imported lazily only if GUI requested.


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Run the Supernova galaxy simulation (GUI or headless)")
    p.add_argument('--num-intervals', type=int, default=10_000)
    p.add_argument('--interval-years', type=float, default=1e6)
    p.add_argument('--rate-per-year', type=float, default=0.02)
    p.add_argument('--R', type=float, default=50_000, help='Galaxy radius (ly)')
    p.add_argument('--h', type=float, default=1_000, help='Galaxy disk thickness (ly)')
    p.add_argument('--bubble-r', type=float, default=50, help='Lethal bubble radius (ly)')
    p.add_argument('--ngrid-xy', type=int, default=200)
    p.add_argument('--ngrid-z', type=int, default=50)
    p.add_argument('--max-threshold', type=int, default=5)
    p.add_argument('--no-civs', action='store_true', help='Disable civilization simulation')
    p.add_argument('--civ-emergence-rate', type=float, default=1/1e9, help='New civs per year')
    p.add_argument('--seed', type=int, default=42)
    p.add_argument('--update-ms', type=int, default=10, help='GUI update interval (ms)')
    # Headless / batch options
    p.add_argument('--no-gui', action='store_true', help='Run headless (no GUI) and exit when complete')
    p.add_argument('--output', type=Path, help='Output file path for headless mode (JSON or CSV)')
    p.add_argument('--output-format', choices=['json', 'csv'], help='Explicit output format (inferred from extension if omitted)')
    p.add_argument('--quiet', action='store_true', help='Reduce stdout in headless mode')
    return p


def run_headless(sim: SupernovaSimulation, args):
    if not args.quiet:
        print("[Headless] Running simulation...")
    while True:
        r = sim.step()
        if not r:
            break
    if not args.quiet:
        print(f"[Headless] Completed intervals: {sim.current_interval}")
        print(f"[Headless] Total supernovae: {sim.supernovae}")
    if args.output:
        fmt = args.output_format
        if fmt is None:
            suffix = args.output.suffix.lower()
            if suffix == '.json':
                fmt = 'json'
            elif suffix == '.csv':
                fmt = 'csv'
            else:
                fmt = 'json'
        if fmt == 'json':
            payload = {
                'parameters': {
                    'num_intervals': sim.num_intervals,
                    'interval_years': sim.interval_years,
                    'rate_per_year': sim.rate_per_year,
                    'R': sim.R,
                    'h': sim.h,
                    'bubble_r': sim.bubble_r,
                    'ngrid_xy': sim.ngrid_xy,
                    'ngrid_z': sim.ngrid_z,
                    'max_threshold': sim.max_threshold,
                    'simulate_civilizations': sim.simulate_civilizations,
                    'civ_emergence_rate': sim.civ_emergence_rate,
                    'seed': args.seed,
                },
                'intervals': sim.intervals,
                'coverage_history': sim.coverage_history,
                'civ_history': sim.civ_history,
                'supernovae': sim.supernovae,
            }
            args.output.write_text(json.dumps(payload, indent=2))
            if not args.quiet:
                print(f"[Headless] Wrote JSON to {args.output}")
        else:  # csv
            fieldnames = ['interval', 'supernovae', 'civ_count'] + [f'coverage_ge_{th}' for th in range(1, sim.max_threshold + 1)]
            with args.output.open('w', newline='') as f:
                w = csv.DictWriter(f, fieldnames=fieldnames)
                w.writeheader()
                for idx, interval in enumerate(sim.intervals):
                    row = {
                        'interval': interval,
                        'supernovae': sim.supernovae,  # final total (per-row cumulative could be added)
                        'civ_count': sim.civ_history[idx] if sim.simulate_civilizations and idx < len(sim.civ_history) else '',
                    }
                    for th in range(1, sim.max_threshold + 1):
                        row[f'coverage_ge_{th}'] = sim.coverage_history[th][idx]
                    w.writerow(row)
            if not args.quiet:
                print(f"[Headless] Wrote CSV to {args.output}")


def main(argv=None):
    args = build_arg_parser().parse_args(argv)
    sim = SupernovaSimulation(
        num_intervals=args.num_intervals,
        interval_years=args.interval_years,
        rate_per_year=args.rate_per_year,
        R=args.R,
        h=args.h,
        bubble_r=args.bubble_r,
        ngrid_xy=args.ngrid_xy,
        ngrid_z=args.ngrid_z,
        max_threshold=args.max_threshold,
        simulate_civilizations=not args.no_civs,
        civ_emergence_rate=args.civ_emergence_rate,
        seed=args.seed,
    )
    if args.no_gui:
        run_headless(sim, args)
        return
    # GUI path (import here so headless mode has no Qt dependency)
    from PyQt5 import QtWidgets  # type: ignore
    from supernova_sim.gui import MainWindow
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow(simulation=sim, update_ms=args.update_ms)
    win.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
