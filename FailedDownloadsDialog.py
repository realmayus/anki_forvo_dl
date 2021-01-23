import os
from typing import List

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontDatabase
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QTableView, QListWidget, QListWidgetItem, QHBoxLayout, \
    QPushButton, QAbstractScrollArea
from anki.cards import Card
from aqt.utils import showInfo

from anki_forvo_dl import Exceptions
from anki_forvo_dl.Util import FailedDownload


# class FailedListWidgetItemWidget(QWidget):
#     def __init__(self, label: str, card: Card):
#         from anki_forvo_dl import asset_dir
#
#
#         hbox = QHBoxLayout()
#         hbox.addWidget(QLabel(label))
#         hbox.addStretch()
#         hbox.addWidget(QPushButton("Card...").clicked.connect(lambda: ))
#
#
#         self.setLayout(vbox)


class FailedDownloadsDialog(QDialog):

    def __init__(self, parent, failed):
        super().__init__(parent)
        from anki_forvo_dl import asset_dir

        self.failed: List[FailedDownload] = failed

        font_db = QFontDatabase()
        font_db.addApplicationFont(os.path.join(asset_dir, "IBMPlexSans-Bold.ttf"))
        font_db.addApplicationFont(os.path.join(asset_dir, "IBMPlexSans-Italic.ttf"))
        font_db.addApplicationFont(os.path.join(asset_dir, "IBMPlexSans-Regular.ttf"))
        self.setFixedWidth(400)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.description = "<h2>%s Download%s Failed</h2>" % (str(len(self.failed)), "s" if len(self.failed) != 1 else "")
        self.description_label = QLabel(text=self.description)
        self.description_label.setMinimumSize(self.sizeHint())
        self.description_label.setWordWrap(True)
        self.description_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.description_label)
        self.show_reasons()

    def get_reasons(self):
        reasons = {}
        for fail in self.failed:
            error_instance = next((e for e in Exceptions.all_errors if isinstance(fail.reason, e)), None)

            if error_instance is not None:
                if error_instance in reasons.keys():
                    reasons[error_instance].append(fail)
                else:
                    reasons[error_instance] = [fail]
            else:
                if type(fail.reason).__name__ in reasons.keys():
                    reasons[type(fail.reason).__name__].append(fail)
                else:
                    reasons[type(fail.reason).__name__] = [fail]

        return reasons

    def show_reasons(self):
        from anki_forvo_dl.BulkAdd import query_field

        reasons = self.get_reasons()
        for reason, fails in reasons.items():
            if hasattr(reason, "friendly"):
                self.layout.addWidget(QLabel("<b>%s</b>" % reason.friendly))
            else:
                self.layout.addWidget(QLabel("<b>%s</b>" % str(reason)))

            if hasattr(reason, "info"):
                self.layout.addWidget(QLabel("<em>%s</em>" % reason.info))

            table = QListWidget()
            for fail in fails:
                item = QListWidgetItem(fail.card.note()[query_field])  #TODO
                table.addItem(item)
            table.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
            table.adjustSize()
            self.layout.addWidget(table)
        self.adjustSize()



