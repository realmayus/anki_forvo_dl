class AnkiForvoException(Exception):
    friendly = "AnkiForvoException"
    info = "An exception occurred in the anki-forvo-dl add-on."

    def __str__(self):
        return self.friendly + ": " + self.info


class NoResultsException(AnkiForvoException):
    friendly = "No results found"
    info = "No pronunciations were found on Forvo for the cards."


class FieldNotFoundException(AnkiForvoException):
    friendly = "Field not found"
    info = "A field couldn't be found."

    def __init__(self, field_name: str):
        self.field_name = field_name
        self.specific_info = "'%s'" % field_name


class DownloadCancelledException(AnkiForvoException):
    friendly = "Download cancelled"
    info = "These pronunciations couldn't be downloaded because the download was cancelled."


all_errors = [NoResultsException, FieldNotFoundException]
