#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import urllib
import json
import os
import random
import unicodedata

from aqt import mw
from aqt.utils import showInfo, getText

from .config import CONFIG_FILE, ConfigParser
from .cognitive_services import get_jwt, bing_tts, HTTPError, MALE, FEMALE
from .updateraddon import Addon, AnySourceFieldUpdater

DIRECTORY = os.path.dirname(__file__)
LANGUAGES = { "catalan": "ca-ES"
            , "chinese": "zh-CN"
            , "chinese (china)": "zh-CN"
            , "chinese (hong kong)": "zh-HK"
            , "chinese (taiwan)": "zh-TW"
            , "danish": "da-DK"
            , "dutch": "nl-NL"
            , "english": "en-GB"
            , "english (australia)": "en-AU"
            , "english (canada)": "en-CA"
            , "english (great britain)": "en-GB"
            , "english (india)": "en-IN"
            , "english (united states)": "en-US"
            , "finnish": "fi-FI"
            , "french": "fr-FR"
            , "french (canada)": "fr-CA"
            , "french (france)": "fr-FR"
            , "german": "de-DE"
            , "italian": "it-IT"
            , "japanese": "ja-JP"
            , "korean": "ko-KR"
            , "norwegian": "nb-NO"
            , "polish": "pl-PL"
            , "portuguese": "pt-PT"
            , "portuguese (brazil)": "pt-BR"
            , "portuguese (portugal)": "pt-PT"
            , "russian": "ru-RU"
            , "spanish": "es-ES"
            , "spanish (mexico)": "es-MX"
            , "spanish (spain)": "es-ES"
            , "swedish (sweden)": "sv-SE"
            }

class VoiceRSSFieldUpdater(AnySourceFieldUpdater):
    """Downloads TTS from VoiceRSS and sets a field accordingly.
    
    Queries VoiceRSS using the contents of the query field and language set
    at initialisation, downloads the file and sets the target field to the 
    location of the file in the collection.

    """
    API_KEY = "afa8bec3c1de4c59962949da0f995bc6"
    URL = "https://api.voicerss.org/"
    FORMAT = "48khz_16bit_mono"
    RATE = "-3"  # rate of speech, from -10 to 10. 10 is inaudably fast.

    DIRECTORY = os.path.dirname(__file__)

    def __init__(self, query_field_names, target_field_name, language):
        """Initialiser.

        Args:
            query_field_name (str): the name of the query field.
            target_field_name (str): the name of the target field.
            langauge (str): Either the English name of a language, e.g.
                "English", "Japanese", "Portuguese", "French (France)"
                or a language code, e.g. "en-gb", "ja-jp"

        Raises:
            ValueError if the language is not supported.
        """
        AnySourceFieldUpdater.__init__(self, query_field_names, target_field_name)

        language = language.lower()
        if language in LANGUAGES:
            self._language_code = LANGUAGES[language]
        elif language in LANGUAGES.values():
            self._language_code = language
        else:
            raise ValueError('Not a valid language.')

    def modifyFields(self, note):
        """Modifies the fields of note.

        *NB: FieldUpdater promises to only call modifyFields if 
        self.sourceFields and self.targetFields exist in note.*

        Downloads TTS from the VoiceRSS api, adds it to the media database and
        updates the target field appropriately. Doesn't modify the note if the
        all source fields are blank. Otherwise, uses the first non-blank
        source field in `self._query_fields`.

        Args:
            note (anki.notes.Note): dictionary-like.

        Returns:
            (bool) True iff the note was modified.

        """
        for f in filter(lambda f: f in note, self.sourceFields()):
            query = mw.col.media.strip(note[f])
            if query:
                break

        if not query:
            return False

        if self._language_code == 'ja-jp':
            # switch placeholder on queries
            assert isinstance(query, unicode)
            placeholder = "KATAKANA-HIRAGANA PROLONGED SOUND MARK"
            kana = ["HIRAGANA", "KATAKANA"]
            replacement = u"、"
            for i, char in enumerate(query):
                if (unicodedata.name(char) == placeholder
                    and (i == 0 or
                         unicodedata.name(query[i-1])[:8] not in kana)):
                    query = query[:i] + replacement + query[i + 1:]
            query = query.replace(u"～", replacement)

        voice_url = self.buildUrl(query)
        filepath = os.path.join(self.DIRECTORY, query + '.mp3')
        tries = 3
        while tries > 0:
            self.downloadFromURL(voice_url, filepath)
            try:
                assert os.path.getsize(filepath) > 512
                break
            except (AssertionError, os.error):
                tries -= 1
        if tries == 0:
            showInfo("Failed to download audio for query {}.".format(query))
            if os.path.isfile(filepath):
                os.remove(filepath)
            return False

        mw.col.media.addFile(os.path.abspath(unicode(filepath)))
        if os.path.isfile(filepath):
            os.remove(filepath)

        dst_text = u'[sound:{}]'.format(os.path.basename(filepath))
        note[self.targetFields()[0]] = dst_text

        return True

    def buildUrl(self, query):
        """Fetches the url of an mp3 reading of `query`.

        Args:
            query (str): The search query.

        Returns:
            (str): The url of an mp3 reading of query.
            
        """
        params = { 'key': self.API_KEY
                 , 'src': query.encode('utf-8')
                 , 'hl': self._language_code
                 , 'f': self.FORMAT
                 , 'r': self.RATE
                 }

        return self.URL + '?' + urllib.urlencode(params)
    
    @classmethod
    def downloadFromURL(clazz, url, filepath):
        """Downloads an image from a url.

        Args:
            query (str): The search query.
            filepath (str): The path of the destination file.
            
        """
        urllib.urlretrieve(url, filepath)

