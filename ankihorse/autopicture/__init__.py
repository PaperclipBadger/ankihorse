"""
autopicture
===========

Addon that automatically adds pictures to anki cards based on a field.

"""
from ..updateraddon import Addon
from .imagefetch import GoogleImageFieldUpdater

def initialise(name='autopicture', source_field='picture_src', 
        target_field='picture', model_name_substring=None):
    field_updater = GoogleImageFieldUpdater(source_field, target_field)
    Addon(field_updater, name, model_name_substring=model_name_substring)
