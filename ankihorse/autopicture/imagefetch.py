#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import urllib
import urllib2
import json
import os

from aqt import mw
from aqt.utils import showInfo

from ..updateraddon import FieldUpdater


class GoogleImageFieldUpdater(FieldUpdater):
    """Downloads an image from Google and sets a field accordingly.
    
    Queries Google Images using the contents of the query field, downloads 
    the image and sets the target field to the location of the image in the
    collection.

    """
    API_KEY = 'AIzaSyAUjcQiTtz9Jyhx54yOydyGIKH6BQgmRdQ'
    CX = '016086122471418819595:b5hlfkq50kk'
    SEARCH_URL = "https://www.googleapis.com/customsearch/v1"
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
            note[self._target_field] = "Image not found."
            return False

        mw.col.media.addFile(os.path.abspath(unicode(filename)))
        os.remove(filename)

        dst_text = u'<img src="{}" />'.format(os.path.basename(filename))
        note[self._target_field] = dst_text

        return True
    
    @classmethod
    def downloadImageFromURL(clazz, url):
        """Downloads an image from a url.

        Args:
            query (str): The search query.
            url (str): Takes a query and returns a url of a jpg image.

        Returns:
            (str) The filename of the saved image, NOT_FOUND_FILENAME on fail.
            
        """
        result = None
        name = url.split('/')[-1]
        filename = os.path.join(clazz.DIRECTORY, name)
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
        params = { 'q': query
                 , 'key': clazz.API_KEY
                 , 'cx': clazz.CX
                 , 'searchType': 'image'
                 }

        url = clazz.SEARCH_URL + '?' + urllib.urlencode(params)
        try:
            response = urllib2.urlopen(url)
        except urllib2.HTTPError as e:
            if e.code == 403:
                showInfo("403 Forbidden. You're probably out of google \
requests. Try again tomorrow.")
                return None
            else:
                raise
        result = json.load(response)
        return result['items'][0]['link']
