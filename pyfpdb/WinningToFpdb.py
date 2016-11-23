#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Copyright 2016, Chaz Littlejohn
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

# Winning HH Format

class Winning(HandHistoryConverter):

    # Class Variables

    sitename = "Winning"
    filetype = "text"
    codepage = ("utf-16", "utf8", "cp1252")
    siteId   = 24 # Needs to match id entry in Sites database
    sym = {
        'USD': "\$", 
        'T$': "", 
        "play": ""
    } 
    substitutions = {
        'LEGAL_ISO' : "USD|TB|CP",      # legal ISO currency codes
        'LS' : u"\$|", # legal currency symbols - Euro(cp1252, utf-8)
        'PLYR': r'(?P<PNAME>.+?)',
        'NUM' :u".,\dK",
    }
    games = {# base, category
        "Hold'em" : ('hold','holdem'),
        'Omaha' : ('hold','omahahi'),
        'Omaha HiLow' : ('hold','omahahilo'),
        'Seven Cards Stud' : ('stud','studhi'),
        'Seven Cards Stud HiLow' : ('stud','studhilo')
    }    
    speeds = {
        'Turbo': 'Turbo',
        'Hyper Turbo': 'Hyper',
        'Regular': 'Normal'
    }
    buyin = {
        'CAP': 'cap',
        'Short': 'shallow'
    }
    
    SnG_Fee = {  
        50: {'Hyper': 0, 'Turbo': 0, 'Normal': 5},
        100: {'Hyper': 0, 'Turbo': 0, 'Normal': 10},
        150: {'Hyper': 11, 'Turbo': 12, 'Normal': 15},
        300: {'Hyper': 20, 'Turbo': 25, 'Normal': 30},
        500: {'Hyper': 30, 'Turbo': 45, 'Normal': 50},
        1000: {'Hyper': 55, 'Turbo': 90, 'Normal': 100},
        1500: {'Hyper': 80, 'Turbo': 140, 'Normal': 150},
        2000: {'Hyper': 100, 'Turbo': 175, 'Normal': 200},
        3000: {'Hyper': 130, 'Turbo': 275, 'Normal': 300},
        5000: {'Hyper': 205, 'Turbo': 475, 'Normal': 500},
        8000: {'Hyper': 290, 'Turbo': 650, 'Normal': 800},
        10000: {'Hyper': 370, 'Turbo': 800, 'Normal': 900}
    }
    
    HUSnG_Fee = {
        200: {'Hyper': 10, 'Turbo': 0, 'Normal': 17},
        220: {'Hyper': 0, 'Turbo': 16, 'Normal': 0},
        240: {'Hyper': 10, 'Turbo': 0, 'Normal': 0},
        500: {'Hyper': 0, 'Turbo': 0, 'Normal': 25},
        550: {'Hyper': 0, 'Turbo': 25, 'Normal': 0},
        600: {'Hyper': 18, 'Turbo': 0, 'Normal': 0},
        1000: {'Hyper': 25, 'Turbo': 0, 'Normal': 50},
        1100: {'Hyper': 0, 'Turbo': 50, 'Normal': 0},
        1200: {'Hyper': 25, 'Turbo': 0, 'Normal': 0},
        2000: {'Hyper': 50, 'Turbo': 0, 'Normal': 100},
        2200: {'Hyper': 0, 'Turbo': 100, 'Normal': 0},
        2400: {'Hyper': 50, 'Turbo': 0, 'Normal': 0},
        3000: {'Hyper': 70, 'Turbo': 0, 'Normal': 150},
        3300: {'Hyper': 0, 'Turbo': 150, 'Normal': 0},
        3600: {'Hyper': 75, 'Turbo': 0, 'Normal': 0},
        5000: {'Hyper': 100, 'Turbo': 0, 'Normal': 250},
        5500: {'Hyper': 0, 'Turbo': 250, 'Normal': 0},
        6000: {'Hyper': 125, 'Turbo': 0, 'Normal': 0},
        10000: {'Hyper': 200, 'Turbo': 0, 'Normal': 450},
        11000: {'Hyper': 0, 'Turbo': 450, 'Normal': 0},
        12000: {'Hyper': 225, 'Turbo': 0, 'Normal': 0},
        15000: {'Hyper': 266, 'Turbo': 0, 'Normal': 0},
        20000: {'Hyper': 400, 'Turbo': 0, 'Normal': 900},
        22000: {'Hyper': 0, 'Turbo': 900, 'Normal': 0},
        24000: {'Hyper': 450, 'Turbo': 0, 'Normal': 0},
        30000: {'Hyper': 600, 'Turbo': 0, 'Normal': 1200},
        33000: {'Hyper': 0, 'Turbo': 1200, 'Normal': 0},
        36000: {'Hyper': 600, 'Turbo': 0, 'Normal': 0},
        40000: {'Hyper': 800, 'Turbo': 0, 'Normal': 0},
        50000: {'Hyper': 0, 'Turbo': 0, 'Normal': 5000},
        55000: {'Hyper': 0, 'Turbo': 2000, 'Normal': 0},
        60000: {'Hyper': 1000, 'Turbo': 0, 'Normal': 0},
        110000: {'Hyper': 0, 'Turbo': 3000, 'Normal': 0},
        120000: {'Hyper': 1500, 'Turbo': 0, 'Normal': 0}
    }
    
    re_GameInfo = re.compile(u"""
        Game\sID:\s\d+\s
        (?P<SB>[%(NUM)s]+)/(?P<BB>[%(NUM)s]+)\s
        (?P<TABLE>.+?)\s
        \((?P<GAME>Hold\'em|Omaha|Omaha\sHiLow|Seven\sCards\sStud|Seven\sCards\sStud\sHiLow)\)$
        """ % substitutions, 
        re.MULTILINE|re.VERBOSE
    )
    
    #Seat 6: puccini (5.34).
    re_PlayerInfo = re.compile(u"""
        ^Seat\s(?P<SEAT>[0-9]+):\s
        (?P<PNAME>.*)\s
        \((?P<CASH>[%(NUM)s]+)\)
        \.$
        """ % substitutions, 
        re.MULTILINE|re.VERBOSE
    )
    
    re_HandInfo = re.compile("""
        Game\sID:\s(?P<HID>\d+)\s
        [%(NUM)s]+/[%(NUM)s]+\s
        (?P<TABLE>.+?)\s
        \(.+?\)$    
        """ % substitutions,  
        re.MULTILINE|re.VERBOSE
    )    
    
    re_DateTime = re.compile("""
        ^Game\sstarted\sat:\s
        (?P<Y>[0-9]{4})/(?P<M>[0-9]{1,2})/(?P<D>[0-9]{1,2})\s
        (?P<H>[0-9]+):(?P<MIN>[0-9]+):(?P<S>[0-9]+)
        $""", 
        re.MULTILINE|re.VERBOSE
    )
    
    #$2.20 Turbo Heads-up, Table 1
    #$2.40 Hyper Turbo Heads-up, Table 1
    #$10 Freeroll - On Demand, Table 13
    #$25 GTD - On Demand, Table 1
    #$5 Regular 9-Max, Table 1 (Hold'em)
        
    re_Table = re.compile(u"""
        ^(?P<CURRENCY>[%(LS)s]|)?(?P<BUYIN>[%(NUM)s]+)\s
        ((?P<GAME>Holdem|PLO|PLO8|Omaha\sHi/Lo|Omaha|PL\sOmaha|PL\sOmaha\sHi/Lo|PLO\sHi/Lo)\s?)?
        ((?P<SPECIAL>(GTD|Freeroll|FREEBUY|Freebuy))\s?)?
        ((?P<SPEED>(Turbo|Hyper\sTurbo|Regular))\s?)?
        ((?P<MAX>(\d+\-Max|Heads\-up|Heads\-Up))\s?)?
        (?P<OTHER>.*?)
        ,\sTable\s(?P<TABLENO>\d+)
        """ % substitutions,  
        re.VERBOSE|re.MULTILINE
    )
    
    re_TourneyName = re.compile(u"(?P<TOURNAME>.*),\sTable\s\d+")    
    re_buyinType    = re.compile("\((?P<BUYINTYPE>CAP|Short)\)", re.MULTILINE)

    re_Identify     = re.compile(u'Game\sID:\s\d+')
    re_SplitHands   = re.compile('\n\n')
    re_Button       = re.compile('Seat (?P<BUTTON>\d+) is the button')
    re_Board        = re.compile(r"\[(?P<CARDS>.+)\]")    
    re_TourNo       = re.compile("\sT(?P<TOURNO>\d+)\-")
    re_File         = re.compile("HH\d{8}\s(T\d+\-)?G\d+")
    
    re_PostSB       = re.compile(r"^Player %(PLYR)s has small blind \((?P<SB>[%(NUM)s]+)\)" %  substitutions, re.MULTILINE)
    re_PostBB       = re.compile(r"^Player %(PLYR)s has big blind \((?P<BB>[%(NUM)s]+)\)" %  substitutions, re.MULTILINE)
    re_Posts        = re.compile(r"^Player %(PLYR)s posts \((?P<SBBB>[%(NUM)s]+)\)" %  substitutions, re.MULTILINE)
    re_Antes        = re.compile(r"^Player %(PLYR)s (posts )?ante \((?P<ANTE>[%(NUM)s]+)\)" % substitutions, re.MULTILINE)
    re_BringIn      = re.compile(r"^Player %(PLYR)s bring in \((?P<BRINGIN>[%(NUM)s]+)\)" % substitutions, re.MULTILINE)
    re_HeroCards    = re.compile(r"^Player %(PLYR)s received card: \[(?P<CARD>.+)\]" %  substitutions, re.MULTILINE)
    
    re_Action       = re.compile(r"""
        ^Player\s(%(PLYR)s)?\s(?P<ATYPE>bets|checks|raises|calls|folds|allin|straddle|caps)
        (\s\((?P<BET>[%(NUM)s]+)\))?
        $""" %  substitutions, 
        re.MULTILINE|re.VERBOSE
    )
    
    #Player lessthanrocko shows: Two pairs. 8s and 5s [3s 3h]. Bets: 420. Collects: 0. Loses: 420.
    #*Player ChazDazzle shows: Full House (5/8) [7s 5s]. Bets: 420. Collects: 840. Wins: 420.
    #*Player fullstacker shows: Flush, A high [2s 8h 2h Jd] Low hand (A A 2 3 4 8 ).Bets: 0.50. Collects: 0.95. Wins: 0.45.
    
    #*Player ChazDazzle shows: High card A [6h 10d 2c As 7d 4d 9s] Low hand (A A 2 4 6 7 ).Bets: 3.55. Collects: 3.53. Loses: 0.02.
    #*Player KickAzzJohnny shows: Two pairs. 8s and 3s [5d 3d 3s 6s 8s 8h Ad]. Bets: 3.55. Collects: 3.52. Loses: 0.03.
    
    re_ShownCards       = re.compile(r"""
        ^\*?Player\s%(PLYR)s\sshows:\s
        (?P<STRING>.+?)\s
        \[(?P<CARDS>.*)\]
        (\sLow\shand\s\((?P<STRING2>.+?)\s?\))?
        \.""" %  substitutions, 
        re.MULTILINE|re.VERBOSE
    )
    
    re_CollectPot = re.compile(r"""
        ^\*?Player\s%(PLYR)s\s
        (does\snot\sshow|shows|mucks)
        .+?\.\s?
        Bets:\s[%(NUM)s]+\.\s
        Collects:\s(?P<POT>[%(NUM)s]+)\.\s
        (Wins|Loses):\s[%(NUM)s]+\.
        $""" %  substitutions, 
        re.MULTILINE|re.VERBOSE
    )
    
    def compilePlayerRegexs(self,  hand):
        pass

    def readSupportedGames(self):
        return [
            ["ring", "hold", "nl"],
            ["ring", "hold", "fl"],
            ["ring", "hold", "pl"],

            ["ring", "stud", "fl"],
            
            ["tour", "hold", "nl"],
            ["tour", "hold", "fl"],
            ["tour", "hold", "pl"],
            
            ["tour", "stud", "fl"]
        ]

    def determineGameType(self, handText):
        info = {}
        if not self.re_File.search(self.in_path):
            tmp = "Invalid filename: %s" % self.in_path
            log.debug(_("WinningToFpdb.determineGameType: '%s'") % tmp)
            raise FpdbHandPartial(tmp)
            
        m = self.re_GameInfo.search(handText)
        if not m:
            tmp = handText[0:200]
            log.error(_("WinningToFpdb.determineGameType: '%s'") % tmp)
            raise FpdbParseError

        mg = m.groupdict()
        m1 = self.re_TourNo.search(self.in_path)
        if m1: mg.update(m1.groupdict())
        
        if 'GAME' in mg:
            (info['base'], info['category']) = self.games[mg['GAME']]
        if 'SB' in mg:
            info['sb'] = mg['SB']
        if 'BB' in mg:
            info['bb'] = mg['BB']
            
        if info['base'] == 'stud':
            info['limitType'] = 'fl'
        else:
            m2 = self.re_PostBB.search(handText)
            if m2:
                bb = self.clearMoneyString(m2.group('BB'))
                if Decimal(self.clearMoneyString(info['sb'])) == Decimal(bb):
                    info['limitType'] = 'fl'
            
            if info.get('limitType') == None:
                if 'omaha' in info['category']:
                    info['limitType'] = 'pl'
                else:
                    info['limitType'] = 'nl'
                
        if 'TOURNO' in mg and mg['TOURNO'] is not None:
            info['type'] = 'tour'
        else:
            info['type'] = 'ring'
            
        if 'TABLE' in mg:
            if re.match('PM\s',mg['TABLE']):
                info['currency'] = 'play'
            elif info['type'] == 'tour':
                info['currency'] = 'T$'
            else:
                info['currency'] = 'USD'
        
        if '(Cap)' in mg['TABLE']:
            info['buyinType'] = 'cap'
        elif '(Short)' in mg['TABLE']:
            info['buyinType'] = 'shallow'
        else:
            info['buyinType'] = 'regular'

        if info['limitType'] == 'fl' and info['bb'] is not None:
            info['sb'] = str((Decimal(mg['SB'])/2).quantize(Decimal("0.01")))
            info['bb'] = str(Decimal(mg['SB']).quantize(Decimal("0.01")))    

        return info

    def readHandInfo(self, hand):
        #First check if partial
        if hand.handText.count('------ Summary ------')!=1:
            raise FpdbHandPartial(_("Hand is not cleanly split into pre and post Summary"))
        
        info = {}
        m  = self.re_HandInfo.search(hand.handText)
        m2 = self.re_DateTime.search(hand.handText)
        if m is None or m2 is None:
            tmp = hand.handText[0:200]
            log.error(_("WinningToFpdb.readHandInfo: '%s'") % tmp)
            raise FpdbParseError

        info.update(m.groupdict())
        
        m1 = self.re_TourNo.search(self.in_path)
        if m1: info.update(m1.groupdict())

        datetimestr = "%s/%s/%s %s:%s:%s" % (m2.group('Y'), m2.group('M'), m2.group('D'), m2.group('H'), m2.group('MIN'), m2.group('S'))
        hand.startTime = datetime.datetime.strptime(datetimestr, "%Y/%m/%d %H:%M:%S") # also timezone at end, e.g. " ET"
        hand.startTime = HandHistoryConverter.changeTimezone(hand.startTime, self.import_parameters['timezone'], "UTC")
        
        if 'TOURNO' in info:
            hand.tourNo = info['TOURNO']
            
        if 'HID' in info:
            hand.handid = info['HID']
            
        if not hand.maxseats:
            if hand.gametype['base'] == 'stud':
                hand.maxseats = 8
            elif hand.gametype['type'] == 'ring':
                hand.maxseats = 9
            else:
                hand.maxseats = 10
        
        if 'TABLE' in info:
            if hand.tourNo:
                hand.buyin = 0
                hand.fee = 0
                hand.buyinCurrency="NA" 
                hand.tablename = 1
                m3 = self.re_Table.search(info['TABLE'])                
                if m3 is not None:
                    tableinfo = m3.groupdict()
                    if 'SPECIAL' in tableinfo and tableinfo['SPECIAL'] != None:
                        if tableinfo['SPECIAL'] in ('Freeroll', 'FREEBUY', 'Freebuy'):
                            hand.buyinCurrency="FREE"
                        hand.guaranteeAmt = int(100*Decimal(self.clearMoneyString(tableinfo['BUYIN'])))
                        
                    if hand.guaranteeAmt == 0:
                        hand.buyinCurrency="USD"
                        hand.buyin = int(100*Decimal(self.clearMoneyString(tableinfo['BUYIN'])))
                    
                    if 'MAX' in tableinfo and tableinfo['MAX'] != None:
                        n = tableinfo['MAX'].replace('-Max', '')
                        if n in ('Heads-up', 'Heads-Up'):
                            hand.maxseats = 2
                        else:
                            hand.maxseats = int(n)
                    
                    if 'SPEED' in tableinfo and tableinfo['SPEED'] != None:
                        hand.speed = self.speeds[tableinfo['SPEED']]                            
                        if hand.maxseats==2 and hand.buyin in self.HUSnG_Fee:
                            hand.fee = self.HUSnG_Fee[hand.buyin][hand.speed]
                            hand.isSng = True
                        if hand.maxseats!=2 and hand.buyin in self.SnG_Fee:
                            hand.fee = self.SnG_Fee[hand.buyin][hand.speed]
                            hand.isSng = True
                        
                    hand.tablename = int(m3.group('TABLENO'))

                if "On Demand" in info['TABLE']:
                    hand.isOnDemand = True
                    
                if " KO" in info['TABLE'] or "Knockout" in info['TABLE']:
                    hand.isKO = True
                    
                if "R/A" in info['TABLE']:
                    hand.isRebuy = True
                    hand.isAddOn = True
                    
                m4 = self.re_TourneyName.search(info['TABLE'])
                if m4:
                    hand.tourneyName = m4.group('TOURNAME')
            else:
                hand.tablename = info['TABLE']
                buyin_type = self.re_buyinType.search(info['TABLE'])
                if buyin_type:
                    hand.gametype['buyinType'] = buyin[buyin_type.group('BUYINTYPE')]
    
    def readButton(self, hand):
        m = self.re_Button.search(hand.handText)
        if m:
            hand.buttonpos = int(m.group('BUTTON'))
        else:
            log.info('readButton: ' + _('not found'))

    def readPlayerStacks(self, hand):
        pre, post = hand.handText.split('------ Summary ------')
        m = self.re_PlayerInfo.finditer(pre)
        for a in m:
            hand.addPlayer(int(a.group('SEAT')), a.group('PNAME'), self.clearMoneyString(a.group('CASH')))

    def markStreets(self, hand):
        if hand.gametype['base'] in ("hold"):
            m =  re.search(r"(?P<PREFLOP>.+(?=\*\*\* FLOP \*\*\*:)|.+)"
                       r"(\*\*\* FLOP \*\*\*:(?P<FLOP> (\[\S\S\S?] )?\[\S\S\S? ?\S\S\S? \S\S\S?].+(?=\*\*\* TURN \*\*\*:)|.+))?"
                       r"(\*\*\* TURN \*\*\*: \[\S\S\S? \S\S\S? \S\S\S?] (?P<TURN>\[\S\S\].+(?=\*\*\* RIVER \*\*\*:)|.+))?"
                       r"(\*\*\* RIVER \*\*\*: \[\S\S\S? \S\S\S? \S\S\S? \S\S\S?] ?(?P<RIVER>\[\S\S\S?\].+))?", hand.handText,re.DOTALL)
        elif hand.gametype['base'] in ("stud"):
            m =  re.search(r"(?P<THIRD>.+(?=\*\*\* Third street \*\*\*)|.+)"
                           r"(\*\*\* Third street \*\*\*(?P<FOURTH>.+(?=\*\*\* Fourth street \*\*\*)|.+))?"
                           r"(\*\*\* Fourth street \*\*\*(?P<FIFTH>.+(?=\*\*\* Fifth street \*\*\*)|.+))?"
                           r"(\*\*\* Fifth street \*\*\*(?P<SIXTH>.+(?=\*\*\* Sixth street \*\*\*)|.+))?"
                           r"(\*\*\* Sixth street \*\*\*(?P<SEVENTH>.+))?", hand.handText,re.DOTALL)
        hand.addStreets(m)

    def readCommunityCards(self, hand, street): # street has been matched by markStreets, so exists in this hand
        m = self.re_Board.search(hand.streets[street])
        hand.setCommunityCards(street, [c.replace("10", "T") for c in m.group('CARDS').split(' ')])

    def readAntes(self, hand):
        log.debug(_("reading antes"))
        m = self.re_Antes.finditer(hand.handText)
        for player in m:
            #~ logging.debug("hand.addAnte(%s,%s)" %(player.group('PNAME'), player.group('ANTE')))
            hand.addAnte(player.group('PNAME'), player.group('ANTE'))
    
    def readBringIn(self, hand):
        m = self.re_BringIn.search(hand.handText,re.DOTALL)
        if m:
            #~ logging.debug("readBringIn: %s for %s" %(m.group('PNAME'),  m.group('BRINGIN')))
            hand.addBringIn(m.group('PNAME'),  m.group('BRINGIN'))
        
    def readBlinds(self, hand):
        liveBlind = True
        for a in self.re_PostSB.finditer(hand.handText):
            if liveBlind:
                hand.addBlind(a.group('PNAME'), 'small blind', a.group('SB'))
                liveBlind = False
            else:
                pass
                # Post dead blinds as ante
                #hand.addBlind(a.group('PNAME'), 'secondsb', a.group('SB'))
        for a in self.re_PostBB.finditer(hand.handText):
            hand.addBlind(a.group('PNAME'), 'big blind', a.group('BB'))
        for a in self.re_Posts.finditer(hand.handText):
            if Decimal(self.clearMoneyString(a.group('SBBB'))) == Decimal(hand.bb):
                hand.addBlind(a.group('PNAME'), 'big blind', a.group('SBBB'))
            else:
                hand.addBlind(a.group('PNAME'), 'secondsb', a.group('SBBB'))

    def readHeroCards(self, hand):
