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
                 , 'src': query
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



import unittest
import mock

import random
import string


def randomstring(n):
    """Generates a string of n random lower case letters."""
    rand_chr = lambda: random.SystemRandom().choice(string.ascii_lowercase)
    return ''.join(rand_chr() for _ in range(30))


class InitialiseTestCase(unittest.TestCase):

    def setUp(self):
        self.query_field = randomstring(30)
        self.target_field = randomstring(30)
        self.valid_language = 'english'
        self.invalid_language = 'invalid language'

    def testQueryField(self):
        g = VoiceRSSFieldUpdater(self.query_field, '',
                                 self.valid_language)
        self.assertEqual(g.sourceFields(), [self.query_field])

    def testTargetField(self):
        g = VoiceRSSFieldUpdater('', self.target_field,
                                 self.valid_language)
        self.assertEqual(g.targetFields(), [self.target_field])

    def testBoth(self):
        g = VoiceRSSFieldUpdater(self.query_field, self.target_field,
                                 self.valid_language)
        self.assertEqual(g.sourceFields(), [self.query_field])
        self.assertEqual(g.targetFields(), [self.target_field])

    def testInvalidLanguage(self):
        try:
            g = VoiceRSSFieldUpdater(self.query_field, self.target_field,
                                     self.invalid_language)
        except ValueError:
            pass
        else:
            assertTrue(False, "initializer should raise")

    def testValidLanguage(self):
        try:
            g = VoiceRSSFieldUpdater(self.query_field, self.target_field,
                                     self.valid_language)
        except ValueError:
            assertTrue(False, "initializer should not raise")


@mock.patch('{}.mw'.format(__name__))
class modifyFieldsTestCase(unittest.TestCase):

    def setUp(self):
        ## create temp file
        self.query = randomstring(10)
        filename = self.query + '.mp3'
        basedir = VoiceRSSFieldUpdater.DIRECTORY
        self.temp_path = os.path.join(basedir, filename)
        with open(self.temp_path, 'a'):
            pass

        ## create test object and patch methods
        self.g = VoiceRSSFieldUpdater(randomstring(9), randomstring(9),
                                      'english')
        self.g.downloadFromURL = mock.MagicMock()
        self.g.build_url = mock.MagicMock()
        self.note = mock.MagicMock()

    def tearDown(self):
        ## delete temp file if it's still there
        if os.path.isfile(self.temp_path):
            os.remove(self.temp_path)

    def testNotModifiedOnBlankQuery(self, mock_mw):
        mock_mw.col.media.strip.return_value = ''

        self.assertFalse(self.g.modifyFields(self.note))
        self.assertFalse(self.note.__setitem__.called)

    def testModifiedCorrectly(self, mock_mw):
        mock_mw.col.media.strip.return_value = self.query
        self.assertTrue(self.g.modifyFields(self.note))

        target = self.g.targetFields()[0]
        filename = os.path.basename(self.temp_path)
        image_tag = u'[sound:{}]'.format(filename)
        self.assertTrue(self.note.__setitem__.called_once_with \
                        (target, image_tag))

    def testAddToMediaDatabase(self, mock_mw):
        mock_mw.col.media.strip.return_value = self.query
        self.assertTrue(self.g.modifyFields(self.note))
        self.assertTrue(mw.col.media.addFile.called)

    def testTempFileRemoved(self, mock_mw):
        mock_mw.col.media.strip.return_value = self.query
        self.g.modifyFields(self.note)
        self.assertFalse(os.path.isfile(self.temp_path))


class buildUrlTestCase(unittest.TestCase):

    def setUp(self):
        self.g = VoiceRSSFieldUpdater('src', 'tgt', 'english')

    def testNoExceptions(self):
        pass

