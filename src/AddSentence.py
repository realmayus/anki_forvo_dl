import json
import os
from typing import List

import anki
from PyQt6.QtWidgets import QWidget, QDialog, QVBoxLayout, QCheckBox
from aqt import mw
from aqt.webview import AnkiWebView

from . import Config
from .Tatoeba import Sentence
from .util.Util import resource_to_data
from .Config import ConfigObject, OptionType

class AddSentenceWebView(AnkiWebView):
    def __init__(self, parent: QWidget) -> None:
        AnkiWebView.__init__(self, parent=parent)


def to_sentence_json_list(sentences: List[Sentence]) -> str:
    # need double json.dumps as it doesn't escape the backslashes used to escape quotes
    return json.dumps(json.dumps([{"id": s.id, "text_orig": s.text_orig, "text_translation": s.text_translation,
                        "transcription": s.transcription, "has_audio": s.audio_orig_id is not None, "author": s.author} for s in sentences])).replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


class AddSentence(QDialog):
    def __init__(self, parent, sentences: List[Sentence], config: Config, deck_id: int):
        super().__init__(parent)
        self.web = AddSentenceWebView(self)
        self.web.set_bridge_command(self.on_bridge_cmd, self)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.setMinimumWidth(770)
        self.setMinimumHeight(500)
        self.setMaximumWidth(770)
        self.setMaximumHeight(500)

        # checkbox "Add transcription"
        self.checkbox = QCheckBox("Add transcription")
        self.add_transcription_config = config.get_deck_specific_config_object("addTranscription", deck_id)
        self.checkbox.setChecked(self.add_transcription_config.value)
        self.checkbox.stateChanged.connect(lambda state: self.toggle_transcription(state, config, deck_id))
        self.layout.addWidget(self.checkbox)

        self.layout.addWidget(self.web)
        self.sentences = sentences

        self.selected_sentence = None
        self.setup_web()

    def toggle_transcription(self, state, config: Config, deck_id: int):
        config.set_deck_specific_config_object(ConfigObject(name="addTranscription", value=state == 2, deck=deck_id, type=OptionType.BOOLEAN))

    def setup_web(self) -> None:
        from .. import asset_dir
        addon_package = mw.addonManager.addonFromModule(__name__)
        self.web.stdHtml(
            "",
            context=self,
            css=[f"/_addons/{addon_package}/web/sentence_web.css"],
            js=[f"/_addons/{addon_package}/web/sentence_web.js"],
            default_css=False,
        )
        sentences_json = to_sentence_json_list(self.sentences)
        images = [resource_to_data(os.path.join(asset_dir, "play_button.png")),
                  resource_to_data(os.path.join(asset_dir, "checkmark.png"))]
        print("Sentences JSON: ", sentences_json)
        self.web.eval(f"setup({sentences_json}, {json.dumps(images)})")
        self.web.show()

    def on_bridge_cmd(self, cmd: str):
        if cmd.startswith("play:") or cmd.startswith("add:"):
            sentence = next(s for s in self.sentences if s.id == int(cmd.split(":")[1]))
            if sentence.audio_orig_id is not None and sentence.audio_orig is None:
                sentence.download_pronunciation()
            if cmd.startswith("play:"):
                anki.sound.play(sentence.audio_orig)
            else:
                self.selected_sentence = sentence
                self.accept()
