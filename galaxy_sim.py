import sys
import math
import random
import numpy as np
from numba import njit
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets

# === Numba-accelerated simulation functions ===

@njit
def update_hit_count(hit_count, domain_mask, R, h, x0, y0, z0, 
                     i_center, j_center, k_center, rx, ry, rz, dx, dy, dz, bubble_r):
    """
    For a given event centered at (x0, y0, z0), update hit_count for cells inside the bubble.
    Returns the number of cells that were hit for the first time.
    """
    new_hit = 0
    r2 = bubble_r * bubble_r
    ngrid_xy, _, ngrid_z = hit_count.shape

    for di in range(-rx, rx + 1):
        i = i_center + di
        if i < 0 or i >= ngrid_xy:
            continue
        x_cell = -R + i * dx  # since x goes from -R to R
        for dj in range(-ry, ry + 1):
            j = j_center + dj
            if j < 0 or j >= ngrid_xy:
                continue
            y_cell = -R + j * dy  # since y goes from -R to R

            # Skip cells that are outside the Milky Way disk in the (x,y) plane.
            if x_cell * x_cell + y_cell * y_cell > R * R:
                continue

            for dk in range(-rz, rz + 1):
                k = k_center + dk
                if k < 0 or k >= ngrid_z:
                    continue
                z_cell = -h / 2 + k * dz  # since z goes from -h/2 to h/2

                # Compute squared distance from the event center.
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
    # Sample a random event location uniformly within the Milky Way disk.
    theta = random.uniform(0, 2 * math.pi)
    u = random.uniform(0, 1)
    r_event = math.sqrt(u) * R
    x0 = np.float32(r_event * math.cos(theta))
    y0 = np.float32(r_event * math.sin(theta))
    z0 = np.float32(random.uniform(-h / 2, h / 2))
    
    # Find the nearest grid cell indices.
    i_center = int(round((x0 + R) / dx))
    j_center = int(round((y0 + R) / dy))
    k_center = int(round((z0 + h / 2) / dz))
    
    new_hits = update_hit_count(hit_count, domain_mask, R, h, x0, y0, z0,
                                i_center, j_center, k_center,
                                rx, ry, rz, dx, dy, dz, bubble_r)
    supernovae += 1  # (this local addition does not affect the caller)
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

# === Simulation class (one simulation step = one interval) ===

class SupernovaSimulation:
    def __init__(self,
                 num_intervals=500,        # total intervals to run
                 interval_years=1e6,       # years per interval
                 rate_per_year=0.02,       # supernova rate per year
                 R=50000, h=1000,          # Milky Way disk parameters (ly)
                 bubble_r=50,              # lethal bubble radius
                 ngrid_xy=200,             # grid resolution (smaller than the original for speed)
                 ngrid_z=50,
                 max_threshold=5,          # track cells hit at least this many times
                 simulate_civilizations=True,
                 civ_emergence_rate=0.1,   # new civs per interval (tweak as desired)
                 seed=42):
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

        # Create grid coordinate arrays.
        self.x = np.linspace(-R, R, ngrid_xy, dtype=np.float32)
        self.y = np.linspace(-R, R, ngrid_xy, dtype=np.float32)
        self.z = np.linspace(-h / 2, h / 2, ngrid_z, dtype=np.float32)
        self.dx = self.x[1] - self.x[0]
        self.dy = self.y[1] - self.y[0]
        self.dz = self.z[1] - self.z[0]
        
        # Domain mask (cells in (x,y) with x^2+y^2 <= R^2).
        X2, Y2 = np.meshgrid(self.x, self.y, indexing='ij')
        domain2d = (X2**2 + Y2**2 <= R**2)
        self.domain_mask = np.repeat(domain2d[:, :, np.newaxis], ngrid_z, axis=2)
        self.total_domain_cells = np.count_nonzero(self.domain_mask)
        
        # Initialize the hit count grid.
        self.hit_count = np.zeros((ngrid_xy, ngrid_xy, ngrid_z), dtype=np.int32)
        self.supernovae = 0
        self.coverage_history = {th: [] for th in range(1, max_threshold + 1)}
        
        # Civilization simulation data.
        self.civilizations = []  # list of civ dicts
        self.next_civ_id = 0
        self.civ_history = []  # living civ count history
        
        # Precompute grid steps needed to cover the bubble.
        self.rx = int(math.ceil(bubble_r / self.dx))
        self.ry = int(math.ceil(bubble_r / self.dy))
        self.rz = int(math.ceil(bubble_r / self.dz))
        
        # Expected number of supernova events per interval.
        self.mean_events = self.rate_per_year * self.interval_years
        
        # To record intervals (for plotting)
        self.intervals = []
    
    def step(self):
        """
        Process one interval of the simulation and return a dictionary with summary data.
        Returns False if the simulation is complete.
        """
        if self.current_interval >= self.num_intervals:
            return False
        
        # Process supernova events.
        num_events = np.random.poisson(self.mean_events)
        for _ in range(num_events):
            x0, y0, z0, new_hits = run_supernova(self.hit_count, self.domain_mask, self.R, self.h,
                                                  self.supernovae, self.dx, self.dy, self.dz,
                                                  self.rx, self.ry, self.rz, self.bubble_r)
            self.supernovae += 1
            
            # Check if this event “hits” any living civilisation.
            if self.simulate_civilizations:
                for civ in self.civilizations:
                    if not civ["extinct"]:
                        dx_civ = civ["x"] - x0
                        dy_civ = civ["y"] - y0
                        dz_civ = civ["z"] - z0
                        if dx_civ * dx_civ + dy_civ * dy_civ + dz_civ * dz_civ <= self.bubble_r * self.bubble_r:
                            civ["extinct"] = True
                            civ["extinction_interval"] = self.current_interval
        
        # Possibly add new civilisations.
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
                    "extinction_interval": None
                })
                self.next_civ_id += 1
            living_count = sum(1 for civ in self.civilizations if not civ["extinct"])
            self.civ_history.append(living_count)
        
        # Compute current grid coverage for each hit threshold.
        coverage = {}
        for threshold in range(1, self.max_threshold + 1):
            covered = np.count_nonzero(self.hit_count >= threshold)
            frac = covered / self.total_domain_cells
            self.coverage_history[threshold].append(frac)
            coverage[threshold] = frac
        
        self.current_interval += 1
        self.intervals.append(self.current_interval)
        
        return {
            "interval": self.current_interval,
            "coverage": coverage,
            "civ_count": self.civ_history[-1] if self.simulate_civilizations else None,
            "supernovae": self.supernovae
        }

