"""
autopicture
===========

Addon that automatically adds pictures to anki cards based on a field.

"""
from .updateraddon import Addon, FieldUpdater
from .imagefetch import GoogleImageFieldUpdater

SRC_FIELD = 'English'
DST_FIELD = 'Picture'

field_updater = GoogleImageFieldUpdater(SRC_FIELD, DST_FIELD)
Addon(field_updater, 'japanese autopicture', 'japanese')
