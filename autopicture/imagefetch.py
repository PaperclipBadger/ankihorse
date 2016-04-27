#TODO: actually set up a dev environment for Anki and write proper unit tests.
import urllib
import urllib2
import json
import os
import shutil

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
        """Return a container of names of target fields.

        Target fields are required to exist in the model for modifyFields to
        be called.

        Args:
            note (anki.notes.Note): dictionary-like.

        Returns:
            (bool) True iff the note was modified.

        """
        query = mw.col.media.strip(note[self._query_field])
        if query != '':
            get_url = self.firstImageFromGoogle
            filename = self.downloadImageFromQuery(query, get_url)

            mw.col.media.addFile(os.path.abspath(unicode(filename)))
            if os.path.basename(filename) != self.NOT_FOUND_FILENAME:
                os.remove(filename)

            dst_text = u'<img src="{}" />'.format(os.path.basename(filename))
            note[self._target_field] = dst_text
            return True
        else:
            return False
    
    @classmethod
    def downloadImageFromQuery(clazz, query, get_url):
        """Downloads an image based on a query.

        Args:
            query (str): The search query.
            get_url (Callable[[str], str]): Takes a query and returns a url
                of a jpg image. Fail by raising.

        Returns:
            (str | None) The filename of the saved image, or None if failure.
            
        """
        result = clazz.NOT_FOUND_FILENAME
        filename = os.path.join(clazz.DIRECTORY, query + '.jpg')
        try:
            image_url = get_url(query)
            urllib.urlretrieve(image_url, filename)
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
