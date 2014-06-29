#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Copyright 2008-2011, Chaz Littlejohn
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

# TODO: straighten out discards for draw games

import sys
from HandHistoryConverter import *
from decimal_wrapper import Decimal

# BetOnline HH Format

class BetOnline(HandHistoryConverter):

    # Class Variables

    sitename = "BetOnline"
    skin     = "BetOnline"
    filetype = "text"
    codepage = ("utf8", "cp1252")
    siteId   = 19 # Needs to match id entry in Sites database
    sym = {'USD': "\$", 'CAD': "\$", 'T$': "", "EUR": "\xe2\x82\xac", "GBP": "\xa3", "play": ""}         # ADD Euro, Sterling, etc HERE
    substitutions = {
                     'LS' : u"\$|\xe2\x82\xac|\u20ac|", # legal currency symbols - Euro(cp1252, utf-8)
                     'PLYR': r'(?P<PNAME>.+?)',
                     'NUM' :u".,\d",
                    }
                    
    # translations from captured groups to fpdb info strings
    Lim_Blinds = {  '0.04': ('0.01', '0.02'),        '0.08': ('0.02', '0.04'),
                        '0.10': ('0.02', '0.05'),    '0.20': ('0.05', '0.10'),
                        '0.40': ('0.10', '0.20'),    '0.50': ('0.10', '0.25'),
                        '1.00': ('0.25', '0.50'),       '1': ('0.25', '0.50'),
                        '2.00': ('0.50', '1.00'),       '2': ('0.50', '1.00'),
                        '4.00': ('1.00', '2.00'),       '4': ('1.00', '2.00'),
                        '6.00': ('1.00', '3.00'),       '6': ('1.00', '3.00'),
                        '8.00': ('2.00', '4.00'),       '8': ('2.00', '4.00'),
                       '10.00': ('2.00', '5.00'),      '10': ('2.00', '5.00'),
                       '20.00': ('5.00', '10.00'),     '20': ('5.00', '10.00'),
                       '30.00': ('10.00', '15.00'),    '30': ('10.00', '15.00'),
                       '40.00': ('10.00', '20.00'),    '40': ('10.00', '20.00'),
                       '60.00': ('15.00', '30.00'),    '60': ('15.00', '30.00'),
                       '80.00': ('20.00', '40.00'),    '80': ('20.00', '40.00'),
                      '100.00': ('25.00', '50.00'),   '100': ('25.00', '50.00'),
                      '200.00': ('50.00', '100.00'),  '200': ('50.00', '100.00'),
                      '400.00': ('100.00', '200.00'), '400': ('100.00', '200.00'),
                      '800.00': ('200.00', '400.00'), '800': ('200.00', '400.00'),
                     '1000.00': ('250.00', '500.00'),'1000': ('250.00', '500.00')
                  }

    limits = { 'No Limit':'nl', 'Pot Limit':'pl', 'Limit':'fl', 'LIMIT':'fl' }
    games = {                          # base, category
                              "Hold'em" : ('hold','holdem'), 
                                'Omaha' : ('hold','omahahi'),
                          'Omaha Hi/Lo' : ('hold','omahahilo'),
                                 'Razz' : ('stud','razz'), 
                          '7 Card Stud' : ('stud','studhi'),
                    '7 Card Stud Hi/Lo' : ('stud','studhilo'),
                               'Badugi' : ('draw','badugi'),
              'Triple Draw 2-7 Lowball' : ('draw','27_3draw'),
              'Single Draw 2-7 Lowball' : ('draw','27_1draw'),
                          '5 Card Draw' : ('draw','fivedraw')
               }
    mixes = {
                                 'HORSE': 'horse',
                                '8-Game': '8game',
                                  'HOSE': 'hose',
                         'Mixed PLH/PLO': 'plh_plo',
                       'Mixed Omaha H/L': 'plo_lo',
                        'Mixed Hold\'em': 'mholdem',
                           'Triple Stud': '3stud'
               } # Legal mixed games
    currencies = { u'€':'EUR', '$':'USD', '':'T$' }
    
    skins = {
                       'BetOnline Poker': 'BetOnline',
                             'PayNoRake': 'PayNoRake',
                       'ActionPoker.com': 'ActionPoker',
                            'Gear Poker': 'GearPoker',
                'SportsBetting.ag Poker': 'SportsBetting.ag',
                          'Tiger Gaming': 'Tiger Gaming'
               } # Legal mixed games

    # Static regexes
    re_GameInfo     = re.compile(u"""
          (?P<SKIN>BetOnline\sPoker|PayNoRake|ActionPoker\.com|Gear\sPoker|SportsBetting\.ag\sPoker|Tiger\sGaming)\sGame\s\#(?P<HID>[0-9]+):\s+
          (\{.*\}\s+)?(Tournament\s\#                # open paren of tournament info
          (?P<TOURNO>\d+):\s?
          # here's how I plan to use LS
          (?P<BUYIN>(?P<BIAMT>(%(LS)s)[%(NUM)s]+)?\+?(?P<BIRAKE>(%(LS)s)[%(NUM)s]+)?\+?(?P<BOUNTY>(%(LS)s)[%(NUM)s]+)?\s?|Freeroll|)\s+)?
          # close paren of tournament info
          (?P<GAME>Hold\'em|Razz|7\sCard\sStud|7\sCard\sStud\sHi/Lo|Omaha|Omaha\sHi/Lo|Badugi|Triple\sDraw\s2\-7\sLowball|Single\sDraw\s2\-7\sLowball|5\sCard\sDraw)\s
          (?P<LIMIT>No\sLimit|Limit|LIMIT|Pot\sLimit)?,?\s?
          (
              \(?                            # open paren of the stakes
              (?P<CURRENCY>%(LS)s|)?
              (?P<SB>[%(NUM)s]+)/(%(LS)s)?
              (?P<BB>[%(NUM)s]+)
              \)?                        # close paren of the stakes
          )?
          \s?-\s
          (?P<DATETIME>.*$)
        """ % substitutions, re.MULTILINE|re.VERBOSE)

    re_PlayerInfo   = re.compile(u"""
          ^Seat\s(?P<SEAT>[0-9]+):\s
          (?P<PNAME>.*)\s
          \((%(LS)s)?(?P<CASH>[%(NUM)s]+)\sin\s[cC]hips\)""" % substitutions, 
          re.MULTILINE|re.VERBOSE)

    re_HandInfo1     = re.compile("""
          ^Table\s\'(?P<TABLE>[\/,\.\-\ &%\$\#a-zA-Z\d\'\(\)]+)\'\s
          ((?P<MAX>\d+)-max\s)?
          (?P<MONEY>\((Play\sMoney|Real\sMoney)\)\s)?
          (Seat\s\#(?P<BUTTON>\d+)\sis\sthe\sbutton)?""", 
          re.MULTILINE|re.VERBOSE)
    
    re_HandInfo2     = re.compile("""
          ^Table\s(?P<TABLE>[\/,\.\-\ &%\$\#a-zA-Z\d\']+)\s
          (?P<MONEY>\((Play\sMoney|Real\sMoney)\)\s)?
          (Seat\s\#(?P<BUTTON>\d+)\sis\sthe\sbutton)?""", 
          re.MULTILINE|re.VERBOSE)

    re_Identify     = re.compile(u'(BetOnline\sPoker|PayNoRake|ActionPoker\.com|Gear\sPoker|SportsBetting\.ag\sPoker|Tiger\sGaming)\sGame\s\#\d+')
    re_SplitHands   = re.compile('\n\n\n+')
    re_TailSplitHands   = re.compile('(\n\n\n+)')
    re_Button       = re.compile('Seat #(?P<BUTTON>\d+) is the button', re.MULTILINE)
    re_Board1        = re.compile(r"Board \[(?P<FLOP>\S\S\S? \S\S\S? \S\S\S?)?\s?(?P<TURN>\S\S\S?)?\s?(?P<RIVER>\S\S\S?)?\]")
    re_Board2        = re.compile(r"\[(?P<CARDS>.+)\]")
    


    re_DateTime1     = re.compile("""(?P<Y>[0-9]{4})\/(?P<M>[0-9]{2})\/(?P<D>[0-9]{2})[\- ]+(?P<H>[0-9]+):(?P<MIN>[0-9]+)(:(?P<S>[0-9]+))?\s(?P<TZ>.*$)""", re.MULTILINE)
    re_DateTime2     = re.compile("""(?P<Y>[0-9]{4})\-(?P<M>[0-9]{2})\-(?P<D>[0-9]{2})[\- ]+(?P<H>[0-9]+):(?P<MIN>[0-9]+):(?P<S>[0-9]+)""", re.MULTILINE)

    re_PostSB           = re.compile(r"^%(PLYR)s: [Pp]osts small blind (%(LS)s)?(?P<SB>[%(NUM)s]+)" %  substitutions, re.MULTILINE)
    re_PostBB           = re.compile(r"^%(PLYR)s: ([Pp]osts big blind|[Pp]osts? [Nn]ow)( (%(LS)s)?(?P<BB>[%(NUM)s]+))?" %  substitutions, re.MULTILINE)
    re_Antes            = re.compile(r"^%(PLYR)s: [Pp]osts the ante (%(LS)s)?(?P<ANTE>[%(NUM)s]+)" % substitutions, re.MULTILINE)
    re_BringIn          = re.compile(r"^%(PLYR)s: brings[- ]in( low|) for (%(LS)s)?(?P<BRINGIN>[%(NUM)s]+)" % substitutions, re.MULTILINE)
    re_PostBoth         = re.compile(r"^%(PLYR)s: [Pp]ost dead (%(LS)s)?(?P<SBBB>[%(NUM)s]+)" %  substitutions, re.MULTILINE)
    re_HeroCards        = re.compile(r"^Dealt [Tt]o %(PLYR)s(?: \[(?P<OLDCARDS>.+?)\])?( \[(?P<NEWCARDS>.+?)\])" % substitutions, re.MULTILINE)
    re_Action           = re.compile(r"""
                        ^%(PLYR)s:(?P<ATYPE>\s[Bb]ets|\s[Cc]hecks|\s[Rr]aises|\s[Cc]alls|\s[Ff]olds|\s[Dd]iscards|\s[Ss]tands\spat|\sReraises)
                        (\s(%(LS)s)?(?P<BET>[%(NUM)s]+))?(\sto\s(%(LS)s)?(?P<BETTO>[%(NUM)s]+))?  # the number discarded goes in <BET>
                        \s*(and\sis\s[Aa]ll.[Ii]n)?
                        (\son|\scards?)?
                        (\s\[(?P<CARDS>.+?)\])?\.?\s*$"""
                         %  substitutions, re.MULTILINE|re.VERBOSE)
    re_ShowdownAction   = re.compile(r"^%s: shows (?P<CARDS>.*)" % substitutions['PLYR'], re.MULTILINE)
    re_sitsOut          = re.compile("^%s sits out" %  substitutions['PLYR'], re.MULTILINE)
    re_JoinsTable       = re.compile("^.+ joins the table at seat #\d+", re.MULTILINE)
    re_TotalPot         = re.compile(r"^Total pot (?P<POT>[%(NUM)s]+)( \| Rake (?P<RAKE>[%(NUM)s]+))?", re.MULTILINE)
    re_ShownCards       = re.compile(r"Seat (?P<SEAT>[0-9]+): %(PLYR)s (\(.+?\)  )?(?P<SHOWED>showed|mucked) \[(?P<CARDS>.*)\]( and won \([%(NUM)s]+\))?" %  substitutions, re.MULTILINE)
    re_CollectPot       = re.compile(r"Seat (?P<SEAT>[0-9]+): %(PLYR)s (\(.+?\)  )?(collected|showed \[.*\] and won) \((%(LS)s)?(?P<POT>[%(NUM)s]+)\)" %  substitutions, re.MULTILINE)

    def compilePlayerRegexs(self,  hand):
        pass

    def readSupportedGames(self):
        return [["ring", "hold", "nl"],
                ["ring", "hold", "pl"],
                ["ring", "hold", "fl"],

                #["ring", "stud", "fl"],

                #["ring", "draw", "fl"],
                #["ring", "draw", "pl"],
                #["ring", "draw", "nl"],

                ["tour", "hold", "nl"],
                ["tour", "hold", "pl"],
                ["tour", "hold", "fl"],

                #["tour", "stud", "fl"],
                
                #["tour", "draw", "fl"],
                #["tour", "draw", "pl"],
                #["tour", "draw", "nl"],
                ]

    def determineGameType(self, handText):
        info = {}
        m = self.re_GameInfo.search(handText)
        if not m:
            # BetOnline starts writing the hh the moment you sit down.
            # Test if the hh contains the join line, and throw a partial if so.
            m2 = self.re_JoinsTable.search(handText)
            if not m2:
                tmp = handText[0:200]
                log.error(_("BetOnlineToFpdb.determineGameType: '%s'") % tmp)
                raise FpdbParseError
            else:
                raise FpdbHandPartial("BetOnlineToFpdb.determineGameType: " + _("Partial hand history: 'Player joining table'"))

        mg = m.groupdict()
        if mg['LIMIT']:
            info['limitType'] = self.limits[mg['LIMIT']]
            if info['limitType']=='pl':
                m = self.re_HeroCards.search(handText)
                if m and len(m.group('NEWCARDS').split(' '))==4:
                    (info['base'], info['category']) = self.games['Omaha']
        else:
            info['limitType'] = self.limits['No Limit']
        if 'SKIN' in mg:
            self.skin = self.skins[mg['SKIN']]
        if 'GAME' in mg and not info.get('base'):
            (info['base'], info['category']) = self.games[mg['GAME']]
        if 'SB' in mg:
            info['sb'] = self.clearMoneyString(mg['SB'])
        if 'BB' in mg:
            info['bb'] = self.clearMoneyString(mg['BB'])
        if 'CURRENCY' in mg and mg['CURRENCY'] is not None:
            info['currency'] = self.currencies[mg['CURRENCY']]
        else:
            info['currency'] = 'USD'
        if 'MIXED' in mg:
            if mg['MIXED'] is not None: info['mix'] = self.mixes[mg['MIXED']]
                
        if 'TOURNO' in mg and mg['TOURNO'] is None:
            info['type'] = 'ring'
        else:
            info['type'] = 'tour'

        if info['limitType'] == 'fl' and info['bb'] is not None:
            if info['type'] == 'ring':
                try:
                    info['sb'] = self.Lim_Blinds[info['BB']][0]
                    info['bb'] = self.Lim_Blinds[info['BB']][1]
                except KeyError:
                    tmp = handText[0:200]
                    log.error(_("BetOnlineToFpdb.determineGameType: Lim_Blinds has no lookup for '%s' - '%s'") % (mg['BB'], tmp))
                    raise FpdbParseError
            else:
                info['sb'] = str((Decimal(info['SB'])/2).quantize(Decimal("0.01")))
                info['bb'] = str(Decimal(info['SB']).quantize(Decimal("0.01")))

        return info

    def readHandInfo(self, hand):
        info = {}
        if self.skin in ('ActionPoker', 'GearPoker'):
            m  = self.re_HandInfo2.search(hand.handText,re.DOTALL)
        else:
            m  = self.re_HandInfo1.search(hand.handText,re.DOTALL)
        m2 = self.re_GameInfo.search(hand.handText)
        if m is None or m2 is None:
            tmp = hand.handText[0:200]
            log.error(_("BetOnlineToFpdb.readHandInfo: '%s'") % tmp)
            raise FpdbParseError

        info.update(m.groupdict())
        info.update(m2.groupdict())

        #print 'DEBUG:', info
        for key in info:
            if key == 'DATETIME':
                #2008/11/12 10:00:48 CET [2008/11/12 4:00:48 ET] # (both dates are parsed so ET date overrides the other)
                #2008/08/17 - 01:14:43 (ET)
                #2008/09/07 06:23:14 ET
                
                datetimestr, time_zone = "2000/01/01 00:00:00", 'ET'  # default used if time not found
                if self.skin not in ('ActionPoker', 'GearPoker'):
                    m1 = self.re_DateTime1.finditer(info[key])
                    for a in m1:
                        seconds = '00'
                        if a.group('S'):
                            seconds = a.group('S')
                        datetimestr = "%s/%s/%s %s:%s:%s" % (a.group('Y'), a.group('M'),a.group('D'),a.group('H'),a.group('MIN'),seconds)
                        tz = a.group('TZ')  # just assume ET??
                        if tz == 'GMT Standard Time':
                            time_zone = 'GMT'
                        elif tz in ('Pacific Daylight Time', 'Pacific Standard Time'):
                            time_zone = 'PT'
                        else:
                            time_zone = 'ET'
                else:
                    m2 = self.re_DateTime2.finditer(info[key])
                    for a in m2:
                        datetimestr = "%s/%s/%s %s:%s:%s" % (a.group('Y'), a.group('M'),a.group('D'),a.group('H'),a.group('MIN'),a.group('S'))
                        time_zone = 'ET'
                    #print "   tz = ", tz, " datetime =", datetimestr
                hand.startTime = datetime.datetime.strptime(datetimestr, "%Y/%m/%d %H:%M:%S") # also timezone at end, e.g. " ET"
                hand.startTime = HandHistoryConverter.changeTimezone(hand.startTime, time_zone, "UTC")
            if key == 'HID':
                hand.handid = info[key]
            if key == 'MONEY':
                if info[key]=='(Play Money) ':
                    hand.gametype['currency'] = 'play'
            if key == 'TOURNO':
                hand.tourNo = info[key]
            if key == 'BUYIN':
                if hand.tourNo!=None:
                    #print "DEBUG: info['BUYIN']: %s" % info['BUYIN']
                    #print "DEBUG: info['BIAMT']: %s" % info['BIAMT']
                    #print "DEBUG: info['BIRAKE']: %s" % info['BIRAKE']
                    #print "DEBUG: info['BOUNTY']: %s" % info['BOUNTY']
                    if not info[key] or info[key] == 'Freeroll':
                        hand.buyin = 0
                        hand.fee = 0
                        hand.buyinCurrency = "FREE"
                    else:
                        if info[key].find("$")!=-1:
                            hand.buyinCurrency="USD"
                        elif info[key].find(u"€")!=-1:
                            hand.buyinCurrency="EUR"
                        elif re.match("^[0-9+]*$", info[key]):
                            hand.buyinCurrency="play"
                        else:
                            #FIXME: handle other currencies, play money
                            raise FpdbParseError(_("BetOnlineToFpdb.readHandInfo: Failed to detect currency.") + " " + _("Hand ID") + ": %s: '%s'" % (hand.handid, info[key]))

                        info['BIAMT'] = info['BIAMT'].strip(u'$€')
                        if info['BOUNTY'] != None:
                            # There is a bounty, Which means we need to switch BOUNTY and BIRAKE values
                            tmp = info['BOUNTY']
                            info['BOUNTY'] = info['BIRAKE']
                            info['BIRAKE'] = tmp
                            info['BOUNTY'] = info['BOUNTY'].strip(u'$€') # Strip here where it isn't 'None'
                            hand.koBounty = int(100*Decimal(info['BOUNTY']))
                            hand.isKO = True
                        else:
                            hand.isKO = False

                        info['BIRAKE'] = info['BIRAKE'].strip(u'$€')

                        hand.buyin = int(100*Decimal(info['BIAMT']))
                        hand.fee = int(100*Decimal(info['BIRAKE']))
            if key == 'LEVEL':
                hand.level = info[key]

            if key == 'TABLE':
                if hand.tourNo != None:
                    hand.tablename = re.split("-", info[key])[1]
                else:
                    hand.tablename = info[key]
            if key == 'BUTTON':
                hand.buttonpos = info[key]
            if key == 'MAX' and info[key] != None:
                hand.maxseats = int(info[key])
        if not self.re_Board1.search(hand.handText) and self.skin not in ('ActionPoker', 'GearPoker'):
            raise FpdbHandPartial("readHandInfo: " + _("Partial hand history") + ": '%s'" % hand.handid)
    
    def readButton(self, hand):
        m = self.re_Button.search(hand.handText)
        if m:
            hand.buttonpos = int(m.group('BUTTON'))
        else:
            log.info('readButton: ' + _('not found'))

    def readPlayerStacks(self, hand):
        m = self.re_PlayerInfo.finditer(hand.handText)
        for a in m:
            pname = self.unknownPlayer(hand, a.group('PNAME'))
            hand.addPlayer(int(a.group('SEAT')), pname, self.clearMoneyString(a.group('CASH')))

    def markStreets(self, hand):

        # There is no marker between deal and draw in Stars single draw games
        #  this upsets the accounting, incorrectly sets handsPlayers.cardxx and 
        #  in consequence the mucked-display is incorrect.
        # Attempt to fix by inserting a DRAW marker into the hand text attribute

        if hand.gametype['category'] in ('27_1draw', 'fivedraw'):
            # isolate the first discard/stand pat line (thanks Carl for the regex)
            discard_split = re.split(r"(?:(.+(?: stands pat|: discards).+))", hand.handText,re.DOTALL)
            if len(hand.handText) == len(discard_split[0]):
                # handText was not split, no DRAW street occurred
                pass
            else:
                # DRAW street found, reassemble, with DRAW marker added
                discard_split[0] += "*** DRAW ***\r\n"
                hand.handText = ""
                for i in discard_split:
                    hand.handText += i

        # PREFLOP = ** Dealing down cards **
        # This re fails if,  say, river is missing; then we don't get the ** that starts the river.
        if hand.gametype['base'] in ("hold"):
            m =  re.search(r"\*\*\* HOLE CARDS \*\*\*(?P<PREFLOP>.+(?=\*\*\* FLOP \*\*\*)|.+)"
                       r"(\*\*\* FLOP \*\*\*(?P<FLOP> \[\S\S\S? \S\S\S? \S\S\S?\].+(?=\*\*\* TURN \*\*\*)|.+))?"
                       r"(\*\*\* TURN \*\*\* \[\S\S\S? \S\S\S? \S\S\S?](?P<TURN>\[\S\S\S?\].+(?=\*\*\* RIVER \*\*\*)|.+))?"
                       r"(\*\*\* RIVER \*\*\* \[\S\S\S? \S\S\S? \S\S\S? \S\S\S?](?P<RIVER>\[\S\S\S?\].+))?", hand.handText,re.DOTALL)
            m2 = self.re_Board1.search(hand.handText)
            if m and m2:
                if m2.group('FLOP') and not m.group('FLOP'):
                    m =  re.search(r"\*\*\* HOLE CARDS \*\*\*(?P<PREFLOP>.+(?=Board )|.+)"
                                   r"(Board \[(?P<FLOP>\S\S\S? \S\S\S? \S\S\S?)?\s?(?P<TURN>\S\S\S?)?\s?(?P<RIVER>\S\S\S?)?\])?", hand.handText,re.DOTALL)
                elif  m2.group('TURN') and not m.group('TURN'):
                    m =  re.search(r"\*\*\* HOLE CARDS \*\*\*(?P<PREFLOP>.+(?=\*\*\* FLOP \*\*\*)|.+)"
                                   r"(\*\*\* FLOP \*\*\*(?P<FLOP> \[\S\S\S? \S\S\S? \S\S\S?\].+(?=Board )|.+))?"
                                   r"(Board \[(?P<BFLOP>\S\S\S? \S\S\S? \S\S\S?)?\s?(?P<TURN>\S\S\S?)?\s?(?P<RIVER>\S\S\S?)?\])?", hand.handText,re.DOTALL)
                elif  m2.group('RIVER') and not m.group('RIVER'):
                    m =  re.search(r"\*\*\* HOLE CARDS \*\*\*(?P<PREFLOP>.+(?=\*\*\* FLOP \*\*\*)|.+)"
                                   r"(\*\*\* FLOP \*\*\*(?P<FLOP> \[\S\S\S? \S\S\S? \S\S\S?\].+(?=\*\*\* TURN \*\*\*)|.+))?"
                                   r"(\*\*\* TURN \*\*\* \[\S\S\S? \S\S\S? \S\S\S?](?P<TURN>\[\S\S\S?\].+(?=Board )|.+))?"
                                   r"(Board \[(?P<BFLOP>\S\S\S? \S\S\S? \S\S\S?)?\s?(?P<BTURN>\S\S\S?)?\s?(?P<RIVER>\S\S\S?)?\])?", hand.handText,re.DOTALL)
        elif hand.gametype['base'] in ("stud"):
            m =  re.search(r"(?P<ANTES>.+(?=\*\*\* 3rd STREET \*\*\*)|.+)"
                           r"(\*\*\* 3rd STREET \*\*\*(?P<THIRD>.+(?=\*\*\* 4th STREET \*\*\*)|.+))?"
                           r"(\*\*\* 4th STREET \*\*\*(?P<FOURTH>.+(?=\*\*\* 5th STREET \*\*\*)|.+))?"
                           r"(\*\*\* 5th STREET \*\*\*(?P<FIFTH>.+(?=\*\*\* 6th STREET \*\*\*)|.+))?"
                           r"(\*\*\* 6th STREET \*\*\*(?P<SIXTH>.+(?=\*\*\* RIVER \*\*\*)|.+))?"
                           r"(\*\*\* RIVER \*\*\*(?P<SEVENTH>.+))?", hand.handText,re.DOTALL)
        elif hand.gametype['base'] in ("draw"):
            if hand.gametype['category'] in ('27_1draw', 'fivedraw'):
                m =  re.search(r"(?P<PREDEAL>.+(?=\*\*\* DEALING HANDS \*\*\*)|.+)"
                           r"(\*\*\* DEALING HANDS \*\*\*(?P<DEAL>.+(?=\*\*\* DRAW \*\*\*)|.+))?"
                           r"(\*\*\* DRAW \*\*\*(?P<DRAWONE>.+))?", hand.handText,re.DOTALL)
            else:
                m =  re.search(r"(?P<PREDEAL>.+(?=\*\*\* DEALING HANDS \*\*\*)|.+)"
                           r"(\*\*\* DEALING HANDS \*\*\*(?P<DEAL>.+(?=\*\*\* FIRST DRAW \*\*\*)|.+))?"
                           r"(\*\*\* FIRST DRAW \*\*\*(?P<DRAWONE>.+(?=\*\*\* SECOND DRAW \*\*\*)|.+))?"
                           r"(\*\*\* SECOND DRAW \*\*\*(?P<DRAWTWO>.+(?=\*\*\* THIRD DRAW \*\*\*)|.+))?"
                           r"(\*\*\* THIRD DRAW \*\*\*(?P<DRAWTHREE>.+))?", hand.handText,re.DOTALL)
        hand.addStreets(m)
        #if m3 and m2:
        #    if m2.group('RIVER') and not m3.group('RIVER'):
        #        print hand.streets

    def readCommunityCards(self, hand, street): # street has been matched by markStreets, so exists in this hand
        if street in ('FLOP','TURN','RIVER'):   # a list of streets which get dealt community cards (i.e. all but PREFLOP)
            if self.skin not in ('ActionPoker', 'GearPoker'):
                m = self.re_Board1.search(hand.handText)
                if m and m.group(street):
                    cards = m.group(street).split(' ')
                    cards = [c.replace("10", "T") for c in cards]
                    hand.setCommunityCards(street, cards)
            else:
                m = self.re_Board2.search(hand.streets[street])
                cards = m.group('CARDS').split(' ')
                cards = [c[:-1].replace('10', 'T') + c[-1].lower() for c in cards]
                hand.setCommunityCards(street, cards)

    def readAntes(self, hand):
        m = self.re_Antes.finditer(hand.handText)
        for player in m:
            pname = self.unknownPlayer(hand, a.group('PNAME'))
            hand.addAnte(pname, self.clearMoneyString(player.group('ANTE')))
    
    def readBringIn(self, hand):
        m = self.re_BringIn.search(hand.handText,re.DOTALL)
        if m:
            #~ logging.debug("readBringIn: %s for %s" %(m.group('PNAME'),  m.group('BRINGIN')))
            hand.addBringIn(m.group('PNAME'),  self.clearMoneyString(m.group('BRINGIN')))
        
    def readBlinds(self, hand):
        liveBlind = True
        for a in self.re_PostSB.finditer(hand.handText):
            pname = self.unknownPlayer(hand, a.group('PNAME'))
            sb = self.clearMoneyString(a.group('SB'))
            if liveBlind:
                hand.addBlind(pname, 'small blind', sb)
                liveBlind = False
            else:
                # Post dead blinds as ante
                hand.addBlind(pname, 'secondsb', sb)
            if not hand.gametype['sb'] and self.skin in ('ActionPoker', 'GearPoker'):
                hand.gametype['sb'] = sb
        for a in self.re_PostBB.finditer(hand.handText):
            pname = self.unknownPlayer(hand, a.group('PNAME'))
            if a.group('BB') is not None:
                bb = self.clearMoneyString(a.group('BB'))
            elif hand.gametype['bb']:
                bb = hand.gametype['bb']
            else:
                raise FpdbHandPartial("BetOnlineToFpdb.readBlinds: " + _("Partial hand history: 'No blind info'"))
            hand.addBlind(pname, 'big blind', bb)
            if not hand.gametype['bb'] and self.skin in ('ActionPoker', 'GearPoker'):
                hand.gametype['bb'] = bb
        for a in self.re_PostBoth.finditer(hand.handText):
            pname = self.unknownPlayer(hand, a.group('PNAME'))
            sbbb = self.clearMoneyString(a.group('SBBB'))
            amount = str(Decimal(sbbb) + Decimal(sbbb)/2)
            hand.addBlind(pname, 'both', amount)
        self.fixActionBlinds(hand)
                
    def fixActionBlinds(self, hand):
        # FIXME
        # The following should only trigger when a small blind is missing in ActionPoker hands, or the sb/bb is ALL_IN
        # see http://sourceforge.net/apps/mantisbt/fpdb/view.php?id=115
        if self.skin in ('ActionPoker', 'GearPoker'):
            if hand.gametype['sb'] == None and hand.gametype['bb'] == None:
                hand.gametype['sb'] = "1"
                hand.gametype['bb'] = "2"
            elif hand.gametype['sb'] == None:
                hand.gametype['sb'] = str(int(Decimal(hand.gametype['bb']))/2)
            elif hand.gametype['bb'] == None:
                hand.gametype['bb'] = str(int(Decimal(hand.gametype['sb']))*2)
            if int(Decimal(hand.gametype['bb']))/2 != int(Decimal(hand.gametype['sb'])):
                if int(Decimal(hand.gametype['bb']))/2 < int(Decimal(hand.gametype['sb'])):
                    hand.gametype['bb'] = str(int(Decimal(hand.gametype['sb']))*2)
                else:
                    hand.gametype['sb'] = str(int(Decimal(hand.gametype['bb']))/2)
            
    def unknownPlayer(self, hand, pname):
        if pname == 'Unknown player' or not pname:
            if not pname: pname = 'Dead'
            if pname not in (p[1] for p in hand.players):
                hand.addPlayer(0, pname, '0')
        return pname

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
                    newcards = [c[:-1].replace('10', 'T') + c[-1].lower() for c in newcards]
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
                    newcards = [c[:-1].replace('10', 'T') + c[-1].lower() for c in newcards]
                if found.group('OLDCARDS') is None:
                    oldcards = []
                else:
                    oldcards = found.group('OLDCARDS').split(' ')
                    oldcards = [c[:-1].replace('10', 'T') + c[-1].lower() for c in oldcards]
                if street == 'THIRD' and len(newcards) == 3: # hero in stud game
                    hand.hero = player
                    hand.dealt.add(player) # need this for stud??
                    hand.addHoleCards(street, player, closed=newcards[0:2], open=[newcards[2]], shown=False, mucked=False, dealt=False)
                else:
                    hand.addHoleCards(street, player, open=newcards, closed=oldcards, shown=False, mucked=False, dealt=False)


    def readAction(self, hand, street):
        m = self.re_Action.finditer(hand.streets[street])
        for action in m:
            acts = action.groupdict()
            #print "DEBUG: acts: %s" %acts
            pname = self.unknownPlayer(hand, action.group('PNAME'))
            if action.group('ATYPE') in (' folds', ' Folds'):
                hand.addFold( street, pname)
            elif action.group('ATYPE') in (' checks', ' Checks'):
                hand.addCheck( street, pname)
            elif action.group('ATYPE') in (' calls', ' Calls'):
                hand.addCall( street, pname, self.clearMoneyString(action.group('BET')) )
            elif action.group('ATYPE') in (' raises', ' Raises', ' Reraises'):
                hand.addCallandRaise( street, pname, self.clearMoneyString(action.group('BET')) )
            elif action.group('ATYPE') in (' bets', ' Bets'):
                hand.addBet( street, pname, self.clearMoneyString(action.group('BET')) )
            elif action.group('ATYPE') == ' discards':
                hand.addDiscard(street, pname, action.group('BET'), action.group('CARDS'))
            elif action.group('ATYPE') == ' stands pat':
                hand.addStandsPat( street, pname, action.group('CARDS'))
            else:
                print (_("DEBUG:") + " " + _("Unimplemented %s: '%s' '%s'") % ("readAction", action.group('PNAME'), action.group('ATYPE')))


    def readShowdownActions(self, hand):
