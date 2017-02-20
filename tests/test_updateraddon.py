#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""Unit tests for updateraddon.py"""
from ankihorse import updateraddon
from ankihorse.updateraddon import FieldUpdater, Addon
import pytest
import mock


class MockFieldUpdater(FieldUpdater):
    """Field updater for testing purposes."""
    def __init__(self, source_fields, target_fields):
        self.modify_return_value = False
        self._source_fields = source_fields
        self._target_fields = target_fields

    def sourceFields(self):
        return self._source_fields

    def targetFields(self):
        return self._target_fields

    def modifyFields(self, note):
        return self.modify_return_value

@pytest.fixture(params=[(('src1', 'src2'), ('tgt1', 'tgt2'))])
def field_updater(request):
    return MockFieldUpdater(*request.param)

@pytest.fixture(params=['horse', 'test'])
def model_name(request):
    return request.param

@pytest.fixture
def valid_model(field_updater, model_name):
    fields = field_updater.sourceFields() + field_updater.targetFields()
    return { 'name': model_name
           , 'flds': [ { 'name': field } for field in fields ]
           }

@pytest.fixture
def patches(monkeypatch):
    patches = {}
    for name in ('SIGNAL', 'QAction', 'addHook', 'mw'):
        patches[name] = mock.MagicMock()
        monkeypatch.setattr(updateraddon, name, patches[name])

    def fieldNames(model): return [ f['name'] for f in model['flds'] ]
    patches['mw'].col.models.fieldNames = fieldNames
    return patches

@pytest.fixture
def addon(patches, field_updater):
    return Addon(field_updater, 'test')

@pytest.fixture
def good_substring_addon(patches, field_updater, model_name):
    return Addon(field_updater, 'test', model_name_substring=model_name[3:])

@pytest.fixture
def bad_substring_addon(patches, field_updater):
    return Addon(field_updater, 'test', model_name_substring='__ASDF')

#def test_addHook(patches, addon):
#    patches['addHook'].assert_called_once_with(
#            'editFocusLost', addon.onFocusLost)

def test_add_menu_item(patches, addon):
    assert patches['mw'].connect.called
    assert patches['mw'].form.menuTools.addAction.called

def test_has_just_source_fields(field_updater, addon):
    model = { 'name': 'testName'
            , 'flds': [ { 'name': f } for f in field_updater.sourceFields() ]
            }
    
    assert not addon.shouldModify(model)
        
def test_has_just_target_fields(field_updater, addon):
    model = { 'name': 'testName'
            , 'flds': [ { 'name': f } for f in field_updater.targetFields() ]
            }
    
    assert not addon.shouldModify(model)

def test_has_required_fields(addon, valid_model):
    assert addon.shouldModify(valid_model)

def test_contains_substring(field_updater, valid_model, good_substring_addon):
    assert good_substring_addon.shouldModify(valid_model)

def test_not_contains_substring(field_updater, valid_model, bad_substring_addon):
    assert not bad_substring_addon.shouldModify(valid_model)

@pytest.fixture
def good_note(valid_model):
    note = mock.Mock()
    note.model.return_value = valid_model
    return note

@pytest.fixture
def bad_note():
    note = mock.Mock()
    note.model.return_value = { 'name': 'testName' , 'flds': [ ] }
    return note

def test_invalid_model(field_updater, addon, bad_note):
    field_updater.modify_return_value = True
    assert not addon.modifyFields(bad_note)
    assert bad_note.mock_calls == [mock.call.model()]
        
def test_valid_model(field_updater, addon, good_note):
    field_updater.modify_return_value = True
    assert addon.modifyFields(good_note)
    field_updater.modify_return_value = False
    assert not addon.modifyFields(good_note)

#class OnFocusLostTestCase(unittest.TestCase):
#
#    @mock.patch('{}.updateraddon.SIGNAL'.format(__name__))
#    @mock.patch('{}.updateraddon.QAction'.format(__name__))
#    @mock.patch('{}.updateraddon.addHook'.format(__name__))
#    @mock.patch('{}.updateraddon.mw'.format(__name__))
#    def setUp(self, *mocks):
#        self.addon = Addon(TestFieldUpdater(), 'test')
#        self.addon.modifyFields = mock.Mock()
#    
#    def testNonSourceField(self):
#        note = mock.Mock()
#        note.model.return_value = TestFieldUpdater.validModel()
#        self.addon.modifyFields.return_value = False
#
#        self.assertTrue(self.addon.onFocusLost(True, note, 2))
#        self.assertFalse(self.addon.onFocusLost(False, note, 2))
#        
#    def testSourceField(self):
#        note = mock.Mock()
#        note.model.return_value = TestFieldUpdater.validModel()
#
#        self.addon.modifyFields.return_value = True
#        self.assertTrue(self.addon.onFocusLost(False, note, 0))
#        self.addon.modifyFields.return_value = False
#        self.assertFalse(self.addon.onFocusLost(False, note, 0))
        

#TODO: tests for regenerateAll
