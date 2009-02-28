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
from time import strftime

# Class for converting Everleaf HH format.

class Everleaf(HandHistoryConverter):
    
    # Static regexes
    re_SplitHands  = re.compile(r"\n\n+")
    re_GameInfo    = re.compile(r"^(Blinds )?\$?(?P<SB>[.0-9]+)/\$?(?P<BB>[.0-9]+) ((?P<LTYPE>NL|PL) )?(?P<GAME>(Hold\'em|Omaha|7 Card Stud))", re.MULTILINE)
    re_HandInfo    = re.compile(r".*#(?P<HID>[0-9]+)\n.*\n(Blinds )?\$?(?P<SB>[.0-9]+)/\$?(?P<BB>[.0-9]+) (?P<GAMETYPE>.*) - (?P<DATETIME>\d\d\d\d/\d\d/\d\d - \d\d:\d\d:\d\d)\nTable (?P<TABLE>[- a-zA-Z]+)")
    re_Button      = re.compile(r"^Seat (?P<BUTTON>\d+) is the button", re.MULTILINE)
    re_PlayerInfo  = re.compile(r"^Seat (?P<SEAT>[0-9]+): (?P<PNAME>.*) \(\s+(\$ (?P<CASH>[.0-9]+) USD|new player|All-in) \)", re.MULTILINE)
    re_Board       = re.compile(r"\[ (?P<CARDS>.+) \]")
        
    
    def __init__(self, config, file):
        print "Initialising Everleaf converter class"
        HandHistoryConverter.__init__(self, config, file, sitename="Everleaf") # Call super class init.
        self.sitename = "Everleaf"
        self.setFileType("text", "cp1252")
        

        try:
            self.ofile     = os.path.join(self.hhdir, file.split(os.path.sep)[-2]+"-"+os.path.basename(file))
        except:
            self.ofile     = os.path.join(self.hhdir, "x"+strftime("%d-%m-%y")+os.path.basename(file))

    def compilePlayerRegexs(self):
        player_re = "(?P<PNAME>" + "|".join(map(re.escape, self.players)) + ")"
        #print "DEBUG player_re: " + player_re
        self.re_PostSB          = re.compile(r"^%s: posts small blind \[\$? (?P<SB>[.0-9]+)" % player_re, re.MULTILINE)
        self.re_PostBB          = re.compile(r"^%s: posts big blind \[\$? (?P<BB>[.0-9]+)" % player_re, re.MULTILINE)
        self.re_PostBoth        = re.compile(r"^%s: posts both blinds \[\$? (?P<SBBB>[.0-9]+)" % player_re, re.MULTILINE)
        self.re_HeroCards       = re.compile(r"^Dealt to %s \[ (?P<CARDS>.*) \]" % player_re, re.MULTILINE)
        self.re_Action          = re.compile(r"^%s(?P<ATYPE>: bets| checks| raises| calls| folds)(\s\[\$ (?P<BET>[.\d]+) (USD|EUR)\])?" % player_re, re.MULTILINE)
        self.re_ShowdownAction  = re.compile(r"^%s shows \[ (?P<CARDS>.*) \]" % player_re, re.MULTILINE)
        self.re_CollectPot      = re.compile(r"^%s wins \$ (?P<POT>[.\d]+) (USD|EUR)(.*?\[ (?P<CARDS>.*?) \])?" % player_re, re.MULTILINE)
        self.re_SitsOut         = re.compile(r"^%s sits out" % player_re, re.MULTILINE)

    def readSupportedGames(self):
        return [["ring", "hold", "nl"],
                ["ring", "hold", "pl"],
                ["ring", "omaha", "pl"]
               ]

    def determineGameType(self):
        # Cheating with this regex, only support nlhe at the moment
        # Blinds $0.50/$1 PL Omaha - 2008/12/07 - 21:59:48
        # Blinds $0.05/$0.10 NL Hold'em - 2009/02/21 - 11:21:57
        # $0.25/$0.50 7 Card Stud - 2008/12/05 - 21:43:59
        
        # Tourney:
        # Everleaf Gaming Game #75065769
        # ***** Hand history for game #75065769 *****
        # Blinds 10/20 NL Hold'em - 2009/02/25 - 17:30:32
        # Table 2

        structure = "" # nl, pl, cn, cp, fl
        game      = ""

        m = self.re_GameInfo.search(self.obs)
        if m == None:
            return None
        if m.group('LTYPE') == "NL":
            structure = "nl"
        elif m.group('LTYPE') == "PL":
            structure = "pl"
        else:
            structure = "fl" # we don't support it, but there should be how to detect it at least.

        if m.group('GAME') == "Hold\'em":
            game = "hold"
        elif m.group('GAME') == "Omaha":
            game = "omahahi"
        elif m.group('GAME') == "7 Card Stud":
            game = "studhi" # Everleaf currently only does Hi stud

        gametype = ["ring", game, structure, m.group('SB'), m.group('BB')]

        return gametype

    def readHandInfo(self, hand):
        m =  self.re_HandInfo.search(hand.string)
        if(m == None):
            print "DEBUG: re_HandInfo.search failed: '%s'" %(hand.string)
        hand.handid = m.group('HID')
        hand.tablename = m.group('TABLE')
        hand.max_seats = 6 # assume 6-max unless we have proof it's a larger/smaller game, since everleaf doesn't give seat max info
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

    def readPlayerStacks(self, hand):
        m = self.re_PlayerInfo.finditer(hand.string)
        for a in m:
            seatnum = int(a.group('SEAT'))
            hand.addPlayer(seatnum, a.group('PNAME'), a.group('CASH'))
            if seatnum > 6:
                hand.max_seats = 10 # everleaf currently does 2/6/10 games, so if seats > 6 are in use, it must be 10-max.
                # TODO: implement lookup list by table-name to determine maxes, then fall back to 6 default/10 here, if there's no entry in the list?
            
        
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
        #print "DEBUG " + street + ":"
        #print hand.streets.group(street) + "\n"
        if street in ('FLOP','TURN','RIVER'):   # a list of streets which get dealt community cards (i.e. all but PREFLOP)
            m = self.re_Board.search(hand.streets.group(street))
            hand.setCommunityCards(street, m.group('CARDS').split(', '))

    def readBlinds(self, hand):
        try:
            m = self.re_PostSB.search(hand.string)
            hand.addBlind(m.group('PNAME'), 'small blind', m.group('SB'))
        except Exception, e: # no small blind
            #print e
            hand.addBlind(None, None, None)
        for a in self.re_PostBB.finditer(hand.string):
            hand.addBlind(a.group('PNAME'), 'big blind', a.group('BB'))
        for a in self.re_PostBoth.finditer(hand.string):
            hand.addBlind(a.group('PNAME'), 'both', a.group('SBBB'))

    def readButton(self, hand):
        hand.buttonpos = int(self.re_Button.search(hand.string).group('BUTTON'))

    def readHeroCards(self, hand):
        m = self.re_HeroCards.search(hand.string)
        if(m == None):
            #Not involved in hand
            hand.involved = False
        else:
            hand.hero = m.group('PNAME')
            # "2c, qh" -> set(["2c","qc"])
            # Also works with Omaha hands.
            cards = m.group('CARDS')
            cards = cards.split(', ')
            hand.addHoleCards(cards, m.group('PNAME'))

    def readAction(self, hand, street):
        m = self.re_Action.finditer(hand.streets.group(street))
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
        """Reads lines where holecards are reported in a showdown"""
        for shows in self.re_ShowdownAction.finditer(hand.string):            
            cards = shows.group('CARDS')
            cards = cards.split(', ')
            hand.addShownCards(cards, shows.group('PNAME'))

    def readCollectPot(self,hand):
        for m in self.re_CollectPot.finditer(hand.string):
            hand.addCollectPot(player=m.group('PNAME'),pot=m.group('POT'))

    def readShownCards(self,hand):
        """Reads lines where hole & board cards are mixed to form a hand (summary lines)"""
        for m in self.re_CollectPot.finditer(hand.string):
            if m.group('CARDS') is not None:
                cards = m.group('CARDS')
                cards = cards.split(', ')
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
