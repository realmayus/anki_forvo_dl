import os
import platform
import subprocess
from dataclasses import dataclass

from PyQt5.QtWidgets import QScrollBar
from anki.cards import Card
from anki.notes import Note

from .Exceptions import FieldNotFoundException


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

