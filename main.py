from PyQt6.QtWidgets import QApplication

import yaml
import pprint

from gui.gui import MainWindow

if __name__ == "__main__":
    with open("settings.json") as f:
        settings = yaml.safe_load(f)
    print(yaml.safe_dump(settings))
    print("Modify settings in 'settings.yaml'")

    app = QApplication([])
    
    window = MainWindow(settings["gui"])
    window.show()

    print("GUI successfully initialized")

    app.exec()