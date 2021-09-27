from typing import List
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QAbstractScrollArea, \
    QPushButton, QHBoxLayout, QWidget, QAbstractItemView
from anki.cards import Card
from aqt.browser import Browser

from .Config import Config
from .Exceptions import all_errors
from .Util import FailedDownload, open_file


class FailedListWidgetItemWidget(QWidget):
    def __init__(self, label: str, card: Card, mw, browser: Browser, specific_info: str = None):
        super().__init__()
        self.mw = mw
        self.card = card
        hbox = QHBoxLayout()
        hbox.addWidget(QLabel(label))
        hbox.addStretch()
        more_info = QLabel(specific_info)
        hbox.addWidget(more_info)
        card_btn = QPushButton("Card")

        def show_card():
            browser.form.searchEdit.lineEdit().setText("cid:" + str(card.id))
            browser.onSearchActivated()

        card_btn.clicked.connect(show_card)
        forvo_btn = QPushButton("Forvo")
        forvo_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://forvo.com/search/" + label)))
        hbox.addWidget(card_btn)
        hbox.addWidget(forvo_btn)
        hbox.setContentsMargins(10, 0, 0, 0)
        vbox = QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.setContentsMargins(0, 10, 10, 10)
        self.setLayout(vbox)
        self.setMinimumSize(vbox.sizeHint())
        self.adjustSize()


class FailedDownloadsDialog(QDialog):

    def __init__(self, parent, failed, mw, config: Config, skipped_cards: int):
        from .. import log_dir
        super().__init__(parent)

        self.parent = parent
        self.failed: List[FailedDownload] = failed
        self.setFixedWidth(400)
        self.mw = mw
        self.config = config
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.description = "<h2>%s Download%s Failed</h2>" % (str(len(self.failed)), "s" if len(self.failed) != 1 else "")
        if skipped_cards > 0:
            self.description += "%s cards that already had something in their audio fields were skipped." % str(skipped_cards)
        self.description_label = QLabel(text=self.description)
        self.description_label.setMinimumSize(self.sizeHint())
        self.description_label.setMinimumHeight(100)
        self.description_label.setWordWrap(True)
        self.description_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.description_label)
        self.show_reasons()

        logs_btn = QPushButton("Open Logs")
        logs_btn.clicked.connect(lambda: open_file(log_dir))
        self.layout.addWidget(logs_btn)

    def get_reasons(self):
        reasons = {}
        for fail in self.failed:
            # Show traceback for debugging:
            # showInfo(''.join(traceback.format_tb(fail.reason.__traceback__)))
            error_instance = next((e for e in all_errors if isinstance(fail.reason, e)), None)

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

    @staticmethod
    def get_specified_field_or_first_non_empty(card: Card, preference: str) -> str:
        if preference in card.note().keys():
            return card.note()[preference]
        for field, value in card.note().items():
            if value is not None and len(value) != 0:
                return value
        return "No fields"

    def show_reasons(self):

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
                item = QListWidgetItem("")
                table.addItem(item)

                item_widget = FailedListWidgetItemWidget(
                    self.get_specified_field_or_first_non_empty(fail.card, self.config.get_note_type_specific_config_object("searchField", fail.card.note_type()["id"]).value),
                    fail.card,
                    self.mw,
                    self.parent,
                    fail.reason.specific_info if hasattr(fail.reason, "specific_info") else None
                )

                item.setSizeHint(item_widget.minimumSizeHint())
                table.setItemWidget(item, item_widget)
            table.setSelectionMode(QAbstractItemView.NoSelection)
            table.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
            table.adjustSize()
            self.layout.addWidget(table)
        self.adjustSize()
