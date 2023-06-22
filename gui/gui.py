from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt

from .grid import Grid

class MainWindow(QMainWindow):
    def __init__(self, gui_settings):
        super().__init__()

        self.grid = Grid(gui_settings["cam-width"])

        self.frame = QWidget()
        self.frame.layout = QVBoxLayout()

        self.frame.layout.addWidget(self.grid)

        self.frame.setLayout(self.frame.layout)

        self.setCentralWidget(self.frame)

    def keyPressEvent(self, e):
        if e.isAutoRepeat():
            return
        
        if e.key() == Qt.Key.Key_W:
            self.grid.camera_size()
            print("w pressed")

    def keyReleaseEvent(self, e):
        if e.isAutoRepeat():
            return
        
        if e.key() == Qt.Key.Key_W:
            print("w released")