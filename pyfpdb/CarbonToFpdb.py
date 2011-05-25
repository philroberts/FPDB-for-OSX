#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Copyright 2010-2011, Matthew Boss
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

# This code is based heavily on EverleafToFpdb.py, by Carl Gherardi
#
# TODO:
#
# -- No support for tournaments (see also the last item below)
# -- Assumes that the currency of ring games is USD
# -- Only accepts 'realmoney="true"'
# -- A hand's time-stamp does not record seconds past the minute (a
#    limitation of the history format)
# -- hand.maxseats can only be guessed at
# -- The last hand in a history file will often be incomplete and is therefore
#    rejected
# -- Is behaviour currently correct when someone shows an uncalled hand?
# -- Information may be lost when the hand ID is converted from the native form
#    xxxxxxxx-yyy(y*) to xxxxxxxxyyy(y*) (in principle this should be stored as
#    a string, but the database does not support this). Is there a possibility
#    of collision between hand IDs that ought to be distinct?
# -- Cannot parse tables that run it twice
# -- Cannot parse hands in which someone is all in in one of the blinds. Until
#    this is corrected tournaments will be unparseable

import sys
import logging
from HandHistoryConverter import *
from decimal_wrapper import Decimal


class Carbon(HandHistoryConverter):
    sitename = "Carbon"
    filetype = "text"
    codepage = "cp1252"
    siteId   = 11
    copyGameHeader = True

    limits = { 'No Limit':'nl', 'No Limit ':'nl', 'Limit':'fl', 'Pot Limit':'pl', 'Pot Limit ':'pl', 'Half Pot Limit':'hp'}
    games = {              # base, category
                    'Holdem' : ('hold','holdem'),
         'Holdem Tournament' : ('hold','holdem'),
                    'Omaha'  : ('hold','omahahi'),
         'Omaha Tournament'  : ('hold','omahahi'),
              '2-7 Lowball'  : ('draw','27_3draw'),
                   'Badugi'  : ('draw','badugi'),
                   '7-Stud'  : ('stud','studhi'),
                   '5-Stud'  : ('stud','5studhi'),
                     'Razz'  : ('stud','razz'),
            }

    # Static regexes
    re_SplitHands = re.compile(r'</game>\n+(?=<game)')
    re_TailSplitHands = re.compile(r'(</game>)')
    re_GameInfo = re.compile(r'<description type="(?P<GAME>[-0-9a-zA-Z ]+)" stakes="(?P<LIMIT>[a-zA-Z ]+)\s\(?\$?(?P<SB>[.0-9]+)?/?\$?(?P<BB>[.0-9]+)?(?P<blah>.*)\)?"/>', re.MULTILINE)
    re_HandInfo = re.compile(r'<game id="(?P<HID1>[0-9]+)-(?P<HID2>[0-9]+)" starttime="(?P<DATETIME>[0-9]+)" numholecards="[0-9]+" gametype="[0-9]+" realmoney="(?P<REALMONEY>(true|false))" data="[0-9]+\|(?P<TABLE>[-\ \#a-zA-Z\d\']+)(\(\d+\))?\|(?P<TOURNO>\d+)?.*>', re.MULTILINE)
    re_Button = re.compile(r'<players dealer="(?P<BUTTON>[0-9]+)">')
    re_PlayerInfo = re.compile(r'<player seat="(?P<SEAT>[0-9]+)" nickname="(?P<PNAME>.+)" balance="\$(?P<CASH>[.0-9]+)" dealtin="(?P<DEALTIN>(true|false))" />', re.MULTILINE)
    re_Board = re.compile(r'<cards type="COMMUNITY" cards="(?P<CARDS>[^"]+)"', re.MULTILINE)
    re_EndOfHand = re.compile(r'<round id="END_OF_GAME"', re.MULTILINE)

    # The following are also static regexes: there is no need to call
    # compilePlayerRegexes (which does nothing), since players are identified
    # not by name but by seat number
    re_PostSB = re.compile(r'<event sequence="[0-9]+" type="(SMALL_BLIND|RETURN_BLIND)" (?P<TIMESTAMP>timestamp="[0-9]+" )?player="(?P<PSEAT>[0-9])" amount="(?P<SB>[.0-9]+)"/>', re.MULTILINE)
    re_PostBB = re.compile(r'<event sequence="[0-9]+" type="(BIG_BLIND|INITIAL_BLIND)" (?P<TIMESTAMP>timestamp="[0-9]+" )?player="(?P<PSEAT>[0-9])" amount="(?P<BB>[.0-9]+)"/>', re.MULTILINE)
    re_PostBoth = re.compile(r'<event sequence="[0-9]+" type="(RETURN_BLIND)" player="(?P<PSEAT>[0-9])" amount="(?P<SBBB>[.0-9]+)"/>', re.MULTILINE)
    re_Antes = re.compile(r'<event sequence="[0-9]+" type="ANTE" (?P<TIMESTAMP>timestamp="\d+" )?player="(?P<PSEAT>[0-9])" amount="(?P<ANTE>[.0-9]+)"/>', re.MULTILINE)
    re_BringIn = re.compile(r'<event sequence="[0-9]+" type="BRING_IN" (?P<TIMESTAMP>timestamp="\d+" )?player="(?P<PSEAT>[0-9])" amount="(?P<BRINGIN>[.0-9]+)"/>', re.MULTILINE)
    re_HeroCards = re.compile(r'<cards type="HOLE" cards="(?P<CARDS>.+)" player="(?P<PSEAT>[0-9])"', re.MULTILINE)
    re_Action = re.compile(r'<event sequence="[0-9]+" type="(?P<ATYPE>FOLD|CHECK|CALL|BET|RAISE|ALL_IN|SIT_OUT)" (?P<TIMESTAMP>timestamp="[0-9]+" )?player="(?P<PSEAT>[0-9])"( amount="(?P<BET>[.0-9]+)")?/>', re.MULTILINE)
    re_ShowdownAction = re.compile(r'<cards type="SHOWN" cards="(?P<CARDS>..,..)" player="(?P<PSEAT>[0-9])"/>', re.MULTILINE)
    re_CollectPot = re.compile(r'<winner amount="(?P<POT>[.0-9]+)" uncalled="false" potnumber="[0-9]+" player="(?P<PSEAT>[0-9])"', re.MULTILINE)
    re_SitsOut = re.compile(r'<event sequence="[0-9]+" type="SIT_OUT" player="(?P<PSEAT>[0-9])"/>', re.MULTILINE)
    re_ShownCards = re.compile(r'<cards type="(SHOWN|MUCKED)" cards="(?P<CARDS>.+)" player="(?P<PSEAT>[0-9])"/>', re.MULTILINE)

    def compilePlayerRegexs(self, hand):
        pass

    def playerNameFromSeatNo(self, seatNo, hand):
        # This special function is required because Carbon Poker records
        # actions by seat number, not by the player's name
        for p in hand.players:
            if p[0] == int(seatNo):
                return p[1]

    def readSupportedGames(self):
        return [["ring", "hold", "nl"],
                ["ring", "hold", "pl"],
                ["ring", "hold", "fl"],

                ["ring", "stud", "fl"],
                ["ring", "stud", "pl"],

                ["ring", "draw", "fl"],
                ["ring", "draw", "pl"],
                ["ring", "draw", "nl"],
                ["ring", "draw", "hp"],
                
                ["tour", "hold", "nl"],
                ["tour", "hold", "pl"],
                ["tour", "hold", "fl"]]

    def determineGameType(self, handText):
        """return dict with keys/values:
    'type'       in ('ring', 'tour')
    'limitType'  in ('nl', 'cn', 'pl', 'cp', 'fl')
    'base'       in ('hold', 'stud', 'draw')
    'category'   in ('holdem', 'omahahi', omahahilo', 'razz', 'studhi', 'studhilo', 'fivedraw', '27_1draw', '27_3draw', 'badugi')
    'hilo'       in ('h','l','s')
    'smallBlind' int?
    'bigBlind'   int?
    'smallBet'
    'bigBet'
    'currency'  in ('USD', 'EUR', 'T$', <countrycode>)
or None if we fail to get the info """

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
        #print "DEBUG: mg: %s" % mg

        if 'LIMIT' in mg:
            self.info['limitType'] = self.limits[mg['LIMIT']]
        if 'GAME' in mg:
            (self.info['base'], self.info['category']) = self.games[mg['GAME']]
        if 'SB' in mg:
            self.info['sb'] = mg['SB']
        if 'BB' in mg:
            self.info['bb'] = mg['BB']
        if 'Tournament' in mg['GAME']:
            self.info['type'] = 'tour'
            self.info['currency'] = 'T$'
        else:
            self.info['type'] = 'ring'
            self.info['currency'] = 'USD'

        return self.info

    def readHandInfo(self, hand):
        m = self.re_HandInfo.search(hand.handText)
        if m is None:
            logging.info(_("No match in readHandInfo: '%s'") % hand.handText[0:100])
            logging.info(hand.handText)
            raise FpdbParseError(_("No match in readHandInfo: '%s'") % hand.handText[0:100])
        logging.debug("HID %s-%s, Table %s" % (m.group('HID1'),
                      m.group('HID2'), m.group('TABLE')[:-1]))
        hand.handid = m.group('HID1') + m.group('HID2')
        if hand.gametype['type'] == 'tour':
            hand.tablename = m.group('TABLE')
            hand.tourNo = m.group('TOURNO')
        else:
            hand.tablename = m.group('TABLE')[:-1]
        hand.maxseats = 2 # This value may be increased as necessary
        hand.startTime = datetime.datetime.strptime(m.group('DATETIME')[:12],'%Y%m%d%H%M')
        # Check that the hand is complete up to the awarding of the pot; if
        # not, the hand is unparseable
        if self.re_EndOfHand.search(hand.handText) is None:
            raise FpdbParseError("readHandInfo failed: EndOfHand missing HID: '%s-%s'" %(m.group('HID1'), m.group('HID2')))

    def readPlayerStacks(self, hand):
        m = self.re_PlayerInfo.finditer(hand.handText)
        for a in m:
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
            if a.group('DEALTIN') == "true":
                hand.addPlayer(seatno, a.group('PNAME'), a.group('CASH'))

    def markStreets(self, hand):
        if hand.gametype['base'] == 'hold':
            m = re.search(r'<round id="PREFLOP" sequence="[0-9]+">(?P<PREFLOP>.+(?=<round id="POSTFLOP")|.+)(<round id="POSTFLOP" sequence="[0-9]+">(?P<FLOP>.+(?=<round id="POSTTURN")|.+))?(<round id="POSTTURN" sequence="[0-9]+">(?P<TURN>.+(?=<round id="POSTRIVER")|.+))?(<round id="POSTRIVER" sequence="[0-9]+">(?P<RIVER>.+))?', hand.handText, re.DOTALL)
        elif hand.gametype['base'] == 'draw':
            if hand.gametype['category'] in ('27_3draw','badugi'):
                m =  re.search(r'(?P<PREDEAL>.+(?=<round id="PRE_FIRST_DRAW" sequence="[0-9]+">)|.+)'
                           r'(<round id="PRE_FIRST_DRAW" sequence="[0-9]+">(?P<DEAL>.+(?=<round id="FIRST_DRAW" sequence="[0-9]+">)|.+))?'
                           r'(<round id="FIRST_DRAW" sequence="[0-9]+">(?P<DRAWONE>.+(?=<round id="SECOND_DRAW" sequence="[0-9]+">)|.+))?'
                           r'(<round id="SECOND_DRAW" sequence="[0-9]+">(?P<DRAWTWO>.+(?=<round id="THIRD_DRAW" sequence="[0-9]+">)|.+))?'
                           r'(<round id="THIRD_DRAW" sequence="[0-9]+">(?P<DRAWTHREE>.+))?', hand.handText,re.DOTALL)
        elif hand.gametype['base'] == 'stud':
            m =  re.search(r'(?P<ANTES>.+(?=<round id="BRING_IN" sequence="[0-9]+">)|.+)'
                       r'(<round id="BRING_IN" sequence="[0-9]+">(?P<THIRD>.+(?=<round id="FOURTH_STREET" sequence="[0-9]+">)|.+))?'
                       r'(<round id="FOURTH_STREET" sequence="[0-9]+">(?P<FOURTH>.+(?=<round id="FIFTH_STREET" sequence="[0-9]+">)|.+))?'
                       r'(<round id="FIFTH_STREET" sequence="[0-9]+">(?P<FIFTH>.+(?=<round id="SIXTH_STREET" sequence="[0-9]+">)|.+))?'
                       r'(<round id="SIXTH_STREET" sequence="[0-9]+">(?P<SIXTH>.+(?=<round id="SEVENTH_STREET" sequence="[0-9]+">)|.+))?'
                       r'(<round id="SEVENTH_STREET" sequence="[0-9]+">(?P<SEVENTH>.+))?', hand.handText,re.DOTALL)

        hand.addStreets(m)

    def readCommunityCards(self, hand, street):
        m = self.re_Board.search(hand.streets[street])
        if street == 'FLOP':
            hand.setCommunityCards(street, m.group('CARDS').split(','))
        elif street in ('TURN','RIVER'):
            hand.setCommunityCards(street, [m.group('CARDS').split(',')[-1]])

    def readAntes(self, hand):
        m = self.re_Antes.finditer(hand.handText)
        for player in m:
            pname = self.playerNameFromSeatNo(player.group('PSEAT'), hand)
            #print "DEBUG: hand.addAnte(%s,%s)" %(pname, player.group('ANTE'))
            hand.addAnte(pname, player.group('ANTE'))

    def readBringIn(self, hand):
        m = self.re_BringIn.search(hand.handText)
        if m:
            pname = self.playerNameFromSeatNo(m.group('PSEAT'), hand)
            #print "DEBUG: hand.addBringIn(%s,%s)" %(pname, m.group('BRINGIN'))
            hand.addBringIn(pname, m.group('BRINGIN'))

    def readBlinds(self, hand):
        for a in self.re_PostSB.finditer(hand.handText):
            #print "DEBUG: found sb: '%s' '%s'" %(self.playerNameFromSeatNo(a.group('PSEAT'), hand), a.group('SB'))
            hand.addBlind(self.playerNameFromSeatNo(a.group('PSEAT'), hand),'small blind', a.group('SB'))
            if not hand.gametype['sb']:
                hand.gametype['sb'] = a.group('SB')
        for a in self.re_PostBB.finditer(hand.handText):
            #print "DEBUG: found bb: '%s' '%s'" %(self.playerNameFromSeatNo(a.group('PSEAT'), hand), a.group('BB'))
            hand.addBlind(self.playerNameFromSeatNo(a.group('PSEAT'), hand), 'big blind', a.group('BB'))
            if not hand.gametype['bb']:
                hand.gametype['bb'] = a.group('BB')
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
        for street in ('PREFLOP', 'DEAL', 'THIRD'):
            if street in hand.streets.keys():
                m = self.re_HeroCards.search(hand.handText)
                if m:
                    hand.hero = self.playerNameFromSeatNo(m.group('PSEAT'), hand)
                    cards = m.group('CARDS').split(',')
                    #print "DEBUG: cards: %s" % cards
                    hand.addHoleCards(street, hand.hero, closed=cards, shown=False, mucked=False, dealt=True)

    def readAction(self, hand, street):
        logging.debug("readAction (%s)" % street)
        m = self.re_Action.finditer(hand.streets[street])
        raises = 0
        for action in m:
            logging.debug("%s %s" % (action.group('ATYPE'), action.groupdict()))
            player = self.playerNameFromSeatNo(action.group('PSEAT'), hand)
            if action.group('ATYPE') == 'RAISE':
                raises += 1
                if self.info['limitType'] == 'fl':
                    hand.addRaiseTo(street, player, action.group('BET'))
                elif raises == 1:
                    hand.addRaiseTo(street, player, action.group('BET'))
                else: # raises > 1
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
                logging.debug(_("Unimplemented %s: '%s' '%s'") % ("readAction", action.group('PSEAT'), action.group('ATYPE')))

    def readShowdownActions(self, hand):
        for street in ('RIVER', 'SEVENTH', 'DRAWTHREE'):
            if street in hand.streets.keys() and hand.streets[street] != None:
                for shows in self.re_ShowdownAction.finditer(hand.streets[street]):
                    cards = shows.group('CARDS').split(',')
                    hand.addShownCards(cards, self.playerNameFromSeatNo(shows.group('PSEAT'), hand))

    def readCollectPot(self, hand):
        pots = [Decimal(0) for n in range(hand.maxseats)]
        for m in self.re_CollectPot.finditer(hand.handText):
            pname = self.playerNameFromSeatNo(m.group('PSEAT'), hand)
            #print "DEBUG: addCollectPot(%s, %s)" %(pname, m.group('POT'))
            hand.addCollectPot(player=pname, pot=m.group('POT'))

    def readShownCards(self, hand):
        for street in ('FLOP', 'TURN', 'RIVER', 'SEVENTH', 'DRAWTHREE'):
            if street in hand.streets.keys() and hand.streets[street] != None:
                for m in self.re_ShownCards.finditer(hand.streets[street]):
                    cards = m.group('CARDS').split(',')
                    hand.addShownCards(cards=cards, player=self.playerNameFromSeatNo(m.group('PSEAT'),hand))

