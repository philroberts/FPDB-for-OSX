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

import sys
import datetime
from HandHistoryConverter import *

# Microgaming HH Format

class Microgaming(HandHistoryConverter):

    sitename = "Microgaming"
    filetype = "text"
    codepage = ["utf-8","cp1252"]
    siteId   = 20

    # Static regexes
    
    re_GameInfo     = re.compile("""(hhversion="(?P<VERSION>\d)"\s)?
                                    id="(?P<HID>[0-9]+)"\s
                                    date="(?P<DATETIME>[-:\d\s]+)"\s
                                    unicodetablename=".+"\s
                                    tablename="(?P<TABLE>.+)"\s
                                    stakes="(?P<SB>[.0-9]+)\|(?P<BB>[.0-9]+)"\s
                                    betlimit="(?P<LIMIT>NL|PL|FL)"\s
                                    tabletype="(Cash\sGame|MTT)"\s
                                    (unicodetabletype="\w+"\s)?
                                    gametypeid="\d+"\s
                                    gametype="(?P<GAME>[a-zA-Z\&; /']+)"\s
                                    realmoney="true"\s
                                    currencysymbol="(?P<CURRENCY>\S+?|)"\s
                                    (rake="\d+"\s)?
                                    playerseat="\d+"\s
                                    betamount="\d+"\s
                                    istournament="(?P<TOUR>\d)"\s?
                                    (totalplayers="\d+"\s)?
                                    (tablesize="(?P<MAX>\d+)"\s)?
                                    """, re.MULTILINE| re.VERBOSE)
    
    re_Identify   = re.compile(u'<Game\s(hhversion="\d"\s)?id=\"\d+\"\sdate=\"[\d\-\s:]+\"\sunicodetablename')
    re_SplitHands = re.compile('\n*----.+.DAT----\n*')
    re_PlayerInfo = re.compile('<Seat num="(?P<SEAT>[0-9]+)" alias="(?P<PNAME>.+)" unicodealias=".+" balance="(?P<CASH>[.0-9]+)" endbalance="[.0-9]+"(?P<BUTTON>\sdealer="true")?', re.MULTILINE)
    re_Card       = re.compile('<Card value="[0-9JQKA]+" suit="[csdh]" id="(?P<CARD>\d+)"\s?/>', re.MULTILINE)
    re_Board      = re.compile('<Action.+?</Action>', re.DOTALL)
    re_Table      = re.compile('\[(?P<TOURNO>[0-9]+)\]:Table (?P<TABLENO>\d+)', re.MULTILINE)    
    re_HeroCards  = re.compile(r'<Action seq="\d+" type="DealCards" seat="(?P<SEAT>\d+)">\s+?(?P<CARDS>(<Card value="[0-9TJQKA]+" suit="[csdh]" id="(?P<CARD>\d+)"\s?/>\s+)+)', re.MULTILINE)
    re_Action     = re.compile(r'<Action seq="\d+" type="(?P<ATYPE>[a-zA-Z]+)" seat="(?P<SEAT>\d+)"( value="(?P<BET>[.0-9]+)")?\s?/>', re.MULTILINE)
    re_CollectPot = re.compile(r'<Seat num="(?P<SEAT>\d+)" amount="(?P<POT>[.\d]+)" pot=".+" type=".*" lowhandwin="\d+"\s?/>', re.MULTILINE)
    re_ShownCards = re.compile(r'<Action seq="\d+" type="(?P<SHOWED>ShowCards|MuckCards)" seat="(?P<SEAT>\d+)">\s+?(?P<CARDS>(<Card value="[0-9TJQKA]+" suit="[csdh]" id="(?P<CARD>\d+)"\s?/>\s+)+)', re.MULTILINE)

    cid_toval = {
             "0":"As",   "1":"2s",  "2":"3s",  "3":"4s",  "4": "5s", "5":"6s",  "6":"7s",  "7":"8s",  "8":"9s",  "9":"Ts", "10":"Js", "11":"Qs", "12":"Ks",
            "13":"Ac",  "14":"2c", "15":"3c", "16":"4c", "17":"5c", "18":"6c", "19":"7c", "20":"8c", "21":"9c", "22":"Tc", "23":"Jc", "24":"Qc", "25":"Kc",
            "26":"Ad",  "27":"2d", "28":"3d", "29":"4d", "30":"5d", "31":"6d", "32":"7d", "33":"8d", "34":"9d", "35":"Td", "36": "Jd", "37":"Qd", "38":"Kd",
            "39":"Ah",  "40":"2h", "41":"3h", "42":"4h", "43":"5h", "44":"6h", "45":"7h", "46":"8h", "47":"9h", "48":"Th", "49": "Jh", "50":"Qh", "51":"Kh",
                   }

    def compilePlayerRegexs(self,  hand):
        pass

    def playerNameFromSeatNo(self, seatNo, hand):
        # This special function is required because Merge Poker records
        # actions by seat number, not by the player's name
        for p in hand.players:
            if p[0] == int(seatNo):
                return p[1]

    def readSupportedGames(self):
        return [["ring", "hold", "nl"],
                ["ring", "hold", "pl"],
                #["ring", "hold", "fl"], need Lim_Blinds
                #["ring", "stud", "fl"],
                #["ring", "draw", "fl"],
                #["tour", "hold", "fl"],
                ["tour", "hold", "pl"],
                ["tour", "hold", "nl"],
               ]

    def determineGameType(self, handText):
        info = {}
        m = self.re_GameInfo.search(handText)
        if not m: 
            tmp = handText[0:200]
            log.error(_("MicrogamingToFpdb.determineGameType: '%s'") % tmp)
            raise FpdbParseError

        mg = m.groupdict()
        #print "DEBUG: mg: %s" % mg
        currencies = { 'rCA=':'EUR', '$':'USD', '':'T$', 'IACsIA==':'EUR', 'IAAkAA==':'EUR'}
        limits = { 'NL':'nl', 'PL':'pl', 'FL':'fl'}
        games = {              # base, category
                  "Hold&apos;em" : ('hold','holdem'), 
                 "Hold &apos;em" : ('hold','holdem'), 
      "Multi Table Hold&apos;em" : ('hold','holdem'),
     "Multi Table Hold &apos;em" : ('hold','holdem'),
                       "Hold'em" : ('hold','holdem'),
                         "Omaha" : ('hold','omahahi'),
                     "Omaha H/L" : ('hold','omahahilo')
                }
        
        if 'LIMIT' in mg:
            info['limitType'] = limits[mg['LIMIT']]
        if 'GAME' in mg:
            (info['base'], info['category']) = games[mg['GAME']]
        if 'SB' in mg:
            info['sb'] = mg['SB']
        if 'BB' in mg:
            info['bb'] = mg['BB']
        if 'CURRENCY' in mg:
            if mg['CURRENCY'] in currencies:
                info['currency'] = currencies[mg['CURRENCY']]
            else: 
                info['currency'] = 'EUR'
        if 'TOUR' in mg:
            if mg['TOUR'] is None or int(mg['TOUR'])==0:
                info['type'] = 'ring'
            else:
                info['type'] = 'tour'
                info['currency'] = 'T$'
        # NB: SB, BB must be interpreted as blinds or bets depending on limit type.
        return info

    def readHandInfo(self, hand):
        info = {}
        m = self.re_GameInfo.search(hand.handText)

        if m is None:
            tmp = hand.handText[0:200]
            log.error(_("MicrogamingToFpdb.readHandInfo: '%s'") % tmp)
            raise FpdbParseError

        info.update(m.groupdict())
        #m = self.re_Button.search(hand.handText)
        #if m: info.update(m.groupdict())
        for key in info:
            if key == 'VERSION':
                if not info[key]:
                    hand.version = 1
                else:
                    hand.version = int(info[key])
            if key == 'DATETIME':
                hand.startTime = datetime.datetime.strptime(info[key],"%Y-%m-%d %H:%M:%S")
            if key == 'HID':
                hand.handid = info[key]
                hand.tablename = info[key]
            if key == 'BUTTON':
                hand.buttonpos = info[key]
            if key == 'LEVEL':
                hand.level = info[key]
            if hand.gametype['type'] == 'tour':
                if key == 'TABLE':
                    m1 = self.re_Table.search(info[key])
                    mg1 = m1.groupdict()
                    hand.tourNo = mg1['TOURNO']
                    hand.tablename = mg1['TABLENO']
                if key == 'CURRENCY':
                    # Hmm. Other useful tourney info doesn't appear to be readily available.
                    hand.buyin = 0
                    hand.fee = 0
                    hand.buyinCurrency = 'NA'
                    hand.isKO = False
            if key == 'MAX' and info.get(key)!=None:
                hand.maxseats = int(info[key])
        
        hand.setUncalledBets(True)
        
    def readButton(self, hand):
        pass
        #m = self.re_Button.search(hand.handText)
        #if m:
        #    for player in hand.players:
        #        if player[1] == m.group('BUTTON'):
        #            hand.buttonpos = player[0]
        #            break
        #else:
        #    log.info('readButton: ' + _('not found'))

    def readPlayerStacks(self, hand):
        logging.debug("readPlayerStacks")
        m = self.re_PlayerInfo.finditer(hand.handText)
        for a in m:
            seatno = int(a.group('SEAT'))
            if a.group('BUTTON') is not None:
                hand.buttonpos = seatno
            hand.addPlayer(seatno, a.group('PNAME'), a.group('CASH'))

    def markStreets(self, hand):
        if hand.gametype['base'] in ("hold"):
            m =  re.search('</Seats>(?P<PREFLOP>.+(?=<Action seq="\d+" type="DealFlop")|.+)'
                       '((?P<FLOP><Action seq="\d+" type="DealFlop">.+(?=<Action seq="\d+" type="DealTurn")|.+))?'
                       '((?P<TURN><Action seq="\d+" type="DealTurn">.+(?=<Action seq="\d+" type="DealRiver")|.+))?'
                       '((?P<RIVER><Action seq="\d+" type="DealRiver">.+?(?=<Action seq="\d+" type="ShowCards|MuckCards")|.+))?', hand.handText,re.DOTALL)
        if hand.gametype['category'] in ('27_1draw', 'fivedraw'):
            m =  re.search(r'(?P<PREDEAL>.+?(?=<ACTION TYPE="HAND_DEAL")|.+)'
                           r'(<ACTION TYPE="HAND_DEAL"(?P<DEAL>.+(?=<ACTION TYPE="HAND_BOARD")|.+))?'
                           r'(<ACTION TYPE="(?P<DRAWONE>.+))?', hand.handText,re.DOTALL)
        #import pprint
        #pprint.pprint(m.groupdict())
        hand.addStreets(m)

    def readCommunityCards(self, hand, street): # street has been matched by markStreets, so exists in this hand
        if street in ('FLOP','TURN','RIVER'):   # a list of streets which get dealt community cards (i.e. all but PREFLOP)
            #print "DEBUG readCommunityCards:", street, hand.streets.group(street)
            boardCards = []
            m = self.re_Board.search(hand.streets[street])
            if m:
                board = m.group()
                m1 = self.re_Card.finditer(board)
                for a in m1:
                    boardCards.append(self.convertMicroCards(a.group('CARD')))
            hand.setCommunityCards(street, boardCards)

    def readAntes(self, hand):
        pass
        #logging.debug(_("reading antes"))
        #m = self.re_Antes.finditer(hand.handText)
        #for player in m:
            #~ logging.debug("hand.addAnte(%s,%s)" %(player.group('PNAME'), player.group('ANTE')))
        #    hand.addAnte(player.group('PNAME'), player.group('ANTE'))
    
    def readBringIn(self, hand):
        pass
        #m = self.re_BringIn.search(hand.handText,re.DOTALL)
        #if m:
            #~ logging.debug("readBringIn: %s for %s" %(m.group('PNAME'),  m.group('BRINGIN')))
        #    hand.addBringIn(m.group('PNAME'),  m.group('BRINGIN'))
        
    def readBlinds(self, hand):
        pass # Dealt with in readAction

    def readHoleCards(self, hand):
