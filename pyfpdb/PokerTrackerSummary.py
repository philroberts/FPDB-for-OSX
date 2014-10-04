#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Copyright 2008-2012 Chaz Littlejohn
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

class PokerTrackerSummary(TourneySummary):
    hhtype = "summary"
    limits = { 'NL':'nl', 'No Limit':'nl', 'Pot Limit':'pl', 'PL': 'pl', 'FL': 'fl', 'Limit':'fl', 'LIMIT':'fl' }
    games = {                          # base, category
                              "Hold'em" : ('hold','holdem'), 
                        "Texas Hold'em" : ('hold','holdem'),
                               "Holdem" : ('hold','holdem'),
                                'Omaha' : ('hold','omahahi'),
                             'Omaha Hi' : ('hold','omahahi'),
                          'Omaha Hi/Lo' : ('hold','omahahilo')
               }

    substitutions = {
                     'LEGAL_ISO' : "USD|EUR|GBP|CAD|FPP",      # legal ISO currency codes
                            'LS' : u"\$|\xe2\x82\xac|\u20ac|\£|", # legal currency symbols - Euro(cp1252, utf-8)
                           'PLYR': r'(?P<PNAME>.+?)',
                           'NUM' : u".,\d",
                            'CUR': u"(\$|\xe2\x82\xac|\u20ac||\£|)",
                    }

    re_Identify = re.compile(u"PokerTracker")

    re_TourneyInfo = re.compile(u"""
                        \s(3|4)\sTournament\sSummary\s+
                        Site:\s(?P<SITE>.+?)\s+
                        Game:\s(?P<GAME>Holdem|Texas\sHold\'em|Omaha|Omaha\sHi|Omaha\sHi/Lo)\s+
                        Tournament\s\#:\s(?P<TOURNO>[0-9]+)\s+
                        Started:\s(?P<DATETIME>.+?)\s+
                        Finished:\s(?P<DATETIME1>.+?)\s+
                        Buyin:\s(?P<CURRENCY>[%(LS)s]?)(?P<BUYIN>[,.0-9]+)\s+
                        Fee:\s[%(LS)s]?(?P<FEE>[,.0-9]+)\s+
                        (Rebuy:\s[%(LS)s]?(?P<REBUYAMT>[,.0-9]+)\s+)?
                        (Addon:\s[%(LS)s]?(?P<ADDON>[,.0-9]+)\s+)?
                        Table\sType:\s(?P<TYPE>.+?)\s+
                        Tourney\sType:\s(?P<LIMIT>No\sLimit|Limit|LIMIT|Pot\sLimit)\s+
                        Players:\s(?P<ENTRIES>\d+)\s+
                        """ % substitutions ,re.VERBOSE|re.MULTILINE)

    re_Player = re.compile(u"""Place:\s(?P<RANK>[0-9]+),\sPlayer:\s(?P<NAME>.*),\sWon:\s(?P<CUR>[%(LS)s]?)(?P<WINNINGS>[,.0-9]+),( Rebuys: (?P<REBUYS>\d+),)?( Addons: (?P<ADDONS>\d+),)?""" % substitutions)
    re_DateTime = re.compile("""(?P<Y>[0-9]{4})\/(?P<M>[0-9]{2})\/(?P<D>[0-9]{2})[\- ]+(?P<H>[0-9]+):(?P<MIN>[0-9]+):(?P<S>[0-9]+)""", re.MULTILINE)

    codepage = ["utf-8"]

    @staticmethod
    def getSplitRe(self, head):
        re_SplitTourneys = re.compile("PokerTracker")
        return re_SplitTourneys
    
    def parseSummary(self):
        m = self.re_TourneyInfo.search(self.summaryText)
        if m == None:
            tmp = self.summaryText[0:200]
            log.error(_("PokerTrackerSummary.parseSummary: '%s'") % tmp)
            raise FpdbParseError

        #print "DEBUG: m.groupdict(): %s" % m.groupdict()

        mg = m.groupdict()
        if 'SITE'    in mg:
            self.siteName = mg['SITE'].replace('MicroGaming', 'Microgaming')
            self.siteId   = self.SITEIDS.get(self.siteName)
            if self.siteId is None:
                tmp = self.summaryText[0:200]
                log.error(_("PokerTrackerSummary.parseSummary: Unsupported site summary '%s'") % tmp)
                raise FpdbParseError
        if 'TOURNO'    in mg: self.tourNo = mg['TOURNO']
        if 'LIMIT'     in mg and mg['LIMIT'] is not None:
            self.gametype['limitType'] = self.limits[mg['LIMIT']]
        else:
            self.gametype['limitType'] = 'fl'
        if 'TYPE'      in mg: self.tourneyName = mg['TYPE']
        if 'GAME'      in mg: self.gametype['category']  = self.games[mg['GAME']][1]
        if mg['BUYIN'] != None:
            self.buyin = int(100*Decimal(self.clearMoneyString(mg['BUYIN'])))
        if mg['FEE'] != None:
            self.fee   = int(100*Decimal(self.clearMoneyString(mg['FEE'])))
        if 'REBUYAMT'in mg and mg['REBUYAMT'] != None:
            self.isRebuy   = True
            self.rebuyCost = int(100*Decimal(self.clearMoneyString(mg['REBUYAMT'])))
        if 'ADDON' in mg and mg['ADDON'] != None:
            self.isAddOn = True
            self.addOnCost = int(100*Decimal(self.clearMoneyString(mg['ADDON'])))
        if 'ENTRIES'   in mg:
            self.entries = mg['ENTRIES']
            self.prizepool = int(Decimal(self.clearMoneyString(mg['BUYIN']))) * int(self.entries)
        if 'DATETIME'  in mg: 
            m1 = self.re_DateTime.finditer(mg['DATETIME'])
            for a in m1:
                datetimestr = "%s/%s/%s %s:%s:%s" % (a.group('Y'), a.group('M'),a.group('D'),a.group('H'),a.group('MIN'),a.group('S'))
        else:
            datetimestr = "2000/01/01 00:00:00"  # default used if time not found
            
        self.startTime = datetime.datetime.strptime(datetimestr, "%Y/%m/%d %H:%M:%S") # also timezone at end, e.g. " ET"

        if mg['CURRENCY'] == "$":     self.buyinCurrency="USD"
        elif mg['CURRENCY'] == u"€":  self.buyinCurrency="EUR"
        elif not mg['CURRENCY']:      self.buyinCurrency="play"
        if self.buyin == 0:           self.buyinCurrency="FREE"
        self.currency = self.buyinCurrency

        m = self.re_Player.finditer(self.summaryText)
        for a in m:
            mg = a.groupdict()
            #print "DEBUG: a.groupdict(): %s" % mg
            name = mg['NAME']
            rank = int(mg['RANK'])
            winnings = 0
            rebuyCount = 0
            addOnCount = 0
            koCount = 0

            if 'WINNINGS' in mg and mg['WINNINGS'] != None:
                winnings = int(100*Decimal(self.clearMoneyString(mg['WINNINGS'])))
                
            if 'REBUYS' in mg and mg['REBUYS']!=None:
                rebuyCount = int(mg['REBUYS'])
                
            if 'ADDONS' in mg and mg['ADDONS']!=None:
                addOnCount = int(mg['ADDONS'])
                
            if 'CUR' in mg and mg['CUR'] != None:
                if mg['CUR'] == "$":     self.currency="USD"
                elif mg['CUR'] == u"€":  self.currency="EUR"
                elif mg['CUR'] == "FPP": self.currency="PSFP"

            if rank==0:
                #print "stillplaying"
                rank=None
                winnings=None

            #TODO: currency, ko/addon/rebuy count -> need examples!
            #print "DEBUG: addPlayer(%s, %s, %s, %s, None, None, None)" %(rank, name, winnings, self.currency)
            #print "DEBUG: self.buyin: %s self.fee %s" %(self.buyin, self.fee)
            self.addPlayer(rank, name, winnings, self.currency, rebuyCount, addOnCount, koCount)

        #print self

#end class PokerStarsSummary
