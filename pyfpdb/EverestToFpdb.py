#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Copyright 2010-2011, Carl Gherardi
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


class Everest(HandHistoryConverter):
    sitename = "Everest"
    filetype = "text"
    codepage = "utf8"
    siteId   = 16
    copyGameHeader = True

    substitutions = {
                        'LS' : u"\$|\xe2\x82\xac|\u20ac|",
                       'TAB' : u"-\u2013'\s\da-zA-Z",
                       'NUM' : u".,\d\s",
                    }

    # Static regexes
    re_Identify   = re.compile(u'<HAND\stime=\"\d+\"\sid=')
    re_SplitHands = re.compile(r'</HAND>')
    re_TailSplitHands = re.compile(r'(</game>)')
    re_GameInfo = re.compile(u"""<SESSION\stime="\d+"\s
                                    tableName="(?P<TABLE>[%(TAB)s]+)"\s
                                    id="(?P<ID>[\d\.]+)"\s
                                    type="(?P<TYPE>[a-zA-Z ]+)"\s
                                    money="(?P<CURRENCY>[%(LS)s])?"\s
                                    screenName=".+"\s
                                    game="(?P<GAME>hold\-em|omaha\-hi)"\s
                                    gametype="(?P<LIMIT>[-a-zA-Z ]+)"/>
                                """ % substitutions, re.VERBOSE|re.MULTILINE)
    re_HandInfo = re.compile(u"""time="(?P<DATETIME>[0-9]+)"\s
                                 id="(?P<HID>[0-9]+)"\s
                                 index="\d+?"\s
                                 blinds="([%(LS)s]?(?P<SB>[%(NUM)s]+)\s?[%(LS)s]?/[%(LS)s]?(?P<BB>[%(NUM)s]+)\s?[%(LS)s]?)"
                                """ % substitutions, re.VERBOSE|re.MULTILINE)
    re_Button = re.compile(r'<DEALER position="(?P<BUTTON>[0-9]+)"\/>')
    re_PlayerInfo = re.compile(r'<SEAT position="(?P<SEAT>[0-9]+)" name="(?P<PNAME>.+)" balance="(?P<CASH>[.0-9]+)"/>', re.MULTILINE)
    re_Board = re.compile(r'(?P<CARDS>.+)<\/COMMUNITY>', re.MULTILINE)

    # The following are also static regexes: there is no need to call
    # compilePlayerRegexes (which does nothing), since players are identified
    # not by name but by seat number
    re_PostXB = re.compile(r'<BLIND position="(?P<PSEAT>[0-9]+)" amount="(?P<XB>[0-9]+)" penalty="(?P<PENALTY>[0-9]+)"\/>', re.MULTILINE)
    re_Antes = re.compile(r'<ANTE position="(?P<PSEAT>[0-9])" amount="(?P<ANTE>[.0-9]+)"/>', re.MULTILINE)
    #re_BringIn = ???
    re_HeroCards = re.compile(r'<HOLE position="(?P<PSEAT>[0-9])">(?P<CARD>[^-]+)</HOLE>', re.MULTILINE)
    re_Action = re.compile(r'<(?P<ATYPE>FOLD|BET) position="(?P<PSEAT>[0-9])"( amount="(?P<BET>[.0-9]+)")?( allin="1")?/>', re.MULTILINE)
    re_ShowdownAction = re.compile(r'<cards type="SHOWN" cards="(?P<CARDS>..,..)" player="(?P<PSEAT>[0-9])"/>', re.MULTILINE)
    re_CollectPot = re.compile(r'<WIN position="(?P<PSEAT>[0-9])" amount="(?P<POT>[.0-9]+)" pot="[0-9]+"', re.MULTILINE)
    re_SitsOut = re.compile(r'<event sequence="[0-9]+" type="SIT_OUT" player="(?P<PSEAT>[0-9])"/>', re.MULTILINE)
    re_ShownCards = re.compile(r'<(?P<SHOW>SHOW|MUCK) position="(?P<PSEAT>[0-9])">(?P<CARDS>.+)?</(SHOW|MUCK)>', re.MULTILINE)
    re_Prize = re.compile(r'\s?<(CHAT|PRIZE|PLACE)', re.MULTILINE)

    def compilePlayerRegexs(self, hand):
        pass

    def playerNameFromSeatNo(self, seatNo, hand):
        # Actions recorded by seat number, not by the player's name
        for p in hand.players:
            if p[0] == seatNo:
                return p[1]

    def readSupportedGames(self):
        return [
                ["ring", "hold", "nl"],
                ["ring", "hold", "fl"],
                ["ring", "hold", "pl"],
                
                ["tour", "hold", "nl"],
                ["tour", "hold", "fl"],
                ["tour", "hold", "pl"]
               ]

    def parseHeader(self, handText, whole_file):
        gametype = self.determineGameType(handText)
        if gametype is None:
            gametype = self.determineGameType(whole_file)
            if gametype is None:
                tmp = handText[0:200]
                log.error(_("EverestToFpdb.determineGameType: Unable to recognise gametype from: '%s'") % tmp)
                raise FpdbParseError
            elif not gametype:
                raise FpdbHandPartial
        elif not gametype:
            raise FpdbHandPartial
        return gametype

    def determineGameType(self, handText):
        
        m = self.re_GameInfo.search(handText)
        m2 = self.re_HandInfo.search(handText)
        if not m: return None
        if not m2: return False

        self.info = {}
        mg = m.groupdict()
        mg.update(m2.groupdict())
        #print "DEBUG: mg: %s" % mg

        limits = { 'no-limit':'nl', 'fixed-limit':'fl', 'limit':'fl', 'pot-limit':'pl' }
        games = {              # base, category
                    'hold-em' : ('hold','holdem'),
                   'omaha-hi' : ('hold','omahahi'),
                }

        if 'LIMIT' in mg:
            self.info['limitType'] = limits[mg['LIMIT']]
        if 'GAME' in mg:
            (self.info['base'], self.info['category']) = games[mg['GAME']]
        if 'SB' in mg:
            sb = self.clearMoneyString(mg['SB'])
            self.info['sb'] = sb
        if 'BB' in mg:
            bb = self.clearMoneyString(mg['BB'])
            self.info['bb'] = bb
        
        if mg['TYPE']=='ring':
            self.info['type'] = 'ring'
        else:
            self.info['type'] = 'tour'
            self.info['tourNo'] = mg['ID']
            
        if mg['CURRENCY'] == u'$':
            self.info['currency'] = 'USD'   
        elif mg['CURRENCY'] == u'\u20ac':
            self.info['currency'] = 'EUR'
        elif not mg['CURRENCY']:
            self.info['currency'] = 'play'
        
        # HACK - tablename not in every hand.
        self.info['TABLENAME'] = mg['TABLE']

        return self.info

    def readHandInfo(self, hand):
        m = self.re_HandInfo.search(hand.handText)
        if m is None:
            if self.re_Prize.match(hand.handText):
                raise FpdbHandPartial
            tmp = hand.handText[0:200]
            log.error(_("EverestToFpdb.readHandInfo: '%s'") % tmp)
            raise FpdbParseError
        mg = m.groupdict()
        hand.handid = m.group('HID')
        hand.tablename = self.info['TABLENAME']
        if hand.gametype['type'] == 'tour':
            hand.tourNo = self.info['tourNo']
            hand.buyin = 0
            hand.fee = 0
            hand.buyinCurrency="NA"
            tablesplit = re.split("-", self.info['TABLENAME'])
            if len(tablesplit)>1:
                hand.tablename = tablesplit[1]
        if 'SB' in mg:
            sb = self.clearMoneyString(mg['SB'])
            hand.gametype['sb'] = sb
        if 'BB' in mg:
            bb = self.clearMoneyString(mg['BB'])
            hand.gametype['bb'] = bb

        if hand.maxseats==None:
            if hand.gametype['type'] == 'tour' and self.maxseats==0:
                hand.maxseats = self.guessMaxSeats(hand)
                self.maxseats = hand.maxseats
            elif hand.gametype['type'] == 'tour':
                hand.maxseats = self.maxseats
            else:
                hand.maxseats = None
        #FIXME: u'DATETIME': u'1291155932'
        hand.startTime = datetime.datetime.fromtimestamp(float(m.group('DATETIME')))
        #hand.startTime = datetime.datetime.strptime('201102091158', '%Y%m%d%H%M')
        #hand.startTime = datetime.datetime.strptime(m.group('DATETIME')[:12], '%Y%m%d%H%M')

    def readPlayerStacks(self, hand):
        m = self.re_PlayerInfo.finditer(hand.handText)
        for a in m:
            stack = Decimal(a.group('CASH'))
            stackstr = "%.2f" % float(stack/100)
            hand.addPlayer(a.group('SEAT'), a.group('PNAME'), stackstr)

    def markStreets(self, hand):
        #if hand.gametype['base'] == 'hold':
        
        m =  re.search(r"<DEALER (?P<PREFLOP>.+?(?=<COMMUNITY>)|.+)"
                       r"(<COMMUNITY>(?P<FLOP>\S\S\S?, \S\S\S?, \S\S\S?<\/COMMUNITY>.+?(?=<COMMUNITY>)|.+))?"
                       r"(<COMMUNITY>(?P<TURN>\S\S\S?<\/COMMUNITY>.+?(?=<COMMUNITY>)|.+))?"
                       r"(<COMMUNITY>(?P<RIVER>\S\S\S?<\/COMMUNITY>.+?(?=<WIN>)|.+))?", hand.handText,re.DOTALL)
        #import pprint
        #pp = pprint.PrettyPrinter(indent=4)
        #pp.pprint(m.groupdict())
        hand.addStreets(m)

    def readCommunityCards(self, hand, street):
        m = self.re_Board.search(hand.streets[street])
        if street == 'FLOP':
            cards = [c.replace('10', 'T').strip() for c in m.group('CARDS').split(',')]
            hand.setCommunityCards(street, cards)
        elif street in ('TURN','RIVER'):
            cards = [c.replace('10', 'T').strip() for c in m.group('CARDS').split(',')]
            hand.setCommunityCards(street, cards)

    def readAntes(self, hand):
        m = self.re_Antes.finditer(hand.handText)
        for player in m:
            amount = "%.2f" % float(float(player.group('ANTE'))/100)
            hand.addAnte(self.playerNameFromSeatNo(player.group('PSEAT'), hand), amount)

    def readBringIn(self, hand):
        pass # ???

    def readBlinds(self, hand):
        i = 0
        for a in self.re_PostXB.finditer(hand.handText):
            amount = "%.2f" % float(float(a.group('XB'))/100)
            both = "%.2f" % (float(float(a.group('PENALTY'))/100) + float(float(a.group('XB'))/100))
            if i==1 and Decimal(a.group('XB'))/100 == Decimal(hand.gametype['bb'])*2:
                hand.gametype['sb'] = hand.gametype['bb']
                hand.gametype['bb'] = str(Decimal(a.group('XB'))/100)
            if i==0:
                hand.addBlind(self.playerNameFromSeatNo(a.group('PSEAT'), hand),'small blind', amount)
            elif i>0 and a.group('PENALTY')=='0':
                hand.addBlind(self.playerNameFromSeatNo(a.group('PSEAT'), hand),'big blind', amount)
            elif i>0 and a.group('PENALTY')!='0':
                hand.addBlind(self.playerNameFromSeatNo(a.group('PSEAT'), hand),'both', both)
            i += 1

    def readButton(self, hand):
        hand.buttonpos = int(self.re_Button.search(hand.handText).group('BUTTON'))

    def readHoleCards(self, hand):
        cards = []
        for m in self.re_HeroCards.finditer(hand.handText):
            hand.hero = self.playerNameFromSeatNo(m.group('PSEAT'), hand)
            cards.append(m.group('CARD').replace('10', 'T'))
        if cards:
            #print "DEBUG: addHoleCards(%s, %s, %s)" %('PREFLOP', hand.hero, cards)
            hand.addHoleCards('PREFLOP', hand.hero, closed=cards, shown=False,mucked=False, dealt=True)

    def readAction(self, hand, street):
        #print "DEBUG: readAction (%s)" % street
        m = self.re_Action.finditer(hand.streets[street])
        curr_pot = Decimal('0')
        for action in m:
            #print " DEBUG: %s %s" % (action.group('ATYPE'), action.groupdict())
            player = self.playerNameFromSeatNo(action.group('PSEAT'), hand)
            if action.group('ATYPE') == 'BET':
                amount = Decimal(action.group('BET'))
                amountstr = "%.2f" % float(amount/100)
                #Gah! BET can mean check, bet, call or raise...
                if action.group('BET') == '0':
                    hand.addCheck(street, player)
                elif amount > 0 and curr_pot == 0:
                    # Open
                    curr_pot = amount
                    hand.addBet(street, player, amountstr)
                elif Decimal(action.group('BET')) > 0 and curr_pot > 0:
                    # Raise or call
                    if amount > curr_pot:
                        # Raise
                        curr_pot = amount
                        hand.addCallandRaise(street, player, amountstr)
                    elif amount <= curr_pot:
                        # Call
                        hand.addCall(street, player, amountstr)
            elif action.group('ATYPE') in ('FOLD', 'SIT_OUT'):
                hand.addFold(street, player)
            else:
                print (_("Unimplemented %s: '%s' '%s'") % ("readAction", action.group('PSEAT'), action.group('ATYPE')))
                log.debug(_("Unimplemented %s: '%s' '%s'") % ("readAction", action.group('PSEAT'), action.group('ATYPE')))

    def readShowdownActions(self, hand):
        for shows in self.re_ShowdownAction.finditer(hand.handText):
            cards = shows.group('CARDS').split(',')
            hand.addShownCards(cards,
                               self.playerNameFromSeatNo(shows.group('PSEAT'),
                                                         hand))

    def readCollectPot(self, hand):
        for m in self.re_CollectPot.finditer(hand.handText):
            player = self.playerNameFromSeatNo(m.group('PSEAT'), hand)
            amount = Decimal(m.group('POT'))
            amountstr = "%.2f" % float(amount/100)
            #print "DEBUG: %s collects %s" % (player, m.group('POT'))
            hand.addCollectPot(player, amountstr)

    def readShownCards(self, hand):
        for m in self.re_ShownCards.finditer(hand.handText):
            name = self.playerNameFromSeatNo(m.group('PSEAT'), hand)
            if name != hand.hero:
                show = False
                muck = False
                if m.group('SHOW')=='SHOW': show=True
                if m.group('SHOW')=='MUCK': muck=True
                cards = [c.replace('10', 'T').strip() for c in m.group('CARDS').split(',')]
                hand.addShownCards(cards=cards, player=name, shown=show, mucked=show)

