#!/usr/bin/env python
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
from decimal import Decimal

import locale
lang=locale.getdefaultlocale()[0][0:2]
if lang=="en":
    def _(string): return string
else:
    import gettext
    try:
        trans = gettext.translation("fpdb", localedir="locale", languages=[lang])
        trans.install()
    except IOError:
        def _(string): return string

# OnGame HH Format

class OnGame(HandHistoryConverter):
    sitename = "OnGame"
    filetype = "text"
    codepage = ("utf8", "cp1252")
    siteId   = 5 # Needs to match id entry in Sites database

    substitutions = {
                     'LEGAL_ISO' : "USD|EUR|GBP|CAD|FPP",    # legal ISO currency codes
                            'LS' : "\$|\xe2\x82\xac|"        # legal currency symbols - Euro(cp1252, utf-8)
                    }

    limits = { 'NO LIMIT':'nl', 'LIMIT':'fl'}

    games = {                          # base, category
                          "TEXAS_HOLDEM" : ('hold','holdem'),
             #                   'Omaha' : ('hold','omahahi'),
             #             'Omaha Hi/Lo' : ('hold','omahahilo'),
             #                    'Razz' : ('stud','razz'),
             #                    'RAZZ' : ('stud','razz'),
             #             '7 Card Stud' : ('stud','studhi'),
             #       '7 Card Stud Hi/Lo' : ('stud','studhilo'),
             #                  'Badugi' : ('draw','badugi'),
             # 'Triple Draw 2-7 Lowball' : ('draw','27_3draw'),
             #             '5 Card Draw' : ('draw','fivedraw')
               }

        #self.rexx.setGameInfoRegex('.*Blinds \$?(?P<SB>[.0-9]+)/\$?(?P<BB>[.0-9]+)')
    # Static regexes
    re_SplitHands = re.compile('\n\n\n+')

    # ***** History for hand R5-75443872-57 *****
    # Start hand: Wed Aug 18 19:29:10 GMT+0100 2010
    # Table: someplace [75443872] (LIMIT TEXAS_HOLDEM 0.50/1, Real money)
    re_HandInfo = re.compile(u"""
            \*\*\*\*\*\sHistory\sfor\shand\s(?P<HID>[-A-Z\d]+).*
            Start\shand:\s(?P<DATETIME>.*)
            Table:\s(?P<TABLE>[\'\w]+)\s\[\d+\]\s\(
            (
            (?P<LIMIT>No\sLimit|Limit|LIMIT|Pot\sLimit)\s
            (?P<GAME>TEXAS_HOLDEM|RAZZ)\s
            (?P<SB>[.0-9]+)/
            (?P<BB>[.0-9]+)
            )?
            """ % substitutions, re.MULTILINE|re.DOTALL|re.VERBOSE)
        
    #    self.rexx.button_re = re.compile('#SUMMARY\nDealer: (?P<BUTTONPNAME>.*)\n')
        
    #Seat 1: .Lucchess ($4.17 in chips) 
    re_PlayerInfo = re.compile(u'Seat (?P<SEAT>[0-9]+): (?P<PNAME>.*) \((\$(?P<CASH>[.0-9]+) in chips)\)')
        
    #ANTES/BLINDS
    #helander2222 posts blind ($0.25), lopllopl posts blind ($0.50).
    re_PostSB    = re.compile('(?P<PNAME>.*) posts blind \(\$?(?P<SB>[.0-9]+)\), ')
    re_PostBB    = re.compile('\), (?P<PNAME>.*) posts blind \(\$?(?P<BB>[.0-9]+)\).')
    re_PostBoth  = re.compile('.*\n(?P<PNAME>.*): posts small \& big blinds \[\$? (?P<SBBB>[.0-9]+)')
    re_HeroCards = re.compile('.*\nDealt\sto\s(?P<PNAME>.*)\s\[ (?P<CARDS>.*) \]')
        
    #lopllopl checks, Eurolll checks, .Lucchess checks.
    re_Action = re.compile('(, )?(?P<PNAME>.*?)(?P<ATYPE> bets| checks| raises| calls| folds)( \$(?P<BET>\d*\.?\d*))?( and is all-in)?')
    re_Board = re.compile(r"\[board cards (?P<CARDS>.+) \]")
        
    #Uchilka shows [ KC,JD ]
    re_ShowdownAction = re.compile('(?P<PNAME>.*) shows \[ (?P<CARDS>.+) \]')
        
    # TODO: read SUMMARY correctly for collected pot stuff.
    #Uchilka, bets $11.75, collects $23.04, net $11.29
    re_CollectPot = re.compile('(?P<PNAME>.*), bets.+, collects \$(?P<POT>\d*\.?\d*), net.* ')
    re_sitsOut    = re.compile('(?P<PNAME>.*) sits out')

    def readSupportedGames(self):
        return [
                ["ring", "hold", "fl"],
                ["ring", "hold", "nl"],
               ]

    def determineGameType(self, handText):
        # Inspect the handText and return the gametype dict
        # gametype dict is: {'limitType': xxx, 'base': xxx, 'category': xxx}
        info = {}

        m = self.re_HandInfo.search(handText)
        if not m:
            tmp = handText[0:100]
            log.error(_("determineGameType: Unable to recognise gametype from: '%s'") % tmp)
            log.error(_("determineGameType: Raising FpdbParseError"))
            raise FpdbParseError(_("Unable to recognise gametype from: '%s'") % tmp)

        mg = m.groupdict()

        info['type'] = 'ring'
        info['currency'] = 'USD'

        if 'LIMIT' in mg:
            info['limitType'] = self.limits[mg['LIMIT']]
        if 'GAME' in mg:
            (info['base'], info['category']) = self.games[mg['GAME']]
        if 'SB' in mg:
            info['sb'] = mg['SB']
        if 'BB' in mg:
            info['bb'] = mg['BB']

        return info

    def readHandInfo(self, hand):
        m =  self.re_HandInfo.search(hand.string)
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
        
        hand.startTime = time.strptime(m.group('DATETIME'), "%d %b %Y %I:%M %p")
        #hand.starttime = "%d/%02d/%02d %d:%02d:%02d ET" %(int(m.group('YEAR')), int(m.group('MON')), int(m.group('DAY')),
                            #int(m.group('HR')), int(m.group('MIN')), int(m.group('SEC')))

    def readPlayerStacks(self, hand):
        m = self.re_PlayerInf.finditer(hand.string)
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
        print hand.streets.group(street)
        if street in ('FLOP','TURN','RIVER'):   # a list of streets which get dealt community cards (i.e. all but PREFLOP)
            m = self.re_Board.search(hand.streets.group(street))
            hand.setCommunityCards(street, m.group('CARDS').split(','))

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
            cards = set(cards.split(','))
            hand.addHoleCards(cards, m.group('PNAME'))

    def readAction(self, hand, street):
        m = self.re_Action.finditer(hand.streets.group(street))
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
        for shows in self.re_ShowdownAction.finditer(hand.string):
            cards = shows.group('CARDS')
            cards = set(cards.split(','))
            hand.addShownCards(cards, shows.group('PNAME'))

    def readCollectPot(self,hand):
        for m in self.re_CollectPot.finditer(hand.string):
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
