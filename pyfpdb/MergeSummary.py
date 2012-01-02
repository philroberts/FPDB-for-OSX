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
import MergeToFpdb
from TourneySummary import *


class MergeSummary(TourneySummary):
    limits = { 'No Limit':'nl', 'No Limit ':'nl', 'Limit':'fl', 'Pot Limit':'pl', 'Pot Limit ':'pl', 'Half Pot Limit':'hp'}
    games = {              # base, category
                    'Holdem' : ('hold','holdem'),
         'Holdem Tournament' : ('hold','holdem'),
                    'Omaha'  : ('hold','omahahi'),
         'Omaha Tournament'  : ('hold','omahahi'),
               'Omaha H/L8'  : ('hold','omahahilo'),
              '2-7 Lowball'  : ('draw','27_3draw'),
              'A-5 Lowball'  : ('draw','a5_3draw'),
                   'Badugi'  : ('draw','badugi'),
           '5-Draw w/Joker'  : ('draw','fivedraw'),
                   '5-Draw'  : ('draw','fivedraw'),
                   '7-Stud'  : ('stud','studhi'),
              '7-Stud H/L8'  : ('stud','studhilo'),
                   '5-Stud'  : ('stud','5studhi'),
                     'Razz'  : ('stud','razz'),
            }
    games_html = {
                    'Texas Holdem' : ('hold','holdem'),
                }


    substitutions = {
                     'LEGAL_ISO' : "USD|EUR|GBP|CAD|FPP",     # legal ISO currency codes
                            'LS' : u"\$|\xe2\x82\xac|\u20ac|" # legal currency symbols
                    }
    re_GameTypeHH = re.compile(r'<description type="(?P<GAME>Holdem|Holdem\sTournament|Omaha|Omaha\sTournament|Omaha\sH/L8|2\-7\sLowball|A\-5\sLowball|Badugi|5\-Draw\sw/Joker|5\-Draw|7\-Stud|7\-Stud\sH/L8|5\-Stud|Razz|HORSE)" stakes="(?P<LIMIT>[a-zA-Z ]+)(\s\(?\$?(?P<SB>[.0-9]+)?/?\$?(?P<BB>[.0-9]+)?(?P<blah>.*)\)?)?"/>', re.MULTILINE)
    re_HandInfoHH = re.compile(r'<game id="(?P<HID1>[0-9]+)-(?P<HID2>[0-9]+)" starttime="(?P<DATETIME>[0-9]+)" numholecards="[0-9]+" gametype="[0-9]+" (multigametype="(?P<MULTIGAMETYPE>\d+)" )?(seats="(?P<SEATS>[0-9]+)" )?realmoney="(?P<REALMONEY>(true|false))" data="[0-9]+\|(?P<TABLENAME>[^|]+)\|(?P<TDATA>[^|]+)\|?.*>', re.MULTILINE)

    re_HTMLGameType = re.compile("""Game Type</th><td>(?P<LIMIT>No Limit|Pot Limit) (?P<GAME>Texas Holdem)</td><h1>""")
    re_HTMLTourNo = re.compile("Game ID</th><td>(?P<TOURNO>[0-9]+)-1</td>")
    re_HTMLPlayer = re.compile(u"""<tr><td align="center">(?P<RANK>\d+)</td><td>(?P<PNAME>.+?)</td><td>(?P<WINNINGS>.+?)</td></tr>""")
    re_HTMLDetails = re.compile(u"""<p class="text">(?P<LABEL>.+?) : (?P<VALUE>.+?)</p>""")
    re_HTMLPrizepool = re.compile(u"""Total Prizepool</th><td>(?P<PRIZEPOOL>[0-9,.]+)</td>""")
    re_HTMLDateTime = re.compile("Start Time</th><td>Sun 1st January 2012, 20:00:00</td>\[(?P<Y>[0-9]{4})\/(?P<M>[0-9]{2})\/(?P<D>[0-9]{2})[\- ]+(?P<H>[0-9]+):(?P<MIN>[0-9]+):(?P<S>[0-9]+)")
    re_Ticket = re.compile(u""" / Ticket (?P<VALUE>[0-9.]+)&euro;""")

    codepage = ["utf-8"]

    @staticmethod
    def getSplitRe(self, head):
        re_SplitTourneys = re.compile("PokerStars Tournament ")
        return re_SplitTourneys

    def parseSummary(self):
        # id type of file and call correct function
        m = self.re_GameTypeHH.search(self.summaryText)
        if m and 'Tournament' in m.group('GAME'):
            self.parseSummaryFromHH(m)
        else:
            self.parseSummaryFile()

    def parseSummaryFromHH(self, gt):
        obj = getattr(MergeToFpdb, "Merge", None)
        hhc = obj(self.config, in_path = None, sitename = None, autostart = False)

        m = self.re_HandInfoHH.search(self.summaryText)
        if m:
            if m.group('TABLENAME') in hhc.SnG_Structures:
                print "DEBUG: SnG: ", hhc.SnG_Structures[m.group('TABLENAME')]
        if hand.gametype['type'] == 'tour':
            tid, table = re.split('-', m.group('TDATA'))
            logging.info("HID %s-%s, Tourney %s Table %s" % (m.group('HID1'), m.group('HID2'), tid, table))
            self.info['tablename'] = m.group('TABLENAME')
            hand.tourNo = tid
            hand.tablename = table


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


    def parseSummaryFile(self):
        self.currency = "USD"
        soup = BeautifulSoup(self.summaryText)
        tl = soup.findAll('table')

        ps = soup.findAll('tr')
        # FIXME: Searching every line for all regexes is pretty horrible
        for p in ps:
            m = self.re_HTMLGameType.search(str(p))
            if m:
                print "DEBUG: re_HTMLGameType: '%s' '%s'" %(m.group('LIMIT'), m.group('GAME'))
                self.gametype['limitType'] = self.limits[m.group('LIMIT')]
                self.gametype['category']  = self.games_html[m.group('GAME')][1]
            m = self.re_HTMLTourNo.search(str(p))
            if m:
                print "DEBUG: re_HTMLTourNo: '%s'" % m.group('TOURNO')
                self.tourNo = m.group('TOURNO')
            m = self.re_HTMLPrizepool.search(str(p))
            if m:
                print "DEBUG: re_HTMLPrizepool: '%s'" % m.group('PRIZEPOOL')
                self.prizepool = int(100*convert_to_decimal(m.group('PRIZEPOOL')))
            #re_HTMLDateTime = re.compile("\[(?P<Y>[0-9]{4})\/(?P<M>[0-9]{2})\/(?P<D>[0-9]{2})[\- ]+(?P<H>[0-9]+):(?P<MIN>[0-9]+):(?P<S>[0-9]+)")
            #self.startTime = datetime.datetime.strptime(datetimestr, "%Y/%m/%d %H:%M:%S")
            m = self.re_HTMLPlayer.search(str(p))
            if m:
                print "DEBUG: rank: %s pname: %s won: %s" %(m.group('RANK'), m.group('PNAME'), m.group('WINNINGS'))
                rank = m.group('RANK')
                name = m.group('PNAME')
                winnings = int(100*convert_to_decimal(m.group('WINNINGS')))
                self.addPlayer(rank, name, winnings, self.currency, None, None, None)

        self.buyin = 0
        self.fee   = 0
        self.entries   = 0
        #print self

def convert_to_decimal(string):
    dec = string.strip(u'€&euro;\u20ac$')
    dec = dec.replace(u',','.')
    dec = dec.replace(u' ','')
    dec = Decimal(dec)
    return dec

