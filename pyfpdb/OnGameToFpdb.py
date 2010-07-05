#!/usr/bin/env python2
# -*- coding: utf-8 -*-

#    Copyright 2008-2010, Carl Gherardi
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

# OnGame HH Format

#Texas Hold'em $.5-$1 NL (real money), hand #P4-76915775-797
#Table Kuopio, 20 Sep 2008 11:59 PM

#Seat 1: .Lucchess ($4.17 in chips) 
#Seat 3: Gloff1 ($108 in chips) 
#Seat 4: far a ($13.54 in chips) 
#Seat 5: helander2222 ($49.77 in chips) 
#Seat 6: lopllopl ($62.06 in chips) 
#Seat 7: crazyhorse6 ($101.91 in chips) 
#Seat 8: peeci ($25.02 in chips) 
#Seat 9: Manuelhertz ($49 in chips) 
#Seat 10: Eurolll ($58.25 in chips) 
#ANTES/BLINDS
#helander2222 posts blind ($0.25), lopllopl posts blind ($0.50).

#PRE-FLOP
#crazyhorse6 folds, peeci folds, Manuelhertz folds, Eurolll calls $0.50, .Lucchess calls $0.50, Gloff1 folds, far a folds, helander2222 folds, lopllopl checks.

#FLOP [board cards AH,8H,KH ]
#lopllopl checks, Eurolll checks, .Lucchess checks.

#TURN [board cards AH,8H,KH,6S ]
#lopllopl checks, Eurolll checks, .Lucchess checks.

#RIVER [board cards AH,8H,KH,6S,8S ]
#lopllopl checks, Eurolll bets $1.25, .Lucchess folds, lopllopl folds.

#SHOWDOWN
#Eurolll wins $2.92.

#SUMMARY
#Dealer: far a
#Pot: $3, (including rake: $0.08)
#.Lucchess, loses $0.50
#Gloff1, loses $0
#far a, loses $0
#helander2222, loses $0.25
#lopllopl, loses $0.50
#crazyhorse6, loses $0
#peeci, loses $0
#Manuelhertz, loses $0
#Eurolll, bets $1.75, collects $2.92, net $1.17  


class OnGame(HandHistoryConverter):
    def __init__(self, config, file):
        print "Initialising OnGame converter class"
        HandHistoryConverter.__init__(self, config, file, sitename="OnGame") # Call super class init.
        self.sitename = "OnGame"
        self.setFileType("text", "cp1252")
        self.siteId   = 5 # Needs to match id entry in Sites database
        #self.rexx.setGameInfoRegex('.*Blinds \$?(?P<SB>[.0-9]+)/\$?(?P<BB>[.0-9]+)')
        self.rexx.setSplitHandRegex('\n\n\n+')
        
        #Texas Hold'em $.5-$1 NL (real money), hand #P4-76915775-797
        #Table Kuopio, 20 Sep 2008 11:59 PM
        self.rexx.setHandInfoRegex(r"Texas Hold'em \$?(?P<SB>[.0-9]+)-\$?(?P<BB>[.0-9]+) NL \(real money\), hand #(?P<HID>[-A-Z\d]+)\nTable\ (?P<TABLE>[\' \w]+), (?P<DATETIME>\d\d \w+ \d\d\d\d \d\d:\d\d (AM|PM))")
         # SB BB HID TABLE DAY MON YEAR HR12 MIN AMPM
        
        self.rexx.button_re = re.compile('#SUMMARY\nDealer: (?P<BUTTONPNAME>.*)\n')
        
        #Seat 1: .Lucchess ($4.17 in chips) 
        self.rexx.setPlayerInfoRegex('Seat (?P<SEAT>[0-9]+): (?P<PNAME>.*) \((\$(?P<CASH>[.0-9]+) in chips)\)')
        
        #ANTES/BLINDS
        #helander2222 posts blind ($0.25), lopllopl posts blind ($0.50).
        self.rexx.setPostSbRegex('(?P<PNAME>.*) posts blind \(\$?(?P<SB>[.0-9]+)\), ')
        self.rexx.setPostBbRegex('\), (?P<PNAME>.*) posts blind \(\$?(?P<BB>[.0-9]+)\).')
        self.rexx.setPostBothRegex('.*\n(?P<PNAME>.*): posts small \& big blinds \[\$? (?P<SBBB>[.0-9]+)')
        self.rexx.setHeroCardsRegex('.*\nDealt\sto\s(?P<PNAME>.*)\s\[ (?P<CARDS>.*) \]')
        
        #lopllopl checks, Eurolll checks, .Lucchess checks.
        self.rexx.setActionStepRegex('(, )?(?P<PNAME>.*?)(?P<ATYPE> bets| checks| raises| calls| folds)( \$(?P<BET>\d*\.?\d*))?( and is all-in)?')
        
        #Uchilka shows [ KC,JD ]
        self.rexx.setShowdownActionRegex('(?P<PNAME>.*) shows \[ (?P<CARDS>.+) \]')
        
        # TODO: read SUMMARY correctly for collected pot stuff.
        #Uchilka, bets $11.75, collects $23.04, net $11.29
        self.rexx.setCollectPotRegex('(?P<PNAME>.*), bets.+, collects \$(?P<POT>\d*\.?\d*), net.* ')
        self.rexx.sits_out_re = re.compile('(?P<PNAME>.*) sits out')
        self.rexx.compileRegexes()

    def readSupportedGames(self):
        pass

    def determineGameType(self):
        # Cheating with this regex, only support nlhe at the moment
        gametype = ["ring", "hold", "nl"]

        m = self.rexx.hand_info_re.search(self.obs)
        gametype = gametype + [m.group('SB')]
        gametype = gametype + [m.group('BB')]
        
        return gametype

    def readHandInfo(self, hand):
        m =  self.rexx.hand_info_re.search(hand.string)
        hand.handid = m.group('HID')
        hand.tablename = m.group('TABLE')
        #hand.buttonpos = self.rexx.button_re.search(hand.string).group('BUTTONPNAME')
