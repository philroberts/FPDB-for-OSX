#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#    Copyright 2008, Carl Gherardi
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

import sys
import Configuration
from HandHistoryConverter import *

# Everleaf HH format

# Everleaf Gaming Game #55208539
# ***** Hand history for game #55208539 *****
# Blinds $0.50/$1 NL Hold'em - 2008/09/01 - 13:35:01
# Table Speed Kuala
# Seat 1 is the button
# Total number of players: 9
# Seat 1: BadBeatBox (  $ 98.97 USD )
# Seat 3: EricBlade (  $ 73.96 USD )
# Seat 4: randy888 (  $ 196.50 USD )
# Seat 5: BaronSengir (  $ 182.80 USD )
# Seat 6: dogge (  $ 186.06 USD )
# Seat 7: wings ( $ 50 USD )
# Seat 8: schoffeltje (  $ 282.05 USD )
# Seat 9: harrydebeng (  $ 109.45 USD )
# Seat 10: smaragdar (  $ 96.50 USD )
# EricBlade: posts small blind [$ 0.50 USD]
# randy888: posts big blind [$ 1 USD]
# wings: posts big blind [$ 1 USD]
# ** Dealing down cards **
# Dealt to EricBlade [ qc, 3c ]
# BaronSengir folds
# dogge folds
# wings raises [$ 2.50 USD]
# schoffeltje folds
# harrydebeng calls [$ 3.50 USD]
# smaragdar raises [$ 15.50 USD]
# BadBeatBox folds
# EricBlade folds
# randy888 folds
# wings calls [$ 12 USD]
# harrydebeng folds
# ** Dealing Flop ** [ qs, 3d, 8h ]
# wings: bets [$ 34.50 USD]
# smaragdar calls [$ 34.50 USD]
# ** Dealing Turn ** [ 2d ]
# ** Dealing River ** [ 6c ]
# dogge shows [ 9h, 9c ]a pair of nines
# spicybum shows [ 5d, 6d ]a straight, eight high
# harrydebeng does not show cards
# smaragdar wins $ 102 USD from main pot with a pair of aces [ ad, ah, qs, 8h, 6c ]

class Everleaf(HandHistoryConverter):
    def __init__(self, config, file):
        print "Initialising Everleaf converter class"
        HandHistoryConverter.__init__(self, config, file, sitename="Everleaf") # Call super class init.
        self.sitename = "Everleaf"
        self.setFileType("text", "cp1252")
        self.rexx.setGameInfoRegex('.*Blinds \$?(?P<SB>[.0-9]+)/\$?(?P<BB>[.0-9]+)')
        self.rexx.setSplitHandRegex('\n\n+')
        self.rexx.setHandInfoRegex('.*#(?P<HID>[0-9]+)\n.*\nBlinds \$?(?P<SB>[.0-9]+)/\$?(?P<BB>[.0-9]+) (?P<GAMETYPE>.*) - (?P<DATETIME>\d\d\d\d/\d\d/\d\d - \d\d:\d\d:\d\d)\nTable (?P<TABLE>[ a-zA-Z]+)\nSeat (?P<BUTTON>[0-9]+)')
        self.rexx.setPlayerInfoRegex('Seat (?P<SEAT>[0-9]+): (?P<PNAME>.*) \(\s+(\$ (?P<CASH>[.0-9]+) USD|new player|All-in) \)')
        self.rexx.setPostSbRegex('.*\n(?P<PNAME>.*): posts small blind \[\$? (?P<SB>[.0-9]+)')
        self.rexx.setPostBbRegex('.*\n(?P<PNAME>.*): posts big blind \[\$? (?P<BB>[.0-9]+)')
        self.rexx.setPostBothRegex('.*\n(?P<PNAME>.*): posts small \& big blinds \[\$? (?P<SBBB>[.0-9]+)')
        self.rexx.setHeroCardsRegex('.*\nDealt\sto\s(?P<PNAME>.*)\s\[ (?P<CARDS>.*) \]')
        self.rexx.setActionStepRegex('.*\n(?P<PNAME>.*)(?P<ATYPE>: bets| checks| raises| calls| folds)(\s\[\$ (?P<BET>[.\d]+) (USD|EUR)\])?')
        self.rexx.setShowdownActionRegex('.*\n(?P<PNAME>.*) shows \[ (?P<CARDS>.*) \]')
        self.rexx.setCollectPotRegex('.*\n(?P<PNAME>.*) wins \$ (?P<POT>[.\d]+) (USD|EUR)(.*?\[ (?P<CARDS>.*?) \])?')
        #self.rexx.setCollectPotRegex('.*\n(?P<PNAME>.*) wins \$ (?P<POT>[.\d]+) USD(.*\[ (?P<CARDS>) \S\S, \S\S, \S\S, \S\S, \S\S \])?')
        self.rexx.sits_out_re = re.compile('(?P<PNAME>.*) sits out')
        self.rexx.compileRegexes()

    def readSupportedGames(self):
        pass

    def determineGameType(self):
        # Cheating with this regex, only support nlhe at the moment
        gametype = ["ring", "hold", "nl"]

        m = self.rexx.game_info_re.search(self.obs)
        gametype = gametype + [m.group('SB')]
        gametype = gametype + [m.group('BB')]
        
        return gametype

    def readHandInfo(self, hand):
        m =  self.rexx.hand_info_re.search(hand.string)
        hand.handid = m.group('HID')
        hand.tablename = m.group('TABLE')
# These work, but the info is already in the Hand class - should be used for tourneys though.
#		m.group('SB')
#		m.group('BB')
#		m.group('GAMETYPE')