#    streets PREFLOP, PREDRAW, and THIRD are special cases beacause
#    we need to grab hero's cards
        for street in ('PREFLOP', 'DEAL'):
            if street in hand.streets.keys():
                newcards = []
                m = self.re_HeroCards.finditer(hand.streets[street])
                for found in m:
                    hand.hero = found.group('PNAME')
                    newcards.append(found.group('CARD').replace("10", "T"))
                if hand.hero:
                    hand.addHoleCards(street, hand.hero, closed=newcards, shown=False, mucked=False, dealt=True)

        for street, text in hand.streets.iteritems():
            if not text or street in ('PREFLOP', 'DEAL'): continue  # already done these
            m = self.re_HeroCards.finditer(hand.streets[street])
            players = {}
            for found in m:
                player = found.group('PNAME')
                if players.get(player) == None:
                    players[player] = []
                players[player].append(found.group('CARD').replace("10", "T"))
            
            for player, cards in players.iteritems():
                if street == 'THIRD': # hero in stud game
                    hand.dealt.add(player) # need this for stud??
                    if len(cards)==3:
                        hand.hero = player
                        hand.addHoleCards(street, player, closed=cards[0:2], open=[cards[2]], shown=False, mucked=False, dealt=False)
                    else:
                        hand.addHoleCards(street, player, closed=[], open=cards, shown=False, mucked=False, dealt=False)
                elif street == 'SEVENTH':
                    if hand.hero==player:
                        hand.addHoleCards(street, player, open=cards, closed=[], shown=False, mucked=False, dealt=False)
                    else:
                        hand.addHoleCards(street, player, open=[], closed=cards, shown=False, mucked=False, dealt=False)
                else:
                    hand.addHoleCards(street, player, open=cards, closed=[], shown=False, mucked=False, dealt=False)


    def readAction(self, hand, street):
        m = self.re_Action.finditer(hand.streets[street])
        for action in m:
            acts = action.groupdict()
            if action.group('PNAME') == None:                
                raise FpdbHandPartial(_("Unknown player acts"))
                
            if action.group('ATYPE') == 'folds':
                hand.addFold( street, action.group('PNAME'))
            elif action.group('ATYPE') == 'checks':
                hand.addCheck( street, action.group('PNAME'))
            elif action.group('ATYPE') == 'calls':
                hand.addCall( street, action.group('PNAME'), self.clearMoneyString(action.group('BET')) )
            elif action.group('ATYPE') in ('raises', 'straddle', 'caps'):
                hand.addCallandRaise( street, action.group('PNAME'), self.clearMoneyString(action.group('BET')) )
            elif action.group('ATYPE') ==  'bets':
                hand.addBet( street, action.group('PNAME'), self.clearMoneyString(action.group('BET')) )
            elif action.group('ATYPE') ==  'allin':
                player = action.group('PNAME')
                # disconnected all in
                if action.group('BET') == None:
                    amount = str(hand.stacks[player])
                else:
                    amount = self.clearMoneyString(action.group('BET')).replace(u',', u'') #some sites have commas
                Ai = Decimal(amount)
                Bp = hand.lastBet[street]
                Bc = sum(hand.bets[street][player])
                C = Bp - Bc
                if Ai <= C:
                    hand.addCall(street, player, amount)
                elif Bp == 0:
                    hand.addBet(street, player, amount)
                else:
                    hand.addCallandRaise(street, player, amount)
            else:
                print (_("DEBUG:") + " " + _("Unimplemented %s: '%s' '%s'") % ("readAction", action.group('PNAME'), action.group('ATYPE')))

    def readCollectPot(self,hand):
        for m in self.re_CollectPot.finditer(hand.handText):
            if Decimal(self.clearMoneyString(m.group('POT'))) > 0:
                hand.addCollectPot(player=m.group('PNAME'),pot=m.group('POT'))
            
    def readShowdownActions(self, hand):
        # TODO: pick up mucks also??
        pass

    def readShownCards(self,hand):
        for m in self.re_ShownCards.finditer(hand.handText):
            if m.group('CARDS') is not None:
                cards = m.group('CARDS')
                cards = [c.replace("10", "T") for c in cards.split(' ')] # needs to be a list, not a set--stud needs the order
                string = m.group('STRING')
                if m.group('STRING2'):
                    string += '|' + m.group('STRING2')

                (shown, mucked) = (False, False)
                #if m.group('SHOWED') == "showed": shown = True
                #elif m.group('SHOWED') == "mucked": mucked = True

                #print "DEBUG: hand.addShownCards(%s, %s, %s, %s)" %(cards, m.group('PNAME'), shown, mucked)
                hand.addShownCards(cards=cards, player=m.group('PNAME'), shown=shown, mucked=mucked, string=string)

    @staticmethod
    def getTableTitleRe(type, table_name=None, tournament = None, table_number=None):
        "Returns string to search in windows titles"
        regex = re.escape(str(table_name))
        if type=="tour":
            regex = ", Table " + re.escape(str(table_number)) + "\s\-.*\s\(" + re.escape(str(tournament)) + "\)"
        log.info("Winning.getTableTitleRe: table_name='%s' tournament='%s' table_number='%s'" % (table_name, tournament, table_number))
        log.info("Winning.getTableTitleRe: returns: '%s'" % (regex))
        return regex

