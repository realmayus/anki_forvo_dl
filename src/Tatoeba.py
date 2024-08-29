import os
from dataclasses import dataclass
from http.client import HTTPResponse
from typing import Union, List
import urllib.request

import requests
from anki.media import MediaManager

from .Config import Config
from .util.Util import language_conversion

search_api = "https://tatoeba.org/en/api_v0/search?"
audio_api = "https://tatoeba.org/en/audio/download/"


@dataclass
class Sentence:
    id: int
    text_orig: str
    text_translation: str
    audio_orig_id: Union[None, int]  # tatoeba audio id
    audio_orig: Union[None, str]  # anki media id
    transcription: str  # html
    media: MediaManager
    author: str
    audio: Union[None, str] = None

    def download_pronunciation(self):
        """Downloads the pronunciation using the pronunciation url in the pronunciation object, adds the audio to Anki's DB and stores the media id in the pronunciation object."""
        from .. import temp_dir
        req = urllib.request.Request(audio_api + str(self.audio_orig_id))
        filename = "pronunciation_" + self.text_orig.replace("/", "-").replace("\\", "-") + ".mp3"
        for forbidden in ["<", ">", ":", "\"", "/", "\\", "|", "?", "*"]:
            filename = filename.replace(forbidden, "_")
        dl_path = os.path.join(temp_dir, filename)
        with open(dl_path, "wb") as f:
            res: HTTPResponse = urllib.request.urlopen(req)
            f.write(res.read())
            res.close()

        media_name = self.media.add_file(dl_path)
        self.audio_orig = media_name

    def remove_pronunciation(self):
        """Removes the media file that was priorly downloaded"""
        self.media.trash_files([self.audio_orig])
        self.audio_orig = None




def prepare_query_string(input_str: str, config: Config) -> str:
    query = str(input_str)  # clone
    query = query.strip()
    for char in config.get_config_object("replaceCharacters").value:
        query = query.replace(char, "")
    return query


def unescape_ruby(ruby: str) -> str:
    return ruby.replace("\u003C", "<").replace("\u003E", ">")


class Tatoeba:
    def __init__(self, query: str, search_lang: str, target_lang: str, media: MediaManager, config: Config):
        self.query = prepare_query_string(query, config)
        self.search_lang = search_lang
        self.target_lang = target_lang
        self.sentences: List[Sentence] = []
        self.config = config
        self.media = media

    def load_search_query_page(self, page: int, force_audio: bool = False, coarse: bool = False):
        print("[Tatoeba] Fetching page %d" % page)
        # get json from tatoeba at prepare_search_url(self.query, self.search_lang, self.target_lang)
        query = self.query if coarse else f"\"{self.query}\""
        url = search_api + f"from={language_conversion(self.search_lang)}&query={query}&trans_filter=limit&trans_to={language_conversion(self.target_lang)}&page={page}"
        if force_audio:
            url += "&has_audio=yes"
        print("[Tatoeba] Querying URL: %s" % url)
        data = requests.get(url).json()
        results = data["results"]
        for result in results:
            translations = [t for t in result["translations"][0] if t["lang"] == language_conversion(self.target_lang)]  # anything else are translations of translations
            if len(translations) == 0:
                continue
            sentence = Sentence(
                id=result["id"],
                text_orig=result["text"],
                text_translation=translations[0]["text"],
                audio_orig_id=result["audios"][0]["id"] if len(result["audios"]) > 0 else None,
                transcription=unescape_ruby(result["transcriptions"][0]["html"]) if len(result["transcriptions"]) > 0 else "",
                media=self.media,
                audio_orig=None,
                author=result["user"]["username"]
            )
            self.sentences.append(sentence)

        return data["paging"]["Sentences"]

    def load_search_query(self, coarse: bool = False):
        min_audio_results = self.config.get_config_object("minSentenceAudioResults").value
        self.load_search_query_page(1, True, coarse)
        if len([s for s in self.sentences if s.audio_orig_id is not None]) >= min_audio_results:
            return self
        paging = self.load_search_query_page(1, coarse=coarse)
        count = min(paging["count"], self.config.get_config_object("maxSentenceResults").value)
        last_page = count // paging["perPage"] + 1
        for i in range(2, last_page):
            self.load_search_query_page(i, coarse=coarse)
            if len([s for s in self.sentences if s.audio_orig_id is not None]) >= min_audio_results:
                break
        self.sentences = sorted(self.sentences, key=lambda x: x.audio_orig_id is not None, reverse=True)
        # remove duplicate IDs, in O(n^infinity) time
        self.sentences = [self.sentences[i] for i in range(len(self.sentences)) if self.sentences[i].id not in [s.id for s in self.sentences[:i]]]
        return self

    @staticmethod
    def cleanup():
        """Removes any files in the /temp directory."""
        from .. import temp_dir
        for f in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, f))

