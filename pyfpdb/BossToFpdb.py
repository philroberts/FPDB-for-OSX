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

# Boss HH Format

class Boss(HandHistoryConverter):

    sitename = "Boss"
    filetype = "text"
    codepage = ("utf8", "cp1252")
    siteId   = 4
    
    Lim_Blinds = {      '0.20': ('0.05','0.10'),        '0.50': ('0.13', '0.25'),
                        '1.00': ('0.25', '0.50'),          '1': ('0.25', '0.50'),
                        '2.00': ('0.50', '1.00'),          '2': ('0.50', '1.00'),
                        '4.00': ('1.00', '2.00'),          '4': ('1.00', '2.00'),
                        '6.00': ('1.50', '3.00'),          '6': ('1.50', '3.00'),
                        '8.00': ('2.00', '4.00'),          '8': ('2.00', '4.00'),
                       '10.00': ('2.50', '5.00'),         '10': ('2.50', '5.00'),
                       '16.00': ('4.00', '8.00'),         '16': ('4.00', '8.00'),
                       '20.00': ('5.00', '10.00'),        '20': ('5.00', '10.00'),
                       '30.00': ('7.50', '15.00'),        '30': ('7.50', '15.00'),
                       '40.00': ('10.00', '20.00'),       '40': ('10.00', '20.00'),
                       '60.00': ('15.00', '30.00'),       '60': ('15.00', '30.00'),
                       '80.00': ('20.00', '40.00'),       '80': ('20.00', '40.00'),
                      '100.00': ('25.00', '50.00'),      '100': ('25.00', '50.00'),
                      '200.00': ('50.00', '100.00'),     '200': ('50.00', '100.00'),
                      '400.00': ('100.00', '200.00'),    '400': ('100.00', '200.00'),
                      '800.00': ('200.00', '400.00'),    '800': ('200.00', '400.00'),
                      '1000.00': ('250.00', '500.00'),  '1000': ('250.00', '500.00'),
                      '2000.00': ('500.00', '1000.00'), '2000': ('500.00', '1000.00'),
                  }

    # Static regexes
    re_GameInfo     = re.compile("""<HISTORY\sID="(?P<HID>[0-9]+)"\s
                                    SESSION="session(?P<SESSIONID>[0-9]+)\.xml"\s
                                    TABLE="(?P<TABLE>.+?)"\s
                                    GAME="(?P<GAME>GAME_THM|GAME_OMA|GAME_FCD|GAME_OMAHL|GAME_OMATU)"\sGAMETYPE="[_a-zA-Z]+"\s
                                    GAMEKIND="(?P<GAMEKIND>[_a-zA-Z]+)"\s
                                    TABLECURRENCY="(?P<CURRENCY>[A-Z]+)"\s
                                    LIMIT="(?P<LIMIT>NL|PL|FL)"\s
                                    STAKES="(?P<SB>[.0-9]+)/(?P<BB>[.0-9]+)"\s
                                    DATE="(?P<DATETIME>[0-9]+)"\s
                                    (TABLETOURNEYID=".*?"\s)?
                                    WIN="[.0-9]+"\sLOSS="[.0-9]+"
                                    """, re.MULTILINE| re.VERBOSE)
    re_Identify     = re.compile(u'<HISTORY\sID="\d+"\sSESSION=')
    re_SplitHands   = re.compile('</HISTORY>')
    re_Button       = re.compile('<ACTION TYPE="HAND_DEAL" PLAYER="(?P<BUTTON>[^"]+)">\n<CARD LINK="[0-9b]+"></CARD>\n<CARD LINK="[0-9b]+"></CARD></ACTION>\n<ACTION TYPE="ACTION_', re.MULTILINE)
    re_PlayerInfo   = re.compile('^<PLAYER NAME="(?P<PNAME>.+)" SEAT="(?P<SEAT>[0-9]+)" AMOUNT="(?P<CASH>[.0-9]+)"( STATE="(?P<STATE>STATE_EMPTY|STATE_PLAYING|STATE_SITOUT)" DEALER="(Y|N)")?></PLAYER>', re.MULTILINE)
    re_Card        = re.compile('^<CARD LINK="(?P<CARD>[0-9]+)"></CARD>', re.MULTILINE)
    re_BoardLast    = re.compile('^<CARD LINK="(?P<CARD>[0-9]+)"></CARD></ACTION>', re.MULTILINE)
    

    # we need to recompile the player regexs.
    player_re = '(?P<PNAME>[^"]+)'
    #logging.debug("player_re: " + player_re)
    #<ACTION TYPE="HAND_BLINDS" PLAYER="prato" KIND="HAND_SB" VALUE="0.25"></ACTION>

    re_PostSB           = re.compile(r'^<ACTION TYPE="HAND_BLINDS" PLAYER="%s" KIND="HAND_SB" VALUE="(?P<SB>[.0-9]+)"></ACTION>' %  player_re, re.MULTILINE)
    re_PostBB           = re.compile(r'^<ACTION TYPE="HAND_BLINDS" PLAYER="%s" KIND="HAND_BB" VALUE="(?P<BB>[.0-9]+)"></ACTION>' %  player_re, re.MULTILINE)
    re_Antes            = re.compile(r'^<ACTION TYPE="HAND_ANTE" PLAYER="%s" VALUE="(?P<ANTE>[.0-9]+)"></ACTION>' % player_re, re.MULTILINE)
    re_BringIn          = re.compile(r"^%s: brings[- ]in( low|) for \$?(?P<BRINGIN>[.0-9]+)" % player_re, re.MULTILINE)
    re_FlopPot          = re.compile(r'^<ACTION TYPE="HAND_BOARD" VALUE="BOARD_FLOP" POT="(?P<POT>[.0-9]+)"', re.MULTILINE)
    re_ShowDownPot      = re.compile(r'^<SHOWDOWN NAME="HAND_SHOWDOWN" POT="(?P<POT>[.0-9]+)"', re.MULTILINE)
    re_PostBoth         = re.compile(r'^<ACTION TYPE="HAND_BLINDS" PLAYER="%s" KIND="HAND_AB" VALUE="(?P<SBBB>[.0-9]+)"></ACTION>' %  player_re, re.MULTILINE)
    
    re_HeroCards        = re.compile(r'PLAYER="%s">(?P<CARDS>(\s+<CARD LINK="[0-9]+"></CARD>){2,5})</ACTION>' % player_re, re.MULTILINE)

    #'^<ACTION TYPE="(?P<ATYPE>[_A-Z]+)" PLAYER="%s"( VALUE="(?P<BET>[.0-9]+)")?></ACTION>'
    re_Action           = re.compile(r'^<ACTION TYPE="(?P<ATYPE>[_A-Z]+)" PLAYER="%s"( VALUE="(?P<BET>[.0-9]+)")?></ACTION>' %  player_re, re.MULTILINE)

    re_ShowdownAction   = re.compile(r'<RESULT (WINTYPE="WINTYPE_(HILO|LO|HI)" )?PLAYER="%s" WIN="[.\d]+" HAND="(?P<HAND>\(\$STR_G_FOLD\)|[\$\(\)_ A-Z]+)".+?>(?P<CARDS>(\s+<CARD LINK="[0-9]+"></CARD>){2,5})</RESULT>' %  player_re, re.MULTILINE)
    #<RESULT PLAYER="wig0r" WIN="4.10" HAND="$(STR_G_WIN_TWOPAIR) $(STR_G_CARDS_TENS) $(STR_G_ANDTEXT) $(STR_G_CARDS_EIGHTS)">
    #
    re_CollectPot       = re.compile(r'<RESULT (WINTYPE="WINTYPE_(HILO|LO|HI)" )?PLAYER="%s" WIN="(?P<POT>[.\d]+)" HAND=".+"' %  player_re, re.MULTILINE)

    def compilePlayerRegexs(self,  hand):
        pass

    def readSupportedGames(self):
        return [["ring", "hold", "nl"],
                ["ring", "hold", "pl"],
                ["ring", "hold", "fl"],
                ["ring", "stud", "fl"],
                ["ring", "draw", "fl"],
                ["tour", "hold", "fl"],
                ["tour", "hold", "pl"],
                ["tour", "hold", "nl"],
               ]

    def determineGameType(self, handText):
        info = {}
        m = self.re_GameInfo.search(handText)
        if not m:
            tmp = handText[0:200]
            log.error(_("BossToFpdb.determineGameType: '%s'") % tmp)
            raise FpdbParseError

        mg = m.groupdict()
        #print "DEBUG: mg: %s" % mg
        
        # translations from captured groups to our info strings
        #limits = { 'NL':'nl', 'PL':'pl', 'Limit':'fl' }
        limits = { 'NL':'nl', 'PL':'pl', 'FL':'fl'}
        games = {              # base, category
                  "GAME_THM" : ('hold','holdem'), 
                  "GAME_OMA" : ('hold','omahahi'),
                "GAME_OMATU" : ('hold','omahahi'),
                "GAME_OMAHL" : ('hold','omahahilo'),
                  "GAME_FCD" : ('draw','fivedraw'),
                }
        if 'GAMEKIND' in mg:
            info['type'] = 'ring'
            if mg['GAMEKIND'] == 'GAMEKIND_TOURNAMENT':
                info['type'] = 'tour'
        if 'LIMIT' in mg:
            info['limitType'] = limits[mg['LIMIT']]
        if 'GAME' in mg:
            (info['base'], info['category']) = games[mg['GAME']]
        if 'SB' in mg:
            info['sb'] = mg['SB']
        if 'BB' in mg:
            info['bb'] = mg['BB']
        if 'CURRENCY' in mg:
            info['currency'] = mg['CURRENCY']
        # NB: SB, BB must be interpreted as blinds or bets depending on limit type.
        if info['limitType'] == 'fl' and info['bb'] is not None:
            if info['type'] == 'ring':
                try:
                    info['sb'] = self.Lim_Blinds[mg['BB']][0]
                    info['bb'] = self.Lim_Blinds[mg['BB']][1]
                except KeyError:
                    tmp = handText[0:200]
                    log.error(_("BossToFpdb.determineGameType: Lim_Blinds has no lookup for '%s' - '%s'") % (mg['BB'], tmp))
                    raise FpdbParseError
            else:
                info['sb'] = str((Decimal(mg['SB'])/2).quantize(Decimal("0.01")))
                info['bb'] = str(Decimal(mg['SB']).quantize(Decimal("0.01")))
        return info


    def readHandInfo(self, hand):
        info = {}
        m = self.re_GameInfo.search(hand.handText)

        if m is None:
            tmp = hand.handText[0:200]
            log.error(_("BossToFpdb.readHandInfo: '%s'") % tmp)
            raise FpdbParseError

        info.update(m.groupdict())
        m = self.re_Button.search(hand.handText)
        if m: info.update(m.groupdict())

        for key in info:
            if key == 'DATETIME':
                # Boss uses UTC timestamp
                hand.startTime = datetime.datetime.fromtimestamp(int(info[key]))
            if key == 'HID':
                hand.handid = info[key]
            if key == 'TABLE':
                if hand.gametype['type'] == 'tour':
                    hand.tablename = '1'
                else:
                    hand.tablename = info[key]
            if key == 'BUTTON':
                hand.buttonpos = info[key]
            if key == 'LEVEL':
                hand.level = info[key]
            if hand.gametype['type'] == 'tour':
                if key == 'SESSIONID': # No idea why Boss doesn't use the TABLETOURNEYID xml field...
                    hand.tourNo = info[key]
                if key == 'CURRENCY' and not hand.buyinCurrency:
                    hand.buyinCurrency = info[key]
                # Hmm. Other useful tourney info doesn't appear to be readily available.
                hand.buyin = 0
                hand.fee = 0
                if key == 'TABLE':
                    if 'FREE' in info[key]:
                        hand.buyinCurrency = 'FREE'
                    else:                       
                        hand.buyinCurrency = 'NA'
        
    def readButton(self, hand):
        m = self.re_Button.search(hand.handText)
        if m:
            for player in hand.players:
                if player[1] == m.group('BUTTON'):
                    hand.buttonpos = player[0]
                    break

    def readPlayerStacks(self, hand):
        m = self.re_PlayerInfo.finditer(hand.handText)
        players = []
        for a in m:
            hand.addPlayer(int(a.group('SEAT')), a.group('PNAME'), a.group('CASH'))

    def markStreets(self, hand):
        # PREFLOP = ** Dealing down cards **
        # This re fails if,  say, river is missing; then we don't get the ** that starts the river.
        if hand.gametype['base'] in ("hold"):
            m =  re.search('<ACTION TYPE="HAND_BLINDS" PLAYER=".+" KIND="(HAND_BB|HAND_SB)" VALUE="[.0-9]+"></ACTION>(?P<PREFLOP>.+(?=<ACTION TYPE="HAND_BOARD" VALUE="BOARD_FLOP")|.+)'
                       '((?P<FLOP><ACTION TYPE="HAND_BOARD" VALUE="BOARD_FLOP" POT="[.0-9]+".+?>.+(?=<ACTION TYPE="HAND_BOARD" VALUE="BOARD_TURN")|.+))?'
                       '((?P<TURN><ACTION TYPE="HAND_BOARD" VALUE="BOARD_TURN" POT="[.0-9]+".+?>.+(?=<ACTION TYPE="HAND_BOARD" VALUE="BOARD_RIVER")|.+))?'
                       '((?P<RIVER><ACTION TYPE="HAND_BOARD" VALUE="BOARD_RIVER" POT="[.0-9]+".+?>.+(?=<SHOWDOWN NAME="HAND_SHOWDOWN")|.+))?', hand.handText,re.DOTALL)
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
            if street == 'FLOP':
                m = self.re_Card.findall(hand.streets[street])
                for card in m:
                    boardCards.append(self.convertBossCards(card))
            else:
                m = self.re_BoardLast.search(hand.streets[street])
                boardCards.append(self.convertBossCards(m.group('CARD')))

            hand.setCommunityCards(street, boardCards)

    def readAntes(self, hand):
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
                # Post dead blinds as ante
                hand.addBlind(a.group('PNAME'), 'secondsb', a.group('SB'))
        for a in self.re_PostBB.finditer(hand.handText):
            hand.addBlind(a.group('PNAME'), 'big blind', a.group('BB'))
        for a in self.re_PostBoth.finditer(hand.handText):
            hand.addBlind(a.group('PNAME'), 'both', a.group('SBBB'))

    def readHeroCards(self, hand):
