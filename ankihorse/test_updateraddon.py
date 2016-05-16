#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""Unit tests for updateraddon.py"""
import unittest
import mock

from . import updateraddon
from .updateraddon import FieldUpdater, Addon

class TestFieldUpdater(FieldUpdater):
    """Field updater for testing purposes."""

    def __init__(self):
        self.modify_return_value = False

    @staticmethod
    def validModel():
        return { 'name': 'testName' 
               , 'flds': [ { 'name': 'src1' }
                         , { 'name': 'src2' }
                         , { 'name': 'tgt1' } 
                         , { 'name': 'tgt2' }
                         ]
               }
    
    def sourceFields(self):
        return ['src1', 'src2']

    def targetFields(self):
        return ['tgt1', 'tgt2']

    def modifyFields(self, note):
        return self.modify_return_value


def fieldNames(model):
    """To be substituted for mw.col.models.fieldNames"""
    return [ f['name'] for f in model['flds'] ]


@mock.patch('{}.updateraddon.SIGNAL'.format(__name__))
@mock.patch('{}.updateraddon.QAction'.format(__name__))
@mock.patch('{}.updateraddon.addHook'.format(__name__))
@mock.patch('{}.updateraddon.mw'.format(__name__))
class InitialiseTestCase(unittest.TestCase):
    
    def testAddHook(self, mock_mw, mock_addHook, *unused):
        a = Addon(TestFieldUpdater(), 'test')
        mock_addHook.assert_called_once_with\
                ('editFocusLost', a.onFocusLost)

    def testAddMenuItem(self, mock_mw, *args):
        a = Addon(TestFieldUpdater(), 'test')
        self.assertTrue(mock_mw.connect.called)
        self.assertTrue(mock_mw.form.menuTools.addAction.called)


@mock.patch('{}.updateraddon.SIGNAL'.format(__name__))
@mock.patch('{}.updateraddon.QAction'.format(__name__))
@mock.patch('{}.updateraddon.addHook'.format(__name__))
@mock.patch('{}.updateraddon.mw'.format(__name__))
class ShouldModifyTestCase(unittest.TestCase):


    def testHasJustSourceFields(self, mock_mw, *unused):
        mock_mw.col.models.fieldNames = fieldNames
        model = { 'name': 'testName'
                , 'flds': [ { 'name': 'src1' }
                          , { 'name': 'src2' }
                          ]
                }
        
        a = Addon(TestFieldUpdater(), 'test')
        self.assertFalse(a.shouldModify(model))
        
    def testHasJustTargetFields(self, mock_mw, *unused):
        mock_mw.col.models.fieldNames = fieldNames
        model = { 'name': 'testName'
                , 'flds': [ { 'name': 'tgt1' }
                          , { 'name': 'tgt2' }
                          ]
                }

        a = Addon(TestFieldUpdater(), 'test')
        self.assertFalse(a.shouldModify(model))

    def testHasRequiredFields(self, mock_mw, *unused):
        mock_mw.col.models.fieldNames = fieldNames
        model = TestFieldUpdater.validModel()

        a = Addon(TestFieldUpdater(), 'test')
        self.assertTrue(a.shouldModify(model))

    def testNameContainsSubstring(self, mock_mw, *unused):
        mock_mw.col.models.fieldNames = fieldNames
        model = TestFieldUpdater.validModel()

        a = Addon(TestFieldUpdater(), 'test', 'test')
        self.assertTrue(a.shouldModify(model))

    def testDoesNotHaveSourceFields(self, mock_mw, *unused):
        mock_mw.col.models.fieldNames = fieldNames
        model = TestFieldUpdater.validModel()

        a = Addon(TestFieldUpdater(), 'test', 'horse')
        self.assertFalse(a.shouldModify(model))


@mock.patch('{}.updateraddon.mw'.format(__name__))
class ModifyFieldsTestCase(unittest.TestCase):

    @mock.patch('{}.updateraddon.SIGNAL'.format(__name__))
    @mock.patch('{}.updateraddon.QAction'.format(__name__))
    @mock.patch('{}.updateraddon.addHook'.format(__name__))
    @mock.patch('{}.updateraddon.mw'.format(__name__))
    def setUp(self, *mocks):
        self.updater = TestFieldUpdater()
        self.addon = Addon(self.updater, 'test')
    
    def testInvalidModel(self, mock_mw):
        mock_mw.col.models.fieldNames = fieldNames
        note = mock.Mock()
        note.model.return_value = { 'name': 'testName' , 'flds': [ ] }

        self.updater.modify_return_value = True
        self.assertFalse(self.addon.modifyFields(note))
        self.assertEqual(note.mock_calls, [mock.call.model()])
        
    def testValidModel(self, mock_mw):
        mock_mw.col.models.fieldNames = fieldNames
        note = mock.Mock()
        note.model.return_value = TestFieldUpdater.validModel()

        self.updater.modify_return_value = True
        self.assertTrue(self.addon.modifyFields(note))
        self.updater.modify_return_value = False
        self.assertFalse(self.addon.modifyFields(note))


class OnFocusLostTestCase(unittest.TestCase):

    @mock.patch('{}.updateraddon.SIGNAL'.format(__name__))
    @mock.patch('{}.updateraddon.QAction'.format(__name__))
    @mock.patch('{}.updateraddon.addHook'.format(__name__))
    @mock.patch('{}.updateraddon.mw'.format(__name__))
    def setUp(self, *mocks):
        self.addon = Addon(TestFieldUpdater(), 'test')
        self.addon.modifyFields = mock.Mock()
    
    def testNonSourceField(self):
        note = mock.Mock()
        note.model.return_value = TestFieldUpdater.validModel()
        self.addon.modifyFields.return_value = False

        self.assertTrue(self.addon.onFocusLost(True, note, 2))
        self.assertFalse(self.addon.onFocusLost(False, note, 2))
        
    def testSourceField(self):
        note = mock.Mock()
        note.model.return_value = TestFieldUpdater.validModel()

        self.addon.modifyFields.return_value = True
        self.assertTrue(self.addon.onFocusLost(False, note, 0))
        self.addon.modifyFields.return_value = False
        self.assertFalse(self.addon.onFocusLost(False, note, 0))
        

#TODO: tests for regenerateAll
