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

from PyQt5.QtCore import QRectF
from PyQt5.QtGui import (QPixmap, QPainter)
from PyQt5.QtSvg import QSvgRenderer

class Deck(object):
    def __init__(self, config, deck_type=u'colour', card_back=u'back04', width=30, height=42):
        self.__width = width
        self.__height = height
        self.__cardspath = os.path.join(config.graphics_path, u"cards", deck_type)
        self.__backfile = os.path.join(config.graphics_path, u"cards", u"backs", (card_back + u".svg"))
        self.__cards = dict({ 's': None, 'h': None, 'd': None, 'c': None })
        self.__card_back = None
        self.__rank_vals = dict()

        for sk in self.__cards:
            self.__load_suit(sk)

        self.__card_back = self.__load_svg(self.__backfile)

        self.__create_rank_lookups()

    def __create_rank_lookups(self):
        self.__rank_vals = {
            '2': 2, '3': 3, '4': 4, '5': 5,
            '6': 6, '7': 7, '8': 8, '9': 9,
            'T': 10, 'J': 11, 'Q': 12,
            'K': 13, 'A': 14 }
    
    
    def __load_svg(self, path):
        renderer = QSvgRenderer(path)
        pm = QPixmap(self.__width, self.__height)
        painter = QPainter(pm)
        renderer.render(painter, QRectF(pm.rect()))
        return pm

    def __load_suit(self, suit_key):
        sd = dict()
        _p = self.__cardspath
        sd[2]   = self.__load_svg(os.path.join(_p, (suit_key + '_' + '2' + '.svg')))
        sd[3]   = self.__load_svg(os.path.join(_p, (suit_key + '_' + '3' + '.svg')))
        sd[4]   = self.__load_svg(os.path.join(_p, (suit_key + '_' + '4' + '.svg')))
        sd[5]   = self.__load_svg(os.path.join(_p, (suit_key + '_' + '5' + '.svg')))
        sd[6]   = self.__load_svg(os.path.join(_p, (suit_key + '_' + '6' + '.svg')))
        sd[7]   = self.__load_svg(os.path.join(_p, (suit_key + '_' + '7' + '.svg')))
        sd[8]   = self.__load_svg(os.path.join(_p, (suit_key + '_' + '8' + '.svg')))
        sd[9]   = self.__load_svg(os.path.join(_p, (suit_key + '_' + '9' + '.svg')))
        sd[10]   = self.__load_svg(os.path.join(_p, (suit_key + '_' + '10' + '.svg')))
        sd[11]   = self.__load_svg(os.path.join(_p, (suit_key + '_' + 'j' + '.svg')))
        sd[12]   = self.__load_svg(os.path.join(_p, (suit_key + '_' + 'q' + '.svg')))
        sd[13]   = self.__load_svg(os.path.join(_p, (suit_key + '_' + 'k' + '.svg')))
        sd[14]   = self.__load_svg(os.path.join(_p, (suit_key + '_' + 'a' + '.svg')))
        self.__cards[suit_key] = sd
        

    def card(self, suit=None, rank=0):
        return self.__cards[suit][rank]

    def back(self):
        return self.__card_back
        
    def rank(self, token=None):
        key = token.upper()
        return self.__rank_vals[key]
    
    def get_all_card_images(self):
        # returns a 4x13-element dictionary of every card image +
        # index-0 = card back each element is a QPixmap
        card_images = dict()

        for suit in ('s', 'h', 'd', 'c'):
            card_images[suit] = dict()
            for rank in (14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2):
                card_images[suit][rank] = self.card(suit, rank)

        # This is a nice trick. We put the card back image behind key 0,
        # which allows the old code to work. A dict[0] looks like first
        # index of an array.
        card_images[0] = self.back()
        return card_images
