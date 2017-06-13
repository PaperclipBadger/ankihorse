#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
Ankihorse
=========

Adds pictures and vocalisation to japanese cards.

"""
from ankihorse import autopicture
from ankihorse import autovoice


autopicture.initialise\
        ( name='Japanese Autopicture'
        , source_fields=['Expression', 'Kanji', 'Kana']
        , target_field='Picture'
        , locale='ja-JP'
        , model_name_substring='japanese'
        ) 

autovoice.initialise\
        ( name='Japanese Autovoice'
        , language='japanese'
        , source_fields=['Pronunciation', 'Expression', 'Kanji', 'Kana']
        , target_field='Voice'
        , model_name_substring='japanese'
        ) 
