#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""Unit tests for imagefetch.py"""
import unittest
import mock

import os
import random
import string

from . import imagefetch 
from .imagefetch import GoogleImageFieldUpdater


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


@mock.patch('{}.imagefetch.mw'.format(__name__))
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
        self.assertTrue(mock_mw.col.media.addFile.called)

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
