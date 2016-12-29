#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

import sys
import exceptions

import Configuration
from HandHistoryConverter import *
from decimal_wrapper import Decimal

# OnGame HH Format

class OnGame(HandHistoryConverter):
    filter = "OnGame"
    filetype = "text"
    codepage = ("utf8", "cp1252")
    siteId   = 5 # Needs to match id entry in Sites database

    mixes = { } # Legal mixed games
    sym = {'USD': "\$", 'CAD': "\$", 'T$': "", "EUR": u"\u20ac", "GBP": "\xa3"}
    substitutions = {
                     'LEGAL_ISO' : "USD|EUR|GBP|CAD|FPP",    # legal ISO currency codes
                            'LS' : u"\$|\xe2\x82\xac|\u20ac|",     # Currency symbols - Euro(cp1252, utf-8)
                           'PLYR': r'(?P<PNAME>.+?)',
                            'CUR': u"(\$|\xe2\x82\xac|\u20ac||\£|)",
                           'NUM' : u".,\dKM",
                    }
    
    Lim_Blinds = {      '0.04': ('0.01', '0.02'),    '0.10': ('0.02', '0.05'),      
                        '0.20': ('0.05', '0.10'),    '0.30': ('0.07', '0.15'),
                        '0.50': ('0.12', '0.25'),
                        '1.00': ('0.25', '0.50'),       '1': ('0.25', '0.50'),
                        '2.00': ('0.50', '1.00'),       '2': ('0.50', '1.00'),
                        '4.00': ('1.00', '2.00'),       '4': ('1.00', '2.00'),
                        '6.00': ('1.50', '3.00'),       '6': ('1.50', '3.00'),
                        '8.00': ('2.00', '4.00'),       '8': ('2.00', '4.00'),
                       '10.00': ('2.50', '5.00'),      '10': ('2.50', '5.00'),
                       '12.00': ('3.00', '6.00'),      '12': ('3.00', '6.00'),
                       '20.00': ('5.00', '10.00'),     '20': ('5.00', '10.00'),
                       '30.00': ('7.50', '15.00'),     '30': ('7.50', '15.00'),
                       '40.00': ('10.00', '20.00'),    '40': ('10.00', '20.00'),
                       '50.00': ('12.50', '25.00'),    '50': ('12.50', '25.00'),
                      '100.00': ('25.00', '50.00'),   '100': ('25.00', '50.00'),
                      '200.00': ('50.00', '100.00'),  '200': ('50.00', '100.00'),
                      '500.00': ('125.00', '250.00'), '500': ('125.00', '250.00'),
                      '1000.00': ('250.00', '500.00'),'1000': ('250.00', '500.00'),
                  }
    
    currencies = { u'\u20ac':'EUR', u'\xe2\x82\xac':'EUR', '$':'USD', '':'T$' }

    limits = { 'NO_LIMIT':'nl', 'POT_LIMIT':'pl', 'LIMIT':'fl'}

    games = {                          # base, category
                          "TEXAS_HOLDEM" : ('hold','holdem'),
                              'OMAHA_HI' : ('hold','omahahi'),
                           'OMAHA_HI_LO' : ('hold','omahahilo'),
                                  'RAZZ' : ('stud','razz'),
                       'SEVEN_CARD_STUD' : ('stud','studhi'),
                 'SEVEN_CARD_STUD_HI_LO' : ('stud','studhilo'),
             #                  'Badugi' : ('draw','badugi'),
             # 'Triple Draw 2-7 Lowball' : ('draw','27_3draw'),
                        'FIVE_CARD_DRAW' : ('draw','fivedraw')
               }

    # Static regexes
    # ***** End of hand R5-75443872-57 *****
    re_Identify   = re.compile(u'\*{5}\sHistory\sfor\shand\s[A-Z0-9\-]+\s')
    re_SplitHands = re.compile(u'\*\*\*\*\*\sEnd\sof\shand\s[-A-Z\d]+.*\n+(?=\*)')

    #TODO: detect play money
    # "Play money" rather than "Real money" and set currency accordingly
    # Table:\s(\[SPEED\]\s)?(?P<TABLE>[-\'\w\#\s\.]+)\s\[\d+\]\s\( 
    re_HandInfo = re.compile(u"""
            \*{5}\sHistory\sfor\shand\s(?P<HID>[-A-Z\d]+)(?P<TOUR>\s\(TOURNAMENT:(\s\"(?P<NAME>.+?)\",)?\s(?P<TID>[-A-Z\d]+)?(?P<BUY>,\sbuy-in:\s(?P<BUYINCUR>[%(LS)s]?)(?P<BUYIN>[%(NUM)s]+))?\))?\s\*{5}\s?
            Start\shand:\s(?P<DATETIME>.+?)\s?
            Table:\s(\[SPEED\]\s)?(?P<TABLE>.+?)\s\[(?P<TABLENO>\d+)\]\s\( 
            (
            (?P<LIMIT>NO_LIMIT|Limit|LIMIT|Pot\sLimit|POT_LIMIT)\s
            (?P<GAME>TEXAS_HOLDEM|OMAHA_HI|OMAHA_HI_LO|SEVEN_CARD_STUD|SEVEN_CARD_STUD_HI_LO|RAZZ|FIVE_CARD_DRAW)\s
            (?P<CURRENCY>%(LS)s|)?(?P<SB>[%(NUM)s]+)/(%(LS)s)?(?P<BB>[%(NUM)s]+),\s(ante:\s(%(LS)s)?[%(NUM)s]+,\s)?
            (?P<MONEY>Play\smoney|Real\smoney|TC|Chips)?\)
            )
            """ % substitutions, re.MULTILINE|re.DOTALL|re.VERBOSE)

    re_TailSplitHands = re.compile(u'(\*\*\*\*\*\sEnd\sof\shand\s[-A-Z\d]+.*\n)(?=\*)')
    re_Button       = re.compile('Button: seat (?P<BUTTON>\d+)', re.MULTILINE)  # Button: seat 2
    re_Board        = re.compile(r"\[(?P<CARDS>.+)\]")
    re_Max          = re.compile(r"Players\sin\sround:\s\d+\s\((?P<MAX>\d+)\)")

    # Wed Aug 18 19:45:30 GMT+0100 2010
    re_DateTime = re.compile("""
            [a-zA-Z]{3}\s
            (?P<M>[a-zA-Z]{3})\s
            (?P<D>[0-9]+)\s
            (?P<H>[0-9]+):(?P<MIN>[0-9]+):(?P<S>[0-9]+)\s
            (?P<OFFSET>\w+([-+]\d+)?)\s
            (?P<Y>[0-9]{4})
            """, re.MULTILINE|re.VERBOSE)
        
    #Seat 1: .Lucchess ($4.17 in chips) 
    #Seat 1: phantomaas ($27.11)
    #Seat 5: mleo17 ($9.37)
    #Seat 2: Montferat (1500)
    re_PlayerInfo = re.compile(u'Seat (?P<SEAT>[0-9]+):\s(?P<PNAME>.*)\s\((%(LS)s)?(?P<CASH>[%(NUM)s]+)\)' % substitutions)

    def compilePlayerRegexs(self, hand):
        players = set([player[1] for player in hand.players])
        if not players <= self.compiledPlayers: # x <= y means 'x is subset of y'
            # we need to recompile the player regexs.
