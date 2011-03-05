#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Copyright 2008-2011 Carl Gherardi
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
from BeautifulSoup import BeautifulSoup

from Exceptions import FpdbParseError
from HandHistoryConverter import *
import PokerStarsToFpdb
from TourneySummary import *


class WinamaxSummary(TourneySummary):
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

    re_GameType = re.compile("""<h1>((?P<LIMIT>No Limit|Pot Limit) (?P<GAME>Hold\'em))</h1>""")

    re_SplitTourneys = re.compile("PokerStars Tournament ")
    
    re_TourNo = re.compile("ID\=(?P<TOURNO>[0-9]+)")

    re_Player = re.compile(u"""(?P<RANK>\d+)<\/td><td width="30%">(?P<PNAME>.+?)<\/td><td width="60%">(?P<WINNINGS>.+?)</td>""")

    re_Details = re.compile(u"""<p class="text">(?P<LABEL>.+?) : (?P<VALUE>.+?)</p>""")
    re_Prizepool = re.compile(u"""<div class="title2">.+: (?P<PRIZEPOOL>[0-9,]+)""")

    re_DateTime = re.compile("\[(?P<Y>[0-9]{4})\/(?P<M>[0-9]{2})\/(?P<D>[0-9]{2})[\- ]+(?P<H>[0-9]+):(?P<MIN>[0-9]+):(?P<S>[0-9]+)")

    codepage = ["utf-8"]

    def parseSummary(self):
        self.currency = "EUR"
        soup = BeautifulSoup(self.summaryText)
        tl = soup.findAll('div', {"class":"left_content"})

        ps = soup.findAll('p', {"class": "text"})
        for p in ps:
            for m in self.re_Details.finditer(str(p)):
                mg = m.groupdict()
                #print mg
                if mg['LABEL'] == 'Buy-in':
                    mg['VALUE'] = mg['VALUE'].replace(u"&euro;", "")
                    mg['VALUE'] = mg['VALUE'].replace(u"+", "")
                    mg['VALUE'] = mg['VALUE'].strip(" $")
                    bi, fee = mg['VALUE'].split(" ")
                    self.buyin = int(100*Decimal(bi))
                    self.fee   = int(100*Decimal(fee))
                    #print "DEBUG: bi: '%s' fee: '%s" % (self.buyin, self.fee)
                if mg['LABEL'] == 'Nombre de joueurs inscrits':
                    self.entries   = mg['VALUE']
                if mg['LABEL'] == 'D\xc3\xa9but du tournoi':
                    self.startTime = datetime.datetime.strptime(mg['VALUE'], "%d-%m-%Y %H:%M")
                if mg['LABEL'] == 'Nombre de joueurs max':
                    # Max seats i think
                    pass

        div = soup.findAll('div', {"class": "title2"})
        for m in self.re_Prizepool.finditer(str(div)):
            mg = m.groupdict()
            #print mg
            self.prizepool = mg['PRIZEPOOL'].replace(u',','.')
            

        for m in self.re_GameType.finditer(str(tl[0])):
            mg = m.groupdict()
            #print mg
            self.gametype['limitType'] = self.limits[mg['LIMIT']]
            self.gametype['category'] = self.games[mg['GAME']][1]

        for m in self.re_Player.finditer(str(tl[0])):
            mg = m.groupdict()
            #print mg
            winnings = mg['WINNINGS'].strip(u'€').replace(u',','.')
            winnings = int(100*Decimal(winnings))
            rank     = mg['RANK']
            name     = mg['PNAME']
            #print "DEBUG: %s: %s" %(name, winnings)
            self.addPlayer(rank, name, winnings, self.currency, None, None, None)


        for m in self.re_TourNo.finditer(self.summaryText):
            mg = m.groupdict()
            #print mg
            self.tourNo = mg['TOURNO']
