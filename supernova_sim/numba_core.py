"""Numba-accelerated core functions for the supernova simulation."""
from __future__ import annotations
import math
import random
import numpy as np
from numba import njit

__all__ = [
    "update_hit_count",
    "run_supernova",
    "generate_civilization",
]

@njit
def update_hit_count(hit_count, domain_mask, R, h, x0, y0, z0,
                     i_center, j_center, k_center, rx, ry, rz, dx, dy, dz, bubble_r):
    new_hit = 0
    r2 = bubble_r * bubble_r
    ngrid_xy, _, ngrid_z = hit_count.shape
    for di in range(-rx, rx + 1):
        i = i_center + di
        if i < 0 or i >= ngrid_xy:
            continue
        x_cell = -R + i * dx
        for dj in range(-ry, ry + 1):
            j = j_center + dj
            if j < 0 or j >= ngrid_xy:
                continue
            y_cell = -R + j * dy
            if x_cell * x_cell + y_cell * y_cell > R * R:
                continue
            for dk in range(-rz, rz + 1):
                k = k_center + dk
                if k < 0 or k >= ngrid_z:
                    continue
                z_cell = -h / 2 + k * dz
                dx_val = x_cell - x0
                dy_val = y_cell - y0
                dz_val = z_cell - z0
                if dx_val * dx_val + dy_val * dy_val + dz_val * dz_val <= r2:
                    if hit_count[i, j, k] == 0:
                        new_hit += 1
                    hit_count[i, j, k] += 1
    return new_hit

@njit
def run_supernova(hit_count, domain_mask, R, h, supernovae, dx, dy, dz, rx, ry, rz, bubble_r):
    theta = random.uniform(0, 2 * math.pi)
    u = random.uniform(0, 1)
    r_event = math.sqrt(u) * R
    x0 = np.float32(r_event * math.cos(theta))
    y0 = np.float32(r_event * math.sin(theta))
    z0 = np.float32(random.uniform(-h / 2, h / 2))
    i_center = int(round((x0 + R) / dx))
    j_center = int(round((y0 + R) / dy))
    k_center = int(round((z0 + h / 2) / dz))
    new_hits = update_hit_count(hit_count, domain_mask, R, h, x0, y0, z0,
                                i_center, j_center, k_center,
                                rx, ry, rz, dx, dy, dz, bubble_r)
    supernovae += 1
    return x0, y0, z0, new_hits

@njit
def generate_civilization(next_civ_id, R, h):
    theta = random.uniform(0, 2 * math.pi)
    u = random.uniform(0, 1)
    r_civ = math.sqrt(u) * R
    civ_x = np.float32(r_civ * math.cos(theta))
    civ_y = np.float32(r_civ * math.sin(theta))
    civ_z = np.float32(random.uniform(-h / 2, h / 2))
    civ_id = next_civ_id
    return civ_id, civ_x, civ_y, civ_z
