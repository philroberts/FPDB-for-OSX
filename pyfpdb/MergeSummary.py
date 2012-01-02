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


    substitutions = {
                     'LEGAL_ISO' : "USD|EUR|GBP|CAD|FPP",     # legal ISO currency codes
                            'LS' : u"\$|\xe2\x82\xac|\u20ac|" # legal currency symbols
                    }
    re_GameTypeHH = re.compile(r'<description type="(?P<GAME>Holdem|Holdem\sTournament|Omaha|Omaha\sTournament|Omaha\sH/L8|2\-7\sLowball|A\-5\sLowball|Badugi|5\-Draw\sw/Joker|5\-Draw|7\-Stud|7\-Stud\sH/L8|5\-Stud|Razz|HORSE)" stakes="(?P<LIMIT>[a-zA-Z ]+)(\s\(?\$?(?P<SB>[.0-9]+)?/?\$?(?P<BB>[.0-9]+)?(?P<blah>.*)\)?)?"/>', re.MULTILINE)
    re_HandInfoHH = re.compile(r'<game id="(?P<HID1>[0-9]+)-(?P<HID2>[0-9]+)" starttime="(?P<DATETIME>[0-9]+)" numholecards="[0-9]+" gametype="[0-9]+" (multigametype="(?P<MULTIGAMETYPE>\d+)" )?(seats="(?P<SEATS>[0-9]+)" )?realmoney="(?P<REALMONEY>(true|false))" data="[0-9]+\|(?P<TABLENAME>[^|]+)\|(?P<TDATA>[^|]+)\|?.*>', re.MULTILINE)

    re_GameType = re.compile("""<h1>((?P<LIMIT>No Limit|Pot Limit) (?P<GAME>Hold\'em))</h1>""")

    re_TourNo = re.compile("ID\=(?P<TOURNO>[0-9]+)")

    re_Player = re.compile(u"""(?P<RANK>\d+)<\/td><td width="30%">(?P<PNAME>.+?)<\/td><td width="60%">(?P<WINNINGS>.+?)</td>""")

    re_Details = re.compile(u"""<p class="text">(?P<LABEL>.+?) : (?P<VALUE>.+?)</p>""")
    re_Prizepool = re.compile(u"""<div class="title2">.+: (?P<PRIZEPOOL>[0-9,]+)""")

    re_DateTime = re.compile("\[(?P<Y>[0-9]{4})\/(?P<M>[0-9]{2})\/(?P<D>[0-9]{2})[\- ]+(?P<H>[0-9]+):(?P<MIN>[0-9]+):(?P<S>[0-9]+)")
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
        self.currency = "EUR"
        soup = BeautifulSoup(self.summaryText)
        tl = soup.findAll('table')

        ps = soup.findAll('tr')
        for p in ps:
            print p
            #for m in self.re_Details.finditer(str(p)):
            #    mg = m.groupdict()
            #    #print mg
            #    if mg['LABEL'] == 'Buy-in':
            #        mg['VALUE'] = mg['VALUE'].replace(u"&euro;", "")
            #        mg['VALUE'] = mg['VALUE'].replace(u"+", "")
            #        mg['VALUE'] = mg['VALUE'].strip(" $")
            #        bi, fee = mg['VALUE'].split(" ")
            #        self.buyin = int(100*Decimal(bi))
            #        self.fee   = int(100*Decimal(fee))
            #        #print "DEBUG: bi: '%s' fee: '%s" % (self.buyin, self.fee)
            #    if mg['LABEL'] == 'Nombre de joueurs inscrits':
            #        self.entries   = mg['VALUE']
            #    if mg['LABEL'] == 'D\xc3\xa9but du tournoi':
            #        self.startTime = datetime.datetime.strptime(mg['VALUE'], "%d-%m-%Y %H:%M")
            #    if mg['LABEL'] == 'Nombre de joueurs max':
            #        # Max seats i think
            #        pass

#            for m in self.re_Prizepool.finditer(str(div)):
#                mg = m.groupdict()
#                #print mg
#                self.prizepool = mg['PRIZEPOOL'].replace(u',','.')
#                
#
#            for m in self.re_GameType.finditer(str(tl[0])):
#                mg = m.groupdict()
#                #print mg
#                self.gametype['limitType'] = self.limits[mg['LIMIT']]
#                self.gametype['category'] = self.games[mg['GAME']][1]
#
#            for m in self.re_Player.finditer(str(tl[0])):
#                winnings = 0
#                mg = m.groupdict()
#                rank     = mg['RANK']
#                name     = mg['PNAME']
#                #print "DEUBG: mg: '%s'" % mg
#                is_satellite = self.re_Ticket.search(mg['WINNINGS'])
#                if is_satellite:
#                    # Ticket
#                    winnings = convert_to_decimal(is_satellite.groupdict()['VALUE'])
#                    # For stallites, any ticket means 1st
#                    if winnings > 0:
#                        rank = 1
#                else:
#                    winnings = convert_to_decimal(mg['WINNINGS'])
#
#                winnings = int(100*Decimal(winnings))
#                #print "DEBUG: %s) %s: %s"  %(rank, name, winnings)
#                self.addPlayer(rank, name, winnings, self.currency, None, None, None)
#
#
#            for m in self.re_TourNo.finditer(self.summaryText):
#                mg = m.groupdict()
#                #print mg
#                self.tourNo = mg['TOURNO']

def convert_to_decimal(string):
    dec = string.strip(u'€&euro;\u20ac')
    dec = dec.replace(u',','.')
    dec = dec.replace(u' ','')
    dec = Decimal(dec)
    return dec

