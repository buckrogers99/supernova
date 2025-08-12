"""Simulation logic for supernova events and (optional) civilization dynamics."""
from __future__ import annotations
import math
import random
from typing import Dict, List, Optional
import numpy as np
from .numba_core import run_supernova, generate_civilization

class SupernovaSimulation:
    """Encapsulates state and stepping logic for the supernova simulation."""
    def __init__(self,
                 num_intervals: int = 500,
                 interval_years: float = 1e6,
                 rate_per_year: float = 0.02,
                 R: float = 50000,
                 h: float = 1000,
                 bubble_r: float = 50,
                 ngrid_xy: int = 200,
                 ngrid_z: int = 50,
                 max_threshold: int = 5,
                 simulate_civilizations: bool = True,
                 civ_emergence_rate: float = 0.1,  # new civs per interval (rate * interval_years gives expected civs per interval)
                 seed: Optional[int] = 42) -> None:
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
        self.num_intervals = num_intervals
        self.interval_years = interval_years
        self.rate_per_year = rate_per_year
        self.R = R
        self.h = h
        self.bubble_r = bubble_r
        self.ngrid_xy = ngrid_xy
        self.ngrid_z = ngrid_z
        self.max_threshold = max_threshold
        self.simulate_civilizations = simulate_civilizations
        self.civ_emergence_rate = civ_emergence_rate
        self.civ_per_interval = civ_emergence_rate * interval_years
        self.current_interval = 0

        # Grid coordinate arrays.
        self.x = np.linspace(-R, R, ngrid_xy, dtype=np.float32)
        self.y = np.linspace(-R, R, ngrid_xy, dtype=np.float32)
        self.z = np.linspace(-h / 2, h / 2, ngrid_z, dtype=np.float32)
        self.dx = float(self.x[1] - self.x[0])
        self.dy = float(self.y[1] - self.y[0])
        self.dz = float(self.z[1] - self.z[0])

        # Domain mask (cells in (x,y) with x^2+y^2 <= R^2).
        X2, Y2 = np.meshgrid(self.x, self.y, indexing='ij')
        domain2d = (X2**2 + Y2**2 <= R**2)
        self.domain_mask = np.repeat(domain2d[:, :, np.newaxis], ngrid_z, axis=2)
        self.total_domain_cells = int(np.count_nonzero(self.domain_mask))

        # Hit count grid.
        self.hit_count = np.zeros((ngrid_xy, ngrid_xy, ngrid_z), dtype=np.int32)
        self.supernovae = 0
        self.coverage_history: Dict[int, List[float]] = {th: [] for th in range(1, max_threshold + 1)}

        # Civilization data.
        self.civilizations: List[dict] = []
        self.next_civ_id = 0
        self.civ_history: List[int] = []

        # Precompute grid steps needed to cover the bubble.
        self.rx = int(math.ceil(bubble_r / self.dx))
        self.ry = int(math.ceil(bubble_r / self.dy))
        self.rz = int(math.ceil(bubble_r / self.dz))

        # Expected number of supernova events per interval.
        self.mean_events = self.rate_per_year * self.interval_years

        # For plotting.
        self.intervals: List[int] = []

    def step(self):  # returns dict or False
        if self.current_interval >= self.num_intervals:
            return False

        # Supernova events this interval.
        num_events = np.random.poisson(self.mean_events)
        for _ in range(num_events):
            x0, y0, z0, _new_hits = run_supernova(
                self.hit_count, self.domain_mask, self.R, self.h,
                self.supernovae, self.dx, self.dy, self.dz,
                self.rx, self.ry, self.rz, self.bubble_r
            )
            self.supernovae += 1

            if self.simulate_civilizations:
                br2 = self.bubble_r * self.bubble_r
                for civ in self.civilizations:
                    if civ["extinct"]:
                        continue
                    dx_civ = civ["x"] - x0
                    dy_civ = civ["y"] - y0
                    dz_civ = civ["z"] - z0
                    if dx_civ * dx_civ + dy_civ * dy_civ + dz_civ * dz_civ <= br2:
                        civ["extinct"] = True
                        civ["extinction_interval"] = self.current_interval

        # New civilizations.
        if self.simulate_civilizations:
            num_new_civs = np.random.poisson(self.civ_per_interval)
            for _ in range(num_new_civs):
                civ_id, civ_x, civ_y, civ_z = generate_civilization(self.next_civ_id, self.R, self.h)
                self.civilizations.append({
                    "id": civ_id,
                    "x": civ_x,
                    "y": civ_y,
                    "z": civ_z,
                    "birth_interval": self.current_interval,
                    "extinct": False,
                    "extinction_interval": None,
                })
                self.next_civ_id += 1
            living_count = sum(1 for civ in self.civilizations if not civ["extinct"])
            self.civ_history.append(living_count)

        # Coverage.
        coverage = {}
        for threshold in range(1, self.max_threshold + 1):
            covered = int(np.count_nonzero(self.hit_count >= threshold))
            frac = covered / self.total_domain_cells if self.total_domain_cells else 0.0
            self.coverage_history[threshold].append(frac)
            coverage[threshold] = frac

        self.current_interval += 1
        self.intervals.append(self.current_interval)

        return {
            "interval": self.current_interval,
            "coverage": coverage,
            "civ_count": self.civ_history[-1] if self.simulate_civilizations and self.civ_history else 0,
            "supernovae": self.supernovae,
        }
