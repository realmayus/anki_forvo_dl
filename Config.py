from typing import List

import copy
import json
import os

from aqt.utils import showInfo
from dataclasses import dataclass
from enum import Enum


class ConfigObjectHasNoValue(Exception):
    def __init__(self, config_object: 'ConfigObject'):
        super().__init__("Config object with config option %s has no value and the default value isn't set as fallback" % config_object.name)


class Config:
    """Ridiculously over-engineered class that handles all things config."""
    config: dict
    template: dict

    def __init__(self, config_path: str, template_path: str):
        self.config_path = config_path
        self.template_path = template_path

    def load_config(self):
        """Loads the config from the file into memory"""
        if not os.path.isfile(self.config_path):
            self.config = dict()
            return self
        with open(self.config_path, "r", encoding="utf8") as f:
            self.config = json.loads(f.read())
        return self

    def load_template(self):
        """Loads the template from the file into memory"""
        with open(self.template_path, "r", encoding="utf8") as f:
            self.template = json.loads(f.read())
        return self

    def _save(self):
        """Saves the current config from memory into the file."""
        with open(self.config_path, "w", encoding="utf8") as f:
            f.write(json.dumps(self.config, indent=4))


    def ensure_options(self):
        """Ensures that all options defined in the template are present in the config."""
        for k, v in self.template.items():
            if k != "noteTypeSpecific" and k != "deckSpecific":
                if k not in self.config.keys():
                    self.config[k] = self.template[k]["default"]

        if "noteTypeSpecific" not in self.config.keys():
            self.config["noteTypeSpecific"] = []

        if "deckSpecific" not in self.config.keys():
            self.config["deckSpecific"] = []

        self._save()
        return self

    def set_config_object(self, config_object: 'ConfigObject'):
        self.config[config_object.name] = config_object.value
        self._save()
        self.load_config()


    def get_config_options(self):
        config_dupe = copy.deepcopy(self.config)
        config_dupe.pop("noteTypeSpecific", None)
        config_dupe.pop("deckSpecific", None)
        return config_dupe

    def get_config_objects_template(self):
        general_options = [x for x in self.template.keys() if x != "noteTypeSpecific" and x != "deckSpecific"]
        objects = []
        for option in general_options:
            objects.append(self.get_config_object(option))

        return objects

    def get_nt_config_objects_template(self, note_type_id: int):
        options = [x for x in self.template["noteTypeSpecific"]]
        objects = []
        for option in options:
            objects.append(self.get_note_type_specific_config_object(option, note_type_id))

        return objects


    def get_deck_config_objects_template(self, deck_id: int):
        """Goes through all options in the *template* and then populates them with the actual values from the
        configuration.  """
        options = [x for x in self.template["deckSpecific"]]
        objects = []
        for option in options:
            objects.append(self.get_deck_specific_config_object(option, deck_id))

        return objects


    def get_config_object(self, name) -> 'ConfigObject':
        return ConfigObject(
            name,
            OptionType(self.template[name]["type"]),
            self.template[name]["friendly"],
            self.template[name]["description"],
            self.template[name].get("default", None) or None,
            self.get_config_options()[name],
            options=self.template[name]["options"] if OptionType(self.template[name]["type"]) is OptionType.CHOICE else None
        )

    def get_specified_deck_ids(self) -> List[int]:
        """Returns a list of decks that are defined in the config."""
        return [deck["id"] for deck in self.config["deckSpecific"]]

    def get_deck_specific_config_object(self, name: str, deck_id: int) -> 'ConfigObject':
        for deck in self.config["deckSpecific"]:
            deck: dict
            if deck["id"] == deck_id:
                if name in deck.keys():
                    return ConfigObject(
                        name,
                        OptionType(self.template["deckSpecific"][name]["type"]),
                        self.template["deckSpecific"][name]["friendly"],
                        self.template["deckSpecific"][name]["description"],
                        self.template["deckSpecific"][name].get("default", None) or None,
                        deck[name],
                        deck=deck_id
                    )
                else:
                    return None
        return None

    def get_specified_note_type_ids(self) -> List[int]:
        """Returns a list of note types that are defined in the config."""
        return [nt["id"] for nt in self.config["noteTypeSpecific"]]

    def get_note_type_specific_config_object(self, name: str, note_type_id: int) -> 'ConfigObject':
        for note_type in self.config["noteTypeSpecific"]:
            note_type: dict
            if note_type["id"] == note_type_id:
                if name in note_type.keys():
                    return ConfigObject(
                        name,
                        OptionType(self.template["noteTypeSpecific"][name]["type"]),
                        self.template["noteTypeSpecific"][name]["friendly"],
                        self.template["noteTypeSpecific"][name]["description"],
                        self.template["noteTypeSpecific"][name].get("default", None) or None,
                        note_type[name],
                        note_type=note_type_id
                    )
                else:
                    return None
        return None

    def set_deck_specific_config_object(self, config_object: 'ConfigObject', use_default_as_fallback=False):
        existing: list = self.config["deckSpecific"]
        existing_options_for_deck = copy.deepcopy(next((x for x in existing if x["id"] == config_object.deck), {}))
        existing = [x for x in existing if x["id"] != config_object.deck]
        existing_options_for_deck["id"] = config_object.deck
        if config_object.value is None and not use_default_as_fallback:
            raise ConfigObjectHasNoValue(config_object)
        existing_options_for_deck[config_object.name] = config_object.value or config_object.default
        existing.append(existing_options_for_deck)
        self.config["deckSpecific"] = existing
        self._save()
        self.load_config()

    def set_note_type_specific_config_object(self, config_object: 'ConfigObject', use_default_as_fallback=False):
        existing: list = self.config["noteTypeSpecific"]
        existing_options_for_note_type = copy.deepcopy(next((x for x in existing if x["id"] == config_object.note_type), {}))
        existing = [x for x in existing if x["id"] != config_object.note_type]
        existing_options_for_note_type["id"] = config_object.note_type
        if config_object.value is None and not use_default_as_fallback:
            raise ConfigObjectHasNoValue(config_object)
        existing_options_for_note_type[config_object.name] = config_object.value or config_object.default
        existing.append(existing_options_for_note_type)
        self.config["noteTypeSpecific"] = existing
        self._save()
        self.load_config()


    def get_template(self, option: str, category=None):
        if category is None:
            return self.template[option]
        else:
            return self.template[category][option]


class OptionType(Enum):
    BOOLEAN = "boolean"
    LANG = "lang"
    COUNTRY = "country"
    STRINGLIST = "stringlist"
    CHOICE = "choice"
    TEXT = "text"

@dataclass
class ConfigObject:
    """A config 'option' that contains more than is actually saved in config.json -
    it basically merges the template information and the config value into a single object."""
    name: str
    type: OptionType
    friendly: str = None
    description: str = None
    default: any = None
    value: any = None
    deck: int = None  # Only if deck-specific
    note_type: int = None  # Only if note type-specific
    options: List[str] = None # Only if type=choice
