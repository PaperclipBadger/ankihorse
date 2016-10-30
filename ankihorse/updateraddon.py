#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
updateraddon
============

Framework for addons that update some fields based on others.

For Anki sources, see [https://github.com/dae/anki]

"""
from __future__ import print_function
import abc
from functools import wraps, partial
import os

from anki.hooks import addHook, wrap
from aqt import mw
from aqt.editor import Editor
from aqt.utils import shortcut, showInfo, askUser
from aqt.qt import *


class FieldUpdater():
    """Updates some note fields based on the content of others."""
    __metaclass__ = abc.ABCMeta

    def requiredFields(self):
        return set(self.sourceFields()) | set(self.targetFields())

    def sourceFields(self):
        """Return a container of names of source fields.

        The modifyFields method is called when a field in the editor loses
        focus and it's name is in self.sourceFields(). The modifyFields
        method will not be called unless the note has all the source fields.

        """
        NotImplemented

    def targetFields(self):
        """Return a container of names of target fields.

        Target fields are required to exist in the model for modifyFields to
        be called.

        """
        NotImplemented

    def shouldModify(self, model):
        """Tests whether a model should be modified.

        First checks whether the model name contains a substring if one was
        specified during initialization, then whether the model has the
        required fields.

        Args:
            model (anki.models.Model): the model to check membership of.

        Returns:
            (bool) True iff the model should be modified.
            
        """
        fields = mw.col.models.fieldNames(model)
        return all(f in fields for f in self.requiredFields())

    @abc.abstractmethod
    def modifyFields(self, note):
        """Return a container of names of target fields.

        Target fields are required to exist in the model for modifyFields to
        be called.

        Args:
            note (anki.notes.Note): dictionary-like.

        Returns:
            (bool) True iff the note was modified.

        """
        pass


class Addon():
    """An addon that updates note fields based on the content of others."""

    def __init__(self, field_updater, addon_name, model_name_substring=None):
        """Initialises the addon.

        Adds a hook to 'editFocusLost' and adds a (re)generate all button to
        the Tools menu.

        Args:
            field_updater (FieldUpdater): a strategy for updating fields.
            addon_name (str): the name of the addon.
            model_name_substring (str): if not None, only models that have
                this string in their name will be modifi

        """
        # state 
        self._field_updater = field_updater
        self._model_name_substring = model_name_substring
        self.name = addon_name

        # add hook
        global button_action
        button_action.register_callback(self.modifyFields, addon_name)
        #addHook('editFocusLost', self.onFocusLost)

        # add menu item
        global menu_action
        menu_action.register_callback(self.regenerateAll, addon_name)
        menu_item = "{} addon: regenerate all fields".format(addon_name)
        action = QAction(menu_item, mw)
        mw.connect(action, SIGNAL("triggered()"), self.regenerateAll)
        mw.form.menuTools.addAction(action)


    def shouldModify(self, model):
        """Tests whether a model should be modified.

        Checks the name of the model, then delegates to the FieldUpdater.

        Args:
            model (anki.models.Model): the model to check membership of.

        Returns:
            (bool) True iff the model should be modified.
            
        """
        name_check = True
        if self._model_name_substring != None:
            model_name = model['name'].lower()
            name_check = self._model_name_substring in model_name
        return name_check and self._field_updater.shouldModify(model)

    def modifyFields(self, note):
        """Modifies the fields of `note`.

        Args:
            note (anki.notes.Note): the note to modify

        Returns:
            (bool) True iff the note was modified.

        """
        if self.shouldModify(note.model()):
            return self._field_updater.modifyFields(note)
        else:
            return False

    def onFocusLost(self, flag, note, current_field_index):
        """Hook for 'editFocusLost'

        Args:
            note (anki.notes.Note): the note to modify
            flag (bool): a flag that is shared between filters registered to
                the 'editFocusLost' hook to indicate whether the note has
                been modified. If it has been modified, the ui is reloaded to
                show the changes.
            current_field_index (int): the index of the field that has been
                modified.

        Returns:
            (bool) True if the note was modified, else `flag`.

        """
        if current_field_index != None:
            field_name = note.model()['flds'][current_field_index]['name']
            if field_name not in self._field_updater.sourceFields():
                return flag
            else:
                return flag or self.modifyFields(note)

    def regenerateAll(self):
        """Applies the modification to each valid card in the database."""
        if not askUser(('Do you want {} to regenerate all fields? '
                        'This may take some time and will overwrite the '
                        'destination fields.').format(self.name)):
            return
        models = [m for m in mw.col.models.all() if self.shouldModify(m)]
        # Find the notes in those models and give them kanji
        counter = 0
        for model in models:
            for nid in mw.col.models.nids(model):
                note = mw.col.getNote(nid)
                self._field_updater.modifyFields(note)
                note.flush()
                counter += 1
        if counter > 0:
            mw.reset()
        showInfo("{} regenerated fields for {} cards."
                 .format(self.name, counter))


class NamedCallbackCollector(object):
    def __init__(self):
        self.callbacks = []

    def register_callback(self, callback, name):
        self.callbacks.append((callback, name))

    def execute_callbacks(self, *args, **kwargs):
        for callback, name in self.callbacks:
            callback(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        self.execute_callbacks(*args, **kwargs)

# set up menu action
menu_action = NamedCallbackCollector()
action = QAction("All field updater addons: regenerate all fields", mw)
mw.connect(action, SIGNAL("triggered()"), menu_action)
mw.form.menuTools.addAction(action)

# set up editor button
button_action = NamedCallbackCollector()
@wraps(Editor.setupButtons)
def setupButtons(self):
    """Monkey-patch the button-setter-upper to add a button."""
    def callback():
        button_action(self.note)
        self.loadNote()
        self.checkValid()
    tooltip = "Run field updater addons. (Ctrl+f)"
    b = self._addButton("updateFieldsButton", callback, tip=tooltip, 
            key="Ctrl+f")
    iconpath = "icons{sep}updateFieldsAllButton.png".format(sep=os.sep)
    fullpath = os.path.join(os.path.dirname(__file__), iconpath)
    b.setIcon(QIcon(fullpath))

    for index, item in enumerate(button_action.callbacks):
        callback_, name = item
        def callback(callback_=callback_, name=name):  # closures!
            callback_(self.note)
            self.loadNote()
            self.checkValid()
        key = "Ctrl+{}".format((index + 1) % 10) if index < 10 else None
        tooltip = "Run {} addon.".format(name)
        if key: tooltip += " ({})".format(key)
        name = ''.join(name.split()) + 'button'
        b = self._addButton(name, callback, tip=tooltip, key=key)
        iconpath = "icons{sep}updateFieldsButton.png".format(sep=os.sep)
        fullpath = os.path.join(os.path.dirname(__file__), iconpath)
        b.setIcon(QIcon(fullpath))

Editor.setupButtons = wrap(Editor.setupButtons, setupButtons)
