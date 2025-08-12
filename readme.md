# Supernova Galaxy Simulation

This project simulates supernova events within a spiral galaxy disk (Milky Way–like). It tracks impacts of supernovae on a 3D discretized disk and (optionally) the emergence and extinction of civilizations. Numba accelerates core loops and PyQtGraph provides a live GUI.

## Features

- **Supernova Simulation**: Stochastic supernova events via Poisson statistics.
- **3D Galaxy Grid**: Cylindrical disk sampled on a Cartesian grid with masking.
- **Civilization Dynamics (optional)**: Random emergence; extinction if inside a lethal bubble.
- **Real-Time Visualization (PyQtGraph)**:
  - Disk coverage vs interval for multiple hit thresholds.
  - Living civilization count vs interval.
  - Hit count histogram.
  - 2D heat map slice of mid-plane hit counts.

## Project Structure

```
main.py                     # CLI / GUI entry point
supernova_sim/
  __init__.py               # package export
  simulation.py             # SupernovaSimulation class (logic/state)
  numba_core.py             # Numba-accelerated inner functions
  gui.py                    # PyQtGraph MainWindow

galaxy_sim.ipynb            # (Legacy / exploratory notebook)
readme.md
```

## Requirements

- Python 3.9+
- numpy
- numba
- pyqtgraph
- PyQt5 (or PyQt6; adjust import if needed)

Install:
```bash
pip install numpy numba pyqtgraph PyQt5
```

## Quick Start

Run the GUI with defaults:
```bash
python main.py
```
Show available options:
```bash
python main.py --help
```
Example custom run:
```bash
python main.py \
  --num-intervals 5000 \
  --interval-years 1e6 \
  --rate-per-year 0.02 \
  --R 50000 --h 1000 \
  --bubble-r 75 \
  --ngrid-xy 150 --ngrid-z 40 \
  --max-threshold 6 \
  --civ-emergence-rate 1e-9 \
  --seed 123
```
Disable civilization simulation:
```bash
python main.py --no-civs
```
Faster lightweight test (small grid):
```bash
python main.py --num-intervals 200 --ngrid-xy 80 --ngrid-z 20 --bubble-r 40
```

## Command-Line Arguments (maps directly to SupernovaSimulation)

- --num-intervals: Total simulation intervals.
- --interval-years: Years per interval.
- --rate-per-year: Mean supernova rate (events/year).
- --R: Galaxy radius (ly).
- --h: Disk thickness (ly).
- --bubble-r: Lethal bubble radius (ly).
- --ngrid-xy / --ngrid-z: Grid resolution.
- --max-threshold: Highest hit threshold tracked for coverage curves.
- --no-civs: Disable civilization modeling.
- --civ-emergence-rate: New civilizations per year (Poisson; internally scaled by interval years).
- --seed: RNG seed.
- --update-ms: GUI refresh timer (milliseconds).

## Adjusting Parameters Programmatically

You can also import and run headless logic:
```python
from supernova_sim import SupernovaSimulation
sim = SupernovaSimulation(num_intervals=1000, ngrid_xy=100, ngrid_z=30)
while True:
    result = sim.step()
    if not result:
        break
print("Total supernovae:", sim.supernovae)
```
(Headless batch / data export helpers can be added; ask if you want this scaffold.)

## Legacy Notebook

The original exploratory notebook (galaxy_sim.ipynb) is retained but the authoritative code now lives in the package and main.py. Prefer modifying simulation.py for logic changes and gui.py for visualization tweaks.

## Extending the Simulation

Ideas:
- Increase grid resolution (performance scales roughly with number of active cells * events).
- Non-uniform spatial SN distribution (e.g., exponential radial profile, thin/thick disk weighting).
- Different event types (gamma-ray bursts) with distinct lethal radii.
- Civilization growth/spread models; longevity distributions.
- Star formation history & IMF/PDMF to drive spatial/temporal SN rates.
- Persistence layer: periodically serialize state for long runs.
- Headless batch mode producing CSV / HDF5 outputs.

## Performance Notes

- First step JIT-compiles Numba functions; expect an initial latency.
- Smaller bubble_r relative to cell size reduces per-event loop volume (rx, ry, rz window).
- For very large grids consider profiling and possibly tiling or sparse representations.

## License

(Add a license section here if you intend to distribute.)

## Contributing

Open issues / PRs for enhancements, optimizations, or scientific modeling improvements.
