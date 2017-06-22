#!/usr/bin/python
#-*- coding: utf-8 -*-
# File: japanese_examples.py
# Description: Looks for example sentences in the Tanaka Corpus for the current card's expression.
#
# Authors: Andreas Klauer, Guaillaume Viry, Johan de Jong
# License: GPLv2

# --- initialize kanji database ---
from aqt import mw
from aqt.qt import *

import os
import codecs
import cPickle
import random
import re
from operator import itemgetter

from .updateraddon import Addon, AnySourceAllTargetFieldUpdater

FNAME = os.path.join(mw.pm.addonFolder(), "ankihorse", "japanese_examples.utf")
FILE_PICKLE = os.path.join(mw.pm.addonFolder(), "ankihorse", "japanese_examples.pickle")

class JapaneseExamplesFieldUpdater(AnySourceAllTargetFieldUpdater):
    def __init__(self, query_field_names, target_field_names, weighted=True):
        """Initialiser.

        Args:
            query_field_name (str): the name of the query field.
            target_field_names (str): the name of the target field.
            weighted (bool): if True, prefer shorter sentences.

        Raises:
            ValueError if the language is not supported.
        """
        AnySourceAllTargetFieldUpdater\
                .__init__(self, query_field_names, target_field_names)

        self.weighted = weighted

        f = codecs.open(FNAME, 'r', 'utf8')
        self.content = f.readlines()
        f.close()

        # Load or generate the dictionaries
        if  (os.path.exists(FILE_PICKLE) and
            os.stat(FILE_PICKLE).st_mtime > os.stat(FNAME).st_mtime):
            f = open(FILE_PICKLE, 'rb')
            self.dictionaries = cPickle.load(f)
            f.close()
        else:
            self.dictionaries = ({}, {})
            self.build_dictionaries()
            f = open(FILE_PICKLE, 'wb')
            cPickle.dump(self.dictionaries, f, cPickle.HIGHEST_PROTOCOL)
            f.close()
                
    def modifyFields(self, note):
        """Modifies the fields of note.

        Downloads TTS from the Bing Speech api, adds it to the media 
        database and updates the target field appropriately. Doesn't 
        modify the note if the all source fields are blank. Otherwise, 
        uses the first non-blank source field in `self._query_fields`.

        Args:
            note (anki.notes.Note): dictionary-like.

        Returns:
            (bool) True iff the note was modified.

        """
        for f in filter(lambda f: f in note, self.sourceFields()):
            query = mw.col.media.strip(note[f])
            if query:
                break

        if not query:
            return False

        if any(note[f] for f in self.target_fields):
            return False

        japanese, english = self.find_examples(query, 1)[0]
        note[self.targetFields()[0]] = japanese
        note[self.targetFields()[1]] = english
        note[self.targetFields()[2]] = japanese.replace(query, u"（　）")
        
        return True

    def build_dictionaries(self):
        def splitter(txt):
            txt = re.compile('\s|\[|\]|\(|\{|\)|\}').split(txt)
            for i in range(0,len(txt)):
                if txt[i] == "~":
                    txt[i-2] = txt[i-2] + "~"
                    txt[i-1] = txt[i-1] + "~"
                    txt[i] = ""
            return [x for x in txt if x]

        for i, line in enumerate(self.content[1::2]):
            words = set(splitter(line)[1:-1])
            linelength = len(self.content[2*i][3:].split("#ID=")[0])
            for word in words:
                # Choose the appropriate dictionary; priority (0) or normal (1)
                if word.endswith("~"):
                    dictionary = self.dictionaries[0]
                    word = word[:-1]
                else:
                    dictionary = self.dictionaries[1]

                if word in dictionary and not word.isdigit():
                    dictionary[word].append((2*i,linelength))
                elif not word.isdigit():
                    dictionary[word]=[]
                    dictionary[word].append((2*i,linelength))

        # Sort all the entries based on their length
        for dictionary in self.dictionaries:
            for d in dictionary:
                dictionary[d] = sorted(dictionary[d], key=itemgetter(1))

    def find_examples(self, expression, maxitems):
        examples = []

        for dictionary in self.dictionaries:
            if expression in dictionary:
                index = dictionary[expression]
                if self.weighted:
                    index = weighted_sample(index, min(len(index),maxitems))
                else:
                    index = random.sample(index, min(len(index),maxitems))
                    index = [a for a,b in index]

                maxitems -= len(index)
                for j in index:
                    example = self.content[j].split("#ID=")[0][3:]
                    if dictionary is self.dictionaries[0]:
                        example = example + " {CHECKED}"
                    example = example.replace(expression,'<FONT COLOR="#ff0000">%s</FONT>' %expression)
                    color_example = self.content[j+1]
                    regexp = "(?:\(*%s\)*)(?:\([^\s]+?\))*(?:\[\d+\])*\{(.+?)\}" %expression
                    match = re.compile("%s" %regexp).search(color_example)
                    regexp_reading = "(?:\s([^\s]*?))(?:\(%s\))" % expression
                    match_reading = re.search(regexp_reading, color_example)
                    if match:
                        expression_bis = match.group(1)
                        example = example.replace(expression_bis,'<FONT COLOR="#ff0000">%s</FONT>' %expression_bis)
                    elif match_reading:
                        expression_bis = match_reading.group(1)
                        example = example.replace(expression_bis,'<FONT COLOR="#ff0000">%s</FONT>' %expression_bis) 
                    else:
                        example = example.replace(expression,'<FONT COLOR="#ff0000">%s</FONT>' %expression)
                    examples.append(tuple(example.split('\t')))
            else:
                match = re.search(u"(.*?)[／/]", expression)
                if match:
                    res = find_examples(match.group(1), maxitems)
                    maxitems -= len(res)
                    examples.extend(res)

                match = re.search(u"(.*?)[(（](.+?)[)）]", expression)
                if match:
                    if match.group(1).strip():
                        res = find_examples("%s%s" % (match.group(1), match.group(2)), maxitems)
                        maxitems -= len(res)
                        examples.extend(res)

        return examples

def initialise(name='japanese_examples', source_fields=['Expression'], 
        target_fields=['Sentence', 'Sentence-Clozed'], weighted=True,
        model_name_substring=None, on_focus_lost=False):
    field_updater = JapaneseExamplesFieldUpdater(
            source_fields, target_fields, weighted)
    Addon(field_updater, name, model_name_substring, on_focus_lost)

class Node:
    pass

def weighted_sample(somelist, n):
    # TODO: See if http://stackoverflow.com/questions/2140787/select-random-k-elements-from-a-list-whose-elements-have-weights is faster for some practical use-cases.
    # This method is O(n²), but is straightforward and simple.

    # Magic numbers:
    minlength = 25
    maxlength = 70
    power = 3

    #
    l = []   # List containing nodes with their (constantly) updated weights
    ret = [] # Array of return values
    tw = 0.0 # Total weight

    for a,b in somelist:
        bold = b
        b = max(b,minlength)
        b = min(b,maxlength)
        b = b - minlength
        b = maxlength - minlength - b + 1
        b = b**power
        z = Node()
        z.w = b
        z.v = a
        tw += b
        l.append(z)

    for j in range(n):
        g = tw * random.random()
        for z in l:
            if g < z.w:
                ret.append(z.v)
                tw -= z.w
                z.w = 0.0
                break
            else:
                g -= z.w

    return ret
