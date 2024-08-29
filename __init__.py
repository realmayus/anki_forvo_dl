import functools
import pathlib
from typing import List, Tuple

import anki
import aqt.utils
from anki.hooks import addHook
from anki.notes import Note
from aqt import mw, gui_hooks
from aqt.editor import Editor
from aqt.operations import QueryOp
from aqt.qt import *
from aqt.utils import showInfo, showWarning
from aqt.webview import WebContent
from bs4 import BeautifulSoup

from .src.About import About
from .src.AddSentence import AddSentence
from .src.AddSingle import AddSingle
from .src.Config import Config, ConfigObject, OptionType
from .src.ConfigManager import ConfigManager
from .src.Exceptions import FieldNotFoundException, NoResultsException
from .src.FieldSelector import FieldSelector
from .src.Forvo import Forvo, Pronunciation
from .src.LanguageSelector import LanguageSelector
from .src.Tatoeba import Sentence, Tatoeba
from .src.WhatsNew import get_changelogs, WhatsNew
from .src.util.Util import get_field_id, parse_version

"""Release:"""
release_ver = "1.2.0"

"""Paths to directories get determined based on __file__"""
asset_dir = os.path.join(pathlib.Path(__file__).parent.absolute(), "assets")
temp_dir = os.path.join(pathlib.Path(__file__).parent.absolute(), "temp")
user_files_dir = os.path.join(pathlib.Path(__file__).parent.absolute(), "user_files")
log_dir = os.path.join(pathlib.Path(__file__).parent.absolute(), "user_files", "logs")

debug_mode = os.path.isfile(os.path.join(user_files_dir, ".debug"))

"""Ensure directories (create if not existing)"""
for path in [temp_dir, user_files_dir, log_dir]:
    if not os.path.exists(path):
        os.makedirs(path)

config = Config(os.path.join(user_files_dir, "config.json"),
                os.path.join(asset_dir, "config.template.json")).load_config().load_template().ensure_options()


def handle_field_select(d, note_type_id, field_type, editor):
    if d.selected_field is not None:
        co = ConfigObject(name=field_type, value=d.selected_field, note_type=note_type_id, type=OptionType.TEXT)
        config.set_note_type_specific_config_object(co)
        return co
    else:
        showInfo("Cancelled download because fields weren't selected.", editor.widget)
        return None

def insert_pronunciation(note: Note, pronunciation: Pronunciation, audio_field: str, editor_widget: QWidget, note_type_id: int):
    try:
        if config.get_config_object("audioFieldAddMode").value == "append":
            note.fields[
                get_field_id(audio_field, note)] += "[sound:%s]" % pronunciation.audio
        elif config.get_config_object("audioFieldAddMode").value == "replace":
            note.fields[
                get_field_id(audio_field, note)] = "[sound:%s]" % pronunciation.audio
        else:  # prepend
            note.fields[
                get_field_id(audio_field, note)] = "[sound:%s]" % pronunciation.audio + note.fields[
                get_field_id(audio_field, note)]
    except FieldNotFoundException:
        showWarning(
            f"Couldn't find field '{audio_field}' for adding the audio string. Please create a field with "
            f"this name or change it in the config for the note type id {str(note_type_id)}", editor_widget)


def on_fetch_success(forvo: Forvo, editor: Editor, note: Note, mode: str, audio_field: str, note_type_id: int):
    try:
        if forvo is None:
            raise NoResultsException()
        results = forvo.get_pronunciations().pronunciations
    except NoResultsException:
        showInfo("No results found! :(", editor.widget)
        return

    hidden_entries_amount = 0
    if config.get_config_object("skipOggFallback").value:
        viable_entries = [p for p in results if not p.is_ogg]
        hidden_entries_amount = len(results) - len(viable_entries)
        if len(viable_entries) == 0:
            showInfo(
                f"No results found! :(\nThere are {hidden_entries_amount} entries which you chose to skip by deactivating .ogg fallback.")
            return
        results = viable_entries

    if mode == "auto":
        def add_automatically(auto_results):
            """If shift key is held down"""
            auto_results.sort(key=lambda result: result.votes)  # sort by votes
            top: Pronunciation = auto_results[len(auto_results) - 1]  # get most upvoted pronunciation

            def on_download_success():
                insert_pronunciation(note, top, audio_field, editor.widget, note_type_id)
                if config.get_config_object("playAudioAfterAutomaticSelection").value:  # play audio if desired
                    anki.sound.play(top.audio)

                if note == editor.note:  # only update note if it's still the current note
                    def flush_field():
                        if not editor.addMode:  # save
                            mw.col.update_note(note)
                        editor.currentField = get_field_id(audio_field, note)
                        editor.loadNote(focusTo=get_field_id(audio_field, note))

                    editor.saveNow(flush_field, keepFocus=True)
                else:
                    mw.col.update_note(note)

            op = QueryOp(parent=editor.mw, op=lambda x: top.download_pronunciation(),
                         success=lambda x: on_download_success())
            op.run_in_background()

        editor.saveNow(functools.partial(add_automatically, results))
    else:
        dialog = AddSingle(editor.parentWindow, pronunciations=results, hidden_entries_amount=hidden_entries_amount)
        dialog.exec()

        Forvo.cleanup()
        if dialog.selected_pronunciation is not None:
            insert_pronunciation(note, dialog.selected_pronunciation, audio_field, editor.widget, note_type_id)
            if not editor.addMode:
                mw.col.update_note(editor.note)
            editor.loadNote()


