import json
import os

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton
from aqt.utils import showInfo


class LanguageSelector(QDialog):

    def __init__(self, parent):
        from anki_forvo_dl import asset_dir
        super().__init__(parent)
        self.setWindowTitle("Select Language")
        self.setFixedWidth(400)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        description = "<h1>Language select</h1>"
        description += "<p>Please select the language for this deck so that anki-forvo-dl can find the right words on Forvo.</p><p>You can change this later in the settings dialog at Tools > anki-forvo-dl > Settings</p>"
        description_label = QLabel(description)
        description_label.setMinimumSize(self.sizeHint())
        description_label.setWordWrap(True)
        description_label.setAlignment(Qt.AlignCenter)

        self.layout.addWidget(description_label)

        self.next_btn = QPushButton("Continue")
        self.next_btn.setEnabled(False)
        self.next_btn.setVisible(False)
        self.next_btn.clicked.connect(lambda: self.close())

        self.language_select = QComboBox()
        with open(os.path.join(asset_dir, "languages.json"), encoding="utf8") as f:
            self.language_list = json.loads(f.read())

        [self.language_select.addItem(lang["English name"], lang["Code"]) for lang in self.language_list]
        self.language_select.setEditable(True)
        self.language_select.currentIndexChanged.connect(self.on_index_change)
        self.language_select.currentTextChanged.connect(self.on_text_change)
        self.language_select.setCurrentText("")

        self.layout.addWidget(self.language_select)
        self.layout.addWidget(self.next_btn)

        self.selected_lang = None


    def on_index_change(self, index: int):
        if index != -1:
            self.next_btn.setEnabled(True)
            self.next_btn.setVisible(True)
            self.selected_lang = self.language_select.itemData(index)

    def on_text_change(self, new_text: str):
        res = next((item for item in self.language_list if item["English name"] == new_text), None)

        if res is not None:
            self.next_btn.setEnabled(True)
            self.next_btn.setVisible(True)
            self.selected_lang = res["Code"]
        else:
            self.next_btn.setEnabled(False)
            self.next_btn.setVisible(False)
