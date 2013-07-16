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
                             'Omaha Hi' : ('hold','omahahi'),
                          'Omaha Hi/Lo' : ('hold','omahahilo'),
                            'Omaha H/L' : ('hold','omahahilo'),
                      '5 Card Omaha Hi' : ('hold', '5_omahahi'),
                      '6 Card Omaha Hi' : ('hold', '6_omahahi'),
                        'Courchevel Hi' : ('hold', 'cour_hi'),
                                'Irish' : ('hold', 'irish'),
                                 'Razz' : ('stud','razz'), 
                                 'RAZZ' : ('stud','razz'),
                          '7 Card Stud' : ('stud','studhi'),
                              'Stud Hi' : ('stud','studhi'),
                    '7 Card Stud Hi/Lo' : ('stud','studhilo'),
                             'Stud H/L' : ('stud','studhilo'),
                          '5 Card Stud' : ('stud', '5_studhi'),
                       '5-Card Stud Hi' : ('stud', '5_studhi'),
                               'Badugi' : ('draw','badugi'),
                      '2-7 Single Draw' : ('draw','27_1draw'),
              'Triple Draw 2-7 Lowball' : ('draw','27_3draw'),
                      '2-7 Triple Draw' : ('draw','27_3draw'),
                          '5 Card Draw' : ('draw','fivedraw'),
                         '7-Game Mixed' : ('mixed','7game'),
                         '8-Game Mixed' : ('mixed','8game'),
                         '9-Game Mixed' : ('mixed','9game'),
                        '10-Game Mixed' : ('mixed','10game'),
                                   'HA' : ('mixed','ha'),
                                'HEROS' : ('mixed','heros'),
                                   'HO' : ('mixed','ho'),
                                  'HOE' : ('mixed','hoe'),
                                'HORSE' : ('mixed','horse'),
                                 'HOSE' : ('mixed','hose'),
                                   'OA' : ('mixed','oa'),
                                   'OE' : ('mixed','oe'),
                                   'SE' : ('mixed','se')                                   
               }

    substitutions = {
                     'LEGAL_ISO' : "USD|EUR|GBP|CAD|FPP|FTP",      # legal ISO currency codes
                            'LS' : u"\$|\xe2\x82\xac|\u20ac|", # legal currency symbols - Euro(cp1252, utf-8)
                           'TAB' : u"-\u2013'\s\da-zA-Z#_\.",      # legal characters for tablename
                           'NUM' : u".,\dKM",                    # legal characters in number format
                    }

    re_Identify = re.compile(u'Full\sTilt\sPoker\.fr\sTournament|Full\sTilt\sPoker\sTournament\sSummary')
    re_TourNo = re.compile("\#(?P<TOURNO>[0-9]+),")
    re_TourneyInfo = re.compile(u"""
                        \s(?P<TOURNAMENT>.+?)\s(\((?P<TOURPAREN>.+)\)\s+)?
                        \((?P<TOURNO>[0-9]+)\)
                        (\s+)?(\sMatch\s(?P<MATCHNO>\d)\s)?
                        (?P<GAME>Hold\'em|Irish|Courchevel\sHi|Razz|RAZZ|5(-|\s)Card\sStud(\sHi)?|7\sCard\sStud|7\sCard\sStud\sHi/Lo|Stud\sH/L|Stud\sHi|Omaha|((5|6)\sCard\s)?Omaha\sHi|Omaha\sHi/Lo|Omaha\sH/L|2\-7\sSingle\sDraw|Badugi|Triple\sDraw\s2\-7\sLowball|2\-7\sTriple\sDraw|5\sCard\sDraw|\d+\-Game\sMixed|HORSE|HA|HEROS|HO|HOE|HORSE|HOSE|OA|OE|SE)\s+
                        ((?P<LIMIT>No\sLimit|Limit|LIMIT|Pot\sLimit)\s+)?(\((?P<TABLEATTRIBUTES>.+)\)\s+)?
                        (Buy-In:\s[%(LS)s]?(?P<BUYIN>[%(NUM)s]+)(\sFTP|\sT\$|\sPlay\sChips)?(\s\+\s[%(LS)s]?(?P<FEE>[%(NUM)s]+)(\sFTP|\sT\$|\sPlay\sChips)?)?\s+)?
                        (Knockout\sBounty:\s[%(LS)s](?P<KOBOUNTY>[%(NUM)s]+)\s+)?
                        ((?P<PNAMEBOUNTIES>.{2,15})\sreceived\s(?P<PBOUNTIES>\d+)\sKnockout\sBounty\sAwards?\s+)?
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
                        (Total\sPrize\sPool:\s[%(LS)s]?(?P<PRIZEPOOL>[%(NUM)s]+)(\sFTP|\sT\$|\sPlay\sChips)?\s+)?
                        (?P<SATELLITE>Top\s(\d+\s)?finishers?\sreceives?\s.+\s+)?
                        (Target\sTournament\s.+\s+)?
                        Tournament\sstarted:\s(?P<DATETIME>((?P<Y>[\d]{4})\/(?P<M>[\d]{2})\/(?P<D>[\d]+)\s+(?P<H>[\d]+):(?P<MIN>[\d]+):(?P<S>[\d]+)\s??(?P<TZ>[A-Z]+)\s|\w+,\s(?P<MONTH>\w+)\s(?P<DAY>\d+),\s(?P<YEAR>[\d]{4})\s(?P<HOUR>\d+):(?P<MIN2>\d+)))
                               """ % substitutions ,re.VERBOSE|re.MULTILINE|re.DOTALL)
    
    re_TourneyExtraInfo = re.compile('''(((?P<SPEED1>(Turbo|Super\sTurbo|Escalator))\s?)?
                                         ((?P<CURRENCY>[%(LS)s])?(?P<BUYINGUAR>[%(NUM)s]+)?(\s*\+\s*[%(LS)s]?(?P<FEE>[%(NUM)s]+))?\s?)?
                                         ((?P<SPEED2>(Turbo|Super\sTurbo|Escalator))\s?)?
                                         ((?P<SPECIAL>(Play\sMoney|Freeroll|KO|Knockout|Heads\sUp|Heads\-Up|Head\'s\sUp|Matrix|Rebuy|Madness|Rush))\s?)?
                                         ((?P<SHOOTOUT>Shootout)\s?)?
                                         ((?P<SNG>Sit\s&\sGo)\s?)?
                                         ((?P<STEP>Step\s(?P<STEPNO>\d))\s?)?
                                         ((?P<GUARANTEE>Guar(antee)?))?)
                                    ''' % substitutions, re.MULTILINE|re.VERBOSE)

    re_Currency = re.compile(u"""(?P<CURRENCY>[%(LS)s]|FPP|FTP|T\$|Play\sChips)""" % substitutions)
    re_Max      = re.compile("((?P<MAX>\d+)\sHanded)|(?P<HU>Heads\sUp)", re.MULTILINE)
    re_Stack    = re.compile("((?P<STACK>(Deep|Super))\sStack)", re.MULTILINE)
    re_NewToGame = re.compile("(?P<NEWTOGAME>New\sto\sthe\sGame)", re.MULTILINE)
    re_Speed    = re.compile("(?P<SPEED>(Turbo|Super\sTurbo|Escalator))", re.MULTILINE)
    re_Multi    = re.compile("(?P<MULTI>(Multi-Entry|Re-Entry))", re.MULTILINE)
    re_Chance   = re.compile("((?P<CHANCE>\d)x\sChance)", re.MULTILINE)
    re_Player = re.compile(u"""(?P<RANK>[\d]+):\s(?P<NAME>[^,\r\n]{2,15})(,\s(?P<CURRENCY>[%(LS)s])?(?P<WINNINGS>[.\d]+)(\s(?P<CURRENCY1>FTP|T\$|Play\sChips))?)?(,\s(?P<TICKET>Step\s(?P<LEVEL>\d)\sTicket))?""" % substitutions)
    re_Finished = re.compile(u"""(?P<NAME>[^,\r\n]{2,15}) finished in (?P<RANK>[\d]+)\S\S place""")

    re_DateTime = re.compile("\[(?P<Y>[0-9]{4})\/(?P<M>[0-9]{2})\/(?P<D>[0-9]{2})[\- ]+(?P<H>[0-9]+):(?P<MIN>[0-9]+):(?P<S>[0-9]+)")

    codepage = ["utf-16", "cp1252", "utf-8"]

    @staticmethod
    def getSplitRe(self, head):
        re_SplitTourneys = re.compile("^Full Tilt Poker Tournament Summary")
        return re_SplitTourneys

    def parseSummary(self):
        m = self.re_TourneyInfo.search(self.summaryText[:2000])
        if m == None:
            tmp = self.summaryText[0:200]
            log.error(_("FullTiltPokerSummary.parseSummary: '%s'") % tmp)
            raise FpdbParseError

        #print "DEBUG: m.groupdict(): %s" % m.groupdict()
        rebuyCounts = {}
        addOnCounts = {}
        koCounts = {}
        mg = m.groupdict()
        if 'TOURNO'    in mg: self.tourNo = mg['TOURNO']
        if 'LIMIT'     in mg and mg['LIMIT'] != None:
            self.gametype['limitType'] = self.limits[mg['LIMIT']]
        else:
            self.gametype['limitType'] = 'mx'
        if 'GAME'      in mg: self.gametype['category']  = self.games[mg['GAME']][1]
        if mg['BUYIN'] != None:
            self.buyin = int(100*Decimal(self.clearMoneyString(mg['BUYIN'])))
        if mg['FEE'] != None:
            self.fee   = int(100*Decimal(self.clearMoneyString(mg['FEE'])))                
        if 'PRIZEPOOL' in mg:
            if mg['PRIZEPOOL'] != None: self.prizepool = int(100*Decimal(self.clearMoneyString(mg['PRIZEPOOL'])))
        if 'ENTRIES'   in mg:
            self.entries = int(mg['ENTRIES'])
        if 'REBUYAMT'in mg and mg['REBUYAMT'] != None:
            self.isRebuy   = True
            self.rebuyCost = int(100*Decimal(self.clearMoneyString(mg['REBUYAMT'])))
        if 'ADDON' in mg and mg['ADDON'] != None:
            self.isAddOn = True
            self.addOnCost = int(100*Decimal(self.clearMoneyString(mg['ADDON'])))
        if 'KOBOUNTY' in mg and mg['KOBOUNTY'] != None:
            self.isKO = True
            self.koBounty = int(100*Decimal(self.clearMoneyString(mg['KOBOUNTY'])))
        if 'PREBUYS' in mg and mg['PREBUYS'] != None:
            rebuyCounts[mg['P2NAME']] = int(mg['PREBUYS'])
        if 'PADDONS' in mg and mg['PADDONS'] != None:
            addOnCounts[mg['P1NAME']] = int(mg['PADDONS'])
        if 'PBOUNTIES' in mg and mg['PBOUNTIES'] != None:
            koCounts[mg['PNAMEBOUNTIES']] = int(mg['PBOUNTIES'])
        if 'SATELLITE' in mg and mg['SATELLITE'] != None:
            self.isSatellite = True
        
        entryId = 1    
        if mg['TOURNAMENT'] != None:
            self.tourneyName = mg['TOURNAMENT']
            if mg['TOURPAREN'] != None:
                self.tourneyName += ' ' + mg['TOURPAREN']
            n = self.re_TourneyExtraInfo.search(mg['TOURNAMENT'])
            if n.group('SNG') is not None:
                self.isSng = True
            if "Rush" in mg['TOURNAMENT']:
                self.isFast = True
            if "On Demand" in mg['TOURNAMENT']:
                self.isOnDemand = True
            if n.group('SPECIAL') is not None :
                special = n.group('SPECIAL')
                if special == "Rebuy":
                    self.isRebuy = True
                if special == "KO":
                    self.isKO = True
                if re.search("Matrix", special):
                    self.isMatrix = True
                    if mg['MATCHNO'] != None:
                        entryId = int(mg['MATCHNO'])
                    else:
                        entryId = 5
                if special == "Shootout":
                    self.isShootout = True
            if n.group('GUARANTEE')!=None:
                self.isGuarantee = True
            if self.isGuarantee and n.group('BUYINGUAR')!=None:
                self.guaranteeAmt = int(100*Decimal(self.clearMoneyString(n.group('BUYINGUAR'))))
            if n.group('STEP')!=None:
                self.isStep = True
            if n.group('STEPNO')!=None:
                self.stepNo = int(n.group('STEPNO'))
            if self.isMatrix:
                self.buyin = self.prizepool / self.entries
                buyinfee = int(100*Decimal(self.clearMoneyString(n.group('BUYINGUAR'))))
                self.fee = buyinfee - self.buyin
                self.isSng = True
            
        tableAttributes = None
        if mg['TABLEATTRIBUTES'] != None and mg['TOURPAREN'] != None:
            tableAttributes = mg['TOURPAREN'] + ' ' + mg['TABLEATTRIBUTES']
        elif mg['TABLEATTRIBUTES'] != None:
            tableAttributes = mg['TABLEATTRIBUTES']
        elif mg['TOURPAREN'] != None:
            tableAttributes = mg['TOURPAREN']
        if tableAttributes:
            # search for keywords "max" and "heads up"
            max_found = self.re_Max.search(tableAttributes)
            if max_found:
                if max_found.group('MAX') != None:
                    self.maxseats = int(max_found.group('MAX'))
                elif max_found.group('HU') != None:
                    self.maxseats = 2
            speed_found = self.re_Speed.search(tableAttributes)
            if speed_found:
                if speed_found.group('SPEED')=='Super Turbo':
                    self.speed = 'Hyper'
                else:
                    self.speed = speed_found.group('SPEED')
            multi_found = self.re_Multi.search(tableAttributes)
            if multi_found:
                if multi_found.group('MULTI')=='Multi-Entry':
                    self.isMultiEntry = True
                elif multi_found.group('MULTI')=='Re-Entry':
                    self.isReEntry = True
            stack_found = self.re_Stack.search(tableAttributes)
            if stack_found:
                self.stack = stack_found.group('STACK')
            new_found = self.re_NewToGame.search(tableAttributes)
            if new_found:
                self.isNewToGame = True
            chance_found = self.re_Chance.search(tableAttributes)
            if chance_found:
                self.isChance = True
                self.chanceCount = int(chance_found.group('CHANCE'))
            if 'Cashout' in tableAttributes:
                self.isCashOut = True
                    
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
            log.error("FullTiltPokerSummary.parseSummary: " + _("Unable to locate currency"))
            raise FpdbParseError
        #print "DEBUG: m.groupdict(): %s" % m.groupdict()

        mg = m.groupdict()
        
        if mg['CURRENCY'] == "$":     self.buyinCurrency="USD"
        elif mg['CURRENCY'] == u"€":  self.buyinCurrency="EUR"
        elif mg['CURRENCY'] == "FPP": self.buyinCurrency="FTFP"
        elif mg['CURRENCY'] == "FTP": self.buyinCurrency="FTFP"
        elif mg['CURRENCY'] == "T$":  self.buyinCurrency="FTFP"
        elif mg['CURRENCY'] == 'Play Chips': self.buyinCurrency="play"
        if self.buyin ==0:            self.buyinCurrency="FREE"
        self.currency = self.buyinCurrency

        m = self.re_Player.finditer(self.summaryText)
        playercount = 0
        for a in m:
            mg = a.groupdict()
            #print "DEBUG: a.groupdict(): %s" % mg
            if mg['NAME']!='[Player not loa':
                name = mg['NAME']
                rank = int(mg['RANK'])
                winnings = 0
                rebuyCount = 0
                addOnCount = 0
                koCount = 0
    
                if 'WINNINGS' in mg and mg['WINNINGS'] != None:
                    winnings = int(100*Decimal(mg['WINNINGS']))
                    if 'CURRENCY' in mg and mg['CURRENCY'] != None:
                        if mg['CURRENCY'] == "$":     self.currency="USD"
                        elif mg['CURRENCY'] == u"€":  self.currency="EUR"
                    elif 'CURRENCY1' in mg and mg['CURRENCY1'] != None:
                        if mg['CURRENCY1'] == "FPP": self.currency="FTFP"
                        elif mg['CURRENCY1'] == "FTP": self.currency="FTFP"
                        elif mg['CURRENCY1'] == "T$": self.currency="FTFP"
                        elif mg['CURRENCY1'] == "Play Chips": self.currency="play"
                    
                if name in rebuyCounts:
                    rebuyCount = rebuyCounts[name]
                
                if name in addOnCounts:
                    addOnCount = addOnCounts[name]
                    
                if name in koCounts:
                    koCount = koCounts[name]
                    
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
                    
                self.addPlayer(rank, name, winnings, self.currency, rebuyCount, addOnCount, koCount, entryId)
    
                playercount += 1


        # Some files dont contain the normals lines, and only contain the line
        # <PLAYER> finished in XXXXrd place
        if playercount == 0:
            m = self.re_Finished.finditer(self.summaryText)
            for a in m:
                winnings = 0
                name = a.group('NAME')
                rank = a.group('RANK')
                self.addPlayer(rank, name, winnings, self.currency, 0, 0, 0)
