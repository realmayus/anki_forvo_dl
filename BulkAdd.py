from typing import List

from PyQt5.QtCore import Qt, QThread, pyqtSignal, QWaitCondition, QMutex, pyqtSlot
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QProgressBar
from anki.cards import Card
from aqt import AnkiQt
from aqt.utils import showInfo

from .Config import Config, ConfigObject
from .Exceptions import FieldNotFoundException
from .FailedDownloadsDialog import FailedDownloadsDialog
from .FieldSelector import FieldSelector
from .Forvo import Pronunciation, Forvo
from .LanguageSelector import LanguageSelector
from .Util import FailedDownload


class BulkAdd(QDialog):
    """Dialog that opens when clicking on 'Bulk Add Forvo Audio to X cards' in the context menu in the browser"""
    def __init__(self, parent, cards: List[Card], mw, config: Config):
        super().__init__(parent)
        self.config: Config = config
        self.setFixedWidth(400)
        self.selected_pronunciation: Pronunciation = None
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.description = "<h1>anki-forvo-dl</h1><p>anki-forvo-dl will download audio files for the selected cards based on the selected search field and put the audio in the selected audio field.</p><p>You can change these fields by going to the add-on's directory > user_files > config.json and changing the field names there.</p>"
        self.description_label = QLabel(text=self.description)
        self.description_label.setMinimumSize(self.sizeHint())
        self.description_label.setWordWrap(True)
        self.description_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.description_label)

        # self.skipCheckbox = QCheckBox("Skip download for cards that already have\n content in the audio field")
        # self.skipCheckbox.setChecked(True)  # TODO read from Config
        # self.layout.addWidget(self.skipCheckbox)

        self.btn = QPushButton("Start Downloads")
        self.btn.clicked.connect(self.start_downloads_wrapper)
        self.layout.addWidget(self.btn)

        self.th = Thread(cards, mw, config)  # Initialize Thread

        self.pb = QPushButton("Pause")
        self.pb.setVisible(False)
        self.pb.clicked.connect(self.slot_clicked_button)
        self.layout.addWidget(self.pb)

        self.progress = QProgressBar()
        self.progress.setMaximum(len(cards))
        self.progress.setMinimum(0)
        self.progress.setVisible(False)
        self.layout.addWidget(self.progress)

        # connect thread's signals to handler functions
        self.th.change_value.connect(self.progress.setValue)
        self.th.finished.connect(self.review_downloads)

        self.setMaximumHeight(1000)  # restrict maximum height to make use of the listview's scrollbar
        self.cards = cards
        self.parent = parent
        self.mw: AnkiQt = mw

    def review_downloads(self):
        """Opens the FailedDownloadsDialog after downloads are completed"""
        if len(self.th.failed) > 0:
            dialog = FailedDownloadsDialog(self.parent, self.th.failed, self.mw, self.config)
            dialog.finished.connect(lambda: self.close())  # close this window when the FailedDownloadsDialog is closed
            dialog.show()
        else:
            showInfo("All downloads finished successfully!")
            self.close()

    @pyqtSlot()
    def slot_clicked_button(self):
        """Pause button"""
        self.th.toggle_status()
        self.pb.setText({True: "Pause", False: "Resume"}[self.th.status])

    def select_lang(self, missing):
        """Recursive function that addresses all cards' decks that are missing a language"""
        deck_id = missing[len(missing) - 1]
        d = LanguageSelector(self.parent, self.mw.col.decks.get(deck_id)["name"])

        def handle_lang_select():
            if d.selected_lang is not None:
                self.config.set_deck_specific_config_object(
                    ConfigObject(name="language", value=d.selected_lang, deck=deck_id))
                if len(missing) > 1:
                    """If some decks are still missing, address them"""
                    missing.pop()
                    self.select_lang(missing)
                else:
                    """If all conflicts are done, start the downloads (yay)"""
                    self.start_downloads()
            else:
                """dummy didn't select a language"""
                showInfo("Cancelled download because no language was selected.")
                return

        d.finished.connect(handle_lang_select)
        d.show()

    def ensure_languages(self):
        """Ensures that the language is set for all selected decks; otherwise show dialog"""
        missing = list(set([card.did for card in self.cards if
                            self.config.get_deck_specific_config_object("language", card.did) is None]))
        if len(missing) > 0:
            self.select_lang(missing)
        else:
            self.start_downloads()

    def start_downloads_wrapper(self):
        """Starts the whole procedure that involves ensuring fields and ensuring languages"""
        self.ensure_fields()

    def select_field(self, missing_ids: List[int], field_type: str):
        """Recursive function that addresses all decks that are missing the field assignment"""
        note_type = missing_ids[len(missing_ids) - 1]
        d = FieldSelector(self.parent, self.mw, note_type, field_type, self.config)

        def handle_field_select():
            if d.selected_field is not None:
                self.config.set_note_type_specific_config_object(
                    ConfigObject(name=field_type, value=d.selected_field, note_type=note_type))
                if len(missing_ids) > 1:
                    missing_ids.pop()
                    self.select_field(missing_ids, field_type)
                else:
                    if field_type == "audioField":
                        """If the program asked for audioFields (which come after the searchFields) and it's done, start the ensure_languages procedure"""
                        self.ensure_languages()
                        return
                    # POV: Asked for searchField -> now ask for audioField
                    new_missing = list(set([card.note_type()["id"] for card in self.cards if
                                            self.config.get_note_type_specific_config_object("audioField",
                                                                                             card.note_type()[
                                                                                                 "id"]) is None]))

                    if len(new_missing) > 0:
                        self.select_field(new_missing, "audioField")
                    else:
                        """If none cards are missing their audioField, ensure the languages!"""
                        self.ensure_languages()
            else:
                """dummy didn't select their fields"""
                showInfo("Cancelled download because field wasn't selected.")
                return

        d.finished.connect(handle_field_select)
        d.show()

    def ensure_fields(self):
        missing = list(set([card.note_type()["id"] for card in self.cards if
                            self.config.get_note_type_specific_config_object("searchField",
                                                                             card.note_type()["id"]) is None]))
        if len(missing) > 0:
            """If some cards don't have their searchFields assigned yet, beg the user to do so!"""
            self.select_field(missing, "searchField")
        else:
            """If all cards have a searchField assigned:"""

            new_missing = list(set([card.note_type()["id"] for card in self.cards if
                                    self.config.get_note_type_specific_config_object("audioField",
                                                                                     card.note_type()[
                                                                                         "id"]) is None]))
            if len(new_missing) > 0:
                """Cards have the searchField assignment but are lacking the audioField one"""
                self.select_field(new_missing, "audioField")
            else:
                """everything's alright!"""
                self.start_downloads()

    def start_downloads(self):
        """FINALLY start the downloads"""
        self.btn.setVisible(False)                # }--- disable some controls and make others visible
        self.pb.setVisible(True)                  # }
        self.progress.setVisible(True)            # }
        self.adjustSize()   # readjust size of window, we just "added" some controls
        self.th.start()  # actually start the download thread

    def update_progress_bar(self):
        """Gets called by signal emitted by download thread, increases the progress bar by 1."""
        self.progress.setValue(self.progress.value() + 1)


