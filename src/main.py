# src/main.py
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Chrono Filer - v0.0.1")
        self.setGeometry(100, 100, 400, 200) # x, y, width, height

        label = QLabel("Welcome to Chrono Filer!", self)
        label.setGeometry(10, 10, 380, 30) # A bit of simple positioning for now

        # In a real app, you'd use layouts, but for "hello world" this is fine.

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
