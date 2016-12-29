#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Copyright 2008-2011, Carl Gherardi
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

import L10n
_ = L10n.get_translation()

import sys
from HandHistoryConverter import *

# Betfair HH format

class Betfair(HandHistoryConverter):

    sitename = 'Betfair'
    filetype = "text"
    codepage = "cp1252"
    siteId   = 7 # Needs to match id entry in Sites database

    # Static regexes
    re_GameInfo      = re.compile("^(?P<LIMIT>NL|PL|) (?P<CURRENCY>\$|)?(?P<SB>[.0-9]+)/\$?(?P<BB>[.0-9]+) (?P<GAME>(Texas Hold\'em|Omaha Hi|Omaha|Razz))", re.MULTILINE)
    re_Identify      = re.compile(u'\*{5}\sBetfair\sPoker\sHand\sHistory\sfor\sGame\s\d+\s')
    re_SplitHands    = re.compile(r'\n\n+')
    re_HandInfo      = re.compile("\*\*\*\*\* Betfair Poker Hand History for Game (?P<HID>[0-9]+) \*\*\*\*\*\n(?P<LIMIT>NL|PL|) (?P<CURRENCY>\$|)?(?P<SB>[.0-9]+)/\$?(?P<BB>[.0-9]+) (?P<GAMETYPE>(Texas Hold\'em|Omaha|Razz)) - (?P<DATETIME>[a-zA-Z]+, [a-zA-Z]+ \d+, \d\d:\d\d:\d\d GMT \d\d\d\d)\nTable (?P<TABLE>[ a-zA-Z0-9]+) \d-max \(Real Money\)\nSeat (?P<BUTTON>[0-9]+)", re.MULTILINE)
    re_Button        = re.compile(ur"^Seat (?P<BUTTON>\d+) is the button", re.MULTILINE)
    re_PlayerInfo    = re.compile("Seat (?P<SEAT>[0-9]+): (?P<PNAME>.*)\s\(\s(\$(?P<CASH>[.0-9]+)) \)")
    re_Board         = re.compile(ur"\[ (?P<CARDS>.+) \]")


    def compilePlayerRegexs(self,  hand):
        players = set([player[1] for player in hand.players])
        if not players <= self.compiledPlayers: # x <= y means 'x is subset of y'
            # we need to recompile the player regexs.
            self.compiledPlayers = players
            player_re = "(?P<PNAME>" + "|".join(map(re.escape, players)) + ")"
            log.debug("player_re: " + player_re)
            self.re_PostSB          = re.compile("^%s posts small blind \[\$?(?P<SB>[.0-9]+)" % player_re, re.MULTILINE)
            self.re_PostBB          = re.compile("^%s posts big blind \[\$?(?P<BB>[.0-9]+)" % player_re, re.MULTILINE)
            self.re_Antes           = re.compile("^%s antes asdf sadf sadf" % player_re, re.MULTILINE)
            self.re_BringIn         = re.compile("^%s antes asdf sadf sadf" % player_re, re.MULTILINE)
            self.re_PostBoth        = re.compile("^%s posts small \& big blinds \[\$?(?P<SBBB>[.0-9]+)" % player_re, re.MULTILINE)
            self.re_HeroCards       = re.compile("^Dealt to %s \[ (?P<CARDS>.*) \]" % player_re, re.MULTILINE)
            self.re_Action          = re.compile("^%s (?P<ATYPE>bets|checks|raises to|raises|calls|folds)(\s\[\$(?P<BET>[.\d]+)\])?" % player_re, re.MULTILINE)
            self.re_ShowdownAction  = re.compile("^%s shows \[ (?P<CARDS>.*) \]" % player_re, re.MULTILINE)
            self.re_CollectPot      = re.compile("^%s wins \$(?P<POT>[.\d]+) (.*?\[ (?P<CARDS>.*?) \])?" % player_re, re.MULTILINE)
            self.re_SitsOut         = re.compile("^%s sits out" % player_re, re.MULTILINE)
            self.re_ShownCards      = re.compile(r"%s (?P<SEAT>[0-9]+) (?P<CARDS>adsfasdf)" % player_re, re.MULTILINE)

    def readSupportedGames(self):
        return [["ring", "hold", "nl"],
                ["ring", "hold", "pl"]
               ]

    def determineGameType(self, handText):
        info = {'type':'ring'}

        m = self.re_GameInfo.search(handText)
        if not m:
            tmp = handText[0:200]
            log.error(_("BetfairToFpdb.determineGameType: '%s'") % tmp)
            raise FpdbParseError

        mg = m.groupdict()

        # translations from captured groups to our info strings
        limits = { 'NL':'nl', 'PL':'pl', 'Limit':'fl' }
        games = {              # base, category
                  "Texas Hold'em" : ('hold','holdem'),
                       'Omaha Hi' : ('hold','omahahi'),
                          'Omaha' : ('hold','omahahi'),
                           'Razz' : ('stud','razz'),
                    '7 Card Stud' : ('stud','studhi')
               }
        currencies = { u' €':'EUR', '$':'USD', '':'T$' }
        if 'LIMIT' in mg:
            info['limitType'] = limits[mg['LIMIT']]
        if 'GAME' in mg:
            (info['base'], info['category']) = games[mg['GAME']]
        if 'SB' in mg:
            info['sb'] = mg['SB']
        if 'BB' in mg:
            info['bb'] = mg['BB']
        if 'CURRENCY' in mg:
            info['currency'] = currencies[mg['CURRENCY']]

        return info

    def readHandInfo(self, hand):
        m = self.re_HandInfo.search(hand.handText)
        if(m == None):
            tmp = hand.handText[0:200]
            log.error(_("BetfairToFpdb.readHandInfo: '%s'") % tmp)
            raise FpdbParseError
        log.debug("HID %s, Table %s" % (m.group('HID'),  m.group('TABLE')))
        hand.handid = m.group('HID')
        hand.tablename = m.group('TABLE')
        hand.startTime = datetime.datetime.strptime(m.group('DATETIME'), "%A, %B %d, %H:%M:%S GMT %Y")
        #hand.buttonpos = int(m.group('BUTTON'))

    def readPlayerStacks(self, hand):
        m = self.re_PlayerInfo.finditer(hand.handText)
        for a in m:
            hand.addPlayer(int(a.group('SEAT')), a.group('PNAME'), a.group('CASH'))

        #Shouldn't really dip into the Hand object, but i've no idea how to tell the length of iter m
        if len(hand.players) < 2:
            log.info(_("Less than 2 players found in hand %s.") % hand.handid)

    def markStreets(self, hand):
        m =  re.search(r"\*\* Dealing down cards \*\*(?P<PREFLOP>.+(?=\*\* Dealing Flop \*\*)|.+)"
                       r"(\*\* Dealing Flop \*\*(?P<FLOP> \[ \S\S, \S\S, \S\S \].+(?=\*\* Dealing Turn \*\*)|.+))?"
                       r"(\*\* Dealing Turn \*\*(?P<TURN> \[ \S\S \].+(?=\*\* Dealing River \*\*)|.+))?"
                       r"(\*\* Dealing River \*\*(?P<RIVER> \[ \S\S \].+))?", hand.handText,re.DOTALL)

        hand.addStreets(m)
            

    def readCommunityCards(self, hand, street): # street has been matched by markStreets, so exists in this hand
        if street in ('FLOP','TURN','RIVER'):   # a list of streets which get dealt community cards (i.e. all but PREFLOP)
            m = self.re_Board.search(hand.streets[street])
            hand.setCommunityCards(street, m.group('CARDS').split(', '))

    def readBlinds(self, hand):
        try:
            m = self.re_PostSB.search(hand.handText)
            hand.addBlind(m.group('PNAME'), 'small blind', m.group('SB'))
        except: # no small blind
            hand.addBlind(None, None, None)
        for a in self.re_PostBB.finditer(hand.handText):
            hand.addBlind(a.group('PNAME'), 'big blind', a.group('BB'))
        for a in self.re_PostBoth.finditer(hand.handText):
            hand.addBlind(a.group('PNAME'), 'small & big blinds', a.group('SBBB'))

    def readAntes(self, hand):
        log.debug("reading antes")
        m = self.re_Antes.finditer(hand.handText)
        for player in m:
            log.debug("hand.addAnte(%s,%s)" %(player.group('PNAME'), player.group('ANTE')))
            hand.addAnte(player.group('PNAME'), player.group('ANTE'))

    def readBringIn(self, hand):
        m = self.re_BringIn.search(hand.handText,re.DOTALL)
        if m:
            log.debug(_("Player bringing in: %s for %s") % (m.group('PNAME'),  m.group('BRINGIN')))
            hand.addBringIn(m.group('PNAME'),  m.group('BRINGIN'))
        else:
            log.warning(_("No bringin found"))

    def readButton(self, hand):
        hand.buttonpos = int(self.re_Button.search(hand.handText).group('BUTTON'))

    def readHoleCards(self, hand):
        #    streets PREFLOP, PREDRAW, and THIRD are special cases beacause
        #    we need to grab hero's cards
        for street in ('PREFLOP', 'DEAL'):
            if street in hand.streets.keys():
                m = self.re_HeroCards.finditer(hand.streets[street])
                for found in m:
                    hand.hero = found.group('PNAME')
                    newcards = [c.strip() for c in found.group('CARDS').split(',')]
                    hand.addHoleCards(street, hand.hero, closed=newcards, shown=False, mucked=False, dealt=True)

    def readStudPlayerCards(self, hand, street):
        # balh blah blah
        pass

    def readAction(self, hand, street):
        m = self.re_Action.finditer(hand.streets[street])
        for action in m:
            if action.group('ATYPE') == 'folds':
                hand.addFold( street, action.group('PNAME'))
            elif action.group('ATYPE') == 'checks':
                hand.addCheck( street, action.group('PNAME'))
            elif action.group('ATYPE') == 'calls':
                hand.addCall( street, action.group('PNAME'), action.group('BET') )
            elif action.group('ATYPE') == 'bets':
                hand.addBet( street, action.group('PNAME'), action.group('BET') )
            elif action.group('ATYPE') == 'raises to':
                hand.addRaiseTo( street, action.group('PNAME'), action.group('BET') )
            else:
                sys.stderr.write(_("DEBUG:") + " " + _("Unimplemented %s: '%s' '%s'") % ("readAction", action.group('PNAME'), action.group('ATYPE')))


    def readShowdownActions(self, hand):
        for shows in self.re_ShowdownAction.finditer(hand.handText):
            cards = shows.group('CARDS')
            cards = cards.split(', ')
            hand.addShownCards(cards, shows.group('PNAME'))

    def readCollectPot(self,hand):
        for m in self.re_CollectPot.finditer(hand.handText):
            hand.addCollectPot(player=m.group('PNAME'),pot=m.group('POT'))

    def readShownCards(self,hand):
        for m in self.re_ShownCards.finditer(hand.handText):
            if m.group('CARDS') is not None:
                cards = m.group('CARDS')
                cards = cards.split(', ')
                hand.addShownCards(cards=None, player=m.group('PNAME'), holeandboard=cards)
