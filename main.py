import sys
from PyQt5.QtWidgets import QApplication
from gui1 import BoutiqueApp

def start_gui():
    app = QApplication(sys.argv)
    window = BoutiqueApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    start_gui()