# === PyQt GUI with live-updating plots ===

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, simulation):
        super().__init__()
        self.simulation = simulation
        self.setWindowTitle("Supernova Simulation – Live Update")
        
        # Central widget and layout.
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QtWidgets.QVBoxLayout(self.central_widget)
        
        # Use a GraphicsLayoutWidget to arrange plots.
        self.graphics_layout = pg.GraphicsLayoutWidget()
        self.layout.addWidget(self.graphics_layout)
        
        # -------------------------------
        # 1. Disk Coverage Evolution Plot
        # -------------------------------
        self.coverage_plot = self.graphics_layout.addPlot(title="Disk Coverage Evolution")
        self.coverage_plot.setLabel('left', 'Coverage (%)')
        self.coverage_plot.setLabel('bottom', 'Interval')
        # Create a curve for each hit threshold.
        self.coverage_curves = {}
        color_list = ['r', 'g', 'b', 'c', 'm', 'y', 'w']
        for i, threshold in enumerate(range(1, simulation.max_threshold + 1)):
            pen = pg.mkPen(color=color_list[i % len(color_list)], width=2)
            curve = self.coverage_plot.plot([], [], pen=pen, name=f"Cells hit ≥ {threshold}")
            self.coverage_curves[threshold] = curve
        
        self.graphics_layout.nextRow()
        
        # -------------------------------
        # 2. Civilisation Count Evolution Plot
        # -------------------------------
        self.civ_plot = self.graphics_layout.addPlot(title="Civilisation Count Evolution")
        self.civ_plot.setLabel('left', 'Living Civilisations')
        self.civ_plot.setLabel('bottom', 'Interval')
        self.civ_curve = self.civ_plot.plot([], [], pen=pg.mkPen('m', width=2))
        
        self.graphics_layout.nextRow()
        
        # -------------------------------
        # 3. Hit Count Histogram Plot
        # -------------------------------
        self.hist_plot = self.graphics_layout.addPlot(title="Hit Count Histogram")
        self.hist_plot.setLabel('left', 'Frequency')
        self.hist_plot.setLabel('bottom', 'Number of Hits')
        self.hist_bar_item = None  # Will hold the BarGraphItem
        
        # Data storage for live plots.
        self.intervals = []
        self.coverage_data = {th: [] for th in range(1, simulation.max_threshold + 1)}
        self.civ_data = []
        
        # Timer to run simulation steps and update plots.
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_simulation)
        self.timer.start(100)  # update every 100 ms (adjust as needed)
    
    def update_simulation(self):
        """Run one simulation step and update all plots."""
        result = self.simulation.step()
        if not result:
            self.timer.stop()
            return
        
        interval = result["interval"]
        self.intervals.append(interval)
        
        # Update coverage curves.
        for th in range(1, self.simulation.max_threshold + 1):
            cov = result["coverage"][th] * 100  # convert to percentage
            self.coverage_data[th].append(cov)
            self.coverage_curves[th].setData(self.intervals, self.coverage_data[th])
        
        # Update civilisation count curve.
        if self.simulation.simulate_civilizations:
            civ_count = result["civ_count"]
            self.civ_data.append(civ_count)
            self.civ_curve.setData(self.intervals, self.civ_data)
        
        # Update histogram plot.
        hit_counts = self.simulation.hit_count[self.simulation.hit_count > 0]
        if hit_counts.size > 0:
            bins = np.arange(1, hit_counts.max() + 2)  # bin edges for hit counts
            hist, bin_edges = np.histogram(hit_counts, bins=bins)
            x = bin_edges[:-1]  # positions for bars
            # Remove the previous histogram (if any)
            if self.hist_bar_item is not None:
                self.hist_plot.removeItem(self.hist_bar_item)
            self.hist_bar_item = pg.BarGraphItem(x=x, height=hist, width=0.6, brush='b')
            self.hist_plot.addItem(self.hist_bar_item)

# === Main Application ===

def main():
    # Create the simulation object.
    # (For live GUI demos it can help to use a smaller grid and fewer intervals.)
    sim = SupernovaSimulation(
        num_intervals=10000,
        interval_years=1e6,
        rate_per_year=0.02,
        R=50000,
        h=1000,
        bubble_r=50,
        ngrid_xy=200,    # smaller than 2000 for speed in the demo
        ngrid_z=50,
        max_threshold=5,
        simulate_civilizations=True,
        civ_emergence_rate=1/1e6,  # new civs per year
        seed=42
    )
    
    # Start the Qt application.
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow(sim)
    win.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()