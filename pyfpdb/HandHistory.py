#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""HandHistory.py

Parses HandHistory xml files and returns requested objects.
"""
#    Copyright 2008-2011, Ray E. Barker
#    
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#    
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#    
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

########################################################################
#    Standard Library modules
import xml.dom.minidom
from   xml.dom.minidom import Node

class HandHistory:
    def __init__(self, xml_string, elements = ('ALL')):

        doc = xml.dom.minidom.parseString(xml_string)
        if elements == ('ALL'):
            elements = ('BETTING', 'AWARDS', 'POSTS', 'PLAYERS', 'GAME')

        if 'BETTING' in elements:
            self.BETTING = Betting(doc.getElementsByTagName('BETTING')[0])
        if 'AWARDS' in elements:
            self.AWARDS  = Awards (doc.getElementsByTagName('AWARDS')[0])
        if 'POSTS' in elements:
            self.POSTS   = Posts  (doc.getElementsByTagName('POSTS')[0])
        if 'GAME' in elements:
            self.GAME   = Game    (doc.getElementsByTagName('GAME')[0])
        if 'PLAYERS' in elements:
            self.PLAYERS = {}
            p_n = doc.getElementsByTagName('PLAYERS')[0]
            for p in p_n.getElementsByTagName('PLAYER'):
                a_player = Player(p)
                self.PLAYERS[a_player.name] = a_player

class Player:
    def __init__(self, node):
        self.name        = node.getAttribute('NAME')
        self.seat        = node.getAttribute('SEAT')
        self.stack       = node.getAttribute('STACK')
        self.showed_hand = node.getAttribute('SHOWED_HAND')
        self.cards       = node.getAttribute('CARDS')
        self.allin       = node.getAttribute('ALLIN')
        self.sitting_out = node.getAttribute('SITTING_OUT')
        self.hand        = node.getAttribute('HAND')
        self.start_cards = node.getAttribute('START_CARDS')
        
        if self.allin       == '' or  \
           self.allin       == '0' or \
           self.allin.upper()       == 'FALSE': self.allin = False
        else: self.allin       = True

        if self.sitting_out == '' or  \
           self.sitting_out == '0' or  \
           self.sitting_out.upper() == 'FALSE': self.sitting_out = False
        else: self.sitting_out       = True

    def __str__(self):
        temp = "%s\n    seat = %s\n    stack = %s\n    cards = %s\n" % \
                (self.name, self.seat, self.stack, self.cards)
        temp = temp + "    showed_hand = %s\n    allin = %s\n" % \
                (self.showed_hand, self.allin)
        temp = temp + "    hand = %s\n    start_cards = %s\n" % \
                (self.hand, self.start_cards)
        return temp

class Awards:
    def __init__(self, node):
        self.awards = []  # just an array of award objects
        for a in node.getElementsByTagName('AWARD'):
            self.awards.append(Award(a))

    def __str__(self):
        temp = ""
        for a in self.awards:
            temp = temp + "%s\n" % (a)
        return temp

class Award:
    def __init__(self, node):
        self.player = node.getAttribute('PLAYER')
        self.amount = node.getAttribute('AMOUNT')
        self.pot    = node.getAttribute('POT')

    def __str__(self):
        return self.player + " won " + self.amount + " from " + self.pot

class Game:
    def __init__(self, node):
        print node
        self.tags = {}
        for tag in ( ('GAME_NAME', 'game_name'), ('MAX', 'max'), ('HIGHLOW', 'high_low'),
                     ('STRUCTURE', 'structure'), ('MIXED', 'mixed') ):
            L = node.getElementsByTagName(tag[0])
            if (not L): continue
            print L
            for node2 in L:
                title = ""
                for node3 in node2.childNodes:
                    if (node3.nodeType == Node.TEXT_NODE):
                        title +=node3.data
                self.tags[tag[1]] = title

    def __str__(self):
        return "%s %s %s, (%s max), %s" % (self.tags['structure'], 
                                           self.tags['game_name'],
                                           self.tags['game_name'],
                                           self.tags['max'],
                                           self.tags['game_name'])

class Posts:
    def __init__(self, node):
        self.posts = []  # just an array of post objects
        for p in node.getElementsByTagName('POST'):
            self.posts.append(Post(p))

    def __str__(self):
        temp = ""
        for p in self.posts:
            temp = temp + "%s\n" % (p)
        return temp

class Post:
    def __init__(self, node):
        self.player = node.getAttribute('PLAYER')
        self.amount = node.getAttribute('AMOUNT')
        self.posted = node.getAttribute('POSTED')
        self.live   = node.getAttribute('LIVE')

    def __str__(self):
        return ("%s posted %s %s %s") % (self.player, self.amount, self.posted, self.live)

class Betting:
    def __init__(self, node):
        self.rounds = []  # a Betting object is just an array of rounds
        for r in node.getElementsByTagName('ROUND'):
            self.rounds.append(Round(r))

    def __str__(self):
        temp = ""
        for r in self.rounds:
            temp = temp + "%s\n" % (r)
        return temp

class Round:
    def __init__(self, node):
        self.name = node.getAttribute('ROUND_NAME')
        self.action = []
        for a in node.getElementsByTagName('ACTION'):
            self.action.append(Action(a))

    def __str__(self):
        temp = self.name + "\n"
        for a in self.action:
            temp = temp + "    %s\n" % (a)
        return temp

class Action:
    def __init__(self, node):
        self.player = node.getAttribute('PLAYER')
        self.action = node.getAttribute('ACT')
        self.amount = node.getAttribute('AMOUNT')
        self.allin  = node.getAttribute('ALLIN')

    def __str__(self):
        return self.player + " " + self.action + " " + self.amount + " " + self.allin
        
if __name__== "__main__":
    file = open('test.xml', 'r')
    xml_string = file.read()
    file.close()
    
    print xml_string + "\n\n\n"
    h = HandHistory(xml_string, ('ALL'))
    print h.GAME
    print h.POSTS
    print h.BETTING
    print h.AWARDS
    
    for p in h.PLAYERS.keys():
        print h.PLAYERS[p]
