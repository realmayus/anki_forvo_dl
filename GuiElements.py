from functools import partial

from PyQt5.QtCore import QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QLayout, QDialog, QPushButton, QVBoxLayout, QWidget, QHBoxLayout, QLineEdit, QLabel, \
    QComboBox

from .Config import ConfigObject
from .Util import delete_layout_contents

import os


class ControlElement:
    def __init__(self, option_name: str, config_object: ConfigObject, outer_layout: QLayout, dialog: QDialog, update_callback):
        self.option_name = option_name
        self.state = config_object.value
        self.outer_layout = outer_layout
        self.dialog = dialog
        self.update_callback = update_callback
        self.edit_control = None
        self.add_btn = QPushButton("Add item")
        self.add_btn.setAutoDefault(False)
        self.add_btn.clicked.connect(lambda: self.add_btn_click())
        self.outer_layout.addWidget(self.add_btn)

        self.list_layout = QVBoxLayout()
        self.list_widget = QWidget()
        self.list_widget.setContentsMargins(50, 0, 50, 0)
        self.list_widget.setLayout(self.list_layout)
        self.outer_layout.addWidget(self.list_widget)
        self.is_editing = False
        self.update_view()

    def init_edit_control(self):
        pass

    def set_state(self, new_value):
        # update state
        self.state = new_value
        self.update_view()
        self.update_callback(new_value)

    def delete_entry(self, item, h_layout):
        h_layout.deleteLater()
        self.set_state([x for x in self.state if x != item])

    def render_edit_control(self, h_layout):
        h_layout.addWidget(self.edit_control)

    def render_entries(self):
        from . import asset_dir
        for item in self.state:
            h_layout = QHBoxLayout()
            if len(item) == 0:  # is editing
                self.render_edit_control(h_layout)
            else:
                label = QLabel("'" + item + "'")
                label.setStyleSheet("font-family: monospace; text-align: right; font-size: 16px")
                h_layout.addWidget(label)

            btn = QPushButton("")
            btn.setIcon(QIcon(os.path.join(asset_dir, "checkmark-1.png" if len(item) == 0 else "trashcan.png")))
            btn.setFixedWidth(30)
            btn.setStyleSheet(
                "background-color: #FFFFFF; border: 1px solid gray; border-radius: 2px; cursor: pointer")
            btn.setFixedHeight(30)
            btn.setIconSize(QSize(20, 20))
            h_layout.addWidget(btn)
            btn.pressed.connect(
                partial(self.submit_draft) if len(item) == 0 else partial(self.delete_entry, item, h_layout))
            self.list_layout.addLayout(h_layout)

    def update_view(self):
        delete_layout_contents(self.list_layout)
        self.init_edit_control()
        self.list_widget.adjustSize()
        self.dialog.adjustSize()

        self.render_entries()
        self.list_widget.adjustSize()
        self.dialog.adjustSize()

    def submit_draft(self):
        pass

    def add_btn_click(self):
        pass

class StringListControl(ControlElement):
    """Model-View Controller for string list UI element"""
    def __init__(self, option_name: str, config_object: ConfigObject, outer_layout: QLayout, dialog: QDialog, update_callback):
        super().__init__(option_name, config_object, outer_layout, dialog, update_callback)

    def init_edit_control(self):
        self.edit_control = QLineEdit("")

    def submit_draft(self):
        self.add_btn.setEnabled(True)
        self.is_editing = False
        if self.edit_control.text() in self.state or len(self.edit_control.text()) == 0:
            self.set_state([x for x in self.state if len(x) != 0])
            return
        self.set_state([x for x in self.state if len(x) != 0] + [self.edit_control.text()])

    def add_btn_click(self):
        self.add_btn.setEnabled(False)
        self.is_editing = True
        new_state = [x for x in self.state]
        new_state.append("")
        self.set_state(new_state)

class CountryListControl(ControlElement):
    """Model-View-Controller implementation for country dropdown list"""
    def __init__(self, option_name: str, config_object: ConfigObject, outer_layout: QLayout, dialog: QDialog, update_callback, country_list):
        super().__init__(option_name, config_object, outer_layout, dialog, update_callback)

    def init_edit_control(self):
        self.edit_control = QComboBox()
        [self.edit_control.addItem(country["Name"]) for country in country_list]

    def submit_draft(self):
        self.add_btn.setEnabled(True)
        self.is_editing = False
        if self.edit_control.currentText() in self.state or len(self.edit_control.currentText()) == 0:
            self.set_state([x for x in self.state if len(x) != 0])
            return
        self.set_state([x for x in self.state if len(x) != 0] + [self.edit_control.text()])

    def add_btn_click(self):
        self.add_btn.setEnabled(False)
        self.is_editing = True
        new_state = [x for x in self.state]
        new_state.append("")
        self.set_state(new_state)
