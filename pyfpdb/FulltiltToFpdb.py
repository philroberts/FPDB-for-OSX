#!/usr/bin/env python
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

# FullTilt HH Format converter

class FullTilt(HandHistoryConverter):
    def __init__(self, config, file):
        print "Initialising FullTilt converter class"
        HandHistoryConverter.__init__(self, config, file, sitename="FullTilt") # Call super class init.
        self.sitename = "FullTilt"
        self.setFileType("text", "cp1252")
        self.re_GameInfo    = re.compile('- \$?(?P<SB>[.0-9]+)/\$?(?P<BB>[.0-9]+) (Ante \$(?P<ANTE>[.0-9]+) )?- (?P<LTYPE>(No|Pot)? )?Limit (?P<GAME>(Hold\'em|Omaha|Razz))')
        self.re_SplitHands  = re.compile(r"\n\n+")
        self.re_HandInfo    = re.compile('.*#(?P<HID>[0-9]+): Table (?P<TABLE>[- a-zA-Z]+) (\((?P<TABLEATTRIBUTES>.+)\) )?- \$?(?P<SB>[.0-9]+)/\$?(?P<BB>[.0-9]+) (Ante \$(?P<ANTE>[.0-9]+) )?- (?P<GAMETYPE>[a-zA-Z\' ]+) - (?P<DATETIME>.*)')
        self.re_Button      = re.compile('The button is in seat #(?P<BUTTON>\d+)')
        self.re_PlayerInfo  = re.compile('Seat (?P<SEAT>[0-9]+): (?P<PNAME>.*) \(\$(?P<CASH>[.0-9]+)\)\n')
        self.re_Board = re.compile(r"\[(?P<CARDS>.+)\]")

    def compile_player_regexs(self):
        player_re = "(?P<PNAME>" + "|".join(map(re.escape, self.players)) + ")"
        #print "DEBUG player_re: " + player_re
        self.re_PostSB           = re.compile('.*\n(?P<PNAME>.*) posts the small blind of \$?(?P<SB>[.0-9]+)')
        self.re_PostBB           = re.compile('.*\n(?P<PNAME>.*) posts (the big blind of )?\$?(?P<BB>[.0-9]+)')
        self.re_BringIn          = re.compile('.*\n(?P<PNAME>.*) brings in for \$?(?P<BRINGIN>[.0-9]+)')
        self.re_PostBoth         = re.compile('.*\n(?P<PNAME>.*) posts small \& big blinds \[\$? (?P<SBBB>[.0-9]+)')
        self.re_HeroCards        = re.compile('.*\nDealt\sto\s(?P<PNAME>.*)\s\[(?P<CARDS>.*)\]( \[(?P<NEWCARD>.*)\])?')
        self.re_Action           = re.compile('.*\n(?P<PNAME>.*)(?P<ATYPE> bets| checks| raises to| calls| folds)(\s\$(?P<BET>[.\d]+))?')
        self.re_ShowdownAction   = re.compile('.*\n(?P<PNAME>.*) shows \[(?P<CARDS>.*)\]')
        self.re_CollectPot       = re.compile(r"Seat (?P<SEAT>[0-9]+): (?P<PNAME>.*?) (\(button\) |\(small blind\) |\(big blind\) )?(collected|showed \[.*\] and won) \(\$(?P<POT>[.\d]+)\)(, mucked| with.*)")
        self.re_SitsOut          = re.compile('(?P<PNAME>.*) sits out')
        self.re_ShownCards       = re.compile('Seat (?P<SEAT>[0-9]+): (?P<PNAME>.*) \(.*\) showed \[(?P<CARDS>.*)\].*')


    def readSupportedGames(self):
        return [["ring", "hold", "nl"], 
                ["ring", "hold", "pl"],
                ["ring", "razz", "fl"],
                ["ring", "omaha", "pl"]
               ]

    def determineGameType(self):
        # Cheating with this regex, only support nlhe at the moment
        # Full Tilt Poker Game #10777181585: Table Deerfly (deep 6) - $0.01/$0.02 - Pot Limit Omaha Hi - 2:24:44 ET - 2009/02/22
        # Full Tilt Poker Game #10773265574: Table Butte (6 max) - $0.01/$0.02 - Pot Limit Hold'em - 21:33:46 ET - 2009/02/21
        # Full Tilt Poker Game #9403951181: Table CR - tay - $0.05/$0.10 - No Limit Hold'em - 9:40:20 ET - 2008/12/09
        structure = "" # nl, pl, cn, cp, fl
        game      = ""


        m = self.re_GameInfo.search(self.obs)
        if m.group('LTYPE') == "No ":
            structure = "nl"
        elif m.group('LTYPE') == "Pot ":
            structure = "pl"
        elif m.group('LTYPE') == None:
            structure = "fl"

        if m.group('GAME') == "Hold\'em":
            game = "hold"
        elif m.group('GAME') == "Omaha":
            game = "omahahi"
        elif m.group('GAME') == "Razz":
            game = "razz"

        print m.groups()

        gametype = ["ring", game, structure, m.group('SB'), m.group('BB')]
        
        return gametype

    def readHandInfo(self, hand):
        m =  self.re_HandInfo.search(hand.string,re.DOTALL)
        #print m.groups()
        hand.handid = m.group('HID')
        hand.tablename = m.group('TABLE')
        hand.starttime = time.strptime(m.group('DATETIME'), "%H:%M:%S ET - %Y/%m/%d")
