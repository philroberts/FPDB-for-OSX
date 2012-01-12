#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Copyright 2008-2012 Steffen Schaumburg
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
import PacificPokerToFpdb
from TourneySummary import *

class PacificPokerSummary(TourneySummary):
    
    limits = { 'No Limit':'nl', 'Pot Limit':'pl', 'Limit':'fl', 'LIMIT':'fl' }
    
    games = {                          # base, category
                             "Hold'em"  : ('hold','holdem'),
                               'Holdem' : ('hold','holdem'),
                                'Omaha' : ('hold','omahahi'),
                          'Omaha Hi/Lo' : ('hold','omahahilo'),
                              'OmahaHL' : ('hold','omahahilo'),
                                 'Razz' : ('stud','razz'), 
                                 'RAZZ' : ('stud','razz'),
                          '7 Card Stud' : ('stud','studhi'),
                    '7 Card Stud Hi/Lo' : ('stud','studhilo'),
                               'Badugi' : ('draw','badugi'),
              'Triple Draw 2-7 Lowball' : ('draw','27_3draw'),
              'Single Draw 2-7 Lowball' : ('draw','27_1draw'),
                          '5 Card Draw' : ('draw','fivedraw')
               }

    substitutions = {
                     'LEGAL_ISO' : "USD|EUR|GBP|CAD|FPP",      # legal ISO currency codes
                            'LS' : u"\$|\xe2\x82\xac|\u20AC|", # legal currency symbols
                           'NUM' : u".,\d"                     # legal characters in number format
                    }
    
    re_TourneyInfo = re.compile(u"""
                        Tournament\sID:\s(?P<TOURNO>[0-9]+)\s+
                        (Buy-In:\s(?P<CURRENCY>%(LS)s|)?(?P<BUYIN>[,.0-9]+)(\s\+\s[%(LS)s]?(?P<FEE>[,.0-9]+))?\s+)?
                        (Rebuy:\s[%(LS)s](?P<REBUYAMT>[,.0-9]+)\s+)?
                        (Add-On:\s[%(LS)s](?P<ADDON>[,.0-9]+)\s+)?
                        ((?P<P1NAME>.*?)\sperformed\s(?P<PREBUYS>\d+)\srebuys?\s+)?
                        ((?P<P2NAME>.*?)\sperformed\s(?P<PADDONS>\d+)\sadd-ons?\s+)?
                        (?P<PNAME>.*)\sfinished\s(?P<RANK>[0-9]+)\/(?P<ENTRIES>[0-9]+)(\sand\swon\s[%(LS)s](?P<WINNINGS>[,.0-9]+))?
                               """ % substitutions ,re.VERBOSE|re.MULTILINE|re.DOTALL)
    
    re_Category = re.compile(u"""
          (?P<LIMIT>No\sLimit|Fix\sLimit|Pot\sLimit)\s
          (?P<GAME>Holdem|Omaha|OmahaHL|Hold\'em|Omaha\sHi/Lo|OmahaHL|Razz|RAZZ|7\sCard\sStud|7\sCard\sStud\sHi/Lo|Badugi|Triple\sDraw\s2\-7\sLowball|Single\sDraw\s2\-7\sLowball|5\sCard\sDraw)
                               """ % substitutions ,re.VERBOSE|re.MULTILINE|re.DOTALL)

    codepage = ["utf-8"]

    @staticmethod
    def getSplitRe(self, head):
        re_SplitTourneys = re.compile(u'\*\*\*\*\* Cassava Tournament Summary \*\*\*\*\*')
        return re_SplitTourneys

    def parseSummary(self):
        m  = self.re_TourneyInfo.search(self.summaryText)
        m1 = self.re_Category.search(self.in_path)
        if m == None or m1 == None:
            tmp = self.summaryText[0:200]
            log.error(_("PacificPokerSummary.parseSummary: '%s'") % tmp)
            raise FpdbParseError

        mg  = m.groupdict()
        mg1 = m1.groupdict()
        #print "DEBUG: m.groupdict(): %s" % mg
        #print "DEBUG: m1.groupdict(): %s" % mg1

        self.tourNo = mg['TOURNO']
        if 'LIMIT'     in mg1 and mg1['LIMIT'] is not None:
            self.gametype['limitType'] = self.limits[mg1['LIMIT']]
        else:
            self.gametype['limitType'] = 'fl'
        if 'GAME'      in mg1: self.gametype['category']  = self.games[mg1['GAME']][1]
        self.buyin = int(100*convert_to_decimal(mg['BUYIN']))
        self.fee   = int(100*convert_to_decimal(mg['FEE']))
        self.prizepool = 0
        self.entries   = mg['ENTRIES']
        if 'REBUYAMT' in mg and mg['REBUYAMT'] != None:
            self.isRebuy   = True
            self.rebuyCost = int(100*convert_to_decimal(mg['REBUYAMT']))
        if 'ADDON' in mg and mg['ADDON'] != None:
            self.isAddOn = True
            self.addOnCost = int(100*convert_to_decimal(mg['ADDON']))
        #self.startTime = datetime.datetime.strptime(datetimestr, "%Y/%m/%d %H:%M:%S")
        if mg['CURRENCY'] == "$":     self.currency = "USD"
        elif mg['CURRENCY'] == u"€":  self.currency="EUR"

        player = mg['PNAME']
        rank = int(mg['RANK'])
        winnings = 0
        rebuyCount = 0
        addOnCount = 0
        koCount = 0
        
        if 'WINNINGS' in mg and mg['WINNINGS'] != None:
            winnings = int(100*convert_to_decimal(mg['WINNINGS']))
        if 'PREBUYS' in mg and mg['PREBUYS'] != None:
            rebuyCount = int(mg['PREBUYS'])
        if 'PADDONS' in mg and mg['PADDONS'] != None:
            addOnCount = int(mg['PADDONS'])
        
        self.addPlayer(rank, player, winnings, self.currency, rebuyCount, addOnCount, koCount)

def convert_to_decimal(string):
    dec = string.strip(u'€&euro;\u20ac$')
    dec = dec.replace(u',','.')
    dec = dec.replace(u' ','')
    dec = Decimal(dec)
    return dec

