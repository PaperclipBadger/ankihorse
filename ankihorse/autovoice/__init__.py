"""
autovoice
===========

Addon that automatically adds TTS to anki cards based on a field.

"""
from ..updateraddon import Addon
from .audiofetch import VoiceRSSFieldUpdater

def initialize(name, source_field, target_field, model_name_substring=None):
    field_updater = VoiceRSSFieldUpdater(source_field, target_field)
    Addon(field_updater, name, model_name_substring=model_name_substring)
