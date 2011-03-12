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
    siteID   = 13

    # Static regexes
    re_SplitHands = re.compile(r'</game>')
    re_TailSplitHands = re.compile(r'(</game>)')
    re_GameInfo = re.compile(r'<gametype>(?P<GAME>[a-zA-Z0-9 ]+) \$(?P<SB>[.0-9]+)/\$(?P<BB>[.0-9]+)</gametype>', re.MULTILINE)
    re_HandInfo = re.compile(r'gamecode="(?P<HID>[0-9]+)">\s+<general>\s+<startdate>(?P<DATETIME>[-: 0-9]+)</startdate>', re.MULTILINE)
    re_Button = re.compile(r'<players dealer="(?P<BUTTON>[0-9]+)">')
    re_PlayerInfo = re.compile(r'<player seat="(?P<SEAT>[0-9]+)" name="(?P<PNAME>[^"]+)" chips="\$(?P<CASH>[.0-9]+)" dealer="(?P<DEALTIN>(0|1))" (?P<WIN>win="\$[^"]+") (bet="\$(?P<BET>[^"]+))?', re.MULTILINE)
    re_Board = re.compile(r'<cards type="COMMUNITY" cards="(?P<CARDS>[^"]+)"', re.MULTILINE)
    re_EndOfHand = re.compile(r'<round id="END_OF_GAME"', re.MULTILINE)

    re_PostSB = re.compile(r'<event sequence="[0-9]+" type="(SMALL_BLIND|RETURN_BLIND)" player="(?P<PSEAT>[0-9])" amount="(?P<SB>[.0-9]+)"/>', re.MULTILINE)
    re_PostBB = re.compile(r'<event sequence="[0-9]+" type="(BIG_BLIND|INITIAL_BLIND)" player="(?P<PSEAT>[0-9])" amount="(?P<BB>[.0-9]+)"/>', re.MULTILINE)
    re_PostBoth = re.compile(r'<event sequence="[0-9]+" type="(RETURN_BLIND)" player="(?P<PSEAT>[0-9])" amount="(?P<SBBB>[.0-9]+)"/>', re.MULTILINE)
    re_HeroCards = re.compile(r'<cards type="HOLE" cards="(?P<CARDS>.+)" player="(?P<PSEAT>[0-9])"', re.MULTILINE)
    re_Action = re.compile(r'<action no="[0-9]+" player="(?P<PNAME>[^"]+)" type="(?P<ATYPE>\d+)" sum="\$(?P<BET>[.0-9]+)"', re.MULTILINE)
    re_Ante   = re.compile(r'<action no="[0-9]+" player="(?P<PNAME>[^"]+)" type="(?P<ATYPE>15)" sum="\$(?P<BET>[.0-9]+)" cards="', re.MULTILINE)
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
                ["ring", "stud", "fl"],
                #["ring", "hold", "nl"],
                #["tour", "hold", "nl"]
                ]

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
                log.error(_("determineGameType: Raising FpdbParseError"))
                raise FpdbParseError(_("Unable to recognise gametype from: '%s'") % tmp)

        self.info = {}
        mg = m.groupdict()
        #print "DEBUG: m.groupdict(): %s" % mg

        limits = { 'No Limit':'nl', 'Limit':'fl' }
        games = {              # base, category
                    '7 Card Stud L' : ('stud','studhilo'),
                }

        if 'LIMIT' in mg:
            self.info['limitType'] = limits[mg['LIMIT']]
        self.info['limitType'] = 'fl'
        if 'GAME' in mg:
            (self.info['base'], self.info['category']) = games[mg['GAME']]
        if 'SB' in mg:
            self.info['sb'] = mg['SB']
        if 'BB' in mg:
            self.info['bb'] = mg['BB']
        if mg['GAME'] == 'Holdem Tournament':
            self.info['type'] = 'tour'
            self.info['currency'] = 'T$'
        else:
            self.info['type'] = 'ring'
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
        print "DEBUG: readPlayerStacks"
        m = self.re_PlayerInfo.finditer(hand.handText)
        for a in m:
            ag = a.groupdict()
            #print "DEBUG: re_PlayerInfo: %s" %ag
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

            hand.addPlayer(seatno, a.group('PNAME'), a.group('CASH'))

    def markStreets(self, hand):
        if hand.gametype['base'] in ('stud'):
            m = re.search(r'(?P<ANTES>.+(?=<round no="2">)|.+)'
                          r'(<round no="2">(?P<THIRD>.+(?=<round no="3">)|.+))?'
                          r'(<round no="3">(?P<FOURTH>.+(?=<round no="4">)|.+))?'
                          r'(<round no="4">(?P<FIFTH>.+(?=<round no="5">)|.+))?'
                          r'(<round no="5">(?P<SIXTH>.+(?=<round no="6">)|.+))?'
                          r'(<round no="6">(?P<SEVENTH>.+))?', hand.handText,re.DOTALL)

        hand.addStreets(m)

    def readCommunityCards(self, hand, street):
        m = self.re_Board.search(hand.streets[street])
        if street == 'FLOP':
            hand.setCommunityCards(street, m.group('CARDS').split(','))
        elif street in ('TURN','RIVER'):
            hand.setCommunityCards(street, [m.group('CARDS').split(',')[-1]])

    def readAntes(self, hand):
        m = self.re_Ante.finditer(hand.handText)
        for a in m:
            #print "DEBUG: addAnte(%s, %s)" %(a.group('PNAME'),  a.group('BET'))
            hand.addAnte(a.group('PNAME'), a.group('BET'))

    def readBringIn(self, hand):
        pass

    def readBlinds(self, hand):
        m = self.re_PostSB.search(hand.handText)
        hand.addBlind(m.group('PNAME'), 'small blind', m.group('SB'))
        for a in self.re_PostBB.finditer(hand.handText):
            hand.addBlind(m.group('PNAME'), 'big blind', a.group('BB'))
        #for a in self.re_PostBoth.finditer(hand.handText):

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
            ag = action.groupdict()
            #print "DEBUG: action.groupdict: %s" % ag
            logging.debug("%s %s" % (action.group('ATYPE'),
                                     action.groupdict()))
            if action.group('ATYPE') == 'RAISE': # Still no example for raise (i think?)
                hand.addCallandRaise(street, player, action.group('BET'))
            elif action.group('ATYPE') == '3': # Believe this is 'call'
                #print "DEBUG: addCall(%s, %s, %s)" %(street, action.group('PNAME'), action.group('BET'))
                hand.addCall(street, action.group('PNAME'), action.group('BET'))
            elif action.group('ATYPE') == '5':
                #print "DEBUG: addBet(%s, %s, %s)" %(street, action.group('PNAME'), action.group('BET'))
                hand.addBet(street, action.group('PNAME'), action.group('BET'))
            elif action.group('ATYPE') == '0': # Belive this is 'fold'
                #print "DEBUG: addFold(%s, %s)" %(street, action.group('PNAME'))
                hand.addFold(street, action.group('PNAME'))
            elif action.group('ATYPE') == '4':
                #print "DEBUG: addCheck(%s, %s)" %(street, action.group('PNAME'))
                hand.addCheck(street, action.group('PNAME'))
            #elif action.group('ATYPE') == 'ALL_IN':
            #    hand.addAllIn(street, player, action.group('BET'))
            elif action.group('ATYPE') == '16': #BringIn
                #print "DEBUG: addBringIn(%s, %s)" %(action.group('PNAME'),  action.group('BET'))
                hand.addBringIn(action.group('PNAME'), action.group('BET'))
            else:
                logging.error(_("Unimplemented readAction: %s") % (ag))

    def readShowdownActions(self, hand):
        for shows in self.re_ShowdownAction.finditer(hand.handText):
            cards = shows.group('CARDS').split(',')
            hand.addShownCards(cards,
                               self.playerNameFromSeatNo(shows.group('PSEAT'),
                                                         hand))

    def readCollectPot(self, hand):
        pots = [Decimal(0) for n in range(hand.maxseats)]
        for m in self.re_CollectPot.finditer(hand.handText):
            pots[int(m.group('PSEAT'))] += Decimal(m.group('POT'))
        # Regarding the processing logic for "committed", see Pot.end() in
        # Hand.py
        committed = sorted([(v,k) for (k,v) in hand.pot.committed.items()])
        for p in range(hand.maxseats):
            pname = self.playerNameFromSeatNo(p, hand)
            if committed[-1][1] == pname:
                pots[p] -= committed[-1][0] - committed[-2][0]
            if pots[p] > 0:
                hand.addCollectPot(player=pname, pot=pots[p])

    def readShownCards(self, hand):
        for m in self.re_ShownCards.finditer(hand.handText):
            cards = m.group('CARDS').split(',')
            hand.addShownCards(cards=cards, player=self.playerNameFromSeatNo(m.group('PSEAT'), hand))

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-i", "--input", dest="ipath", help=_("parse input hand history"), default="-")
    parser.add_option("-o", "--output", dest="opath", help=_("output translation to"), default="-")
    parser.add_option("-f", "--follow", dest="follow", help=_("follow (tail -f) the input"), action="store_true", default=False)
    parser.add_option("-q", "--quiet", action="store_const", const=logging.CRITICAL, dest="verbosity", default=logging.INFO)
    parser.add_option("-v", "--verbose", action="store_const", const=logging.INFO, dest="verbosity")
    parser.add_option("--vv", action="store_const", const=logging.DEBUG, dest="verbosity")

    (options, args) = parser.parse_args()

    LOG_FILENAME = './logging.out'
    logging.basicConfig(filename=LOG_FILENAME, level=options.verbosity)

    e = Carbon(in_path = options.ipath,
               out_path = options.opath,
               follow = options.follow,
               autostart = True)

