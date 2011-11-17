#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Copyright 2008-2011 Steffen Schaumburg
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
                          '5 Card Draw' : ('draw','fivedraw'),
                                'HORSE' : ('mixed','mix_horse'),
                               '8-Game' : ('mixed','mix_8game'),
               }

    substitutions = {
                     'LEGAL_ISO' : "USD|EUR|GBP|CAD|FPP",    # legal ISO currency codes
                            'LS' : u"\$|\xe2\x82\xac|\u20AC|" # legal currency symbols - Euro(cp1252, utf-8)
                    }

    re_SplitTourneys = re.compile("PokerStars Tournament ")
    
    re_TourNo = re.compile("\#(?P<TOURNO>[0-9]+),")

    re_TourneyInfo = re.compile(u"""
                        \#(?P<TOURNO>[0-9]+),\s
                        ((?P<LIMIT>No\sLimit|Limit|LIMIT|Pot\sLimit)\s)?
                        (?P<GAME>Hold\'em|Razz|RAZZ|7\sCard\sStud|7\sCard\sStud\sHi/Lo|Omaha|Omaha\sHi/Lo|Badugi|Triple\sDraw\s2\-7\sLowball|5\sCard\sDraw|HORSE|8-Game)\s+
                        (?P<DESC>[ a-zA-Z]+\s+)?
                        (Buy-In:\s[%(LS)s](?P<BUYIN>[.0-9]+)(\/[%(LS)s](?P<FEE>[.0-9]+))?(?P<CUR>\s(%(LEGAL_ISO)s))?\s+)?
                        (?P<ENTRIES>[0-9]+)\splayers\s+
                        ([%(LS)s]?(?P<ADDED>[.\d]+)(\s(%(LEGAL_ISO)s))?\sadded\sto\sthe\sprize\spool\sby\sPokerStars(\.com)?\s+)?
                        (Total\sPrize\sPool:\s[%(LS)s]?(?P<PRIZEPOOL>[.0-9]+)(\s(%(LEGAL_ISO)s))?\s+)?
                        (Target\sTournament\s.*)?
                        Tournament\sstarted\s+(-\s)?
                        (?P<DATETIME>.*$)
                        """ % substitutions ,re.VERBOSE|re.MULTILINE)

    re_Currency = re.compile(u"""(?P<CURRENCY>[%(LS)s]|FPP)""" % substitutions)

    re_Player = re.compile(u"""(?P<RANK>[0-9]+):\s(?P<NAME>.*)\s\(.*\),(\s)?([%(LS)s](?P<WINNINGS>[0-9]+\.[0-9]+))?(?P<STILLPLAYING>still\splaying)?((?P<TICKET>Tournament\sTicket)\s\(WSOP\sStep\s(?P<LEVEL>\d)\))?(\s+)?""" % substitutions)

    re_DateTime = re.compile("""(?P<Y>[0-9]{4})\/(?P<M>[0-9]{2})\/(?P<D>[0-9]{2})[\- ]+(?P<H>[0-9]+):(?P<MIN>[0-9]+):(?P<S>[0-9]+)""", re.MULTILINE)

    codepage = ["utf-8"]

    def parseSummary(self):
        m = self.re_TourneyInfo.search(self.summaryText)
        if m == None:
            tmp = self.summaryText[0:200]
            log.error("parseSummary: " + _("Unable to recognise Tourney Info: '%s'") % tmp)
            log.error("parseSummary: " + _("Raising FpdbParseError"))
            raise FpdbParseError(_("Unable to recognise Tourney Info: '%s'") % tmp)

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
            self.prizepool = int(self.clearMoneyString(mg['PRIZEPOOL']))
        if 'ENTRIES'   in mg: self.entries               = mg['ENTRIES']
        if 'DATETIME'  in mg: m1 = self.re_DateTime.finditer(mg['DATETIME'])
        datetimestr = "2000/01/01 00:00:00"  # default used if time not found
        for a in m1:
            datetimestr = "%s/%s/%s %s:%s:%s" % (a.group('Y'), a.group('M'),a.group('D'),a.group('H'),a.group('MIN'),a.group('S'))
            
        self.startTime = datetime.datetime.strptime(datetimestr, "%Y/%m/%d %H:%M:%S") # also timezone at end, e.g. " ET"
        self.startTime = HandHistoryConverter.changeTimezone(self.startTime, "ET", "UTC")

        m = self.re_Currency.search(self.summaryText)
        if m == None:
            log.error("parseSummary: " + _("Unable to locate currency"))
            log.error("parseSummary: " + _("Raising FpdbParseError"))
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
            self.addPlayer(rank, name, winnings, self.currency, None, None, None)

        #print self

#end class PokerStarsSummary
