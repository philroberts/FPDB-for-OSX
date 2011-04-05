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

import logging
from HandHistoryConverter import *
#import TourneySummary

# Fulltilt HH Format converter

class Fulltilt(HandHistoryConverter):
    
    sitename = "Fulltilt"
    filetype = "text"
    codepage = ["utf-16", "cp1252", "utf-8"]
    siteId   = 1 # Needs to match id entry in Sites database

    substitutions = {
                     'LEGAL_ISO' : "USD|EUR|GBP|CAD|FPP",       # legal ISO currency codes
                            'LS' : u"\$|\u20AC|\xe2\x82\xac|",  # legal currency symbols - Euro(cp1252, utf-8)
                           'TAB' : u"-\u2013'\s\da-zA-Z#_",     # legal characters for tablename
                           'NUM' : u".,\d",                     # legal characters in number format
                    }

    Lim_Blinds = {  '0.04': ('0.01', '0.02'),    '0.10': ('0.02', '0.05'),     '0.20': ('0.05', '0.10'),
                        '0.40': ('0.10', '0.20'),    '0.50': ('0.10', '0.25'),
                        '1.00': ('0.25', '0.50'),       '1': ('0.25', '0.50'),
                        '2.00': ('0.50', '1.00'),       '2': ('0.50', '1.00'),
                        '4.00': ('1.00', '2.00'),       '4': ('1.00', '2.00'),
                        '6.00': ('1.00', '3.00'),       '6': ('1.00', '3.00'),
                        '8.00': ('2.00', '4.00'),       '8': ('2.00', '4.00'),
                       '10.00': ('2.00', '5.00'),      '10': ('2.00', '5.00'),
                       '16.00': ('4.00', '8.00'),      '16': ('4.00', '8.00'),
                       '20.00': ('5.00', '10.00'),     '20': ('5.00', '10.00'),
                       '30.00': ('10.00', '15.00'),    '30': ('10.00', '15.00'),
                       '40.00': ('10.00', '20.00'),    '40': ('10.00', '20.00'),
                       '60.00': ('15.00', '30.00'),    '60': ('15.00', '30.00'),
                       '80.00': ('20.00', '40.00'),    '80': ('20.00', '40.00'),
                      '100.00': ('25.00', '50.00'),   '100': ('25.00', '50.00'),
                      '200.00': ('50.00', '100.00'),  '200': ('50.00', '100.00'),
                      '300.00': ('75.00', '150.00'),  '300': ('75.00', '150.00'),
                      '400.00': ('100.00', '200.00'), '400': ('100.00', '200.00'),
                      '500.00': ('125.00', '250.00'), '500': ('125.00', '250.00'),
                      '800.00': ('200.00', '400.00'), '800': ('200.00', '400.00'),
                     '1000.00': ('250.00', '500.00'),'1000': ('250.00', '500.00'),
                     '2000.00': ('500.00', '750.00'),'2000': ('500.00', '1000.00'),
                     '3000.00': ('750.00', '1500.00'),'3000': ('750.00', '1500.00'),
                  }

    # Static regexes
    re_GameInfo     = re.compile(u'''.*\#(?P<HID>[0-9]+):\s
                                    (?:(?P<TOURNAMENT>.+)\s\((?P<TOURNO>\d+)\),\s)?
                                    .+
                                    -\s(?P<CURRENCY>[%(LS)s]|)?
                                    (?P<SB>[%(NUM)s]+)/
                                    [%(LS)s]?(?P<BB>[%(NUM)s]+)\s
                                    (Ante\s\$?(?P<ANTE>[%(NUM)s]+)\s)?-\s
                                    [%(LS)s]?(?P<CAP>[%(NUM)s]+\sCap\s)?
                                    (?P<LIMIT>(No\sLimit|Pot\sLimit|Limit))?\s
                                    (?P<GAME>(Hold\'em|Omaha(\sH/L|\sHi/Lo|\sHi|)|7\sCard\sStud|Stud\sH/L|Razz|Stud\sHi|2-7\sTriple\sDraw|5\sCard\sDraw|Badugi|2-7\sSingle\sDraw))
                                 ''' % substitutions, re.VERBOSE)
    re_SplitHands   = re.compile(r"\n\n\n+")
    re_TailSplitHands   = re.compile(r"(\n\n+)")
    re_HandInfo     = re.compile(u'''.*\#(?P<HID>[0-9]+):\s
                                    (?:(?P<TOURNAMENT>.+)\s\((?P<TOURNO>\d+)\),\s)?
                                    ((Table|Match)\s)?
                                    (?P<PLAY>Play\sChip\s|PC)?
                                    ((?P<TABLE>[%(TAB)s]+)(\s|,))
                                    (?P<ENTRYID>\sEntry\s\#\d+\s)?
                                    (\((?P<TABLEATTRIBUTES>.+)\)\s)?-\s
                                    [%(LS)s]?(?P<SB>[%(NUM)s]+)/[%(LS)s]?(?P<BB>[%(NUM)s]+)\s(Ante\s[%(LS)s]?(?P<ANTE>[.0-9]+)\s)?-\s
                                    [%(LS)s]?(?P<CAP>[.0-9]+\sCap\s)?
                                    (?P<GAMETYPE>[-\da-zA-Z\/\'\s]+)\s-\s
                                    (?P<DATETIME>.*$)
                                    (?P<PARTIAL>\(partial\))?\s
                                    (?:.*?\n(?P<CANCELLED>Hand\s\#(?P=HID)\shas\sbeen\scanceled))?
                                 ''' % substitutions, re.MULTILINE|re.VERBOSE)
    re_TourneyExtraInfo  = re.compile('''(((?P<TOURNEY_NAME>[^$]+)?
                                         (?P<CURRENCY>[%(LS)s])?(?P<BUYIN>[.0-9]+)?\s*\+\s*[%(LS)s]?(?P<FEE>[.0-9]+)?
                                         (\s(?P<SPECIAL>(KO|Heads\sUp|Matrix\s\dx|Rebuy|Madness)))?
                                         (\s(?P<SHOOTOUT>Shootout))?
                                         (\s(?P<SNG>Sit\s&\sGo))?
                                         (\s\((?P<TURBO>Turbo)\))?)|(?P<UNREADABLE_INFO>.+))
                                    ''' % substitutions, re.VERBOSE)
    re_Button       = re.compile('^The button is in seat #(?P<BUTTON>\d+)', re.MULTILINE)
    re_PlayerInfo   = re.compile('Seat (?P<SEAT>[0-9]+): (?P<PNAME>.{2,15}) \([%(LS)s]?(?P<CASH>[%(NUM)s]+)\)(?P<SITOUT>, is sitting out)?$' % substitutions, re.MULTILINE)
    re_SummarySitout = re.compile('Seat (?P<SEAT>[0-9]+): (?P<PNAME>.{2,15}?) (\(button\) )?is sitting out?$' % substitutions, re.MULTILINE)
    re_Board        = re.compile(r"\[(?P<CARDS>.+)\]")

    #static regex for tourney purpose
    re_TourneyInfo  = re.compile('''Tournament\sSummary\s
                                    (?P<TOURNAMENT_NAME>[^$(]+)?\s*
                                    ((?P<CURRENCY>[%(LS)s]|)?(?P<BUYIN>[.0-9]+)\s*\+\s*[%(LS)s]?(?P<FEE>[.0-9]+)\s)?
                                    ((?P<SPECIAL>(KO|Heads\sUp|Matrix\s\dx|Rebuy|Madness))\s)?
                                    ((?P<SHOOTOUT>Shootout)\s)?
                                    ((?P<SNG>Sit\s&\sGo)\s)?
                                    (\((?P<TURBO1>Turbo)\)\s)?
                                    \((?P<TOURNO>\d+)\)\s
                                    ((?P<MATCHNO>Match\s\d)\s)?
                                    (?P<GAME>(Hold\'em|Omaha(\sHi/Lo|\sH/L|\sHi|)|7\sCard\sStud|Stud\sH/L|Razz|Stud\sHi))\s
                                    (\((?P<TURBO2>Turbo)\)\s)?
                                    (?P<LIMIT>(No\sLimit|Pot\sLimit|Limit))?
                                ''' % substitutions, re.VERBOSE)
    re_TourneyBuyInFee      = re.compile("Buy-In: (?P<BUYIN_CURRENCY>[%(LS)s]|)?(?P<BUYIN>[.0-9]+) \+ [%(LS)s]?(?P<FEE>[.0-9]+)" % substitutions)
    re_TourneyBuyInChips    = re.compile("Buy-In Chips: (?P<BUYINCHIPS>\d+)")
    re_TourneyEntries       = re.compile("(?P<ENTRIES>\d+) Entries")
    re_TourneyPrizePool     = re.compile("Total Prize Pool: (?P<PRIZEPOOL_CURRENCY>[%(LS)s]|)?(?P<PRIZEPOOL>[.,0-9]+)" % substitutions)
    re_TourneyRebuyCost     = re.compile("Rebuy: (?P<REBUY_CURRENCY>[%(LS)s]|)?(?P<REBUY_COST>[.,0-9]+)"% substitutions)
    re_TourneyAddOnCost     = re.compile("Add-On: (?P<ADDON_CURRENCY>[%(LS)s]|)?(?P<ADDON_COST>[.,0-9]+)"% substitutions)
    re_TourneyRebuyCount    = re.compile("performed (?P<REBUY_COUNT>\d+) Rebuy")
    re_TourneyAddOnCount    = re.compile("performed (?P<ADDON_COUNT>\d+) Add-On")
    re_TourneyRebuysTotal   = re.compile("Total Rebuys: (?P<REBUY_TOTAL>\d+)")
    re_TourneyAddOnsTotal   = re.compile("Total Add-Ons: (?P<ADDONS_TOTAL>\d+)")
    re_TourneyRebuyChips    = re.compile("Rebuy Chips: (?P<REBUY_CHIPS>\d+)")
    re_TourneyAddOnChips    = re.compile("Add-On Chips: (?P<ADDON_CHIPS>\d+)")
    re_TourneyKOBounty      = re.compile("Knockout Bounty: (?P<KO_BOUNTY_CURRENCY>[%(LS)s]|)?(?P<KO_BOUNTY_AMOUNT>[.,0-9]+)" % substitutions)
    re_TourneyKoCount       = re.compile("received (?P<COUNT_KO>\d+) Knockout Bounty Award(s)?")
    re_TourneyTimeInfo      = re.compile("Tournament started: (?P<STARTTIME>.*)\nTournament ((?P<IN_PROGRESS>is still in progress)?|(finished:(?P<ENDTIME>.*))?)$")

    re_TourneysPlayersSummary = re.compile("^(?P<RANK>(Still Playing|\d+))( - |: )(?P<PNAME>[^\n,]+)(, )?(?P<WINNING_CURRENCY>[%(LS)s]|)?(?P<WINNING>[.\d]+)?" % substitutions, re.MULTILINE)
    re_TourneyHeroFinishingP = re.compile("(?P<HERO_NAME>.*) finished in (?P<HERO_FINISHING_POS>\d+)(st|nd|rd|th) place")

