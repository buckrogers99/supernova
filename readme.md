# Supernova Galaxy Simulation

This project simulates supernova events within a spiral galaxy disk, specifically modeling the Milky Way. It tracks the impact of these events on nearby "cells" within the galaxy, which can also harbor civilizations. The simulation uses Numba for performance acceleration and PyQtGraph to provide a live-updating visualization of the simulation's progress.

## Features

- **Supernova Simulation**: Randomly simulates supernovae occurring within a disk-shaped galaxy.
- **3D Galaxy Modeling**: Uses a 3D grid to model the galaxy's structure and track supernova impacts.
- **Civilization Dynamics**: Simulates the emergence and extinction of civilizations affected by supernova events.
- **Real-Time Visualization**: Provides a PyQt-based GUI with live-updating plots:
  - **Disk Coverage Evolution**: Displays the percentage of the galaxy affected by supernova impacts over time.
  - **Civilization Count Evolution**: Shows the number of living civilizations throughout the simulation.
  - **Hit Count Histogram**: Represents the frequency of grid cells impacted by supernovae.

## Requirements

- Python 3.x
- NumPy
- Numba
- PyQtGraph
- PyQt5

Install the required packages using pip:

```bash
pip install numpy numba pyqtgraph PyQt5
```

Run the simulation in the `galaxy_sim.ipynd` file:

## Simulation Parameters

You can adjust the simulation’s behavior by modifying parameters in the SupernovaSimulation class within galaxy_sim.py. Key parameters include:

Simulation Settings:

- num_intervals: Total number of simulation intervals to run.
- interval_years: Number of years per interval.
- rate_per_year: Average number of supernovae per year.

Galaxy Dimensions:

- R: Radius of the galaxy disk (light-years).
- h: Thickness of the galaxy disk (light-years).

Supernova Impact:

- bubble_r: Radius of the lethal impact zone of a supernova (light-years).

Grid Resolution:

- ngrid_xy: Number of grid cells along the x and y axes.
- ngrid_z: Number of grid cells along the z-axis.

Civilization Settings:

- simulate_civilizations: Enable or disable civilization simulation.
- civ_emergence_rate: Rate at which new civilizations emerge (per year).

Random Seed:

- seed: Seed for random number generation to ensure reproducibility.

To modify these parameters, edit them directly when instantiating the SupernovaSimulation object in the main() function:

```python
sim = SupernovaSimulation(
    num_intervals=10000,
    interval_years=1e6,
    rate_per_year=0.02,
    R=50000,
    h=1000,
    bubble_r=50,
    ngrid_xy=200,
    ngrid_z=50,
    max_threshold=5,
    simulate_civilizations=True,
    civ_emergence_rate=1e-6,  # New civilizations per year
    seed=42
)
```

## Extending the Simulation

The simulation is designed to be flexible and extendable. Here are some ideas:

- Adjust Grid Resolution: Increase ngrid_xy and ngrid_z for a more detailed simulation (note that this will increase computational load).
- Modify Supernova Rates: Experiment with different rate_per_year values to simulate various galaxy environments.
- Introduce New Features: Add elements like gamma-ray bursts, civilization expansion, and civilization extinction.
- Data Analysis: Collect and analyze data on civilization lifespans, extinction events, or impact frequencies.
- Spatio-temporal Supernova Modeling: Incorporate spatial and temporal effects to model supernova events in a more complex galaxy environment. Given that supernovae belong to stars that are greater than 8 solar masses, and these stars burn fast, supernova events can only be found in areas that have recently formed stars.
- Incorporate an IMF and a PDMF to more accurately model the distribution of the mass of stars in the galaxy.
