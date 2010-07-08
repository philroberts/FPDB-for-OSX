#!/usr/bin/python
# -*- coding: utf-8 -*-

#Copyright 2008-2010 Steffen Schaumburg
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

"""pokerstars-specific summary parsing code"""

from decimal import Decimal

from PokerStarsToFpdb import PokerStars
from TourneySummary import *

class PokerStarsSummary(TourneySummary):
    re_TourNo = re.compile("\#[0-9]+,")
    re_Entries = re.compile("[0-9]+")
    re_Prizepool = re.compile("\$[0-9]+\.[0-9]+")
    re_Player = re.compile(u"""(?P<RANK>[0-9]+):\s(?P<NAME>.*)\s\(.*\),(\s\$(?P<WINNINGS>[0-9]+\.[0-9]+)\s\()?""")
    re_BuyInFee = re.compile("(?P<BUYIN>[0-9]+\.[0-9]+).*(?P<FEE>[0-9]+\.[0-9]+)")
    # = re.compile("")

    def parseSummary(self):
        lines=self.summaryText.splitlines()
        
        self.tourNo = self.re_TourNo.findall(lines[0])[0][1:-1] #ignore game and limit type as thats not recorded
        
        if lines[1].find("$")!=-1:
            self.currency="USD"
        elif lines[1].find(u"€")!=-1:
            self.currency="EUR"
        else:
            raise fpdbParseError("didn't recognise buyin currency")
        
        result=self.re_BuyInFee.search(lines[1])
        result=result.groupdict()
        self.buyin=int(100*Decimal(result['BUYIN']))
        self.fee=int(100*Decimal(result['FEE']))
        
        self.entries = self.re_Entries.findall(lines[2])[0]
        
        self.prizepool = self.re_Prizepool.findall(lines[3])[0]
        self.prizepool = self.prizepool[1:-3]+self.prizepool[-2:]
        
        #TODO: lines 4 and 5 are dates, read them
        
        for i in range(6,len(lines)-2): #lines with rank and winnings info
            if lines[i].find(":")==-1:
                break
            result=self.re_Player.search(lines[i])
            result=result.groupdict()
            rank=result['RANK']
            name=result['NAME']
            winnings=result['WINNINGS']
            if winnings:
                winnings=int(100*Decimal(winnings))
            else:
                winnings=0
            
            self.addPlayer(rank, name, winnings, "USD", None, None, None)#TODO: currency, ko/addon/rebuy count -> need examples!
    #end def parseSummary
#end class PokerStarsSummary