# TODO: should probably rename re_HeroCards and corresponding method,
#    since they are used to find all cards on lines starting with "Dealt to:"
#    They still identify the hero.
            self.compiledPlayers = players

            #ANTES/BLINDS
            #helander2222 posts blind ($0.25), lopllopl posts blind ($0.50).
            #player_re = "(?P<PNAME>" + "|".join(map(re.escape, players)) + ")"
            #subst = {'PLYR': player_re, 'CUR': self.sym[hand.gametype['currency']]}
            self.re_PostSB    = re.compile('%(PLYR)s posts small blind \((%(CUR)s)?(?P<SB>[%(NUM)s]+)\)' % self.substitutions, re.MULTILINE)
            self.re_PostBB    = re.compile('%(PLYR)s posts big blind \((%(CUR)s)?(?P<BB>[%(NUM)s]+)\)' % self.substitutions, re.MULTILINE)
            self.re_Antes     = re.compile(r"^%(PLYR)s posts ante (%(CUR)s)?(?P<ANTE>[%(NUM)s]+)" % self.substitutions, re.MULTILINE)
            self.re_BringIn   = re.compile(r"^%(PLYR)s (small|big) bring in (%(CUR)s)?(?P<BRINGIN>[%(NUM)s]+)" % self.substitutions, re.MULTILINE)
            self.re_PostBoth  = re.compile('%(PLYR)s posts small \& big blind \( (%(CUR)s)?(?P<SBBB>[%(NUM)s]+)\)' % self.substitutions)
            self.re_PostDead  = re.compile('%(PLYR)s posts dead blind \((%(CUR)s)?(?P<DEAD>[%(NUM)s]+)\)' % self.substitutions, re.MULTILINE)
            self.re_HeroCards = re.compile('(New\shand\sfor|Dealing\sto)\s%(PLYR)s:\s\[(?P<CARDS>.*)\]' % self.substitutions)

            self.re_Action = re.compile('(, )?%(PLYR)s(?P<ATYPE> bets| checks| raises| calls| folds| changed)( (%(CUR)s)?(?P<BET>[%(NUM)s]+))?( to (%(CUR)s)?(?P<BET2>[%(NUM)s]+))?( and is all-in)?' % self.substitutions)
            #self.re_Board = re.compile(r"\[board cards (?P<CARDS>.+) \]")

            #Uchilka shows [ KC,JD ]
            self.re_ShowdownAction = re.compile('%(PLYR)s shows \[ (?P<CARDS>.+) \]' % self.substitutions)

            #Main pot: $3.57 won by mleo17 ($3.40)
            #Side pot 1: $3.26 won by maac_5 ($3.10)
            #Main pot: $2.87 won by maac_5 ($1.37), sagi34 ($1.36)
            self.re_Pot = re.compile('(Main|Side)\spot(\s\d+)?:\s.*won\sby(?P<POT>.*$)', re.MULTILINE)
            self.re_CollectPot = re.compile('\s(?P<PNAME>.+?)\s\((%(CUR)s)?(?P<POT>[%(NUM)s]+)(\s(High|Low))?\)' % self.substitutions)
            #Seat 5: mleo17 ($3.40), net: +$2.57, [Jd, Qd] (TWO_PAIR QUEEN, JACK)
            self.re_ShownCards = re.compile("^Seat (?P<SEAT>[0-9]+): (?P<PNAME>.*) \(.*\), net:.* \[(?P<CARDS>.*)\].*" % self.substitutions, re.MULTILINE)
            self.re_sitsOut    = re.compile('%(PLYR)s sits out' % self.substitutions, re.MULTILINE)

    def readSupportedGames(self):
        return [["ring", "hold", "nl"],
                ["ring", "hold", "pl"],
                ["ring", "hold", "fl"],

                ["ring", "stud", "fl"],

                ["ring", "draw", "fl"],
                ["ring", "draw", "pl"],
                ["ring", "draw", "nl"],

                ["tour", "hold", "nl"],
                ["tour", "hold", "pl"],
                ["tour", "hold", "fl"],

                ["tour", "stud", "fl"],
                
                ["tour", "draw", "fl"],
                ["tour", "draw", "pl"],
                ["tour", "draw", "nl"],
                ]

    def determineGameType(self, handText):
        # Inspect the handText and return the gametype dict
        # gametype dict is: {'limitType': xxx, 'base': xxx, 'category': xxx}
        info = {}
        m = self.re_HandInfo.search(handText)
        if not m:
            tmp = handText[0:200]
            log.error(_("OnGameToFpdb.determineGameType: '%s'") % tmp)
            raise FpdbParseError

        mg = m.groupdict()
        #print "DEBUG: mg: %s" % mg

        info['type'] = 'ring'
        if mg['TOUR'] != None:
            if mg['TID'] != None:
                info['type'] = 'tour'
            else:
                raise FpdbHandPartial

        if 'CURRENCY' in mg and mg['CURRENCY'] != None:
            if 'MONEY' in mg and mg['MONEY']=='Play money':
                info['currency'] = 'play'
            else:
                info['currency'] = self.currencies[mg['CURRENCY']]

        if 'LIMIT' in mg:
            if mg['LIMIT'] in self.limits:
                info['limitType'] = self.limits[mg['LIMIT']]
            else:
                tmp = handText[0:200]
                log.error(_("OnGameToFpdb.determineGameType: Limit not found in '%s'") % tmp)
                raise FpdbParseError
        if 'GAME' in mg:
            (info['base'], info['category']) = self.games[mg['GAME']]
        if 'SB' in mg:
            info['sb'] = self.clearMoneyString(mg['SB'])
        if 'BB' in mg:
            info['bb'] = self.clearMoneyString(mg['BB'])
        if 'Strobe' in mg['TABLE']:
            info['fast'] = True
        else:
            info['fast'] = False

        if info['limitType'] == 'fl' and info['bb'] is not None:
            if info['type'] == 'ring':
                try:
                    bb = self.clearMoneyString(mg['BB'])
                    info['sb'] = self.Lim_Blinds[bb][0]
                    info['bb'] = self.Lim_Blinds[bb][1]
                except KeyError:
                    tmp = handText[0:200]
                    log.error(_("OnGameToFpdb.determineGameType: Lim_Blinds has no lookup for '%s' - '%s'") % (bb, tmp))
                    raise FpdbParseError
            else:
                sb = self.clearMoneyString(mg['SB'])
                info['sb'] = str((Decimal(sb)/2).quantize(Decimal("0.01")))
                info['bb'] = str(Decimal(sb).quantize(Decimal("0.01")))    
        return info

    def readHandInfo(self, hand):
        info = {}
        m =  self.re_HandInfo.search(hand.handText)
        if m is None:
            tmp = hand.handText[0:200]
            log.error(_("OnGameToFpdb.readHandInfo: '%s'") % tmp)
            raise FpdbParseError

        info.update(m.groupdict())
        m2 =  self.re_Max.search(hand.handText)
        if m2 is not None:
            info.update(m2.groupdict())
        #log.debug("readHandInfo: %s" % info)
        for key in info:
            if key == 'DATETIME':
                #'Wed Aug 18 19:45:30 GMT+0100 2010
                # %a   %b %d %H:%M:%S     %z   %Y
                #hand.startTime = time.strptime(m.group('DATETIME'), "%a %b %d %H:%M:%S GMT%z %Y")
                # Stupid library doesn't seem to support %z (http://docs.python.org/library/time.html?highlight=strptime#time.strptime)
                # So we need to re-interpret te string to be useful
                a = self.re_DateTime.search(info[key])
                if a:
                    datetimestr = "%s/%s/%s %s:%s:%s" % (a.group('Y'),a.group('M'), a.group('D'), a.group('H'),a.group('MIN'),a.group('S'))
                    tzoffset = a.group('OFFSET')
                else:
                    datetimestr = "2010/Jan/01 01:01:01"
                    log.error("OnGameToFpdb.readHandInfo: " + _("DATETIME not matched: '%s'") % info[key])
                    raise FpdbParseError
                    #print (_("DEBUG:") + " readHandInfo: " + _("DATETIME not matched: '%s'") % info[key])
                # TODO: Manually adjust time against OFFSET
                hand.startTime = datetime.datetime.strptime(datetimestr, "%Y/%b/%d %H:%M:%S") # also timezone at end, e.g. " ET"
                hand.startTime = HandHistoryConverter.changeTimezone(hand.startTime, tzoffset, "UTC")
            if key == 'HID':
                hand.handid = info[key]
                # Need to remove non-alphanumerics for MySQL
                hand.handid = hand.handid.replace('T','')
                hand.handid = hand.handid.replace('R','')
                hand.handid = hand.handid.replace('-','')
            if key == 'TID':
                hand.tourNo = info[key]
                if hand.tourNo:
                    hand.tourNo = hand.tourNo.replace('T','')
                    hand.tourNo = hand.tourNo.replace('S','')
                    hand.tourNo = hand.tourNo.replace('R','')
                    hand.tourNo = hand.tourNo.replace('O','')
                    hand.tourNo = hand.tourNo.replace('-','')
            if key == 'BUYIN':
                if info[key] is not None:
                    hand.buyin = int(100*Decimal(self.clearMoneyString(info[key])))
                    hand.fee = int(hand.buyin - hand.buyin/1.1)
                    hand.buyin -= hand.fee
                else:
                    hand.buyin = 0
                    hand.fee = 0
            if key == 'BUYINCUR':
                if info[key] is not None:
                    hand.buyinCurrency = self.currencies[info[key]]
                    if hand.buyin == 0:
                        hand.buyinCurrency = 'FREE'
                else:
                    hand.buyinCurrency = 'NA'
            if key == 'TABLE' and not info['TOUR']:
                hand.tablename = info[key]
            if key == 'TABLENO' and info['TOUR']:
                hand.tablename = info[key]
            if key == 'MAX':
                hand.maxseats = int(info[key])
            if key == 'BUTTON':
                hand.buttonpos = info[key]
        
        if hand.gametype['fast']:
            hand.isFast = True

    def readPlayerStacks(self, hand):
        #log.debug("readplayerstacks: re is '%s'" % self.re_PlayerInfo)
        head = re.split(re.compile('Summary:'),  hand.handText)
        m = self.re_PlayerInfo.finditer(head[0])
        for a in m:
            hand.addPlayer(int(a.group('SEAT')), a.group('PNAME'), self.clearMoneyString(a.group('CASH')))

    def markStreets(self, hand):
        if hand.gametype['base'] in ("hold"):
            m =  re.search(r"pocket cards(?P<PREFLOP>.+?(?= Dealing flop )|.+(?=Summary))"
                       r"( Dealing flop (?P<FLOP>\[\S\S, \S\S, \S\S\].+?(?= Dealing turn)|.+(?=Summary)))?"
                       r"( Dealing turn (?P<TURN>\[\S\S\].+?(?= Dealing river)|.+(?=Summary)))?"
                       r"( Dealing river (?P<RIVER>\[\S\S\].+?(?=Summary)))?", hand.handText, re.DOTALL)
        elif hand.gametype['base'] in ("stud"):
            m =  re.search(r"(?P<ANTES>.+(?=Dealing pocket cards)|.+)"
                           r"(Dealing pocket cards(?P<THIRD>.+?(?=Dealing 4th street)|.+))?"
                           r"(Dealing 4th street(?P<FOURTH>.+?(?=Dealing 5th street)|.+))?"
                           r"(Dealing 5th street(?P<FIFTH>.+?(?=Dealing 6th street)|.+))?"
                           r"(Dealing 6th street(?P<SIXTH>.+?(?=Dealing river)|.+))?"
                           r"(Dealing river(?P<SEVENTH>.+))?", hand.handText,re.DOTALL)
        elif hand.gametype['base'] in ("draw"):
            # isolate the first discard/stand pat line
            discard_split = re.split(r"(?:(.+(?: changed).+))", hand.handText,re.DOTALL)
            if len(hand.handText) == len(discard_split[0]):
                # handText was not split, no DRAW street occurred
                pass
            else:
                # DRAW street found, reassemble, with DRAW marker added
                discard_split[0] += "*** DRAW ***\r\n"
                hand.handText = ""
                for i in discard_split:
                    hand.handText += i
            m =  re.search(r"(?P<PREDEAL>.+(?=Dealing pocket cards)|.+)"
                           r"(Dealing pocket cards(?P<DEAL>.+(?=\*\*\* DRAW \*\*\*)|.+))?"
                           r"(\*\*\* DRAW \*\*\*(?P<DRAWONE>.+))?", hand.handText,re.DOTALL)
        #import pprint
        #pprint.pprint(m.groupdict())

        hand.addStreets(m)

    #Needs to return a list in the format
    # ['player1name', 'player2name', ...] where player1name is the sb and player2name is bb,
    # addtional players are assumed to post a bb oop

    def readButton(self, hand):
        m = self.re_Button.search(hand.handText)
        if m:
            hand.buttonpos = int(m.group('BUTTON'))
        else:
            log.info('readButton: ' + _('not found'))

