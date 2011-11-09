# Deck.py
# -*- coding: utf-8
# PokerStats, an online poker statistics tracking software for Linux
# Copyright (C) 2007-2011 Mika Boström <bostik@iki.fi>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
"""Deck.py

Helper class for mucked card display. Loads specified deck from SVG
images and returns it as a dict of pixbufs.
"""

import os
import gtk

# This is used to get the path(s) to card images
import card_path

class Deck(object):
    def __init__(self, decktype='simple', width=30, height=42):
        self.__width = width
        self.__height = height
        self.__path = card_path.deck_path()
        self.__cards = dict({ 's': None, 'h': None, 'd': None, 'c': None })
        self.__card_back = None
        self.__rank_vals = dict()
        #
        for sk in self.__cards:
            self.__load_suit(sk, decktype)
        self.__load_back()
        #
        self.__create_rank_lookups()

    def __create_rank_lookups(self):
        self.__rank_vals = {
            '2': 2, '3': 3, '4': 4, '5': 5,
            '6': 6, '7': 7, '8': 8, '9': 9,
            'T': 10, 'J': 11, 'Q': 12,
            'K': 13, 'A': 14 }
    
    
    def __load_svg(self, path):
        pb = gtk.gdk.pixbuf_new_from_file_at_size(path,
            self.__width, self.__height)
        return pb

    def __load_suit(self, suit_key, decktype):
        sd = dict()
        _p = '%s/cards/%s' % (self.__path, decktype)
        sd[2]   = self.__load_svg(_p + '/' + suit_key + '_' + '2' + '.svg')
        sd[3]   = self.__load_svg(_p + '/' + suit_key + '_' + '3' + '.svg')
        sd[4]   = self.__load_svg(_p + '/' + suit_key + '_' + '4' + '.svg')
        sd[5]   = self.__load_svg(_p + '/' + suit_key + '_' + '5' + '.svg')
        sd[6]   = self.__load_svg(_p + '/' + suit_key + '_' + '6' + '.svg')
        sd[7]   = self.__load_svg(_p + '/' + suit_key + '_' + '7' + '.svg')
        sd[8]   = self.__load_svg(_p + '/' + suit_key + '_' + '8' + '.svg')
        sd[9]   = self.__load_svg(_p + '/' + suit_key + '_' + '9' + '.svg')
        sd[10]  = self.__load_svg(_p + '/' + suit_key + '_' + '10' + '.svg')
        sd[11]  = self.__load_svg(_p + '/' + suit_key + '_' + 'j' + '.svg')
        sd[12]  = self.__load_svg(_p + '/' + suit_key + '_' + 'q' + '.svg')
        sd[13]  = self.__load_svg(_p + '/' + suit_key + '_' + 'k' + '.svg')
        sd[14]  = self.__load_svg(_p + '/' + suit_key + '_' + 'a' + '.svg')
        self.__cards[suit_key] = sd


    def __load_back(self, name='back04'):
        _path = '%s/cards/backs/%s.svg' % (self.__path, name)
        self.__card_back = self.__load_svg(_path)
        

    def card(self, suit=None, rank=0):
        return self.__cards[suit][rank]

    def back(self):
        return self.__card_back
        
    def rank(self, token=None):
        key = token.upper()
        return self.__rank_vals[key]
