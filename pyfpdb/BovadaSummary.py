#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Copyright 2008-2013 Chaz Littlejohn
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
import BovadaToFpdb

class BovadaSummary(TourneySummary):
    
    substitutions = {
                         'LEGAL_ISO' : "USD",      # legal ISO currency codes
                                'LS' : u"\$|", # legal currency symbols - Euro(cp1252, utf-8)
                               'PLYR': r'(?P<PNAME>.+?)',
                                'CUR': u"(\$|)",
                                'NUM' :u".,\d",
                        }
    codepage = ("utf8", "cp1252")
    
    re_Identify = re.compile(u'(Bovada|Bodog(\sUK|\sCanada|88)?)\sHand')
    re_AddOn = re.compile(r"^%(PLYR)s  ?\[ME\] : Addon (?P<ADDON>[%(NUM)s]+)" % substitutions, re.MULTILINE)
    re_Rebuyin = re.compile(r"%(PLYR)s  ?\[ME\] : Rebuyin (?P<REBUY>[%(NUM)s]+)" % substitutions, re.MULTILINE)
    re_Ranking = re.compile(r"%(PLYR)s  ?\[ME\] : Ranking (?P<RANK>[%(NUM)s]+)" % substitutions, re.MULTILINE)
    re_Winnings = re.compile(r"%(PLYR)s  ?\[ME\] : Prize Cash \[(?P<WINNINGS>%(CUR)s[%(NUM)s]+)\]" % substitutions, re.MULTILINE)   
    
    @staticmethod
    def getSplitRe(self, head):
        re_SplitTourneys = re.compile("PokerStars Tournament ")
        return re_SplitTourneys
    
    def parseSummary(self):
        obj = getattr(BovadaToFpdb, "Bovada", None)
        hhc = obj(self.config, in_path = self.in_path, sitename = None, autostart = False)
        m = hhc.re_GameInfo.search(self.summaryText)
        if m == None:
            tmp = self.summaryText[0:200]
            log.error(_("BovadaSummary.parseSummary: '%s'") % tmp)
            raise FpdbParseError
        
        info = {}
        info.update(m.groupdict())
        m = hhc.re_Buyin.search(self.in_path)
        if m: info.update(m.groupdict())
        
        if info['TOURNO'] is None:
            tmp = self.summaryText[0:200]
            log.error(_("BovadaSummary.parseSummary: Text does not appear to be a tournament '%s'") % tmp)
            raise FpdbParseError
        else:
            self.tourNo = info['TOURNO']
            if 'LIMIT' in info:
                if not info['LIMIT']:
                    self.gametype['limitType'] = 'nl'
                else:
                    self.gametype['limitType'] = hhc.limits[info['LIMIT']]
            if 'GAME' in info:
                self.gametype['category'] = hhc.games[info['GAME']][1]
                 
            if 'CURRENCY' in info and info['CURRENCY']:
                self.buyinCurrency = hhc.currencies[info['CURRENCY']]
            self.currency = self.buyinCurrency
            
            if 'DATETIME' in info and info['CURRENCY'] is not None:
                m1 = hhc.re_DateTime.finditer(info['DATETIME'])
                datetimestr = "2000/01/01 00:00:00"  # default used if time not found
                for a in m1:
                    datetimestr = "%s/%s/%s %s:%s:%s" % (a.group('Y'), a.group('M'),a.group('D'),a.group('H'),a.group('MIN'),a.group('S'))
                    #tz = a.group('TZ')  # just assume ET??
                    #print "   tz = ", tz, " datetime =", datetimestr
                self.startTime = datetime.datetime.strptime(datetimestr, "%Y/%m/%d %H:%M:%S") # also timezone at end, e.g. " ET"
                self.startTime = HandHistoryConverter.changeTimezone(self.startTime, "ET", "UTC")
                
            self.buyin = 0
            self.fee   = 0
            self.prizepool = None
            self.entries   = None
            
            if self.currency is None:
                self.buyinCurrency = "FREE"
            
            if 'BUYIN' in info and info['BUYIN'] is not None:
                if info['BIAMT'] is not None and info['BIRAKE'] is not None:
                    if info['BUYIN'].find("$")!=-1:
                        self.buyinCurrency="USD"
                    elif re.match("^[0-9+]*$", info['BUYIN']):
                        self.buyinCurrency="play"
                    else:
                        log.error(_("BovadaSummary.parseSummary: Failed to detect currency"))
                        raise FpdbParseError
                    self.currency = self.buyinCurrency

                    info['BIAMT'] = info['BIAMT'].strip(u'$')
                    
                    if info['BIRAKE']:
                        info['BIRAKE'] = info['BIRAKE'].strip(u'$')
                    else:
                        info['BIRAKE'] = '0'

                    self.buyin = int(100*Decimal(info['BIAMT']))
                    self.fee = int(100*Decimal(info['BIRAKE']))
                    
                    if info['TOURNAME'] is not None:
                        tourneyNameFull = info['TOURNAME'] + ' - ' + info['BIAMT'] + '+' + info['BIRAKE']
                        self.tourneyName = tourneyNameFull
                        
                        if 'TOURNAME' in info and 'Rebuy' in info['TOURNAME']:
                            self.isAddOn, self.isRebuy = True, True
                            self.rebuyCost = self.buyin
                            self.addOnCost = self.buyin
            
            rank, winnings, rebuys, addons = None, None, 0, 0
            
            m = self.re_Ranking.search(self.summaryText)
            if m and m.group('RANK') is not None: 
                rank = int(m.group('RANK'))
                winnings = 0
                
            m = self.re_Winnings.search(self.summaryText)
            if m and m.group('WINNINGS') is not None: 
                if m.group('WINNINGS').find("$")!=-1:
                    self.currency="USD"
                elif re.match("^[0-9+]*$", m.group('WINNINGS')):
                    self.currency="play"
                winnings = int(100*Decimal(self.clearMoneyString(m.group('WINNINGS'))))
                
            m = self.re_Rebuyin.finditer(self.summaryText)
            for a in m: rebuys += 1
                
            m = self.re_AddOn.finditer(self.summaryText)
            for a in m: addons += 1
                            
            self.addPlayer(rank, 'Hero', winnings, self.currency, rebuys, addons, 0)
        