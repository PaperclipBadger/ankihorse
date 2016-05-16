#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import urllib
import os

from aqt import mw

from ..updateraddon import FieldUpdater


class VoiceRSSFieldUpdater(FieldUpdater):
    """Downloads TTS from VoiceRSS and sets a field accordingly.
    
    Queries VoiceRSS using the contents of the query field and language set
    at initialisation, downloads the file and sets the target field to the 
    location of the file in the collection.

    """
    LANGUAGES = { "catalan": "ca-es"
                , "chinese": "zh-cn"
                , "chinese (china)": "zh-cn"
                , "chinese (hong kong)": "zh-hk"
                , "chinese (taiwan)": "zh-tw"
                , "danish": "da-dk"
                , "dutch": "nl-nl"
                , "english": "en-gb"
                , "english (australia)": "en-au"
                , "english (canada)": "en-ca"
                , "english (great britain)": "en-gb"
                , "english (india)": "en-in"
                , "english (united states)": "en-us"
                , "finnish": "fi-fi"
                , "french": "fr-fr"
                , "french (canada)": "fr-ca"
                , "french (france)": "fr-fr"
                , "german": "de-de"
                , "italian": "it-it"
                , "japanese": "ja-jp"
                , "korean": "ko-kr"
                , "norwegian": "nb-no"
                , "polish": "pl-pl"
                , "portuguese": "pt-pt"
                , "portuguese (brazil)": "pt-br"
                , "portuguese (portugal)": "pt-pt"
                , "russian": "ru-ru"
                , "spanish": "es-es"
                , "spanish (mexico)": "es-mx"
                , "spanish (spain)": "es-es"
                , "swedish (sweden)": "sv-se"
                }
    
    API_KEY = "afa8bec3c1de4c59962949da0f995bc6"
    URL = "https://api.voicerss.org/"
    FORMAT = "48khz_16bit_mono"
    RATE = "-3"  # rate of speech, from -10 to 10. 10 is inaudably fast.

    DIRECTORY = os.path.dirname(__file__)

    def __init__(self, query_field_name, target_field_name, language):
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
        language = language.lower()
        if language in self.LANGUAGES:
            self._language_code = self.LANGUAGES[language]
        elif language in self.LANGUAGES.values():
            self._language_code = language
        else:
            raise ValueError('Not a valid language.')

        self._query_field = query_field_name
        self._target_field = target_field_name

    def sourceFields(self):
        """Return a container of names of source fields.

        The modifyFields method is called when a field in the editor loses
        focus and it's name is in self.sourceFields(). The modifyFields
        method will not be called unless the note has all the source fields.

        """
        return [self._query_field]

    def targetFields(self):
        """Return a container of names of target fields.

        Target fields are required to exist in the model for modifyFields to
        be called.

        """
        return [self._target_field]

    def modifyFields(self, note):
        """Modifies the fields of note.

        *NB: FieldUpdater promises to only call modifyFields if 
        self.sourceFields and self.targetFields exist in note.*

        Downloads TTS from the VoiceRSS api, adds it to the media database and
        updates the target field appropriately. Doesn't modify the note if the
        source field was blank.

        Args:
            note (anki.notes.Note): dictionary-like.

        Returns:
            (bool) True iff the note was modified.

        """
        query = mw.col.media.strip(note[self._query_field])
        if not query:
            return False

        voice_url = self.buildUrl(query)
        filepath = os.path.join(self.DIRECTORY, query + '.mp3')
        self.downloadFromURL(voice_url, filepath)
        mw.col.media.addFile(os.path.abspath(unicode(filepath)))
        if os.path.isfile(filepath):
            os.remove(filepath)

        dst_text = u'[sound:{}]'.format(os.path.basename(filepath))
        note[self._target_field] = dst_text

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



