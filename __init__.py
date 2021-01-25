from typing import List

from anki.decks import DeckManager
from anki.hooks import addHook
from aqt import mw, gui_hooks
from aqt.browser import Browser
from aqt.editor import Editor
from aqt.qt import *
from aqt.utils import showInfo

from anki_forvo_dl.About import About
from anki_forvo_dl.AddSingle import AddSingle
from anki_forvo_dl.BulkAdd import BulkAdd
from anki_forvo_dl.ConfigManager import ConfigManager
from anki_forvo_dl.Forvo import Forvo
from anki_forvo_dl.Util import get_field_id

asset_dir = os.path.join(os.readlink(os.path.dirname(__file__)), "assets")
temp_dir = os.path.join(os.readlink(os.path.dirname(__file__)), "temp")
user_files_dir = os.path.join(os.readlink(os.path.dirname(__file__)), "user_files")

search_field = "Word"
audio_field = "Audio"


def ensure_directories():
    """Creates some directories if they don't exist yet."""
    for path in [temp_dir, user_files_dir]:
        if not os.path.exists(path):
            os.makedirs(path)


def on_editor_btn_click(editor: Editor):
    if editor.note is not None and editor.note[search_field] is not None and len(editor.note[search_field]) != 0:
        """If available, use the content of the defined search field as the query"""
        query = editor.note[search_field]
    elif editor.note is not None and editor.currentField is not None and editor.note.fields[editor.currentField] is not None and len(editor.note.fields[editor.currentField]) != 0:
        """If the search field is empty, use the content of the currently selected field"""
        query = editor.note.fields[editor.currentField]
    else:
        """Last resort: Show error"""
        showInfo("Please enter a search term in the field '" + search_field + "' or focus the field you want to search for.\nYou can change the search field under Tools > anki_forvo_dl > Search field")
        return

    results = Forvo(query, "ja", editor.mw)\
        .load_search_query()\
        .get_pronunciations()\
        .download_pronunciations()\
        .cleanup()\
        .pronunciations

    dialog = AddSingle(editor.parentWindow, pronunciations=results)

    def handle_close():
        if dialog.selected_pronunciation is not None:
            editor.note.fields[get_field_id(audio_field, editor.note)] = "[sound:%s]" % dialog.selected_pronunciation.audio
            if not editor.addMode:
                editor.note.flush()
            editor.loadNote()

    dialog.finished.connect(handle_close)
    dialog.show()


def on_browser_ctx_menu_click(browser: Browser, selected):
    dialog = BulkAdd(browser.window(), [browser.mw.col.getCard(card) for card in selected], browser.mw)
    dialog.show()


def add_editor_button(buttons: List[str], editor: Editor):
    editor._links["forvo_dl"] = on_editor_btn_click
    if os.path.isabs(os.path.join(asset_dir, "icon.png")):
        iconstr = editor.resourceToData(os.path.join(asset_dir, "icon.png"))
    else:
        iconstr = "/_anki/imgs/{}.png".format(os.path.join(asset_dir, "icon.png"))

    return buttons + ["<div style=\"float: right; margin: 0 3px\"><div style=\"display: flex; width: 50px; height: 25px; justify-content: center; align-items: center; padding: 0 5px; border-radius: 5px; background-color: #0094FF; color: #ffffff; font-size: 10px\" onclick=\"pycmd('forvo_dl');return false;\"><img style=\"margin-right: 5px; margin-left: 5px; height: 20px; width: 20px\" src=\"%s\"/><b style=\"user-select: none; margin-right: 7px\">Forvo</b></div></div>" % iconstr]


def add_browser_context_menu_entry(browser: Browser, m: QMenu):
    selected = browser.selectedCards()


    m.addSeparator()
    action = m.addAction(QIcon(os.path.join(asset_dir, "icon.png")), "Bulk add Forvo audio to " + str(len(selected)) + " card" + ("s" if len(selected) != 1 else "") + "...")
    action.triggered.connect(lambda: on_browser_ctx_menu_click(browser, selected))


def open_config_manager(parent):
    ConfigManager(parent).show()



def open_about_window():
    ConfigManager(mw).show()


def add_menubar_action():
    menu = QMenu("anki-forvo-dl")
    action_a = QAction("About", menu)
    action_s = QAction("Settings", menu)
    action_a.triggered.connect(open_about_window)
    action_s.triggered.connect(lambda: open_config_manager(mw))
    menu.addAction(action_a)
    menu.addAction(action_s)
    mw.form.menuTools.addAction(action_s)


def test(x):
    deck: DeckManager = mw.col.decks
    deck.all_names_and_ids()
    with open(asset_dir + "/debug.txt", "w", encoding="utf-8") as f:
        f.write(", ".join([str(deck_) for deck_ in deck.all_names_and_ids()]))


about = About(mw)
addHook("setupEditorButtons", add_editor_button)
gui_hooks.browser_will_show_context_menu.append(add_browser_context_menu_entry)
gui_hooks.collection_did_load.append(test)


add_menubar_action()