#    streets PREFLOP, PREDRAW, and THIRD are special cases beacause
#    we need to grab hero's cards
        for street in ('PREFLOP', 'DEAL'):
            if street in hand.streets.keys():
                m = self.re_HeroCards.finditer(hand.streets[street])
                newcards = []
                for found in m:
                    hand.hero = found.group('PNAME')
                    for card in self.re_Card.finditer(found.group('CARDS')):
                        newcards.append(self.convertBossCards(card.group('CARD')))
                    hand.addHoleCards(street, hand.hero, closed=newcards, shown=False, mucked=False, dealt=True)

    def convertBossCards(self, card):
        card = int(card)
        retCard = ''
        cardconvert = { 1:'A',
                       10:'T',
                       11:'J',
                       12:'Q',
                       13:'K'}
        realNumber = card % 13 + 1
        if(realNumber in cardconvert):
            retCard += cardconvert[realNumber]
        else:
            retCard += str(realNumber)
       
        if(card > 38):
            retCard += 's'
        elif(card > 25):
            retCard += 'h'
        elif(card > 12):
            retCard += 'c'
        else:
            retCard += 'd'
            
        return(retCard)
    
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
        m = self.re_Action.finditer(hand.streets[street])
        for action in m:
            if action.group('ATYPE') == 'ACTION_FOLD':
                hand.addFold( street, action.group('PNAME'))
            elif action.group('ATYPE') == 'ACTION_CHECK':
                hand.addCheck( street, action.group('PNAME'))
            elif action.group('ATYPE') == 'ACTION_CALL':
                bet = action.group('BET') 
                hand.addCallTo(street, action.group('PNAME'), bet )
            elif action.group('ATYPE') == 'ACTION_RAISE':
                bet = action.group('BET') 
                hand.addRaiseTo( street, action.group('PNAME'), bet)
            elif action.group('ATYPE') == 'ACTION_BET':
                hand.addBet( street, action.group('PNAME'), action.group('BET') )
            elif action.group('ATYPE') == 'ACTION_DISCARD':
                hand.addDiscard(street, action.group('PNAME'), action.group('NODISCARDED'), action.group('DISCARDED'))
            elif action.group('ATYPE') == 'ACTION_STAND':
                hand.addStandsPat( street, action.group('PNAME'))
            elif action.group('ATYPE') == 'ACTION_ALLIN':
                bet = action.group('BET')
                player = action.group('PNAME')
                hand.checkPlayerExists(action.group('PNAME'), 'addAllIn')
                bet = bet.replace(u',', u'') #some sites have commas
                Ai = Decimal(bet)
                Bp = hand.lastBet[street]
                if Ai <= Bp:
                    hand.addCallTo(street, player, bet)
                elif Bp == 0:
                    hand.addBet(street, player, bet)
                else:
                    hand.addRaiseTo( street, player, bet)
            else:
                print (_("DEBUG:") + _("Unimplemented %s: '%s' '%s'") % ("readAction", action.group('PNAME'), action.group('ATYPE')))
        self.calculateAntes(street, hand)
                
    def calculateAntes(self, street, hand):
        if street in ('PREFLOP', 'DEAL', 'THIRD'):
            contributed = sum(hand.pot.committed.values()) + sum(hand.pot.common.values())
            committed = sorted([ (v,k) for (k,v) in hand.pot.committed.items()])
            try:
                lastbet = committed[-1][0] - committed[-2][0]
                if lastbet > 0: # uncalled
                    contributed -= lastbet
            except IndexError, e:
                log.error(_("BossToFpdb.calculateAntes(): '%s': Major failure while calculating pot: '%s'") % (self.handid, e))
                raise FpdbParseError
            m = self.re_FlopPot.search(hand.handText)
            if not m:
                m = self.re_ShowDownPot.search(hand.handText)
            if m:
                pot = Decimal(m.groupdict()['POT'])
                ante = (pot-contributed)/len(hand.players)
                for player in hand.players:
                    if ante>0:
                        hand.addAnte(player[1], str(ante))

    def readShowdownActions(self, hand):
        for shows in self.re_ShowdownAction.finditer(hand.handText):
            showdownCards = []
            for card in self.re_Card.finditer(shows.group('CARDS')):
                #print "DEBUG:", card, card.group('CARD'), self.convertBossCards(card.group('CARD'))
                showdownCards.append(self.convertBossCards(card.group('CARD')))
            
            hand.addShownCards(showdownCards, shows.group('PNAME'))

    def readCollectPot(self,hand):
        for m in self.re_CollectPot.finditer(hand.handText):
            potcoll = Decimal(m.group('POT'))
            if potcoll > 0:
                 hand.addCollectPot(player=m.group('PNAME'),pot=potcoll)

    def readShownCards(self,hand):
        pass