# These work, but the info is already in the Hand class - should be used for tourneys though.
#       m.group('SB')
#       m.group('BB')
#       m.group('GAMETYPE')

# Believe Everleaf time is GMT/UTC, no transation necessary
# Stars format (Nov 10 2008): 2008/11/07 12:38:49 CET [2008/11/07 7:38:49 ET]
# or                        : 2008/11/07 12:38:49 ET
# Not getting it in my HH files yet, so using
# 2008/11/10 3:58:52 ET
#TODO: Do conversion from GMT to ET
#TODO: Need some date functions to convert to different timezones (Date::Manip for perl rocked for this)
        
        hand.starttime = time.strptime(m.group('DATETIME'), "%d %b %Y %I:%M %p")
        #hand.starttime = "%d/%02d/%02d %d:%02d:%02d ET" %(int(m.group('YEAR')), int(m.group('MON')), int(m.group('DAY')),
                            #int(m.group('HR')), int(m.group('MIN')), int(m.group('SEC')))

    def readPlayerStacks(self, hand):
        m = self.rexx.player_info_re.finditer(hand.string)
        players = []
        for a in m:
            hand.addPlayer(int(a.group('SEAT')), a.group('PNAME'), a.group('CASH'))

    def markStreets(self, hand):
        # PREFLOP = ** Dealing down cards **
        # This re fails if,  say, river is missing; then we don't get the ** that starts the river.
        #m = re.search('(\*\* Dealing down cards \*\*\n)(?P<PREFLOP>.*?\n\*\*)?( Dealing Flop \*\* \[ (?P<FLOP1>\S\S), (?P<FLOP2>\S\S), (?P<FLOP3>\S\S) \])?(?P<FLOP>.*?\*\*)?( Dealing Turn \*\* \[ (?P<TURN1>\S\S) \])?(?P<TURN>.*?\*\*)?( Dealing River \*\* \[ (?P<RIVER1>\S\S) \])?(?P<RIVER>.*)', hand.string,re.DOTALL)

        m =  re.search(r"PRE-FLOP(?P<PREFLOP>.+(?=FLOP)|.+(?=SHOWDOWN))"
                       r"(FLOP (?P<FLOP>\[board cards .+ \].+(?=TURN)|.+(?=SHOWDOWN)))?"
                       r"(TURN (?P<TURN>\[board cards .+ \].+(?=RIVER)|.+(?=SHOWDOWN)))?"
                       r"(RIVER (?P<RIVER>\[board cards .+ \].+(?=SHOWDOWN)))?", hand.string,re.DOTALL)

        hand.addStreets(m)
            

    def readCommunityCards(self, hand, street):
        self.rexx.board_re = re.compile(r"\[board cards (?P<CARDS>.+) \]")
        print hand.streets.group(street)
        if street in ('FLOP','TURN','RIVER'):   # a list of streets which get dealt community cards (i.e. all but PREFLOP)
            m = self.rexx.board_re.search(hand.streets.group(street))
            hand.setCommunityCards(street, m.group('CARDS').split(','))

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
            cards = set(cards.split(','))
            hand.addHoleCards(cards, m.group('PNAME'))

    def readAction(self, hand, street):
        m = self.rexx.action_re.finditer(hand.streets.group(street))
        for action in m:
            if action.group('ATYPE') == ' raises':
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
                #hand.actions[street] += [[action.group('PNAME'), action.group('ATYPE')]]
        # TODO: Everleaf does not record uncalled bets.

    def readShowdownActions(self, hand):
        for shows in self.rexx.showdown_action_re.finditer(hand.string):            
            cards = shows.group('CARDS')
            cards = set(cards.split(','))
            hand.addShownCards(cards, shows.group('PNAME'))

    def readCollectPot(self,hand):
        for m in self.rexx.collect_pot_re.finditer(hand.string):
            hand.addCollectPot(player=m.group('PNAME'),pot=m.group('POT'))

    def readShownCards(self,hand):
        return
        #for m in self.rexx.collect_pot_re.finditer(hand.string):
            #if m.group('CARDS') is not None:
                #cards = m.group('CARDS')
                #cards = set(cards.split(','))
                #hand.addShownCards(cards=None, player=m.group('PNAME'), holeandboard=cards)

 


if __name__ == "__main__":
    c = Configuration.Config()
    if len(sys.argv) ==  1:
        testfile = "regression-test-files/ongame/nlhe/ong NLH handhq_0.txt"
    else:
        testfile = sys.argv[1]
    e = OnGame(c, testfile)
    e.processFile()
    print str(e)