# These work, but the info is already in the Hand class - should be used for tourneys though.
#		m.group('SB')
#		m.group('BB')
#		m.group('GAMETYPE')

# Stars format (Nov 10 2008): 2008/11/07 12:38:49 CET [2008/11/07 7:38:49 ET]
# or                        : 2008/11/07 12:38:49 ET
# Not getting it in my HH files yet, so using
# 2008/11/10 3:58:52 ET
#TODO: Do conversion from GMT to ET
#TODO: Need some date functions to convert to different timezones (Date::Manip for perl rocked for this)
        #hand.starttime = "%d/%02d/%02d %d:%02d:%02d ET" %(int(m.group('YEAR')), int(m.group('MON')), int(m.group('DAY')),
                            ##int(m.group('HR')), int(m.group('MIN')), int(m.group('SEC')))
#FIXME:        hand.buttonpos = int(m.group('BUTTON'))

    def readPlayerStacks(self, hand):
        m = self.re_PlayerInfo.finditer(hand.string)
        players = []
        for a in m:
            hand.addPlayer(int(a.group('SEAT')), a.group('PNAME'), a.group('CASH'))

    def markStreets(self, hand):
        # PREFLOP = ** Dealing down cards **
        # This re fails if,  say, river is missing; then we don't get the ** that starts the river.

        if self.gametype[1] == "hold" or self.gametype[1] == "omaha":
            m =  re.search(r"\*\*\* HOLE CARDS \*\*\*(?P<PREFLOP>.+(?=\*\*\* FLOP \*\*\*)|.+)"
                       r"(\*\*\* FLOP \*\*\*(?P<FLOP> \[\S\S \S\S \S\S\].+(?=\*\*\* TURN \*\*\*)|.+))?"
                       r"(\*\*\* TURN \*\*\* \[\S\S \S\S \S\S] (?P<TURN>\[\S\S\].+(?=\*\*\* RIVER \*\*\*)|.+))?"
                       r"(\*\*\* RIVER \*\*\* \[\S\S \S\S \S\S \S\S] (?P<RIVER>\[\S\S\].+))?", hand.string,re.DOTALL)
        elif self.gametype[1] == "razz":
            m =  re.search(r"(?P<ANTES>.+(?=\*\*\* 3RD STREET \*\*\*)|.+)"
                           r"(\*\*\* 3RD STREET \*\*\*(?P<THIRD>.+(?=\*\*\* 4TH STREET \*\*\*)|.+))?"
                           r"(\*\*\* 4TH STREET \*\*\*(?P<FOURTH>.+(?=\*\*\* 5TH STREET \*\*\*)|.+))?"
                           r"(\*\*\* 5TH STREET \*\*\*(?P<FIFTH>.+(?=\*\*\* 6TH STREET \*\*\*)|.+))?"
                           r"(\*\*\* 6TH STREET \*\*\*(?P<SIXTH>.+(?=\*\*\* 7TH STREET \*\*\*)|.+))?"
                           r"(\*\*\* 7TH STREET \*\*\*(?P<SEVENTH>.+))?", hand.string,re.DOTALL)
        hand.addStreets(m)

    def readCommunityCards(self, hand, street): # street has been matched by markStreets, so exists in this hand
        if street in ('FLOP','TURN','RIVER'):   # a list of streets which get dealt community cards (i.e. all but PREFLOP)
            #print "DEBUG readCommunityCards:", street, hand.streets.group(street)
            m = self.re_Board.search(hand.streets.group(street))
            hand.setCommunityCards(street, m.group('CARDS').split(' '))


    def readBlinds(self, hand):
        try:
            m = self.re_PostSB.search(hand.string)
            hand.addBlind(m.group('PNAME'), 'small blind', m.group('SB'))
        except: # no small blind
            hand.addBlind(None, None, None)
        for a in self.re_PostBB.finditer(hand.string):
            hand.addBlind(a.group('PNAME'), 'big blind', a.group('BB'))
        for a in self.re_PostBoth.finditer(hand.string):
            hand.addBlind(a.group('PNAME'), 'small & big blinds', a.group('SBBB'))

    def readAntes(self, hand):
        print "DEBUG: reading antes"
        print "DEBUG: FIXME reading antes"

    def readBringIn(self, hand):
        print "DEBUG: reading bring in"
