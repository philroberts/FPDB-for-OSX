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
import datetime

from Exceptions import FpdbParseError
import PokerStarsToFpdb
from TourneySummary import *

class PokerStarsSummary(TourneySummary):
    re_TourNo = re.compile("\#[0-9]+,")
    re_Entries = re.compile("[0-9]+")
    re_Prizepool = re.compile("\$[0-9]+\.[0-9]+")
    re_Player = re.compile("""(?P<RANK>[0-9]+):\s(?P<NAME>.*)\s\(.*\),(\s\$(?P<WINNINGS>[0-9]+\.[0-9]+)\s\()?""")
    re_BuyInFee = re.compile("(?P<BUYIN>[0-9]+\.[0-9]+).*(?P<FEE>[0-9]+\.[0-9]+)")
    re_FPP = re.compile("(?P<FPP>[0-9]+)\sFPP")
    #note: the dollar and cent in the below line are currency-agnostic
    re_Added = re.compile("(?P<DOLLAR>[0-9]+)\.(?P<CENT>[0-9]+)\s(?P<CURRENCY>[A-Z]+)(\sadded\sto\sthe\sprize\spool\sby\sPokerStars)")
    re_DateTime = re.compile("(?P<Y>[0-9]{4})\/(?P<M>[0-9]{2})\/(?P<D>[0-9]{2})[\- ]+(?P<H>[0-9]+):(?P<MIN>[0-9]+):(?P<S>[0-9]+)")
    # = re.compile("")

    def parseSummary(self):
        lines=self.summaryText.splitlines()
        
        self.tourNo = self.re_TourNo.findall(lines[0])[0][1:-1] #ignore game and limit type as thats not recorded
        print "tourNo:",self.tourNo
        
        if lines[1].find("$")!=-1: #TODO: move this into a method and call that from PokerStarsToFpdb.py:269    if hand.buyinCurrency=="USD" etc.
            self.currency="USD"
        elif lines[1].find(u"€")!=-1:
            self.currency="EUR"
        elif lines[1].find("FPP")!=-1:
            self.currency="PSFP"
        else:
            raise FpdbParseError("didn't recognise buyin currency in:"+lines[1])
        
        if self.currency=="USD" or self.currency=="EUR":
            result=self.re_BuyInFee.search(lines[1])
            result=result.groupdict()
            self.buyin=int(100*Decimal(result['BUYIN']))
            self.fee=int(100*Decimal(result['FEE']))
        elif self.currency=="PSFP":
            result=self.re_FPP.search(lines[1])
            result=result.groupdict()
            self.buyin=int(Decimal(result['FPP']))
            self.fee=0
        
        currentLine=2
        self.entries = self.re_Entries.findall(lines[currentLine])[0]
        currentLine+=1 #note that I chose to make the code keep state (the current line number)
                       #as that means it'll fail rather than silently skip potentially valuable information
        print "after entries lines[currentLine]", lines[currentLine]
        
        result=self.re_Added.search(lines[currentLine])
        if result:
            result=result.groupdict()
            self.added=100*int(Decimal(result['DOLLAR']))+int(Decimal(result['CENT']))
            self.addedCurrency=result['CURRENCY']
            #print "TODO: implement added:",self.added,self.addedCurrency
            currentLine+=1
        print "after added/entries lines[currentLine]", lines[currentLine]
        
        result=self.re_Prizepool.findall(lines[currentLine])
        if result:
            print "prizepool result", result
            self.prizepool = result[0]
            self.prizepool = self.prizepool[1:-3]+self.prizepool[-2:]
            currentLine+=1
        #print "after prizepool lines[currentLine]", lines[currentLine]
        
        result=self.re_DateTime.search(lines[currentLine])
        result=result.groupdict()
        datetimestr = "%s/%s/%s %s:%s:%s" % (result['Y'], result['M'],result['D'],result['H'],result['MIN'],result['S'])
        self.startTime= datetime.datetime.strptime(datetimestr, "%Y/%m/%d %H:%M:%S") # also timezone at end, e.g. " ET"
        self.startTime = PokerStarsToFpdb.removeET(self.startTime)
        currentLine+=1
        
        result=self.re_DateTime.search(lines[currentLine])
        if result:
            print "endtime result", result
            result=result.groupdict()
            datetimestr = "%s/%s/%s %s:%s:%s" % (result['Y'], result['M'],result['D'],result['H'],result['MIN'],result['S'])
            self.endTime= datetime.datetime.strptime(datetimestr, "%Y/%m/%d %H:%M:%S") # also timezone at end, e.g. " ET"
            currentLine+=1
        
        for i in range(currentLine,len(lines)-2): #lines with rank and winnings info
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
            
            self.addPlayer(rank, name, winnings, self.currency, None, None, None)#TODO: currency, ko/addon/rebuy count -> need examples!
    #end def parseSummary
#end class PokerStarsSummary
