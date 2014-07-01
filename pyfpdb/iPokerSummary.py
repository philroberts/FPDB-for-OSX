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
                     'LS'  : u"\$|\xe2\x82\xac|\xe2\u201a\xac|\u20ac|\xc2\xa3|\£|RSD|",
                     'PLYR': r'(?P<PNAME>[a-zA-Z0-9]+)',
                     'NUM' : r'.,0-9',
                    }
    currencies = { u'€':'EUR', '$':'USD', '':'T$', u'£':'GBP', 'RSD': 'RSD'}

    months = { 'Jan':1, 'Feb':2, 'Mar':3, 'Apr':4, 'May':5, 'Jun':6, 'Jul':7, 'Aug':8, 'Sep':9, 'Oct':10, 'Nov':11, 'Dec':12}
    
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
          '7 Card Stud Hi-Lo' : ('stud','studhilo'),
                '5 Card Stud' : ('stud','5_studhi'),
                     'Holdem' : ('hold','holdem'),
                      'Omaha' : ('hold','omahahi'),
                'Omaha Hi-Lo' : ('hold','omahahilo'),
            }
    
    re_Identify = re.compile(u'<game\sgamecode=')

    re_GameType = re.compile(ur"""
            <gametype>(?P<GAME>((?P<CATEGORY>(5|7)\sCard\sStud(\sHi\-Lo)?|Holdem|Omaha(\sHi\-Lo)?)\s(?P<LIMIT>NL|SL|L|LZ|PL|БЛ|LP|No\slimit|Pot\slimit|Limit))|LH\s(?P<LSB>[%(NUM)s]+)/(?P<LBB>[%(NUM)s]+).+?)
            (\s(%(LS)s)?(?P<SB>[%(NUM)s]+)/(%(LS)s)?(?P<BB>[%(NUM)s]+))?(\sAnte\s(%(LS)s)?(?P<ANTE>[%(NUM)s]+))?</gametype>\s+?
            <tablename>(?P<TABLE>.+)?</tablename>\s+?
            (<(tablecurrency|tournamentcurrency)>.*</(tablecurrency|tournamentcurrency)>\s+?)?
            <duration>.+</duration>\s+?
            <gamecount>.+</gamecount>\s+?
            <startdate>(?P<DATETIME>.+)</startdate>\s+?
            <currency>(?P<CURRENCY>.+)</currency>\s+?
            <nickname>(?P<HERO>.+)</nickname>
            """ % substitutions, re.MULTILINE|re.VERBOSE)

    re_GameInfoTrny = re.compile(r"""
                <tournamentname>(?P<NAME>.+?)</tournamentname><place>(?P<PLACE>.+?)</place>
                <buyin>(?P<BUYIN>(?P<BIAMT>.+?)(\+(?P<BIRAKE>.+?))?(\+(?P<BIRAKE1>.+?))?)</buyin>\s+?
                <totalbuyin>(?P<TOTBUYIN>.*)</totalbuyin>\s+?
                <ipoints>.+?</ipoints>\s+?
                <win>(?P<CURRENCY>%(LS)s)?(?P<WIN>([%(NUM)s]+)|.+?)</win>
            """ % substitutions, re.MULTILINE|re.VERBOSE)
    re_Buyin = re.compile(r"""(?P<BUYIN>[%(NUM)s]+)""" % substitutions, re.MULTILINE|re.VERBOSE)
    re_TotalBuyin = re.compile(r"""(?P<BUYIN>(?P<BIAMT>[%(LS)s%(NUM)s]+)\s\+\s?(?P<BIRAKE>[%(LS)s%(NUM)s]+)?)""" % substitutions, re.MULTILINE|re.VERBOSE)
    re_DateTime1 = re.compile("""(?P<D>[0-9]{2})\-(?P<M>[a-zA-Z]{3})\-(?P<Y>[0-9]{4})\s+(?P<H>[0-9]+):(?P<MIN>[0-9]+)(:(?P<S>[0-9]+))?""", re.MULTILINE)
    re_DateTime2 = re.compile("""(?P<D>[0-9]{2})\/(?P<M>[0-9]{2})\/(?P<Y>[0-9]{4})\s+(?P<H>[0-9]+):(?P<MIN>[0-9]+)(:(?P<S>[0-9]+))?""", re.MULTILINE)
    re_Place     = re.compile("\d+")
    re_FPP       = re.compile(r'Pts\s')
    
    codepage = ["utf8", "cp1252"]

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
            (self.gametype['base'], self.gametype['category']) = self.games[mg['CATEGORY']]
        if 'LIMIT' in mg:
            self.gametype['limitType'] = self.limits[mg['LIMIT']]

        m2 = self.re_DateTime1.search(mg['DATETIME'])
        if m2:
            month = self.months[m2.group('M')]
            sec = m2.group('S')
            if m2.group('S') == None:
                sec = '00'
            datetimestr = "%s/%s/%s %s:%s:%s" % (m2.group('Y'), month,m2.group('D'),m2.group('H'),m2.group('MIN'),sec)
            self.startTime = datetime.datetime.strptime(datetimestr, "%Y/%m/%d %H:%M:%S")
        else:
            try:
                self.startTime = datetime.datetime.strptime(mg['DATETIME'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                datestr = '%d/%m/%Y %H:%M:%S'
                date_match = self.re_DateTime2.search(mg['DATETIME'])
                if date_match.group('S') == None:
                    datestr = '%d/%m/%Y %H:%M'
                self.startTime = datetime.datetime.strptime(mg['DATETIME'], datestr)

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

                if mg2['CURRENCY']:
                    self.currency = self.currencies[mg2['CURRENCY']]
                rank, winnings = None, None
                if self.re_Place.search(mg2['PLACE']):
                    rank     = int(mg2['PLACE'])
                    winnings = int(100*self.convert_to_decimal(mg2['WIN']))

                self.tourneyName = mg2['NAME'][:40]

                if not mg2['BIRAKE'] and mg2['TOTBUYIN']:
                    m3 = self.re_TotalBuyin.search(mg2['TOTBUYIN'])
                    if m3:
                        mg2 = m3.groupdict()
                    elif mg2['BIAMT']: mg2['BIRAKE'] = '0'
                if mg2['BIAMT'] and mg2['BIRAKE']:
                    self.buyin =  int(100*self.convert_to_decimal(mg2['BIAMT']))
                    self.fee   =  int(100*self.convert_to_decimal(mg2['BIRAKE']))
                    if 'BIRAKE1' in mg2 and mg2['BIRAKE1']:
                        self.buyin += int(100*self.convert_to_decimal(mg2['BIRAKE1']))
                    if self.re_FPP.match(mg2['BIAMT']):
                        self.buyinCurrency = 'FPP'
                else:
                    self.buyin = 0
                    self.fee   = 0
                if self.buyin == 0:
                    self.buyinCurrency = 'FREE'
                hero = mg['HERO']
                self.addPlayer(rank, hero, winnings, self.currency, 0, 0, 0)
            else:
                raise FpdbHandPartial(hid=self.tourNo)
        else:
            tmp = self.summaryText[0:200]
            log.error(_("iPokerSummary.determineGameType: Text does not appear to be a tournament '%s'") % tmp)
            raise FpdbParseError


    def convert_to_decimal(self, string):
        dec = self.clearMoneyString(string)
        m = self.re_Buyin.search(dec)
        if m:
            dec = Decimal(m.group('BUYIN'))
        else:
            dec = 0
        return dec