# Believe Everleaf time is GMT/UTC, no transation necessary
# Stars format (Nov 10 2008): 2008/11/07 12:38:49 CET [2008/11/07 7:38:49 ET]
# or                        : 2008/11/07 12:38:49 ET
# Not getting it in my HH files yet, so using
# 2008/11/10 3:58:52 ET
#TODO: Do conversion from GMT to ET
#TODO: Need some date functions to convert to different timezones (Date::Manip for perl rocked for this)
        hand.starttime = time.strptime(m.group('DATETIME'), "%Y/%m/%d - %H:%M:%S")
        hand.buttonpos = int(m.group('BUTTON'))

    def readPlayerStacks(self, hand):
        m = self.rexx.player_info_re.finditer(hand.string)
        players = []
        for a in m:
            hand.addPlayer(int(a.group('SEAT')), a.group('PNAME'), a.group('CASH'))

    def markStreets(self, hand):
        # PREFLOP = ** Dealing down cards **
        # This re fails if,  say, river is missing; then we don't get the ** that starts the river.
        #m = re.search('(\*\* Dealing down cards \*\*\n)(?P<PREFLOP>.*?\n\*\*)?( Dealing Flop \*\* \[ (?P<FLOP1>\S\S), (?P<FLOP2>\S\S), (?P<FLOP3>\S\S) \])?(?P<FLOP>.*?\*\*)?( Dealing Turn \*\* \[ (?P<TURN1>\S\S) \])?(?P<TURN>.*?\*\*)?( Dealing River \*\* \[ (?P<RIVER1>\S\S) \])?(?P<RIVER>.*)', hand.string,re.DOTALL)

        m =  re.search(r"\*\* Dealing down cards \*\*(?P<PREFLOP>.+(?=\*\* Dealing Flop \*\*)|.+)"
                       r"(\*\* Dealing Flop \*\*(?P<FLOP> \[ \S\S, \S\S, \S\S \].+(?=\*\* Dealing Turn \*\*)|.+))?"
                       r"(\*\* Dealing Turn \*\*(?P<TURN> \[ \S\S \].+(?=\*\* Dealing River \*\*)|.+))?"
                       r"(\*\* Dealing River \*\*(?P<RIVER> \[ \S\S \].+))?", hand.string,re.DOTALL)

        hand.addStreets(m)
            

    def readCommunityCards(self, hand, street): # street has been matched by markStreets, so exists in this hand
        self.rexx.board_re = re.compile(r"\[ (?P<CARDS>.+) \]")
        print hand.streets.group(street)
        if street in ('FLOP','TURN','RIVER'):   # a list of streets which get dealt community cards (i.e. all but PREFLOP)
            m = self.rexx.board_re.search(hand.streets.group(street))
            hand.setCommunityCards(street, m.group('CARDS').split(', '))

    def readBlinds(self, hand):
        try:
            m = self.rexx.small_blind_re.search(hand.string)
            hand.addBlind(m.group('PNAME'), 'small blind', m.group('SB'))
        except: # no small blind
            hand.addBlind(None, None, None)
        for a in self.rexx.big_blind_re.finditer(hand.string):
            hand.addBlind(a.group('PNAME'), 'big blind', a.group('BB'))
        for a in self.rexx.both_blinds_re.finditer(hand.string):
            hand.addBlind(a.group('PNAME'), 'small & big blinds', a.group('SBBB'))

    def readHeroCards(self, hand):
        m = self.rexx.hero_cards_re.search(hand.string)
        if(m == None):
            #Not involved in hand
            hand.involved = False
        else:
            hand.hero = m.group('PNAME')
            # "2c, qh" -> set(["2c","qc"])
            # Also works with Omaha hands.
            cards = m.group('CARDS')
            cards = set(cards.split(', '))
            hand.addHoleCards(cards, m.group('PNAME'))

    def readAction(self, hand, street):
        m = self.rexx.action_re.finditer(hand.streets.group(street))
        for action in m:
            if action.group('ATYPE') == ' raises':
                hand.addCallandRaise( street, action.group('PNAME'), action.group('BET') )
            elif action.group('ATYPE') == ' calls':
                hand.addCall( street, action.group('PNAME'), action.group('BET') )
            elif action.group('ATYPE') == ': bets':
                hand.addBet( street, action.group('PNAME'), action.group('BET') )
            elif action.group('ATYPE') == ' folds':
                hand.addFold( street, action.group('PNAME'))
            elif action.group('ATYPE') == ' checks':
                hand.addCheck( street, action.group('PNAME'))
            else:
                print "DEBUG: unimplemented readAction: %s %s" %(action.group('PNAME'),action.group('ATYPE'),)


    def readShowdownActions(self, hand):
        for shows in self.rexx.showdown_action_re.finditer(hand.string):            
            cards = shows.group('CARDS')
            cards = set(cards.split(', '))
            hand.addShownCards(cards, shows.group('PNAME'))

    def readCollectPot(self,hand):
        for m in self.rexx.collect_pot_re.finditer(hand.string):
            hand.addCollectPot(player=m.group('PNAME'),pot=m.group('POT'))

    def readShownCards(self,hand):
        for m in self.rexx.collect_pot_re.finditer(hand.string):
            if m.group('CARDS') is not None:
                cards = m.group('CARDS')
                cards = set(cards.split(', '))
                hand.addShownCards(cards=None, player=m.group('PNAME'), holeandboard=cards)



if __name__ == "__main__":
    c = Configuration.Config()
    if len(sys.argv) ==  1:
        testfile = "regression-test-files/everleaf/Speed_Kuala_full.txt"
    else:
        testfile = sys.argv[1]
    e = Everleaf(c, testfile)
    e.processFile()
    print str(e)
