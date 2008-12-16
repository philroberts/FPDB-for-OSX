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

# FullTilt HH Format

#Full Tilt Poker Game #9403951181: Table CR - tay - $0.05/$0.10 - No Limit Hold'em - 9:40:20 ET - 2008/12/09
#Seat 1: rigoise ($15.95)
#Seat 2: K2dream ($6.70)
#Seat 4: ravens2216 ($10)
#Seat 5: rizkouner ($4)
#Seat 6: Sorrowful ($8.35)
#rigoise posts the small blind of $0.05
#K2dream posts the big blind of $0.10
#5 seconds left to act
#rizkouner posts $0.10
#The button is in seat #6
#*** HOLE CARDS ***
#Dealt to Sorrowful [8h Qc]
#ravens2216 folds
#rizkouner checks
#Sorrowful has 15 seconds left to act
#Sorrowful folds
#rigoise folds
#K2dream checks
#*** FLOP *** [9d Kc 5c]
#K2dream checks
#rizkouner checks
#*** TURN *** [9d Kc 5c] [5h]
#K2dream has 15 seconds left to act
#K2dream bets $0.20
#rizkouner calls $0.20
#*** RIVER *** [9d Kc 5c 5h] [6h]
#K2dream checks
#rizkouner has 15 seconds left to act
#rizkouner bets $0.20
#K2dream folds
#Uncalled bet of $0.20 returned to rizkouner
#rizkouner mucks
#rizkouner wins the pot ($0.60)
#*** SUMMARY ***
#Total pot $0.65 | Rake $0.05
#Board: [9d Kc 5c 5h 6h]
#Seat 1: rigoise (small blind) folded before the Flop
#Seat 2: K2dream (big blind) folded on the River
#Seat 4: ravens2216 didn't bet (folded)
#Seat 5: rizkouner collected ($0.60), mucked
#Seat 6: Sorrowful (button) didn't bet (folded)
#Seat N: rizkouner (button) showed [Jh Ah] and won ($0.70) with a pair of Threes

class FullTilt(HandHistoryConverter):
    def __init__(self, config, file):
        print "Initialising FullTilt converter class"
        HandHistoryConverter.__init__(self, config, file, sitename="FullTilt") # Call super class init.
        self.sitename = "FullTilt"
        self.setFileType("text", "cp1252")
        self.rexx.setGameInfoRegex('- \$?(?P<SB>[.0-9]+)/\$?(?P<BB>[.0-9]+) -')
        self.rexx.setSplitHandRegex('\n\n+')
        self.rexx.setHandInfoRegex('.*#(?P<HID>[0-9]+): Table (?P<TABLE>[- a-zA-Z]+) - \$?(?P<SB>[.0-9]+)/\$?(?P<BB>[.0-9]+) - (?P<GAMETYPE>[a-zA-Z\' ]+) - (?P<HR>[0-9]+):(?P<MIN>[0-9]+):(?P<SEC>[0-9]+) ET - (?P<YEAR>[0-9]+)/(?P<MON>[0-9]+)/(?P<DAY>[0-9]+)')
#        self.rexx.setHandInfoRegex('.*#(?P<HID>[0-9]+): Table (?P<TABLE>[ a-zA-Z]+) - \$?(?P<SB>[.0-9]+)/\$?(?P<BB>[.0-9]+) - (?P<GAMETYPE>.*) - (?P<HR>[0-9]+):(?P<MIN>[0-9]+) ET - (?P<YEAR>[0-9]+)/(?P<MON>[0-9]+)/(?P<DAY>[0-9]+)Table (?P<TABLE>[ a-zA-Z]+)\nSeat (?P<BUTTON>[0-9]+)')
        self.rexx.button_re = re.compile('The button is in seat #(?P<BUTTON>\d+)')
        self.rexx.setPlayerInfoRegex('Seat (?P<SEAT>[0-9]+): (?P<PNAME>.*) \(\$(?P<CASH>[.0-9]+)\)\n')
        self.rexx.setPostSbRegex('.*\n(?P<PNAME>.*) posts the small blind of \$?(?P<SB>[.0-9]+)')
        self.rexx.setPostBbRegex('.*\n(?P<PNAME>.*) posts (the big blind of )?\$?(?P<BB>[.0-9]+)')
        self.rexx.setPostBothRegex('.*\n(?P<PNAME>.*) posts small \& big blinds \[\$? (?P<SBBB>[.0-9]+)')
        self.rexx.setHeroCardsRegex('.*\nDealt\sto\s(?P<PNAME>.*)\s\[(?P<CARDS>.*)\]')
        self.rexx.setActionStepRegex('.*\n(?P<PNAME>.*)(?P<ATYPE> bets| checks| raises to| calls| folds)(\s\$(?P<BET>[.\d]+))?')
        self.rexx.setShowdownActionRegex('.*\n(?P<PNAME>.*) shows \[(?P<CARDS>.*)\]')
        self.rexx.setCollectPotRegex(r"Seat (?P<SEAT>[0-9]+): (?P<PNAME>.*?) (\(button\) |\(small blind\) |\(big blind\) )?(collected|showed \[.*\] and won) \(\$(?P<POT>[.\d]+)\)(, mucked| with.*)")
        self.rexx.shown_cards_re = re.compile('Seat (?P<SEAT>[0-9]+): (?P<PNAME>.*) \(.*\) showed \[(?P<CARDS>.*)\].*')
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
        m =  self.rexx.hand_info_re.search(hand.string,re.DOTALL)
        #print m.groups()
        hand.handid = m.group('HID')
        hand.tablename = m.group('TABLE')
        hand.buttonpos = int(self.rexx.button_re.search(hand.string).group('BUTTON'))
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
        hand.starttime = "%d/%02d/%02d %d:%02d:%02d ET" %(int(m.group('YEAR')), int(m.group('MON')), int(m.group('DAY')),
                            int(m.group('HR')), int(m.group('MIN')), int(m.group('SEC')))
