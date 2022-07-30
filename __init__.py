import functools
import pathlib
from typing import List, Tuple, Union
import os
import anki
import aqt.utils
from anki.hooks import addHook
from aqt import mw, gui_hooks
from aqt.editor import Editor
from aqt.qt import *
from aqt.utils import showInfo, showWarning
from bs4 import BeautifulSoup

from .src.About import About
from .src.AddSingle import AddSingle
from .src.Config import Config, ConfigObject, OptionType
from .src.ConfigManager import ConfigManager
from .src.Exceptions import NoResultsException, FieldNotFoundException
from .src.FieldSelector import FieldSelector
from .src.Forvo import Forvo, Pronunciation
from .src.LanguageSelector import LanguageSelector
from .src.util.Util import get_field_id, parse_version
from .src.WhatsNew import get_changelogs, WhatsNew


"""Release:"""
release_ver = "1.0.6"


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


def add_pronunciation(editor: Editor, mode: Union[None, str] = None):
    if mode is None:
        modifiers = QApplication.keyboardModifiers()
        if modifiers == Qt.ShiftModifier:
            """Choose top pronunciation automatically when shift key is held down"""
            mode = "auto"

    deck_id = editor.card.did if editor.card is not None else editor.parentWindow.deckChooser.selectedId()

    if editor.note is not None:
        note_type_id = editor.note.mid
    elif editor.card is not None:
        note_type_id = editor.card.note().mid
    else:
        note_type_id = editor.mw.col.models.current()["id"]

    search_field = config.get_note_type_specific_config_object("searchField", note_type_id)
    if search_field is None or search_field.value not in editor.note.keys():
        d = FieldSelector(editor.parentWindow, editor.mw, note_type_id, "searchField", config)
        d.exec()
        search_field = handle_field_select(d, note_type_id, "searchField", editor)
        if search_field is None:
            return

    audio_field = config.get_note_type_specific_config_object("audioField", note_type_id)
    if audio_field is None or audio_field.value not in editor.note.keys():
        d = FieldSelector(editor.parentWindow, editor.mw, note_type_id, "audioField", config)
        d.exec()
        audio_field = handle_field_select(d, note_type_id, "audioField", editor)
        if audio_field is None:
            return

    search_field = search_field.value
    audio_field = audio_field.value

    if editor.note is None:
        showInfo("Please enter a search term in the field '" + search_field + "'.", editor.widget)
        return

    if mode == 'input':
        query, suc = aqt.utils.getText("Please enter a custom search term:", editor.widget,
                                       title="Enter custom search term")
        if not suc:
            showWarning("Didn't get any text, please try again.", editor.widget)
            return
    elif editor.note is not None and search_field in editor.note.keys() and len(editor.note[search_field]) != 0:
        """If available, use the content of the defined search field as the query"""
        query = editor.note[search_field]
    else:
        showInfo("Please enter a search term in the field '" + search_field + "'.", editor.widget)
        return

    query = BeautifulSoup(query, "html.parser").text

    if deck_id is not None:
        config_lang = config.get_deck_specific_config_object("language", deck_id)

        if config_lang is None:
            d = LanguageSelector(editor.parentWindow, mw.col.decks.get(deck_id)["name"])
            d.exec()
            if d.selected_lang is not None:
                config.set_deck_specific_config_object(
                    ConfigObject(name="language", value=d.selected_lang, deck=deck_id, type=OptionType.LANG))
                language = d.selected_lang
            else:
                showInfo("Cancelled download because no language was selected.")
                return
        else:
            language = config_lang.value

        try:
            forvo = Forvo(query, language, editor.mw, config).load_search_query()
            if forvo is not None:
                results = forvo.get_pronunciations().pronunciations
            else:
                raise NoResultsException()
        except NoResultsException:
            showInfo("No results found! :(", editor.widget)
            return

        hidden_entries_amount = 0
        if config.get_config_object("skipOggFallback").value:
            viable_entries = [p for p in results if not p.is_ogg]
            hidden_entries_amount = len(results) - len(viable_entries)
            if len(viable_entries) == 0:
                showInfo(f"No results found! :(\nThere are {hidden_entries_amount} entries which you chose to skip by deactivating .ogg fallback.")
                return
            results = viable_entries


        if mode == "auto":
            def add_automatically(auto_results):
                """If shift key is held down"""
                auto_results.sort(key=lambda result: result.votes)  # sort by votes
                top: Pronunciation = auto_results[len(auto_results) - 1]  # get most upvoted pronunciation
                top.download_pronunciation()  # download that
                try:
                    if config.get_config_object("audioFieldAddMode").value == "append":
                        """append"""
                        editor.note.fields[
                            get_field_id(audio_field, editor.note)] += "[sound:%s]" % top.audio
                    elif config.get_config_object("audioFieldAddMode").value == "replace":
                        """replace"""
                        editor.note.fields[
                            get_field_id(audio_field, editor.note)] = "[sound:%s]" % top.audio
                    else:
                        """prepend"""
                        editor.note.fields[
                            get_field_id(audio_field, editor.note)] = "[sound:%s]" % top.audio + editor.note.fields[
                            get_field_id(audio_field, editor.note)]
                except FieldNotFoundException:
                    showWarning(
                        "Couldn't find field '%s' for adding the audio string. Please create a field with this name or change it in the config for the note type id %s" % (
                            audio_field, str(note_type_id)), editor.widget)

                if config.get_config_object("playAudioAfterSingleAddAutomaticSelection").value:  # play audio if desired
                    anki.sound.play(top.audio)

                def flush_field():
                    if not editor.addMode:  # save
                        editor.note.flush()
                    editor.currentField = get_field_id(audio_field, editor.note)
                    editor.loadNote(focusTo=get_field_id(audio_field, editor.note))

                editor.saveNow(flush_field, keepFocus=True)

            editor.saveNow(functools.partial(add_automatically, results), keepFocus=False)
        else:
            dialog = AddSingle(editor.parentWindow, pronunciations=results, hidden_entries_amount=hidden_entries_amount)
            dialog.exec()

            Forvo.cleanup()
            if dialog.selected_pronunciation is not None:
                try:
                    add_mode = config.get_config_object("audioFieldAddMode").value
                    if add_mode == "append":
                        editor.note.fields[
                            get_field_id(audio_field,
                                         editor.note)] += "[sound:%s]" % dialog.selected_pronunciation.audio
                    elif add_mode == "prepend":
                        editor.note.fields[
                            get_field_id(audio_field,
                                         editor.note)] = "[sound:%s]" % dialog.selected_pronunciation.audio + \
                                                         editor.note.fields[
                                                             get_field_id(audio_field,
                                                                          editor.note)]
                    elif add_mode == "replace":
                        editor.note.fields[
                            get_field_id(audio_field,
                                         editor.note)] = "[sound:%s]" % dialog.selected_pronunciation.audio
                except FieldNotFoundException:
                    showWarning(
                        "Couldn't find field '%s' for adding the audio string. Please create a field with this name or change it in the config for the note type id %s" % (
                            audio_field, str(note_type_id)), editor.widget)
                if not editor.addMode:
                    editor.note.flush()
                editor.loadNote()


