#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Copyright 2008-2010, Carl Gherardi
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

import sys
from HandHistoryConverter import *
from decimal_wrapper import Decimal

# PacificPoker HH Format

class PacificPoker(HandHistoryConverter):

    # Class Variables

    sitename = "PacificPoker"
    filetype = "text"
    codepage = ("utf8", "cp1252")
    siteId   = 10 # Needs to match id entry in Sites database

    mixes = { 'HORSE': 'horse', '8-Game': '8game', 'HOSE': 'hose'} # Legal mixed games
    sym = {'USD': "\$", 'CAD': "\$", 'T$': "", "EUR": "\xe2\x82\xac", "GBP": "\xa3", "play": ""}         # ADD Euro, Sterling, etc HERE
    substitutions = {
                     'LEGAL_ISO' : "USD|EUR|GBP|CAD|FPP",     # legal ISO currency codes
                           'PLYR': r'(?P<PNAME>.+?)',
                            'LS' : u"\$|\xe2\x82\xac|\u20ac|", # legal currency symbols - Euro(cp1252, utf-8)
                           'NUM' : u".,\d\xa0",
                           'CUR' : u"(\$|\xe2\x82\xac|\u20ac|)"
                    }
                    
    # translations from captured groups to fpdb info strings
    # not needed for PacificPoker
    #Lim_Blinds = {      '0.01': ('0.01', '0.02'),
    #                    '0.02': ('0.02', '0.04'),
    #                    '0.03': ('0.03', '0.06'),
    #                    '0.05': ('0.05', '0.10'),
    #                    '0.12': ('0.12', '0.25'),
    #                    '0.25': ('0.25', '0.50'),
    #                    '0.50': ('0.50', '1.00'),
    #                    '1.00': ('1.00', '2.00'),         '1': ('1.00', '2.00'),
    #                    '2.00': ('2.00', '4.00'),         '2': ('2.00', '4.00'),
    #                    '3.00': ('3.00', '6.00'),         '3': ('3.00', '6.00'),
    #                    '5.00': ('5.00', '10.00'),        '5': ('5.00', '10.00'),
    #                   '10.00': ('10.00', '20.00'),      '10': ('10.00', '20.00'),
    #                   '15.00': ('15.00', '30.00'),      '15': ('15.00', '30.00'),
    #                   '30.00': ('30.00', '60.00'),      '30': ('30.00', '60.00'),
    #                   '50.00': ('50.00', '100.00'),     '50': ('50.00', '100.00'),
    #                   '75.00': ('75.00', '150.00'),     '75': ('75.00', '150.00'),
    #                  '100.00': ('100.00', '200.00'),   '100': ('100.00', '200.00'),
    #                  '200.00': ('200.00', '400.00'),   '200': ('200.00', '400.00'),
    #                  '250.00': ('250.00', '500.00'),   '250': ('250.00', '500.00')
    #              }

    limits = { 'No Limit':'nl', 'Pot Limit':'pl', 'Limit':'fl', 'LIMIT':'fl', 'Fix Limit':'fl' }

    games = {                          # base, category
                             "Hold'em"  : ('hold','holdem'),
                               'Holdem' : ('hold','holdem'),
                                'Omaha' : ('hold','omahahi'),
                          'Omaha Hi/Lo' : ('hold','omahahilo'),
                              'OmahaHL' : ('hold','omahahilo')
               }

    currencies = { u'€':'EUR', '$':'USD', '':'T$' }

    # Static regexes
    re_GameInfo     = re.compile(u"""
          (\#Game\sNo\s:\s[0-9]+\\n)?
          \*\*\*\*\*\s(Cassava|888poker|888\.es)\s(?P<FAST>Snap\sPoker\s)?Hand\sHistory\sfor\sGame\s(?P<HID>[0-9]+)\s\*\*\*\*\*\\n
          (?P<CURRENCY1>%(LS)s)?\s?(?P<SB>[%(NUM)s]+)\s?(?P<CURRENCY2>%(LS)s)?/(%(LS)s)?\s?(?P<BB>[%(NUM)s]+)\s?(%(LS)s)?\sBlinds\s
          (?P<LIMIT>No\sLimit|Fix\sLimit|Pot\sLimit)\s
          (?P<GAME>Holdem|Omaha|OmahaHL|Hold\'em|Omaha\sHi/Lo|OmahaHL)
          (\sJackpot\stable)?
          \s-\s\*\*\*\s
          (?P<DATETIME>.*$)\s
          (Tournament\s\#(?P<TOURNO>\d+))?
          """ % substitutions, re.MULTILINE|re.VERBOSE)

    re_PlayerInfo   = re.compile(u"""
          ^Seat\s(?P<SEAT>[0-9]+):\s
          (?P<PNAME>.*)\s
          \(\s(%(LS)s)?\s?(?P<CASH>[%(NUM)s]+)\s?(%(LS)s)?\s\)""" % substitutions, 
          re.MULTILINE|re.VERBOSE)

    re_HandInfo     = re.compile("""
          ^(
            (Table\s(?P<TABLE>[-\ \#a-zA-Z\d]+?)\s)
            |
            (Tournament\s\#(?P<TOURNO>\d+)\s
              (
                (?P<BUYIN>(
                  ((?P<BIAMT>(%(LS)s)?\s?[%(NUM)s]+\s?(%(LS)s)?)(\s\+\s?(?P<BIRAKE>(%(LS)s)?\s?[%(NUM)s]+\s?(%(LS)s)?))?)
                  |
                  (Free)
                  |
                  (.+?)
                ))
              )
              \s-\sTable\s\#(?P<TABLEID>\d+)\s
            )
           )
          ((?P<MAX>\d+)\sMax\s)?
          (\(Real\sMoney\))?
          (?P<PLAY>\(Practice\sPlay\))?
          \\n
          Seat\s(?P<BUTTON>[0-9]+)\sis\sthe\sbutton
          """ % substitutions, re.MULTILINE|re.VERBOSE)

    re_Identify     = re.compile(u'\*{5}\s(Cassava|888poker|888\.es)\s(Snap\sPoker\s)?Hand\sHistory\sfor\sGame\s\d+\s')
    re_SplitHands   = re.compile('\n\n+')
    re_TailSplitHands   = re.compile('(\n\n\n+)')
    re_Button       = re.compile('Seat (?P<BUTTON>\d+) is the button', re.MULTILINE)
    re_Board        = re.compile(u"\[\s(?P<CARDS>.+)\s\]")
    re_Spanish_10   = re.compile(u'D([tpeo])')

    re_DateTime     = re.compile("""(?P<D>[0-9]{2})\s(?P<M>[0-9]{2})\s(?P<Y>[0-9]{4})[\- ]+(?P<H>[0-9]+):(?P<MIN>[0-9]+):(?P<S>[0-9]+)""", re.MULTILINE)

    short_subst = {'PLYR': r'(?P<PNAME>.+?)', 'CUR': '\$?', 'NUM' : u".,\d\xa0"}
    re_PostSB           = re.compile(r"^%(PLYR)s posts small blind \[(%(CUR)s)?\s?(?P<SB>[%(NUM)s]+)\s?(%(CUR)s)?\]" %  substitutions, re.MULTILINE)
    re_PostBB           = re.compile(r"^%(PLYR)s posts big blind \[(%(CUR)s)?\s?(?P<BB>[%(NUM)s]+)\s?(%(CUR)s)?\]" %  substitutions, re.MULTILINE)
    re_Antes            = re.compile(r"^%(PLYR)s posts (the\s)?ante \[(%(CUR)s)?\s?(?P<ANTE>[%(NUM)s]+)\s?(%(CUR)s)?\]" % substitutions, re.MULTILINE)
    # TODO: unknown in available hand histories for pacificpoker:
    re_BringIn          = re.compile(r"^%(PLYR)s: brings[- ]in( low|) for (%(CUR)s)?\s?(?P<BRINGIN>[%(NUM)s]+)\s?(%(CUR)s)?" % substitutions, re.MULTILINE)
    re_PostBoth         = re.compile(r"^%(PLYR)s posts dead blind \[(%(CUR)s)?\s?(?P<SB>[%(NUM)s]+)\s?(%(CUR)s)?\s\+\s(%(CUR)s)?\s?(?P<BB>[%(NUM)s]+)\s?(%(CUR)s)?\]" %  substitutions, re.MULTILINE)
    re_HeroCards        = re.compile(r"^Dealt to %(PLYR)s( \[\s(?P<NEWCARDS>.+?)\s\])" % substitutions, re.MULTILINE)
    re_Action           = re.compile(r"""
                        ^%(PLYR)s(?P<ATYPE>\sbets|\schecks|\sraises|\scalls|\sfolds|\sdiscards|\sstands\spat)
                        (\s\[(%(CUR)s)?\s?(?P<BET>[%(NUM)s]+)\s?(%(CUR)s)?\])?
                        (\s*and\sis\sall.in)?
                        (\s*and\shas\sreached\sthe\s[%(CUR)s\s?\d\.]+\scap)?
                        (\s*cards?(\s\[(?P<DISCARDED>.+?)\])?)?\s*$"""
                         %  substitutions, re.MULTILINE|re.VERBOSE)
    re_ShowdownAction   = re.compile(r"^%s shows \[(?P<CARDS>.*)\]" % substitutions['PLYR'], re.MULTILINE)
    re_sitsOut          = re.compile("^%s sits out" %  substitutions['PLYR'], re.MULTILINE)
    re_ShownCards       = re.compile("^%s ?(?P<SHOWED>shows|mucks) \[ (?P<CARDS>.*) \]$" %  substitutions['PLYR'], re.MULTILINE)
    re_CollectPot       = re.compile(r"^%(PLYR)s collected \[ (%(CUR)s)?\s?(?P<POT>[%(NUM)s]+)\s?(%(CUR)s)? \]$" %  substitutions, re.MULTILINE)

    def compilePlayerRegexs(self,  hand):
        pass

    def readSupportedGames(self):
        return [["ring", "hold", "nl"],
                ["ring", "hold", "pl"],
                ["ring", "hold", "fl"],

                ["tour", "hold", "nl"],
                ["tour", "hold", "pl"],
                ["tour", "hold", "fl"],
                ]

    def determineGameType(self, handText):
        info = {}
        m = self.re_GameInfo.search(handText)
        if not m:
            tmp = handText[0:200]
            log.error(_("PacificPokerToFpdb.determineGameType: '%s'") % tmp)
            raise FpdbParseError

        mg = m.groupdict()
        #print "DEBUG: mg: ", mg
        if 'LIMIT' in mg:
            #print "DEBUG: re_GameInfo[LIMIT] \'", mg['LIMIT'], "\'"
            info['limitType'] = self.limits[mg['LIMIT']]
        if 'GAME' in mg:
            #print "DEBUG: re_GameInfo[GAME] \'", mg['GAME'], "\'"
            (info['base'], info['category']) = self.games[mg['GAME']]
        if 'SB' in mg:
            #print "DEBUG: re_GameInfo[SB] \'", mg['SB'], "\'"
            info['sb'] = self.clearMoneyString(mg['SB'])
        if 'BB' in mg:
            #print "DEBUG: re_GameInfo[BB] \'", mg['BB'], "\'"
            info['bb'] = self.clearMoneyString(mg['BB'])
        if 'CURRENCY1' in mg:
            #print "DEBUG: re_GameInfo[CURRENCY] \'", mg['CURRENCY'], "\'"
            info['currency'] = self.currencies[mg['CURRENCY1']]
        if 'CURRENCY2' in mg and mg['CURRENCY2']:
            #print "DEBUG: re_GameInfo[CURRENCY] \'", mg['CURRENCY'], "\'"
            info['currency'] = self.currencies[mg['CURRENCY2']]
        if 'FAST' in mg and mg['FAST'] is not None:
            info['fast'] = True

        if 'TOURNO' in mg and mg['TOURNO'] is not None:
            info['type'] = 'tour'
            info['currency'] = 'T$'
        else:
            info['type'] = 'ring'

        # Pacific Poker includes the blind levels in the gametype, the following is not needed.
        #if info['limitType'] == 'fl' and info['bb'] is not None and info['type'] == 'ring' and info['base'] != 'stud':
        #    try:
        #        info['sb'] = self.Lim_Blinds[mg['BB']][0]
        #        info['bb'] = self.Lim_Blinds[mg['BB']][1]
        #    except KeyError:
        #        log.error(_("determineGameType: Lim_Blinds has no lookup for '%s'" % mg['BB']))
        #        log.error(_("determineGameType: Raising FpdbParseError"))
        #        raise FpdbParseError(_("Lim_Blinds has no lookup for '%s'") % mg['BB'])

        return info

    def readHandInfo(self, hand):
        info = {}
        m  = self.re_HandInfo.search(hand.handText,re.DOTALL)
        if m is None:
            log.error("re_HandInfo could not be parsed")
        m2 = self.re_GameInfo.search(hand.handText)
        if m2 is None:
            log.error("re_GameInfo could not be parsed")
        if m is None or m2 is None:
            tmp = hand.handText[0:200]
            log.error(_("PacificPokerToFpdb.readHandInfo: '%s'") % tmp)
            raise FpdbParseError

        info.update(m.groupdict())
        info.update(m2.groupdict())

        #log.debug("readHandInfo: %s" % info)
        for key in info:
            if key == 'DATETIME':
                # 28 11 2011 19:05:11
                m1 = self.re_DateTime.finditer(info[key])
                datetimestr = "2000/01/01 00:00:00"  # default used if time not found
                for a in m1:
                    datetimestr = "%s/%s/%s %s:%s:%s" % (a.group('Y'), a.group('M'),a.group('D'),a.group('H'),a.group('MIN'),a.group('S'))
                hand.startTime = datetime.datetime.strptime(datetimestr, "%Y/%m/%d %H:%M:%S")
                hand.startTime = HandHistoryConverter.changeTimezone(hand.startTime, "ET", "UTC")
            if key == 'HID':
                hand.handid = info[key]
            if key == 'TOURNO' and info['TOURNO'] != None:
                hand.tourNo = info[key]
                hand.isKO = False
            if key == 'BUYIN' and info['BUYIN'] != None:
                if info[key] == 'Free' or info['BIAMT'] is None:
                    hand.buyin = 0
                    hand.fee = 0
                    hand.buyinCurrency = "FREE"
                else: 
                    if info['BUYIN'].find("$")!=-1:
                        hand.buyinCurrency="USD"
                    elif info['BUYIN'].find(u"€")!=-1:
                        hand.buyinCurrency="EUR"
                    elif 'PLAY' in info and info['PLAY'] != "Practice Play":
                        hand.buyinCurrency="FREE"
                    else:
                        #FIXME: handle other currencies, FPP, play money
                        log.error(_("PacificPokerToFpdb.readHandInfo: Failed to detect currency.") + " Hand ID: %s: '%s'" % (hand.handid, info[key]))
                        raise FpdbParseError

                    info['BIAMT'] = self.clearMoneyString(info['BIAMT'].strip(u'$€'))
                    hand.buyin = int(100*Decimal(info['BIAMT']))
                    
                    if info['BIRAKE'] is None:
                        hand.fee = 0
                    else:
                        info['BIRAKE'] = self.clearMoneyString(info['BIRAKE'].strip(u'$€'))
                        hand.fee = int(100*Decimal(info['BIRAKE']))

            if key == 'TABLE' and info['TABLE'] != None:
                hand.tablename = info[key]
            if key == 'TABLEID' and info['TABLEID'] != None:
                hand.tablename = info[key]
            if key == 'BUTTON':
                hand.buttonpos = info[key]
            if key == 'MAX' and info['MAX'] != None:
                hand.maxseats = int(info[key])

            if key == 'PLAY' and info['PLAY'] is not None:
                #hand.currency = 'play' # overrides previously set value
                hand.gametype['currency'] = 'play'
    
    def readButton(self, hand):
        m = self.re_Button.search(hand.handText)
        if m:
            hand.buttonpos = int(m.group('BUTTON'))
        else:
            log.info('readButton: ' + _('not found'))

    def readPlayerStacks(self, hand):
        m = self.re_PlayerInfo.finditer(hand.handText)
        for a in m:
            if (len(a.group('PNAME'))==0):
                log.error("PacificPokerToFpdb.readPlayerStacks: Player name empty %s" % hand.handid)
                raise FpdbParseError
            hand.addPlayer(int(a.group('SEAT')), a.group('PNAME'), self.clearMoneyString(a.group('CASH')))

    def markStreets(self, hand):
        # PREFLOP = ** Dealing down cards ** (observed hands don't have this line)
        # This re fails if,  say, river is missing; then we don't get the ** that starts the river.
        if hand.gametype['base'] in ("hold"):
            m =  re.search(r"(?P<PREFLOP>.+(?=\*\* Dealing flop \*\*)|.+)"
                       r"(\*\* Dealing flop \*\* (?P<FLOP>\[ \S\S, \S\S, \S\S \].+(?=\*\* Dealing turn \*\*)|.+))?"
                       r"(\*\* Dealing turn \*\* (?P<TURN>\[ \S\S \].+(?=\*\* Dealing river \*\*)|.+))?"
                       r"(\*\* Dealing river \*\* (?P<RIVER>\[ \S\S \].+?(?=\*\* Summary \*\*)|.+))?"
                       , hand.handText,re.DOTALL)
        if m is None:
            log.error(_("PacificPokerToFpdb.markStreets: Unable to recognise streets %s" % hand.handid))
            raise FpdbParseError
        else:
            #print "DEBUG: Matched markStreets"
            mg = m.groupdict()
