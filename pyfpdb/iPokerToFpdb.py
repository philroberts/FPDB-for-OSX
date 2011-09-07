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

# This code is based on CarbonToFpdb.py by Matthew Boss
#
# TODO:
#
# -- No support for tournaments (see also the last item below)
# -- Assumes that the currency of ring games is USD
# -- No support for a bring-in or for antes (is the latter in fact unnecessary
#    for hold 'em on Carbon?)
# -- hand.maxseats can only be guessed at
# -- The last hand in a history file will often be incomplete and is therefore
#    rejected
# -- Is behaviour currently correct when someone shows an uncalled hand?
# -- Information may be lost when the hand ID is converted from the native form
#    xxxxxxxx-yyy(y*) to xxxxxxxxyyy(y*) (in principle this should be stored as
#    a string, but the database does not support this). Is there a possibility
#    of collision between hand IDs that ought to be distinct?
# -- Cannot parse tables that run it twice (nor is this likely ever to be
#    possible)
# -- Cannot parse hands in which someone is all in in one of the blinds. Until
#    this is corrected tournaments will be unparseable

import sys
import logging
from HandHistoryConverter import *
from decimal_wrapper import Decimal


class iPoker(HandHistoryConverter):

    sitename = "iPoker"
    filetype = "text"
    codepage = "cp1252"
    siteId   = 13

    suit_trans  = { 'S':'s', 'H':'h', 'C':'c', 'D':'d'}

    substitutions = {
                     'LS'  : u"\$|\xe2\x82\xac|\xe2\u201a\xac|\u20ac|\xc2\xa3|",
                     'PLYR': r'(?P<PNAME>[a-zA-Z0-9]+)',
                     'NUM' : r'.,0-9',
                    }

    # Static regexes
    re_SplitHands = re.compile(r'</game>')
    re_TailSplitHands = re.compile(r'(</game>)')
    re_GameInfo = re.compile(r"""
            <gametype>(?P<GAME>7\sCard\sStud\sL|Holdem\sNL|Holdem\sL|Omaha\sPL)\s
            (%(LS)s)(?P<SB>[.0-9]+)/(%(LS)s)(?P<BB>[.0-9]+)</gametype>
            """ % substitutions, re.MULTILINE|re.VERBOSE)
    re_HandInfo = re.compile(r'gamecode="(?P<HID>[0-9]+)">\s+<general>\s+<startdate>(?P<DATETIME>[-: 0-9]+)</startdate>', re.MULTILINE)
    re_PlayerInfo = re.compile(r'<player seat="(?P<SEAT>[0-9]+)" name="(?P<PNAME>[^"]+)" chips="(%(LS)s)(?P<CASH>[%(NUM)s]+)" dealer="(?P<BUTTONPOS>(0|1))" win="(%(LS)s)(?P<WIN>[%(NUM)s]+)" (bet="(%(LS)s)(?P<BET>[^"]+))?' % substitutions, re.MULTILINE)
    re_Board = re.compile(r'<cards type="(?P<STREET>Flop|Turn|River)" player="">(?P<CARDS>.+?)</cards>', re.MULTILINE)
    re_EndOfHand = re.compile(r'<round id="END_OF_GAME"', re.MULTILINE)
    re_PostSB = re.compile(r'<action no="[0-9]+" player="%(PLYR)s" type="1" sum="(%(LS)s)(?P<SB>[%(NUM)s]+)"' % substitutions, re.MULTILINE)
    re_PostBB = re.compile(r'<action no="[0-9]+" player="%(PLYR)s" type="2" sum="(%(LS)s)(?P<BB>[%(NUM)s]+)"' % substitutions, re.MULTILINE)
    re_PostBoth = re.compile(r'<event sequence="[0-9]+" type="(RETURN_BLIND)" player="(?P<PSEAT>[0-9])" amount="(?P<SBBB>[%(NUM)s]+)"/>' % substitutions, re.MULTILINE)
    re_HeroCards = re.compile(r'<cards type="HOLE" cards="(?P<CARDS>.+)" player="(?P<PSEAT>[0-9])"', re.MULTILINE)
    re_Action = re.compile(r'<action no="(?P<ACT>[0-9]+)" player="(?P<PNAME>[^"]+)" type="(?P<ATYPE>\d+)" sum="(%(LS)s)(?P<BET>[%(NUM)s]+)"' % substitutions, re.MULTILINE)
    re_Ante   = re.compile(r'<action no="[0-9]+" player="(?P<PNAME>[^"]+)" type="(?P<ATYPE>15)" sum="(%(LS)s)(?P<BET>[%(NUM)s]+)" cards="' % substitutions, re.MULTILINE)
    re_ShowdownAction = re.compile(r'<cards type="SHOWN" cards="(?P<CARDS>..,..)" player="(?P<PSEAT>[0-9])"/>', re.MULTILINE)
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
                ["ring", "stud", "fl"],
                ["ring", "hold", "nl"],
                ["ring", "hold", "pl"],
                ["ring", "hold", "fl"],
                #["tour", "hold", "nl"]
                ]

    def determineGameType(self, handText):
        m = self.re_GameInfo.search(handText)
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

        self.info = {}
        mg = m.groupdict()
        #print "DEBUG: m.groupdict(): %s" % mg

        games = {              # base, category
                    '7 Card Stud L' : ('stud','studhilo'),
                        'Holdem NL' : ('hold','holdem'),
                         'Holdem L' : ('hold','holdem'),
                         'Omaha PL' : ('hold','omahahi'),
                }

        if 'GAME' in mg:
            (self.info['base'], self.info['category']) = games[mg['GAME']]
        if self.info['base'] == 'stud':
            self.info['limitType'] = 'fl'
        if self.info['base'] == 'hold':
            if mg['GAME'][-2:] == 'NL':
                self.info['limitType'] = 'nl'
            elif mg['GAME'][-2:] == 'PL':
                self.info['limitType'] = 'pl'
            else:
                self.info['limitType'] = 'fl'
        if 'SB' in mg:
            self.info['sb'] = mg['SB']
        if 'BB' in mg:
            self.info['bb'] = mg['BB']
        if mg['GAME'] == 'Holdem Tournament':
            self.info['type'] = 'tour'
            self.info['currency'] = 'T$'
        else:
            self.info['type'] = 'ring'
            #FIXME: Need to fix currencies for this site
            self.info['currency'] = 'USD'

        return self.info

    def readHandInfo(self, hand):
        m = self.re_HandInfo.search(hand.handText)
        if m is None:
            logging.error(_("No match in readHandInfo: '%s'") % hand.handText[0:100])
            logging.info(hand.handText)
            raise FpdbParseError(_("No match in readHandInfo: '%s'") % hand.handText[0:100])
        mg = m.groupdict()
        #print "DEBUG: m.groupdict(): %s" % mg
        hand.handid = m.group('HID')
        #hand.tablename = m.group('TABLE')[:-1]
        hand.maxseats = None
        hand.startTime = datetime.datetime.strptime(m.group('DATETIME'), '%Y-%m-%d %H:%M:%S')

    def readPlayerStacks(self, hand):
        m = self.re_PlayerInfo.finditer(hand.handText)
        for a in m:
            ag = a.groupdict()
            seatno = int(a.group('SEAT'))
            # It may be necessary to adjust 'hand.maxseats', which is an
            # educated guess, starting with 2 (indicating a heads-up table) and
            # adjusted upwards in steps to 6, then 9, then 10. An adjustment is
            # made whenever a player is discovered whose seat number is
            # currently above the maximum allowable for the table.
            if seatno >= hand.maxseats:
                if seatno > 8:
                    hand.maxseats = 10
                elif seatno > 5:
                    hand.maxseats = 9
                else:
                    hand.maxseats = 6

            if a.group('BUTTONPOS') == '1':
                hand.buttonpos = seatno
            hand.addPlayer(seatno, a.group('PNAME'), a.group('CASH'))
            if a.group('WIN') != '0':
                hand.addCollectPot(player=a.group('PNAME'), pot=a.group('WIN'))

    def markStreets(self, hand):
        if hand.gametype['base'] in ('hold'):
            m =  re.search(r'(?P<PREFLOP>.+(?=<round no="2">)|.+)'
                       r'(<round no="2">(?P<FLOP>.+(?=<round no="3">)|.+))?'
                       r'(<round no="3">(?P<TURN>.+(?=<round no="4">)|.+))?'
                       r'(<round no="4">(?P<RIVER>.+))?', hand.handText,re.DOTALL)
        elif hand.gametype['base'] in ('stud'):
            m = re.search(r'(?P<ANTES>.+(?=<round no="2">)|.+)'
                          r'(<round no="2">(?P<THIRD>.+(?=<round no="3">)|.+))?'
                          r'(<round no="3">(?P<FOURTH>.+(?=<round no="4">)|.+))?'
                          r'(<round no="4">(?P<FIFTH>.+(?=<round no="5">)|.+))?'
                          r'(<round no="5">(?P<SIXTH>.+(?=<round no="6">)|.+))?'
                          r'(<round no="6">(?P<SEVENTH>.+))?', hand.handText,re.DOTALL)
        hand.addStreets(m)

    def readCommunityCards(self, hand, street):
        cards = []
        m = self.re_Board.search(hand.streets[street])
        cards = m.group('CARDS').split(' ')
        for i, c in enumerate(cards):
            val, suit = c[1:], c[0]
            if val == '10': val = 'T'
            suit = self.suit_trans[suit]
            cards[i] = "%s%s" %(val, suit)

        hand.setCommunityCards(street, cards)

    def readAntes(self, hand):
        m = self.re_Ante.finditer(hand.handText)
        for a in m:
            #print "DEBUG: addAnte(%s, %s)" %(a.group('PNAME'),  a.group('BET'))
            hand.addAnte(a.group('PNAME'), a.group('BET'))

    def readBringIn(self, hand):
        pass

    def readBlinds(self, hand):
        for a in self.re_PostSB.finditer(hand.streets['PREFLOP']):
            hand.addBlind(a.group('PNAME'), 'small blind', a.group('SB'))
        for a in self.re_PostBB.finditer(hand.streets['PREFLOP']):
            hand.addBlind(a.group('PNAME'), 'big blind', a.group('BB'))
        #for a in self.re_PostBoth.finditer(hand.handText):

    def readButton(self, hand):
        # Found in re_Player
        pass

    def readHeroCards(self, hand):
        m = self.re_HeroCards.search(hand.handText)
        if m:
            hand.hero = self.playerNameFromSeatNo(m.group('PSEAT'), hand)
            cards = m.group('CARDS').split(',')
            hand.addHoleCards('PREFLOP', hand.hero, closed=cards, shown=False,
                              mucked=False, dealt=True)

    def readAction(self, hand, street):
        # HH format doesn't actually print the actions in order!
        m = self.re_Action.finditer(hand.streets[street])
        actions = {}
        for a in m:
            actions[int(a.group('ACT'))] = a.groupdict()
        for a in sorted(actions.iterkeys()):
            action = actions[a]
            atype = action['ATYPE']
            player = action['PNAME']
            #print "DEBUG: action: %s" % action
            if atype == '23': # Raise to
                hand.addRaiseTo(street, player, action['BET'])
            elif atype == '6': # Raise by
                #This is only a guess
                hand.addRaiseBy(street, player, action['BET'])
            elif atype == '3':
                hand.addCall(street, player, action['BET'])
            elif atype == '5':
                hand.addBet(street, player, action['BET'])
            elif atype == '0':
                hand.addFold(street, player)
            elif atype == '4':
                hand.addCheck(street, player)
            elif atype == '16': #BringIn
                hand.addBringIn(player, action['BET'])
            elif atype == '7':
                hand.addAllIn(street, player, action['BET'])
            elif atype == '1' or atype == '2' or atype == '8': #sb/bb/no action this hand (joined table)
                pass
            elif atype == '9': #FIXME: Sitting out
                pass
            else:
                logging.error(_("DEBUG:") + " " + _("Unimplemented %s: '%s' '%s'") % ("readAction", action['PNAME'], action['ATYPE']))

    def readShowdownActions(self, hand):
        for shows in self.re_ShowdownAction.finditer(hand.handText):
            cards = shows.group('CARDS').split(',')
            hand.addShownCards(cards,
                               self.playerNameFromSeatNo(shows.group('PSEAT'),
                                                         hand))

    def readCollectPot(self, hand):
        # Player lines contain winnings
        pass

    def readShownCards(self, hand):
        for m in self.re_ShownCards.finditer(hand.handText):
            cards = m.group('CARDS').split(',')
            hand.addShownCards(cards=cards, player=self.playerNameFromSeatNo(m.group('PSEAT'), hand))
