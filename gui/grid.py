from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import Qt, QThread, pyqtSlot, pyqtSignal

import cv2
from numpy import ndarray

class Grid(QWidget):
    def __init__(self, cam_width):
        super().__init__()

        self.cam_width = cam_width

        self.cam_1 = Camera(self, 0)
        self.cam_2 = Camera(self, 0)

        self.layout = QHBoxLayout()

        self.layout.addWidget(self.cam_1)
        self.layout.addWidget(self.cam_2)

        self.setLayout(self.layout)

class Camera(QLabel):
    def __init__(self, parent, port):
        super().__init__("Connecting...")

        self.parent = parent

        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.thread = VideoThread(port)
        self.thread.change_pixmap_signal.connect(self.update_image)
        self.thread.start()

    def close_event(self, event):
        self.thread.stop()
        event.accept()

    @pyqtSlot(ndarray)
    def update_image(self, cv_img):
        qt_img = self.convert_cv_qt(cv_img)
        self.setPixmap(qt_img)

    def convert_cv_qt(self, cv_img):
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        p = convert_to_Qt_format.scaledToWidth(self.parent.cam_width)#, Qt.AspectRatioMode.KeepAspectRatio)# (self.parent.cam_width, self.parent.cam_height, Qt.AspectRatioMode.KeepAspectRatio)
        return QPixmap.fromImage(p)

class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(ndarray)

    def __init__(self, port):
        super().__init__()

        self.running = True
        self.port = port

        self.recording = False

    def run(self):
        cap = cv2.VideoCapture(self.port)
        print(f"Camera started on port: {self.port}")

        while self.running:
            ret, image = cap.read()
            if ret:
                self.change_pixmap_signal.emit(image)
                
        cap.release()
        
    def stop(self):
        self.running = False
        self.wait()