def insert_sentence(sentence: Sentence, note: Note, sentence_field: str, sentence_translation_field: str,
                    sentence_audio_field: str, note_type_id: int, deck_id: int, editor: Editor):
    try:
        if config.get_deck_specific_config_object("addTranscription", deck_id).value:
            text = sentence.transcription
        else:
            text = sentence.text_orig
        note.fields[
            get_field_id(sentence_field, note)] += text
    except FieldNotFoundException:
        showWarning(
            f"Couldn't find field '{sentence_field}' for adding the sentence string. Please create a field with "
            f"this name or change it in the config for the note type id {str(note_type_id)}", editor.widget)
    try:
        note.fields[
            get_field_id(sentence_translation_field, note)] += sentence.text_translation
    except FieldNotFoundException:
        showWarning(
            f"Couldn't find field '{sentence_translation_field}' for adding the sentence translation string. Please create a field with "
            f"this name or change it in the config for the note type id {str(note_type_id)}", editor.widget)
    if sentence.audio_orig is not None:
        try:
            note.fields[
                get_field_id(sentence_audio_field, note)] += "[sound:%s]" % sentence.audio_orig
        except FieldNotFoundException:
            showWarning(
                f"Couldn't find field '{sentence_audio_field}' for adding the sentence audio string. Please create a field with "
                f"this name or change it in the config for the note type id {str(note_type_id)}",
                editor.widget)


def on_fetch_sentence_success(tatoeba, editor: Editor, note: Note, mode: str, sentence_field: str,
                              sentence_translation_field: str, sentence_audio_field: str, note_type_id: int,
                              deck_id: int):
    try:
        if tatoeba is None:
            raise NoResultsException()
        results = tatoeba.sentences
    except NoResultsException:
        showInfo("No results found! :(", editor.widget)
        return

    if mode == "auto":
        def add_automatically(auto_results):
            """If shift key is held down"""
            top: Sentence = auto_results[len(auto_results) - 1]  # get most upvoted pronunciation

            def on_download_success():
                insert_sentence(top, note, sentence_field, sentence_translation_field, sentence_audio_field,
                                note_type_id, deck_id, editor)

                if config.get_config_object("playAudioAfterAutomaticSelection").value:  # play audio if desired
                    anki.sound.play(top.audio_orig)

                if note == editor.note:  # only update note if it's still the current note
                    def flush_field():
                        if not editor.addMode:  # save
                            mw.col.update_note(note)
                        editor.currentField = get_field_id(sentence_translation_field, note)
                        editor.loadNote(focusTo=get_field_id(sentence_translation_field, note))

                    editor.saveNow(flush_field, keepFocus=True)
                else:
                    mw.col.update_note(note)

            op = QueryOp(parent=editor.mw, op=lambda x: top.download_pronunciation(),
                         success=lambda x: on_download_success())
            op.run_in_background()

        editor.saveNow(functools.partial(add_automatically, results))
    else:
        dialog = AddSentence(editor.parentWindow, results, config, deck_id)
        dialog.exec()

        Tatoeba.cleanup()
        if dialog.selected_sentence is not None:
            insert_sentence(dialog.selected_sentence, note, sentence_field, sentence_translation_field,
                            sentence_audio_field, note_type_id, deck_id, editor)
            if not editor.addMode:
                mw.col.update_note(editor.note)
            editor.loadNote()


