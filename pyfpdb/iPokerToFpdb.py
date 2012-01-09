#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Copyright 2010-2012, Carl Gherardi
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
    codepage = ("utf8", "cp1252")
    siteId   = 13
    copyGameHeader = True   #NOTE: Not sure if this is necessary yet. The file is xml so its likely
    summaryInFile = True

    substitutions = {
                     'LS'  : u"\$|\xe2\x82\xac|\xe2\u201a\xac|\u20ac|\xc2\xa3|\£|",
                     'PLYR': r'(?P<PNAME>[a-zA-Z0-9]+)',
                     'NUM' : r'.,0-9',
                    }
    
    currencies = { u'€':'EUR', '$':'USD', '':'T$', u'£':'GBP' }

    # Static regexes
    re_SplitHands = re.compile(r'</game>')
    re_TailSplitHands = re.compile(r'(</game>)')
    re_GameInfo = re.compile(r"""
            <gametype>(?P<GAME>(5|7)\sCard\sStud\sL|Holdem\sNL|Holdem\sL|Omaha\sPL|Omaha\sL)(\s(%(LS)s)(?P<SB>[.0-9]+)/(%(LS)s)(?P<BB>[.0-9]+))?</gametype>\s+?
            <tablename>(?P<TABLE>.+)?</tablename>\s+?
            <duration>.+</duration>\s+?
            <gamecount>.+</gamecount>\s+?
            <startdate>.+</startdate>\s+?
            <currency>(?P<CURRENCY>.+)</currency>
            """ % substitutions, re.MULTILINE|re.VERBOSE)
    re_GameInfoTrny = re.compile(r"""
                <tournamentname>.+?<place>(?P<PLACE>.+?)</place>
                <buyin>(?P<BUYIN>(?P<BIAMT>[%(LS)s\d\.]+)\+?(?P<BIRAKE>[%(LS)s\d\.]+)?)</buyin>\s+?
                <totalbuyin>(?P<TOTBUYIN>.+)</totalbuyin>\s+?
                <ipoints>([%(NUM)s]+|N/A)</ipoints>\s+?
                <win>(%(LS)s)?(?P<WIN>([%(NUM)s]+)|N/A)</win>
            """ % substitutions, re.MULTILINE|re.VERBOSE)
    re_HandInfo = re.compile(r'code="(?P<HID>[0-9]+)">\s+<general>\s+<startdate>(?P<DATETIME>[-: 0-9]+)</startdate>', re.MULTILINE)
    re_PlayerInfo = re.compile(r'<player seat="(?P<SEAT>[0-9]+)" name="(?P<PNAME>[^"]+)" chips="(%(LS)s)(?P<CASH>[%(NUM)s]+)" dealer="(?P<BUTTONPOS>(0|1))" win="(%(LS)s)(?P<WIN>[%(NUM)s]+)" (bet="(%(LS)s)(?P<BET>[^"]+))?' % substitutions, re.MULTILINE)
    re_Board = re.compile(r'<cards type="(?P<STREET>Flop|Turn|River)" player="">(?P<CARDS>.+?)</cards>', re.MULTILINE)
    re_EndOfHand = re.compile(r'<round id="END_OF_GAME"', re.MULTILINE)
    re_PostSB = re.compile(r'<action no="[0-9]+" player="%(PLYR)s" type="1" sum="(%(LS)s)(?P<SB>[%(NUM)s]+)"' % substitutions, re.MULTILINE)
    re_PostBB = re.compile(r'<action no="[0-9]+" player="%(PLYR)s" type="2" sum="(%(LS)s)(?P<BB>[%(NUM)s]+)"' % substitutions, re.MULTILINE)
    re_PostBoth = re.compile(r'<event sequence="[0-9]+" type="(RETURN_BLIND)" player="(?P<PSEAT>[0-9])" amount="(?P<SBBB>[%(NUM)s]+)"/>' % substitutions, re.MULTILINE)
    re_Hero = re.compile(r'<nickname>(?P<HERO>.+)</nickname>', re.MULTILINE)
    re_HeroCards = re.compile(r'<cards type="(Pocket|Third\sStreet|Fourth\sStreet|Fifth\sStreet|Sixth\sStreet|River)" player="(?P<PNAME>[^"]+)">(?P<CARDS>.+?)</cards>', re.MULTILINE)
    re_Action = re.compile(r'<action no="(?P<ACT>[0-9]+)" player="(?P<PNAME>[^"]+)" type="(?P<ATYPE>\d+)" sum="(%(LS)s)(?P<BET>[%(NUM)s]+)"' % substitutions, re.MULTILINE)
    re_Ante   = re.compile(r'<action no="[0-9]+" player="(?P<PNAME>[^"]+)" type="(?P<ATYPE>15)" sum="(%(LS)s)(?P<BET>[%(NUM)s]+)" cards="' % substitutions, re.MULTILINE)
    re_SitsOut = re.compile(r'<event sequence="[0-9]+" type="SIT_OUT" player="(?P<PSEAT>[0-9])"/>', re.MULTILINE)
    
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
                ["tour", "hold", "nl"],
                ["tour", "hold", "pl"],
                ["tour", "hold", "fl"],
                ]

    def determineGameType(self, handText):
        tourney = False
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
                tmp = handText[0:200]
                log.error("determineGameType: " + _("Raising FpdbParseError for file '%s'") % self.in_path)
                raise FpdbParseError(_("Unable to recognise gametype from: '%s'") % tmp)

        self.info = {}
        mg = m.groupdict()
        #print "DEBUG: m.groupdict(): %s" % mg

        games = {              # base, category
                    '7 Card Stud L' : ('stud','studhilo'),
                    '5 Card Stud L' : ('stud','5studhi'),
                        'Holdem NL' : ('hold','holdem'),
                         'Holdem L' : ('hold','holdem'),
                         'Omaha PL' : ('hold','omahahi'),
                }

        if 'GAME' in mg:
            (self.info['base'], self.info['category']) = games[mg['GAME']]
            m = self.re_Hero.search(handText)
            if m:
                self.hero = m.group('HERO')
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
            self.info['sb'] = self.clearMoneyString(mg['SB'])
            if not mg['SB']: tourney = True
        if 'BB' in mg:
            self.info['bb'] = self.clearMoneyString(mg['BB'])

        if tourney:
            self.info['type'] = 'tour'
            self.info['currency'] = 'T$'
            # FIXME: The sb/bb isn't listed in the game header. Fixing to 1/2 for now
            self.tinfo = {} # FIXME?: Full tourney info is only at the top of the file. After the
                            #         first hand in a file, there is no way for auto-import to
                            #         gather the info unless it reads the entire file every time.
            self.tinfo['tourNo'] = mg['TABLE'].split(',')[-1].strip()
            self.tablename = mg['TABLE'].split(',')[0].strip()
            self.tinfo['buyinCurrency'] = mg['CURRENCY']
            m2 = self.re_GameInfoTrny.search(handText)
            if m2:
                mg =  m2.groupdict()
                #FIXME: tournament no looks liek it is in the table name
                mg['BIAMT']  = mg['BIAMT'].strip(u'$€£FPP')
                mg['BIRAKE'] = mg['BIRAKE'].strip(u'$€£')
                self.tinfo['buyin'] = int(100*Decimal(self.clearMoneyString(mg['BIAMT'])))
                self.tinfo['fee']   = int(100*Decimal(self.clearMoneyString(mg['BIRAKE'])))
                # FIXME: <place> and <win> not parsed at the moment.
                #  NOTE: Both place and win can have the value N/A
            else:
                self.tinfo['buyin'] = 0
                self.tinfo['fee'] = 0
        else:
            self.info['type'] = 'ring'
            self.tablename = mg['TABLE']
            self.info['currency'] = mg['CURRENCY']

        return self.info

    def readHandInfo(self, hand):
        m = self.re_HandInfo.search(hand.handText)
        if m is None:
            tmp = hand.handText[0:200]
            log.error("readHandInfo: " + _("Raising FpdbParseError for file '%s'") % self.in_path)
            raise FpdbParseError(_("Unable to recognise hand info from: '%s'") % tmp)
        
        mg = m.groupdict()
        #print "DEBUG: m.groupdict(): %s" % mg
        hand.tablename = self.tablename
        hand.handid = m.group('HID')
        hand.maxseats = None
        hand.startTime = datetime.datetime.strptime(m.group('DATETIME'), '%Y-%m-%d %H:%M:%S')
        if self.info['type'] == 'tour':
            hand.tourNo = self.tinfo['tourNo']
            hand.buyinCurrency = self.tinfo['buyinCurrency']
            hand.buyin = self.tinfo['buyin']
            hand.fee = self.tinfo['fee']

    def readPlayerStacks(self, hand):
        self.playerWinnings = {}
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
            cash = self.clearMoneyString(a.group('CASH'))
            hand.addPlayer(seatno, a.group('PNAME'), cash)
            if a.group('WIN') != '0':
                win = self.clearMoneyString(a.group('WIN'))
                self.playerWinnings[a.group('PNAME')] = win

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
        cards = [c[1:].replace('10', 'T') + c[0].lower() for c in cards]
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
            hand.addBlind(a.group('PNAME'), 'small blind', self.clearMoneyString(a.group('SB')))
            if not hand.gametype['sb']:
                hand.gametype['sb'] = self.clearMoneyString(a.group('SB'))
        for a in self.re_PostBB.finditer(hand.streets['PREFLOP']):
            if not hand.gametype['bb']:
                hand.gametype['bb'] = self.clearMoneyString(a.group('BB'))
            hand.addBlind(a.group('PNAME'), 'big blind', self.clearMoneyString(a.group('BB')))
        for a in self.re_PostBoth.finditer(hand.streets['PREFLOP']):
            bb = Decimal(self.info['bb'])
            amount = Decimal(self.clearMoneyString(a.group('SBBB')))
            if amount < bb:
                hand.addBlind(a.group('PNAME'), 'small blind', self.clearMoneyString(a.group('SBBB')))
            elif amount == bb:
                hand.addBlind(a.group('PNAME'), 'big blind', self.clearMoneyString(a.group('SBBB')))
            else:
                hand.addBlind(a.group('PNAME'), 'both', self.clearMoneyString(a.group('SBBB')))

        # FIXME
        # The following should only trigger when a small blind is missing in a tournament, or the sb/bb is ALL_IN
        # see http://sourceforge.net/apps/mantisbt/fpdb/view.php?id=115
        if hand.gametype['type'] == 'tour':
            if hand.gametype['sb'] == None and hand.gametype['bb'] == None:
                hand.gametype['sb'] = "1"
                hand.gametype['bb'] = "2"
            elif hand.gametype['sb'] == None:
                hand.gametype['sb'] = str(int(Decimal(hand.gametype['bb']))/2)
            elif hand.gametype['bb'] == None:
                hand.gametype['bb'] = str(int(Decimal(hand.gametype['sb']))*2)
            if int(Decimal(hand.gametype['bb']))/2 != int(Decimal(hand.gametype['sb'])):
                if int(Decimal(hand.gametype['bb']))/2 < int(Decimal(hand.gametype['sb'])):
                    hand.gametype['bb'] = str(int(Decimal(hand.gametype['sb']))*2)
                else:
                    hand.gametype['sb'] = str(int(Decimal(hand.gametype['bb']))/2)

    def readButton(self, hand):
        # Found in re_Player
        pass
            
    def readHeroCards(self, hand):
