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
    limits = { 'No Limit':'nl', 'Pot Limit':'pl', 'Limit':'fl', 'LIMIT':'fl', 'NL':'nl', 'PL':'pl', 'Fixed':'fl'}
    games = {                          # base, category
                              "Hold'em" : ('hold','holdem'), 
                               "Holdem" : ('hold','holdem'), 
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
                               '7 Stud' : ('stud','studhi'),
                              'Stud Hi' : ('stud','studhi'),
                         '7 Stud Hi/Lo' : ('stud','studhilo'),
                    '7 Card Stud Hi/Lo' : ('stud','studhilo'),
                             'Stud H/L' : ('stud','studhilo'),
                          '5-Card Stud' : ('stud', '5_studhi'),
                          '5 Card Stud' : ('stud', '5_studhi'),
                       '5-Card Stud Hi' : ('stud', '5_studhi'),
                               'Badugi' : ('draw','badugi'),
                      '2-7 Single Draw' : ('draw','27_1draw'),
              'Triple Draw 2-7 Lowball' : ('draw','27_3draw'),
                      '2-7 Triple Draw' : ('draw','27_3draw'),
                      'A-5 Triple Draw' : ('draw','a5_3draw'),
                          '5 Card Draw' : ('draw','fivedraw'),
                               '7-Game' : ('mixed','7game'),
                               '8-Game' : ('mixed','8game'),
                               '9-Game' : ('mixed','9game'),
                              '10-Game' : ('mixed','10game'),
                              '25-Game' : ('mixed','25game'),
                         '7-Game Mixed' : ('mixed','7game'),
                         '8-Game Mixed' : ('mixed','8game'),
                         '9-Game Mixed' : ('mixed','9game'),
                        '10-Game Mixed' : ('mixed','10game'),
                        '25-Game Mixed' : ('mixed','25game'),
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
                           'NUM' : u".,\dKMB",                    # legal characters in number format
                    }
    
    months = { 'January':1, 'Jan':1, 'February':2, 'Feb':2, 'March':3, 'Mar':3,
                 'April':4, 'Apr':4, 'May':5, 'May':5, 'June':6, 'Jun':6,
                  'July':7, 'Jul':7, 'August':8, 'Aug':8, 'September':9, 'Sep':9,
               'October':10, 'Oct':10, 'November':11, 'Nov':11, 'December':12, 'Dec':12}

    re_Identify = re.compile(u'Full\sTilt\sPoker\.fr\sTournament|Full\sTilt\sPoker\sTournament\sSummary')
    re_TourNo = re.compile("\#(?P<TOURNO>[0-9]+),")
    re_TourneyInfo = re.compile(u"""
                        \s(?P<TOURNAMENT>.+?)\s(\((?P<TOURPAREN>.+)\)\s+)?
                        \((?P<TOURNO>[0-9]+)\)
                        (\s+)?(\sMatch\s(?P<MATCHNO>\d)\s)?
                        (?P<GAME>Hold\'em|Irish|Courchevel\sHi|Razz|RAZZ|5(-|\s)Card\sStud(\sHi)?|7\sCard\sStud|7\sCard\sStud\sHi/Lo|Stud\sH/L|Stud\sHi|Omaha|((5|6)\sCard\s)?Omaha\sHi|Omaha\sHi/Lo|Omaha\sH/L|2\-7\sSingle\sDraw|Badugi|Triple\sDraw\s2\-7\sLowball|2\-7\sTriple\sDraw|5\sCard\sDraw|A-5\sTriple\sDraw|\d+\-Game(\sMixed)?|HORSE|HA|HEROS|HO|HOE|HORSE|HOSE|OA|OE|SE)\s+
                        ((?P<LIMIT>No\sLimit|Limit|LIMIT|Pot\sLimit)\s+)?(\((?P<TABLEATTRIBUTES>.+)\)\s+)?
                        (Buy-In:\s[%(LS)s]?(?P<BUYIN>[%(NUM)s]+)(\sFTP|\sT\$|\sPlay\sChips)?(\s\+\s[%(LS)s]?(?P<FEE>[%(NUM)s]+)(\sFTP|\sT\$|\sPlay\sChips)?)?\s+)?
                        (Knockout\sBounty:\s[%(LS)s](?P<KOBOUNTY>[%(NUM)s]+)\s+)?
                        ((?P<PNAMEBOUNTIES>(.{2,15}|\d+))\sreceived\s(?P<PBOUNTIES>(%%)?\d+)\sKnockout\sBounty\sAwards?\s+)?
                        (Add-On:\s[%(LS)s]?(?P<ADDON>[%(NUM)s]+)(\sFTP|\sT\$|\sPlay\sChips)?\s+)?
                        (Rebuy:\s[%(LS)s]?(?P<REBUYAMT>[%(NUM)s]+)(\sFTP|\sT\$|\sPlay\sChips)?\s+)?
                        ((?P<P1NAME>.{2,15})\sperformed\s(?P<PADDONS>\d+)\sAdd-Ons?\s+)?
                        ((?P<P2NAME>.{2,15})\sperformed\s(?P<PREBUYS>\d+)\sRebuys?\s+)?
                        (Buy-In\sChips:\s(?P<CHIPS>\d+)\s+)?
                        (Add-On\sChips:\s(?P<ADDONCHIPS>\d+)\s+)?
                        (Rebuy\sChips:\s(?P<REBUYCHIPS>\d+)\s+)?
                        (Cashout\svalue\sof\s\d+\schips:\s[%(LS)s]?\d+(\sFTP|\sT\$|\sPlay\sChips)?\s+)?
                        (?P<ENTRIES>[0-9]+)\sEntries\s+
                        (Total\sAdd-Ons:\s(?P<ADDONS>\d+)\s+)?
                        (Total\sRebuys:\s(?P<REBUYS>\d+)\s*)?
                        (Total\sPrize\sPool:\s[%(LS)s]?(?P<PRIZEPOOL>[%(NUM)s]+)(\sFTP|\sT\$|\sPlay\sChips)?\s+)?
                        (Total\sCashout\sPool:\s[%(LS)s]?(?P<TOTALCASHOUT>[%(NUM)s]+)(\sFTP|\sT\$|\sPlay\sChips)?\s+)?
                        (Current\sCashout\sPool:\s[%(LS)s]?(?P<CURRENTCASHOUT>[%(NUM)s]+)(\sFTP|\sT\$|\sPlay\sChips)?\s+)?
                        (?P<SATELLITE>Top\s(\d+\s)?finishers?\sreceives?\s.+\s+)?
                        (Target\sTournament\s.+\s+)?
                        Tournament\sstarted:\s(?P<DATETIME>((?P<Y>[\d]{4})\/(?P<M>[\d]{2})\/(?P<D>[\d]+)\s+(?P<H>[\d]+):(?P<MIN>[\d]+):(?P<S>[\d]+)\s?(?P<TZ>[A-Z]+)\s|\w+,\s(?P<MONTH>\w+)\s(?P<DAY>\d+),\s(?P<YEAR>[\d]{4})\s(?P<HOUR>\d+):(?P<MIN2>\d+)))
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
    re_Player = re.compile(u"""(?P<RANK>[\d]+):\s(?P<NAME>[^,\r\n]{2,15})(,\s(?P<CURRENCY>[%(LS)s])?(?P<WINNINGS>[%(NUM)s]+)(\s(?P<CURRENCY1>FTP|T\$|Play\sChips))?)?(,\s(?P<TICKET>Step\s(?P<LEVEL>\d)\sTicket))?""" % substitutions)
    re_Finished = re.compile(u"""(?P<NAME>[^,\r\n]{2,15}) finished in (?P<RANK>[\d]+)\S\S place""")
    #19-Aug-2013 15:32
    re_HeroXLS = re.compile(r'Player\sTournament\sReport\sfor\s(?P<NAME>.*?)\s\(.*\)') 
    re_DateTimeXLS = re.compile("(?P<D>[0-9]{2})\-(?P<M>\w+)\-(?P<Y>[0-9]{4})\s(?P<H>[0-9]+):(?P<MIN>[0-9]+)")
    re_GameXLS = re.compile(u"""(?P<GAME>Hold\'?em|Irish|Courchevel\sHi|Razz|RAZZ|5(-|\s)Card\sStud(\sHi)?|7(\sCard)?\sStud|7(\sCard)?\sStud\sHi/Lo|Stud\sH/L|Stud\sHi|Omaha|((5|6)\sCard\s)?Omaha\sHi|Omaha\sHi/Lo|Omaha\sH/L|2\-7\sSingle\sDraw|Badugi|Triple\sDraw\s2\-7\sLowball|2\-7\sTriple\sDraw|5\sCard\sDraw|\d+\-Game(\sMixed)?|HORSE|HA|HEROS|HO|HOE|HORSE|HOSE|OA|OE|SE)
                                (\-(?P<LIMIT>NL|PL|Fixed))?
                             """,re.VERBOSE|re.MULTILINE|re.DOTALL)
    re_BuyInXLS = re.compile("(?P<CURRENCY1>[%(LS)s])?(?P<BUYIN>[%(NUM)s]+)(\s(?P<CURRENCY2>(FTP|T\$|Play\sChips)))?(\s\+\s[%(LS)s]?(?P<FEE>[%(NUM)s]+)(\sFTP|\sT\$|\sPlay\sChips)?)?" % substitutions)
    re_WinningsXLS = re.compile("(?P<CURRENCY1>[%(LS)s])?(?P<WINNINGS>[%(NUM)s]+)(\s?(?P<CURRENCY2>(FTP|T\$|Play\sChips)))?" % substitutions)
    
    codepage = ["utf-16", "cp1252", "utf-8"]

    @staticmethod
    def getSplitRe(self, head):
        re_SplitTourneys = re.compile("^Full Tilt Poker Tournament Summary")
        self.hhtype = "summary"
        return re_SplitTourneys
    
    def parseSummary(self):
        if self.hhtype == "summary":
            self.parseSummaryFile()
        elif self.hhtype == "xls":
            self.parseSummaryXLS()
        else:
            raise FpdbParseError(_("parseSummary FAIL"))
        
    def parseSummaryXLS(self):
        info = self.summaryText[0]
        m = self.re_HeroXLS.search(info['header'])
        if m==None:
            tmp1 = info['header']
            tmp2 = str(info)[0:200]
            log.error(_("FullTiltPokerSummary.parseSummaryXLS: '%s' '%s") % (tmp1, tmp2))
            raise FpdbParseError
        info.update(m.groupdict())
        if 'SNG' in info:
            self.isSng = True
        if 'tournament key' in info:
            self.tourNo = int(float(info['tournament key']))
        if 'tournament name' in info: 
            self.tourneyName = info['tournament name']
            self.readTourneyName(self.tourneyName)
        if 'tournament start datetime' in info: 
            m1 = self.re_DateTimeXLS.finditer(info['tournament start datetime'])
            datetimestr = "2000/01/01 12:00:00"  # default used if time not found
            for a in m1:
                month = self.months[a.group('M')]
                datetimestr = "%s/%s/%s %s:%s:%s" % (a.group('Y'),month,a.group('D'),a.group('H'),a.group('MIN'),'0')
            self.startTime = datetime.datetime.strptime(datetimestr, "%Y/%m/%d %H:%M:%S") # also timezone at end, e.g. " ET"
            self.startTime = HandHistoryConverter.changeTimezone(self.startTime, "ET", "UTC")
        if 'tournament end datetime' in info:
            m2 = self.re_DateTimeXLS.finditer(info['tournament end datetime'])
            datetimestr = "2000/01/01 12:00:00"  # default used if time not found
            for a in m2:
                month = self.months[a.group('M')]
                datetimestr = "%s/%s/%s %s:%s:%s" % (a.group('Y'),month,a.group('D'),a.group('H'),a.group('MIN'),'0')
            self.endTime = datetime.datetime.strptime(datetimestr, "%Y/%m/%d %H:%M:%S") # also timezone at end, e.g. " ET"
            self.endTime = HandHistoryConverter.changeTimezone(self.endTime, "ET", "UTC")
        if 'game type desc' in info:
            m3 = self.re_GameXLS.search(info['game type desc'])
            if m3:
                base, self.gametype['category']  = self.games[m3.group('GAME')]
                if m3.group('LIMIT') != None:
                    self.gametype['limitType'] = self.limits[m3.group('LIMIT')]
                elif base=='mixed':
                    self.gametype['limitType'] = 'mx'
                else:
                    self.gametype['limitType'] = 'nl'
            else:
                log.error(_("FullTiltPokerSummary.parseSummaryXLS Game '%s' not found") % info['game type desc'])
                raise FpdbParseError
        if 'buy in amount' in info:
            m4 = self.re_BuyInXLS.search(info['buy in amount'])
            if m4:
                if m4.group('BUYIN')!=None:
                    self.buyin = int(100*Decimal(self.clearMoneyString(m4.group('BUYIN'))))
                if m4.group('FEE')!=None:
                    self.fee   = int(100*Decimal(self.clearMoneyString(m4.group('FEE'))))
                self.buyinCurrency = self.setCurrency(m4, self.buyinCurrency)
                self.currency = self.buyinCurrency
                if self.buyin ==0: self.buyinCurrency="FREE"
        if 'addons' in info and info['addons']:
            self.isAddOn   = True
            self.addOnCost = self.buyin
        if 'rebuys' in info and info['rebuys']:
            self.isRebuy   = True
            self.rebuyCost = self.buyin
        
        koAmt, entryId = 0, 1
        for entry in self.summaryText:
            if info.get('NAME')!=None and entry.get('position'): 
                name = info['NAME']
                rank = int(Decimal(entry['position']))
                winnings = 0
                entryId += 1

                if 'payout amount' in entry and entry['payout amount']:
                    m5 = self.re_WinningsXLS.search(entry['payout amount'])
                    if m5:
                        winnings = int(100*Decimal(self.clearMoneyString(m5.group('WINNINGS'))))
                        self.currency = self.setCurrency(m5, self.currency)
                    
                if self.isAddOn:
                    addOnAmt = 0
                    m6 = self.re_WinningsXLS.finditer(entry['addons'])
                    for a6 in m6:
                        addOnAmt += int(100*Decimal(self.clearMoneyString(a6.group('WINNINGS'))))
                    addOnCount = addOnAmt/self.addOnCost
                else:
                    addOnCount = None
                    
                if self.isRebuy:
                    rebuyAmt = 0
                    m7 = self.re_WinningsXLS.finditer(entry['rebuys'])
                    for a7 in m7:
                        rebuyAmt += int(100*Decimal(self.clearMoneyString(a7.group('WINNINGS'))))
                    rebuyCount = rebuyAmt/self.rebuyCost
                else:
                    rebuyCount = None
                    
                if 'total bounty amount' in entry and entry['total bounty amount']:
                    m8 = self.re_WinningsXLS.search(entry['total bounty amount'])
                    if m8:
                        self.koBounty += int(100*Decimal(self.clearMoneyString(m8.group('WINNINGS'))))
                        self.currency = self.setCurrency(m8, self.currency)
                    
                if 'pro bounty amount' in entry and entry['pro bounty amount']:
                    m9 = self.re_WinningsXLS.search(entry['pro bounty amount'])
                    if m9:
                        self.koBounty += int(100*Decimal(self.clearMoneyString(m9.group('WINNINGS'))))
                        self.currency = self.setCurrency(m9, self.currency)
                        
                if self.koBounty and not self.isKO:
                    self.isKO = True
                    koCount = 1
                else:
                    koCount = None
                      
                self.addPlayer(rank, name, winnings, self.currency, rebuyCount, addOnCount, koCount, entryId)            

    def parseSummaryFile(self):
        m = self.re_TourneyInfo.search(self.summaryText[:2000])
        if m == None:
            tmp = self.summaryText[0:200]
            log.error(_("FullTiltPokerSummary.parseSummary: '%s'") % tmp)
            raise FpdbParseError

        #print "DEBUG: m.groupdict(): %s" % m.groupdict()
        base = None
        rebuyCounts = {}
        addOnCounts = {}
        koCounts = {}
        mg = m.groupdict()
        if 'TOURNO'    in mg: self.tourNo = mg['TOURNO']
        if 'GAME'      in mg: 
            base, self.gametype['category'] = self.games[mg['GAME']]
        if 'LIMIT'     in mg and mg['LIMIT'] != None:
            self.gametype['limitType'] = self.limits[mg['LIMIT']]
        elif base=='mixed':
            self.gametype['limitType'] = 'mx'
        else:
            self.gametype['limitType'] = 'nl'
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
        if 'PBOUNTIES' in mg and mg['PBOUNTIES'] != None and mg['PBOUNTIES'][0]!='%':
            koCounts[mg['PNAMEBOUNTIES']] = int(mg['PBOUNTIES'])
        if 'SATELLITE' in mg and mg['SATELLITE'] != None:
            self.isSatellite = True
        
        entryId = 1
        if mg['TOURNAMENT'] != None:
            self.tourneyName = mg['TOURNAMENT']
            if mg['TOURPAREN'] != None:
                self.tourneyName += ' ' + mg['TOURPAREN']
            entryId = self.readTourneyName(mg['TOURNAMENT'], mg['MATCHNO'])
            
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
        elif mg['CURRENCY'] == "T$":  self.buyinCurrency="USD"
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
                rebuyCount = None
                addOnCount = None
                koCount = None
    
                if 'WINNINGS' in mg and mg['WINNINGS'] != None:
                    winnings = int(100*Decimal(self.clearMoneyString(mg['WINNINGS'])))
                    if 'CURRENCY' in mg and mg['CURRENCY'] != None:
                        if mg['CURRENCY'] == "$":     self.currency="USD"
                        elif mg['CURRENCY'] == u"€":  self.currency="EUR"
                    elif 'CURRENCY1' in mg and mg['CURRENCY1'] != None:
                        if mg['CURRENCY1'] == "FPP": self.currency="FTFP"
                        elif mg['CURRENCY1'] == "FTP": self.currency="FTFP"
                        elif mg['CURRENCY1'] == "T$": self.currency="USD"
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
                    winnings = int(step_values[mg['LEVEL']])
                    
                self.addPlayer(rank, name, winnings, self.currency, rebuyCount, addOnCount, koCount, entryId)
    
                playercount += 1


        # Some files dont contain the normals lines, and only contain the line
        # <PLAYER> finished in XXXXrd place
        if playercount == 0:
            m = self.re_Finished.finditer(self.summaryText)
            for a in m:
                winnings = 0
                name = a.group('NAME')
                rank = int(a.group('RANK'))
                self.addPlayer(rank, name, winnings, self.currency, None, None, None)
                
    def setCurrency(self, m, currency=None):
        if m.group('CURRENCY1') == "$":     currency="USD"
        elif m.group('CURRENCY1') == u"€":  currency="EUR"
        elif m.group('CURRENCY2') == "FPP": currency="FTFP"
        elif m.group('CURRENCY2') == "FTP": currency="FTFP"
        elif m.group('CURRENCY2') == "T$":  currency="USD"
        elif m.group('CURRENCY2') == 'Play Chips': currency="play"
        return currency        
    
    def readTourneyName(self, tourneyName, matchNo=None):
        entryId = 1
        n = self.re_TourneyExtraInfo.search(tourneyName)
        if n.group('SNG') is not None:
            self.isSng = True
        if "Rush" in tourneyName:
            self.isFast = True
        if "On Demand" in tourneyName:
            self.isOnDemand = True
        if n.group('SPECIAL') is not None :
            special = n.group('SPECIAL')
            if special == "Rebuy":
                self.isRebuy = True
            elif special == "KO":
                self.isKO = True
            elif re.search("Matrix", special):
                self.isMatrix = True
                if matchNo != None:
                    entryId = int(matchNo)
                else:
                    entryId = 5
            elif special == "Shootout":
                self.isShootout = True
            elif special in ('Heads Up', 'Heads-Up', 'Head\'s Up'):
                self.maxseats = 2
        if n.group('SPEED1') is not None :
            if n.group('SPEED1')=='Super Turbo':
                self.speed = 'Hyper'
            else:
                self.speed = n.group('SPEED1')
        if n.group('SPEED2') is not None :
            if n.group('SPEED2')=='Super Turbo':
                self.speed = 'Hyper'
            else:
                self.speed = n.group('SPEED2')
        if n.group('GUARANTEE')!=None:
            self.isGuarantee = True
        if self.isGuarantee and n.group('BUYINGUAR')!=None:
            self.guaranteeAmt = int(100*Decimal(self.clearMoneyString(n.group('BUYINGUAR'))))
        if n.group('STEP')!=None:
            self.isStep = True
        if n.group('STEPNO')!=None:
            self.stepNo = int(n.group('STEPNO'))
        if self.isMatrix and self.entries > 0:
            self.buyin = self.prizepool / self.entries
            buyinfee = int(100*Decimal(self.clearMoneyString(n.group('BUYINGUAR'))))
            self.fee = buyinfee - self.buyin
            self.isSng = True
        return entryId