#TODO: See if we need to deal with play money tourney summaries -- Not right now (they shouldn't pass the re_TourneyInfo)
##Full Tilt Poker Tournament Summary 250 Play Money Sit & Go (102909471) Hold'em No Limit
##Buy-In: 250 Play Chips + 0 Play Chips
##Buy-In Chips: 1500
##6 Entries
##Total Prize Pool: 1,500 Play Chips

# These regexes are for FTP only
    re_Mixed        = re.compile(r'\s\-\s(?P<MIXED>HA|HORSE|HOSE)\s\-\s', re.VERBOSE)
    re_Max          = re.compile("(?P<MAX>\d+)( max)?", re.MULTILINE)
    # NB: if we ever match "Full Tilt Poker" we should also match "FullTiltPoker", which PT Stud erroneously exports.
    re_DateTime     = re.compile("""((?P<H>[0-9]+):(?P<MIN>[0-9]+):(?P<S>[0-9]+)\s(?P<TZ>\w+)\s-\s(?P<Y>[0-9]{4})\/(?P<M>[0-9]{2})\/(?P<D>[0-9]{2})|(?P<H2>[0-9]+):(?P<MIN2>[0-9]+)\s(?P<TZ2>\w+)\s-\s\w+\,\s(?P<M2>\w+)\s(?P<D2>\d+)\,\s(?P<Y2>[0-9]{4}))(?P<PARTIAL>\s\(partial\))?""", re.MULTILINE)




    mixes = { 'HORSE': 'horse', '7-Game': '7game', 'HOSE': 'hose', 'HA': 'ha'}


    def compilePlayerRegexs(self,  hand):
        players = set([player[1] for player in hand.players])
        if not players <= self.compiledPlayers: # x <= y means 'x is subset of y'
            # we need to recompile the player regexs.
            self.compiledPlayers = players
            player_re = "(?P<PNAME>" + "|".join(map(re.escape, players)) + ")"
            self.substitutions['PLAYERS'] = player_re

            logging.debug("player_re: " + player_re)
            self.re_PostSB           = re.compile(r"^%(PLAYERS)s posts the small blind of [%(LS)s]?(?P<SB>[%(NUM)s]+)" % self.substitutions, re.MULTILINE)
            self.re_PostDead         = re.compile(r"^%(PLAYERS)s posts a dead small blind of [%(LS)s]?(?P<SB>[%(NUM)s]+)" % self.substitutions, re.MULTILINE)
            self.re_PostBB           = re.compile(r"^%(PLAYERS)s posts (the big blind of )?[%(LS)s]?(?P<BB>[%(NUM)s]+)" % self.substitutions, re.MULTILINE)
            self.re_Antes            = re.compile(r"^%(PLAYERS)s antes [%(LS)s]?(?P<ANTE>[%(NUM)s]+)" % self.substitutions, re.MULTILINE)
            self.re_BringIn          = re.compile(r"^%(PLAYERS)s brings in for [%(LS)s]?(?P<BRINGIN>[%(NUM)s]+)" % self.substitutions, re.MULTILINE)
            self.re_PostBoth         = re.compile(r"^%(PLAYERS)s posts small \& big blinds \[[%(LS)s]? (?P<SBBB>[%(NUM)s]+)" % self.substitutions, re.MULTILINE)
            self.re_HeroCards        = re.compile(r"^Dealt to %s(?: \[(?P<OLDCARDS>.+?)\])?( \[(?P<NEWCARDS>.+?)\])" % player_re, re.MULTILINE)
            self.re_Action           = re.compile(r"^%(PLAYERS)s(?P<ATYPE> bets| checks| raises to| completes it to| calls| folds| discards| stands pat)( [%(LS)s]?(?P<BET>[%(NUM)s]+))?(\son|\scards?)?(\s\[(?P<CARDS>.+?)\])?" % self.substitutions, re.MULTILINE)
            self.re_ShowdownAction   = re.compile(r"^%s shows \[(?P<CARDS>.*)\]" % player_re, re.MULTILINE)
            self.re_CollectPot       = re.compile(r"^Seat (?P<SEAT>[0-9]+): %(PLAYERS)s (\(button\) |\(small blind\) |\(big blind\) )?(collected|showed \[.*\] and won) \([%(LS)s]?(?P<POT>[%(NUM)s]+)\)(, mucked| with.*)?" % self.substitutions, re.MULTILINE)
            self.re_SitsOut          = re.compile(r"^%s sits out" % player_re, re.MULTILINE)
            self.re_ShownCards       = re.compile(r"^Seat (?P<SEAT>[0-9]+): %s (\(button\) |\(small blind\) |\(big blind\) )?(?P<ACT>showed|mucked) \[(?P<CARDS>.*)\].*" % player_re, re.MULTILINE)

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

                ["tour", "stud", "fl"],
               ]

    def determineGameType(self, handText):
        info = {'type':'ring'}
        
        m = self.re_GameInfo.search(handText)
        if not m:
            tmp = handText[0:100]
            log.error(_("Unable to recognise gametype from: '%s'") % tmp)
            log.error("determineGameType: " + _("Raising FpdbParseError for file '%s'") % self.in_path)
            raise FpdbParseError(_("Unable to recognise gametype from: '%s'") % tmp)
        mg = m.groupdict()

        # translations from captured groups to our info strings
        limits = { 'No Limit':'nl', 'Pot Limit':'pl', 'Limit':'fl' }
        games = {              # base, category
                  "Hold'em" : ('hold','holdem'), 
                 'Omaha Hi' : ('hold','omahahi'), 
                    'Omaha' : ('hold','omahahi'),
                'Omaha H/L' : ('hold','omahahilo'),
              'Omaha Hi/Lo' : ('hold','omahahilo'),
                     'Razz' : ('stud','razz'), 
                  'Stud Hi' : ('stud','studhi'), 
                 'Stud H/L' : ('stud','studhilo'),
          '2-7 Triple Draw' : ('draw','27_3draw'),
              '5 Card Draw' : ('draw','fivedraw'),
                   'Badugi' : ('draw','badugi'),
          '2-7 Single Draw' : ('draw','27_1draw')
               }
        currencies = { u'€':'EUR', '$':'USD', '':'T$' }

        if 'SB' in mg:
            info['sb'] = self.clearMoneyString(mg['SB'])

        if 'BB' in mg:
            info['bb'] = self.clearMoneyString(mg['BB'])

        if mg['TOURNO'] is None:  info['type'] = "ring"
        else:                     info['type'] = "tour"

        if mg['CAP']:
            info['limitType'] = 'cn'
        else:
            info['limitType'] = limits[mg['LIMIT']]

        if info['limitType'] == 'fl' and info['bb'] is not None and info['type'] == 'ring':
            try:
                bb = self.clearMoneyString(mg['BB'])
                info['sb'] = self.Lim_Blinds[bb][0]
                info['bb'] = self.Lim_Blinds[bb][1]
            except KeyError:
                log.error(_("Lim_Blinds has no lookup for '%s'") % mg['BB'])
                log.error("determineGameType: " + _("Raising FpdbParseError"))
                raise FpdbParseError(_("Lim_Blinds has no lookup for '%s'") % mg['BB'])

        if mg['GAME'] is not None:
            (info['base'], info['category']) = games[mg['GAME']]
        if mg['CURRENCY'] is not None:
            info['currency'] = currencies[mg['CURRENCY']]
        # NB: SB, BB must be interpreted as blinds or bets depending on limit type.
        return info

    def readHandInfo(self, hand):
        m =  self.re_HandInfo.search(hand.handText)
        if m is None:
            tmp = hand.handText[0:100]
            log.error(_("Unable to recognise handinfo from: '%s'") % tmp)
            log.error("readHandInfo: " + _("Raising FpdbParseError"))
            raise FpdbParseError(_("Unable to recognise handinfo from: '%s'"))

        #print "DEBUG: m.groupdict: %s" % m.groupdict()
        hand.handid = m.group('HID')
        hand.tablename = m.group('TABLE')

        if m.group('DATETIME'):
            # This section of code should match either a single date (which is ET) or
            # the last date in the header, which is also recorded in ET.
            timezone = "ET"
            m1 = self.re_DateTime.finditer(m.group('DATETIME'))
            datetimestr = "2000/01/01 00:00:00"
            for a in m1:
                if a.group('TZ2') == None:
                    datetimestr = "%s/%s/%s %s:%s:%s" % (a.group('Y'), a.group('M'),a.group('D'),a.group('H'),a.group('MIN'),a.group('S'))
                    timezone = a.group('TZ')
                    hand.startTime = datetime.datetime.strptime(datetimestr, "%Y/%m/%d %H:%M:%S")
                else: # Short-lived date format
                    datetimestr = "%s/%s/%s %s:%s" % (a.group('Y2'), a.group('M2'),a.group('D2'),a.group('H2'),a.group('MIN2'))
                    timezone = a.group('TZ2')
                    hand.startTime = datetime.datetime.strptime(datetimestr, "%Y/%B/%d %H:%M")
                if a.group('PARTIAL'):
                    raise FpdbParseError(hid=m.group('HID'))

            hand.startTime = HandHistoryConverter.changeTimezone(hand.startTime, timezone, "UTC")

        if m.group("CANCELLED") or m.group("PARTIAL"):
            # It would appear this can't be triggered as DATETIME is a bit greedy
            raise FpdbParseError(hid=m.group('HID'))

        if m.group('TABLEATTRIBUTES'):
            m2 = self.re_Max.search(m.group('TABLEATTRIBUTES'))
            if m2: hand.maxseats = int(m2.group('MAX'))

        hand.tourNo = m.group('TOURNO')
        if m.group('PLAY') is not None:
            hand.gametype['currency'] = 'play'
            
        # Done: if there's a way to figure these out, we should.. otherwise we have to stuff it with unknowns
        if m.group('TOURNAMENT') is not None:
            n = self.re_TourneyExtraInfo.search(m.group('TOURNAMENT'))
            if n.group('UNREADABLE_INFO') is not None:
                hand.tourneyComment = n.group('UNREADABLE_INFO') 
            else:
                hand.tourneyComment = n.group('TOURNEY_NAME')   # can be None
                if (n.group('CURRENCY') is not None and n.group('BUYIN') is not None and n.group('FEE') is not None):
                    if n.group('CURRENCY')=="$":
                        hand.buyinCurrency="USD"
                    elif n.group('CURRENCY')==u"€":
                        hand.buyinCurrency="EUR"
                    else:
                        hand.buyinCurrency="NA"
                    hand.buyin = int(100*Decimal(n.group('BUYIN')))
                    hand.fee = int(100*Decimal(n.group('FEE')))
                if n.group('TURBO') is not None :
                    hand.speed = "Turbo"
                if n.group('SPECIAL') is not None :
                    special = n.group('SPECIAL')
                    if special == "Rebuy":
                        hand.isRebuy = True
                    if special == "KO":
                        hand.isKO = True
                    if special == "Head's Up" or special == "Heads Up":
                        hand.maxseats = 2
                    if re.search("Matrix", special):
                        hand.isMatrix = True
                    if special == "Shootout":
                        hand.isShootout = True
            if hand.buyin is None:
                hand.buyin = 0
                hand.fee=0
                hand.buyinCurrency="NA"

        if hand.level is None:
            hand.level = "0"            

    def readPlayerStacks(self, hand):
        # Split hand text for FTP, as the regex matches the player names incorrectly
        # in the summary section
        pre, post = hand.handText.split('*** SUMMARY ***')
        m = self.re_PlayerInfo.finditer(pre)
        plist = {}

        # Get list of players in header.
        for a in m:
            plist[a.group('PNAME')] = [int(a.group('SEAT')), a.group('CASH')]

        if hand.gametype['type'] == "ring" :
            # Remove any listed as sitting out in the summary as start of hand info unreliable
            n = self.re_SummarySitout.finditer(post)
            for b in n:
                del plist[b.group('PNAME')]
                #print "DEBUG: Deleting '%s' from player dict" %(b.group('PNAME'))

        # Add remaining players
        for a in plist:
            seat, stack = plist[a]
            hand.addPlayer(seat, a, stack)

        if plist == {}:
            #No players! The hand is either missing stacks or everyone is sitting out
            raise FpdbParseError(_("readPlayerStacks: No players detected (hand #%s)") % hand.handid)


    def markStreets(self, hand):

        if hand.gametype['base'] == 'hold':
            m =  re.search(r"\*\*\* HOLE CARDS \*\*\*(?P<PREFLOP>.+(?=\*\*\* FLOP \*\*\*)|.+)"
                       r"(\*\*\* FLOP \*\*\*(?P<FLOP> \[\S\S \S\S \S\S\].+(?=\*\*\* TURN \*\*\*)|.+))?"
                       r"(\*\*\* TURN \*\*\* \[\S\S \S\S \S\S] (?P<TURN>\[\S\S\].+(?=\*\*\* RIVER \*\*\*)|.+))?"
                       r"(\*\*\* RIVER \*\*\* \[\S\S \S\S \S\S \S\S] (?P<RIVER>\[\S\S\].+))?", hand.handText,re.DOTALL)
        elif hand.gametype['base'] == "stud":
            m =  re.search(r"(?P<ANTES>.+(?=\*\*\* 3RD STREET \*\*\*)|.+)"
                           r"(\*\*\* 3RD STREET \*\*\*(?P<THIRD>.+(?=\*\*\* 4TH STREET \*\*\*)|.+))?"
                           r"(\*\*\* 4TH STREET \*\*\*(?P<FOURTH>.+(?=\*\*\* 5TH STREET \*\*\*)|.+))?"
                           r"(\*\*\* 5TH STREET \*\*\*(?P<FIFTH>.+(?=\*\*\* 6TH STREET \*\*\*)|.+))?"
                           r"(\*\*\* 6TH STREET \*\*\*(?P<SIXTH>.+(?=\*\*\* 7TH STREET \*\*\*)|.+))?"
                           r"(\*\*\* 7TH STREET \*\*\*(?P<SEVENTH>.+))?", hand.handText,re.DOTALL)
        elif hand.gametype['base'] in ("draw"):
            m =  re.search(r"(?P<PREDEAL>.+(?=\*\*\* HOLE CARDS \*\*\*)|.+)"
                           r"(\*\*\* HOLE CARDS \*\*\*(?P<DEAL>.+(?=(\*\*\* FIRST DRAW \*\*\*|\*\*\* DRAW \*\*\*))|.+))?"
                           r"((\*\*\* FIRST DRAW \*\*\*|\*\*\* DRAW \*\*\*)(?P<DRAWONE>.+(?=\*\*\* SECOND DRAW \*\*\*)|.+))?"
                           r"(\*\*\* SECOND DRAW \*\*\*(?P<DRAWTWO>.+(?=\*\*\* THIRD DRAW \*\*\*)|.+))?"
                           r"(\*\*\* THIRD DRAW \*\*\*(?P<DRAWTHREE>.+))?", hand.handText,re.DOTALL)

        hand.addStreets(m)

    def readCommunityCards(self, hand, street): # street has been matched by markStreets, so exists in this hand
        if street in ('FLOP','TURN','RIVER'):   # a list of streets which get dealt community cards (i.e. all but PREFLOP)
            #print "DEBUG readCommunityCards:", street, hand.streets.group(street)
            m = self.re_Board.search(hand.streets[street])
            hand.setCommunityCards(street, m.group('CARDS').split(' '))


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
            hand.addBlind(a.group('PNAME'), 'small & big blinds', self.clearMoneyString(a.group('SBBB')))

    def readAntes(self, hand):
        logging.debug(_("reading antes"))
        m = self.re_Antes.finditer(hand.handText)
        for player in m:
            logging.debug("hand.addAnte(%s,%s)" %(player.group('PNAME'), player.group('ANTE')))
