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
                           "5 Card Omaha": ('hold','5_omahahi'),
                     "5 Card Omaha Hi/Lo": ('hold','5_omahahi'), #incorrect in file
                            "Omaha Hi/Lo": ('hold','omahahilo'),
                            "7-Card Stud": ('stud','studhi'),
                      "7-Card Stud Hi/Lo": ('stud','studhilo'),
                                   "Razz": ('stud','razz'),
                        "2-7 Triple Draw": ('draw','27_3draw')
               }

    substitutions = {
                     'LEGAL_ISO' : "USD|EUR|GBP|CAD|FPP",     # legal ISO currency codes
                            'LS' : u"\$|\xe2\x82\xac|\u20ac|" # legal currency symbols
                    }
    
    re_Identify = re.compile(u"Winamax\sPoker\s\-\sTournament\ssummary")
    
    re_SummaryTourneyInfo = re.compile(u"""\s:\s
                                           ((?P<LIMIT>No\sLimit|Limit|LIMIT|Pot\sLimit)\s)?
                                           (?P<GAME>.+)?
                                           \((?P<TOURNO>[0-9]+)\)(\s-\sLate\sregistration)?\s+
                                           (Player\s:\s(?P<PNAME>.*)\s+)?
                                           Buy-In\s:\s(?P<BUYIN>(?P<BIAMT>.+)\s\+\s(?P<BIRAKE>.+)|Freeroll|Gratuit|Ticket\suniquement|Free|Ticket)\s+
                                           (Rebuy\scost\s:\s(?P<REBUY>(?P<REBUYAMT>.+)\s\+\s(?P<REBUYRAKE>.+))\s+)?
                                           (Addon\scost\s:\s(?P<ADDON>(?P<ADDONAMT>.+)\s\+\s(?P<ADDONRAKE>.+))\s+)?
                                           (Your\srebuys\s:\s(?P<PREBUYS>\d+)\s+)?
                                           (Your\saddons\s:\s(?P<PADDONS>\d+)\s+)?
                                           Registered\splayers\s:\s(?P<ENTRIES>[0-9]+)\s+
                                           (Total\srebuys\s:\s\d+\s+)?
                                           (Total\saddons\s:\s\d+\s+)?
                                           Prizepool\s:\s(?P<PRIZEPOOL>[.0-9%(LS)s]+)\s+
                                           (Mode\s:\s(?P<TTYPE>(ttType|sngType))\s:\s.+\s+)?
                                           (Speed\s:\s(?P<SPEED>.+)?\s+)?
                                           (Flight\sID\s:\s.+\s+)?
                                           (Levels\s:\s.+\s+)?
                                           Tournament\sstarted\s(?P<DATETIME>[0-9]{4}\/[0-9]{2}\/[0-9]{2}\s[0-9]{2}:[0-9]{2}:[0-9]{2}\sUTC)\s+
                                           (?P<BLAH>You\splayed\s.+)\s+
                                           You\sfinished\sin\s(?P<RANK>[.0-9]+)(st|nd|rd|th)?\splace\s+
                                           (You\swon\s(?P<WINNINGS>[.0-9%(LS)s]+))?
                                        """ % substitutions ,re.VERBOSE|re.MULTILINE)

    re_GameType = re.compile("""<h1>((?P<LIMIT>No Limit|Pot Limit) (?P<GAME>Hold\'em|Omaha))</h1>""")

    re_TourNo = re.compile("ID\=(?P<TOURNO>[0-9]+)")

    re_Player = re.compile(u"""(?P<RANK>\d+)<\/td><td width="30%">(?P<PNAME>.+?)<\/td><td width="60%">(?P<WINNINGS>.+?)</td>""")

    re_Details = re.compile(u"""<p class="text">(?P<LABEL>.+?) : (?P<VALUE>.+?)</p>""")
    re_Prizepool = re.compile(u"""<div class="title2">.+: (?P<PRIZEPOOL>[0-9,]+)""")

    re_DateTime = re.compile("\[(?P<Y>[0-9]{4})\/(?P<M>[0-9]{2})\/(?P<D>[0-9]{2})[\- ]+(?P<H>[0-9]+):(?P<MIN>[0-9]+):(?P<S>[0-9]+)")
    re_Ticket = re.compile(u""" / (?P<TTYPE>Ticket (?P<VALUE>[0-9.]+)&euro;|Tremplin Winamax Poker Tour|Starting Block Winamax Poker Tour|Finale Freeroll Mobile 2012|SNG Freeroll Mobile 2012)""")

    codepage = ("utf8", "cp1252")

    @staticmethod
    def getSplitRe(self, head):
        re_SplitTourneys = re.compile("Winamax\sPoker\s-\sTournament\ssummary")
        m = re.search("<!DOCTYPE html PUBLIC", head)
        if m != None:
            self.hhtype = "html"
        else:
            self.hhtype = "summary"
        return re_SplitTourneys

    def parseSummary(self):
        if self.hhtype == "summary":
            self.parseSummaryFile()
        elif self.hhtype == "html":
            self.parseSummaryHtml()

    def parseSummaryHtml(self):
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
        else:
            #FIXME: No gametype
            #       Quitte or Double, Starting Block Winamax Poker Tour
            #       Do not contain enough the gametype.
            # Lookup the tid from the db, if it exists get the gametype info from there, otherwise ParseError
            log.warning(_("WinamaxSummary.parseSummary: Gametype unknown defaulting to NLHE"))
            self.gametype['limitType'] = 'nl'
            self.gametype['category'] = 'holdem'

        for m in self.re_Player.finditer(str(tl[0])):
            winnings = 0
            mg = m.groupdict()
            rank     = mg['RANK']
            name     = mg['PNAME']
            if rank!='...':
                rank = int(mg['RANK'])
                #print "DEUBG: mg: '%s'" % mg
                is_satellite = self.re_Ticket.search(mg['WINNINGS'])
                if is_satellite:
                    # Ticket
                    if is_satellite.group('VALUE'):
                        winnings = self.convert_to_decimal(is_satellite.group('VALUE'))
                    else: # Value not specified
                        rank = 1
                        # FIXME: Do lookup here
                        # Tremplin Winamax Poker Tour
                        # Starting Block Winamax Poker Tour
                        pass
                    # For stallites, any ticket means 1st
                    if winnings > 0:
                        rank = 1
                else:
                    winnings = self.convert_to_decimal(mg['WINNINGS'])
    
                winnings = int(100*Decimal(winnings))
                #print "DEBUG: %s) %s: %s"  %(rank, name, winnings)
                self.addPlayer(rank, name, winnings, self.currency, None, None, None)


        for m in self.re_TourNo.finditer(self.summaryText):
            mg = m.groupdict()
            #print mg
            self.tourNo = mg['TOURNO']

    def parseSummaryFile(self):
        m = self.re_SummaryTourneyInfo.search(self.summaryText)
        if m == None:
            tmp = self.summaryText[0:200]
            log.error(_("WinamaxSummary.parseSummaryFromFile: '%s'") % tmp)
            raise FpdbParseError

        mg = m.groupdict()
        #print "DEBUG: m.groupdict(): %s" % m.groupdict()

        if 'LIMIT' in mg and mg['LIMIT'] != None:
            self.gametype['limitType'] = self.limits[mg['LIMIT']]
            self.gametype['category'] = self.games[mg['GAME']][1]
        else:
            #FIXME: No gametype
            #       Quitte or Double, Starting Block Winamax Poker Tour
            #       Do not contain enough the gametype.
            # Lookup the tid from the db, if it exists get the gametype info from there, otherwise ParseError
            log.warning(_("WinamaxSummary.parseSummary: Gametype unknown defaulting to NLHE"))
            self.gametype['limitType'] = 'nl'
            self.gametype['category'] = 'holdem'
            self.tourneyName = mg['GAME']
        if 'ENTRIES' in mg:
            self.entries   = mg['ENTRIES']
        if 'PRIZEPOOL' in mg:
            self.prizepool = int(100*self.convert_to_decimal(mg['PRIZEPOOL']))
        if 'DATETIME' in mg:
            self.startTime = datetime.datetime.strptime(mg['DATETIME'], "%Y/%m/%d %H:%M:%S UTC")

        #FIXME: buyinCurrency and currency not detected
        self.buyinCurrency = 'EUR'
        self.currency  = 'EUR'

        if 'BUYIN' in mg:
            #print "DEBUG: BUYIN '%s'" % mg['BUYIN']
            if mg['BUYIN'] in ('Gratuit', 'Freeroll', 'Ticket uniquement', 'Ticket'):
                self.buyin = 0
                self.fee = 0
                self.buyinCurrency = "FREE"
            else:
                if mg['BUYIN'].find(u"€")!=-1:
                    self.buyinCurrency="EUR"
                elif mg['BUYIN'].find("FPP")!=-1:
                    self.buyinCurrency="WIFP"
                elif mg['BUYIN'].find("Free")!=-1:
                    self.buyinCurrency="WIFP"
                else:
                    self.buyinCurrency="play"
                rake = mg['BIRAKE'].strip('\r')
                self.buyin = int(100*self.convert_to_decimal(mg['BIAMT']))
                self.fee   = int(100*self.convert_to_decimal(rake))
    
                if self.buyin == 0 and self.fee == 0:
                    self.buyinCurrency = "FREE"
                
        if 'REBUY' in mg and mg['REBUY'] != None:
            self.isRebuy   = True
            rebuyrake = mg['REBUYRAKE'].strip('\r')
            rebuyamt = int(100*self.convert_to_decimal(mg['REBUYAMT']))
            rebuyfee   = int(100*self.convert_to_decimal(rebuyrake))
            self.rebuyCost = rebuyamt + rebuyfee
        if 'ADDON' in mg and mg['ADDON'] != None:
            self.isAddOn = True
            addonrake = mg['ADDONRAKE'].strip('\r')
            addonamt = int(100*self.convert_to_decimal(mg['ADDONAMT']))
            addonfee   = int(100*self.convert_to_decimal(addonrake))
            self.addOnCost = addonamt + addonfee

        if 'TOURNO' in mg:
            self.tourNo = mg['TOURNO']
        #self.maxseats  =
        if int(self.entries) <= 10: #FIXME: obv not a great metric
            self.isSng     = True
        if 'TTYPE' in mg and mg['TTYPE'] != None:
            if mg['TTYPE']=='sngType':
                self.isSng = True
        if 'SPEED' in mg and mg['SPEED'] != None:
            if mg['SPEED']=='turbo':
                self.speed = 'Hyper'
            elif mg['SPEED']=='semiturbo':
                self.speed = 'Turbo'
            
        if 'PNAME' in mg and mg['PNAME'] is not None:
            name = mg['PNAME'].strip('\r')
            rank = mg['RANK']
            if rank!='...':
                rank = int(mg['RANK'])
                winnings = 0
                rebuyCount = None
                addOnCount = None
                koCount = None
    
                if 'WINNINGS' in mg and mg['WINNINGS'] != None:
                    if mg['WINNINGS'].find(u"€")!=-1:
                        self.currency="EUR"
                    elif mg['WINNINGS'].find("FPP")!=-1:
                        self.currency="WIFP"
                    elif mg['WINNINGS'].find("Free")!=-1:
                        self.currency="WIFP"
                    else:
                        self.currency="play"
                    winnings = int(100*self.convert_to_decimal(mg['WINNINGS']))
                if 'PREBUYS' in mg and mg['PREBUYS'] != None:
                    rebuyCount = int(mg['PREBUYS'])
                if 'PADDONS' in mg and mg['PADDONS'] != None:
                    addOnCount = int(mg['PADDONS'])
    
                #print "DEBUG: addPlayer(%s, %s, %s, %s, %s, %s, %s)" %(rank, name, winnings, self.currency, rebuyCount, addOnCount, koCount)
                self.addPlayer(rank, name, winnings, self.currency, rebuyCount, addOnCount, koCount)

    def convert_to_decimal(self, string):
        dec = self.clearMoneyString(string)
        dec = Decimal(dec)
        return dec

