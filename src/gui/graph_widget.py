from PySide6.QtWidgets import QWidget, QVBoxLayout
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class HashrateGraph(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.figure = Figure(figsize=(5, 3), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title("Hashrate (H/s)")
        self.ax.set_xlabel("Temps (s)")
        self.ax.set_ylabel("H/s")
        self.ax.grid(True, linestyle='--', alpha=0.7)

        self.times = []
        self.hashrates = []
        self.max_points = 60  # 60 segons

    def add_hashrate(self, hashrate):
        if hashrate == 0:
            return
        if len(self.times) == 0:
            t = 0
        else:
            t = self.times[-1] + 1
        self.times.append(t)
        self.hashrates.append(hashrate)
        if len(self.times) > self.max_points:
            self.times.pop(0)
            self.hashrates.pop(0)

        self.ax.clear()
        self.ax.set_title("Hashrate (H/s)")
        self.ax.set_xlabel("Temps (s)")
        self.ax.set_ylabel("H/s")
        self.ax.grid(True, linestyle='--', alpha=0.7)
        self.ax.plot(self.times, self.hashrates, 'b-', linewidth=2)
        self.canvas.draw()