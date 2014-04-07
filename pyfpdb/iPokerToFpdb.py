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
from HandHistoryConverter import *
from decimal_wrapper import Decimal


class iPoker(HandHistoryConverter):

    sitename = "iPoker"
    filetype = "text"
    codepage = ("utf8", "cp1252")
    siteId   = 14
    copyGameHeader = True   #NOTE: Not sure if this is necessary yet. The file is xml so its likely
    summaryInFile = True

    substitutions = {
                     'LS'  : u"\$|\xe2\x82\xac|\xe2\u201a\xac|\u20ac|\xc2\xa3|\£|RSD|",
                     'PLYR': r'(?P<PNAME>[ a-zA-Z0-9_]+)',
                     'NUM' : r'.,\d',
                    }
    limits = { 'No limit':'nl', 
              'Pot limit':'pl', 
                  'Limit':'fl',
                     'NL':'nl',
                     'SL':'nl',
                    u'БЛ':'nl',
                     'PL':'pl',
                     'LP':'pl',
                      'L':'fl',
                     'LZ':'fl',
                  }
    games = {              # base, category
                '7 Card Stud' : ('stud','studhi'),
                '5 Card Stud' : ('stud','5_studhi'),
                     'Holdem' : ('hold','holdem'),
                      'Omaha' : ('hold','omahahi'),
                'Omaha Hi-Lo' : ('hold','omahahilo'),
            }

    currencies = { u'€':'EUR', '$':'USD', '':'T$', u'£':'GBP', 'RSD': 'RSD'}
    
    # translations from captured groups to fpdb info strings
    Lim_Blinds = {      '0.04': ('0.01', '0.02'),         '0.08': ('0.02', '0.04'),
                        '0.10': ('0.02', '0.05'),         '0.20': ('0.05', '0.10'),
                        '0.40': ('0.10', '0.20'),         '0.50': ('0.10', '0.25'),
                        '1.00': ('0.25', '0.50'),         '1': ('0.25', '0.50'),
                        '2.00': ('0.50', '1.00'),         '2': ('0.50', '1.00'),
                        '4.00': ('1.00', '2.00'),         '4': ('1.00', '2.00'),
                        '6.00': ('1.00', '3.00'),         '6': ('1.00', '3.00'),
                        '8.00': ('2.00', '4.00'),         '8': ('2.00', '4.00'),
                       '10.00': ('2.00', '5.00'),        '10': ('2.00', '5.00'),
                       '20.00': ('5.00', '10.00'),       '20': ('5.00', '10.00'),
                       '30.00': ('10.00', '15.00'),      '30': ('10.00', '15.00'),
                       '40.00': ('10.00', '20.00'),      '40': ('10.00', '20.00'),
                       '60.00': ('15.00', '30.00'),      '60': ('15.00', '30.00'),
                       '80.00': ('20.00', '40.00'),      '80': ('20.00', '40.00'),
                      '100.00': ('25.00', '50.00'),     '100': ('25.00', '50.00'),
                      '150.00': ('50.00', '75.00'),     '150': ('50.00', '75.00'),
                      '200.00': ('50.00', '100.00'),    '200': ('50.00', '100.00'),
                      '400.00': ('100.00', '200.00'),   '400': ('100.00', '200.00'),
                      '800.00': ('200.00', '400.00'),   '800': ('200.00', '400.00'),
                     '1000.00': ('250.00', '500.00'),  '1000': ('250.00', '500.00'),
                     '2000.00': ('500.00', '1000.00'), '2000': ('500.00', '1000.00'),
                  }

    # translations from captured groups to fpdb info strings
    Lim_Blinds = {      '0.04': ('0.01', '0.02'),         '0.08': ('0.02', '0.04'),
                        '0.10': ('0.02', '0.05'),         '0.20': ('0.05', '0.10'),
                        '0.40': ('0.10', '0.20'),         '0.50': ('0.10', '0.25'),
                        '1.00': ('0.25', '0.50'),         '1': ('0.25', '0.50'),
                        '2.00': ('0.50', '1.00'),         '2': ('0.50', '1.00'),
                        '4.00': ('1.00', '2.00'),         '4': ('1.00', '2.00'),
                        '6.00': ('1.50', '3.00'),         '6': ('1.50', '3.00'),
                        '8.00': ('2.00', '4.00'),         '8': ('2.00', '4.00'),
                       '10.00': ('2.50', '5.00'),        '10': ('2.50', '5.00'),
                       '20.00': ('5.00', '10.00'),       '20': ('5.00', '10.00'),
                       '30.00': ('7.50', '15.00'),       '30': ('7.50', '15.00'),
                       '40.00': ('10.00', '20.00'),      '40': ('10.00', '20.00'),
                       '60.00': ('15.00', '30.00'),      '60': ('15.00', '30.00'),
                       '80.00': ('20.00', '40.00'),      '80': ('20.00', '40.00'),
                      '100.00': ('25.00', '50.00'),     '100': ('25.00', '50.00'),
                      '150.00': ('50.00', '75.00'),     '150': ('50.00', '75.00'),
                      '200.00': ('50.00', '100.00'),    '200': ('50.00', '100.00'),
                      '300.00': ('75.00', '150.00'),    '300': ('75.00', '150.00'),
                      '400.00': ('100.00', '200.00'),   '400': ('100.00', '200.00'),
                      '600.00': ('150.00', '300.00'),   '600': ('150.00', '300.00'),
                      '800.00': ('200.00', '400.00'),   '800': ('200.00', '400.00'),
                     '1000.00': ('250.00', '500.00'),  '1000': ('250.00', '500.00'),
                     '2000.00': ('500.00', '1000.00'), '2000': ('500.00', '1000.00'),
                     '4000.00': ('1000.00','2000.00'), '4000': ('1000.00', '2000.00'),
                  }

    months = { 'Jan':1, 'Feb':2, 'Mar':3, 'Apr':4, 'May':5, 'Jun':6, 'Jul':7, 'Aug':8, 'Sep':9, 'Oct':10, 'Nov':11, 'Dec':12}

    # Static regexes
    re_Identify = re.compile(u'<game\sgamecode=')
    re_SplitHands = re.compile(r'</game>')
    re_TailSplitHands = re.compile(r'(</game>)')
    re_GameInfo = re.compile(ur"""
            <gametype>(?P<GAME>((?P<CATEGORY>(5|7)\sCard\sStud|Holdem|Omaha|Omaha\sHi\-Lo)\s(?P<LIMIT>NL|SL|L|LZ|PL|БЛ|LP|No\slimit|Pot\slimit|Limit))|LH\s(?P<LSB>[%(NUM)s]+)/(?P<LBB>[%(NUM)s]+).+?)
            (\s(%(LS)s)?(?P<SB>[%(NUM)s]+)/(%(LS)s)?(?P<BB>[%(NUM)s]+))?(\sAnte\s(%(LS)s)?(?P<ANTE>[%(NUM)s]+))?</gametype>\s+?
            <tablename>(?P<TABLE>.+)?</tablename>\s+?
            (<(tablecurrency|tournamentcurrency)>(?P<TABLECURRENCY>.*)</(tablecurrency|tournamentcurrency)>\s+?)?
            <duration>.+</duration>\s+?
            <gamecount>.+</gamecount>\s+?
            <startdate>.+</startdate>\s+?
            <currency>(?P<CURRENCY>.+)?</currency>\s+?
            <nickname>(?P<HERO>.+)?</nickname>
            """ % substitutions, re.MULTILINE|re.VERBOSE)
    re_GameInfoTrny = re.compile(r"""(?P<HEAD>
                <tournamentname>.+?<place>(?P<PLACE>.+?)</place>
                <buyin>(?P<BUYIN>(?P<BIAMT>.+?)(\+(?P<BIRAKE>.+?))?(\+(?P<BIRAKE1>.+?))?)</buyin>\s+?
                <totalbuyin>(?P<TOTBUYIN>.*)</totalbuyin>\s+?
                <ipoints>.+?</ipoints>\s+?
                <win>(%(LS)s)?(?P<WIN>([%(NUM)s]+)|.+?)</win>\s+?)
            """ % substitutions, re.MULTILINE|re.VERBOSE)
    re_Buyin = re.compile(r"""(?P<BUYIN>[%(NUM)s]+)""" % substitutions, re.MULTILINE|re.VERBOSE)
    re_TotalBuyin  = re.compile(r"""(?P<BUYIN>(?P<BIAMT>[%(LS)s%(NUM)s]+)\s\+\s?(?P<BIRAKE>[%(LS)s%(NUM)s]+)?)""" % substitutions, re.MULTILINE|re.VERBOSE)
    re_HandInfo = re.compile(r'code="(?P<HID>[0-9]+)">\s*?<general>\s*?<startdate>(?P<DATETIME>[a-zA-Z-/: 0-9]+)</startdate>', re.MULTILINE)
    re_PlayerInfo = re.compile(r'<player seat="(?P<SEAT>[0-9]+)" name="(?P<PNAME>[^"]+)" chips="(%(LS)s)(?P<CASH>[%(NUM)s]+)" dealer="(?P<BUTTONPOS>(0|1))" win="(%(LS)s)(?P<WIN>[%(NUM)s]+)" (bet="(%(LS)s)(?P<BET>[^"]+))?' % substitutions, re.MULTILINE)
    re_Board = re.compile(r'<cards type="(?P<STREET>Flop|Turn|River)"( player="")?>(?P<CARDS>.+?)</cards>', re.MULTILINE)
    re_EndOfHand = re.compile(r'<round id="END_OF_GAME"', re.MULTILINE)
    re_PostSB = re.compile(r'<action no="[0-9]+" player="%(PLYR)s"( actiontxt="[^"]+" turntime="[^"]+")? type="1" sum="(%(LS)s)(?P<SB>[%(NUM)s]+)"' % substitutions, re.MULTILINE)
    re_PostBB = re.compile(r'<action no="(?P<ACT>[0-9]+)" player="%(PLYR)s"( actiontxt="[^"]+" turntime="[^"]+")? type="2" sum="(%(LS)s)(?P<BB>[%(NUM)s]+)"' % substitutions, re.MULTILINE)
    re_Hero = re.compile(r'<nickname>(?P<HERO>.+)</nickname>', re.MULTILINE)
    re_HeroCards = re.compile(r'<cards type="(Pocket|Second\sStreet|Third\sStreet|Fourth\sStreet|Fifth\sStreet|Sixth\sStreet|River)" player="(?P<PNAME>[^"]+)">(?P<CARDS>.+?)</cards>', re.MULTILINE)
    re_Action = re.compile(r'<action no="(?P<ACT>[0-9]+)" player="(?P<PNAME>[^"]+)"( actiontxt="[^"]+" turntime="[^"]+")? type="(?P<ATYPE>\d+)" sum="(%(LS)s)(?P<BET>[%(NUM)s]+)"' % substitutions, re.MULTILINE)
    re_Ante   = re.compile(r'<action no="[0-9]+" player="(?P<PNAME>[^"]+)"( actiontxt="[^"]+" turntime="[^"]+")? type="(?P<ATYPE>15)" sum="(%(LS)s)(?P<BET>[%(NUM)s]+)" cards="' % substitutions, re.MULTILINE)
    re_SitsOut = re.compile(r'<event sequence="[0-9]+" type="SIT_OUT" player="(?P<PSEAT>[0-9])"/>', re.MULTILINE)
    re_DateTime1 = re.compile("""(?P<D>[0-9]{2})\-(?P<M>[a-zA-Z]{3})\-(?P<Y>[0-9]{4})\s+(?P<H>[0-9]+):(?P<MIN>[0-9]+)(:(?P<S>[0-9]+))?""", re.MULTILINE)
    re_DateTime2 = re.compile("""(?P<D>[0-9]{2})\/(?P<M>[0-9]{2})\/(?P<Y>[0-9]{4})\s+(?P<H>[0-9]+):(?P<MIN>[0-9]+)(:(?P<S>[0-9]+))?""", re.MULTILINE)
    re_MaxSeats = re.compile(r'(?P<SEATS>[0-9]+) Max', re.MULTILINE)

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
                ["tour", "stud", "fl"],
                ]

    def parseHeader(self, handText, whole_file):
        gametype = self.determineGameType(handText)
        if gametype is None:
            gametype = self.determineGameType(whole_file)
            if gametype is None:
                tmp = handText[0:200]
                log.error(_("iPokerToFpdb.determineGameType: '%s'") % tmp)
                raise FpdbParseError
        return gametype

    def determineGameType(self, handText):

        m = self.re_GameInfo.search(handText)
        if not m: return None

        self.info = {}
        mg = m.groupdict()
        tourney = False
        #print "DEBUG: m.groupdict(): %s" % mg
        if mg['GAME'][:2]=='LH':
            mg['CATEGORY'] = 'Holdem'
            mg['LIMIT'] = 'L'
            mg['BB'] = mg['LBB']
        if 'GAME' in mg:
            (self.info['base'], self.info['category']) = self.games[mg['CATEGORY']]
        if 'LIMIT' in mg:
            self.info['limitType'] = self.limits[mg['LIMIT']]
        if 'HERO' in mg:
            self.hero = mg['HERO']
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
            self.tinfo['tourNo'] = mg['TABLE'].split(',')[-1].strip().split(' ')[0]
            self.tablename = '1'
            if not mg['CURRENCY'] or mg['CURRENCY']=='fun':
                self.tinfo['buyinCurrency'] = 'play'
            else:
                self.tinfo['buyinCurrency'] = mg['CURRENCY']
            self.tinfo['buyin'] = 0
            self.tinfo['fee'] = 0
            m2 = self.re_GameInfoTrny.search(handText)
            if m2:
                mg =  m2.groupdict()
                if not mg['BIRAKE'] and mg['TOTBUYIN']:
                    m3 = self.re_TotalBuyin.search(mg['TOTBUYIN'])
                    if m3:
                        mg = m3.groupdict()
                    elif mg['BIAMT']: mg['BIRAKE'] = '0'
                if mg['BIRAKE']:
                    #FIXME: tournament no looks liek it is in the table name
                    mg['BIRAKE'] = self.clearMoneyString(mg['BIRAKE'].strip(u'$€£'))
                    mg['BIAMT']  = self.clearMoneyString(mg['BIAMT'].strip(u'$€£'))
                    m4 = self.re_Buyin.search(mg['BIAMT'])
                    if m4:
                        mg['BIAMT'] = m4.group('BUYIN')
                        self.tinfo['fee']   = int(100*Decimal(self.clearMoneyString(mg['BIRAKE'])))
                        self.tinfo['buyin'] = int(100*Decimal(self.clearMoneyString(mg['BIAMT'])))
                        if mg['BIRAKE1']:
                            self.tinfo['buyin'] += int(100*Decimal(self.clearMoneyString(mg['BIRAKE1'].strip(u'$€£'))))
                    # FIXME: <place> and <win> not parsed at the moment.
                    #  NOTE: Both place and win can have the value N/A
            if self.tinfo['buyin'] == 0:
                self.tinfo['buyinCurrency'] = 'FREE'
        else:
            self.info['type'] = 'ring'
            self.tablename = mg['TABLE']
            if not mg['TABLECURRENCY'] and not mg['CURRENCY']:
                self.info['currency'] = 'play'
            elif not mg['TABLECURRENCY']:
                self.info['currency'] = mg['CURRENCY']
            else:
                self.info['currency'] = mg['TABLECURRENCY']

            if self.info['limitType'] == 'fl' and self.info['bb'] is not None:
                try:
                    self.info['sb'] = self.Lim_Blinds[self.clearMoneyString(mg['BB'])][0]
                    self.info['bb'] = self.Lim_Blinds[self.clearMoneyString(mg['BB'])][1]
                except KeyError:
                    tmp = handText[0:200]
                    log.error(_("iPokerToFpdb.determineGameType: Lim_Blinds has no lookup for '%s' - '%s'") % (mg['BB'], tmp))
                    raise FpdbParseError

        return self.info

    def readHandInfo(self, hand):
        m = self.re_HandInfo.search(hand.handText)
        if m is None:
            tmp = hand.handText[0:200]
            log.error(_("iPokerToFpdb.readHandInfo: '%s'") % tmp)
            raise FpdbParseError

        mg = m.groupdict()
        #print "DEBUG: m.groupdict(): %s" % mg
        hand.tablename = self.tablename
        m1 = self.re_MaxSeats.search(self.tablename)
        if m1:
            seats = int(m1.group('SEATS'))
            if seats > 1 and seats < 11:
                hand.maxseats = seats
        hand.handid = m.group('HID')
        m2 = self.re_DateTime1.search(m.group('DATETIME'))
        if m2:
            month = self.months[m2.group('M')]
            sec = m2.group('S')
            if m2.group('S') == None:
                sec = '00'
            datetimestr = "%s/%s/%s %s:%s:%s" % (m2.group('Y'), month,m2.group('D'),m2.group('H'),m2.group('MIN'),sec)
            hand.startTime = datetime.datetime.strptime(datetimestr, "%Y/%m/%d %H:%M:%S")
        else:
            try:
                hand.startTime = datetime.datetime.strptime(m.group('DATETIME'), '%Y-%m-%d %H:%M:%S')
            except ValueError:
                datestr = '%d/%m/%Y %H:%M:%S'
                date_match = self.re_DateTime2.search(m.group('DATETIME'))
                if date_match.group('S') == None:
                    datestr = '%d/%m/%Y %H:%M'
                hand.startTime = datetime.datetime.strptime(m.group('DATETIME'), datestr)

        if self.info['type'] == 'tour':
            hand.tourNo = self.tinfo['tourNo']
            hand.buyinCurrency = self.tinfo['buyinCurrency']
            hand.buyin = self.tinfo['buyin']
            hand.fee = self.tinfo['fee']

    def readPlayerStacks(self, hand):
        self.playerWinnings, plist = {}, {}
        m = self.re_PlayerInfo.finditer(hand.handText)
        for a in m:
            ag = a.groupdict()
            plist[a.group('PNAME')] = [int(a.group('SEAT')), self.clearMoneyString(a.group('CASH')), self.clearMoneyString(a.group('WIN')), False]
            re_sitout = re.compile(r'<action no="[0-9]+" player="' + re.escape(a.group('PNAME')) + '" type="9"')
            if re_sitout.search(hand.handText):
                if hand.gametype['type'] == "ring" :
                    # Remove any listed as sitting out in the summary as start of hand info unreliable
                    #print "DEBUG: Deleting '%s' from player dict" %(b.group('PNAME'))
                    del plist[a.group('PNAME')]
                else:
                    plist[a.group('PNAME')][2] = True
            else:
                if a.group('BUTTONPOS') == '1':
                    hand.buttonpos = int(a.group('SEAT'))
                    
        if len(plist)<=1:
            # Hand cancelled
            raise FpdbHandPartial(hid=hand.handid)
                                
        # Add remaining players
        for pname in plist:
            seat, stack, win, sitout = plist[pname]
            hand.addPlayer(seat, pname, stack, None, sitout)
            if Decimal(win) != 0:
                self.playerWinnings[pname] = win
                
        if hand.maxseats==None:
            if self.info['type'] == 'tour' and self.maxseats==0:
                hand.maxseats = self.guessMaxSeats(hand)
                self.maxseats = hand.maxseats
            elif self.info['type'] == 'tour':
                hand.maxseats = self.maxseats
            else:
                hand.maxseats = None

    def markStreets(self, hand):
        if hand.gametype['base'] in ('hold'):
            m =  re.search(r'(?P<PREFLOP>.+(?=<round no="2">)|.+)'
                       r'(<round no="2">(?P<FLOP>.+(?=<round no="3">)|.+))?'
                       r'(<round no="3">(?P<TURN>.+(?=<round no="4">)|.+))?'
                       r'(<round no="4">(?P<RIVER>.+))?', hand.handText,re.DOTALL)
        elif hand.gametype['base'] in ('stud'):
            if hand.gametype['category'] == '5_studhi':
                m = re.search(r'(?P<ANTES>.+(?=<round no="2">)|.+)'
                              r'(<round no="2">(?P<SECOND>.+(?=<round no="3">)|.+))?'
                              r'(<round no="3">(?P<THIRD>.+(?=<round no="4">)|.+))?'
                              r'(<round no="4">(?P<FOURTH>.+(?=<round no="5">)|.+))?'
                              r'(<round no="5">(?P<FIFTH>.+))?', hand.handText,re.DOTALL)
            else:
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
        if m:
            cards = m.group('CARDS').split(' ')
            cards = [c[1:].replace('10', 'T') + c[0].lower() for c in cards]
            hand.setCommunityCards(street, cards)
        else:
            raise FpdbHandPartial(hid=hand.handid)

    def readAntes(self, hand):
        m = self.re_Ante.finditer(hand.handText)
        for a in m:
            hand.addAnte(a.group('PNAME'), self.clearMoneyString(a.group('BET')))

    def readBringIn(self, hand):
        if hand.gametype['sb'] == None and hand.gametype['bb'] == None:
            hand.gametype['sb'] = "1"
            hand.gametype['bb'] = "2"

    def readBlinds(self, hand):
        for a in self.re_PostSB.finditer(hand.streets['PREFLOP']):
            hand.addBlind(a.group('PNAME'), 'small blind', self.clearMoneyString(a.group('SB')))
            if not hand.gametype['sb']:
                hand.gametype['sb'] = self.clearMoneyString(a.group('SB'))
        m = self.re_PostBB.finditer(hand.streets['PREFLOP'])
        blinds = {}
        for a in m:
            blinds[int(a.group('ACT'))] = a.groupdict()
        for b in sorted(blinds.iterkeys()):
            type = 'big blind'
            blind = blinds[b]
            if not hand.gametype['bb']:
                hand.gametype['bb'] = self.clearMoneyString(blind['BB'])
            elif hand.gametype['sb']:
                bb = Decimal(hand.gametype['bb'])
                amount = Decimal(self.clearMoneyString(blind['BB']))
                if amount > bb:
                    type = 'both'
            hand.addBlind(blind['PNAME'], type, self.clearMoneyString(blind['BB']))
        self.fixTourBlinds(hand)

    def fixTourBlinds(self, hand):
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
                if street == 'SEVENTH' and self.hero != player:
                    newcards = []
                    oldcards = [c[1:].replace('10', 'T') + c[0].lower() for c in cards if c[0].lower()!='x']
                else:
                    newcards = [c[1:].replace('10', 'T') + c[0].lower() for c in cards if c[0].lower()!='x']
                    oldcards = []
                
                if street == 'THIRD' and len(newcards) == 3 and self.hero == player: # hero in stud game
                    hand.hero = player
                    hand.dealt.add(player) # need this for stud??
                    hand.addHoleCards(street, player, closed=newcards[0:2], open=[newcards[2]], shown=True, mucked=False, dealt=False)
                elif street == 'SECOND' and len(newcards) == 2 and self.hero == player: # hero in stud game
                    hand.hero = player
                    hand.dealt.add(player)
                    hand.addHoleCards(street, player, closed=[newcards[0]], open=[newcards[1]], shown=True, mucked=False, dealt=False)
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
            bet = self.clearMoneyString(action['BET'])
            #print "DEBUG: action: %s" % action
            if atype == '0':
                hand.addFold(street, player)
            elif atype == '4':
                hand.addCheck(street, player)
            elif atype == '3':
                hand.addCall(street, player, bet)
            elif atype == '23': # Raise to
                hand.addRaiseTo(street, player, bet)
            elif atype == '6': # Raise by
                #This is only a guess
                hand.addRaiseBy(street, player, bet)
            elif atype == '5':
                hand.addBet(street, player, bet)
            elif atype == '16': #BringIn
                hand.addBringIn(player, bet)
            elif atype == '7':
                hand.addAllIn(street, player, bet)
            elif atype == '15': # Ante
                pass # Antes dealt with in readAntes
            elif atype == '1' or atype == '2' or atype == '8': #sb/bb/no action this hand (joined table)
                pass
            elif atype == '9': #FIXME: Sitting out
                pass
            else:
                log.error(_("DEBUG:") + " " + _("Unimplemented %s: '%s' '%s'") % ("readAction", action['PNAME'], action['ATYPE']))

    def readShowdownActions(self, hand):
        # Cards lines contain cards
        pass

    def readCollectPot(self, hand):
        hand.setUncalledBets(True)
        for pname, pot in self.playerWinnings.iteritems():
            hand.addCollectPot(player=pname, pot=self.clearMoneyString(pot))

    def readShownCards(self, hand):
        # Cards lines contain cards
        pass

    def guessMaxSeats(self, hand):
        """Return a guess at maxseats when not specified in HH."""
        # if some other code prior to this has already set it, return it
        if self.maxseats > 1 and self.maxseats < 11:
            if self.maxseats >= len(hand.players):
                return self.maxseats
        mo = len(hand.players)

        if mo == 10: return 10 #that was easy

        if hand.gametype['base'] == 'stud':
            if mo <= 8: return 8
            else: return mo

        if hand.gametype['base'] == 'draw':
            if mo <= 6: return 6
            else: return mo

        if mo == 2: return 2
        if mo <= 6: return 6
        return 10

    @staticmethod
    def getTableTitleRe(type, table_name=None, tournament = None, table_number=None):
        log.info("iPoker getTableTitleRe: table_name='%s' tournament='%s' table_number='%s'" % (table_name, tournament, table_number))
        regex = "%s" % (table_name)
        if tournament:
            regex = "%s" % (tournament)
        elif table_name.find('(No DP),') != -1:
            regex = table_name.split('(No DP),')[0]
        elif table_name.find(',') != -1:
            regex = table_name.split(',')[0]
        else:
            regex = table_name.split(' ')[0]

        log.info("iPoker getTableTitleRe: returns: '%s'" % (regex))
        return regex
