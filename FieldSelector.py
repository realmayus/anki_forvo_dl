from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QDialog
from anki.models import NoteType


class FieldSelector(QDialog):
    def __init__(self, parent, mw, note_type: NoteType):
        super().__init__(parent)
        self.mw = mw
        self.noteType = note_type
        self.page = 0
        self.setWindowTitle("Select Fields")
        self.setFixedWidth(400)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.description_header = "<h1>Select Fields</h1>"
        self.description_label = QLabel(self.description_header)
        self.description_label.setMinimumSize(self.sizeHint())
        self.description_label.setWordWrap(True)
        self.description_label.setAlignment(Qt.AlignCenter)

        self.layout.addWidget(self.description_label)
        self.showPage(0)

    def showPage(self, index):
        if index == 0:
            self.description_label.setText(self.description_header + "<p>Please select the field in the note type <em>" + self.note_type["name"] + "</em> that anki-forvo-dl should use to <b>search</b> for the word on Forvo</p>")
