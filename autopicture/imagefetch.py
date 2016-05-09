import urllib
import urllib2
import json
import os

from aqt import mw

from updateraddon import FieldUpdater


class GoogleImageFieldUpdater(FieldUpdater):
    """Downloads an image from Google and sets a field accordingly.
    
    Queries Google Images using the contents of the query field, downloads 
    the image and sets the target field to the location of the image in the
    collection.

    """
    API_KEY = 'AIzaSyAUjcQiTtz9Jyhx54yOydyGIKH6BQgmRdQ'
    CX = '016086122471418819595:b5hlfkq50kk'
    SEARCH_URL = "https://www.googleapis.com/customsearch/v1"
    NOT_FOUND_FILENAME = 'imageNotFound.jpg'
    DIRECTORY = os.path.dirname(__file__)

    def __init__(self, query_field_name, target_field_name):
        """Initialiser.

        Args:
            query_field_name (str): the name of the query field.
            target_field_name (str): the name of the target field.

        """
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

        Attempts to download an image from google. If it can, adds the image
        to the media database and updates the field to an appropriate img tag.
        Else, returns without modifying the note.

        Args:
            note (anki.notes.Note): dictionary-like.

        Returns:
            (bool) True iff the note was modified.

        """
        query = mw.col.media.strip(note[self._query_field])
        if not query:
            return False

        image_url = self.firstImageFromGoogle(query)
        if not image_url:
            return False

        filename = self.downloadImageFromURL(image_url)
        if not filename:
            return False

        mw.col.media.addFile(os.path.abspath(unicode(filename)))
        if os.path.basename(filename) != self.NOT_FOUND_FILENAME:
            os.remove(filename)

        dst_text = u'<img src="{}" />'.format(os.path.basename(filename))
        note[self._target_field] = dst_text

        return True
    
    @classmethod
    def downloadImageFromURL(clazz, url):
        """Downloads an image from a url.

        Args:
            query (str): The search query.
            get_url (Callable[[str], str]): Takes a query and returns a url
                of a jpg image. Fail by raising.

        Returns:
            (str | None) The filename of the saved image, or None if failure.
            
        """
        result = clazz.NOT_FOUND_FILENAME
        basename = '.jpg'.join(url.split('/')[-1].split('.jpg')[:-1])
        filename = os.path.join(clazz.DIRECTORY, basename + '.jpg')
        try:
            urllib.urlretrieve(url, filename)
            result = filename
        finally:
            return result

    @classmethod
    def firstImageFromGoogle(clazz, query):
        """Fetches the url of the first image of a google search for `query`.

        Args:
            query (str): The search query.

        Returns:
            (str | None) The url of the image, or None if failure.
            
        """
        query = query + ' filetype:jpg'
        params = { 'q': query
                 , 'key': clazz.API_KEY
                 , 'cx': clazz.CX
                 , 'searchType': 'image'
                 }

        url = clazz.SEARCH_URL + '?' + urllib.urlencode(params)
        response = urllib2.urlopen(url)
        result = json.load(response)
        return result['items'][0]['link']


if __name__ == '__main__':
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

        def testQueryField(self):
            g = GoogleImageFieldUpdater(self.query_field, '')
            self.assertEqual(g.sourceFields(), [self.query_field])

        def testTargetField(self):
            g = GoogleImageFieldUpdater('', self.target_field)
            self.assertEqual(g.targetFields(), [self.target_field])

        def testBoth(self):
            g = GoogleImageFieldUpdater(self.query_field, self.target_field)
            self.assertEqual(g.sourceFields(), [self.query_field])
            self.assertEqual(g.targetFields(), [self.target_field])


    @mock.patch('__main__.mw')
    class modifyFieldsTestCase(unittest.TestCase):

        def setUp(self, *mocks):
            ## create temp file
            filename = randomstring(10) + '.jpg'
            basedir = GoogleImageFieldUpdater.DIRECTORY
            self.temp_path = os.path.join(basedir, filename)
            with open(self.temp_path, 'a'):
                pass

            ## create test object and patch methods
            self.g = GoogleImageFieldUpdater(randomstring(9), randomstring(9))
            self.g.downloadImageFromURL = mock.MagicMock()
            self.g.downloadImageFromURL.return_value = self.temp_path
            self.g.firstImageFromGoogle = mock.MagicMock()
            self.note = mock.MagicMock()

        def tearDown(self, *mocks):
            ## delete temp file if it's still there
            if os.path.isfile(self.temp_path):
                os.remove(self.temp_path)

        def testNotModifiedOnUrlFetchFailure(self, mock_mw):
            self.g.firstImageFromGoogle.return_value = None

            self.assertFalse(self.g.modifyFields(self.note))
            self.assertFalse(self.note.__setitem__.called)

        def testNotModifiedOnImageFetchFailure(self, mock_mw):
            self.g.downloadImageFromURL.return_value = None

            self.assertFalse(self.g.modifyFields(self.note))
            self.assertFalse(self.note.__setitem__.called)

        def testNotModifiedOnBlankQuery(self, mock_mw):
            mock_mw.col.media.strip.return_value = ''

            self.assertFalse(self.g.modifyFields(self.note))
            self.assertFalse(self.note.__setitem__.called)

        def testModifiedCorrectly(self, mock_mw):
            self.assertTrue(self.g.modifyFields(self.note))

            target = self.g.targetFields()[0]
            filename = os.path.basename(self.temp_path)
            image_tag = u'<img src="{}" />'.format(filename)
            self.assertTrue(self.note.__setitem__.called_once_with \
                            (target, image_tag))

        def testAddToMediaDatabase(self, mock_mw):
            self.assertTrue(self.g.modifyFields(self.note))
            self.assertTrue(mw.col.media.addFile.called)

        def testTempFileRemoved(self, mock_mw):
            self.g.modifyFields(self.note)
            self.assertFalse(os.path.isfile(self.temp_path))


    @mock.patch('urllib.urlretrieve')
    class DownloadImageFromURLTestCase(unittest.TestCase):

        def testFileName(self, mock_retrieve):
            website = 'http://' + randomstring(10) + '.com/'
            remote_image = randomstring(10) + '.jpg'
            url = website + remote_image

            filename = GoogleImageFieldUpdater.downloadImageFromURL(url)

            basedir = GoogleImageFieldUpdater.DIRECTORY
            self.assertEqual(filename, os.path.join(basedir, remote_image))
            

    unittest.main()