class BingTTSFieldUpdater(AnySourceFieldUpdater):
    def __init__(self, query_field_names, target_field_name, language):
        """Initialiser.

        Args:
            query_field_name (str): the name of the query field.
            target_field_name (str): the name of the target field.
            langauge (str): Either the English name of a language, e.g.
                "English", "Japanese", "Portuguese", "French (France)"
                or a language code, e.g. "en-gb", "ja-jp"

        Raises:
            ValueError if the language is not supported.
        """
        AnySourceFieldUpdater.__init__(self, query_field_names, target_field_name)

        language = language.lower()
        if language in LANGUAGES:
            self._language_code = LANGUAGES[language]
        elif language in LANGUAGES.values():
            self._language_code = language
        else:
            raise ValueError('Not a valid language.')

        self._jwt = None

        parser = ConfigParser()
        section = 'cognitive services'
        option = 'bing speech api key'
        if parser.read(CONFIG_FILE) and parser.has_option(section, option):
            self.api_key = parser.get(section, option)
        else:
            prompt = 'Please input API key for the Bing Speech API.'
            self.api_key = getText(prompt)[0].encode('utf-8')
            if not parser.has_section(section):
                parser.add_section(section)
            parser.set(section, option, self.api_key)
            with open(CONFIG_FILE, 'w') as f:
                parser.write(f)

    def modifyFields(self, note):
        """Modifies the fields of note.

        Downloads TTS from the Bing Speech api, adds it to the media 
        database and updates the target field appropriately. Doesn't 
        modify the note if the all source fields are blank. Otherwise, 
        uses the first non-blank source field in `self._query_fields`.

        Args:
            note (anki.notes.Note): dictionary-like.

        Returns:
            (bool) True iff the note was modified.

        """
        for f in filter(lambda f: f in note, self.sourceFields()):
            query = mw.col.media.strip(note[f])
            if query:
                break

        if not query:
            return False

        gender = MALE if random.randrange(0, 2) else FEMALE
        filepath = self.get_file(gender, query)
        mw.col.media.addFile(os.path.abspath(unicode(filepath)))

        dst_text = u'[sound:{}]'.format(os.path.basename(filepath))
        note[self.targetFields()[0]] = dst_text

        if os.path.isfile(filepath):
            os.remove(filepath)

        return True

    def get_file(self, gender, text):
        if not self._jwt:
            self._jwt = get_jwt(self.api_key)

        try:
            return bing_tts(self._jwt, self._language_code, gender, text)
        except HTTPError as e:
            if e.code in (403, 401):
                self._jwt = get_jwt(self.api_key)
                return bing_tts(self._jwt, self._language_code, gender, text)

def initialise(name='autovoice', language='english', 
        source_fields=['voice_src'], target_field='voice',
        model_name_substring=None):
    field_updater = BingTTSFieldUpdater(source_fields, target_field, language)
    Addon(field_updater, name, model_name_substring=model_name_substring)
