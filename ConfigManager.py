from PyQt5.QtWidgets import QDialog, QVBoxLayout


class ConfigManager(QDialog):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Configure anki-forvo-dl")
        self.setFixedWidth(400)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        description = "<h2>General Settings</h1>"

        self.layout



