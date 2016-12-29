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

#Note that this filter also supports UltimateBet, they are both owned by the same company and form the Cereus Network

import L10n
_ = L10n.get_translation()

# TODO: I have no idea if AP has multi-currency options, i just copied the regex out of Everleaf converter for the currency symbols.. weeeeee - Eric
import sys
from HandHistoryConverter import *

# Class for converting Absolute HH format.

class Absolute(HandHistoryConverter):

    # Class Variables
    sitename = "Absolute"
    filetype = "text"
    codepage = "cp1252"
    siteId   = 8
    HORSEHand = False
    
    Lim_Blinds = {'0.04': ('0.01', '0.02'), '0.08': ('0.02', '0.04'), '0.20': ('0.05', '0.10'),
                        #'0.10': ('0.02', '0.05'),         '0.20': ('0.05', '0.10'),
                        '0.40': ('0.10', '0.20'),         '0.50': ('0.10', '0.25'),
                        '1.00': ('0.25', '0.50'),         '1': ('0.25', '0.50'),
                        '2.00': ('0.50', '1.00'),         '2': ('0.50', '1.00'),
                        '4.00': ('1.00', '2.00'),         '4': ('1.00', '2.00'),
                        '6.00': ('2.00', '3.00'),         '6': ('2.00', '3.00'),
                        '8.00': ('2.00', '4.00'),         '8': ('2.00', '4.00'),
                       '10.00': ('3.00', '5.00'),        '10': ('3.00', '5.00'),
                       '20.00': ('5.00', '10.00'),       '20': ('5.00', '10.00'),
                       '30.00': ('10.00', '15.00'),      '30': ('10.00', '15.00'),
                       '40.00': ('10.00', '20.00'),      '40': ('10.00', '20.00'),
                       '50.00': ('15.00', '25.00'),      '50': ('15.00', '25.00'),
                       '60.00': ('15.00', '30.00'),      '60': ('15.00', '30.00'),
                       '80.00': ('20.00', '40.00'),      '80': ('20.00', '40.00'),
                      '100.00': ('25.00', '50.00'),     '100': ('25.00', '50.00'),
                      '150.00': ('50.00', '75.00'),     '150': ('50.00', '75.00'),
                      '200.00': ('50.00', '100.00'),    '200': ('50.00', '100.00'),
                      '400.00': ('100.00', '200.00'),   '400': ('100.00', '200.00'),
                      '600.00': ('150.00', '300.00'),   '600': ('150.00', '300.00'),
                      '800.00': ('200.00', '400.00'),   '800': ('200.00', '400.00'),
                     '1000.00': ('250.00', '500.00'),  '1000': ('250.00', '500.00'),
                     '2000.00': ('500.00', '1000.00'), '2000': ('500.00', '1000.00'),
                  }

    # Static regexes
    re_Identify = re.compile(u'Stage\s+\#C?[0-9]+')
    re_SplitHands  = re.compile(r"\n\n+")
    re_TailSplitHands  = re.compile(r"(\nn\n+)")
    #Stage #1571362962: Holdem  No Limit $0.02 - 2009-08-05 15:24:06 (ET)
    #Table: TORONTO AVE (Real Money) Seat #6 is the dealer
    #Seat 6 - FETS63 ($0.75 in chips)
    #Board [10s 5d Kh Qh 8c]

    re_GameInfo = re.compile( ur"""
              ^Stage\s+\#C?(?P<HID>[0-9]+):?\s+
              (?:Tourney\ ID\ (?P<TRNY_ID>\d+)\s+)?
              (?P<GAME>Holdem|HOLDEM|Seven\ Card\ Hi\/Lo|HORSE|Omaha|Omaha\ Hi\/Lo|OMAHA)\s+
              (?P<TRNY_TYPE>\(1\son\s1\)|\(1\sON\s1\)|Single\ Tournament|SINGLE\ TOURNAMENT|Multi\ Normal\ Tournament|MULTI\ NORMAL\ TOURNAMENT|)\s*
              (?P<LIMIT>No\ Limit|NO\ LIMIT|Pot\ Limit|POT\ LIMIT|Normal|NORMAL|)\s?
              (?P<CURRENCY>\$|\s€|)
              (?P<SB>[.,0-9]+)(/(?:\$|\s€|)(?P<BB>[.,0-9]+))?
              (,\s(?:\$|\s€|)(?P<ANTE>[.,0-9]+)\sante)?
              \s+
              ((?P<TTYPE>(Turbo))\s+)?
              (\(7-2\)\s)?-\s+
              ((?P<DATETIME>\d\d\d\d-\d\d-\d\d\ \d\d:\d\d:\d\d)(\.\d+)?)\s+
              (?: \( (?P<TZ>[A-Z]+) \)\s+ )?
              .*?
              (Table:\ (?P<TABLE>.*?)\ \(Real\ Money\))?
        """, re.MULTILINE|re.VERBOSE|re.DOTALL)

    re_HorseGameInfo = re.compile(
            ur"^Game Type: (?P<LIMIT>Limit) (?P<GAME>Holdem)",
            re.MULTILINE)

    re_HandInfo = re_GameInfo

    # TODO: that's not the right way to match for "dead" dealer is it?
    re_Button = re.compile(ur"Seat #(?P<BUTTON>[0-9]) is the ?[dead]* dealer$", re.MULTILINE)

    re_PlayerInfo = re.compile(
            ur"^Seat (?P<SEAT>[0-9]) - (?P<PNAME>.*) "\
            ur"\((?:\$| €|)(?P<CASH>[0-9]*[.,0-9]+) in chips\)",
            re.MULTILINE)

    re_Board = re.compile(ur"\[(?P<CARDS>[^\]]*)\]? *$", re.MULTILINE)
    
    re_Pocket = re.compile(r"\*\*\* POCKET CARDS \*\*\*")

    def compilePlayerRegexs(self, hand):
        players = set([player[1] for player in hand.players])
        if not players <= self.compiledPlayers: # x <= y means 'x is subset of y'
            # we need to recompile the player regexs.
            self.compiledPlayers = players
            player_re = "(?P<PNAME>" + "|".join(map(re.escape, players)) + ")"
            #(?P<CURRENCY>\$| €|)(?P<BB>[0-9]*[.0-9]+)
            self.re_PostSB          = re.compile(ur"^%s - Posts small blind (?:\$| €|)(?P<SB>[,.0-9]+)" % player_re, re.MULTILINE)
            self.re_PostBB          = re.compile(ur"^%s - Posts big blind (?:\$| €|)(?P<BB>[.,0-9]+)" % player_re, re.MULTILINE)
            self.re_Post            = re.compile(ur"^%s - Posts (?:\$| €|)(?P<BB>[.,0-9]+)$" % player_re, re.MULTILINE)
            # TODO: Absolute posting when coming in new: %s - Posts $0.02 .. should that be a new Post line? where do we need to add support for that? *confused*
            self.re_PostBoth        = re.compile(ur"^%s - Posts (dead )?(?:\$| €|)(?P<BB>[,.0-9]+) (dead )?(?:\$| €|)(?P<SB>[,.0-9]+)" % player_re, re.MULTILINE)
            self.re_Action          = re.compile(ur"^%s - (?P<ATYPE>Bets |Raises |All-In |All-In\(Raise\) |Calls |Folds|Checks)?\$?(?P<BET>[,.0-9]+)?" % player_re, re.MULTILINE)
            self.re_ShowdownAction  = re.compile(ur"^%s - Shows \[(?P<CARDS>.*)\] \((?P<STRING>.+?)\)" % player_re, re.MULTILINE)
            self.re_CollectPot      = re.compile(ur"^Seat [0-9]: %s(?: \(dealer\)|)(?: \(big blind\)| \(small blind\)|) (?:won|collected) Total \((?:\$| €|)(?P<POT>[,.0-9]+)\)(.*72 Prop Win \((?:\$| €|)(?P<PROP>[,.0-9]+)\))?" % player_re, re.MULTILINE)
            self.re_Antes           = re.compile(ur"^%s - Ante (?:\$| €|)(?P<ANTE>[,.0-9]+)" % player_re, re.MULTILINE)
            self.re_BringIn         = re.compile(ur"^%s - Bring-In (?:\$| €|)(?P<BRINGIN>[.0-9]+)\." % player_re, re.MULTILINE)
            self.re_HeroCards       = re.compile(ur"^(Dealt to )?%s (- Pocket )?\[(?P<CARDS>.*)\]" % player_re, re.MULTILINE)

    def readSupportedGames(self):
        return [["ring", "hold", "nl"],
                ["ring", "hold", "pl"],
                ["ring", "hold", "fl"],
                ["ring", "stud", "fl"],
                ["tour", "hold", "nl"],
               ]

    def determineGameType(self, handText):
        """return dict with keys/values:
        'type'       in ('ring', 'tour')
        'limitType'  in ('nl', 'cn', 'pl', 'cp', 'fl')
        'base'       in ('hold', 'stud', 'draw')
        'category'   in ('holdem', 'omahahi', omahahilo', 'razz',
                         'studhi', 'studhilo', 'fivedraw', '27_1draw',
                         '27_3draw', 'badugi')
        'hilo'       in ('h','l','s')
        'smallBlind' int?
        'bigBlind'   int?
        'smallBet'
        'bigBet'
        'currency'  in ('USD', 'EUR', 'T$', <countrycode>)

        or None if we fail to get the info """
        info = {'type':'ring'}

        m = self.re_GameInfo.search(handText)
        if not m:
            tmp = handText[0:200]
            log.error(_("AbsoluteToFpdb.determineGameType: '%s'") % tmp)
            raise FpdbParseError

        mg = m.groupdict()
        #print "DEBUG: mg: %s" % mg

        # translations from captured groups to our info strings
        limits = { 
                  'No Limit':'nl', 
                  'NO LIMIT':'nl',
                  'Pot Limit':'pl', 
                  'POT LIMIT': 'pl',
                  'Normal':'fl', 
                  'NORMAL':'fl', 
                  'Limit':'fl',
                  'LIMIT': 'fl'
        }
        games = {              # base, category
                   "Holdem" : ('hold','holdem'),
                   "HOLDEM" : ('hold','holdem'),
                    'Omaha' : ('hold','omahahi'),
              'Omaha Hi/Lo' : ('hold','omahahilo'),
                    'OMAHA' : ('hold','omahahi'),
                     'Razz' : ('stud','razz'),
         'Seven Card Hi/Lo' : ('stud','studhilo'),
              '7 Card Stud' : ('stud','studhi')
               }
        currencies = { u' €':'EUR', '$':'USD', '':'T$' }
        if 'GAME' in mg and mg['GAME'] == "HORSE": # if we're a HORSE game, the game type is on the next line
            self.HORSEHand = True
            m = self.re_HorseGameInfo.search(handText)
            if not m:
                return None # it's a HORSE game and we don't understand the game type
            temp = m.groupdict()
            #print "AP HORSE processing"
            if 'GAME' not in temp or 'LIMIT' not in temp:
                return None # sort of understood it but not really
            #print "temp=", temp
            mg['GAME'] = temp['GAME']
            mg['LIMIT'] = temp['LIMIT']
        if 'GAME' in mg:
            (info['base'], info['category']) = games[mg['GAME']]
        if 'LIMIT' in mg:
            info['limitType'] = limits[mg['LIMIT']]
        if 'CURRENCY' in mg:
            info['currency'] = currencies[mg['CURRENCY']]
            if info['currency'] == 'T$':
                info['type'] = 'tour'
        if 'SB' in mg:
            mg['SB'] = mg['SB'].replace(',', '')
            info['sb'] = mg['SB']
        if 'BB' in mg:
            info['bb'] = mg['BB']
        # NB: SB, BB must be interpreted as blinds or bets depending on limit type.
        if info['bb'] is None:
            mg['SB'] = mg['SB'].replace(',', '')
            info['bb'] = mg['SB']
            info['sb'] = str(float(mg['SB']) * 0.5) # TODO: AP does provide Small BET for Limit .. I think? at least 1-on-1 limit they do.. sigh

        if info['limitType'] == 'fl' and info['bb'] is not None:
            if info['type'] == 'ring':
                try:
                    bb = self.clearMoneyString(info['bb'])
                    info['sb'] = self.Lim_Blinds[bb][0]
                    info['bb'] = self.Lim_Blinds[bb][1]
                except KeyError:
                    tmp = handText[0:200]
                    log.error(_("AbsoluteToFpdb.determineGameType: Lim_Blinds has no lookup for '%s' - '%s'") % (info['bb'], tmp))
                    raise FpdbParseError
        return info


    def readHandInfo(self, hand):
        m = self.re_HandInfo.search(hand.handText)
        #print "DEBUG: fname_info.groupdict(): %s" %(fname_info.groupdict())
        if m is None:
            tmp = hand.handText[0:200]
            log.error(_("AbsoluteToFpdb.readHandInfo: '%s'") % tmp)
            raise FpdbParseError

        hand.handid =  m.group('HID')
        if m.group('TABLE'):
            hand.tablename = m.group('TABLE')
        else:
            hand.tablename = 'TABLE'

        hand.startTime = datetime.datetime.strptime(m.group('DATETIME'), "%Y-%m-%d %H:%M:%S")

        if hand.gametype['type']=='tour':
            hand.buyin = 0
            hand.fee = 0
            hand.buyinCurrency="NA"
            hand.maxseats = None  
            hand.tourNo = m.group('TRNY_ID')

        # assume 6-max unless we have proof it's a larger/smaller game, 
        #since absolute doesn't give seat max info
        # TODO: (1-on-1) does have that info in the game type line
        hand.maxseats = 6

        if self.HORSEHand:
            hand.maxseats = 8  # todo : unless it's heads up!!?
        return

    def readPlayerStacks(self, hand):
        m = self.re_PlayerInfo.finditer(hand.handText)
        for a in m:
            seatnum = int(a.group('SEAT'))
            hand.addPlayer(seatnum, a.group('PNAME'), a.group('CASH'))
            if seatnum > 6:
                hand.maxseats = 9 # absolute does 2/4/6/9 games
                # TODO: implement lookup list by table-name to determine maxes, 
                # then fall back to 6 default/10 here, if there's no entry in the list?


    def markStreets(self, hand):
        # PREFLOP = ** Dealing down cards **
        # This re fails if,  say, river is missing; then we don't get the ** that starts the river.
        #m = re.search('(\*\* Dealing down cards \*\*\n)(?P<PREFLOP>.*?\n\*\*)?( Dealing Flop \*\* \[ (?P<FLOP1>\S\S), (?P<FLOP2>\S\S), (?P<FLOP3>\S\S) \])?(?P<FLOP>.*?\*\*)?( Dealing Turn \*\* \[ (?P<TURN1>\S\S) \])?(?P<TURN>.*?\*\*)?( Dealing River \*\* \[ (?P<RIVER1>\S\S) \])?(?P<RIVER>.*)', hand.handText,re.DOTALL)
        if hand.gametype['base'] == 'hold':
            m = re.search(r"\*\*\* POCKET CARDS \*\*\*(?P<PREFLOP>.+(?=\*\*\* FLOP \*\*\*)|.+)"
                    r"(\*\*\* FLOP \*\*\*(?P<FLOP>.+(?=\*\*\* TURN \*\*\*)|.+))?"
                    r"(\*\*\* TURN \*\*\*(?P<TURN>.+(?=\*\*\* RIVER \*\*\*)|.+))?"
                    r"(\*\*\* RIVER \*\*\*(?P<RIVER>.+))?", hand.handText, re.DOTALL)

        elif hand.gametype['base'] == 'stud': # TODO: Not implemented yet
            m =     re.search(r"(?P<ANTES>.+(?=\*\*\* 3rd STREET \*\*\*)|.+)"
                           r"(\*\*\* 3rd STREET \*\*\*(?P<THIRD>.+(?=\*\*\* 4TH STREET \*\*\*)|.+))?"
                           r"(\*\*\* 4TH STREET \*\*\*(?P<FOURTH>.+(?=\*\*\* 5TH STREET \*\*\*)|.+))?"
                           r"(\*\*\* 5TH STREET \*\*\*(?P<FIFTH>.+(?=\*\*\* 6TH STREET \*\*\*)|.+))?"
                           r"(\*\*\* 6TH STREET \*\*\*(?P<SIXTH>.+(?=\*\*\* RIVER \*\*\*)|.+))?"
                           r"(\*\*\* RIVER \*\*\*(?P<SEVENTH>.+))?", hand.handText,re.DOTALL)
        hand.addStreets(m)

    def readCommunityCards(self, hand, street):
        # street has been matched by markStreets, so exists in this hand
        # If this has been called, street is a street which gets dealt
        # community cards by type hand but it might be worth checking somehow.
        # if street in ('FLOP','TURN','RIVER'):
        #    a list of streets which get dealt community cards (i.e. all but PREFLOP)
        log.debug("readCommunityCards (%s)" % street)
        m = self.re_Board.search(hand.streets[street])
        cards = m.group('CARDS')
        cards = [validCard(card) for card in cards.split(' ')]
        hand.setCommunityCards(street=street, cards=cards)

    def readAntes(self, hand):
        log.debug(_("reading antes"))
        m = self.re_Antes.finditer(hand.handText)
        for player in m:
            log.debug("hand.addAnte(%s,%s)" %(player.group('PNAME'), player.group('ANTE')))
            hand.addAnte(player.group('PNAME'), player.group('ANTE'))

    def readBringIn(self, hand):
        m = self.re_BringIn.search(hand.handText,re.DOTALL)
        if m:
            log.debug(_("Player bringing in: %s for %s") % (m.group('PNAME'),  m.group('BRINGIN')))
            hand.addBringIn(m.group('PNAME'),  m.group('BRINGIN'))
        else:
            log.warning(_("No bringin found."))

    def readBlinds(self, hand):
        found_small, found_big = False, False
        m = self.re_PostSB.search(hand.handText)
        if m is not None:
            hand.addBlind(m.group('PNAME'), 'small blind', m.group('SB'))
            found_small = True
        else:
            log.debug(_("No small blind"))
            hand.addBlind(None, None, None)
        for a in self.re_PostBB.finditer(hand.handText):
            hand.addBlind(a.group('PNAME'), 'big blind', a.group('BB'))
            hand.setUncalledBets(True)
            found_big = True
        for a in self.re_Post.finditer(hand.handText):
            hand.addBlind(a.group('PNAME'), 'big blind', a.group('BB'))
            found_big = True
        
        if found_small != found_big:
            for a in self.re_Action.finditer(self.re_Pocket.split(hand.handText)[0]):
                acts = a.groupdict()
                if acts['ATYPE'] == 'All-In ':
                    if acts['BET'] == None:
                        # timeout all-in
                        raise FpdbHandPartial("Partial hand history: %s" % hand.handid)
                    bet = acts['BET'].replace(',', '')
                    if found_small:
                        hand.addBlind(acts['PNAME'], 'big blind', bet)
                        hand.setUncalledBets(True)
                    elif found_big:
                        hand.addBlind(acts['PNAME'], 'small blind', bet)
                    
        for a in self.re_PostBoth.finditer(hand.handText):
            hand.setUncalledBets(None)
            hand.addBlind(a.group('PNAME'), 'both', a.group('BB'))

    def readButton(self, hand):
        hand.buttonpos = int(self.re_Button.search(hand.handText).group('BUTTON'))
            
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
                    newcards = [validCard(card) for card in found.group('CARDS').split(' ') if card != 'H']
                    hand.addHoleCards(street, hand.hero, closed=newcards, shown=False, mucked=False, dealt=True)

        for street, text in hand.streets.iteritems():
            if not text or street in ('PREFLOP', 'DEAL'): continue  # already done these
            m = self.re_HeroCards.finditer(hand.streets[street])
            for found in m:
                player = found.group('PNAME')
                if found.group('CARDS') is None:
                    newcards = []
                else:
                    newcards = [validCard(card) for card in found.group('CARDS').split(' ') if card != 'H']
                    oldcards = []
                
                if street == 'THIRD' and len(newcards) == 3: # hero in stud game
                    hand.hero = player
                    hand.dealt.add(player) # need this for stud??
                    hand.addHoleCards(street, player, closed=newcards[0:2], open=[newcards[2]], shown=False, mucked=False, dealt=False)
                else:
                    hand.addHoleCards(street, player, open=newcards, closed=oldcards, shown=False, mucked=False, dealt=False)

    def readStudPlayerCards(self, hand, street):
        log.warning(_("%s cannot read all stud/razz hands yet.") % hand.sitename)

    def readAction(self, hand, street):
        m = self.re_Action.finditer(hand.streets[street])
        for action in m:
            #print "%s %s %s" % (street, action.group('ATYPE'), action.groupdict())
            if action.group('ATYPE') == 'Folds':
                hand.addFold( street, action.group('PNAME'))
            elif action.group('ATYPE') == 'Checks':
                hand.addCheck( street, action.group('PNAME'))
            elif action.group('ATYPE') == 'Calls ':
                bet = action.group('BET').replace(',', '')
                hand.setUncalledBets(None)
                hand.addCall( street, action.group('PNAME'), bet)
            elif action.group('ATYPE') == 'Bets ' or action.group('ATYPE') == 'All-In ':
                if action.group('BET') == None:
                    # timeout all-in
                    raise FpdbHandPartial("Partial hand history: %s" % hand.handid)
                bet = action.group('BET').replace(',', '')
                hand.setUncalledBets(None)
                hand.addBet( street, action.group('PNAME'), bet)
            elif action.group('ATYPE') == 'Raises ' or action.group('ATYPE') == 'All-In(Raise) ':
                bet = action.group('BET').replace(',', '')
                hand.setUncalledBets(None)
                hand.addCallandRaise( street, action.group('PNAME'), bet)
            elif action.group('ATYPE') == ' complete to': # TODO: not supported yet ?
                bet = action.group('BET').replace(',', '')
                hand.setUncalledBets(None)
                hand.addComplete( street, action.group('PNAME'), bet)
            else:
                log.debug(_("Unimplemented %s: '%s' '%s'") % ("readAction", action.group('PNAME'), action.group('ATYPE')))


    def readShowdownActions(self, hand):
        """Reads lines where holecards are reported in a showdown"""
        for m in self.re_ShowdownAction.finditer(hand.handText):
            if m.group('CARDS') is not None:
                newcards = [validCard(card) for card in m.group('CARDS').split(' ') if card != 'H']
                string = m.group('STRING')
                (shown, mucked) = (True, False)
                hand.addShownCards(cards=newcards, player=m.group('PNAME'), shown=shown, mucked=mucked, string=string)

    def readCollectPot(self,hand):
        for m in self.re_CollectPot.finditer(hand.handText):
            pot = m.group('POT').replace(',','')
            if m.group('PROP'):
                pot = str(Decimal(pot) - Decimal(m.group('PROP').replace(',','')))
            hand.addCollectPot(player=m.group('PNAME'),pot=pot)

    def readShownCards(self,hand):
        pass


def validCard(card):
    card = card.strip()
    if card == '10s': card = 'Ts'
    if card == '10h': card = 'Th'
    if card == '10d': card = 'Td'
    if card == '10c': card = 'Tc'
    return card
