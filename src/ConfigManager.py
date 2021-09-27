import json
import os

import aqt
from PyQt5 import QtCore
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLayout, QLineEdit, QComboBox, QCheckBox, QHBoxLayout

from .Config import Config, ConfigObject, OptionType
from .GuiElements import StringListControl
from .Util import delete_layout_contents


class ConfigManager(QDialog):

    def __init__(self, config: Config):
        """Initializes the window."""
        from anki_forvo_dl import asset_dir
        super().__init__()

        self.mw = aqt.mw
        self.config = config

        self.setWindowTitle("Configure anki-forvo-dl")

        self.layout = QHBoxLayout()
        self.layout.setAlignment(QtCore.Qt.AlignTop)
        self.layout.setSpacing(20)
        self.setLayout(self.layout)
        self.layout.setSizeConstraint(QLayout.SetFixedSize)

        # Cache language list
        with open(os.path.join(asset_dir, "languages.json"), encoding="utf8") as f:
            self.language_list = json.loads(f.read())
        with open(os.path.join(asset_dir, "countries.json"), encoding="utf8") as f:
            self.country_list = json.loads(f.read())

        # -----------------------------
        # General Column (note-type- and deck-agnostic settings)
        # -----------------------------
        description = "<h2>General Settings</h2>"
        label = QLabel(description)
        label.setFixedWidth(400)
        label.setContentsMargins(0, 20, 0, 0)

        self.general_col = QVBoxLayout()
        self.general_col.addWidget(label)
        self.general_col.setAlignment(QtCore.Qt.AlignTop)

        for item in self.config.get_config_objects_template():
            item: ConfigObject
            self.add_control_element(self.general_col, item, item.name)


        # -----------------------------
        # Deck Column
        # -----------------------------
        description = "<h2>Deck-specific Settings</h2>"  # big headline
        label = QLabel(description)
        label.setFixedWidth(400)  # ensure width of column
        label.setContentsMargins(0, 20, 0, 0)

        self.deck_col = QVBoxLayout()  # outer column that contains all deck-specific settings
        self.deck_col.setAlignment(QtCore.Qt.AlignTop)
        self.deck_col.addWidget(label)

        selector = QVBoxLayout()  # layout that incorporates deck selection dropdown and label
        selector.setContentsMargins(20, 0, 20, 0)
        selector.setSpacing(5)

        label = QLabel("<b>Select Deck:</b>")
        selector.addWidget(label)

        self.inner_deck_col = QVBoxLayout()  # inner layout (within the deck_col layout) that contains the individual settings
        self.inner_deck_col.setAlignment(QtCore.Qt.AlignTop)

        self.deck_selector = QComboBox()  # Actual dropdown
        self.deck_selector.currentIndexChanged.connect(lambda: self.draw_deck_elements())  # Connect events that fire on dropdown selection change
        self.deck_selector.currentTextChanged.connect(lambda: self.draw_deck_elements())
        selector.addWidget(self.deck_selector)  # add dropdown to layout


        for deck_id in config.get_specified_deck_ids():  # populate the dropdown with all available decks
            self.deck_selector.addItem(self.mw.col.decks.name(deck_id), deck_id)

        self.deck_col.addLayout(selector)  # add the selector layout to the deck column

        self.deck_col.addLayout(self.inner_deck_col)  # add inner layout to deck_col layout

        # draw the actual options
        self.draw_deck_elements()


        # -----------------------------
        # Note Type Column  (nt = Note type)
        # -----------------------------
        description = "<h2>Note Type-specific Settings</h2>"  # big headline
        label = QLabel(description)
        label.setFixedWidth(400)  # ensure width of column
        label.setContentsMargins(0, 20, 0, 0)

        self.nt_col = QVBoxLayout()  # outer column that contains all nt-specific settings
        self.nt_col.setAlignment(QtCore.Qt.AlignTop)
        self.nt_col.addWidget(label)

        selector = QVBoxLayout() # layout that incorporates nt selector and label
        selector.setContentsMargins(20, 0, 20, 0)
        selector.setSpacing(5)

        label = QLabel("<b>Select Note Type:</b>")
        selector.addWidget(label)

        self.inner_nt_col = QVBoxLayout()  # inner layout (within the nt_col layout) that contains the individual settings
        self.inner_nt_col.setAlignment(QtCore.Qt.AlignTop)

        self.nt_selector = QComboBox()  # Actual dropdown
        self.nt_selector.currentIndexChanged.connect(self.draw_nt_elements)  # Connect events that fire on dropdown selection change
        self.nt_selector.currentTextChanged.connect(self.draw_nt_elements)
        selector.addWidget(self.nt_selector)  # add dropdown to layout



        for nt_id in config.get_specified_note_type_ids():  # populate the dropdown with all available NTs
            self.nt_selector.addItem(str(next(nt.name for nt in self.mw.col.models.all_names_and_ids() if nt.id == nt_id)), nt_id)

        self.nt_col.addLayout(selector)  # add the selector layout to the deck column

        self.nt_col.addLayout(self.inner_nt_col)  # add inner layout to nt_col layout

        # draw the actual options
        self.draw_nt_elements()

        # -----------------------------
        self.layout.addLayout(self.general_col)  # add columns to horizontal layout
        self.layout.addLayout(self.deck_col)
        self.layout.addLayout(self.nt_col)
        self.adjustSize()  # recalculate geometry so that everything fits into the window


    def draw_deck_elements(self):
        """Gathers all config objects for a deck and then adds control elements for those."""
        delete_layout_contents(self.inner_deck_col)
        for item in self.config.get_deck_config_objects_template(self.deck_selector.currentData()):
            if item is None:
                continue
            item: ConfigObject
            self.add_control_element(self.inner_deck_col, item, item.name, deck_id=self.deck_selector.currentData())

    def draw_nt_elements(self):
        """Gathers all config objects for a NT and then adds control elements for those."""
        delete_layout_contents(self.inner_nt_col)
        for item in self.config.get_nt_config_objects_template(self.nt_selector.currentData()):
            if item is None:
                continue
            item: ConfigObject
            self.add_control_element(self.inner_nt_col, item, item.name, note_type_id=self.nt_selector.currentData())

    def add_control_element(self, layout: QLayout, config_object: ConfigObject, option_name: str, note_type_id=None, deck_id=None):
        """Adds a control element to a layout. Takes a ConfigObject as input and determines the type of the option.
        Then, a suitable control element is placed in the layout.   """

        # Add title and description
        label = QLabel(f"<b>{config_object.friendly}</b><br/><small>{config_object.description}</small>")
        label.setWordWrap(True)
        label.adjustSize()
        label.setContentsMargins(0, 10, 0, 0)
        layout.addWidget(label)

        # Add control element (dropdown, checkbox, etc.)
        if config_object.type is OptionType.BOOLEAN:
            checkbox = QCheckBox(config_object.name)
            checkbox.setChecked(config_object.value)
            checkbox.stateChanged.connect(lambda new: self.update_state(option_name, bool(new), note_type_id, deck_id))
            checkbox.setContentsMargins(50, 0, 50, 0)
            layout.addWidget(checkbox)

        elif config_object.type is OptionType.LANG:
            language_select = QComboBox()
            [language_select.addItem(lang["English name"], lang["Code"]) for lang in self.language_list]
            language_select.setEditable(True)
            language_select.setCurrentIndex(next(i for i, x in enumerate(self.language_list) if x["Code"] == config_object.value))
            language_select.currentIndexChanged.connect(lambda new: self.update_state(option_name, language_select.itemData(new), note_type_id, deck_id))
            layout.addWidget(language_select)

        elif config_object.type is OptionType.COUNTRY:
            pass
            # CountryListControl(config_object.name, config_object, layout, self, lambda new: self.update_state(option_name, new, note_type_id, deck_id), self.country_list)

        elif config_object.type is OptionType.TEXT:
            control = QLineEdit(config_object.value)
            layout.addWidget(control)
            control.textChanged.connect(lambda new: self.update_state(option_name, new, note_type_id, deck_id))

        elif config_object.type is OptionType.STRINGLIST:
            StringListControl(config_object.name, config_object, layout, self, lambda new: self.update_state(option_name, new, note_type_id, deck_id))

        elif config_object.type is OptionType.CHOICE:
            dropdown = QComboBox()
            dropdown.addItems(config_object.options)
            dropdown.setCurrentIndex(next(i for i, x in enumerate(config_object.options) if x == config_object.value))
            layout.addWidget(dropdown)
            dropdown.currentIndexChanged.connect(lambda new: self.update_state(option_name, new, note_type_id, deck_id))
            dropdown.currentTextChanged.connect(lambda new: self.update_state(option_name, new, note_type_id, deck_id))

    def update_state(self, option_name: str, new_value, note_type_id=None, deck_id=None):
        """Based on the arguments passed, this function automatically determines where in the settings to update the
        specified option.   """
        if note_type_id is not None:
            co = self.config.get_note_type_specific_config_object(option_name, note_type_id)
            co.value = new_value
            self.config.set_note_type_specific_config_object(co)
        elif deck_id is not None:
            co = self.config.get_deck_specific_config_object(option_name, deck_id)
            co.value = new_value
            self.config.set_deck_specific_config_object(co)
        else:
            co = self.config.get_config_object(option_name)
            co.value = new_value
            self.config.set_config_object(co)
