#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Copyright 2008-2012 Steffen Schaumburg, Carl Gherardi
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

import L10n
_ = L10n.get_translation()

from decimal_wrapper import Decimal
import datetime

from Exceptions import FpdbParseError
from HandHistoryConverter import *
import PokerStarsToFpdb
from TourneySummary import *

class PokerStarsSummary(TourneySummary):
    hhtype = "summary"
    limits = { 'No Limit':'nl', 'NO LIMIT':'nl', 'Pot Limit':'pl', 'POT LIMIT':'pl', 'Limit':'fl', 'LIMIT':'fl' , 'Pot Limit Pre-Flop, No Limit Post-Flop': 'pn'}
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
              'Single Draw 2-7 Lowball' : ('draw','27_1draw'),
                          '5 Card Draw' : ('draw','fivedraw'),
                                'HORSE' : ('mixed','horse'),
                                 'HOSE' : ('mixed','hose'),
                          'Triple Stud' : ('mixed','3stud'),
                               '8-Game' : ('mixed','8game'),
                        'Mixed PLH/PLO' : ('mixed','plh_plo'),
                        'Mixed NLH/PLO' : ('mixed','nlh_plo'),
                      'Mixed Omaha H/L' : ('mixed','plo_lo'),
                       'Mixed Hold\'em' : ('mixed','mholdem'),
                          'Triple Stud' : ('mixed','3stud'),
               }

    substitutions = {
                     'LEGAL_ISO' : "USD|EUR|GBP|CAD|FPP",    # legal ISO currency codes
                            'LS' : u"\$|\xe2\x82\xac|\u20AC|" # legal currency symbols - Euro(cp1252, utf-8)
                    }

    
    re_TourNo = re.compile("\#(?P<TOURNO>[0-9]+),")

    re_TourneyInfo = re.compile(u"""
                        \#(?P<TOURNO>[0-9]+),\s
                        ((?P<LIMIT>No\sLimit|NO\sLIMIT|Limit|LIMIT|Pot\sLimit|POT\sLIMIT|Pot\sLimit\sPre\-Flop,\sNo\sLimit\sPost\-Flop)\s)?
                        (?P<GAME>Hold\'em|Razz|RAZZ|7\sCard\sStud|7\sCard\sStud\sHi/Lo|Omaha|Omaha\sHi/Lo|Badugi|Triple\sDraw\s2\-7\sLowball|Single\sDraw\s2\-7\sLowball|5\sCard\sDraw|HORSE|8\-Game|HOSE|Mixed\sOmaha\sH/L|Mixed\sHold\'em|Mixed\sPLH/PLO|Mixed\sNLH/PLO|Triple\sStud)\s+
                        (?P<DESC>[ a-zA-Z]+\s+)?
                        (Buy-In:\s(?P<CURRENCY>[%(LS)s]?)(?P<BUYIN>[,.0-9]+)(\/[%(LS)s]?(?P<FEE>[,.0-9]+))?(?P<CUR>\s(%(LEGAL_ISO)s))?\s+)?
                        (?P<ENTRIES>[0-9]+)\splayers\s+
                        ([%(LS)s]?(?P<ADDED>[,.\d]+)(\s(%(LEGAL_ISO)s))?\sadded\sto\sthe\sprize\spool\sby\sPokerStars(\.com)?\s+)?
                        (Total\sPrize\sPool:\s[%(LS)s]?(?P<PRIZEPOOL>[,.0-9]+)(\s(%(LEGAL_ISO)s))?\s+)?
                        (Target\sTournament\s.+?\s)?
                        Tournament\sstarted\s+(-\s)?
                        (?P<DATETIME>.*$)
                        """ % substitutions ,re.VERBOSE|re.MULTILINE)

    re_Player = re.compile(u"""(?P<RANK>[0-9]+):\s(?P<NAME>.*)\s\(.*\),(\s)?((?P<CUR>[%(LS)s]?)(?P<WINNINGS>[,.0-9]+))?(?P<STILLPLAYING>still\splaying)?((?P<TICKET>Tournament\sTicket)\s\(WSOP\sStep\s(?P<LEVEL>\d)\))?(\s+)?""" % substitutions)

    re_DateTime = re.compile("""(?P<Y>[0-9]{4})\/(?P<M>[0-9]{2})\/(?P<D>[0-9]{2})[\- ]+(?P<H>[0-9]+):(?P<MIN>[0-9]+):(?P<S>[0-9]+)""", re.MULTILINE)

    #re_WinningRankOne   = re.compile(u"^%(PLYR)s wins the tournament and receives %(CUR)s(?P<AMT>[\.0-9]+) - congratulations!$" %  substitutions, re.MULTILINE)
    #re_WinningRankOther = re.compile(u"^%(PLYR)s finished the tournament in (?P<RANK>[0-9]+)(st|nd|rd|th) place and received %(CUR)s(?P<AMT>[.0-9]+)\.$" %  substitutions, re.MULTILINE)
    #re_RankOther        = re.compile(u"^%(PLYR)s finished the tournament in (?P<RANK>[0-9]+)(st|nd|rd|th) place$" %  substitutions, re.MULTILINE)

    codepage = ("utf8", "cp1252")

    @staticmethod
    def getSplitRe(self, head):
        re_SplitTourneys = re.compile("PokerStars Tournament ")
        re_HTMLSplitTourneys = re.compile("TR id=row_\d+")
        m = re.search("DOCTYPE HTML PUBLIC", head)
        if m != None:
            self.hhtype = "html"
            return re_HTMLSplitTourneys
        self.hhtype = "summary"
        return re_SplitTourneys

    def parseSummary(self):
        if self.hhtype == "summary":
            self.parseSummaryFile()
        elif self.hhtype == "html":
            self.parseSummaryHtml()
        elif self.hhtype == "hh":
            self.parseSummaryFromHH()
        else:
            raise FpdbParseError(_("parseSummary FAIL"))

    def parseSummaryFromHH(self):
        raise FpdbParseError(_("PokerStarsSummary.parseSummaryHtml: This file format is not yet supported"))
        # self.entries   = Unavailable from HH
        # self.prizepool = Unavailable from HH
        # self.startTime = Unreliable from HH (late reg)
        #obj = getattr(PokerStarsToFpdb, "PokerStars", None)
        #hhc = obj(self.config, in_path = self.in_path, sitename = None, autostart = False)

        #self.buyin     = int(100*hhc.SnG_Structures[tourneyNameFull]['buyIn'])
        #self.fee       = int(100*hhc.SnG_Structures[tourneyNameFull]['fee'])

        #self.tourNo = 
        #self.buyin     =
        #self.fee       =
        #self.buyinCurrency =
        #self.currency  =
        #self.maxseats  =
        #self.isSng     =
        #self.addPlayer(rank, name, winnings, self.currency, rebuyCount, addOnCount, koCount)

    def parseSummaryHtml(self):
        raise FpdbParseError(_("PokerStarsSummary.parseSummaryHtml: This file format is not yet supported"))
        #from BeautifulSoup import BeautifulSoup
        #soup = BeautifulSoup(self.summaryText)
        #h2 = soup.findAll('h2')
        #print h2
        ## Hero name
        #tbl = soup.findAll('tr')
        #print tbl

    def parseSummaryFile(self):
        m = self.re_TourneyInfo.search(self.summaryText)
        if m == None:
            tmp = self.summaryText[0:200]
            log.error(_("PokerStarsSummary.parseSummary: '%s'") % tmp)
            raise FpdbParseError

        #print "DEBUG: m.groupdict(): %s" % m.groupdict()

        mg = m.groupdict()
        if 'TOURNO'    in mg: self.tourNo = mg['TOURNO']
        if 'LIMIT'     in mg and mg['LIMIT'] is not None:
            self.gametype['limitType'] = self.limits[mg['LIMIT']]
        else:
            self.gametype['limitType'] = 'fl'
        if 'GAME'      in mg: self.gametype['category']  = self.games[mg['GAME']][1]
        if mg['BUYIN'] != None:
            self.buyin = int(100*Decimal(self.clearMoneyString(mg['BUYIN'])))
        if mg['FEE'] != None:
            self.fee   = int(100*Decimal(self.clearMoneyString(mg['FEE'])))
        if 'PRIZEPOOL' in mg:
            if mg['PRIZEPOOL'] != None: self.prizepool = int(Decimal(self.clearMoneyString(mg['PRIZEPOOL'])))
        if 'ENTRIES'   in mg: self.entries               = mg['ENTRIES']
        if 'DATETIME'  in mg: m1 = self.re_DateTime.finditer(mg['DATETIME'])
        datetimestr = "2000/01/01 00:00:00"  # default used if time not found
        for a in m1:
            datetimestr = "%s/%s/%s %s:%s:%s" % (a.group('Y'), a.group('M'),a.group('D'),a.group('H'),a.group('MIN'),a.group('S'))
            
        self.startTime = datetime.datetime.strptime(datetimestr, "%Y/%m/%d %H:%M:%S") # also timezone at end, e.g. " ET"
        self.startTime = HandHistoryConverter.changeTimezone(self.startTime, "ET", "UTC")

        if mg['CURRENCY'] == "$":     self.buyinCurrency="USD"
        elif mg['CURRENCY'] == u"€":  self.buyinCurrency="EUR"
        elif mg['CURRENCY'] == "FPP": self.buyinCurrency="PSFP"
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
                winnings = int(100*Decimal(mg['WINNINGS']))
                
            if 'CUR' in mg and mg['CUR'] != None:
                if mg['CUR'] == "$":     self.currency="USD"
                elif mg['CUR'] == u"€":  self.currency="EUR"
                elif mg['CUR'] == "FPP": self.currency="PSFP"

            if 'STILLPLAYING' in mg and mg['STILLPLAYING'] != None:
                #print "stillplaying"
                rank=None
                winnings=None

            if 'TICKET' and mg['TICKET'] != None:
                #print "Tournament Ticket Level %s" % mg['LEVEL']
                step_values = {
                                '1' :    '750', # Step 1 -    $7.50 USD
                                '2' :   '2750', # Step 2 -   $27.00 USD
                                '3' :   '8200', # Step 3 -   $82.00 USD
                                '4' :  '21500', # Step 4 -  $215.00 USD
                                '5' :  '70000', # Step 5 -  $700.00 USD
                                '6' : '210000', # Step 6 - $2100.00 USD
                              }
                winnings = step_values[mg['LEVEL']]

            #TODO: currency, ko/addon/rebuy count -> need examples!
            #print "DEBUG: addPlayer(%s, %s, %s, %s, None, None, None)" %(rank, name, winnings, self.currency)
            #print "DEBUG: self.buyin: %s self.fee %s" %(self.buyin, self.fee)
            self.addPlayer(rank, name, winnings, self.currency, rebuyCount, addOnCount, koCount)

        #print self

#end class PokerStarsSummary