#    streets PREFLOP, PREDRAW, and THIRD are special cases beacause
#    we need to grab hero's cards
        for street in ('PREFLOP', 'DEAL'):
            if street in hand.streets.keys():
                m = self.re_HeroCards.finditer(hand.streets[street])
                newcards = []
                for found in m:
                    hand.hero = self.playerNameFromSeatNo(found.group('SEAT'), hand)
                    for card in self.re_Card.finditer(found.group('CARDS')):
                        newcards.append(self.convertMicroCards(card.group('CARD')))
                    hand.addHoleCards(street, hand.hero, closed=newcards, shown=False, mucked=False, dealt=True)

    def convertMicroCards(self, card):
        return self.cid_toval[card]
    
    def readDrawCards(self, hand, street):
        logging.debug("readDrawCards")
        m = self.re_HeroCards.finditer(hand.streets[street])
        if m == None:
            hand.involved = False
        else:
            for player in m:
                hand.hero = player.group('PNAME') # Only really need to do this once
                newcards = player.group('NEWCARDS')
                oldcards = player.group('OLDCARDS')
                if newcards == None:
                    newcards = []
                else:
                    newcards = newcards.split(' ')
                if oldcards == None:
                    oldcards = []
                else:
                    oldcards = oldcards.split(' ')
                hand.addDrawHoleCards(newcards, oldcards, player.group('PNAME'), street)


    def readStudPlayerCards(self, hand, street):
        # See comments of reference implementation in FullTiltToFpdb.py
        # logging.debug("readStudPlayerCards")
        m = self.re_HeroCards.finditer(hand.streets[street])
        for player in m:
            #~ logging.debug(player.groupdict())
            (pname,  oldcards,  newcards) = (player.group('PNAME'), player.group('OLDCARDS'), player.group('NEWCARDS'))
            if oldcards:
                oldcards = [c.strip() for c in oldcards.split(' ')]
            if newcards:
                newcards = [c.strip() for c in newcards.split(' ')]
            if street=='ANTES':
                return
            elif street=='THIRD':
                # we'll have observed hero holecards in CARDS and thirdstreet open cards in 'NEWCARDS'
                # hero: [xx][o]
                # others: [o]
                hand.addPlayerCards(player = player.group('PNAME'), street = street,  closed = oldcards,  open = newcards)
            elif street in ('FOURTH',  'FIFTH',  'SIXTH'):
                # 4th:
                # hero: [xxo] [o]
                # others: [o] [o]
                # 5th:
                # hero: [xxoo] [o]
                # others: [oo] [o]
                # 6th:
                # hero: [xxooo] [o]
                # others:  [ooo] [o]
                hand.addPlayerCards(player = player.group('PNAME'), street = street, open = newcards)
                # we may additionally want to check the earlier streets tally with what we have but lets trust it for now.
            elif street=='SEVENTH' and newcards:
                # hero: [xxoooo] [x]
                # others: not reported.
                hand.addPlayerCards(player = player.group('PNAME'), street = street, closed = newcards)

    def readAction(self, hand, street):
        allIns = 0
        m = self.re_Action.finditer(hand.streets[street])
        for action in m:
            if action.group('ATYPE') in ('Call','Raise', 'AllIn') and allIns>0:
                hand.setUncalledBets(False)
            #print "DEBUG: %s action.groupdict(): %s" % (street, action.groupdict())
            pname = self.playerNameFromSeatNo(action.group('SEAT'), hand)
            if action.group('ATYPE') == 'Fold':
                hand.addFold(street, pname)
            elif action.group('ATYPE') == 'Check':
                hand.addCheck(street, pname)
            elif action.group('ATYPE') == 'Call':
                if hand.version==1:
                    hand.addCallTo(street, pname, action.group('BET') )
                else:
                    hand.addCall(street, pname, action.group('BET') )
            elif action.group('ATYPE') == 'SmallBlind':
                hand.addBlind(pname, 'small blind', action.group('BET'))
            elif action.group('ATYPE') == 'BigBlind':
                hand.addBlind(pname, 'big blind', action.group('BET'))
            elif action.group('ATYPE') == 'Raise':
                if hand.version==1:
                    hand.addRaiseTo(street, pname, action.group('BET') )
                else:
                    amount = Decimal(action.group('BET'))
                    if sum(hand.bets[street][pname]) == 0 and hand.pot.common[pname] > 0:
                        amount += hand.pot.common[pname]
                    hand.addCallandRaise(street, pname, str(amount) )
            elif action.group('ATYPE') == 'Bet':
                if street in ('PREFLOP', 'THIRD', 'DEAL'):
                    if hand.version==1:
                        hand.addRaiseTo(street, pname, action.group('BET'))
                    else:
                        amount = Decimal(action.group('BET'))
                        if sum(hand.bets[street][pname]) == 0 and hand.pot.common[pname] > 0:
                            amount += hand.pot.common[pname]
                        hand.addCallandRaise(street, pname, str(amount))
                else:
                    hand.addBet(street, pname, action.group('BET'))
            elif action.group('ATYPE') == 'AllIn':
                amount = action.group('BET').replace(u',', u'')
                if (Decimal(amount) <= (hand.lastBet[street] - sum(hand.bets[street][pname]))):
                    hand.setUncalledBets(False)
                hand.addAllIn(street, pname, action.group('BET'))
                allIns+=1
            elif action.group('ATYPE') == 'PostedToPlay':
                if Decimal(action.group('BET')) == Decimal(hand.gametype['sb']):
                    hand.addBlind(pname, 'secondsb', action.group('BET'))
                else:
                    amount = str(Decimal(action.group('BET')) + Decimal(action.group('BET'))/2)
                    hand.addBlind(pname, 'both', amount)
            elif action.group('ATYPE') == 'Disconnect':
                pass # Deal with elsewhere
            elif action.group('ATYPE') == 'Reconnect':
                pass # Deal with elsewhere
            elif action.group('ATYPE') == 'MuckCards':
                pass # Deal with elsewhere
            elif action.group('ATYPE') == 'MoneyReturned':
                pass # Deal with elsewhere
            else:
                print (_("DEBUG:") + _("Unimplemented %s: '%s' '%s'") % ("readAction", pname, action.group('ATYPE')))
            #elif action.group('ATYPE') == 'ACTION_ALLIN':
            #    hand.addRaiseBy( street, action.group('PNAME'), action.group('BET') )
            #elif action.group('ATYPE') == 'ACTION_DISCARD':
            #    hand.addDiscard(street, action.group('PNAME'), action.group('NODISCARDED'), action.group('DISCARDED'))
            #elif action.group('ATYPE') == 'ACTION_STAND':
            #    hand.addStandsPat( street, action.group('PNAME'))


    def readShowdownActions(self, hand):
        pass


    def readCollectPot(self,hand):
        
        for m in self.re_CollectPot.finditer(hand.handText):
            pname = self.playerNameFromSeatNo(m.group('SEAT'), hand)
            pot = m.group('POT')
            #print "DEBUG: addCollectPot(%s, %s)" %(pname, m.group('POT'))
            hand.addCollectPot(player=pname, pot=pot)

    def readShownCards(self, hand):
        for shows in self.re_ShownCards.finditer(hand.handText):
            cards = []
            for card in self.re_Card.finditer(shows.group('CARDS')):
                cards.append(self.convertMicroCards(card.group('CARD')))
            (shown, mucked) = (False, False)
            if shows.group('SHOWED') == "ShowCards": shown = True
            elif shows.group('SHOWED') == "MuckCards": mucked = True
            hand.addShownCards(cards, self.playerNameFromSeatNo(shows.group('SEAT'), hand), shown=shown, mucked=mucked)
