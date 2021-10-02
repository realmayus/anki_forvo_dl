import os
from typing import Union
from PyQt5.QtWidgets import QDialog, QLabel, QVBoxLayout, QSizePolicy, QLayout

from .Util import parse_version


class WhatsNew(QDialog):
    def __init__(self, parent, changelogs):
        from .. import release_ver
        super().__init__(parent)
        self.setWindowTitle("What's new")
        self.setFixedWidth(400)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.description = "<h1>What's new</h1>"
        self.description += f"<p>anki-forvo-dl has just been updated to version {release_ver.strip()}. Here's what changed:</p>"
        self.description += changelogs
        self.description_l = QLabel(self.description)
        self.description_l.setWordWrap(True)
        self.description_l.adjustSize()
        self.description_l.setFixedHeight(self.description_l.height())
        self.layout.addWidget(self.description_l)
        self.layout.setSizeConstraint(QLayout.SetFixedSize)
        self.adjustSize()


def get_changelogs(current_ver: str) -> Union[str, None]:
    """Returns all changelogs since the passed version in a nicely formatted html string. Returns None if there aren't any changelogs.
       The changelog file is formatted like so:

       ------- start of file
       # 1.0.4
       - Added a nice feature
       - Fixed a bug in the add dialog

       # 1.0.1
       - Added a config dialog
       - Fixed issue that would crash the preferences dialog
       ------- end of file

    """
    from .. import asset_dir
    with open(os.path.join(asset_dir, "changelog"), "r") as f:
        in_block = False
        changelog = ""

        for line in f.readlines():  # iterate through changelog file
            line = line.strip("\n")  # strip from newline characters and whitespace
            if line.startswith("#"):  # if current line indicates the start of a new version block:
                version_str = line[1:]  # actual version number comes after a number sign
                if in_block:
                    changelog += "</ul>"  # close ul tag if we were in a block previously
                    in_block = False
                if parse_version(version_str) > parse_version(current_ver):  # Check if there are any change logs for our version
                    in_block = True
                    changelog += f"<h3>{version_str}</h3>"  # add a headline stating the version number for this block
                    changelog += "<ul>"  # open ul tag (gets closed later)
            elif in_block:
                if len(line) > 2:
                    changelog += f"<li>{line[2:]}</li>"  # add a changelog bullet point; slice removes "bullet point" from raw config string
        if len(changelog) > 0:
            if not changelog.endswith("</ul>"):
                changelog += "</ul>"  # close last ul tag after we've iterated over all options in the changelog
            return changelog
        else:
            return None  # return None if there are no changelogs
