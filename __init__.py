from typing import List
from anki.hooks import addHook
from anki.notes import Note
from aqt import gui_hooks
from aqt.browser import Browser
from aqt.editor import Editor
from aqt.qt import *
from aqt.utils import showInfo

from anki_forvo_dl.AddSingle import AddSingle
from anki_forvo_dl.BulkAdd import BulkAdd
from anki_forvo_dl.Forvo import Forvo
from anki_forvo_dl.Util import get_field_id

asset_dir = os.path.join(os.readlink(os.path.dirname(__file__)), "assets")
showInfo(asset_dir)
temp_dir = os.path.join(os.readlink(os.path.dirname(__file__)), "temp")

search_field = "Word"
audio_field = "Audio"



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
    # browser.model.selectedCards
    # selected_rows = set(index.row() for index in browser.form.tableView.selectedIndexes())
    selected = browser.selectedCards()
    m.addSeparator()
    action = m.addAction(QIcon(os.path.join(asset_dir, "icon.png")), "Bulk add Forvo audio to " + str(len(selected)) + " card" + ("s" if len(selected) != 1 else "") + "...")
    action.triggered.connect(lambda: on_browser_ctx_menu_click(browser, selected))


addHook("setupEditorButtons", add_editor_button)
gui_hooks.browser_will_show_context_menu.append(add_browser_context_menu_entry)