def get_query(note: Note, mode: str, search_field: str, editor_widget: QWidget) -> Union[None, str]:
    if note is None:
        showInfo("Please enter a search term in the field '" + search_field + "'.", editor_widget)
        return None

    if mode == 'input':
        query, suc = aqt.utils.getText("Please enter a custom search term:", editor_widget,
                                       title="Enter custom search term")
        if not suc:
            showWarning("Didn't get any text, please try again.", editor_widget)
            return None
    elif note is not None and search_field in note.keys() and len(note[search_field]) != 0:
        # If available, use the content of the defined search field as the query
        query = note[search_field]
    else:
        showInfo("Please enter a search term in the field '" + search_field + "'.", editor_widget)
        return None

    return BeautifulSoup(query, "html.parser").text  # strip any HTML (if user is using rich text)


def get_deck_language(deck_id, parent_window: QWidget) -> Union[None, str]:
    config_lang = config.get_deck_specific_config_object("language", deck_id)

    if config_lang is None:
        d = LanguageSelector(parent_window, mw.col.decks.get(deck_id)["name"])
        d.exec()
        if d.selected_lang is not None:
            config.set_deck_specific_config_object(
                ConfigObject(name="language", value=d.selected_lang, deck=deck_id, type=OptionType.LANG))
            return d.selected_lang
        else:
            showInfo("Cancelled download because no language was selected.")
            return None
    else:
        return config_lang.value


def get_field(field_name: str, note_type_id: int, editor: Editor) -> Union[str, None]:
    field = config.get_note_type_specific_config_object(field_name, note_type_id)
    if field is None or field.value not in editor.note.keys():
        d = FieldSelector(editor.parentWindow, editor.mw, note_type_id, field_name, config)
        d.exec()
        return handle_field_select(d, note_type_id, field_name, editor).value
    return field.value


def get_note_type_and_deck_id(editor: Editor) -> Tuple[int, int]:
    if editor.note is not None:
        note_type_id = editor.note.mid
    elif editor.card is not None:
        note_type_id = editor.card.note().mid
    else:
        note_type_id = editor.mw.col.models.current()["id"]

    deck_id = editor.card.did if editor.card is not None else editor.parentWindow.deck_chooser.selectedId()
    return note_type_id, deck_id


def fetch_pronunciations(editor: Editor, mode: Union[None, str] = None):
    note_type_id, deck_id = get_note_type_and_deck_id(editor)

    search_field = get_field("searchField", note_type_id, editor)
    if search_field is None:
        return

    audio_field = get_field("audioField", note_type_id, editor)
    if audio_field is None:
        return


    if editor.note is None:
        showInfo("Please enter a search term in the field '" + search_field + "'.", editor.widget)
        return

    query = get_query(editor.note, mode, search_field, editor.widget)
    if query is None:
        return

    if deck_id is not None:
        language = get_deck_language(deck_id, editor.parentWindow)
        if language is None:
            return
        op = QueryOp(parent=editor.mw,
                     op=lambda x: Forvo(query, language, editor.mw.col.media, config).load_search_query(),
                     success=lambda forvo: on_fetch_success(forvo, editor, editor.note, mode, audio_field,
                                                            note_type_id))
        op.run_in_background()


def fetch_sentences(editor: Editor, mode: Union[None, str] = None):
    note_type_id, deck_id = get_note_type_and_deck_id(editor)
    print("11")
    search_field = get_field("searchField", note_type_id, editor)
    if search_field is None:
        return
    print("22")

    sentence_field = get_field("sentenceField", note_type_id, editor)
    if sentence_field is None:
        return

    sentence_translation_field = get_field("sentenceTranslationField", note_type_id, editor)
    if sentence_translation_field is None:
        return

    sentence_audio_field = get_field("sentenceAudioField", note_type_id, editor)
    if sentence_audio_field is None:
        return
    print("boop")
    query = get_query(editor.note, mode, search_field, editor.widget)
    if query is None:
        return

    if deck_id is not None:
        language = get_deck_language(deck_id, editor.parentWindow)
        if language is None:
            return
        shift = QApplication.keyboardModifiers() == Qt.KeyboardModifier.ShiftModifier
        print("SHIFT: ", shift)
        op = QueryOp(parent=editor.mw,
                     op=lambda x: Tatoeba(query, language, "en", editor.mw.col.media, config).load_search_query(coarse=shift),
                     success=lambda tatoeba: on_fetch_sentence_success(tatoeba, editor, editor.note, mode,
                                                                       sentence_field, sentence_translation_field,
                                                                       sentence_audio_field, note_type_id, deck_id))
        op.run_in_background()


def on_editor_pronunciation_click(editor: Editor, mode: Union[None, str] = None):
    editor.saveNow(lambda: fetch_pronunciations(editor, mode))


