#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""Unit tests for audiofetch.py"""
import unittest
import mock

import os
import random
import string

from . import audiofetch
from .audiofetch import VoiceRSSFieldUpdater


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


@mock.patch('{}.audiofetch.mw'.format(__name__))
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
        self.assertTrue(mock_mw.col.media.addFile.called)

    def testTempFileRemoved(self, mock_mw):
        mock_mw.col.media.strip.return_value = self.query
        self.g.modifyFields(self.note)
        self.assertFalse(os.path.isfile(self.temp_path))


class buildUrlTestCase(unittest.TestCase):

    def setUp(self):
        self.g = VoiceRSSFieldUpdater('src', 'tgt', 'english')

    def testNoExceptions(self):
        self.g.buildUrl('horse')

    def testUnicode(self):
        self.g.buildUrl(unicode('うにこで', 'utf-8'))

