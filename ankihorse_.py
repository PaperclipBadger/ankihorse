#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
Ankihorse
=========

Adds pictures and vocalisation to japanese cards.

"""
from ankihorse import autopicture
from ankihorse import autovoice
from ankihorse import japanese_examples


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
        , on_focus_lost=True
        ) 

japanese_examples.initialise\
        ( name='Japanese Example Sentences'
        , source_fields=['Expression']
        , target_fields=['Sentence', 'Sentence-English', 'Sentence-Clozed']
        , weighted=True
        , model_name_substring='japanese'
        , on_focus_lost=True
        )

autovoice.initialise\
        ( name='Japanese Autovoice (Sentences)'
        , language='japanese'
        , source_fields=['Sentence']
        , target_field='Sentence-Voice'
        , model_name_substring='japanese'
        , on_focus_lost=True
        ) 
