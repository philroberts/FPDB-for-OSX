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
from HandHistoryConverter import *
import PokerStarsToFpdb
from TourneySummary import *

import locale
lang=locale.getdefaultlocale()[0][0:2]
if lang=="en":
    def _(string): return string
else:
    import gettext
    try:
        trans = gettext.translation("fpdb", localedir="locale", languages=[lang])
        trans.install()
    except IOError:
        def _(string): return string

class PokerStarsSummary(TourneySummary):
    limits = { 'No Limit':'nl', 'Pot Limit':'pl', 'Limit':'fl', 'LIMIT':'fl' }
    games = {                          # base, category
                              "Hold'em" : ('hold','holdem'), 
                                'Omaha' : ('hold','omahahi'),
                          'Omaha Hi/Lo' : ('hold','omahahilo'),
                                 'Razz' : ('stud','razz'), 
                                 'RAZZ' : ('stud','razz'),
                          '7 Card Stud' : ('stud','studhi'),
                    '7 Card Stud Hi/Lo' : ('stud','studhilo'),
                               'Badugi' : ('draw','badugi'),
              'Triple Draw 2-7 Lowball' : ('draw','27_3draw'),
                          '5 Card Draw' : ('draw','fivedraw')
               }

    substitutions = {
                     'LEGAL_ISO' : "USD|EUR|GBP|CAD|FPP",    # legal ISO currency codes
                            'LS' : "\$|\xe2\x82\xac|"        # legal currency symbols - Euro(cp1252, utf-8)
                    }

    re_SplitGames = re.compile("^PokerStars")
    
    re_TourNo = re.compile("\#(?P<TOURNO>[0-9]+),")

    re_TourneyInfo = re.compile(u"""
                        \#(?P<TOURNO>[0-9]+),\s
                        (?P<LIMIT>No\sLimit|Limit|LIMIT|Pot\sLimit)\s
                        (?P<GAME>Hold\'em|Razz|RAZZ|7\sCard\sStud|7\sCard\sStud\sHi/Lo|Omaha|Omaha\sHi/Lo|Badugi|Triple\sDraw\s2\-7\sLowball|5\sCard\sDraw)\s
                        (?P<DESC>[ a-zA-Z]+\s)?
                        (Buy-In:\s\$(?P<BUYIN>[.0-9]+)(\/\$(?P<FEE>[.0-9]+))?\s)?
                        (?P<ENTRIES>[0-9]+)\splayers\s
                        (\$?(?P<ADDED>[.\d]+)\sadded\sto\sthe\sprize\spool\sby\sPokerStars\.com\s)?
                        (Total\sPrize\sPool:\s\$?(?P<PRIZEPOOL>[.0-9]+)\s)?
                        (Target\sTournament\s.*)?
                        Tournament\sstarted\s-\s
                        (?P<Y>[0-9]{4})\/(?P<M>[0-9]{2})\/(?P<D>[0-9]{2})[\-\s]+(?P<H>[0-9]+):(?P<MIN>[0-9]+):(?P<S>[0-9]+)\s?\(?(?P<TZ>[A-Z]+)\)\s
                               """ % substitutions ,re.VERBOSE|re.MULTILINE|re.DOTALL)

    re_Currency = re.compile(u"""(?P<CURRENCY>[%(LS)s]|FPP)""" % substitutions)

    re_Player = re.compile(u"""(?P<RANK>[0-9]+):\s(?P<NAME>.*)\s\(.*\),(\s)(\$(?P<WINNINGS>[0-9]+\.[0-9]+))?(?P<STILLPLAYING>still\splaying)?((?P<TICKET>Tournament\sTicket)\s\(WSOP\sStep\s(?P<LEVEL>\d)\))?""")

    re_DateTime = re.compile("\[(?P<Y>[0-9]{4})\/(?P<M>[0-9]{2})\/(?P<D>[0-9]{2})[\- ]+(?P<H>[0-9]+):(?P<MIN>[0-9]+):(?P<S>[0-9]+)")

    re_Entries = re.compile("[0-9]+")
    re_Prizepool = re.compile("\$[0-9]+\.[0-9]+")
    re_BuyInFee = re.compile("(?P<BUYIN>[0-9]+\.[0-9]+).*(?P<FEE>[0-9]+\.[0-9]+)")
    re_FPP = re.compile("(?P<FPP>[0-9]+)\sFPP")
    #note: the dollar and cent in the below line are currency-agnostic
    re_Added = re.compile("(?P<DOLLAR>[0-9]+)\.(?P<CENT>[0-9]+)\s(?P<CURRENCY>[A-Z]+)(\sadded\sto\sthe\sprize\spool\sby\sPokerStars)")
    re_DateTimeET = re.compile("(?P<Y>[0-9]{4})\/(?P<M>[0-9]{2})\/(?P<D>[0-9]{2})[\- ]+(?P<H>[0-9]+):(?P<MIN>[0-9]+):(?P<S>[0-9]+)")
    re_GameInfo = re.compile(u""".+(?P<LIMIT>No\sLimit|Limit|LIMIT|Pot\sLimit)\s(?P<GAME>Hold\'em|Razz|RAZZ|7\sCard\sStud|7\sCard\sStud\sHi/Lo|Omaha|Omaha\sHi/Lo|Badugi|Triple\sDraw\s2\-7\sLowball|5\sCard\sDraw)""")

    def parseSummary(self):
        lines=self.summaryText.splitlines()
        
        self.tourNo = self.re_TourNo.findall(lines[0])[0][1:-1] #ignore game and limit type as thats not recorded
        
        result=self.re_GameInfo.search(lines[0])
        result=result.groupdict()
        self.gametype['limitType']=self.limits[result['LIMIT']]
        self.gametype['category']=self.games[result['GAME']][1]
        
        if lines[1].find("$")!=-1: #TODO: move this into a method and call that from PokerStarsToFpdb.py:269    if hand.buyinCurrency=="USD" etc.
            self.currency="USD"
        elif lines[1].find(u"€")!=-1:
            self.currency="EUR"
        elif lines[1].find("FPP")!=-1:
            self.currency="PSFP"
        else:
            raise FpdbParseError(_("didn't recognise buyin currency in:")+lines[1])
        
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
        #print "after entries lines[currentLine]", lines[currentLine]

        result=self.re_Added.search(lines[currentLine])
        if result:
            result=result.groupdict()
            self.added=100*int(Decimal(result['DOLLAR']))+int(Decimal(result['CENT']))
            self.addedCurrency=result['CURRENCY']
            currentLine+=1
        else:
            self.added=0
            self.addedCurrency="NA"
        #print "after added/entries lines[currentLine]", lines[currentLine]

        result=self.re_Prizepool.findall(lines[currentLine])
        if result:
            self.prizepool = result[0]
            self.prizepool = self.prizepool[1:-3]+self.prizepool[-2:]
            currentLine+=1
        #print "after prizepool lines[currentLine]", lines[currentLine]
        
        useET=False
        result=self.re_DateTime.search(lines[currentLine])
        if not result:
            print _("in not result starttime")
            useET=True
            result=self.re_DateTimeET.search(lines[currentLine])
        result=result.groupdict()
        datetimestr = "%s/%s/%s %s:%s:%s" % (result['Y'], result['M'],result['D'],result['H'],result['MIN'],result['S'])
        self.startTime= datetime.datetime.strptime(datetimestr, "%Y/%m/%d %H:%M:%S") # also timezone at end, e.g. " ET"
        self.startTime = HandHistoryConverter.changeTimezone(self.startTime, "ET", "UTC")
        currentLine+=1

        if useET:
            result=self.re_DateTimeET.search(lines[currentLine])
        else:
            result=self.re_DateTime.search(lines[currentLine])
        if result:
            result=result.groupdict()
            datetimestr = "%s/%s/%s %s:%s:%s" % (result['Y'], result['M'],result['D'],result['H'],result['MIN'],result['S'])
            self.endTime= datetime.datetime.strptime(datetimestr, "%Y/%m/%d %H:%M:%S") # also timezone at end, e.g. " ET"
            self.endTime = HandHistoryConverter.changeTimezone(self.endTime, "ET", "UTC")
        currentLine+=1
        
        if lines[currentLine].find("Tournament is still in progress")!=-1:
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
            
            if result['STILLPLAYING']:
                #print "stillplaying"
                rank=None
                winnings=None
            
            self.addPlayer(rank, name, winnings, self.currency, None, None, None)#TODO: currency, ko/addon/rebuy count -> need examples!
    #end def parseSummary

    def parseSummaryFile(self):
        m = self.re_TourneyInfo.search(self.summaryText)
        if m == None:
            tmp = self.summaryText[0:200]
            log.error(_("parseSummaryFile: Unable to recognise Tourney Info: '%s'") % tmp)
            log.error(_("parseSummaryFile: Raising FpdbParseError"))
            raise FpdbParseError(_("Unable to recognise Tourney Info: '%s'") % tmp)

        #print "DEBUG: m.groupdict(): %s" % m.groupdict()

        mg = m.groupdict()
        if 'TOURNO'    in mg: self.tourNo = mg['TOURNO']
        if 'LIMIT'     in mg: self.gametype['limitType'] = self.limits[mg['LIMIT']]
        if 'GAME'      in mg: self.gametype['category']  = self.games[mg['GAME']][1]
        if mg['BUYIN'] != None:
            self.buyin = int(100*Decimal(mg['BUYIN']))
        if mg['FEE'] != None:
            self.fee   = int(100*Decimal(mg['FEE']))
        if 'PRIZEPOOL' in mg: self.prizepool             = mg['PRIZEPOOL']
        if 'ENTRIES'   in mg: self.entries               = mg['ENTRIES']

        datetimestr = "%s/%s/%s %s:%s:%s" % (mg['Y'], mg['M'], mg['D'], mg['H'], mg['MIN'], mg['S'])
        self.startTime = datetime.datetime.strptime(datetimestr, "%Y/%m/%d %H:%M:%S")

        if 'TZ' in mg:
            self.startTime = HandHistoryConverter.changeTimezone(self.startTime, mg['TZ'], "UTC")


        m = self.re_Currency.search(self.summaryText)
        if m == None:
            log.error(_("parseSummaryFile: Unable to locate currency"))
            log.error(_("parseSummaryFile: Raising FpdbParseError"))
            raise FpdbParseError(_("Unable to locate currency"))
        #print "DEBUG: m.groupdict(): %s" % m.groupdict()

        mg = m.groupdict()
        if mg['CURRENCY'] == "$":     self.currency = "USD"
        elif mg['CURRENCY'] == u"€":  self.currency="EUR"
        elif mg['CURRENCY'] == "FPP": self.currency="PSFP"

        m = self.re_Player.finditer(self.summaryText)
        for a in m:
            mg = a.groupdict()
            #print "DEBUG: a.groupdict(): %s" % mg
            name = mg['NAME']
            rank = mg['RANK']
            winnings = 0

            if 'WINNINGS' in mg and mg['WINNINGS'] != None:
                winnings = int(100*Decimal(mg['WINNINGS']))

            if 'STILLPLAYING' in mg and mg['STILLPLAYING'] != None:
                #print "stillplaying"
                rank=None
                winnings=None

            if 'TICKET' and mg['TICKET'] != None:
                print "DEBUG: TODO! fix Step ticket values"
                print "\tWinning = Level %s" % mg['LEVEL']

            #TODO: currency, ko/addon/rebuy count -> need examples!
            #print "DEBUG: addPlayer(%s, %s, %s, %s, None, None, None)" %(rank, name, winnings, self.currency)
            #print "DEBUG: self.buyin: %s self.fee %s" %(self.buyin, self.fee)
            self.addPlayer(rank, name, winnings, self.currency, None, None, None)

        #print self

#end class PokerStarsSummary