#    def readCommunityCards(self, hand, street):
#        #print hand.streets.group(street)
#        if street in ('FLOP','TURN','RIVER'):   # a list of streets which get dealt community cards (i.e. all but PREFLOP)
#            m = self.re_Board.search(hand.streets.group(street))
#            hand.setCommunityCards(street, m.group('CARDS').split(','))

    def readCommunityCards(self, hand, street): # street has been matched by markStreets, so exists in this hand
        if street in ('FLOP','TURN','RIVER'):   # a list of streets which get dealt community cards (i.e. all but PREFLOP)
            #print "DEBUG readCommunityCards:", street, hand.streets.group(street)
            m = self.re_Board.search(hand.streets[street])
            hand.setCommunityCards(street, m.group('CARDS').split(', '))

    def readBlinds(self, hand):
        try:
            for a in self.re_PostSB.finditer(hand.handText):
                hand.addBlind(a.group('PNAME'), 'small blind', self.clearMoneyString(a.group('SB')))
        except exceptions.AttributeError: # no small blind
            log.debug( _("No small blinds found.")+str(sys.exc_info()) )
            #hand.addBlind(None, None, None)
        for a in self.re_PostBB.finditer(hand.handText):
            hand.addBlind(a.group('PNAME'), 'big blind', self.clearMoneyString(a.group('BB')))
        for a in self.re_PostDead.finditer(hand.handText):
            #print "DEBUG: Found dead blind: addBlind(%s, 'secondsb', %s)" %(a.group('PNAME'), a.group('DEAD'))
            hand.addBlind(a.group('PNAME'), 'secondsb', self.clearMoneyString(a.group('DEAD')))
        for a in self.re_PostBoth.finditer(hand.handText):
            hand.addBlind(a.group('PNAME'), 'small & big blinds', self.clearMoneyString(a.group('SBBB')))

    def readAntes(self, hand):
        log.debug(_("reading antes"))
        m = self.re_Antes.finditer(hand.handText)
        for player in m:
            #~ log.debug("hand.addAnte(%s,%s)" %(player.group('PNAME'), player.group('ANTE')))
            hand.addAnte(player.group('PNAME'), self.clearMoneyString(player.group('ANTE')))
    
    def readBringIn(self, hand):
        m = self.re_BringIn.search(hand.handText,re.DOTALL)
        if m:
            #~ log.debug("readBringIn: %s for %s" %(m.group('PNAME'),  m.group('BRINGIN')))
            hand.addBringIn(m.group('PNAME'),  self.clearMoneyString(m.group('BRINGIN')))

    def readHoleCards(self, hand):
        # streets PREFLOP, PREDRAW, and THIRD are special cases beacause
        # we need to grab hero's cards
        for street in ('PREFLOP', 'DEAL'):
            if street in hand.streets.keys():
                m = self.re_HeroCards.finditer(hand.streets[street])
                for found in m:
                    hand.hero = found.group('PNAME')
                    newcards = found.group('CARDS').split(', ')
                    hand.addHoleCards(street, hand.hero, closed=newcards, shown=False, mucked=False, dealt=True)
                    
        for street in hand.holeStreets:
            if hand.streets.has_key(street):
                if not hand.streets[street] or street in ('PREFLOP', 'DEAL') or hand.gametype['base'] == 'hold': continue  # already done these
                m = self.re_HeroCards.finditer(hand.streets[street])
                for found in m:
                    player = found.group('PNAME')
                    newcards = [c for c in found.group('CARDS').split(', ') if c != u'-']
    
                    if street == 'THIRD' and len(newcards) == 3: # hero in stud game
                        hand.hero = player
                        hand.dealt.add(player) # need this for stud??
                        hand.addHoleCards(street, player, closed=newcards[0:2], open=[newcards[2]], shown=False, mucked=False, dealt=False)
                    else:
                        hand.addHoleCards(street, player, open=newcards, shown=False, mucked=False, dealt=False)

    def readAction(self, hand, street):
        m = self.re_Action.finditer(hand.streets[street])
        for action in m:
            #acts = action.groupdict()
            #print "readaction: acts: %s" %acts
            bet = self.clearMoneyString(action.group('BET')) if action.group('BET') else None
            bet2 = self.clearMoneyString(action.group('BET2')) if action.group('BET2') else None
            
            if action.group('ATYPE') == ' folds':
                hand.addFold( street, action.group('PNAME'))
            elif action.group('ATYPE') == ' checks':
                hand.addCheck( street, action.group('PNAME'))
            elif action.group('ATYPE') == ' calls':
                hand.addCall( street, action.group('PNAME'), bet )
            elif action.group('ATYPE') == ' raises':
                hand.addRaiseTo( street, action.group('PNAME'), bet2 )
            elif action.group('ATYPE') == ' bets':
                hand.addBet( street, action.group('PNAME'), bet )
            elif action.group('ATYPE') == ' changed':
                if int(action.group('BET'))>0:
                    hand.addDiscard(street, action.group('PNAME'), bet)
                else:
                    hand.addStandsPat( street, action.group('PNAME'))
            else:
                print (_("DEBUG:") + " " + _("Unimplemented %s: '%s' '%s'") % ("readAction", action.group('PNAME'), action.group('ATYPE')))

    def readShowdownActions(self, hand):
        for shows in self.re_ShowdownAction.finditer(hand.handText):
            cards = shows.group('CARDS')
            cards = set(cards.split(','))
            hand.addShownCards(cards, shows.group('PNAME'))

    def readCollectPot(self,hand):
        for m in self.re_Pot.finditer(hand.handText):
            for m in self.re_CollectPot.finditer(m.group('POT')):
                hand.addCollectPot(player=m.group('PNAME'),pot=self.clearMoneyString(m.group('POT')))

    def readShownCards(self,hand):
        for m in self.re_ShownCards.finditer(hand.handText):
            cards = m.group('CARDS')
            cards = cards.split(', ') # needs to be a list, not a set--stud needs the order

            (shown, mucked) = (False, False)
            if m.group('CARDS') is not None:
                shown = True
                hand.addShownCards(cards=cards, player=m.group('PNAME'), shown=shown, mucked=mucked)

    @staticmethod
    def getTableTitleRe(type, table_name=None, tournament = None, table_number=None):
        "Returns string to search in windows titles"
        regex = re.escape(str(table_name))
        if type=="tour":
            regex = "%s" % table_number
        log.info("OnGame.getTableTitleRe: table_name='%s' tournament='%s' table_number='%s'" % (table_name, tournament, table_number))
        log.info("OnGame.getTableTitleRe: returns: '%s'" % (regex))
        return regex
