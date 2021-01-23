class NoResultsException(Exception):
    friendly = "No results found"
    info = "No pronunciations were found on Forvo for the cards."


class FieldNotFoundException(Exception):
    friendly = "Field not found"
    info = "A field couldn't be found."

    def __init__(self, field_name: str):
        self.field_name = field_name
        self.info = "The field '%s' couldn't be found. Please check the config." % field_name



all_errors = [NoResultsException, FieldNotFoundException]
