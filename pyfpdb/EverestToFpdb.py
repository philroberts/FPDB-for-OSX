#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Copyright 2010-2011, Carl Gherardi
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
from decimal_wrapper import Decimal


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
    re_PostXB = re.compile(r'<BLIND position="(?P<PSEAT>[0-9]+)" amount="(?P<XB>[0-9]+)" penalty="(?P<PENALTY>[0-9]+)"\/>', re.MULTILINE)
    #re_Antes = ???
    #re_BringIn = ???
    re_HeroCards = re.compile(r'<cards type="HOLE" cards="(?P<CARDS>.+)" player="(?P<PSEAT>[0-9])"', re.MULTILINE)
    re_Action = re.compile(r'<(?P<ATYPE>FOLD|BET) position="(?P<PSEAT>[0-9])"( amount="(?P<BET>[.0-9]+)")?\/>', re.MULTILINE)
    re_ShowdownAction = re.compile(r'<cards type="SHOWN" cards="(?P<CARDS>..,..)" player="(?P<PSEAT>[0-9])"/>', re.MULTILINE)
    re_CollectPot = re.compile(r'<WIN position="(?P<PSEAT>[0-9])" amount="(?P<POT>[.0-9]+)" pot="[0-9]+"', re.MULTILINE)
    re_SitsOut = re.compile(r'<event sequence="[0-9]+" type="SIT_OUT" player="(?P<PSEAT>[0-9])"/>', re.MULTILINE)
    re_ShownCards = re.compile(r'<cards type="(SHOWN|MUCKED)" cards="(?P<CARDS>..,..)" player="(?P<PSEAT>[0-9])"/>', re.MULTILINE)

    def compilePlayerRegexs(self, hand):
        pass

    def playerNameFromSeatNo(self, seatNo, hand):
        # Actions recorded by seat number, not by the player's name
        for p in hand.players:
            if p[0] == seatNo:
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
                log.error(_("Unable to recognise gametype from: '%s'") % tmp)
                log.error("determineGameType: " + _("Raising FpdbParseError"))
                raise FpdbParseError(_("Unable to recognise gametype from: '%s'") % tmp)

        if not m2:
            tmp = handText[0:100]
            log.error("determineGameType: " + _("Raising FpdbParseError"))
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
            logging.info(_("No match in readHandInfo: '%s'") % hand.handText[0:100])
            logging.info(hand.handText)
            raise FpdbParseError(_("No match in readHandInfo: '%s'") % hand.handText[0:100])
        hand.handid = m.group('HID')
        hand.tablename = self.info['TABLENAME']
        hand.maxseats = None
        #FIXME: u'DATETIME': u'1291155932'
        hand.startTime = datetime.datetime.strptime('201102091158', '%Y%m%d%H%M')
        #hand.startTime = datetime.datetime.strptime(m.group('DATETIME')[:12], '%Y%m%d%H%M')

    def readPlayerStacks(self, hand):
        m = self.re_PlayerInfo.finditer(hand.handText)
        for a in m:
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
        if street == 'FLOP':
            hand.setCommunityCards(street, m.group('CARDS').split(','))
        elif street in ('TURN','RIVER'):
            hand.setCommunityCards(street, [m.group('CARDS').split(',')[-1]])

    def readAntes(self, hand):
        pass # ???

    def readBringIn(self, hand):
        pass # ???

    def readBlinds(self, hand):
        for a in self.re_PostXB.finditer(hand.handText):
            amount = "%.2f" % float(int(a.group('XB'))/100)
            print "DEBUG: readBlinds amount: %s" % amount
            if Decimal(a.group('XB'))/100 == Decimal(self.info['sb']):
                hand.addBlind(self.playerNameFromSeatNo(a.group('PSEAT'), hand),'small blind', amount)
            elif Decimal(a.group('XB'))/100 == Decimal(self.info['bb']):
                hand.addBlind(self.playerNameFromSeatNo(a.group('PSEAT'), hand),'big blind', amount)

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
        print "DEBUG: readAction (%s)" % street
        m = self.re_Action.finditer(hand.streets[street])
        curr_pot = Decimal('0')
        for action in m:
            print " DEBUG: %s %s" % (action.group('ATYPE'), action.groupdict())
            player = self.playerNameFromSeatNo(action.group('PSEAT'), hand)
            if action.group('ATYPE') == 'BET':
                amount = Decimal(action.group('BET'))
                amountstr = "%.2f" % float(int(action.group('BET'))/100)
                #Gah! BET can mean check, bet, call or raise...
                if amount > 0 and curr_pot == 0:
                    # Open
                    curr_pot = amount
                    hand.addBet(street, player, amountstr)
                elif Decimal(action.group('BET')) > 0 and curr_pot > 0:
                    # Raise or call
                    if amount > curr_pot:
                        # Raise
                        curr_pot = amount
                        hand.addCallandRaise(street, player, amountstr)
                    elif amount <= curr_pot:
                        # Call
                        hand.addCall(street, player, amountstr)
                if action.group('BET') == '0':
                    hand.addCheck(street, player)
            elif action.group('ATYPE') in ('FOLD', 'SIT_OUT'):
                hand.addFold(street, player)
            else:
                print (_("Unimplemented readAction: '%s' '%s'") % (action.group('PSEAT'), action.group('ATYPE')))
                logging.debug(_("Unimplemented readAction: '%s' '%s'") % (action.group('PSEAT'), action.group('ATYPE')))

    def readShowdownActions(self, hand):
        for shows in self.re_ShowdownAction.finditer(hand.handText):
            cards = shows.group('CARDS').split(',')
            hand.addShownCards(cards,
                               self.playerNameFromSeatNo(shows.group('PSEAT'),
                                                         hand))

    def readCollectPot(self, hand):
        for m in self.re_CollectPot.finditer(hand.handText):
            player = self.playerNameFromSeatNo(m.group('PSEAT'), hand)
            print "DEBUG: %s collects %s" % (player, m.group('POT'))
            hand.addCollectPot(player, str(int(m.group('POT'))/100))

    def readShownCards(self, hand):
        for m in self.re_ShownCards.finditer(hand.handText):
            cards = m.group('CARDS').split(',')
            hand.addShownCards(cards=cards, player=self.playerNameFromSeatNo(m.group('PSEAT'), hand))

