#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Copyright 2011, Carl Gherardi
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
import logging
from HandHistoryConverter import *
from decimal import Decimal


class Everest(HandHistoryConverter):
    sitename = "Everest"
    filetype = "text"
    codepage = "utf8"
    siteID   = 15

    substitutions = {
                        'LS' : u"\$|\xe2\x82\xac|\u20ac|",
                       'TAB' : u"-\u2013'\s\da-zA-Z",       # legal characters for tablename
                    }

    # Static regexes
    re_SplitHands = re.compile(r'</HAND>\n+(?=<HAND)')
    re_TailSplitHands = re.compile(r'(</game>)')
    re_GameInfo = re.compile(u"""<SESSION\stime="\d+"\s
                                    tableName="(?P<TABLE>[%(TAB)s]+)"\s
                                    id="[\d\.]+"\s
                                    type="(?P<TYPE>[a-zA-Z ]+)"\s
                                    money="(?P<CURRENCY>[%(LS)s])"\s
                                    screenName="[a-zA-Z]+"\s
                                    game="(?P<GAME>[-a-zA-Z ]+)"\s
                                    gametype="(?P<LIMIT>[-a-zA-Z ]+)"/>
                                """ % substitutions, re.VERBOSE|re.MULTILINE)
    re_HandInfo = re.compile(r'<HAND time="(?P<DATETIME>[0-9]+)" id="(?P<HID>[0-9]+)" index="\d+" blinds="((?P<SB>\d+) (?P<CURRENCY>[%(LS)s])/(?P<BB>\d+))' % substitutions, re.MULTILINE)
    re_Button = re.compile(r'<DEALER position="(?P<BUTTON>[0-9]+)"\/>')
    re_PlayerInfo = re.compile(r'<SEAT position="(?P<SEAT>[0-9]+)" name="(?P<PNAME>.+)" balance="(?P<CASH>[.0-9]+)"/>', re.MULTILINE)
    re_Board = re.compile(r'(?P<CARDS>.+)<\/COMMUNITY>', re.MULTILINE)

    # The following are also static regexes: there is no need to call
    # compilePlayerRegexes (which does nothing), since players are identified
    # not by name but by seat number
    re_PostSB = re.compile(r'<event sequence="[0-9]+" type="(SMALL_BLIND|RETURN_BLIND)" (?P<TIMESTAMP>timestamp="[0-9]+" )?player="(?P<PSEAT>[0-9])" amount="(?P<SB>[.0-9]+)"/>', re.MULTILINE)
    re_PostBB = re.compile(r'<event sequence="[0-9]+" type="(BIG_BLIND|INITIAL_BLIND)" (?P<TIMESTAMP>timestamp="[0-9]+" )?player="(?P<PSEAT>[0-9])" amount="(?P<BB>[.0-9]+)"/>', re.MULTILINE)
    re_PostBoth = re.compile(r'<event sequence="[0-9]+" type="(RETURN_BLIND)" player="(?P<PSEAT>[0-9])" amount="(?P<SBBB>[.0-9]+)"/>', re.MULTILINE)
    #re_Antes = ???
    #re_BringIn = ???
    re_HeroCards = re.compile(r'<cards type="HOLE" cards="(?P<CARDS>.+)" player="(?P<PSEAT>[0-9])"', re.MULTILINE)
    re_Action = re.compile(r'<event sequence="[0-9]+" type="(?P<ATYPE>FOLD|CHECK|CALL|BET|RAISE|ALL_IN|SIT_OUT)" (?P<TIMESTAMP>timestamp="[0-9]+" )?player="(?P<PSEAT>[0-9])"( amount="(?P<BET>[.0-9]+)")?/>', re.MULTILINE)
    re_ShowdownAction = re.compile(r'<cards type="SHOWN" cards="(?P<CARDS>..,..)" player="(?P<PSEAT>[0-9])"/>', re.MULTILINE)
    re_CollectPot = re.compile(r'<winner amount="(?P<POT>[.0-9]+)" uncalled="(true|false)" potnumber="[0-9]+" player="(?P<PSEAT>[0-9])"', re.MULTILINE)
    re_SitsOut = re.compile(r'<event sequence="[0-9]+" type="SIT_OUT" player="(?P<PSEAT>[0-9])"/>', re.MULTILINE)
    re_ShownCards = re.compile(r'<cards type="(SHOWN|MUCKED)" cards="(?P<CARDS>..,..)" player="(?P<PSEAT>[0-9])"/>', re.MULTILINE)

    def compilePlayerRegexs(self, hand):
        pass

    def playerNameFromSeatNo(self, seatNo, hand):
        # This special function is required because Carbon Poker records
        # actions by seat number, not by the player's name
        for p in hand.players:
            if p[0] == int(seatNo):
                return p[1]

    def readSupportedGames(self):
        return [
                ["ring", "hold", "nl"],
                ["ring", "hold", "pl"],
                #["tour", "hold", "nl"]
               ]

    def determineGameType(self, handText):
        m = self.re_GameInfo.search(handText)
        m2 = self.re_HandInfo.search(handText)
        if not m:
            # Information about the game type appears only at the beginning of
            # a hand history file; hence it is not supplied with the second
            # and subsequent hands. In these cases we use the value previously
            # stored.
            try:
                self.info
                return self.info
            except AttributeError:
                tmp = handText[0:100]
                log.error(_("determineGameType: Unable to recognise gametype from: '%s'") % tmp)
                log.error(_("determineGameType: Raising FpdbParseError"))
                raise FpdbParseError(_("Unable to recognise gametype from: '%s'") % tmp)

        if not m2:
            tmp = handText[0:100]
            raise FpdbParseError(_("Unable to recognise handinfo from: '%s'") % tmp)

        self.info = {}
        mg = m.groupdict()
        mg.update(m2.groupdict())
        print "DEBUG: mg: %s" % mg

        limits = { 'No Limit':'nl', 'No Limit ':'nl', 'Limit':'fl', 'pot-limit':'pl' }
        games = {              # base, category
                    'Holdem' : ('hold','holdem'),
         'Holdem Tournament' : ('hold','holdem'),
                  'omaha-hi' : ('hold','omahahi'),
                }

        if 'LIMIT' in mg:
            self.info['limitType'] = limits[mg['LIMIT']]
        if 'GAME' in mg:
            (self.info['base'], self.info['category']) = games[mg['GAME']]
        if 'SB' in mg:
            self.info['sb'] = mg['SB']
        if 'BB' in mg:
            self.info['bb'] = mg['BB']

        self.info['type'] = 'ring'
        if mg['CURRENCY'] == u'\u20ac':
            self.info['currency'] = 'EUR'

        # HACK - tablename not in every hand.
        self.info['TABLENAME'] = mg['TABLE']

        print "DEBUG: self.info: %s" % self.info

        return self.info

    def readHandInfo(self, hand):
        m = self.re_HandInfo.search(hand.handText)
        if m is None:
            logging.info(_("Didn't match re_HandInfo"))
            logging.info(hand.handText)
            raise FpdbParseError(_("No match in readHandInfo."))
        hand.handid = m.group('HID')
        hand.tablename = self.info['TABLENAME']
        hand.maxseats = None
        #FIXME: u'DATETIME': u'1291155932'
        hand.startTime = datetime.datetime.strptime('201102091158', '%Y%m%d%H%M')
        #hand.startTime = datetime.datetime.strptime(m.group('DATETIME')[:12], '%Y%m%d%H%M')

    def readPlayerStacks(self, hand):
        m = self.re_PlayerInfo.finditer(hand.handText)
        for a in m:
            print "DEBUG: adding %s %s %s" % (a.group('SEAT'), a.group('PNAME'), a.group('CASH'))
            hand.addPlayer(a.group('SEAT'), a.group('PNAME'), a.group('CASH'))

    def markStreets(self, hand):
        #if hand.gametype['base'] == 'hold':
        
        m =  re.search(r"<DEALER (?P<PREFLOP>.+?(?=<COMMUNITY>)|.+)"
                       r"(<COMMUNITY>(?P<FLOP>\S\S, \S\S, \S\S<\/COMMUNITY>.+?(?=<COMMUNITY>)|.+))?"
                       r"(<COMMUNITY>(?P<TURN>\S\S<\/COMMUNITY>.+?(?=<COMMUNITY>)|.+))?"
                       r"(<COMMUNITY>(?P<RIVER>\S\S<\/COMMUNITY>.+))?", hand.handText,re.DOTALL)
        #import pprint
        #pp = pprint.PrettyPrinter(indent=4)
        #pp.pprint(m.groupdict())
        hand.addStreets(m)

    def readCommunityCards(self, hand, street):
        m = self.re_Board.search(hand.streets[street])
        print "DEBUG: hand.streets[street]: %s" % hand.streets[street]
        if street == 'FLOP':
            hand.setCommunityCards(street, m.group('CARDS').split(','))
        elif street in ('TURN','RIVER'):
            hand.setCommunityCards(street, [m.group('CARDS').split(',')[-1]])

    def readAntes(self, hand):
        pass # ???

    def readBringIn(self, hand):
        pass # ???

    def readBlinds(self, hand):
        for a in self.re_PostSB.finditer(hand.handText):
            #print "DEBUG: found sb: '%s' '%s'" %(self.playerNameFromSeatNo(a.group('PSEAT'), hand), a.group('SB'))
            hand.addBlind(self.playerNameFromSeatNo(a.group('PSEAT'), hand),'small blind', a.group('SB'))

        for a in self.re_PostBB.finditer(hand.handText):
            #print "DEBUG: found bb: '%s' '%s'" %(self.playerNameFromSeatNo(a.group('PSEAT'), hand), a.group('BB'))
            hand.addBlind(self.playerNameFromSeatNo(a.group('PSEAT'), hand), 'big blind', a.group('BB'))
        for a in self.re_PostBoth.finditer(hand.handText):
            bb = Decimal(self.info['bb'])
            amount = Decimal(a.group('SBBB'))
            if amount < bb:
                hand.addBlind(self.playerNameFromSeatNo(a.group('PSEAT'),
                              hand), 'small blind', a.group('SBBB'))
            elif amount == bb:
                hand.addBlind(self.playerNameFromSeatNo(a.group('PSEAT'),
                              hand), 'big blind', a.group('SBBB'))
            else:
                hand.addBlind(self.playerNameFromSeatNo(a.group('PSEAT'),
                              hand), 'both', a.group('SBBB'))

    def readButton(self, hand):
        hand.buttonpos = int(self.re_Button.search(hand.handText).group('BUTTON'))

    def readHeroCards(self, hand):
        m = self.re_HeroCards.search(hand.handText)
        if m:
            hand.hero = self.playerNameFromSeatNo(m.group('PSEAT'), hand)
            cards = m.group('CARDS').split(',')
            hand.addHoleCards('PREFLOP', hand.hero, closed=cards, shown=False,
                              mucked=False, dealt=True)

    def readAction(self, hand, street):
        logging.debug("readAction (%s)" % street)
        m = self.re_Action.finditer(hand.streets[street])
        for action in m:
            logging.debug("%s %s" % (action.group('ATYPE'),
                                     action.groupdict()))
            player = self.playerNameFromSeatNo(action.group('PSEAT'), hand)
            if action.group('ATYPE') == 'RAISE':
                hand.addCallandRaise(street, player, action.group('BET'))
            elif action.group('ATYPE') == 'CALL':
                hand.addCall(street, player, action.group('BET'))
            elif action.group('ATYPE') == 'BET':
                hand.addBet(street, player, action.group('BET'))
            elif action.group('ATYPE') in ('FOLD', 'SIT_OUT'):
                hand.addFold(street, player)
            elif action.group('ATYPE') == 'CHECK':
                hand.addCheck(street, player)
            elif action.group('ATYPE') == 'ALL_IN':
                hand.addAllIn(street, player, action.group('BET'))
            else:
                logging.debug(_("Unimplemented readAction: %s %s"
                              % (action.group('PSEAT'),action.group('ATYPE'),)))

    def readShowdownActions(self, hand):
        for shows in self.re_ShowdownAction.finditer(hand.handText):
            cards = shows.group('CARDS').split(',')
            hand.addShownCards(cards,
                               self.playerNameFromSeatNo(shows.group('PSEAT'),
                                                         hand))

    def readCollectPot(self, hand):
        for m in self.re_CollectPot.finditer(hand.handText):
            pots[int(m.group('PSEAT'))] += Decimal(m.group('POT'))

    def readShownCards(self, hand):
        for m in self.re_ShownCards.finditer(hand.handText):
            cards = m.group('CARDS').split(',')
            hand.addShownCards(cards=cards, player=self.playerNameFromSeatNo(m.group('PSEAT'), hand))

