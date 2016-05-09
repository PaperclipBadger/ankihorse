"""
autopicture
===========

Addon that automatically adds pictures to anki cards based on a field.

"""
from ..updateraddon import Addon, FieldUpdater
from .imagefetch import GoogleImageFieldUpdater

def initialize(name, source_field, target_field, model_name_substring=None)
    field_updater = GoogleImageFieldUpdater(source_field, target_field)
    Addon(field_updater, name, model_name_substring=model_name_substring)
