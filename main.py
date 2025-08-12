#!/usr/bin/env python3
"""Entry point for the Supernova simulation GUI.

Run:
  python main.py --help
"""
from __future__ import annotations
import argparse
import sys
from PyQt5 import QtWidgets
from supernova_sim import SupernovaSimulation
from supernova_sim.gui import MainWindow

def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Run the Supernova galaxy simulation GUI")
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
    return p

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
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow(simulation=sim, update_ms=args.update_ms)
    win.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
