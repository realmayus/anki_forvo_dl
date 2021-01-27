import os
import threading
from dataclasses import dataclass
from typing import List

from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QWaitCondition, QMutex, pyqtSlot
from PyQt5.QtGui import QFontDatabase
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton, QProgressBar, \
    QCheckBox
from anki.cards import Card
from aqt import AnkiQt
from aqt.utils import showInfo

from anki_forvo_dl.LanguageSelector import LanguageSelector
from anki_forvo_dl.Config import Config, ConfigObject
from anki_forvo_dl.Exceptions import FieldNotFoundException
from anki_forvo_dl.FailedDownloadsDialog import FailedDownloadsDialog
from anki_forvo_dl.Util import get_field_id, FailedDownload
from anki_forvo_dl.Forvo import Pronunciation, Forvo

query_field = "Word"
audio_field = "Audio"


class BulkAdd(QDialog):
    def __init__(self, parent, cards: List[Card], mw, config: Config):
        super().__init__(parent)
        self.config: Config = config
        self.setFixedWidth(400)
        self.selected_pronunciation: Pronunciation = None
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.description = "<h1>anki_forvo_dl</h1><p>anki-forvo-dl will download audio files for the selected cards based on the field <b>" + query_field + "</b> and put the audio in the field <b>" + audio_field + "</b>.</p>"
        self.description_label = QLabel(text=self.description)
        self.description_label.setMinimumSize(self.sizeHint())
        self.description_label.setWordWrap(True)
        self.description_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.description_label)

        self.skipCheckbox = QCheckBox("Skip download for cards that already have\n content in the field '" + query_field + "'")
        self.skipCheckbox.setChecked(True)  #TODO read from Config
        self.layout.addWidget(self.skipCheckbox)

        self.btn = QPushButton("Start Downloads")
        self.btn.clicked.connect(self.start_downloads_wrapper)
        self.layout.addWidget(self.btn)

        self.th = Thread(cards, mw)

        self.pb = QPushButton("Pause")
        self.pb.setVisible(False)
        self.pb.clicked.connect(self.slot_clicked_button)
        self.layout.addWidget(self.pb)
        self.progress = QProgressBar()
        self.progress.setMaximum(len(cards))
        self.progress.setMinimum(0)
        self.progress.setVisible(False)
        self.layout.addWidget(self.progress)

        self.th.change_value.connect(self.progress.setValue)
        self.th.finished.connect(self.review_downloads)

        self.setMaximumHeight(1000)
        self.cards = cards
        self.parent = parent
        self.mw: AnkiQt = mw

    def review_downloads(self):
        dialog = FailedDownloadsDialog(self.parent, self.th.failed, self.mw)
        dialog.finished.connect(lambda: self.close())
        dialog.show()

    @pyqtSlot()
    def slot_clicked_button(self):
        self.th.toggle_status()
        self.pb.setText({True: "Pause", False: "Resume"}[self.th.status])

    def select_lang(self, missing):
        deck_id = missing[0]
        d = LanguageSelector(self.parent)

        def handle_lang_select():
            if d.selected_lang is not None:
                self.config.set_deck_specific_config_object(
                    ConfigObject(name="language", value=d.selected_lang, deck=deck_id))
                if len(missing) > 1:
                    missing.pop()
                    self.select_lang(missing)
                else:
                    self.start_downloads()
            else:
                showInfo("Cancelled download because no language was selected.")
                return

        d.finished.connect(handle_lang_select)
        d.show()


    def ensure_languages(self):
        """Ensures that the language is set for all selected decks; otherwise show dialog"""
        missing = list(set([card.did for card in self.cards if self.config.get_deck_specific_config_object("language", card.did) is None]))
        if len(missing) > 0:
            self.select_lang(missing)
        else:
            self.start_downloads()


    def start_downloads_wrapper(self):
        self.ensure_fields()
        self.ensure_languages()

    def select_field(self, missing, fieldType: str, friendlyType: str): #TODO
        deck_id = missing[0]
        d = LanguageSelector(self.parent)

        def handle_lang_select():
            if d.selected_lang is not None:
                self.config.set_deck_specific_config_object(
                    ConfigObject(name="language", value=d.selected_lang, deck=deck_id))
                if len(missing) > 1:
                    missing.pop()
                    self.select_lang(missing)
                else:
                    self.start_downloads()
            else:
                showInfo("Cancelled download because field wasn't selected.")
                return

        d.finished.connect(handle_lang_select)
        d.show()

    def ensure_fields(self):
        showInfo(str(self.cards[0].note_type()))
        missing = list(set([card.note_type() for card in self.cards if self.config.get_note_type_specific_config_object("searchField", card.did) is None]))
        if len(missing) > 0:
            self.select_field(missing, "searchField", "Search Field")
        else:
            self.start_downloads()


    def start_downloads(self):
        self.btn.setVisible(False)
        self.skipCheckbox.setEnabled(False)
        self.pb.setVisible(True)
        self.progress.setVisible(True)
        self.adjustSize()
        self.th.start()


    def update_progress_bar(self):
        self.progress.setValue(self.progress.value() + 1)

    def select_pronunciation(self, pronunciation: Pronunciation):
        self.selected_pronunciation = pronunciation
        self.close()




class Thread(QThread):
    change_value = pyqtSignal(int)
    done = pyqtSignal(int)

    def __init__(self, cards, mw):
        QThread.__init__(self)
        self.cond = QWaitCondition()
        self.mutex = QMutex()
        self.cnt = 0
        self._status = True
        self.cards = cards
        self.mw = mw
        self.failed: List[FailedDownload] = []
        self.exceptions: List[str] = []

    def __del__(self):
        self.wait()

    def run(self):
        for card in self.cards:
            self.mutex.lock()
            if not self._status:
                self.cond.wait(self.mutex)
            try:
                if query_field not in card.note():
                    raise FieldNotFoundException(query_field)
                query = card.note()[query_field]
                results = Forvo(query, "ja", self.mw) \
                    .load_search_query() \
                    .get_pronunciations().pronunciations
                results.sort(key=lambda result: result.votes)
                top: Pronunciation = results[0]
                top.download_pronunciation()
                card.note().fields[get_field_id(audio_field, card.note())] = "[sound:%s]" % top.audio
                card.note().flush()
            except Exception as e:
                self.exceptions.append(str(e))
                self.failed.append(FailedDownload(reason=e, card=card))
            self.cnt += 1
            self.change_value.emit(self.cnt)
            self.msleep(100)

            self.mutex.unlock()

        Forvo.cleanup(None)

    def toggle_status(self):
        with open(".", "a") as f:
            f.write("")
        self._status = not self._status
        if self._status:
            self.cond.wakeAll()

    @property
    def status(self):
        return self._status
