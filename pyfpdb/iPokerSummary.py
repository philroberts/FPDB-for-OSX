#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Copyright 2008-2011 Carl Gherardi
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU Affero General Public License as published by
#the Free Software Foundation, version 3 of the License.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU Affero General Public License
#along with this program. If not, see <http://www.gnu.org/licenses/>.
#In the "official" distribution you can find the license in agpl-3.0.txt.

import L10n
_ = L10n.get_translation()

from decimal_wrapper import Decimal
import datetime

from Exceptions import FpdbParseError
from HandHistoryConverter import *
from TourneySummary import *


class iPokerSummary(TourneySummary):
    substitutions = {
                     'LS'  : u"\$|\xe2\x82\xac|\xe2\u201a\xac|\u20ac|\xc2\xa3|\£|",
                     'PLYR': r'(?P<PNAME>[a-zA-Z0-9]+)',
                     'NUM' : r'.,0-9',
                    }
    currencies = { u'€':'EUR', '$':'USD', '':'T$', u'£':'GBP' }

    limits = { 'No Limit':'nl', 'Pot Limit':'pl', 'Limit':'fl', 'LIMIT':'fl' }
    
    games = {
                    '7 Card Stud L' : ('stud','studhilo'),
                        'Holdem NL' : ('hold','holdem'),
                         'Holdem L' : ('hold','holdem'),
                         'Omaha PL' : ('hold','omahahi'),
            }

    re_GameType = re.compile(r"""
            <gametype>(?P<GAME>7\sCard\sStud\sL|Holdem\sNL|Holdem\sL|Omaha\sPL|Omaha\sL)(\s(%(LS)s)(?P<SB>[.0-9]+)/(%(LS)s)(?P<BB>[.0-9]+))?</gametype>\s+?
            <tablename>(?P<TABLE>.+)?</tablename>\s+?
            <duration>.+</duration>\s+?
            <gamecount>.+</gamecount>\s+?
            <startdate>(?P<DATETIME>.+)</startdate>\s+?
            <currency>(?P<CURRENCY>.+)</currency>\s+?
            <nickname>(?P<HERO>.+)</nickname>
            """ % substitutions, re.MULTILINE|re.VERBOSE)

    re_GameInfoTrny = re.compile(r"""
                <tournamentname>(?P<NAME>.+?)</tournamentname><place>(?P<PLACE>.+?)</place>
                <buyin>(?P<BUYIN>(?P<BIAMT>.+?)(\+(?P<BIRAKE>.+?))?)</buyin>\s+?
                <totalbuyin>(?P<TOTBUYIN>.+)</totalbuyin>\s+?
                <ipoints>.+?</ipoints>\s+?
                <win>(?P<CURRENCY>%(LS)s)?(?P<WIN>([%(NUM)s]+)|.+?)</win>
            """ % substitutions, re.MULTILINE|re.VERBOSE)
    re_TotalBuyin = re.compile(r"""(?P<BUYIN>(?P<BIAMT>[%(LS)s%(NUM)s]+)\s\+\s?(?P<BIRAKE>[%(LS)s%(NUM)s]+)?)""" % substitutions, re.MULTILINE|re.VERBOSE)
    re_DateTime = re.compile("""(?P<D>[0-9]{2})\/(?P<M>[0-9]{2})\/(?P<Y>[0-9]{4})\s+(?P<H>[0-9]+):(?P<MIN>[0-9]+)(:(?P<S>[0-9]+))?""", re.MULTILINE)

    codepage = ["utf-8"]

    @staticmethod
    def getSplitRe(self, head):
        re_SplitTourneys = re.compile("PokerStars Tournament ")
        return re_SplitTourneys


    def parseSummary(self):
        m = self.re_GameType.search(self.summaryText)
        if not m:
            tmp = self.summaryText[0:200]
            log.error(_("iPokerSummary.determineGameType: '%s'") % tmp)
            raise FpdbParseError

        mg = m.groupdict()
        #print "DEBUG: m.groupdict(): %s" % mg

        if 'SB' in mg and mg['SB'] != None:
            tmp = self.summaryText[0:200]
            log.error(_("iPokerSummary.determineGameType: Text does not appear to be a tournament '%s'") % tmp)
            raise FpdbParseError
        else:
            tourney = True
#                self.gametype['limitType'] = 
        if 'GAME' in mg:
            self.gametype['category'] = self.games[mg['GAME']][1]

        if mg['GAME'][-2:] == 'NL':
            self.gametype['limitType'] = 'nl'
        elif mg['GAME'][-2:] == 'PL':
            self.gametype['limitType'] = 'pl'
        else:
            self.gametype['limitType'] = 'fl'

        try:
            self.startTime = datetime.datetime.strptime(mg['DATETIME'], '%Y-%m-%d %H:%M:%S')
        except ValueError:
            datestr = '%d/%m/%Y %H:%M:%S'
            date_match = self.re_DateTime.search(m.group('DATETIME'))
            if date_match.group('S') == None:
                datestr = '%d/%m/%Y %H:%M'
            self.startTime = datetime.datetime.strptime(m.group('DATETIME'), datestr)
            
        if not mg['CURRENCY'] or mg['CURRENCY']=='fun':
            self.buyinCurrency = 'play'
        else:
            self.buyinCurrency = mg['CURRENCY']
        self.currency = self.buyinCurrency
        self.tourNo = mg['TABLE'].split(',')[-1].strip().split(' ')[0]

        if tourney:
            m2 = self.re_GameInfoTrny.search(self.summaryText)
            if m2:
                mg2 =  m2.groupdict()
                self.buyin = 0
                self.fee   = 0
                self.prizepool = None
                self.entries   = None
                
                winnings = int(100*convert_to_decimal(mg2['WIN']))
                if mg2['CURRENCY']:
                    self.currency = self.currencies[mg2['CURRENCY']]
                rank     = mg2['PLACE']
                self.tourneyName = mg2['NAME'][:40]
                
                if not mg2['BIRAKE'] and mg2['TOTBUYIN']:
                    m3 = self.re_TotalBuyin.search(mg2['TOTBUYIN'])
                    if m3:
                        mg2 = m3.groupdict()
                    elif mg2['BIAMT']: mg2['BIRAKE'] = '0'
                if mg2['BIAMT'] and mg2['BIRAKE']:
                    self.buyin =  int(100*convert_to_decimal(mg2['BIAMT']))
                    self.fee   =  int(100*convert_to_decimal(mg2['BIRAKE']))
                else:
                    self.buyin = 0
                    self.fee   = 0
                if self.buyin == 0:
                    self.buyinCurrency = 'FREE'
                hero = mg['HERO']
                if rank in ('N/A', 'N/D'):
                    rank = None
                self.addPlayer(rank, hero, winnings, self.currency, 0, 0, 0)
            else:
                raise FpdbHandPartial(hid=self.tourNo)
        else:
            tmp = self.summaryText[0:200]
            log.error(_("iPokerSummary.determineGameType: Text does not appear to be a tournament '%s'") % tmp)
            raise FpdbParseError


def convert_to_decimal(string):
    dec = string.strip(u'$£€&euro;\u20ac')
    dec = dec.replace(u',','.')
    dec = dec.replace(u' ','')
    if dec in ('N/A', 'N/D'):
        dec = 0
    dec = Decimal(dec)
    return dec

