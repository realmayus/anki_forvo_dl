from aqt.qt import Qt, QLabel, QVBoxLayout, QDialog, QRadioButton, QPushButton, QButtonGroup
from aqt import AnkiQt

from .Config import Config


class FieldSelector(QDialog):
    def __init__(self, parent, mw: AnkiQt, note_type: int, field_type: str, config: Config):
        super().__init__(parent)
        self.config = config
        self.mw = mw
        self.page = 0
        self.setWindowTitle("Select Fields")
        self.setFixedWidth(400)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        description_header = "<h1>Select Fields</h1>"
        description_label = QLabel(description_header)
        description_label.setMinimumSize(self.sizeHint())
        description_label.setWordWrap(True)
        description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout.addWidget(description_label)

        note_type_fetched = mw.col.models.get(note_type)

        description_label.setText(description_header + config.get_template(field_type, "noteTypeSpecific")["description"].replace("{{noteType}}", note_type_fetched["name"]))

        fields: list = note_type_fetched["flds"]

        self.next_btn = QPushButton("Continue")
        self.next_btn.setEnabled(False)
        self.next_btn.clicked.connect(lambda: self.close())
        self.buttongroup = QButtonGroup()
        radios = []
        for field in fields:
            radio = QRadioButton(field["name"])
            radio.field = field["name"]
            radios.append(radio)

        [self.buttongroup.addButton(x) for x in radios]
        [self.layout.addWidget(x) for x in radios]
        self.buttongroup.buttonClicked.connect(self.selection_changed)
        self.selected_field = None
        self.layout.addWidget(self.next_btn)



    def selection_changed(self):
        selected = self.buttongroup.checkedButton()
        if selected is not None:
            self.selected_field = selected.field
            self.next_btn.setEnabled(True)
        else:
            self.selected_field = None
            self.next_btn.setEnabled(False)
