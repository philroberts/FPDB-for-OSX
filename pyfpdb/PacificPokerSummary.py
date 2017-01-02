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
                              'OmahaHL' : ('hold','omahahilo')
               }

    substitutions = {
                     'LEGAL_ISO' : "USD|EUR|GBP|CAD|FPP",      # legal ISO currency codes
                            'LS' : u"\$|\xe2\x82\xac|\u20AC|", # legal currency symbols
                           'NUM' : u".,\d\xa0"                     # legal characters in number format
                    }
    
    re_Identify = re.compile(u'\*{5}\s(Cassava|888poker|888.es) Tournament Summary\s\*{5}')
    
    re_TourneyInfo = re.compile(u"""
                        Tournament\sID:\s(?P<TOURNO>[0-9]+)\s+
                        Buy-In:\s(?P<BUYIN>(((?P<BIAMT>(?P<CURRENCY1>%(LS)s)?[%(NUM)s]+\s?(?P<CURRENCY2>%(LS)s)?)(\s\+\s?(?P<BIRAKE>(%(LS)s)?[%(NUM)s]+\s?(%(LS)s)?))?)|(Free)|(.+?)))\s+
                        (Rebuy:\s[%(LS)s](?P<REBUYAMT>[%(NUM)s]+)\s?(%(LS)s)?\s+)?
                        (Add-On:\s[%(LS)s](?P<ADDON>[%(NUM)s]+)\s?(%(LS)s)?\s+)?
                        ((?P<P1NAME>.*?)\sperformed\s(?P<PREBUYS>\d+)\srebuys?\s+)?
                        ((?P<P2NAME>.*?)\sperformed\s(?P<PADDONS>\d+)\sadd-ons?\s+)?
                        ^(?P<PNAME>.+?)\sfinished\s(?P<RANK>[0-9]+)\/(?P<ENTRIES>[0-9]+)(\sand\swon\s(?P<WCURRENCY>[%(LS)s])?(?P<WINNINGS>[%(NUM)s]+)\s?(?P<WCURRENCY2>[%(LS)s])?)?
                               """ % substitutions ,re.VERBOSE|re.MULTILINE|re.DOTALL)
    
    re_Category = re.compile(u"""
          (?P<LIMIT>No\sLimit|Fix\sLimit|Pot\sLimit)\s
          (?P<GAME>Holdem|Omaha|OmahaHL|Hold\'em|Omaha\sHi/Lo|OmahaHL)
                               """ % substitutions ,re.VERBOSE|re.MULTILINE|re.DOTALL)

    codepage = ("utf8", "cp1252")

    @staticmethod
    def getSplitRe(self, head):
        re_SplitTourneys = re.compile(u'\*\*\*\*\* (?:Cassava|888poker|888.es) Tournament Summary \*\*\*\*\*')
        return re_SplitTourneys

    def parseSummary(self):
        m  = self.re_TourneyInfo.search(self.summaryText)
        if m == None:
            tmp = self.summaryText[0:200]
            log.error(_("PacificPokerSummary.parseSummary: '%s'") % tmp)
            raise FpdbParseError

        mg  = m.groupdict()
        #print "DEBUG: m.groupdict(): %s" % mg
        #print "DEBUG: m1.groupdict(): %s" % mg1

        self.tourNo = mg['TOURNO']
        
        m1 = self.re_Category.search(self.in_path)
        if m1:
            mg1 = m1.groupdict()
            if 'LIMIT'     in mg1 and mg1['LIMIT'] is not None:
                self.gametype['limitType'] = self.limits[mg1['LIMIT']]
            else:
                self.gametype['limitType'] = 'fl'
            if 'GAME'      in mg1: self.gametype['category']  = self.games[mg1['GAME']][1]
        else:
            self.gametype['limitType'] = 'nl'
            self.gametype['category']  = 'holdem'
        
        if 'BUYIN' in mg and mg['BUYIN'] is not None:
            if mg['BUYIN'] == 'Free' or mg['BIAMT'] is None:
                self.buyin = 0
                self.fee = 0
            else:
                self.buyin = int(100*self.convert_to_decimal(mg['BIAMT']))
                if mg['BIRAKE'] is None:
                    self.fee = 0
                else:
                    self.fee = int(100*self.convert_to_decimal(mg['BIRAKE']))
         
        self.entries   = mg['ENTRIES']
        self.prizepool = self.buyin * int(self.entries)
        if 'REBUYAMT' in mg and mg['REBUYAMT'] != None:
            self.isRebuy   = True
            self.rebuyCost = int(100*self.convert_to_decimal(mg['REBUYAMT']))
        if 'ADDON' in mg and mg['ADDON'] != None:
            self.isAddOn = True
            self.addOnCost = int(100*self.convert_to_decimal(mg['ADDON']))
        #self.startTime = datetime.datetime.strptime(datetimestr, "%Y/%m/%d %H:%M:%S")
        
        if 'CURRENCY1' in mg and mg['CURRENCY1']:
            currency = mg['CURRENCY1']
        elif 'CURRENCY2' in mg and mg['CURRENCY2']:
            currency = mg['CURRENCY2']
        else:
            currency = None
            
        if currency:
            if currency == "$":     self.buyinCurrency="USD"
            elif currency == u"€":  self.buyinCurrency="EUR"
        elif self.buyin == 0:
            self.buyinCurrency="FREE"
        else:
            self.buyinCurrency="play"
        self.currency = self.buyinCurrency

        player = mg['PNAME']
        rank = int(mg['RANK'])
        winnings = 0
        rebuyCount = None
        addOnCount = None
        koCount = None
        
        if 'WINNINGS' in mg and mg['WINNINGS'] != None:
            winnings = int(100*self.convert_to_decimal(mg['WINNINGS']))
            if mg.get('WCURRENCY'):
                if mg['WCURRENCY'] == "$":     self.currency="USD"
                elif mg['WCURRENCY'] == u"€":  self.currency="EUR"
            elif mg.get('WCURRENCY2'):
                if mg['WCURRENCY2'] == "$":     self.currency="USD"
                elif mg['WCURRENCY2'] == u"€":  self.currency="EUR"
        if 'PREBUYS' in mg and mg['PREBUYS'] != None:
            rebuyCount = int(mg['PREBUYS'])
        if 'PADDONS' in mg and mg['PADDONS'] != None:
            addOnCount = int(mg['PADDONS'])
        
        self.addPlayer(rank, player, winnings, self.currency, rebuyCount, addOnCount, koCount)

    def convert_to_decimal(self, string):
        dec = self.clearMoneyString(string)
        dec = Decimal(dec)
        return dec

