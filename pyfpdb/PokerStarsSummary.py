#!/usr/bin/python2
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

from TourneySummary import *
from PokerStarsToFpdb import PokerStars

class PokerStarsSummary(TourneySummary):
    sitename = "PokerStars"
    siteId   = 2
    limits = PokerStars.limits
    games = PokerStars.games
    # = PokerStars.
    
    
    re_TourNo = re.compile("\#[0-9]+,")
    re_Entries = re.compile("[0-9]+")
    re_Prizepool = re.compile("\$[0-9]+\.[0-9]+")
    re_Rank = re.compile("[0-9]+:")
    re_Name = re.compile(":.*\(")
    re_Winnings = re.compile("\$[0-9]+\.[0-9]+ \(")
    # = re.compile("")

    def parseSummary(self):
        lines=self.summaryText.splitlines()
        
        self.tourNo = self.re_TourNo.findall(lines[0])[0][1:-1] #ignore game and limit type as thats not recorded
        
        #ignore lines[1] as buyin/fee are already recorded by HHC
        
        self.entries = self.re_Entries.findall(lines[2])[0]
        
        self.prizepool = self.re_Prizepool.findall(lines[3])[0]
        self.prizepool = self.prizepool[1:-3]+self.prizepool[-2:]
        
        #TODO: lines 4 and 5 are dates, read them
        
        for i in range(6,len(lines)-2): #lines with rank and winnings info
            if lines[i].find(":")==-1:
                break
            rank=self.re_Rank.findall(lines[i])[0][:-1]
            start = lines[i].find(":")+2
            end = lines[i].find("(")-1
            name=lines[i][start:end]
            winnings=self.re_Winnings.findall(lines[i])
            if winnings:
                winnings=winnings[0][1:-5]+winnings[0][-4:-2]
            else:
                winnings=0
            
            self.addPlayer(rank, name, winnings, "USD", -1, -1, -1)
            
    #end def parseSummary
        
#end class PokerStarsSummary