#            if player.group() != 
            hand.addAnte(player.group('PNAME'), player.group('ANTE'))

    def readBringIn(self, hand):
        m = self.re_BringIn.search(hand.handText,re.DOTALL)
        if m:
            logging.debug(_("Player bringing in: %s for %s") %(m.group('PNAME'),  m.group('BRINGIN')))
            hand.addBringIn(m.group('PNAME'),  m.group('BRINGIN'))
        else:
            logging.debug(_("No bringin found, handid =%s") % hand.handid)

    def readButton(self, hand):
        try:
            hand.buttonpos = int(self.re_Button.search(hand.handText).group('BUTTON'))
        except AttributeError, e:
            # FTP has no indication that a hand is cancelled.
            raise FpdbParseError(_("readButton: Failed to detect button (hand #%s cancelled?)") % hand.handid)

    def readHeroCards(self, hand):
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

                if street == 'THIRD' and len(oldcards) == 2: # hero in stud game
                    hand.hero = player
                    hand.dealt.add(player) # need this for stud??
                    hand.addHoleCards(street, player, closed=oldcards, open=newcards, shown=False, mucked=False, dealt=False)
                else:
                    hand.addHoleCards(street, player, open=newcards, closed=oldcards, shown=False, mucked=False, dealt=False)


    def readAction(self, hand, street):
        m = self.re_Action.finditer(hand.streets[street])
        for action in m:
            if action.group('ATYPE') == ' raises to':
                hand.addRaiseTo( street, action.group('PNAME'), action.group('BET') )
            elif action.group('ATYPE') == ' completes it to':
                hand.addComplete( street, action.group('PNAME'), action.group('BET') )
            elif action.group('ATYPE') == ' calls':
                hand.addCall( street, action.group('PNAME'), action.group('BET') )
            elif action.group('ATYPE') == ' bets':
                hand.addBet( street, action.group('PNAME'), action.group('BET') )
            elif action.group('ATYPE') == ' folds':
                hand.addFold( street, action.group('PNAME'))
            elif action.group('ATYPE') == ' checks':
                hand.addCheck( street, action.group('PNAME'))
            elif action.group('ATYPE') == ' discards':
                hand.addDiscard(street, action.group('PNAME'), action.group('BET'), action.group('CARDS'))
            elif action.group('ATYPE') == ' stands pat':
                hand.addStandsPat( street, action.group('PNAME'), action.group('CARDS'))
            else:
                print (_("DEBUG: ") + " " + _("Unimplemented readAction: '%s' '%s'") % (action.group('PNAME'), action.group('ATYPE')))


    def readShowdownActions(self, hand):
        for shows in self.re_ShowdownAction.finditer(hand.handText):
            cards = shows.group('CARDS')
            cards = cards.split(' ')
            hand.addShownCards(cards, shows.group('PNAME'))

    def readCollectPot(self,hand):
        for m in self.re_CollectPot.finditer(hand.handText):
            hand.addCollectPot(player=m.group('PNAME'),pot=re.sub(u',',u'',m.group('POT')))

    def readShownCards(self,hand):
        for m in self.re_ShownCards.finditer(hand.handText):
            if m.group('CARDS') is not None:
                if m.group('ACT'):
                    hand.addShownCards(cards=m.group('CARDS').split(' '), player=m.group('PNAME'), shown = False, mucked = True)
                else:
                    hand.addShownCards(cards=m.group('CARDS').split(' '), player=m.group('PNAME'), shown = True, mucked = False)

    def guessMaxSeats(self, hand):
        """Return a guess at max_seats when not specified in HH."""
        mo = self.maxOccSeat(hand)

        if mo == 10: return 10 #that was easy

        if hand.gametype['base'] == 'stud':
            if mo <= 8: return 8
            else: return mo 

        if hand.gametype['base'] == 'draw':
            if mo <= 6: return 6
            else: return mo

        if mo == 2: return 2
        if mo <= 6: return 6
        return 9

    def readOther(self, hand):
        m = self.re_Mixed.search(self.in_path)
        if m is None:
            hand.mixed = None
        else:
            hand.mixed = self.mixes[m.groupdict()['MIXED']]

    def readSummaryInfo(self, summaryInfoList):
        self.status = True

        #m = re.search("Tournament Summary", summaryInfoList[0])
        #if m:
        #    # info list should be 2 lines : Tourney infos & Finsihing postions with winnings
        #    if (len(summaryInfoList) != 2 ):
        #        log.info("Too many or too few lines (%d) in file '%s' : '%s'" % (len(summaryInfoList), self.in_path, summaryInfoList) )
        #        self.status = False
        #    else:
        #        self.tourney = TourneySummary.TourneySummary(sitename = self.sitename, gametype = None, summaryText = summaryInfoList, builtFrom = "HHC")
        #        self.status = self.getPlayersPositionsAndWinnings(self.tourney)
        #        if self.status == True :
        #            self.status = self.determineTourneyType(self.tourney)
        #            #print self.tourney
        #        else:
        #            log.info("Parsing NOK : rejected")
        #else:
        #    log.info( "This is not a summary file : '%s'" % (self.in_path) )
        #    self.status = False

        return self.status

    def determineTourneyType(self, tourney):
        info = {'type':'tour'}
        tourneyText = tourney.summaryText[0]
        #print "Examine : '%s'" %(tourneyText)
        
        m = self.re_TourneyInfo.search(tourneyText)
        if not m: 
            log.info(_("determineTourneyType : Parsing NOK"))
            return False
        mg = m.groupdict()
        #print mg
        
        # translations from captured groups to our info strings
        limits = { 'No Limit':'nl', 'Pot Limit':'pl', 'Limit':'fl' }
        games = {              # base, category
                  "Hold'em" : ('hold','holdem'), 
                 'Omaha Hi' : ('hold','omahahi'), 
                'Omaha H/L' : ('hold','omahahilo'),
                     'Razz' : ('stud','razz'), 
                  'Stud Hi' : ('stud','studhi'), 
                 'Stud H/L' : ('stud','studhilo')
               }
        currencies = { u' €':'EUR', '$':'USD', '':'T$' }
        info['limitType'] = limits[mg['LIMIT']]
        if mg['GAME'] is not None:
            (info['base'], info['category']) = games[mg['GAME']]
        if mg['CURRENCY'] is not None:
            info['currency'] = currencies[mg['CURRENCY']]
        if mg['TOURNO'] is None:
            info['type'] = "ring"
        else:
            info['type'] = "tour"
        # NB: SB, BB must be interpreted as blinds or bets depending on limit type.

        # Info is now ready to be copied in the tourney object        
        tourney.gametype = info

        # Additional info can be stored in the tourney object
        if mg['BUYIN'] is not None:
            tourney.buyin = 100*Decimal(self.clearMoneyString(mg['BUYIN']))
            tourney.fee = 0 
        if mg['FEE'] is not None:
            tourney.fee = 100*Decimal(self.clearMoneyString(mg['FEE']))
        if mg['TOURNAMENT_NAME'] is not None:
            # Tournament Name can have a trailing space at the end (depending on the tournament description)
            tourney.tourneyName = mg['TOURNAMENT_NAME'].rstrip()
        if mg['SPECIAL'] is not None:
            special = mg['SPECIAL']
            if special == "KO":
                tourney.isKO = True
            if special == "Heads Up":
                tourney.maxseats = 2
            if re.search("Matrix", special):
                tourney.isMatrix = True
            if special == "Rebuy":
                tourney.isRebuy = True
            if special == "Madness":
                tourney.tourneyComment = "Madness"
        if mg['SHOOTOUT'] is not None:
            tourney.isShootout = True
        if mg['TURBO1'] is not None or mg['TURBO2'] is not None :
            tourney.speed = "Turbo"
        if mg['TOURNO'] is not None:
            tourney.tourNo = mg['TOURNO']
        else:
            log.info(_("Unable to get a valid Tournament ID -- File rejected"))
            return False
        if tourney.isMatrix:
            if mg['MATCHNO'] is not None:
                tourney.matrixMatchId = mg['MATCHNO']
            else:
                tourney.matrixMatchId = 0


        # Get BuyIn/Fee
        # Try and deal with the different cases that can occur :
        # - No buy-in/fee can be on the first line (freerolls, Satellites sometimes ?, ...) but appears in the rest of the description ==> use this one
        # - Buy-In/Fee from the first line differs from the rest of the description : 
        #   * OK in matrix tourneys (global buy-in dispatched between the different matches)
        #   * NOK otherwise ==> issue a warning and store specific data as if were a Matrix Tourney
        # - If no buy-in/fee can be found : assume it's a freeroll
        m = self.re_TourneyBuyInFee.search(tourneyText)
        if m is not None:
            mg = m.groupdict()
            if tourney.isMatrix :
                if mg['BUYIN'] is not None:
                    tourney.subTourneyBuyin = 100*Decimal(self.clearMoneyString(mg['BUYIN']))
                    tourney.subTourneyFee = 0
                if mg['FEE'] is not None:
                    tourney.subTourneyFee = 100*Decimal(self.clearMoneyString(mg['FEE']))
            else :
                if mg['BUYIN'] is not None:
                    if tourney.buyin is None:
                        tourney.buyin = 100*Decimal(clearMoneyString(mg['BUYIN']))
                    else :
                        if 100*Decimal(clearMoneyString(mg['BUYIN'])) != tourney.buyin:
                            log.error(_("Conflict between buyins read in topline (%s) and in BuyIn field (%s)") % (tourney.buyin, 100*Decimal(re.sub(u',', u'', "%s" % mg['BUYIN']))) )
                            tourney.subTourneyBuyin = 100*Decimal(clearMoneyString(mg['BUYIN']))
                if mg['FEE'] is not None:
                    if tourney.fee is None:
                        tourney.fee = 100*Decimal(clearMoneyString(mg['FEE']))
                    else :
                        if 100*Decimal(clearMoneyString(mg['FEE'])) != tourney.fee:
                            log.error(_("Conflict between fees read in topline (%s) and in BuyIn field (%s)") % (tourney.fee, 100*Decimal(clearMoneyString(mg['FEE']))) )
                            tourney.subTourneyFee = 100*Decimal(clearMoneyString(mg['FEE']))

        if tourney.buyin is None:
            log.info(_("Unable to affect a buyin to this tournament : assume it's a freeroll"))
            tourney.buyin = 0
            tourney.fee = 0
        else:
            if tourney.fee is None:
                #print "Couldn't initialize fee, even though buyin went OK : assume there are no fees"
                tourney.fee = 0

        #Get single line infos
        dictRegex = {   "BUYINCHIPS"        : self.re_TourneyBuyInChips,
                        "ENTRIES"           : self.re_TourneyEntries,
                        "PRIZEPOOL"         : self.re_TourneyPrizePool,
                        "REBUY_COST"        : self.re_TourneyRebuyCost,
                        "ADDON_COST"        : self.re_TourneyAddOnCost,
                        "REBUY_TOTAL"       : self.re_TourneyRebuysTotal,
                        "ADDONS_TOTAL"      : self.re_TourneyAddOnsTotal,
                        "REBUY_CHIPS"       : self.re_TourneyRebuyChips,
                        "ADDON_CHIPS"       : self.re_TourneyAddOnChips,
                        "STARTTIME"         : self.re_TourneyTimeInfo,
                        "KO_BOUNTY_AMOUNT"  : self.re_TourneyKOBounty,
                    }


        dictHolders = { "BUYINCHIPS"        : "buyInChips",
                        "ENTRIES"           : "entries",
                        "PRIZEPOOL"         : "prizepool",
                        "REBUY_COST"        : "rebuyCost",
                        "ADDON_COST"        : "addOnCost",
                        "REBUY_TOTAL"       : "totalRebuyCount",
                        "ADDONS_TOTAL"      : "totalAddOnCount",
                        "REBUY_CHIPS"       : "rebuyChips",
                        "ADDON_CHIPS"       : "addOnChips",
                        "STARTTIME"         : "starttime",
                        "KO_BOUNTY_AMOUNT"  : "koBounty"
                    }

        mg = {}     # After the loop, mg will contain all the matching groups, including the ones that have not been used, like ENDTIME and IN-PROGRESS
        for data in dictRegex:
            m = dictRegex.get(data).search(tourneyText)
            if m is not None:
                mg.update(m.groupdict())
                setattr(tourney, dictHolders[data], mg[data])

        if mg['IN_PROGRESS'] is not None or mg['ENDTIME'] is not None:
            # Assign endtime to tourney (if None, that's ok, it's because the tourney wans't over over when the summary file was produced)
            tourney.endtime = mg['ENDTIME']

        # Deal with hero specific information
        if tourney.hero is not None :
            m = self.re_TourneyRebuyCount.search(tourneyText)
            if m is not None:
                mg = m.groupdict()
                if mg['REBUY_COUNT'] is not None :
                    tourney.rebuyCounts.update( { tourney.hero : Decimal(mg['REBUY_COUNT']) } )
            m = self.re_TourneyAddOnCount.search(tourneyText)
            if m is not None:
                mg = m.groupdict()
                if mg['ADDON_COUNT'] is not None :
                    tourney.addOnCounts.update( { tourney.hero : Decimal(mg['ADDON_COUNT']) } )
            m = self.re_TourneyKoCount.search(tourneyText)
            if m is not None:
                mg = m.groupdict()
                if mg['COUNT_KO'] is not None :
                    tourney.koCounts.update( { tourney.hero : Decimal(mg['COUNT_KO']) } )

        # Deal with money amounts
        tourney.koBounty    = 100*Decimal(clearMoneyString(tourney.koBounty))
        tourney.prizepool   = 100*Decimal(clearMoneyString(tourney.prizepool))
        tourney.rebuyCost   = 100*Decimal(clearMoneyString(tourney.rebuyCost))
        tourney.addOnCost   = 100*Decimal(clearMoneyString(tourney.addOnCost))
        
        # Calculate payin amounts and update winnings -- not possible to take into account nb of rebuys, addons or Knockouts for other players than hero on FTP
        for p in tourney.players :
            if tourney.isKO :
                #tourney.incrementPlayerWinnings(tourney.players[p], Decimal(tourney.koBounty)*Decimal(tourney.koCounts[p]))
                tourney.winnings[p] += Decimal(tourney.koBounty)*Decimal(tourney.koCounts[p])
                #print "player %s : winnings %d" % (p, tourney.winnings[p])

        #print mg
        return True
    #end def determineTourneyType

    def getPlayersPositionsAndWinnings(self, tourney):
        playersText = tourney.summaryText[1]
        #print "Examine : '%s'" %(playersText)
        m = self.re_TourneysPlayersSummary.finditer(playersText)

        for a in m:
            if a.group('PNAME') is not None and a.group('RANK') is not None:
                if a.group('RANK') == "Still Playing":
                    rank = -1
                else:
                    rank = Decimal(a.group('RANK'))

                if a.group('WINNING') is not None:
                    winnings = 100*Decimal(clearMoneyString(a.group('WINNING')))
                else:
                    winnings = "0"

                tourney.addPlayer(rank, a.group('PNAME'), winnings, "USD", 0, 0, 0) #TODO: make it store actual winnings currency
            else:
                print (_("Player finishing stats unreadable : %s") % a)

        # Find Hero
        n = self.re_TourneyHeroFinishingP.search(playersText)
        if n is not None:
            heroName = n.group('HERO_NAME')
            tourney.hero = heroName
            # Is this really useful ?
            if heroName not in tourney.ranks:
                print (_("%s not found in tourney.ranks ...") % heroName)
            elif (tourney.ranks[heroName] != Decimal(n.group('HERO_FINISHING_POS'))):            
                print (_("Bad parsing : finish position incoherent : %s / %s") % (tourney.ranks[heroName], n.group('HERO_FINISHING_POS')))

        return True

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-i", "--input", dest="ipath", help=_("parse input hand history"), default="regression-test-files/fulltilt/razz/FT20090223 Danville - $0.50-$1 Ante $0.10 - Limit Razz.txt")
    parser.add_option("-o", "--output", dest="opath", help=_("output translation to"), default="-")
    parser.add_option("-f", "--follow", dest="follow", help=_("follow (tail -f) the input"), action="store_true", default=False)
    parser.add_option("-q", "--quiet",
                  action="store_const", const=logging.CRITICAL, dest="verbosity", default=logging.INFO)
    parser.add_option("-v", "--verbose",
                  action="store_const", const=logging.INFO, dest="verbosity")
    parser.add_option("--vv",
                  action="store_const", const=logging.DEBUG, dest="verbosity")

    (options, args) = parser.parse_args()

    e = Fulltilt(in_path = options.ipath, out_path = options.opath, follow = options.follow)