class Thread(QThread):
    """The downloading is handled in a separate thread in order for the progress bar and the pause button to work"""
    change_value = pyqtSignal(int)
    done = pyqtSignal(int)

    def __init__(self, cards, mw, config):
        QThread.__init__(self)
        self.cond = QWaitCondition()
        self.mutex = QMutex()
        self.cnt = 0
        self._status = True
        self.cards = cards
        self.mw = mw
        self.failed: List[FailedDownload] = []
        self.config: Config = config

    def __del__(self):
        self.wait()

    def run(self):
        card: Card
        for card in self.cards:
            """Go through all cards that are selected in the editor"""
            self.mutex.lock()
            if not self._status:  # If download is paused, wait
                self.cond.wait(self.mutex)
            try:  # use try to avoid stopping the entire thread because of a single exception
                # Get fields from config
                query_field = self.config.get_note_type_specific_config_object("searchField", card.note_type()["id"]).value
                audio_field = self.config.get_note_type_specific_config_object("audioField", card.note_type()["id"]).value

                if query_field not in card.note():
                    raise FieldNotFoundException(query_field)

                query = card.note()[query_field]  # Get query string from card's note using field name

                # Get language from config for the card's deck
                language = self.config.get_deck_specific_config_object("language", card.did).value

                # Get the results
                results = Forvo(query, language, self.mw) \
                    .load_search_query() \
                    .get_pronunciations().pronunciations

                results.sort(key=lambda result: result.votes)  # sort by votes

                top: Pronunciation = results[len(results) - 1]  # get most upvoted pronunciation
                top.download_pronunciation()  # download that
                if self.config.get_config_object("appendAudio").value:
                    card.note()[audio_field] += "[sound:%s]" % top.audio  # set audio field content to the respective sound
                else:
                    card.note()[audio_field] = "[sound:%s]" % top.audio  # set audio field content to the respective sound
                card.note().flush()  # flush the toilet
            except Exception as e:
                # Save all raised exceptions in a list to retrieve them later in the FailedDownloadsDialog
                self.failed.append(FailedDownload(reason=e, card=card))
            self.cnt += 1  # Increase count for progress bar
            self.change_value.emit(self.cnt)  # emit signal to update progress bar
            self.msleep(500)  # sleep to give progress bar time to update

            self.mutex.unlock()

        Forvo.cleanup(None)  # cleanup files in temp directory (None is passed as the self parameter here)

    def toggle_status(self):  # toggle pause state
        self._status = not self._status
        if self._status:
            self.cond.wakeAll()

    @property
    def status(self):
        return self._status