#    streets PREFLOP, PREDRAW, and THIRD are special cases beacause
#    we need to grab hero's cards
        for street in ('PREFLOP', 'DEAL'):
            if street in hand.streets.keys():
                m = self.re_HeroCards.finditer(hand.streets[street])
                for found in m:
                    player = found.group('PNAME')
                    cards = found.group('CARDS').split(' ')
                    cards = [c[1:].replace('10', 'T') + c[0].lower().replace('x', '') for c in cards]
                    if player == self.hero and cards[0]:
                        hand.hero = player
                    hand.addHoleCards(street, player, closed=cards, shown=True, mucked=False, dealt=True)
                    
        for street, text in hand.streets.iteritems():
            if not text or street in ('PREFLOP', 'DEAL'): continue  # already done these
            m = self.re_HeroCards.finditer(hand.streets[street])
            for found in m:
                player = found.group('PNAME')
                cards = found.group('CARDS').split(' ')
                if street == 'SEVENTH' and hand.hero != player:
                    newcards = []
                    oldcards = [c[1:].replace('10', 'T') + c[0].lower() for c in cards if c != 'X']
                else:
                    newcards = [c[1:].replace('10', 'T') + c[0].lower() for c in cards if c != 'X']
                    oldcards = []

                if street == 'THIRD' and len(newcards) == 3 and self.hero == player: # hero in stud game
                    hand.hero = player
                    hand.dealt.add(player) # need this for stud??
                    hand.addHoleCards(street, player, closed=newcards[0:2], open=[newcards[2]], shown=True, mucked=False, dealt=False)
                else:                       
                    hand.addHoleCards(street, player, open=newcards, closed=oldcards, shown=True, mucked=False, dealt=False)

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
            elif atype == '15': # Ante
                pass # Antes dealt with in readAntes
            elif atype == '1' or atype == '2' or atype == '8': #sb/bb/no action this hand (joined table)
                pass
            elif atype == '9': #FIXME: Sitting out
                pass
            else:
                logging.error(_("DEBUG:") + " " + _("Unimplemented %s: '%s' '%s'") % ("readAction", action['PNAME'], action['ATYPE']))

    def readShowdownActions(self, hand):
        # Cards lines contain cards
        pass

    def readCollectPot(self, hand):
        hand.setUncalledBets(True)
        for pname, pot in self.playerWinnings.iteritems():
            hand.addCollectPot(player=pname, pot=pot)

    def readShownCards(self, hand):
        # Cards lines contain cards
        pass

    @staticmethod
    def getTableTitleRe(type, table_name=None, tournament = None, table_number=None):
        log.info("iPoker getTableTitleRe: table_name='%s' tournament='%s' table_number='%s'" % (table_name, tournament, table_number))
        regex = "%s" % (table_name)
        if tournament:
            regex = "%s" % (table_number)
        else:
            regex = table_name.split(',')[0]
        log.info("iPoker getTableTitleRe: returns: '%s'" % (regex))
        return regex
