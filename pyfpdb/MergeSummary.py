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
    limits = { 'No Limit':'nl', 'No Limit ':'nl', 'Fixed Limit':'fl', 'Limit':'fl', 'Pot Limit':'pl', 'Pot Limit ':'pl', 'Half Pot Limit':'hp'}
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
                     'Razz'  : ('stud','razz')
            }
    games_html = {
                    'Texas Holdem' : ('hold','holdem'),
                           'Omaha' : ('hold','omahahi'),
                      'Omaha HiLo' : ('hold','omahahilo'),
            '2-7 Low Triple Draw'  : ('draw','27_3draw'),
                         'Badugi'  : ('draw','badugi'),
                'Seven Card Stud'  : ('stud','studhi'),
           'Seven Card Stud HiLo'  : ('stud','studhilo'),
                 'Five Card Stud'  : ('stud','studhilo'),
                           'Razz'  : ('stud','razz')
                }
    
    months = { 'January':1, 'Jan':1, 'February':2, 'Feb':2, 'March':3, 'Mar':3,
                     'April':4, 'Apr':4, 'May':5, 'May':5, 'June':6, 'Jun':6,
                      'July':7, 'Jul':7, 'August':8, 'Aug':8, 'September':9, 'Sep':9,
                   'October':10, 'Oct':10, 'November':11, 'Nov':11, 'December':12, 'Dec':12}


    substitutions = {
                     'LEGAL_ISO' : "USD|EUR|GBP|CAD|FPP",     # legal ISO currency codes
                            'LS' : u"\$|\xe2\x82\xac|\u20ac|" # legal currency symbols
                    }
    re_GameTypeHH = re.compile(r'<description type="(?P<GAME>Holdem|Omaha|Omaha|Omaha\sH/L8|2\-7\sLowball|A\-5\sLowball|Badugi|5\-Draw\sw/Joker|5\-Draw|7\-Stud|7\-Stud\sH/L8|5\-Stud|Razz|HORSE)(?P<TYPE>\sTournament)?" stakes="(?P<LIMIT>[a-zA-Z ]+)(\s\(?\$?(?P<SB>[.0-9]+)?/?\$?(?P<BB>[.0-9]+)?(?P<blah>.*)\)?)?"/>', re.MULTILINE)
    re_HandInfoHH = re.compile(r'<game id="(?P<HID1>[0-9]+)-(?P<HID2>[0-9]+)" starttime="(?P<DATETIME>[0-9]+)" numholecards="[0-9]+" gametype="[0-9]+" (multigametype="(?P<MULTIGAMETYPE>\d+)" )?(seats="(?P<SEATS>[0-9]+)" )?realmoney="(?P<REALMONEY>(true|false))" data="[0-9]+\|(?P<TABLENAME>[^|]+)\|(?P<TDATA>[^|]+)\|?.*>', re.MULTILINE)
    
    re_HTMLName = re.compile("Name</th><td>(?P<NAME>.+?)</td>")
    re_HTMLGameType = re.compile("""Game Type</th><td>(?P<LIMIT>Fixed Limit|No Limit|Pot Limit) (?P<GAME>Texas\sHoldem|Omaha|Omaha\sHiLo|2\-7\sLow\sTriple\sDraw|Badugi|Seven\sCard\sStud|Seven\sCard\sStud\sHiLo|Five\sCard\sStud|Razz|HORSE|HA|HO)</td>""")
    re_HTMLBuyIn = re.compile("Buy In</th><td>(?P<BUYIN>[0-9,.]+)</td>")
    re_HTMLFee = re.compile("Entry Fee</th><td>(?P<FEE>[0-9,.]+)</td>")
    re_HTMLBounty = re.compile("Bounty</th><td>(?P<KOBOUNTY>.+?)</td>")
    re_HTMLAddons = re.compile("Addons</th><td>(?P<ADDON>.+?)</td>")
    re_HTMLRebuy = re.compile("Rebuys</th><td>(?P<REBUY>.+?)</td>")
    re_HTMLTourNo = re.compile("Game ID</th><td>(?P<TOURNO>[0-9]+)-1</td>")
    re_HTMLPlayer = re.compile(u"""<tr><td align="center">(?P<RANK>\d+)</td><td>(?P<PNAME>.+?)</td><td>(?P<WINNINGS>.+?)</td></tr>""")
    re_HTMLDetails = re.compile(u"""<p class="text">(?P<LABEL>.+?) : (?P<VALUE>.+?)</p>""")
    re_HTMLPrizepool = re.compile(u"""Total Prizepool</th><td>(?P<PRIZEPOOL>[0-9,.]+)</td>""")
    re_HTMLStartTime = re.compile("Start Time</th><td>(?P<STARTTIME>.+?)</td>")
    re_HTMLDateTime = re.compile("\w+?\s+?(?P<D>\d+)\w+?\s+(?P<M>\w+)\s+(?P<Y>\d+),?\s+(?P<H>\d+):(?P<MIN>\d+):(?P<S>\d+)")
    
    re_Ticket = re.compile(u""" / Ticket (?P<VALUE>[0-9.]+)&euro;""")

    codepage = ["utf-8"]

    @staticmethod
    def getSplitRe(self, head):
        re_SplitTourneys = re.compile("PokerStars Tournament ")
        return re_SplitTourneys

    def parseSummary(self):
        # id type of file and call correct function
        m = self.re_GameTypeHH.search(self.summaryText)
        if m:
            mg = m.groupdict()
            if ' Tournament' == mg['TYPE']:
                self.parseSummaryFromHH(mg)
        else:
            self.parseSummaryFile()

    def parseSummaryFromHH(self, mg):
        if 'LIMIT' in mg:
            self.gametype['limitType'] = self.limits[mg['LIMIT']]
        if 'GAME' in mg:
            if mg['GAME'] == "HORSE":
                log.error(_("MergeSummary.determineGameType: HORSE found, unsupported"))
                raise FpdbParseError
                #(self.info['base'], self.info['category']) = self.Multigametypes[m2.group('MULTIGAMETYPE')]
            else:
                self.gametype['category'] = self.games[mg['GAME']][1]
        m = self.re_HandInfoHH.search(self.summaryText)
        if m is None:
            tmp = self.summaryText[0:200]
            log.error(_("MergeSummary.readHandInfo: '%s'") % tmp)
            raise FpdbParseError
            
        tourneyNameFull = m.group('TABLENAME')
        self.tourneyName = m.group('TABLENAME')[:40]
        self.tourNo = re.split('-', m.group('TDATA'))[0]
        self.startTime = datetime.datetime.strptime(m.group('DATETIME')[:12],'%Y%m%d%H%M')
        self.startTime = HandHistoryConverter.changeTimezone(self.startTime, "ET", "UTC")
        obj = getattr(MergeToFpdb, "Merge", None)
        hhc = obj(self.config, in_path = self.in_path, sitename = None, autostart = False)
        
        if tourneyNameFull not in hhc.SnG_Structures:
            log.error(_("MergeSummary.determineGameType: No match in SnG_Structures"))
            raise FpdbParseError
        
        self.buyin     = int(100*hhc.SnG_Structures[tourneyNameFull]['buyIn'])
        self.fee       = int(100*hhc.SnG_Structures[tourneyNameFull]['fee'])
        self.entries   = hhc.SnG_Structures[tourneyNameFull]['seats']
        self.buyinCurrency = hhc.SnG_Structures[tourneyNameFull]['currency']
        self.currency  = hhc.SnG_Structures[tourneyNameFull]['payoutCurrency']
        self.maxseats  = hhc.SnG_Structures[tourneyNameFull]['seats']
        self.prizepool = sum(hhc.SnG_Structures[tourneyNameFull]['payouts'])
        payouts = len(hhc.SnG_Structures[tourneyNameFull]['payouts'])
        self.isSng     = True
        
        if hhc.SnG_Structures[tourneyNameFull]['multi']:
            log.error(_("MergeSummary.determineGameType: Muli-table SnG found, unsupported"))
            raise FpdbParseError
        
        handsList = hhc.allHandsAsList()
        for handText in handsList:
            players, out, won = {}, [], []
            for m in hhc.re_PlayerOut.finditer(handText):
                out.append(m.group('PSEAT'))
            if out:
                for m in hhc.re_PlayerInfo.finditer(handText):
                    players[m.group('SEAT')] = m.group('PNAME')
                if not players: continue
                for m in hhc.re_CollectPot.finditer(handText):
                    won.append(m.group('PSEAT'))
                i = 0
                for n in out:
                    winnings = 0
                    if n in won:
                        rank = 1
                        winnings = int(100*hhc.SnG_Structures[tourneyNameFull]['payouts'][0])
                    else:
                        rank = len(players) - i
                        if rank <= payouts:
                            winnings = int(100*hhc.SnG_Structures[tourneyNameFull]['payouts'][rank-1])
                        i += 1
                    self.addPlayer(rank, players[n], winnings, self.currency, 0, 0, 0)

    def parseSummaryFile(self):
        self.buyinCurrency = "USD"
        soup = BeautifulSoup(self.summaryText)
        tables = soup.findAll('table')
        table1 = BeautifulSoup(str(tables[0])).findAll('tr')
        table2 = BeautifulSoup(str(tables[1])).findAll('tr')
        # FIXME: Searching every line for all regexes is pretty horrible
        # FIXME: Need to search for 'Status:  Finished'
        #print self.in_path
        for p in table1:
            m = self.re_HTMLGameType.search(str(p))
            if m:
                #print "DEBUG: re_HTMLGameType: '%s' '%s'" %(m.group('LIMIT'), m.group('GAME'))
                if m.group('GAME') in ("HORSE", "HA", "HO"):
                    log.error(_("MergeSummary.parseSummaryFile: %s found, unsupported") % m.group('GAME'))
                    raise FpdbParseError
                self.gametype['limitType'] = self.limits[m.group('LIMIT')]
                self.gametype['category']  = self.games_html[m.group('GAME')][1]
            m = self.re_HTMLTourNo.search(str(p))
            if m:
                #print "DEBUG: re_HTMLTourNo: '%s'" % m.group('TOURNO')
                self.tourNo = m.group('TOURNO')
            m = self.re_HTMLName.search(str(p))
            if m:
                #print "DEBUG: re_HTMLName: '%s'" % m.group('NAME')
                self.tourneyName = m.group('NAME')[:40]
                if m.group('NAME').find("$")!=-1:
                    self.buyinCurrency="USD"
                elif m.group('NAME').find(u"€")!=-1:
                    self.buyinCurrency="EUR"
            m = self.re_HTMLPrizepool.search(str(p))
            if m:
                #print "DEBUG: re_HTMLPrizepool: '%s'" % m.group('PRIZEPOOL')
                self.prizepool = int(convert_to_decimal(m.group('PRIZEPOOL')))
            m = self.re_HTMLBuyIn.search(str(p))
            if m:
                #print "DEBUG: re_HTMLBuyIn: '%s'" % m.group('BUYIN')
                self.buyin = int(100*convert_to_decimal(m.group('BUYIN')))
                if self.buyin==0:
                    self.buyinCurrency="FREE"
            m = self.re_HTMLFee.search(str(p))
            if m:
                #print "DEBUG: re_HTMLFee: '%s'" % m.group('FEE')
                self.fee = int(100*convert_to_decimal(m.group('FEE')))
            m = self.re_HTMLBounty.search(str(p))
            if m:
                #print "DEBUG: re_HTMLBounty: '%s'" % m.group('KOBOUNTY')
                if m.group('KOBOUNTY') != '0.00':
                    self.isKO = True
                    self.koBounty = int(100*convert_to_decimal(m.group('KOBOUNTY')))
            m = self.re_HTMLAddons.search(str(p))
            if m:
                #print "DEBUG: re_HTMLAddons: '%s'" % m.group('ADDON')
                if m.group('ADDON') != '0':
                    self.isAddOn = True
                    self.addOnCost = self.buyin
            m = self.re_HTMLRebuy.search(str(p))
            if m:
                #print "DEBUG: re_HTMLRebuy: '%s'" % m.group('REBUY')
                if m.group('REBUY') != '0':
                    self.isRebuy   = True
                    self.rebuyCost = self.buyin
            m = self.re_HTMLStartTime.search(str(p))
            if m:
                m2 = self.re_HTMLDateTime.search(m.group('STARTTIME'))
                if m2:
                    month = self.months[m2.group('M')]
                    datetimestr = "%s/%s/%s %s:%s:%s" % (m2.group('Y'), month,m2.group('D'),m2.group('H'),m2.group('MIN'),m2.group('S'))
                    self.startTime = datetime.datetime.strptime(datetimestr, "%Y/%m/%d %H:%M:%S")
                    self.startTime = HandHistoryConverter.changeTimezone(self.startTime, "ET", "UTC")
        
        self.currency = self.buyinCurrency
        for p in table2:
            m = self.re_HTMLPlayer.search(str(p))
            if m:
                self.entries += 1
                #print "DEBUG: rank: %s pname: %s won: %s" %(m.group('RANK'), m.group('PNAME'), m.group('WINNINGS'))
                winnings = 0
                rebuyCount = 0
                addOnCount = 0
                koCount = 0
                
                rank = int(m.group('RANK'))
                name = m.group('PNAME')
                if m.group('WINNINGS') != None:
                    if m.group('WINNINGS').find("$")!=-1:
                        self.currency="USD"
                    elif m.group('WINNINGS').find(u"€")!=-1:
                        self.currency="EUR"
                    winnings = int(100*convert_to_decimal(m.group('WINNINGS')))
                self.addPlayer(rank, name, winnings, self.currency, rebuyCount, addOnCount, koCount)
                
def convert_to_decimal(string):
    dec = string.strip(u'€&euro;\u20ac$')
    dec = dec.replace(u',','.')
    dec = dec.replace(u' ','')
    dec = Decimal(dec)
    return dec

