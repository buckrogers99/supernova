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
- **Headless / Batch Mode**: Run without a GUI and export JSON or CSV.

## Project Structure

```
main.py                     # CLI / GUI & headless entry point
supernova_sim/
  __init__.py               # package export
  simulation.py             # SupernovaSimulation class (logic/state)
  numba_core.py             # Numba-accelerated inner functions
  gui.py                    # PyQtGraph MainWindow

readme.md
Dockerfile                  # Container build (GUI capable)
requirements.txt
```

## Requirements

- Python 3.9+
- numpy
- numba
- pyqtgraph
- PyQt5 (or PyQt6; adjust import if needed; not required for headless mode if you do not import gui)

Install:
```bash
pip install -r requirements.txt
```

## Quick Start (GUI)

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

## Headless / Batch Mode

Run without a GUI (no Qt dependency at runtime) and export results:
```bash
# JSON export (auto-detected by extension)
python main.py --no-gui --num-intervals 3000 --output results.json

# Explicit CSV export
python main.py --no-gui --output summary.csv --output-format csv --num-intervals 5000

# Quiet mode (minimal stdout)
python main.py --no-gui --output results.json --quiet
```
JSON payload includes parameters, coverage histories (fractions), civilization counts, and total supernovae. CSV rows list interval-wise coverage and civ counts.

## Command-Line Arguments (maps to SupernovaSimulation + runner)

- --num-intervals: Total simulation intervals.
- --interval-years: Years per interval.
- --rate-per-year: Mean supernova rate (events/year).
- --R: Galaxy radius (ly).
- --h: Disk thickness (ly).
- --bubble-r: Lethal bubble radius (ly).
- --ngrid-xy / --ngrid-z: Grid resolution.
- --max-threshold: Highest hit threshold tracked for coverage curves.
- --no-civs: Disable civilization modeling.
- --civ-emergence-rate: New civilizations per year (scaled by interval years internally).
- --seed: RNG seed.
- --update-ms: GUI refresh timer (ms).
- --no-gui: Run headless (no GUI) until completion.
- --output PATH: Write results (headless mode) to JSON or CSV.
- --output-format {json,csv}: Force output format (otherwise inferred from extension).
- --quiet: Suppress progress prints in headless mode.

## Adjusting Parameters Programmatically

```python
from supernova_sim import SupernovaSimulation
sim = SupernovaSimulation(num_intervals=1000, ngrid_xy=100, ngrid_z=30)
while True:
    if not sim.step():
        break
print("Total supernovae:", sim.supernovae)
```
(Headless helpers already integrated; use CLI for export.)

## Docker

Build image:
```bash
docker build -t supernova .
```
Run GUI (X11 forwarding example on Linux):
```bash
xhost +local:root
docker run --rm -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix supernova
```
Headless batch (no display needed):
```bash
docker run --rm supernova --no-gui --num-intervals 3000 --output results.json
```
Copy results out (mount a host volume):
```bash
docker run --rm -v "$(pwd)/out:/data" supernova \
  --no-gui --num-intervals 5000 --output /data/results.json
```

macOS note: For GUI inside container you need an X server (XQuartz) and set `-e DISPLAY=host.docker.internal:0` (allow connections in XQuartz preferences).

## Extending the Simulation

Ideas:
- Increase grid resolution (performance ~ active cells * events).
- Non-uniform spatial SN distribution (exponential radial profile, vertical scale height).
- Additional transient types (GRBs) with distinct lethality radii.
- Civilization growth/spread models; longevity distributions.
- Star formation history & IMF/PDMF driven temporal/spatial SN rates.
- State checkpointing & resume for very long runs.
- Parallel batch sweeps over parameter grids (e.g., via multiprocessing or Snakemake).

## Performance Notes

- First step JIT-compiles Numba functions (warm-up cost).
- Bubble radius vs cell size controls per-event loop volume (rx, ry, rz window extents).
- Consider profiling (e.g., `numba --annotate-html` or external profilers) for large grids.

## Scientific Assumptions (Current Simplifications)

- Uniform spatial SN distribution in disk interior.
- Instantaneous lethal sphere; no radiation falloff gradient.
- Independent events; no clustering or spiral arm structure.
- Civilization emergence is spatially uniform (subject to disk mask) and temporally Poisson.

## Contributing

Open issues / PRs for enhancements, optimizations, or scientific modeling improvements.
