#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
autovoice
===========

Addon that automatically adds TTS to anki cards based on a field.

"""
from ..updateraddon import Addon
from .audiofetch import VoiceRSSFieldUpdater

def initialise(name='autovoice', language='english', source_field='voice_src',
        target_field='voice', model_name_substring=None):
    field_updater = VoiceRSSFieldUpdater(source_field, target_field, language)
    Addon(field_updater, name, model_name_substring=model_name_substring)