#            if 'PREFLOP' in mg:
#                print "DEBUG: PREFLOP: ", [mg['PREFLOP']]
#            if 'FLOP' in mg:
#                print "DEBUG: FLOP: ", [mg['FLOP']]
#            if 'TURN' in mg:
#                print "DEBUG: TURN: ", [mg['TURN']]
#            if 'RIVER' in mg:
#                print "DEBUG: RIVER: ", [mg['RIVER']]

        hand.addStreets(m)

    def readCommunityCards(self, hand, street): # street has been matched by markStreets, so exists in this hand
        if street in ('FLOP','TURN','RIVER'):   # a list of streets which get dealt community cards (i.e. all but PREFLOP)
            #print "DEBUG readCommunityCards:", street, hand.streets.group(street)
            m = self.re_Board.search(hand.streets[street])
            cards = self.splitCards(m.group('CARDS'))
            hand.setCommunityCards(street, cards)

    def readAntes(self, hand):
        m = self.re_Antes.finditer(hand.handText)
        for player in m:
            #~ logging.debug("hand.addAnte(%s,%s)" %(player.group('PNAME'), player.group('ANTE')))
            hand.addAnte(player.group('PNAME'), self.clearMoneyString(player.group('ANTE')))
            self.allInBlind(hand, 'PREFLOP', player, 'ante')
    
    def readBringIn(self, hand):
        m = self.re_BringIn.search(hand.handText,re.DOTALL)
        if m:
            #~ logging.debug("readBringIn: %s for %s" %(m.group('PNAME'),  m.group('BRINGIN')))
            hand.addBringIn(m.group('PNAME'),  m.group('BRINGIN'))
        
    def readBlinds(self, hand):
        hand.setUncalledBets(True)
        liveBlind, hand.allInBlind = True, False
        for a in self.re_PostSB.finditer(hand.handText):
            if a.group('PNAME') in hand.stacks:
                if liveBlind:
                    hand.addBlind(a.group('PNAME'), 'small blind', self.clearMoneyString(a.group('SB')))
                    liveBlind = False
                else:
                    # Post dead blinds as ante
                    hand.addBlind(a.group('PNAME'), 'secondsb', self.clearMoneyString(a.group('SB')))
                self.allInBlind(hand, 'PREFLOP', a, 'secondsb')
            else:
                log.error("PacificPokerToFpdb.readBlinds (SB): '%s', '%s' not in hand.stacks" % (hand.handid, a.group('PNAME')))
                raise FpdbParseError
        for a in self.re_PostBB.finditer(hand.handText):
            if a.group('PNAME') in hand.stacks:
                hand.addBlind(a.group('PNAME'), 'big blind', self.clearMoneyString(a.group('BB')))
                self.allInBlind(hand, 'PREFLOP', a, 'big blind')
            else:
                log.error("PacificPokerToFpdb.readBlinds (BB): '%s', '%s' not in hand.stacks" % (hand.handid, a.group('PNAME')))
                raise FpdbParseError
        for a in self.re_PostBoth.finditer(hand.handText):
            if a.group('PNAME') in hand.stacks:
                if Decimal(self.clearMoneyString(a.group('BB')))>0:
                    bb = self.clearMoneyString(a.group('BB'))
                    sb = self.clearMoneyString(a.group('SB'))
                    both = str(Decimal(bb) + Decimal(sb))
                    hand.addBlind(a.group('PNAME'), 'both', both)
                else:
                    hand.addBlind(a.group('PNAME'), 'secondsb', self.clearMoneyString(a.group('SB')))
                self.allInBlind(hand, 'PREFLOP', a, 'both')
            else:
                log.error("PacificPokerToFpdb.readBlinds (Both): '%s', '%s' not in hand.stacks" % (hand.handid, a.group('PNAME')))
                raise FpdbParseError

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
                    newcards = self.splitCards(found.group('NEWCARDS'))
                    hand.addHoleCards(street, hand.hero, closed=newcards, shown=False, mucked=False, dealt=True)

        for street, text in hand.streets.iteritems():
            if not text or street in ('PREFLOP', 'DEAL'): continue  # already done these
            m = self.re_HeroCards.finditer(hand.streets[street])
            for found in m:
                player = found.group('PNAME')
                if found.group('NEWCARDS') is None:
                    newcards = []
                else:
                    newcards = self.splitCards(found.group('NEWCARDS'))
                if found.group('OLDCARDS') is None:
                    oldcards = []
                else:
                    oldcards = self.splitCards(found.group('OLDCARDS'))

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
            if street not in ('PREFLOP', 'DEAL'):
                hand.setUncalledBets(False)
            #print "DEBUG: acts: %s" %acts
            bet = self.clearMoneyString(action.group('BET')) if action.group('BET') else None
            if action.group('PNAME') in hand.stacks:
                if action.group('ATYPE') == ' folds':
                    hand.addFold( street, action.group('PNAME'))
                elif action.group('ATYPE') == ' checks':
                    hand.addCheck( street, action.group('PNAME'))
                elif action.group('ATYPE') == ' calls':
                    hand.addCall( street, action.group('PNAME'), bet)
                elif action.group('ATYPE') == ' raises':
                    hand.addCallandRaise( street, action.group('PNAME'), bet)
                elif action.group('ATYPE') == ' bets':
                    hand.addBet( street, action.group('PNAME'), bet )
                elif action.group('ATYPE') == ' discards':
                    hand.addDiscard(street, action.group('PNAME'), bet, action.group('DISCARDED'))
                elif action.group('ATYPE') == ' stands pat':
                    hand.addStandsPat( street, action.group('PNAME'))
                else:
                    print (_("DEBUG:") + " " + _("Unimplemented %s: '%s' '%s'") % ("readAction", action.group('PNAME'), action.group('ATYPE')))
                
                if action.group('ATYPE') not in (' checks', ' folds'):
                    if not hand.allInBlind:
                        if not (hand.stacks[action.group('PNAME')]==0 and action.group('ATYPE') ==' calls' ):
                            hand.setUncalledBets(False)
                        if (hand.stacks[action.group('PNAME')]==0 and action.group('ATYPE') ==' raises' ):
                            hand.checkForUncalled = True
            else:
                log.error("PacificPokerToFpdb.readAction: '%s', '%s' not in hand.stacks" % (hand.handid, action.group('PNAME')))
                raise FpdbParseError
            
    def allInBlind(self, hand, street, action, actiontype):
        if street in ('PREFLOP', 'DEAL'):
            if hand.stacks[action.group('PNAME')]==0:
                if actiontype=='ante':
                    if action.group('PNAME') in [p for (p,b) in hand.posted]:
                        hand.setUncalledBets(False)
                        hand.checkForUncalled = True
                        hand.allInBlind = True
                elif actiontype in ('secondsb', 'big blind', 'both') and not self.re_Antes.search(hand.handText):
                    hand.setUncalledBets(False)
                    hand.checkForUncalled = True
                    hand.allInBlind = True

    def readShowdownActions(self, hand):
        # TODO: pick up mucks also??
        for shows in self.re_ShowdownAction.finditer(hand.handText):            
            cards = shows.group('CARDS').split(', ')
            hand.addShownCards(cards, shows.group('PNAME'))

    def readCollectPot(self,hand):
        for m in self.re_CollectPot.finditer(hand.handText):
            #print "DEBUG: hand.addCollectPot(player=", m.group('PNAME'), ", pot=", m.group('POT'), ")"
            hand.addCollectPot(player=m.group('PNAME'),pot=self.clearMoneyString(m.group('POT')))

    def readShownCards(self,hand):
        for m in self.re_ShownCards.finditer(hand.handText):
            if m.group('CARDS') is not None:
                cards = m.group('CARDS')
                cards = self.splitCards(cards)

                (shown, mucked) = (False, False)
                if m.group('SHOWED') == "shows": shown = True
                elif m.group('SHOWED') == "mucks": mucked = True

                #print "DEBUG: hand.addShownCards(%s, %s, %s, %s)" %(cards, m.group('PNAME'), shown, mucked)
                hand.addShownCards(cards=cards, player=m.group('PNAME'), shown=shown, mucked=mucked)
                
    def splitCards(self, cards):
        #Polish
        cards = cards.replace(u'Kreuz', 'c')
        cards = cards.replace(u'Karo', 'd')
        cards = cards.replace(u'Pik', 's')
        cards = cards.replace(u'Herz', 'h')
        cards = cards.replace(u'10', 'T')
        #Russian
        cards = cards.replace(u'\xd2', 'Q')
        cards = cards.replace(u'\xc2', 'A')
        cards = cards.replace(u'\xc4', 'J')
        #Spanish
        cards = self.re_Spanish_10.sub('T\g<1>', cards)
        cards = cards.replace(u't', 'h')
        cards = cards.replace(u'p', 's')
        cards = cards.replace(u'e', 'd')
        cards = cards.replace(u'o', 'h')
        #Dutch
        cards = cards.replace(u'B', 'J')
        cards = cards.replace(u'V', 'Q')
        cards = cards.replace(u'H', 'K')
        #Swedish
        cards = cards.replace(u'Kn', 'J')
        cards = cards.replace(u'D', 'Q')
        cards = cards.replace(u'E', 'A')
        cards = cards.split(', ')
        return cards

    @staticmethod
    def getTableTitleRe(type, table_name=None, tournament = None, table_number=None):
        # Tournament tables look like:
        # Tour NLH 50+5 Brouhaha ID #28353026 Table #7 Blinds: 200/400
        log.info("Pacific.getTableTitleRe: table_name='%s' tournament='%s' table_number='%s'" % (table_name, tournament, table_number))
        regex = "%s" % (table_name)
        if tournament:
            regex = "%s Table #%s" % (tournament, table_number)

        log.info("Pacific.getTableTitleRe: returns: '%s'" % (regex))
        return regex

    def readSummaryInfo(self, summaryInfoList):
        self.status = True
        return self.status
