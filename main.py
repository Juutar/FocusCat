from PySide6.QtWidgets import QApplication
import sys
from logic import FocusCat

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = FocusCat()
    w.show()
    sys.exit(app.exec())