#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Copyright 2008-2012 Steffen Schaumburg
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
import PacificPokerToFpdb
from TourneySummary import *

class PacificPoker(TourneySummary):
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
    
    re_TourneyInfo = re.compile(u"""
                        Tournament\sID:\s(?P<TOURNO>[0-9]+)\s+
                        Buy-In:\s[%(LS)s](?P<BUYIN>[.0-9]+)\s\+\s\[%(LS)s](?P<FEE>[.0-9]+)\s+
                        (?P<NAME>.*)\sfinished\s(?P<RANK>[0-9]+)\/(?P<ENTRIES>[0-9]+)(\sand\swon\s[%(LS)s](?P<WINNINGS>[.0-9]+))?
                               """ % substitutions ,re.VERBOSE|re.MULTILINE|re.DOTALL)
                        #(?P<LIMIT>No\sLimit|Limit|LIMIT|Pot\sLimit)\s
                        #(?P<GAME>Hold\'em|Razz|RAZZ|7\sCard\sStud|7\sCard\sStud\sHi/Lo|Omaha|Omaha\sHi/Lo|Badugi|Triple\sDraw\s2\-7\sLowball|5\sCard\sDraw)\s+
                        #(?P<DESC>[ a-zA-Z]+\s+)?
                        #(?P<ENTRIES>[0-9]+)\splayers\s+
                        #([%(LS)s]?(?P<ADDED>[.\d]+)\sadded\sto\sthe\sprize\spool\sby\sPokerStars\.com\s+)?
                        #(Total\sPrize\sPool:\s[%(LS)s]?(?P<PRIZEPOOL>[.0-9]+)(\s(%(LEGAL_ISO)s))?\s+)?
                        #(Target\sTournament\s.*)?
                        #Tournament\sstarted\s+(-\s)?
                        #(?P<Y>[0-9]{4})\/(?P<M>[0-9]{2})\/(?P<D>[0-9]{2})[\-\s]+(?P<H>[0-9]+):(?P<MIN>[0-9]+):(?P<S>[0-9]+)\s?\(?(?P<TZ>[A-Z]+)\)?\s

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

        mg = m.groupdict()
        print "DEBUG: m.groupdict(): %s" % mg

        self.tourNo = mg['TOURNO']
        #FIXME: We need info from the filename... or to read the associated hh... both ugh
        #self.gametype['limitType'] = ''
        #self.gametype['category']  = ''
        self.buyin = int(100*convert_to_decimal(mg2['BUYIN']))
        self.fee   = int(100*convert_to_decimal(mg2['FEE']))
        self.prizepool = 0
        self.entries   = mg['ENTRIES']
        #self.startTime = datetime.datetime.strptime(datetimestr, "%Y/%m/%d %H:%M:%S")

        self.currency = "USD"
        player = mg['NAME']
        rank = mg['RANK']
        winnings = int(100*convert_to_decimal(mg['WINNINGS']))

        self.addPlayer(rank, player, winnings, self.currency, None, None, None)

def convert_to_decimal(string):
    dec = string.strip(u'€&euro;\u20ac$')
    dec = dec.replace(u',','.')
    dec = dec.replace(u' ','')
    dec = Decimal(dec)
    return dec

