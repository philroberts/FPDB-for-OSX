#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Copyright 2008-2011, Carl Gherardi
#    
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#    
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#    
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
########################################################################

import L10n
_ = L10n.get_translation()

from HandHistoryConverter import *
#import TourneySummary

# Fulltilt HH Format converter

class Fulltilt(HandHistoryConverter):
    
    sitename = "Fulltilt"
    filetype = "text"
    codepage = ["utf-16", "utf-8", "cp1252"]
    siteId   = 1 # Needs to match id entry in Sites database

    substitutions = {
                     'LEGAL_ISO' : "USD|EUR|GBP|CAD|FPP",       # legal ISO currency codes
                            'LS' : u"\$|\u20AC|\xe2\x82\xac|",  # legal currency symbols - Euro(cp1252, utf-8)
                           'NUM' : u".,\dKMB",                     # legal characters in number format
                    }

    Lim_Blinds = {  '0.04': ('0.01', '0.02'),    '0.10': ('0.02', '0.05'),     '0.20': ('0.05', '0.10'),
                        '0.40': ('0.10', '0.20'),    '0.50': ('0.10', '0.25'),
                        '1.00': ('0.25', '0.50'),       '1': ('0.25', '0.50'),
                        '2.00': ('0.50', '1.00'),       '2': ('0.50', '1.00'),
                        '4.00': ('1.00', '2.00'),       '4': ('1.00', '2.00'),
                        '5.00': ('1.25', '2.50'),       '5': ('1.25', '2.50'),
                        '6.00': ('1.50', '3.00'),       '6': ('1.50', '3.00'),
                        '8.00': ('2.00', '4.00'),       '8': ('2.00', '4.00'),
                       '10.00': ('2.50', '5.00'),      '10': ('2.50', '5.00'),
                       '16.00': ('4.00', '8.00'),      '16': ('4.00', '8.00'),
                       '20.00': ('5.00', '10.00'),     '20': ('5.00', '10.00'),
                       '24.00': ('6.00', '12.00'),     '24': ('6.00', '12.00'),
                       '30.00': ('10.00', '15.00'),    '30': ('10.00', '15.00'),
                       '40.00': ('10.00', '20.00'),    '40': ('10.00', '20.00'),
                       '50.00': ('8.00',  '25.00'),     '50': ('8.00',  '25.00'),
                       '60.00': ('15.00', '30.00'),    '60': ('15.00', '30.00'),
                       '80.00': ('20.00', '40.00'),    '80': ('20.00', '40.00'),
                      '100.00': ('25.00', '50.00'),   '100': ('25.00', '50.00'),
                      '120.00': ('30.00', '60.00'),   '120': ('30.00', '60.00'),
                      '200.00': ('50.00', '100.00'),  '200': ('50.00', '100.00'),
                      '300.00': ('75.00', '150.00'),  '300': ('75.00', '150.00'),
                      '400.00': ('100.00', '200.00'), '400': ('100.00', '200.00'),
                      '500.00': ('125.00', '250.00'), '500': ('125.00', '250.00'),
                      '600.00': ('150.00', '300.00'), '600': ('150.00', '300.00'),
                      '800.00': ('200.00', '400.00'), '800': ('200.00', '400.00'),
                     '1000.00': ('250.00', '500.00'),'1000': ('250.00', '500.00'),
                     '2000.00': ('500.00', '750.00'),'2000': ('500.00', '1000.00'),
                     '3000.00': ('750.00', '1500.00'),'3000': ('750.00', '1500.00'),
                     '4000.00': ('1000.00','2000.00'),'4000': ('1000.00', '2000.00'),
                     '6000.00': ('1500.00','3000.00'),'6000': ('1500.00', '3000.00'),
                  }
    
    SnG_Fee = {  50: {'Hyper': 5, 'Turbo': 6, 'Normal': 7},
                100: {'Hyper': 8, 'Turbo': 10, 'Normal': 12},
                225: {'Hyper': 15, 'Turbo': 20, 'Normal': 25},
                500: {'Hyper': 25, 'Turbo': 35, 'Normal': 45},
                1000: {'Hyper': 45, 'Turbo': 68, 'Normal': 80},
                2000: {'Hyper': 85, 'Turbo': 135, 'Normal': 155},
                3500: {'Hyper': 130, 'Turbo': 225, 'Normal': 260},
                6000: {'Hyper': 215, 'Turbo': 375, 'Normal': 445},
                11500: {'Hyper': 375, 'Turbo': 650, 'Normal': 800},
                21500: {'Hyper': 600, 'Turbo': 1200, 'Normal': 1400},
                37500: {'Hyper': 900, 'Turbo': 2000, 'Normal': 2300},
                63500: {'Hyper': 1400, 'Turbo': 2800, 'Normal': 3100},
                100000: {'Hyper': 2000, 'Turbo': 4000, 'Normal': 4700}
              }
    
    HUSnG_Fee = {50: {'Hyper': 3, 'Turbo': 4, 'Normal': 5},
                100: {'Hyper': 5, 'Turbo': 7, 'Normal': 8},
                225: {'Hyper': 10, 'Turbo': 13, 'Normal': 15},
                500: {'Hyper': 14, 'Turbo': 20, 'Normal': 23},
                1000: {'Hyper': 24, 'Turbo': 38, 'Normal': 45},
                2000: {'Hyper': 40, 'Turbo': 75, 'Normal': 89},
                3500: {'Hyper': 67, 'Turbo': 125, 'Normal': 150},
                6000: {'Hyper': 110, 'Turbo': 210, 'Normal': 250},
                11500: {'Hyper': 205, 'Turbo': 375, 'Normal': 450},
                20000: {'Hyper': 325, 'Turbo': 600, 'Normal': 700},
                35000: {'Hyper': 475, 'Turbo': 900, 'Normal': 1000},
                60000: {'Hyper': 700, 'Turbo': 1400, 'Normal': 1600},
                100000: {'Hyper': 1000, 'Turbo': 2000, 'Normal': 2400},
                200000: {'Turbo': 3000, 'Normal': 4000},
                500000: {'Turbo': 5500, 'Normal': 7000}
                }
    
    Rush_Tables = ('Mach 10', 'Lightning', 'Velociraptor', 'Supercharger', 'Adrenaline',
                    'Afterburner', 'Mercury', 'Apollo', 'Warp Speed', 'Speeding Bullet',
                    'Flash', 'Bazinga', 'Lickety Split', 'Electro', 'Celerity', 'Alacrity',
                    'Dart',  'Accelerator', 'Sonic Boom', 'Vroom', 'Hermes', 'Thunderbolt',
                    'Swiftly Tilting', 'Rapido', 'Veyron', )

    # Static regexes
    re_GameInfo     = re.compile(u'''\#(?P<HID>[0-9]+):\s
                                    (?:(?P<TOURNAMENT>.+)\s\((?P<TOURNO>\d+)\),\s)?
                                    .+?
                                    \s-\s(?P<STAKES1>(?P<CURRENCY1>[%(LS)s]|)?(?P<SB1>[%(NUM)s]+)/[%(LS)s]?(?P<BB1>[%(NUM)s]+)\s(Ante\s\$?(?P<ANTE1>[%(NUM)s]+)\s)?-\s)?
                                    (?P<CAP>([%(LS)s]?[%(NUM)s]+\s)?(Cap\s|CAP\s)?)
                                    (?P<LIMIT>(No\sLimit|Pot\sLimit|Limit|NL|PL|FL))\s
                                    (?P<GAME>(Hold\'em|((5|6)\sCard\s)?Omaha(\sH/L|\sHi/Lo|\sHi|)|Irish|Courchevel\sHi|5(-|\s)Card\sStud(\sHi)?|7\sCard\sStud|7\sCard\sStud|Stud\sH/L|Razz|Stud\sHi|2-7\sTriple\sDraw|5\sCard\sDraw|Badugi|2-7\sSingle\sDraw|A-5\sTriple\sDraw))\s
                                    (?P<STAKES2>-\s(?P<CURRENCY2>[%(LS)s]|)?(?P<SB2>[%(NUM)s]+)/[%(LS)s]?(?P<BB2>[%(NUM)s]+)\s(Ante\s\$?(?P<ANTE2>[%(NUM)s]+)\s)?)?-\s
                                 ''' % substitutions, re.VERBOSE)
    re_Identify     = re.compile(u'FullTiltPoker|Full\sTilt\sPoker\sGame\s#\d+:')
    re_SplitHands   = re.compile(r"\n\n\n+")
    re_TailSplitHands   = re.compile(r"(\n\n+)")
    re_HandInfo     = re.compile(u'''\#(?P<HID>[0-9]+):\s
                                    (?:(?P<TOURNAMENT>.+?)\s(\((?P<TOURPAREN>.+)\)\s+)?\((?P<TOURNO>\d+)\),\s)?
                                    ((Table|Match)\s)?
                                    ((?P<PLAY>Play\sChip\s|PC)?
                                    (?P<TABLE>.+?)(\s|,)
                                    (?P<ENTRYID>\sEntry\s\#\d+\s)?)
                                    (\((?P<TABLEATTRIBUTES>.+)\)\s)?-\s
                                    (?P<STAKES1>[%(LS)s]?(?P<SB1>[%(NUM)s]+)/[%(LS)s]?(?P<BB1>[%(NUM)s]+)\s(Ante\s[%(LS)s]?(?P<ANTE1>[%(NUM)s]+)\s)?-\s)?
                                    (?P<CAP>([%(LS)s]?[%(NUM)s]+\s)?(Cap\s|CAP\s)?)
                                    (?P<GAMETYPE>[-\da-zA-Z\/\'\s]+)\s
                                    (?P<STAKES2>-\s[%(LS)s]?(?P<SB2>[%(NUM)s]+)/[%(LS)s]?(?P<BB2>[%(NUM)s]+)\s(Ante\s[%(LS)s]?(?P<ANTE2>[%(NUM)s]+)\s)?)?-\s
                                    (?P<DATETIME>.+$)
                                    (?P<PARTIAL>\(partial\))?\s
                                 ''' % substitutions, re.MULTILINE|re.VERBOSE)
    re_Cancelled = re.compile("Hand\s\#[0-9]+\shas\sbeen\scanceled?")
    re_TourneyExtraInfo  = re.compile('''(((?P<SPEED1>(Turbo|Super\sTurbo|Escalator))\s?)?
                                         ((?P<CURRENCY>[%(LS)s])?(?P<BUYINGUAR>[%(NUM)s]+)?(\s*\+\s*[%(LS)s]?(?P<FEE>[%(NUM)s]+))?\s?)?
                                         ((?P<SPEED2>(Turbo|Super\sTurbo|Escalator))\s?)?
                                         ((?P<SPECIAL>(Play\sMoney|Freeroll|KO|Knockout|Heads\sUp|Heads\-Up|Head\'s\sUp|Matrix|Rebuy|Madness|Rush))\s?)?
                                         ((?P<SHOOTOUT>Shootout)\s?)?
                                         ((?P<SNG>Sit\s&\sGo)\s?)?
                                         ((?P<STEP>Step\s(?P<STEPNO>\d))\s?)?
                                         ((?P<GUARANTEE>Guar(antee)?))?)
                                    ''' % substitutions, re.MULTILINE|re.VERBOSE)
    re_Button       = re.compile('^The button is in seat #(?P<BUTTON>\d+)', re.MULTILINE)
    re_PlayerInfo   = re.compile('Seat (?P<SEAT>[0-9]+): (?P<PNAME>.{2,15}) \([%(LS)s]?(?P<CASH>[%(NUM)s]+)\)(?P<SITOUT>, is sitting out)?$' % substitutions, re.MULTILINE)
    re_SummarySitout = re.compile('Seat (?P<SEAT>[0-9]+): (?P<PNAME>.{2,15}?) (\(button\) )?is sitting out?$' % substitutions, re.MULTILINE)
    re_Board        = re.compile(r"\[(?P<CARDS>.+)\]")
    re_Mixed        = re.compile(r'\s\-\s(?P<MIXED>\d+\-Game|HA|HEROS|HO|HOE|HORSE|HOSE|OA|OE|SE)\s\-\s', re.VERBOSE)
    re_Max          = re.compile("(?P<MAX>\d+)( max|handed)?", re.MULTILINE)
    re_HeadsUp      = re.compile("heads up", re.MULTILINE)
    re_buyinType    = re.compile("(?P<BUYINTYPE>deep|shallow)", re.MULTILINE)
    re_EntryNo      = re.compile("(Entry\s(?P<ENTRYNO>\d+))", re.MULTILINE)
    re_Speed        = re.compile("(?P<SPEED>(Turbo|Super\sTurbo|Escalator))", re.MULTILINE)
    re_Chance       = re.compile("((?P<CHANCE>\d)x\sChance)", re.MULTILINE)
    # NB: if we ever match "Full Tilt Poker" we should also match "FullTiltPoker", which PT Stud erroneously exports.
    re_DateTime     = re.compile("""((?P<H>[0-9]+):(?P<MIN>[0-9]+):(?P<S>[0-9]+)\s(?P<TZ>\w+)\s-\s(?P<Y>[0-9]{4})\/(?P<M>[0-9]{2})\/(?P<D>[0-9]{2})|(?P<H2>[0-9]+):(?P<MIN2>[0-9]+)\s(?P<TZ2>\w+)\s-\s\w+\,\s(?P<M2>\w+)\s(?P<D2>\d+)\,\s(?P<Y2>[0-9]{4}))(?P<PARTIAL>\s\(partial\))?""", re.MULTILINE)

    def compilePlayerRegexs(self,  hand):
        players = set([player[1] for player in hand.players])
        if not players <= self.compiledPlayers: # x <= y means 'x is subset of y'
            # we need to recompile the player regexs.
            self.compiledPlayers = players
            player_re = "(?P<PNAME>" + "|".join(map(re.escape, players)) + ")"
            self.substitutions['PLAYERS'] = player_re

            #log.debug("player_re: " + player_re)
            self.re_PostSB           = re.compile(r"^%(PLAYERS)s posts the small blind of [%(LS)s]?(?P<SB>[%(NUM)s]+)" % self.substitutions, re.MULTILINE)
            self.re_PostDead         = re.compile(r"^%(PLAYERS)s posts a dead small blind of [%(LS)s]?(?P<SB>[%(NUM)s]+)" % self.substitutions, re.MULTILINE)
            self.re_PostBB           = re.compile(r"^%(PLAYERS)s posts (the big blind of )?[%(LS)s]?(?P<BB>[%(NUM)s]+)" % self.substitutions, re.MULTILINE)
            self.re_Antes            = re.compile(r"^%(PLAYERS)s antes [%(LS)s]?(?P<ANTE>[%(NUM)s]+)" % self.substitutions, re.MULTILINE)
            self.re_ReturnsAnte      = re.compile(r"^Ante of [%(LS)s]?[%(NUM)s]+ returned to %(PLAYERS)s" % self.substitutions, re.MULTILINE)
            self.re_BringIn          = re.compile(r"^%(PLAYERS)s brings in for [%(LS)s]?(?P<BRINGIN>[%(NUM)s]+)" % self.substitutions, re.MULTILINE)
            self.re_PostBoth         = re.compile(r"^%(PLAYERS)s posts small \& big blinds \[[%(LS)s]? (?P<SBBB>[%(NUM)s]+)" % self.substitutions, re.MULTILINE)
            self.re_HeroCards        = re.compile(r"^Dealt to %s(?: \[(?P<OLDCARDS>.+?)\])?( \[(?P<NEWCARDS>.+?)\])" % player_re, re.MULTILINE)
            self.re_Action           = re.compile(r"^%(PLAYERS)s(?P<ATYPE> bets| checks| raises to| completes it to| calls| folds| discards| stands pat)( [%(LS)s]?(?P<BET>[%(NUM)s]+))?( on| cards?)?( \[(?P<CARDS>.+?)\])?" % self.substitutions, re.MULTILINE)
            self.re_ShowdownAction   = re.compile(r"^%s shows \[(?P<CARDS>.*)\]" % player_re, re.MULTILINE)
            self.re_CollectPot       = re.compile(r"^Seat (?P<SEAT>[0-9]+): %(PLAYERS)s (\(button\) |\(small blind\) |\(big blind\) )?(collected|showed \[.*\] and won) \([%(LS)s]?(?P<POT>[%(NUM)s]+)\)(, mucked| with.*)?" % self.substitutions, re.MULTILINE)
            self.re_CollectPot2      = re.compile(r"^%(PLAYERS)s (ties for|wins) (the (main |side )?pot|pot (1|2)) \([%(LS)s]?(?P<POT>[%(NUM)s]+)\)" %  self.substitutions, re.MULTILINE)
            self.re_CollectSidePot   = re.compile(r"^Seat (?P<SEAT>[0-9]+): %(PLAYERS)s \s?(ties for|wins) (the (main |side )?pot|pot (1|2)) \([%(LS)s]?(?P<POT>[%(NUM)s]+)\)" %  self.substitutions, re.MULTILINE)
            self.re_SitsOut          = re.compile(r"^%s sits out" % player_re, re.MULTILINE)
            self.re_ShownCards       = re.compile(r"^Seat (?P<SEAT>[0-9]+): %s (\(button\) |\(small blind\) |\(big blind\) )?(?P<SHOWED>showed|mucked) \[(?P<CARDS>.*)\](( and won \(.*\) with | and lost with | \- )(?P<STRING>.*))?" % player_re, re.MULTILINE)

    def readSupportedGames(self):
        return [["ring", "hold", "nl"], 
                ["ring", "hold", "pl"],
                ["ring", "hold", "fl"],
                ["ring", "hold", "cn"],

                ["ring", "stud", "fl"],

                ["ring", "draw", "fl"],
                ["ring", "draw", "pl"],
                ["ring", "draw", "nl"],

                ["tour", "hold", "nl"],
                ["tour", "hold", "pl"],
                ["tour", "hold", "fl"],
                ["tour", "hold", "cn"],
                
                ["tour", "stud", "fl"],
                
                ["tour", "draw", "fl"],
                ["tour", "draw", "pl"],
                ["tour", "draw", "nl"],
        ]

    def determineGameType(self, handText):
        info = {'type':'ring'}
        
        m = self.re_GameInfo.search(handText)
        if not m:
            tmp = handText[0:200]
            log.error(_("FulltiltToFpdb.determineGameType: '%s'") % tmp)
            raise FpdbParseError
        mg = m.groupdict()

        # translations from captured groups to our info strings
        limits = { 'No Limit':'nl', 'Pot Limit':'pl', 'Limit':'fl', 'NL' : 'nl', 'PL' : 'pl', 'FL': 'fl'}
        games = {              # base, category
                  "Hold'em" : ('hold','holdem'), 
                 'Omaha Hi' : ('hold','omahahi'), 
                    'Omaha' : ('hold','omahahi'),
                'Omaha H/L' : ('hold','omahahilo'),
              'Omaha Hi/Lo' : ('hold','omahahilo'),
          '5 Card Omaha Hi' : ('hold', '5_omahahi'),
          '6 Card Omaha Hi' : ('hold', '6_omahahi'),
            'Courchevel Hi' : ('hold', 'cour_hi'),
                    'Irish' : ('hold','irish'), 
                     'Razz' : ('stud','razz'), 
              '7 Card Stud' : ('stud','studhi'),
                  'Stud Hi' : ('stud','studhi'),
        '7 Card Stud Hi/Lo' : ('stud','studhilo'),
                 'Stud H/L' : ('stud','studhilo'),
              '5 Card Stud' : ('stud', '5_studhi'),
           '5-Card Stud Hi' : ('stud', '5_studhi'),
          '2-7 Triple Draw' : ('draw','27_3draw'),
          'A-5 Triple Draw' : ('draw','a5_3draw'),
              '5 Card Draw' : ('draw','fivedraw'),
                   'Badugi' : ('draw','badugi'),
          '2-7 Single Draw' : ('draw','27_1draw'),
               }
        mixes = { 
                   '7-Game' : '7game',
                   '8-Game' : '8game',
                   '9-Game' : '9game',
                  '10-Game' : '10game',
                  '25-Game' : '25game',
                       'HA' : 'ha',
                    'HEROS' : 'heros',
                       'HO' : 'ho',
                      'HOE' : 'hoe',
                    'HORSE' : 'horse',
                     'HOSE' : 'hose',
                       'OA' : 'oa',
                       'OE' : 'oe',
                       'SE' : 'se'
            }
        currencies = { u'€':'EUR', '$':'USD', '':'T$' }
        
        if mg['STAKES1'] is not None:
            stakesId = '1'
        else:
            stakesId = '2'
            
        if 'SB%s' % stakesId in mg:
            info['sb'] = self.clearMoneyString(mg['SB%s' % stakesId])
        if 'BB%s' % stakesId in mg:
            info['bb'] = self.clearMoneyString(mg['BB%s' % stakesId])
        
        if mg['CURRENCY%s' % stakesId] is not None:
            info['currency'] = currencies[mg['CURRENCY%s' % stakesId]]

        if mg['TOURNO'] is None:  info['type'] = "ring"
        else:                     info['type'] = "tour"
        if mg['LIMIT'] is not None:
            info['limitType'] = limits[mg['LIMIT']]
        if mg['GAME'] is not None:
            (info['base'], info['category']) = games[mg['GAME']]
        # NB: SB, BB must be interpreted as blinds or bets depending on limit type.
        m = self.re_Mixed.search(self.in_path)
        if m: info['mix'] = mixes[m.groupdict()['MIXED']]
            
        if not mg['CURRENCY%s' % stakesId] and info['type']=='ring':
            info['currency'] = 'play'

        if info['limitType'] == 'fl' and info['bb'] is not None:
            if info['type'] == 'ring':
                try:
                    bb = self.clearMoneyString(info['bb'])
                    info['sb'] = self.Lim_Blinds[bb][0]
                    info['bb'] = self.Lim_Blinds[bb][1]
                except KeyError:
                    tmp = handText[0:200]
                    log.error(_("FulltiltToFpdb.determineGameType: Lim_Blinds has no lookup for '%s' - '%s'") % (bb, tmp))
                    raise FpdbParseError
            else:
                sb = self.clearMoneyString(info['sb'])
                info['sb'] = str((Decimal(sb)/2).quantize(Decimal("0.01")))
                info['bb'] = str(Decimal(sb).quantize(Decimal("0.01")))

        return info

    def readHandInfo(self, hand):
        m =  self.re_HandInfo.search(hand.handText)
        if m is None:
            tmp = hand.handText[0:200]
            log.error(_("FulltiltToFpdb.readHandInfo: '%s'") % tmp)
            raise FpdbParseError

        #print "DEBUG: m.groupdict: %s" % m.groupdict()
        hand.handid = m.group('HID')
        hand.tablename = m.group('TABLE')
        
        if hand.tablename in self.Rush_Tables:
            hand.isFast, hand.gametype['fast'] = True, True

        if m.group('DATETIME'):
            # This section of code should match either a single date (which is ET) or
            # the last date in the header, which is also recorded in ET.
            timezone = "ET"
            m1 = self.re_DateTime.finditer(m.group('DATETIME'))
            datetimestr = "2000/01/01 00:00:00"
            dateformat  = "%Y/%m/%d %H:%M:%S"
            for a in m1:
                if a.group('TZ2') == None:
                    datetimestr = "%s/%s/%s %s:%s:%s" % (a.group('Y'), a.group('M'),a.group('D'),a.group('H'),a.group('MIN'),a.group('S'))
                    timezone = a.group('TZ')
                else: # Short-lived date format
                    datetimestr = "%s/%s/%s %s:%s" % (a.group('Y2'), a.group('M2'),a.group('D2'),a.group('H2'),a.group('MIN2'))
                    timezone = a.group('TZ2')
                    dateformat = "%Y/%B/%d %H:%M"  
                if a.group('PARTIAL'):
                    raise FpdbHandPartial(hid=m.group('HID'))
            
            hand.startTime = datetime.datetime.strptime(datetimestr, dateformat)
            hand.startTime = HandHistoryConverter.changeTimezone(hand.startTime, timezone, "UTC")

        if m.group("PARTIAL"):
            # It would appear this can't be triggered as DATETIME is a bit greedy
            raise FpdbHandPartial(hid=m.group('HID'))
        
        if self.re_Cancelled.search(hand.handText):
            raise FpdbHandPartial(_("Hand '%s' was cancelled.") % m.group('HID'))
        
        if m.group('CAP'):
            hand.gametype['buyinType'] = 'cap'

        if m.group('TABLEATTRIBUTES'):
            # search for keywords "max" and "heads up"
            max_found = self.re_Max.search(m.group('TABLEATTRIBUTES'))
            if max_found:
                hand.maxseats = int(max_found.group('MAX'))
            elif self.re_HeadsUp.search(m.group('TABLEATTRIBUTES')):
                hand.maxseats = 2
            buyin_type = self.re_buyinType.search(m.group('TABLEATTRIBUTES'))
            if buyin_type:
                hand.gametype['buyinType'] = buyin_type.group('BUYINTYPE')
            if 'New to the Game' in m.group('TABLEATTRIBUTES'):
                (hand.isNewToGame, hand.gametype['newToGame']) = (True, True)
            # otherwise use some sensible defaults based on gametype
        if not hand.maxseats:
            if hand.gametype['base'] == 'stud':
                hand.maxseats = 8
            elif hand.gametype['base'] == 'draw':
                hand.maxseats = 6
            else:
                hand.maxseats = 9
        #print hand.maxseats

        hand.tourNo = m.group('TOURNO')
        if m.group('PLAY') is not None:
            hand.gametype['currency'] = 'play'
            
        # Done: if there's a way to figure these out, we should.. otherwise we have to stuff it with unknowns
        if m.group('TOURNAMENT') is not None:
            n = self.re_TourneyExtraInfo.search(m.group('TOURNAMENT'))
            turbo = None
            if n.group('SPEED1') is not None :
                turbo = n.group('SPEED1')
            elif n.group('SPEED2') is not None :
                turbo = n.group('SPEED2')
            if m.group('TOURPAREN') is not None:
                n1 = self.re_Speed.search(m.group('TOURPAREN'))
                if n1 is not None :
                    turbo = n1.group('SPEED')
                if 'Rush' == m.group('TOURPAREN'):
                    hand.isFast, hand.gametype['fast'] = True, True
                if 'Cashout' == m.group('TOURPAREN'):
                    hand.isCashOut = True
                chance_found = self.re_Chance.search(m.group('TOURPAREN'))
                if chance_found:
                    self.isChance = True
                    self.chanceCount = int(chance_found.group('CHANCE'))
            if turbo:
                if 'Sup' in turbo:
                    hand.speed = "Hyper"
                else:
                    hand.speed = turbo
            if n.group('SNG') is not None:
                hand.isSng = True
            if 'Rush' in m.group('TOURNAMENT'):
                hand.isFast, hand.gametype['fast'] = True, True
            if "On Demand" in m.group('TOURNAMENT'):
                hand.isOnDemand = True
            m1 = self.re_EntryNo.search(self.in_path)
            if m1: hand.entryId = int(m1.group('ENTRYNO'))
            
            hand.buyin = 0
            hand.fee=0
            hand.buyinCurrency="NA"  
            if (n.group('BUYINGUAR') is not None and n.group('FEE') is not None):
                if n.group('CURRENCY')=="$":
                    hand.buyinCurrency="USD"
                elif n.group('CURRENCY')==u"€":
                    hand.buyinCurrency="EUR"
                hand.buyin = int(100*Decimal(self.clearMoneyString(n.group('BUYINGUAR'))))
                hand.fee = int(100*Decimal(self.clearMoneyString(n.group('FEE'))))
            elif n.group('SPECIAL')=='Play Money':
                hand.buyinCurrency="play"
                hand.buyin = int(100*Decimal(self.clearMoneyString(n.group('BUYINGUAR'))))
                hand.fee = 0
            elif n.group('SPECIAL')=='Freeroll':
                hand.buyin = 0
                hand.fee=0
                hand.buyinCurrency="FREE"  
            elif (n.group('BUYINGUAR') is not None and hand.isSng):
                if n.group('CURRENCY')=="$":
                    hand.buyinCurrency="USD"
                elif n.group('CURRENCY')==u"€":
                    hand.buyinCurrency="EUR"
                buyinfee = int(100*Decimal(self.clearMoneyString(n.group('BUYINGUAR'))))
                if hand.maxseats==2 and buyinfee in self.HUSnG_Fee and self.HUSnG_Fee[buyinfee].get(hand.speed) is not None:
                    hand.fee = self.HUSnG_Fee[buyinfee][hand.speed]
                    hand.buyin = buyinfee - hand.fee
                if hand.maxseats!=2 and buyinfee in self.SnG_Fee and self.SnG_Fee[buyinfee].get(hand.speed) is not None:
                    hand.fee = self.SnG_Fee[buyinfee][hand.speed]
                    hand.buyin = buyinfee - hand.fee
                 
            if n.group('SPECIAL') is not None :
                special = n.group('SPECIAL')
                if special == "Rebuy":
                    hand.isRebuy = True
                if special == "KO":
                    hand.isKO = True
                if special in ("Head's Up", "Heads-Up", "Heads Up"):
                    hand.maxseats = 2
                if re.search("Matrix", special):
                    hand.isMatrix, hand.isSng = True, True
                    hand.entryId = int(hand.tablename)
                if special == "Shootout":
                    hand.isShootout = True
            
            if n.group('GUARANTEE')!=None:
                hand.isGuarantee = True
            if hand.isGuarantee and n.group('BUYINGUAR')!=None:
                hand.guaranteeAmt = int(100*Decimal(self.clearMoneyString(n.group('BUYINGUAR'))))
            if n.group('STEP')!=None:
                hand.isStep = True
            if n.group('STEPNO')!=None:
                hand.stepNo = int(n.group('STEPNO'))

    def readPlayerStacks(self, hand):
        # Split hand text for FTP, as the regex matches the player names incorrectly
        # in the summary section
        handsplit = hand.handText.split('*** SUMMARY ***')
        if len(handsplit)!=2:
            raise FpdbHandPartial(_("Hand is not cleanly split into pre and post Summary %s.") % hand.handid)
        pre, post = handsplit
        m = self.re_PlayerInfo.finditer(pre)
        plist = {}

        # Get list of players in header.
        for a in m:
            plist[a.group('PNAME')] = [int(a.group('SEAT')), a.group('CASH'), False]

            n = self.re_SummarySitout.finditer(post)
            for b in n:
                if b.group('PNAME') in plist:
                    if hand.gametype['type'] == "ring" :
                        # Remove any listed as sitting out in the summary as start of hand info unreliable
                        #print "DEBUG: Deleting '%s' from player dict" %(b.group('PNAME'))
                        del plist[b.group('PNAME')]
                    else:
                        plist[b.group('PNAME')][2] = True

        # Add remaining players
        for a in plist:
            seat, stack, sitout = plist[a]
            hand.addPlayer(seat, a, stack, None, sitout)

        if plist == {}:
            #No players! The hand is either missing stacks or everyone is sitting out
            raise FpdbHandPartial(_("No players detected in hand %s.") % hand.handid)


    def markStreets(self, hand):

        if hand.gametype['base'] == 'hold':
            m =  re.search(r"\*\*\* HOLE CARDS \*\*\*(?P<PREFLOP>(.+\*\*\* FLOPET \*\*\* (?P<FLOPET>\[\S\S\]))?.+(?=\*\*\* FLOP (1\s)?\*\*\*)|.+)"
                       r"(\*\*\* FLOP \*\*\*(?P<FLOP> \[\S\S \S\S( \S\S)?\].+(?=\*\*\* TURN (1\s)?\*\*\*)|.+))?"
                       r"(\*\*\* TURN \*\*\* \[\S\S \S\S \S\S] (?P<TURN>\[\S\S\].+(?=\*\*\* RIVER (1\s)?\*\*\*)|.+))?"
                       r"(\*\*\* RIVER \*\*\* \[\S\S \S\S \S\S \S\S] (?P<RIVER>\[\S\S\].+))?"
                       r"(\*\*\* FLOP 1 \*\*\*(?P<FLOP1> \[\S\S \S\S( \S\S)\].+(?=\*\*\* TURN 1 \*\*\*)|.+))?"
                       r"(\*\*\* TURN 1 \*\*\* \[\S\S \S\S \S\S] (?P<TURN1>\[\S\S\].+(?=\*\*\* RIVER 1 \*\*\*)|.+))?"
                       r"(\*\*\* RIVER 1 \*\*\* \[\S\S \S\S \S\S \S\S] (?P<RIVER1>\[\S\S\].+?(?=\*\*\* (FLOP|TURN|RIVER) 2 \*\*\*)))?"
                       r"(\*\*\* FLOP 2 \*\*\*(?P<FLOP2> \[\S\S \S\S( \S\S)?\].+(?=\*\*\* TURN 2 \*\*\*)|.+))?"
                       r"(\*\*\* TURN 2 \*\*\* \[\S\S \S\S \S\S] (?P<TURN2>\[\S\S\].+(?=\*\*\* RIVER 2 \*\*\*)|.+))?"
                       r"(\*\*\* RIVER 2 \*\*\* \[\S\S \S\S \S\S \S\S] (?P<RIVER2>\[\S\S\].+))?", hand.handText,re.DOTALL)
        elif hand.gametype['base'] == "stud":
            if hand.gametype['category'] != '5_studhi':
                m =  re.search(r"(?P<ANTES>.+(?=\*\*\* 3RD STREET \*\*\*)|.+)"
                               r"(\*\*\* 3RD STREET \*\*\*(?P<THIRD>.+(?=\*\*\* 4TH STREET \*\*\*)|.+))?"
                               r"(\*\*\* 4TH STREET \*\*\*(?P<FOURTH>.+(?=\*\*\* 5TH STREET \*\*\*)|.+))?"
                               r"(\*\*\* 5TH STREET \*\*\*(?P<FIFTH>.+(?=\*\*\* 6TH STREET \*\*\*)|.+))?"
                               r"(\*\*\* 6TH STREET \*\*\*(?P<SIXTH>.+(?=\*\*\* 7TH STREET \*\*\*)|.+))?"
                               r"(\*\*\* 7TH STREET \*\*\*(?P<SEVENTH>.+))?", hand.handText,re.DOTALL)
            else:
                m =  re.search(r"(?P<ANTES>.+(?=\*\*\* 2ND STREET \*\*\*)|.+)"
                               r"(\*\*\* 2ND STREET \*\*\*(?P<SECOND>.+(?=\*\*\* 3RD STREET \*\*\*)|.+))?"
                               r"(\*\*\* 3RD STREET \*\*\*(?P<THIRD>.+(?=\*\*\* 4TH STREET \*\*\*)|.+))?"
                               r"(\*\*\* 4TH STREET \*\*\*(?P<FOURTH>.+(?=\*\*\* 5TH STREET \*\*\*)|.+))?"
                               r"(\*\*\* 5TH STREET \*\*\*(?P<FIFTH>.+))?", hand.handText,re.DOTALL)
        elif hand.gametype['base'] in ("draw"):
            m =  re.search(r"(?P<PREDEAL>.+(?=\*\*\* HOLE CARDS \*\*\*)|.+)"
                           r"(\*\*\* HOLE CARDS \*\*\*(?P<DEAL>.+(?=(\*\*\* FIRST DRAW \*\*\*|\*\*\* DRAW \*\*\*))|.+))?"
                           r"((\*\*\* FIRST DRAW \*\*\*|\*\*\* DRAW \*\*\*)(?P<DRAWONE>.+(?=\*\*\* SECOND DRAW \*\*\*)|.+))?"
                           r"(\*\*\* SECOND DRAW \*\*\*(?P<DRAWTWO>.+(?=\*\*\* THIRD DRAW \*\*\*)|.+))?"
                           r"(\*\*\* THIRD DRAW \*\*\*(?P<DRAWTHREE>.+))?", hand.handText,re.DOTALL)

        hand.addStreets(m)

    def readCommunityCards(self, hand, street):
        if street in ('FLOPET','FLOP','TURN','RIVER'):
            #print "DEBUG readCommunityCards:", street, hand.streets[street]
            m = self.re_Board.search(hand.streets[street])
            hand.setCommunityCards(street, m.group('CARDS').split(' '))
        if street in ('FLOP1', 'TURN1', 'RIVER1', 'FLOP2', 'TURN2', 'RIVER2'):
            m = self.re_Board.search(hand.streets[street])
            hand.setCommunityCards(street, m.group('CARDS').split(' '))
            hand.runItTimes = 2

    def readBlinds(self, hand):
        try:
            m = self.re_PostSB.search(hand.handText)
            hand.addBlind(m.group('PNAME'), 'small blind', self.clearMoneyString(m.group('SB')))
        except: # no small blind
            hand.addBlind(None, None, None)
        for a in self.re_PostDead.finditer(hand.handText):
            hand.addBlind(a.group('PNAME'), 'secondsb', self.clearMoneyString(a.group('SB')))
        for a in self.re_PostBB.finditer(hand.handText):
            hand.addBlind(a.group('PNAME'), 'big blind', self.clearMoneyString(a.group('BB')))
        for a in self.re_PostBoth.finditer(hand.handText):
            hand.addBlind(a.group('PNAME'), 'both', self.clearMoneyString(a.group('SBBB')))

    def readAntes(self, hand):
        #log.debug(_("reading antes"))
        slist = []
        n = self.re_ReturnsAnte.finditer(hand.handText)
        for player in n:
            #If a player has their ante returned, then they timed out and are actually sitting out
            slist.append(player.group('PNAME'))
        m = self.re_Antes.finditer(hand.handText)
        for player in m:
            #log.debug("hand.addAnte(%s,%s)" %(player.group('PNAME'), player.group('ANTE')))
            if player.group('PNAME') not in slist:
                hand.addAnte(player.group('PNAME'), self.clearMoneyString(player.group('ANTE')))

    def readBringIn(self, hand):
        m = self.re_BringIn.search(hand.handText,re.DOTALL)
        if m:
            #log.debug(_("Player bringing in: %s for %s") %(m.group('PNAME'),  m.group('BRINGIN')))
            hand.addBringIn(m.group('PNAME'),  self.clearMoneyString(m.group('BRINGIN')))
        #else:
            #log.debug(_("No bringin found, handid =%s") % hand.handid)

    def readButton(self, hand):
        try:
            hand.buttonpos = int(self.re_Button.search(hand.handText).group('BUTTON'))
        except AttributeError, e:
            # FTP has no indication that a hand is cancelled.
            raise FpdbHandPartial(_("%s Failed to detect button (hand #%s cancelled?)") % ("readButton:", hand.handid))

    def readHoleCards(self, hand):
