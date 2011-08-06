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
from TourneySummary import *

class FullTiltPokerSummary(TourneySummary):
    limits = { 'No Limit':'nl', 'Pot Limit':'pl', 'Limit':'fl', 'LIMIT':'fl' }
    games = {                          # base, category
                              "Hold'em" : ('hold','holdem'), 
                                'Omaha' : ('hold','omahahi'),
                            'Omahai Hi' : ('hold','omahahi'),
                          'Omaha Hi/Lo' : ('hold','omahahilo'),
                            'Omaha H/L' : ('hold','omahahilo'),
                                 'Razz' : ('stud','razz'), 
                                 'RAZZ' : ('stud','razz'),
                          '7 Card Stud' : ('stud','studhi'),
                    '7 Card Stud Hi/Lo' : ('stud','studhilo'),
                             'Stud H/L' : ('stud','studhilo'),
                               'Badugi' : ('draw','badugi'),
              'Triple Draw 2-7 Lowball' : ('draw','27_3draw'),
                          '5 Card Draw' : ('draw','fivedraw'),
                         '7-Game Mixed' : ('mixed','mix_7game'),
               }

    substitutions = {
                     'LEGAL_ISO' : "USD|EUR|GBP|CAD|FPP",      # legal ISO currency codes
                            'LS' : u"\$|\xe2\x82\xac|\u20ac|", # legal currency symbols - Euro(cp1252, utf-8)
                           'TAB' : u"-\u2013'\s\da-zA-Z",      # legal characters for tablename
                           'NUM' : u".,\d",                    # legal characters in number format
                    }

    re_SplitTourneys = re.compile("^Full Tilt Poker Tournament Summary")
    
    re_TourNo = re.compile("\#(?P<TOURNO>[0-9]+),")

    re_TourneyInfo = re.compile(u"""
                        (\s*.*(?P<TYPE>Tournament|Sit\s\&\sGo|Sit\&Go|\(Rebuy\)|Matrix|Knockout|KO|Rush|Satellite|FTOPS|MiniFTOPS|Step\s\d|Daily\sDollar|Madness|Freeroll|Heads-Up|Challenge|Super\sTurbo|The\sKitchen\sSink|Tier\sOne).*\s)
                        \((?P<TOURNO>[0-9]+)\)
                        (\s+)?(\sMatch\s\d\s)?
                        (?P<GAME>Hold\'em|Razz|RAZZ|7\sCard\sStud|7\sCard\sStud\sHi/Lo|Stud\sH/L|Omaha|Omaha\sHi|Omaha\sHi/Lo|Omaha\sH/L|Badugi|Triple\sDraw\s2\-7\sLowball|5\sCard\sDraw|7-Game\sMixed)\s+
                        ((?P<LIMIT>No\sLimit|Limit|LIMIT|Pot\sLimit)\s+)?
                        (Buy-In:\s[%(LS)s](?P<BUYIN>[%(NUM)s]+)(\s\+\s[%(LS)s](?P<FEE>[%(NUM)s]+))?\s+)?
                        (Knockout\sBounty:\s[%(LS)s](?P<KOBOUNTY>[%(NUM)s]+)\s+)?
                        ((?P<PNAMEBOUNTIES>.{2,15})\sreceived\s\d+\sKnockout\sBounty\sAwards?\s+)?
                        (Add-On:\s[%(LS)s](?P<ADDON>[%(NUM)s]+)\s+)?
                        (Rebuy:\s[%(LS)s](?P<REBUYAMT>[%(NUM)s]+)\s+)?
                        ((?P<P1NAME>.{2,15})\sperformed\s(?P<PADDONS>\d+)\sAdd-Ons?\s+)?
                        ((?P<P2NAME>.{2,15})\sperformed\s(?P<PREBUYS>\d+)\sRebuys?\s+)?
                        (Buy-In\sChips:\s(?P<CHIPS>\d+)\s+)?
                        (Add-On\sChips:\s(?P<ADDONCHIPS>\d+)\s+)?
                        (Rebuy\sChips:\s(?P<REBUYCHIPS>\d+)\s+)?
                        (?P<ENTRIES>[0-9]+)\sEntries\s+
                        (Total\sAdd-Ons:\s(?P<ADDONS>\d+)\s+)?
                        (Total\sRebuys:\s(?P<REBUYS>\d+)\s+)?
                        ([%(LS)s]?(?P<ADDED>[.\d]+)\sadded\sto\sthe\sprize\spool\sby\sPokerStars\.com\s+)?
                        (Total\sPrize\sPool:\s[%(LS)s]?(?P<PRIZEPOOL>[%(NUM)s]+)\s+)?
                        (Top\s(\d+\s)?finishers?\sreceives?\s(entry\sto\s[Tt]ournament\s\d+|Step\s\d\sTicket|FTPA\sChallenge\sFinals\sTicket|[%(LS)s]\d+\sSatellite\sToken)\s+)?
                        (Target\sTournament\s.*)?
                        Tournament\sstarted:\s
                        (?P<DATETIME>((?P<Y>[\d]{4})\/(?P<M>[\d]{2})\/(?P<D>[\d]+)\s+(?P<H>[\d]+):(?P<MIN>[\d]+):(?P<S>[\d]+)\s??(?P<TZ>[A-Z]+)\s|\w+,\s(?P<MONTH>\w+)\s(?P<DAY>\d+),\s(?P<YEAR>[\d]{4})\s(?P<HOUR>\d+):(?P<MIN2>\d+)))
                               """ % substitutions ,re.VERBOSE|re.MULTILINE|re.DOTALL)

    re_Currency = re.compile(u"""(?P<CURRENCY>[%(LS)s]|FPP)""" % substitutions)

    re_Player = re.compile(u"""(?P<RANK>[\d]+):\s(?P<NAME>[^,\r\n]{2,15})(,\s[%(LS)s](?P<WINNINGS>[.\d]+))?(,\s(?P<TICKET>Step\s(?P<LEVEL>\d)\sTicket))?""" % substitutions)
    re_Finished = re.compile(u"""(?P<NAME>[^,\r\n]{2,15}) finished in (?P<RANK>[\d]+)\S\S place""")

    re_DateTime = re.compile("\[(?P<Y>[0-9]{4})\/(?P<M>[0-9]{2})\/(?P<D>[0-9]{2})[\- ]+(?P<H>[0-9]+):(?P<MIN>[0-9]+):(?P<S>[0-9]+)")

    codepage = ["utf-16", "cp1252", "utf-8"]

    def parseSummary(self):
        m = self.re_TourneyInfo.search(self.summaryText[:2000])
        if m == None:
            tmp = self.summaryText[0:200]
            log.error("parseSummary: " + _("Unable to recognise Tourney Info: '%s'") % tmp)
            log.error("parseSummary: " + _("Raising FpdbParseError"))
            raise FpdbParseError(_("Unable to recognise Tourney Info: '%s'") % tmp)

        #print "DEBUG: m.groupdict(): %s" % m.groupdict()

        mg = m.groupdict()
        if 'TOURNO'    in mg: self.tourNo = mg['TOURNO']
        if 'LIMIT'     in mg and mg['LIMIT'] != None:
            self.gametype['limitType'] = self.limits[mg['LIMIT']]
        else:
            self.gametype['limitType'] = 'mx'
        if 'GAME'      in mg: self.gametype['category']  = self.games[mg['GAME']][1]
        if mg['BUYIN'] != None:
            self.buyin = int(100*Decimal(mg['BUYIN']))
        if mg['FEE'] != None:
            self.fee   = int(100*Decimal(mg['FEE']))
        if 'PRIZEPOOL' in mg: self.prizepool             = mg['PRIZEPOOL']
        if 'ENTRIES'   in mg: self.entries               = mg['ENTRIES']

        datetimestr = ""
        if mg['YEAR'] == None:
            datetimestr = "%s/%s/%s %s:%s:%s" % (mg['Y'], mg['M'], mg['D'], mg['H'], mg['MIN'], mg['S'])
            self.startTime = datetime.datetime.strptime(datetimestr, "%Y/%m/%d %H:%M:%S")
        else:
            datetimestr = "%s/%s/%s %s:%s" % (mg['YEAR'], mg['MONTH'], mg['DAY'], mg['HOUR'], mg['MIN2'])
            self.startTime = datetime.datetime.strptime(datetimestr, "%Y/%B/%d %H:%M")

        if 'TZ' in mg and mg['TZ'] is not None:
            self.startTime = HandHistoryConverter.changeTimezone(self.startTime, mg['TZ'], "UTC")


        m = self.re_Currency.search(self.summaryText)
        if m == None:
            log.error("parseSummary: " + _("Unable to locate currency"))
            log.error("parseSummary: " + _("Raising FpdbParseError"))
            raise FpdbParseError(_("Unable to locate currency"))
        #print "DEBUG: m.groupdict(): %s" % m.groupdict()

        mg = m.groupdict()
        if mg['CURRENCY'] == "$":     self.currency = "USD"
        elif mg['CURRENCY'] == u"€":  self.currency="EUR"
        elif mg['CURRENCY'] == "FPP": self.currency="FTFP"

        m = self.re_Player.finditer(self.summaryText)
        playercount = 0
        for a in m:
            mg = a.groupdict()
            #print "DEBUG: a.groupdict(): %s" % mg
            name = mg['NAME']
            rank = mg['RANK']
            winnings = 0

            if 'WINNINGS' in mg and mg['WINNINGS'] != None:
                winnings = int(100*Decimal(mg['WINNINGS']))

            if 'TICKET' and mg['TICKET'] != None:
                #print "Tournament Ticket Level %s" % mg['LEVEL']
                step_values = {
                                '1' :    '330', # Step 1 -    $3.30 USD
                                '2' :    '870', # Step 2 -    $8.70 USD
                                '3' :   '2600', # Step 3 -   $26.00 USD
                                '4' :   '7500', # Step 4 -   $75.00 USD
                                '5' :  '21600', # Step 5 -  $216.00 USD
                                '6' :  '64000', # Step 6 -  $640.00 USD
                                '7' : '210000', # Step 7 - $2100.00 USD
                              }
                winnings = step_values[mg['LEVEL']]
            self.addPlayer(rank, name, winnings, self.currency, None, None, None)

            playercount += 1


        # Some files dont contain the normals lines, and only contain the line
        # <PLAYER> finished in XXXXrd place
        if playercount == 0:
            m = self.re_Finished.finditer(self.summaryText)
            for a in m:
                winnings = 0
                name = a.group('NAME')
                rank = a.group('RANK')
                self.addPlayer(rank, name, winnings, self.currency, None, None, None)
