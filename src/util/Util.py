import os
import platform
import subprocess
from dataclasses import dataclass

from aqt.qt import QScrollBar
from anki.cards import Card
from anki.notes import Note

from ..Exceptions import FieldNotFoundException


def get_field_id(field_name: str, note: Note) -> int:
    res = next((i for i, item in enumerate(note.items()) if item[0] == field_name), None)
    if res is None:
        raise FieldNotFoundException(field_name)
    return res


class CustomScrollbar(QScrollBar):
    def __init__(self, *__args):
        super().__init__(*__args)
        self.setStyleSheet("""

        QScrollBar:vertical {
            background-color: #C5D4E2;
            width: 7px;
            padding: 0px 3px 0px 0px;
        }

        QScrollBar::handle:vertical {
            background: #000000;
            min-height: 0px;
            width: 7px;
            border-radius: 1px;
        }

        QScrollBar::add-line:vertical {
            height: 0px;
            subcontrol-position: bottom;
            subcontrol-origin: margin;
        }

        QScrollBar::sub-line:vertical {
            height: 0 px;
            subcontrol-position: top;
            subcontrol-origin: margin;
        }
        """
                           )


@dataclass()
class FailedDownload:
    card: Card
    reason: Exception


def open_file(path):
    if platform.system() == "Windows":
        os.startfile(path)
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


def log_debug(msg):
    from ... import user_files_dir, debug_mode
    if debug_mode:
        with open(os.path.join(user_files_dir, "logs", "debug"), "a", encoding="utf8") as f:
            f.write(msg + "\n")


def delete_layout_contents(layout):
    if layout is not None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
            else:
                delete_layout_contents(item.layout())


def parse_version(version):
    return tuple(map(int, (version.split("."))))