#    streets PREFLOP, PREDRAW, and THIRD are special cases beacause
#    we need to grab hero's cards
        for street in ('PREFLOP', 'DEAL'):
            if street in hand.streets.keys():
                m = self.re_HeroCards.finditer(hand.streets[street])
                for found in m:
#                    if m == None:
#                        hand.involved = False
#                    else:
                    hand.hero = found.group('PNAME')
                    newcards = found.group('NEWCARDS').split(' ')
                    hand.addHoleCards(street, hand.hero, closed=newcards, shown=False, mucked=False, dealt=True)

        for street, text in hand.streets.iteritems():
            if not text or street in ('PREFLOP', 'DEAL'): continue  # already done these
            m = self.re_HeroCards.finditer(hand.streets[street])
            for found in m:
                player = found.group('PNAME')
                if found.group('NEWCARDS') is None:
                    newcards = []
                else:
                    newcards = found.group('NEWCARDS').split(' ')
                if found.group('OLDCARDS') is None:
                    oldcards = []
                else:
                    oldcards = found.group('OLDCARDS').split(' ')
                    
                if ((hand.gametype['category'] == '5_studhi' and street == 'SECOND' and len(oldcards) == 1) or 
                     hand.gametype['category'] != '5_studhi' and street == 'THIRD' and len(oldcards) == 2): # hero in stud game
                    hand.hero = player
                    hand.dealt.add(player) # need this for stud??
                    hand.addHoleCards(street, player, closed=oldcards, open=newcards, shown=False, mucked=False, dealt=False)
                else:
                    hand.addHoleCards(street, player, open=newcards, closed=oldcards, shown=False, mucked=False, dealt=False)


    def readAction(self, hand, street):
        m = self.re_Action.finditer(hand.streets[street])
        for action in m:
            if action.group('ATYPE') == ' folds':
                hand.addFold( street, action.group('PNAME'))
            elif action.group('ATYPE') == ' checks':
                hand.addCheck( street, action.group('PNAME'))
            elif action.group('ATYPE') == ' calls':
                hand.addCall( street, action.group('PNAME'), action.group('BET') )
            elif action.group('ATYPE') == ' raises to':
                hand.addRaiseTo( street, action.group('PNAME'), action.group('BET') )
            elif action.group('ATYPE') == ' bets':
                hand.addBet( street, action.group('PNAME'), action.group('BET') )
            elif action.group('ATYPE') == ' discards':
                discarded = action.group('BET')
                if hand.gametype['category'] == 'irish':
                    street, discarded = 'TURN', '2'
                hand.addDiscard(street, action.group('PNAME'), discarded, action.group('CARDS'))
            elif action.group('ATYPE') == ' completes it to':
                hand.addComplete( street, action.group('PNAME'), action.group('BET') )
            elif action.group('ATYPE') == ' stands pat':
                hand.addStandsPat( street, action.group('PNAME'), action.group('CARDS'))
            else:
                print (_("DEBUG:") + " " + _("Unimplemented %s: '%s' '%s'") % ("readAction", action.group('PNAME'), action.group('ATYPE')))


    def readShowdownActions(self, hand):
        for shows in self.re_ShowdownAction.finditer(hand.handText):
            cards = shows.group('CARDS')
            cards = cards.split(' ')
            hand.addShownCards(cards, shows.group('PNAME'))

    def readCollectPot(self,hand):
        awardFound = False
        for m in self.re_CollectPot.finditer(hand.handText):
            hand.addCollectPot(player=m.group('PNAME'),pot=re.sub(u',',u'',m.group('POT')))
            awardFound = True
        for m in self.re_CollectSidePot.finditer(hand.handText):
            hand.addCollectPot(player=m.group('PNAME'),pot=re.sub(u',',u'',m.group('POT')))
            awardFound = True
        if not awardFound:
            for m in self.re_CollectPot2.finditer(hand.handText):
                 hand.addCollectPot(player=m.group('PNAME'),pot=re.sub(u',',u'',m.group('POT')))

    def readShownCards(self,hand):
        for m in self.re_ShownCards.finditer(hand.handText):
            if m.group('CARDS') is not None:
                cards = m.group('CARDS')
                cards = cards.split(' ') # needs to be a list, not a set--stud needs the order
                string = m.group('STRING')

                (shown, mucked) = (False, False)
                if m.group('SHOWED') == "showed": shown = True
                elif m.group('SHOWED') == "mucked": mucked = True

                #print "DEBUG: hand.addShownCards(%s, %s, %s, %s)" %(cards, m.group('PNAME'), shown, mucked)
                hand.addShownCards(cards=cards, player=m.group('PNAME'), shown=shown, mucked=mucked, string=string)
                
    @staticmethod
    def getTableTitleRe(type, table_name=None, tournament = None, table_number=None):
        "Returns string to search in windows titles"
        if type=="tour":
            regex = "Tournament " + re.escape(str(tournament)) + "( - Entry \d+)?, Table " + re.escape(str(table_number))
        else:
            regex = re.escape(str(table_name))
        log.info("Fulltilt.getTableTitleRe: table_name='%s' tournament='%s' table_number='%s'" % (table_name, tournament, table_number))
        log.info("Fulltilt.getTableTitleRe: returns: '%s'" % (regex))
        return regex
        
