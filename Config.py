import copy
import json
import os
from dataclasses import dataclass


asset_dir = os.path.join("/Users/marius/PycharmProjects/anki-scripting/anki_forvo_dl", "assets")
temp_dir = os.path.join("/Users/marius/PycharmProjects/anki-scripting/anki_forvo_dl", "temp")
user_files_dir = os.path.join("/Users/marius/PycharmProjects/anki-scripting/anki_forvo_dl", "user_files")
# TODO
# from anki_forvo_dl import asset_dir, user_files_dir


class NoConfigAvailableForDeckError(Exception):
    def __init__(self, deck):
        super().__init__("No config available for deck %s" % deck)


class ConfigOptionNotPresentInDeckError(Exception):
    def __init__(self, deck: int, config_option: str):
        super().__init__("Config option %s not present in deck %s" % (config_option, deck))


class NoConfigAvailableForNoteTypeError(Exception):
    def __init__(self, note_type):
        super().__init__("No config available for note type %s" % note_type)


class ConfigOptionNotPresentInNoteTypeError(Exception):
    def __init__(self, note_type: int, config_option: str):
        super().__init__("Config option %s not present in note type %s" % (config_option, note_type))


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
        with open(self.config_path, "r") as f:
            self.config = json.loads(f.read())
        return self

    def load_template(self):
        """Loads the template from the file into memory"""
        with open(self.template_path, "r") as f:
            self.template = json.loads(f.read())
        return self

    def _save(self):
        """Saves the current config from memory into the file."""
        with open(self.config_path, "w") as f:
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

    def get_config_objects(self):
        config_dupe = copy.deepcopy(self.config)
        config_dupe.pop("noteTypeSpecific", None)
        config_dupe.pop("deckSpecific", None)

    def get_deck_specific_config_object(self, name: str, deck_id: int) -> 'ConfigObject':
        for deck in self.config["deckSpecific"]:
            deck: dict
            if deck["id"] == deck_id:
                if name in deck.keys():
                    return ConfigObject(
                        name,
                        self.template["deckSpecific"][name]["friendly"],
                        self.template["deckSpecific"][name]["description"],
                        self.template["deckSpecific"][name].get("default", None) or None,
                        list(deck.values())[1],  # items()[0] is "id", items()[1] is name of option
                        deck=deck_id
                    )
                else:
                    return None
        return None

    def get_note_type_specific_config_object(self, name: str, note_type_id: int) -> 'ConfigObject':
        for note_type in self.config["noteTypeSpecific"]:
            note_type: dict
            if note_type["id"] == note_type_id:
                if name in note_type.keys():
                    return ConfigObject(
                        name,
                        self.template["noteTypeSpecific"][name]["friendly"],
                        self.template["noteTypeSpecific"][name]["description"],
                        self.template["noteTypeSpecific"][name].get("default", None) or None,
                        list(note_type.values())[1],  # items()[0] is "id", items()[1] is name of option
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


@dataclass
class ConfigObject:
    """A config 'option' that contains more than is actually saved in config.json -
    it basically merges the template information and the config value into a single object."""
    name: str
    friendly: str = None
    description: str = None
    default: any = None
    value: any = None
    deck: int = None  # Only if deck-specific
    note_type: int = None  # Only if note type-specific



# if __name__ == "__main__":
#     config = Config(os.path.join(user_files_dir, "config.json"), os.path.join(asset_dir, "config.template.json"))
#     config.load_config()
#     config.load_template()
#     config.ensure_options()
#     co = config.get_deck_specific_config_object("language", 878798)
#     coNT = config.get_note_type_specific_config_object("audioField", 9137498)
#     co.value = None
#     config.set_deck_specific_config_object(co, True)
#     coNT.value = "HAHAHAHAHHA"
#     config.set_note_type_specific_config_object(coNT, True)
#     coNT2 = config.get_note_type_specific_config_object("searchField", 9137498)
#
#     coNT2.value = "boop"
#     config.set_note_type_specific_config_object(ConfigObject("test", "A simple fucking test.", "egegegwzefzusef", "foo", note_type=9137498), True)
