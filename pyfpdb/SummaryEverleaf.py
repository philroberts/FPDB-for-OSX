#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2009-2011 Eric Blade, and the FPDB team.

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

import urllib, htmllib, formatter

class AppURLopener(urllib.FancyURLopener):
    version = "Free Poker Database/0.12+"

urllib._urlopener = AppURLopener()

class SummaryParser(htmllib.HTMLParser): # derive new HTML parser
    def get_attr(self, attrs, key):
        #print attrs;
        for a in attrs:
            if a[0] == key:
#                print key,"=",a[1]
                return a[1]
        return None
            
    def __init__(self, formatter) :        # class constructor
        htmllib.HTMLParser.__init__(self, formatter)  # base class constructor
        self.nofill         = True
        self.SiteName       = None
        self.TourneyId      = None
        self.TourneyName    = None
        self.nextStartTime  = False
        self.TourneyStartTime = None
        self.nextEndTime    = False
        self.TourneyEndTime = None
        self.TourneyGameType = None
        self.nextGameType   = False
        self.nextStructure  = False
        self.TourneyStructure = None
        self.nextBuyIn      = False
        self.TourneyBuyIn   = None
        self.nextPool       = False
        self.TourneyPool    = None
        self.nextPlayers    = False
        self.TourneysPlayers = None
        self.nextAllowRebuys = False
        self.TourneyRebuys  = None
        self.parseResultsA  = False
        self.parseResultsB  = False
        self.TempResultStore    = [0,0,0,0]
        self.TempResultPos  = 0
        self.Results        = {}
      
    def start_meta(self, attrs):
        x = self.get_attr(attrs, 'name')
        if x == "author":
            self.SiteName = self.get_attr(attrs, 'content')
            
    def start_input(self, attrs):
        x = self.get_attr(attrs, 'name')
        #print "input name=",x
        if x == "tid":
            self.TourneyId = self.get_attr(attrs, 'value')
    
    def start_h1(self, attrs):
        if self.TourneyName is None:
            self.save_bgn()
        
    def end_h1(self):
        if self.TourneyName is None:
            self.TourneyName = self.save_end()
            
    def start_div(self, attrs):
        x = self.get_attr(attrs, 'id')
        if x == "result":
            self.parseResultsA = True
            
    def end_div(self): # TODO: Can we get attrs in the END tag too? I don't know? Would be useful to make SURE we're closing the right div ..
        if self.parseResultsA:
            self.parseResultsA = False # TODO: Should probably just make sure everything is false at this point, since we're not going to be having anything in the middle of a DIV.. oh well
            
    def start_td(self, attrs):
        self.save_bgn()
        
    def end_td(self):
        x = self.save_end()
        
        if not self.parseResultsA:        
            if not self.nextStartTime and x == "Start:":
                self.nextStartTime = True
            elif self.nextStartTime:
                self.TourneyStartTime = x
                self.nextStartTime = False
            
            if not self.nextEndTime and x == "Finished:":
                self.nextEndTime = True
            elif self.nextEndTime:
                self.TourneyEndTime = x
                self.nextEndTime = False
                
            if not self.nextGameType and x == "Game Type:":
                self.nextGameType = True
            elif self.nextGameType:
                self.TourneyGameType = x
                self.nextGameType = False
                
            if not self.nextStructure and x == "Limit:":
                self.nextStructure = True
            elif self.nextStructure:
                self.TourneyStructure = x
                self.nextStructure = False
                
            if not self.nextBuyIn and x == "Buy In / Fee:":
                self.nextBuyIn = True
            elif self.nextBuyIn:
                self.TourneyBuyIn = x # TODO: Further parse the fee from this
                self.nextBuyIn = False
            
            if not self.nextPool and x == "Prize Money:":
                self.nextPool = True
            elif self.nextPool:
                self.TourneyPool = x
                self.nextPool = False
                
            if not self.nextPlayers and x == "Player Count:":
                self.nextPlayers = True
            elif self.nextPlayers:
                self.TourneysPlayers = x
                self.nextPlayers = False
                
            if not self.nextAllowRebuys and x == "Rebuys possible?:":
                self.nextAllowRebuys = True
            elif self.nextAllowRebuys:
                self.TourneyRebuys = x
                self.nextAllowRebuys = False
                
        else: # parse results
            if x == "Won Prize":
                self.parseResultsB = True # ok, NOW we can start parsing the results
            elif self.parseResultsB:
                if x[0] == "$": # first char of the last of each row is the dollar sign, so now we can put it into a sane order
                    self.TempResultPos = 0
                    name = self.TempResultStore[1]
                    place = self.TempResultStore[0]
                    time = self.TempResultStore[2]
#                    print self.TempResultStore
                    
                    self.Results[name] = {}
                    self.Results[name]['place'] = place
                    self.Results[name]['winamount'] = x
                    self.Results[name]['outtime'] = time
                    
#                    self.Results[self.TempResultStore[1]] = {}
#                    self.Results[self.TempResultStore[1]]['place'] = self.TempResultStore[self.TempResultStore[0]]
#                    self.Results[self.TempResultStore[1]]['winamount'] = x
#                    self.Results[self.TempResultStore[1]]['outtime'] = self.TempResultStore[self.TempResultStore[2]]
                else:
                    self.TempResultStore[self.TempResultPos] = x
                    self.TempResultPos += 1

class EverleafSummary:
    def __init__(self):
        if __name__ != "__main__":
            self.main()
            
    def main(self, id="785646"):
        file = urllib.urlopen("http://www.poker4ever.com/en.tournaments.tournament-statistics?tid="+id)
        self.parser = SummaryParser(formatter.NullFormatter())
        self.parser.feed(file.read())
        print "site=",self.parser.SiteName, "tourneyname=", self.parser.TourneyName, "tourneyid=", self.parser.TourneyId
        print "start time=",self.parser.TourneyStartTime, "end time=",self.parser.TourneyEndTime
        print "structure=", self.parser.TourneyStructure, "game type=",self.parser.TourneyGameType
        print "buy-in=", self.parser.TourneyBuyIn, "rebuys=", self.parser.TourneyRebuys, "total players=", self.parser.TourneysPlayers, "pool=", self.parser.TourneyPool
        print "results=", self.parser.Results
    
    
if __name__ == "__main__":
    me = EverleafSummary()
    me.main()
