#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Copyright 2016 Chaz Littlejohn
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

"""winning poker specific summary parsing code"""

import L10n
_ = L10n.get_translation()

from decimal_wrapper import Decimal
import datetime

from Exceptions import FpdbParseError
from HandHistoryConverter import *
from TourneySummary import *

class WinningSummary(TourneySummary):
    sym = {
        'USD': "\$", 
        'T$': "", 
        "play": ""
    } 
    substitutions = {
        'LEGAL_ISO' : "TB|CP",  # legal ISO currency codes
        'LS' : u"\$|", # legal currency symbols
        'PLYR': r'(?P<PNAME>.+?)',
        'NUM' :u".,\dK",
    }
    games = {# base, category
        "Hold'em" : ('hold','holdem'),
        'Omaha' : ('hold','omahahi'),
        'Omaha HiLow' : ('hold','omahahilo'),
        'Seven Cards Stud' : ('stud','studhi'),
        'Seven Cards Stud HiLow' : ('stud','studhilo')
    }
    
    speeds = {
        'Turbo': 'Turbo',
        'Hyper Turbo': 'Hyper',
        'Regular': 'Normal'
    }
    
    re_Identify = re.compile(ur'<link\sid="ctl00_CalendarTheme"')
    
    re_HTMLPlayer = re.compile(ur"Player\sDetails:\s%(PLYR)s</a>" % substitutions, re.IGNORECASE)
                        
    re_HTMLTourneyInfo = re.compile(
        ur'<td>(?P<TOURNO>[0-9]+)</td>' \
        ur'<td>(?P<GAME>Hold\'em|Omaha|Omaha\sHiLow|Seven\sCards\sStud|Seven\sCards\sStud\sHiLow)</td>' \
        ur'<td>(?P<TOURNAME>.*)</td>' \
        ur'<td>(?P<CURRENCY>[%(LS)s])(?P<BUYIN>[%(NUM)s]+)</td>' \
        ur'<td>[%(NUM)s]+</td>' \
        ur'<td>[%(NUM)s]+</td>' \
        ur'<td>[%(NUM)s]+</td>' \
        ur'<td>[%(LS)s](?P<FEE>[%(NUM)s]+)</td>' \
        ur'<td>[%(NUM)s]+</td>' \
        ur'<td>[%(NUM)s]+</td>' \
        ur'<td>[%(NUM)s]+</td>' \
        ur'<td>[%(LS)s](?P<REBUYS>[%(NUM)s]+)</td>' \
        ur'<td>[%(NUM)s]+</td>' \
        ur'<td>[%(NUM)s]+</td>' \
        ur'<td>[%(NUM)s]+</td>' \
        ur'<td>[%(LS)s](?P<ADDONS>[%(NUM)s]+)</td>' \
        ur'<td>[%(NUM)s]+</td>' \
        ur'<td>[%(NUM)s]+</td>' \
        ur'<td>[%(NUM)s]+</td>' \
        ur'<td>[%(LS)s](?P<WINNINGS>[%(NUM)s]+)</td>' \
        ur'<td>[%(NUM)s]+</td>' \
        ur'<td>[%(NUM)s]+</td>' \
        ur'<td>[%(NUM)s]+</td>' \
        ur'<td>.*</td>' \
        ur'<td>(?P<TOURNEYSTART>.*)</td>' \
        ur'<td>(?P<TOURNEYEND>.*)</td>' \
        ur'<td>.*</td>' # duration
        % substitutions,  
        re.VERBOSE|re.IGNORECASE
    )

    re_HTMLTourneyExtraInfo = re.compile(u"""
        ^([%(LS)s]|)?(?P<GUAR>[%(NUM)s]+)\s
        ((?P<GAMEEXTRA>Holdem|PLO|PLO8|Omaha\sHi/Lo|Omaha|PL\sOmaha|PL\sOmaha\sHi/Lo|PLO\sHi/Lo)\s?)?
        ((?P<SPECIAL>(GTD|Freeroll|FREEBUY|Freebuy))\s?)?
        ((?P<SPEED>(Turbo|Hyper\sTurbo|Regular))\s?)?
        ((?P<MAX>(\d+\-Max|Heads\-up|Heads\-Up))\s?)?
        (?P<OTHER>.*?)
        """ % substitutions,  
        re.VERBOSE|re.MULTILINE
    )
    
    re_HTMLDateTime = re.compile("(?P<M>[0-9]+)\/(?P<D>[0-9]+)\/(?P<Y>[0-9]{4})[\- ]+(?P<H>[0-9]+):(?P<MIN>[0-9]+):(?P<S>[0-9]+) (?P<AMPM>(AM|PM))", re.MULTILINE)
    re_HTMLTourNo = re.compile("\s+<td>(?P<TOURNO>[0-9]+)</td>", re.DOTALL)
    
    codepage = ["utf8", "cp1252"]

    @staticmethod
    def getSplitRe(self, head):
        return re.compile("</tr><tr")

    def parseSummary(self):
        info = {}
        m1 = self.re_HTMLPlayer.search(self.header)
        m2 = self.re_HTMLTourneyInfo.search(self.summaryText)
        if m1 == None or m2==None:
            if self.re_HTMLTourNo.search(self.summaryText):
                tmp1 = self.header[0:200] if m1 == None else 'NA'
                tmp2 = self.summaryText[0:200] if m2 == None else 'NA'
                log.error(_("WinningSummary.parseSummaryHtml: '%s' '%s") % (tmp1, tmp2))
                raise FpdbParseError
            else:
                raise FpdbHandPartial   
        #print m2.groupdict()
        info.update(m1.groupdict())
        info.update(m2.groupdict())
        self.parseSummaryArchive(info)
        
    def parseSummaryArchive(self, info):        
        #if 'SNG' in info and "Sit & Go" in info['SNG']:
        #    self.isSng = True
        
        if 'TOURNAME' in info and info['TOURNAME'] != None:
            self.tourneyName = info['TOURNAME']
            m3 = self.re_HTMLTourneyExtraInfo.search(self.tourneyName)
            if m3 != None:
                info.update(m3.groupdict())
                
        if 'GAME'      in info: 
            self.gametype['category']  = self.games[info['GAME']][1]
                
        if self.gametype['category'] == 'holdem':
            self.gametype['limitType'] = 'nl'
        elif self.gametype['category'] == 'omaha':
            self.gametype['limitType'] = 'pl'
        else:
            self.gametype['limitType'] = 'fl'
            
        self.buyinCurrency="USD"
        if 'SPECIAL' in info and info['SPECIAL'] != None:
            if info['SPECIAL'] in ('Freeroll', 'FREEBUY', 'Freebuy'):
                self.buyinCurrency="FREE"
            self.guaranteeAmt = int(100*Decimal(self.clearMoneyString(info['GUAR'])))
        
        if 'TOURNO'    in info: 
            self.tourNo = info['TOURNO']
        if info['BUYIN'] != None:
            self.buyin = int(100*Decimal(self.clearMoneyString(info['BUYIN'])))
        if info['FEE'] != None:
            self.fee   = int(100*Decimal(self.clearMoneyString(info['FEE'])))
            
        if ('REBUYS' in info and Decimal(self.clearMoneyString(info['REBUYS'].replace(" ", "")))>0):
            self.isRebuy   = True
            self.rebuyCost = self.buyin
            
        if ('ADDONS' in info and Decimal(self.clearMoneyString(info['ADDONS'].replace(" ", "")))>0):
            self.isAddOn   = True
            self.addOnCost = self.buyin

        if 'MAX' in info and info['MAX'] != None:
            n = info['MAX'].replace('-Max', '')
            if n in ('Heads-up', 'Heads-Up'):
                self.maxseats = 2
            else:
                self.maxseats = int(n)
        else:
            self.maxseats = 10

        if 'SPEED' in info and info['SPEED'] != None:
            self.speed = self.speeds[info['SPEED']]  
            self.isSng = True
    
        if "On Demand" in self.tourneyName:
            self.isOnDemand = True
            
        if " KO" in self.tourneyName or "Knockout" in self.tourneyName:
            self.isKO = True
            
        if "R/A" in self.tourneyName:
            self.isRebuy = True
            self.isAddOn = True
            self.addOnCost = self.buyin
            self.rebuyCost = self.buyin
            
        if 'TOURNEYSTART'  in info: m4 = self.re_HTMLDateTime.finditer(info['TOURNEYSTART'])
        datetimestr = None  # default used if time not found
        for a in m4:
            datetimestr = "%s/%s/%s %s:%s:%s %s" % (a.group('Y'), a.group('M'),a.group('D'),a.group('H'),a.group('MIN'),a.group('S'),a.group('AMPM'))
            self.startTime = datetime.datetime.strptime(datetimestr, "%Y/%m/%d %I:%M:%S %p") # also timezone at end, e.g. " ET"
            self.startTime = HandHistoryConverter.changeTimezone(self.startTime, self.import_parameters['timezone'], "UTC")          
            
        if 'TOURNEYEND'  in info: m5 = self.re_HTMLDateTime.finditer(info['TOURNEYEND'])
        datetimestr = None  # default used if time not found
        for a in m5:
            datetimestr = "%s/%s/%s %s:%s:%s %s" % (a.group('Y'), a.group('M'),a.group('D'),a.group('H'),a.group('MIN'),a.group('S'),a.group('AMPM'))
            self.endTime = datetime.datetime.strptime(datetimestr, "%Y/%m/%d %I:%M:%S %p") # also timezone at end, e.g. " ET"
            self.endTime = HandHistoryConverter.changeTimezone(self.endTime, self.import_parameters['timezone'], "UTC")
        
        
        self.currency="USD"        
        winnings = 0
        rebuyCount = 0
        addOnCount = 0
        koCount = 0
        rank = 0 #fix with lookups
        
        if 'WINNINGS' in info and info['WINNINGS'] != None:
            winnings = int(100*Decimal(self.clearMoneyString(info['WINNINGS'])))
            
        if self.isRebuy and self.rebuyCost > 0:
            rebuyAmt = int(100*Decimal(self.clearMoneyString(info['REBUYS'].replace(" ", ""))))
            rebuyCount = rebuyAmt/self.rebuyCost
            
        if self.isAddOn and self.addOnCost > 0:
            addOnAmt = int(100*Decimal(self.clearMoneyString(info['ADDONS'].replace(" ", ""))))
            addOnCount = addOnAmt/self.addOnCost
            
        self.hero = info['PNAME']
            
        self.addPlayer(9999, info['PNAME'], winnings, self.currency, rebuyCount, addOnCount, koCount)
        