def on_editor_btn_click(editor: Editor, mode: Union[None, str] = None):
    editor.saveNow(lambda: add_pronunciation(editor, mode))


def add_editor_button(buttons: List[str], editor: Editor):
    editor._links["forvo_dl"] = on_editor_btn_click
    if os.path.isabs(os.path.join(asset_dir, "icon.png")):
        iconstr = editor.resourceToData(os.path.join(asset_dir, "icon.png"))
    else:
        iconstr = "/_anki/imgs/{}.png".format(os.path.join(asset_dir, "icon.png"))

    return buttons + [
        "<div title=\"Hold down shift + click to select top audio\n\nCTRL+F to open window\nCTRL+SHIFT+F to select top audio\nCTRL+S to search for custom term\" style=\"float: right; margin: 0 3px\"><div style=\"display: flex; width: 50px; height: 25px; justify-content: center; align-items: center; padding: 0 5px; border-radius: 5px; background-color: #0094FF; color: #ffffff; font-size: 10px\" onclick=\"pycmd('forvo_dl');return false;\"><img style=\"height: 20px; width: 20px\" src=\"%s\"/></div></div>" % iconstr]


def add_editor_shortcut(shortcuts: List[Tuple], editor: Editor):
    shortcuts.append(("Ctrl+S", lambda: on_editor_btn_click(editor, 'input')))
    shortcuts.append(("Ctrl+F", lambda: on_editor_btn_click(editor, 'select')))
    shortcuts.append(("Ctrl+Shift+F", lambda: on_editor_btn_click(editor, 'auto')))


def on_pref_btn_click():
    config_manager = ConfigManager(config)
    config_manager.exec()


def on_about_btn_click():
    showInfo(f"VERSION: v.{release_ver}\n\n-----------\n\nこんにちは！\nMade by realmayus.\nPlease see https://github.com/realmayus/anki_forvo_dl for more information.")


def show_whats_new():
    config_ver_obj = config.get_config_object("configVersion")
    config_ver = config_ver_obj.value
    changelogs = get_changelogs(config_ver)
    if parse_version(config_ver) < parse_version(release_ver) and changelogs is not None:
        whatsnew = WhatsNew(mw, changelogs)
        whatsnew.exec()
        config_ver_obj.value = release_ver
        config.set_config_object(config_ver_obj)


about = About(mw)
addHook("setupEditorButtons", add_editor_button)
gui_hooks.editor_did_init_shortcuts.append(add_editor_shortcut)

gui_hooks.main_window_did_init.append(show_whats_new)

menu = QMenu("anki-forvo-dl", aqt.mw)
pref_action = QAction("Preferences", menu)
about_action = QAction("About", menu)
menu.addAction(pref_action)
menu.addAction(about_action)

pref_action.triggered.connect(on_pref_btn_click)  # type: ignore
about_action.triggered.connect(on_about_btn_click)  # type: ignore

aqt.mw.form.menuTools.addMenu(menu)
