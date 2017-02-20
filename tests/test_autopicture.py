#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""Unit tests for autopicture.py"""
import os
import random
import string
import urllib

import pytest
import mock

from ankihorse import autopicture
from ankihorse.autopicture import GoogleImageFieldUpdater


@pytest.fixture
def patches(monkeypatch):
    patches = {}
    for name in ('mw', 'showInfo'):
        patches[name] = mock.MagicMock()
        monkeypatch.setattr(autopicture, name, patches[name])
    return patches

@pytest.fixture
def source_field(): return randomstring(9)

@pytest.fixture
def target_field(): return randomstring(9)

@pytest.fixture
def filename(): return randomstring(10)

@pytest.fixture
def patched_field_updater(monkeypatch, patches, tmpdir, filename,
        source_field, target_field):
    field_updater = GoogleImageFieldUpdater([source_field], [target_field])
    for name in ('downloadImageFromURL', 'firstImageFromGoogle'):
        monkeypatch.setattr(field_updater, name, mock.MagicMock())
    
    monkeypatch.setattr(field_updater, 'DIRECTORY', str(tmpdir))
    temp_path = tmpdir.join(filename)
    temp_path.ensure(file=True)
    field_updater.downloadImageFromURL.return_value = str(temp_path)

    return field_updater

@pytest.fixture
def note(source_field, target_field):
    note = mock.MagicMock()
    note.__contains__ = lambda _, f: f in {source_field, target_field}
    return note

def randomstring(n):
    """Generates a string of n random lower case letters."""
    rand_chr = lambda: random.SystemRandom().choice(string.ascii_lowercase)
    return ''.join(rand_chr() for _ in range(30))


def test_url_fetch_failure(patched_field_updater, note):
    patched_field_updater.firstImageFromGoogle.return_value = None

    assert not patched_field_updater.modifyFields(note)
    assert not note.__setitem__.called

def test_image_fetch_failure(patched_field_updater, note):
    patched_field_updater.downloadImageFromURL.return_value = None

    assert not patched_field_updater.modifyFields(note)
    assert not note.__setitem__.called

def test_blank_query(patches, patched_field_updater, note):
    patches['mw'].col.media.strip.return_value = ''

    assert not patched_field_updater.modifyFields(note)
    assert not note.__setitem__.called

def test_modified_correctly(patched_field_updater, note, 
        target_field, filename):
    assert patched_field_updater.modifyFields(note)

    image_tag = u'<img src="{}" />'.format(filename)
    assert note.__setitem__.called_once_with(target_field, image_tag)

def test_add_to_media_database(patches, patched_field_updater, note):
    assert patched_field_updater.modifyFields(note)
    assert patches['mw'].col.media.addFile.called

def test_temp_file_removed(patched_field_updater, tmpdir, filename, note):
    patched_field_updater.modifyFields(note)
    assert not tmpdir.join(filename).check()

def test_download(monkeypatch, tmpdir):
    mock_retrieve = mock.MagicMock()
    monkeypatch.setattr(urllib, 'urlretrieve', mock_retrieve)
    monkeypatch.setattr(GoogleImageFieldUpdater, 'DIRECTORY', str(tmpdir))

    website = 'http://' + randomstring(10) + '.com/'
    remote_image = randomstring(10) + '.jpg'
    url = website + remote_image
    
    filename = GoogleImageFieldUpdater.downloadImageFromURL(url)
    
    assert filename == str(tmpdir.join(remote_image))
