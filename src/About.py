from PyQt6.QtWidgets import QDialog, QLabel, QVBoxLayout


class About(QDialog):

    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("About anki-forvo-dl")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.description = "<h1>About anki-forvo-dl</h1>"
        self.description_l = QLabel(self.description)
        self.layout.addWidget(self.description_l)