#        print hand.string
        m = self.re_BringIn.search(hand.string,re.DOTALL)
        print "DEBUG: Player bringing in: %s for %s" %(m.group('PNAME'),  m.group('BRINGIN'))

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
            cards = set(cards.split(' '))
            hand.addHoleCards(cards, m.group('PNAME'))

    def readPlayerCards(self, hand, street):
        #Used for stud hands - borrows the HeroCards regex for now.
        m = self.re_HeroCards.finditer(hand.streets.group(street))
        print "DEBUG: razz/stud readPlayerCards"
        print "DEBUG: STREET: %s", street
        for player in m:
            print player.groups()
            #hand.hero = m.group('PNAME')
            # "2c, qh" -> set(["2c","qc"])
            # Also works with Omaha hands.
            cards = player.group('CARDS')
            print "DEBUG: PNAME: %s CARDS: %s" %(player.group('PNAME'), player.group('CARDS'))
            cards = set(cards.split(' '))
#            hand.addHoleCards(cards, m.group('PNAME'))

    def readAction(self, hand, street):
        m = self.re_Action.finditer(hand.streets.group(street))
        for action in m:
            if action.group('ATYPE') == ' raises to':
                hand.addRaiseTo( street, action.group('PNAME'), action.group('BET') )
            elif action.group('ATYPE') == ' calls':
                hand.addCall( street, action.group('PNAME'), action.group('BET') )
            elif action.group('ATYPE') == ' bets':
                hand.addBet( street, action.group('PNAME'), action.group('BET') )
            elif action.group('ATYPE') == ' folds':
                hand.addFold( street, action.group('PNAME'))
            elif action.group('ATYPE') == ' checks':
                hand.addCheck( street, action.group('PNAME'))
            else:
                print "DEBUG: unimplemented readAction: %s %s" %(action.group('PNAME'),action.group('ATYPE'),)


    def readShowdownActions(self, hand):
        for shows in self.re_ShowdownAction.finditer(hand.string):
            cards = shows.group('CARDS')
            cards = set(cards.split(' '))
            hand.addShownCards(cards, shows.group('PNAME'))

    def readCollectPot(self,hand):
        for m in self.re_CollectPot.finditer(hand.string):
            hand.addCollectPot(player=m.group('PNAME'),pot=m.group('POT'))

    def readShownCards(self,hand):
        for m in self.re_ShownCards.finditer(hand.string):
            if m.group('CARDS') is not None:
                cards = m.group('CARDS')
                cards = set(cards.split(' '))
                hand.addShownCards(cards=cards, player=m.group('PNAME'))


if __name__ == "__main__":
    c = Configuration.Config()
    if len(sys.argv) ==  1:
        testfile = "regression-test-files/fulltilt/razz/FT20090223 Danville - $0.50-$1 Ante $0.10 - Limit Razz.txt"
    else:
        testfile = sys.argv[1]
        print "Converting: ", testfile
    e = FullTilt(c, testfile)
    e.processFile()
    print str(e)
