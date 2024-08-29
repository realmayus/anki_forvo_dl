import base64
import mimetypes
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


def resource_to_data(path: str) -> str:
    """Convert a file (specified by a path) into a data URI."""
    if not os.path.exists(path):
        raise FileNotFoundError
    mime, _ = mimetypes.guess_type(path)
    with open(path, "rb") as fp:
        data = fp.read()
        data64 = b"".join(base64.encodebytes(data).splitlines())
        return f"data:{mime};base64,{data64.decode('ascii')}"


# todo: find a better way to do this
# Converts ISO 639-1 language codes to ISO 639-2 language codes
# This is necessary because Tatoeba uses ISO 639-2 language codes, while Forvo uses ISO 639-1 language codes
def language_conversion(iso_639_1_code: str) -> str:
    if iso_639_1_code == "ja":
        return "jpn"
    elif iso_639_1_code == "en":
        return "eng"
    elif iso_639_1_code == "es":
        return "spa"
    elif iso_639_1_code == "fr":
        return "fra"
    elif iso_639_1_code == "de":
        return "deu"
    elif iso_639_1_code == "it":
        return "ita"
    elif iso_639_1_code == "pt":
        return "por"
    elif iso_639_1_code == "ru":
        return "rus"
    else:
        return iso_639_1_code
