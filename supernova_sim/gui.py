"""PyQtGraph GUI for live visualization of the supernova simulation."""
from __future__ import annotations
import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, simulation, update_ms: int = 10):
        super().__init__()
        self.simulation = simulation
        self.setWindowTitle("Supernova Simulation – Live Update")

        # Central widget + layout
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        vbox = QtWidgets.QVBoxLayout(central)

        self.graphics_layout = pg.GraphicsLayoutWidget()
        vbox.addWidget(self.graphics_layout)

        # 1. Coverage plot
        self.coverage_plot = self.graphics_layout.addPlot(title="Disk Coverage Evolution")
        self.coverage_plot.setLabel('left', 'Coverage (%)')
        self.coverage_plot.setLabel('bottom', 'Interval')
        self.coverage_curves = {}
        color_list = ['r', 'g', 'b', 'c', 'm', 'y', 'w']
        for i, threshold in enumerate(range(1, simulation.max_threshold + 1)):
            pen = pg.mkPen(color=color_list[i % len(color_list)], width=2)
            self.coverage_curves[threshold] = self.coverage_plot.plot([], [], pen=pen)

        self.graphics_layout.nextRow()

        # 2. Civilization count plot
        self.civ_plot = self.graphics_layout.addPlot(title="Civilisation Count Evolution")
        self.civ_plot.setLabel('left', 'Living Civilisations')
        self.civ_plot.setLabel('bottom', 'Interval')
        self.civ_curve = self.civ_plot.plot([], [], pen=pg.mkPen('m', width=2))

        self.graphics_layout.nextRow()

        # 3. Histogram plot
        self.hist_plot = self.graphics_layout.addPlot(title="Hit Count Histogram")
        self.hist_plot.setLabel('left', 'Frequency')
        self.hist_plot.setLabel('bottom', 'Number of Hits')
        self.hist_bar_item = None

        # 4. Disk heatmap (right side)
        self.disk_plot = self.graphics_layout.addPlot(row=0, col=1, rowspan=3, title="Disk Hit Map (z≈0)")
        self.disk_plot.setAspectLocked(True)
        self.disk_img = pg.ImageItem(border='w')
        self.disk_plot.addItem(self.disk_img)

        self.cbar = pg.ColorBarItem(values=(0, 1), orientation='vertical')  # updated each step
        self.graphics_layout.addItem(self.cbar, row=0, col=2, rowspan=3)
        self.cbar.setImageItem(self.disk_img)

        # Data storage
        self.intervals = []
        self.coverage_data = {th: [] for th in range(1, simulation.max_threshold + 1)}
        self.civ_data = []

        # Timer
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_simulation)
        self.timer.start(update_ms)

    def update_simulation(self):
        result = self.simulation.step()
        if not result:
            self.timer.stop()
            return

        interval = result['interval']
        self.intervals.append(interval)

        # Coverage
        for th in range(1, self.simulation.max_threshold + 1):
            pct = result['coverage'][th] * 100.0
            self.coverage_data[th].append(pct)
            self.coverage_curves[th].setData(self.intervals, self.coverage_data[th])

        # Civ count
        if self.simulation.simulate_civilizations:
            self.civ_data.append(result['civ_count'])
            self.civ_curve.setData(self.intervals, self.civ_data)

        # Histogram
        hit_counts = self.simulation.hit_count[self.simulation.hit_count > 0]
        if hit_counts.size:
            bins = np.arange(1, hit_counts.max() + 2)
            hist, edges = np.histogram(hit_counts, bins=bins)
            x = edges[:-1]
            if self.hist_bar_item is not None:
                self.hist_plot.removeItem(self.hist_bar_item)
            self.hist_bar_item = pg.BarGraphItem(x=x, height=hist, width=0.6, brush='b')
            self.hist_plot.addItem(self.hist_bar_item)

        # Disk slice (mid-plane)
        mid_k = self.simulation.ngrid_z // 2
        slice2d = self.simulation.hit_count[:, :, mid_k]
        mask2d = self.simulation.domain_mask[:, :, mid_k]
        slice2d = np.where(mask2d, slice2d, 0)
        self.disk_img.setImage(slice2d.T, autoLevels=True)
        self.cbar.setLevels((0, max(1, slice2d.max())))
