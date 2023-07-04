from PyQt6.QtWidgets import QApplication

import yaml

from gui.gui import MainWindow
from comms.comms import Comms

if __name__ == "__main__":
    with open("settings.yaml") as f:
        settings = yaml.safe_load(f)
    print(yaml.safe_dump(settings))
    print("Modify settings in 'settings.yaml'")

    app = QApplication([])
    
    window = MainWindow(settings["gui"], Comms() if not settings["debug"] else None)
    window.show()

    print("GUI successfully initialized")

    app.exec()