#FIXME:        hand.buttonpos = int(m.group('BUTTON'))

    def readPlayerStacks(self, hand):
        m = self.rexx.player_info_re.finditer(hand.string)
        players = []
        for a in m:
            hand.addPlayer(int(a.group('SEAT')), a.group('PNAME'), a.group('CASH'))

    def markStreets(self, hand):
        # PREFLOP = ** Dealing down cards **
        # This re fails if,  say, river is missing; then we don't get the ** that starts the river.

        m =  re.search(r"\*\*\* HOLE CARDS \*\*\*(?P<PREFLOP>.+(?=\*\*\* FLOP \*\*\*)|.+)"
                       r"(\*\*\* FLOP \*\*\*(?P<FLOP> \[\S\S \S\S \S\S\].+(?=\*\*\* TURN \*\*\*)|.+))?"
                       r"(\*\*\* TURN \*\*\* \[\S\S \S\S \S\S] (?P<TURN>\[\S\S\].+(?=\*\*\* RIVER \*\*\*)|.+))?"
                       r"(\*\*\* RIVER \*\*\* \[\S\S \S\S \S\S \S\S] (?P<RIVER>\[\S\S\].+))?", hand.string,re.DOTALL)

        hand.addStreets(m)

    def readCommunityCards(self, hand, street): # street has been matched by markStreets, so exists in this hand
        if street in ('FLOP','TURN','RIVER'):   # a list of streets which get dealt community cards (i.e. all but PREFLOP)
            self.rexx.board_re = re.compile(r"\[(?P<CARDS>.+)\]")
            #print "DEBUG readCommunityCards:", street, hand.streets.group(street)
            m = self.rexx.board_re.search(hand.streets.group(street))
            hand.setCommunityCards(street, m.group('CARDS').split(' '))


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
            cards = set(cards.split(' '))
            hand.addHoleCards(cards, m.group('PNAME'))

    def readAction(self, hand, street):
        m = self.rexx.action_re.finditer(hand.streets.group(street))
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
        for shows in self.rexx.showdown_action_re.finditer(hand.string):            
            cards = shows.group('CARDS')
            cards = set(cards.split(' '))
            hand.addShownCards(cards, shows.group('PNAME'))

    def readCollectPot(self,hand):
        for m in self.rexx.collect_pot_re.finditer(hand.string):
            hand.addCollectPot(player=m.group('PNAME'),pot=m.group('POT'))

    def readShownCards(self,hand):
        for m in self.rexx.shown_cards_re.finditer(hand.string):
            if m.group('CARDS') is not None:
                cards = m.group('CARDS')
                cards = set(cards.split(' '))
                hand.addShownCards(cards=cards, player=m.group('PNAME'))


if __name__ == "__main__":
    c = Configuration.Config()
    if len(sys.argv) ==  1:
        testfile = "regression-test-files/FT20081209 CR - tay - $0.05-$0.10 - No Limit Hold'em.txt"
    else:
        testfile = sys.argv[1]
        print "Converting: ", testfile
    e = FullTilt(c, testfile)
    e.processFile()
    print str(e)