def on_editor_sentence_click(editor: Editor, mode: Union[None, str] = None):
    editor.saveNow(lambda: fetch_sentences(editor, mode))


def add_editor_button(buttons: List[str], editor: Editor):
    editor._links["forvo_dl"] = on_editor_pronunciation_click
    editor._links["sentence_dl"] = on_editor_sentence_click
    if os.path.isabs(os.path.join(asset_dir, "icon.png")):
        iconstr = editor.resourceToData(os.path.join(asset_dir, "icon.png"))
    else:
        iconstr = "/_anki/imgs/{}.png".format(os.path.join(asset_dir, "icon.png"))

    return buttons + [
        "<div title=\"Add Forvo Pronunciation\n\nCTRL+F to open window\nCTRL+SHIFT+F to select top audio "
        "automatically\nCTRL+ALT+F to search for custom term\" style=\"float: right; margin: 0 3px\"><div "
        "style=\"display: flex; width: 50px; height: 25px; justify-content: center; align-items: center; padding: 0 "
        "5px; border-radius: 5px; background-color: #0094FF; color: #ffffff; font-size: 10px\" onclick=\"pycmd("
        "'forvo_dl');return false;\"><img style=\"height: 20px; width: 20px\" src=\"%s\"/></div></div>" % iconstr,

        "<div title=\"Add Tatoeba Sentence\n\nSHIFT+click for coarse search\nCTRL+S to open window\nCTRL+SHIFT+S to select top "
        "sentence\nCTRL+ALT+S to search for custom term\" style=\"float: right; margin: 0 3px\"><div "
        "style=\"display: flex; width: 50px; height: 25px; justify-content: center; align-items: center; padding: 0 "
        "5px; border-radius: 5px; background-color: #00AA00; color: #ffffff; font-size: 10px\" onclick=\"pycmd("
        "'sentence_dl');return false;\">!?</div></div>"
    ]


def add_editor_shortcut(shortcuts: List[Tuple], editor: Editor):
    shortcuts.append(("Ctrl+F", lambda: on_editor_pronunciation_click(editor, 'select')))
    shortcuts.append(("Ctrl+Alt+F", lambda: on_editor_pronunciation_click(editor, 'input')))
    shortcuts.append(("Ctrl+Shift+F", lambda: on_editor_pronunciation_click(editor, 'auto')))

    shortcuts.append(("Ctrl+S", lambda: on_editor_sentence_click(editor, 'select')))
    shortcuts.append(("Ctrl+Alt+S", lambda: on_editor_sentence_click(editor, 'input')))
    shortcuts.append(("Ctrl+Shift+S", lambda: on_editor_sentence_click(editor, 'auto')))


def on_pref_btn_click():
    config_manager = ConfigManager(config)
    config_manager.exec()


def on_about_btn_click():
    showInfo(
        f"VERSION: v.{release_ver}\n\n-----------\n\nこんにちは！\nMade by realmayus.\nPlease see https://github.com/realmayus/anki_forvo_dl for more information.")


def show_whats_new():
    config_ver_obj = config.get_config_object("configVersion")
    config_ver = config_ver_obj.value
    changelogs = get_changelogs(config_ver)
    if parse_version(config_ver) < parse_version(release_ver) and changelogs is not None:
        whatsnew = WhatsNew(mw, changelogs)
        whatsnew.exec()
        config_ver_obj.value = release_ver
        config.set_config_object(config_ver_obj)


def on_webview_will_set_content(web_content: WebContent, context) -> None:
    addon_package = mw.addonManager.addonFromModule(__name__)
    web_content.css.append(
        f"/_addons/{addon_package}/web/sentence_web.css")
    web_content.js.append(
        f"/_addons/{addon_package}/web/sentence_web.js")


about = About(mw)
addHook("setupEditorButtons", add_editor_button)
gui_hooks.editor_did_init_shortcuts.append(add_editor_shortcut)

gui_hooks.main_window_did_init.append(show_whats_new)
print("__name__", __name__)
mw.addonManager.setWebExports(__name__, r"web/.*")
gui_hooks.webview_will_set_content(on_webview_will_set_content, None)
menu = QMenu("anki-forvo-dl", aqt.mw)
pref_action = QAction("Preferences", menu)
about_action = QAction("About", menu)
menu.addAction(pref_action)
menu.addAction(about_action)

pref_action.triggered.connect(on_pref_btn_click)  # type: ignore
about_action.triggered.connect(on_about_btn_click)  # type: ignore

aqt.mw.form.menuTools.addMenu(menu)