# TODO: pick up mucks also??
        for shows in self.re_ShowdownAction.finditer(hand.handText):            
            cards = shows.group('CARDS').split(' ')
            cards = [c[:-1].replace('10', 'T') + c[-1].lower() for c in cards]
            hand.addShownCards(cards, shows.group('PNAME'))

    def readCollectPot(self,hand):
        hand.adjustCollected = True
        for m in self.re_CollectPot.finditer(hand.handText):
            hand.addCollectPot(player=m.group('PNAME'),pot=m.group('POT'))
        for m in self.re_TotalPot.finditer(hand.handText):
            if hand.rakes.get('pot'):
                hand.rakes['pot'] += Decimal(self.clearMoneyString(m.group('POT')))
            else:
                hand.rakes['pot'] = Decimal(self.clearMoneyString(m.group('POT')))

    def readShownCards(self,hand):
        for m in self.re_ShownCards.finditer(hand.handText):
            if m.group('CARDS') is not None:
                pname = self.unknownPlayer(hand, m.group('PNAME'))
                cards = m.group('CARDS')
                cards = cards.split(' ') # needs to be a list, not a set--stud needs the order
                cards = [c[:-1].replace('10', 'T') + c[-1].lower() for c in cards if len(c)>0]
                (shown, mucked) = (False, False)
                if m.group('SHOWED') == "showed": shown = True
                elif m.group('SHOWED') == "mucked": mucked = True
                if hand.gametype['category']=='holdem' and len(cards)>2: continue
                #print "DEBUG: hand.addShownCards(%s, %s, %s, %s)" %(cards, m.group('PNAME'), shown, mucked)
                hand.addShownCards(cards=cards, player=pname, shown=shown, mucked=mucked, string=None)
