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

"""A site template for tourney summary parsing"""

import L10n
_ = L10n.get_translation()

from decimal_wrapper import Decimal
import datetime

from Exceptions import FpdbParseError
from HandHistoryConverter import *
import PokerStarsToFpdb
from TourneySummary import *

class Sitename(TourneySummary):
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
                            'LS' : u"\$|\xe2\x82\xac|\u20AC|" # legal currency symbols
                    }

    re_SplitTourneys = re.compile("PokerStars Tournament ")
    
    re_TourNo = re.compile("\#(?P<TOURNO>[0-9]+),")

    re_TourneyInfo = re.compile(u"""
                        \#(?P<TOURNO>[0-9]+),\s
                        (?P<LIMIT>No\sLimit|Limit|LIMIT|Pot\sLimit)\s
                        (?P<GAME>Hold\'em|Razz|RAZZ|7\sCard\sStud|7\sCard\sStud\sHi/Lo|Omaha|Omaha\sHi/Lo|Badugi|Triple\sDraw\s2\-7\sLowball|5\sCard\sDraw)\s+
                        (?P<DESC>[ a-zA-Z]+\s+)?
                        (Buy-In:\s[%(LS)s](?P<BUYIN>[.0-9]+)(\/[%(LS)s](?P<FEE>[.0-9]+))?(?P<CUR>\s(%(LEGAL_ISO)s))?\s+)?
                        (?P<ENTRIES>[0-9]+)\splayers\s+
                        ([%(LS)s]?(?P<ADDED>[.\d]+)\sadded\sto\sthe\sprize\spool\sby\sPokerStars\.com\s+)?
                        (Total\sPrize\sPool:\s[%(LS)s]?(?P<PRIZEPOOL>[.0-9]+)(\s(%(LEGAL_ISO)s))?\s+)?
                        (Target\sTournament\s.*)?
                        Tournament\sstarted\s+(-\s)?
                        (?P<Y>[0-9]{4})\/(?P<M>[0-9]{2})\/(?P<D>[0-9]{2})[\-\s]+(?P<H>[0-9]+):(?P<MIN>[0-9]+):(?P<S>[0-9]+)\s?\(?(?P<TZ>[A-Z]+)\)?\s
                               """ % substitutions ,re.VERBOSE|re.MULTILINE|re.DOTALL)

    re_Currency = re.compile(u"""(?P<CURRENCY>[%(LS)s]|FPP)""" % substitutions)

    re_Player = re.compile(u"""(?P<RANK>[0-9]+):\s(?P<NAME>.*)\s\(.*\),(\s)?(\$(?P<WINNINGS>[0-9]+\.[0-9]+))?(?P<STILLPLAYING>still\splaying)?((?P<TICKET>Tournament\sTicket)\s\(WSOP\sStep\s(?P<LEVEL>\d)\))?(\s+)?""")

    re_DateTime = re.compile("\[(?P<Y>[0-9]{4})\/(?P<M>[0-9]{2})\/(?P<D>[0-9]{2})[\- ]+(?P<H>[0-9]+):(?P<MIN>[0-9]+):(?P<S>[0-9]+)")

    codepage = ["utf-8"]

    def getSplitRe(self, head):
        return re_SplitTourneys

    def parseSummary(self):
        m = self.re_TourneyInfo.search(self.summaryText)
        if m == None:
            tmp = self.summaryText[0:200]
            log.error("parseSummary: " + _("Unable to recognise Tourney Info: '%s'") % tmp)
            log.error("parseSummary: " + _("Raising FpdbParseError"))
            raise FpdbParseError(_("Unable to recognise Tourney Info: '%s'") % tmp)

        print "DEBUG: m.groupdict(): %s" % m.groupdict()

        mg = m.groupdict()
        self.tourNo = ''
        self.gametype['limitType'] = ''
        self.gametype['category']  = ''
        self.buyin = 0
        self.fee   = 0
        self.prizepool = 0
        self.entries   = 0
        #self.startTime = datetime.datetime.strptime(datetimestr, "%Y/%m/%d %H:%M:%S")

        self.currency = "USD"

        #self.addPlayer(rank, name, winnings, self.currency, None, None, None)

