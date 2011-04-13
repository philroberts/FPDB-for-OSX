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

# Win2day HH Format

class Win2day(HandHistoryConverter):

    sitename = "Win2day"
    filetype = "text"
    codepage = "utf-8"
    siteID   = 4

    # Static regexes
    re_GameInfo     = re.compile("""<HISTORY\sID="(?P<HID>[0-9]+)"\sSESSION="session[0-9]+\.xml"\s
                                    TABLE="(?P<TABLE>[-\sa-zA-Z0-9\xc0-\xfc/.]+)"\s
                                    GAME="(?P<GAME>[_A-Z]+)"\sGAMETYPE="[_a-zA-Z]+"\sGAMEKIND="[_a-zA-Z]+"\s
                                    TABLECURRENCY="(?P<CURRENCY>[A-Z]+)"\s
                                    LIMIT="(?P<LIMIT>NL|PL)"\s
                                    STAKES="(?P<SB>[.0-9]+)/(?P<BB>[.0-9]+)"\s
                                    DATE="(?P<DATETIME>[0-9]+)"\s
                                    (TABLETOURNEYID=""\s)?
                                    WIN="[.0-9]+"\sLOSS="[.0-9]+"
                                    """, re.MULTILINE| re.VERBOSE)
    re_SplitHands   = re.compile('</HISTORY>')
    re_HandInfo     = re.compile("^Table \'(?P<TABLE>[- a-zA-Z]+)\'(?P<TABLEATTRIBUTES>.+?$)?", re.MULTILINE)
    re_Button       = re.compile('<ACTION TYPE="HAND_DEAL" PLAYER="(?P<BUTTON>[^"]+)">\n<CARD LINK="[0-9b]+"></CARD>\n<CARD LINK="[0-9b]+"></CARD></ACTION>\n<ACTION TYPE="ACTION_', re.MULTILINE)
    #<PLAYER NAME="prato" SEAT="1" AMOUNT="61.29"></PLAYER>
    re_PlayerInfo   = re.compile('^<PLAYER NAME="(?P<PNAME>.*)" SEAT="(?P<SEAT>[0-9]+)" AMOUNT="(?P<CASH>[.0-9]+)"></PLAYER>', re.MULTILINE)
    re_Card        = re.compile('^<CARD LINK="(?P<CARD>[0-9]+)"></CARD>', re.MULTILINE)
    re_BoardLast    = re.compile('^<CARD LINK="(?P<CARD>[0-9]+)"></CARD></ACTION>', re.MULTILINE)
    

    def compilePlayerRegexs(self,  hand):
        players = set([player[1] for player in hand.players])
        if not players <= self.compiledPlayers: # x <= y means 'x is subset of y'
            # we need to recompile the player regexs.
            self.compiledPlayers = players
            player_re = "(?P<PNAME>" + "|".join(map(re.escape, players)) + ")"
            logging.debug("player_re: " + player_re)
            #<ACTION TYPE="HAND_BLINDS" PLAYER="prato" KIND="HAND_SB" VALUE="0.25"></ACTION>

            self.re_PostSB           = re.compile(r'^<ACTION TYPE="HAND_BLINDS" PLAYER="%s" KIND="HAND_SB" VALUE="(?P<SB>[.0-9]+)"></ACTION>' %  player_re, re.MULTILINE)
            self.re_PostBB           = re.compile(r'^<ACTION TYPE="HAND_BLINDS" PLAYER="%s" KIND="HAND_BB" VALUE="(?P<BB>[.0-9]+)"></ACTION>' %  player_re, re.MULTILINE)
            self.re_Antes            = re.compile(r"^%s: posts the ante \$?(?P<ANTE>[.0-9]+)" % player_re, re.MULTILINE)
            self.re_BringIn          = re.compile(r"^%s: brings[- ]in( low|) for \$?(?P<BRINGIN>[.0-9]+)" % player_re, re.MULTILINE)
            self.re_PostBoth         = re.compile(r'^<ACTION TYPE="HAND_BLINDS" PLAYER="%s" KIND="HAND_AB" VALUE="(?P<SBBB>[.0-9]+)"></ACTION>' %  player_re, re.MULTILINE)
    
            #r'<ACTION TYPE="HAND_DEAL" PLAYER="%s">\n<CARD LINK="(?P<CARD1>[0-9]+)"></CARD>\n<CARD LINK="(?P<CARD2>[0-9]+)"></CARD></ACTION>'
            self.re_HeroCards        = re.compile(r'<ACTION TYPE="HAND_DEAL" PLAYER="%s">\n(?P<CARDS><CARD LINK="[0-9]+"></CARD>\n<CARD LINK="[0-9]+"></CARD>)</ACTION>' % player_re, re.MULTILINE)
            
            #'^<ACTION TYPE="(?P<ATYPE>[_A-Z]+)" PLAYER="%s"( VALUE="(?P<BET>[.0-9]+)")?></ACTION>'
            self.re_Action           = re.compile(r'^<ACTION TYPE="(?P<ATYPE>[_A-Z]+)" PLAYER="%s"( VALUE="(?P<BET>[.0-9]+)")?></ACTION>' %  player_re, re.MULTILINE)

            self.re_ShowdownAction   = re.compile(r'<RESULT PLAYER="%s" WIN="[.0-9]+" HAND="(?P<HAND>\(\$STR_G_FOLD\)|[\$\(\)_ A-Z]+)">\n(?P<CARDS><CARD LINK="[0-9]+"></CARD>\n<CARD LINK="[0-9]+"></CARD>)</RESULT>' %  player_re, re.MULTILINE)
            #<RESULT PLAYER="wig0r" WIN="4.10" HAND="$(STR_G_WIN_TWOPAIR) $(STR_G_CARDS_TENS) $(STR_G_ANDTEXT) $(STR_G_CARDS_EIGHTS)">
            #
            self.re_CollectPot       = re.compile(r'<RESULT PLAYER="%s" WIN="(?P<POT>[.\d]+)" HAND=".+">' %  player_re, re.MULTILINE)
            self.re_sitsOut          = re.compile("^%s sits out" %  player_re, re.MULTILINE)
            self.re_ShownCards       = re.compile("^Seat (?P<SEAT>[0-9]+): %s \(.*\) showed \[(?P<CARDS>.*)\].*" %  player_re, re.MULTILINE)


    def readSupportedGames(self):
        return [["ring", "hold", "nl"],
                ["ring", "hold", "pl"],
                ["ring", "hold", "fl"],
                ["ring", "stud", "fl"],
                ["ring", "draw", "fl"],
                ["ring", "omaha", "pl"]
               ]

    def determineGameType(self, handText):
        info = {'type':'ring'}
        
        m = self.re_GameInfo.search(handText)
        if not m:
            tmp = handText[0:1000]
            log.error(_("Unable to recognise gametype from: '%s'") % tmp)
            log.error("determineGameType: " + _("Raising FpdbParseError"))
            raise FpdbParseError(_("Unable to recognise gametype from: '%s'") % tmp)

        mg = m.groupdict()
        #print "DEBUG: mg: %s" % mg
        
        # translations from captured groups to our info strings
        #limits = { 'NL':'nl', 'PL':'pl', 'Limit':'fl' }
        limits = { 'NL':'nl', 'PL':'pl'}
        games = {              # base, category
                  "GAME_THM" : ('hold','holdem'), 
                  "GAME_OMA" : ('hold','omahahi'),

              #'Omaha Hi/Lo' : ('hold','omahahilo'),
              #       'Razz' : ('stud','razz'), 
              #'7 Card Stud' : ('stud','studhi'),
              #     'Badugi' : ('draw','badugi')
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
            info['currency'] = mg['CURRENCY']
        # NB: SB, BB must be interpreted as blinds or bets depending on limit type.
        
        return info


    def readHandInfo(self, hand):
        info = {}
        m = self.re_HandInfo.search(hand.handText,re.DOTALL)
        if m:
            info.update(m.groupdict())
            # TODO: Be less lazy and parse maxseats from the HandInfo regex
            if m.group('TABLEATTRIBUTES'):
                m2 = re.search("\s*(\d+)-max", m.group('TABLEATTRIBUTES'))
                hand.maxseats = int(m2.group(1))
        m = self.re_GameInfo.search(hand.handText)
        if m: info.update(m.groupdict())
        m = self.re_Button.search(hand.handText)
        if m: info.update(m.groupdict()) 
        # TODO : I rather like the idea of just having this dict as hand.info
        logging.debug("readHandInfo: %s" % info)
        for key in info:
            if key == 'DATETIME':
                # Win2day uses UTC timestamp
                hand.startTime = datetime.datetime.fromtimestamp(int(info[key]))
            if key == 'HID':
                hand.handid = info[key]
            if key == 'TABLE':
                hand.tablename = info[key]
            if key == 'BUTTON':
                hand.buttonpos = info[key]
        
    def readButton(self, hand):
        m = self.re_Button.search(hand.handText)
        if m:
            for player in hand.players:
                if player[1] == m.group('BUTTON'):
                    hand.buttonpos = player[0]
                    break
        else:
            logging.info(_('readButton: not found'))

    def readPlayerStacks(self, hand):
        logging.debug("readPlayerStacks")
        m = self.re_PlayerInfo.finditer(hand.handText)
        players = []
        for a in m:
            hand.addPlayer(int(a.group('SEAT')), a.group('PNAME'), a.group('CASH'))

    def markStreets(self, hand):
        # PREFLOP = ** Dealing down cards **
        # This re fails if,  say, river is missing; then we don't get the ** that starts the river.
        if hand.gametype['base'] in ("hold"):
           #m =  re.search(r"\*\*\* HOLE CARDS \*\*\*(?P<PREFLOP>.+(?=\*\*\* FLOP \*\*\*)|.+)"
           #           r"(\*\*\* FLOP \*\*\*(?P<FLOP> \[\S\S \S\S \S\S\].+(?=\*\*\* TURN \*\*\*)|.+))?"
           #           r"(\*\*\* TURN \*\*\* \[\S\S \S\S \S\S] (?P<TURN>\[\S\S\].+(?=\*\*\* RIVER \*\*\*)|.+))?"
           #           r"(\*\*\* RIVER \*\*\* \[\S\S \S\S \S\S \S\S] (?P<RIVER>\[\S\S\].+))?", hand.handText,re.DOTALL)

            m =  re.search('<ACTION TYPE="HAND_BLINDS" PLAYER=".+" KIND="HAND_BB" VALUE="[.0-9]+"></ACTION>(?P<PREFLOP>.+(?=<ACTION TYPE="HAND_BOARD" VALUE="BOARD_FLOP")|.+)'
                       '((?P<FLOP><ACTION TYPE="HAND_BOARD" VALUE="BOARD_FLOP" POT="[.0-9]+">.+(?=<ACTION TYPE="HAND_BOARD" VALUE="BOARD_TURN")|.+))?'
                       '((?P<TURN><ACTION TYPE="HAND_BOARD" VALUE="BOARD_TURN" POT="[.0-9]+">.+(?=<ACTION TYPE="HAND_BOARD" VALUE="BOARD_RIVER")|.+))?'
                       '((?P<RIVER><ACTION TYPE="HAND_BOARD" VALUE="BOARD_RIVER" POT="[.0-9]+">.+(?=<SHOWDOWN NAME="HAND_SHOWDOWN")|.+))?', hand.handText,re.DOTALL)

        hand.addStreets(m)

    def readCommunityCards(self, hand, street): # street has been matched by markStreets, so exists in this hand
        if street in ('FLOP','TURN','RIVER'):   # a list of streets which get dealt community cards (i.e. all but PREFLOP)
            #print "DEBUG readCommunityCards:", street, hand.streets.group(street)

            boardCards = []
            if street == 'FLOP':
                m = self.re_Card.findall(hand.streets[street])
                for card in m:
                    boardCards.append(self.convertWin2dayCards(card))
            else:
                m = self.re_BoardLast.search(hand.streets[street])
                boardCards.append(self.convertWin2dayCards(m.group('CARD')))

            hand.setCommunityCards(street, boardCards)

    def readAntes(self, hand):
        logging.debug(_("reading antes"))
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
        try:
            m = self.re_PostSB.search(hand.handText)
            hand.addBlind(m.group('PNAME'), 'small blind', m.group('SB'))
        except: # no small blind
            hand.addBlind(None, None, None)
        for a in self.re_PostBB.finditer(hand.handText):
            hand.addBlind(a.group('PNAME'), 'big blind', a.group('BB'))
        for a in self.re_PostBoth.finditer(hand.handText):
            hand.addBlind(a.group('PNAME'), 'both', a.group('SBBB'))

    def readHeroCards(self, hand):
#    streets PREFLOP, PREDRAW, and THIRD are special cases beacause
#    we need to grab hero's cards
        m = self.re_HeroCards.finditer(hand.streets['PREFLOP'])
        newcards = []
        for found in m:
            hand.hero = found.group('PNAME')
            for card in self.re_Card.finditer(found.group('CARDS')):
                #print self.convertWin2dayCards(card.group('CARD'))
                newcards.append(self.convertWin2dayCards(card.group('CARD')))
            
                    #hand.addHoleCards(holeCards, m.group('PNAME'))
            hand.addHoleCards('PREFLOP', hand.hero, closed=newcards, shown=False, mucked=False, dealt=True)

    def convertWin2dayCards(self, card):
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
            if action.group('ATYPE') == 'ACTION_RAISE':
                hand.addRaiseBy( street, action.group('PNAME'), action.group('BET') )
            elif action.group('ATYPE') == 'ACTION_CALL':
                hand.addCall( street, action.group('PNAME'), action.group('BET') )
            elif action.group('ATYPE') == 'ACTION_ALLIN':
                hand.addRaiseBy( street, action.group('PNAME'), action.group('BET') )
            elif action.group('ATYPE') == 'ACTION_BET':
                hand.addBet( street, action.group('PNAME'), action.group('BET') )
            elif action.group('ATYPE') == 'ACTION_FOLD':
                hand.addFold( street, action.group('PNAME'))
            elif action.group('ATYPE') == 'ACTION_CHECK':
                hand.addCheck( street, action.group('PNAME'))
            elif action.group('ATYPE') == 'ACTION_DISCARD':
                hand.addDiscard(street, action.group('PNAME'), action.group('NODISCARDED'), action.group('DISCARDED'))
            elif action.group('ATYPE') == 'ACTION_STAND':
                hand.addStandsPat( street, action.group('PNAME'))
            else:
                print (_("DEBUG:") + _("Unimplemented %s: '%s' '%s'") % ("readAction", action.group('PNAME'), action.group('ATYPE')))


    def readShowdownActions(self, hand):
        for shows in self.re_ShowdownAction.finditer(hand.handText):
            showdownCards = []
            for card in self.re_Card.finditer(shows.group('CARDS')):
                #print "DEBUG:", card, card.group('CARD'), self.convertWin2dayCards(card.group('CARD'))
                showdownCards.append(self.convertWin2dayCards(card.group('CARD')))
            
            hand.addShownCards(showdownCards, shows.group('PNAME'))

    def readCollectPot(self,hand):
        for m in self.re_CollectPot.finditer(hand.handText):
            potcoll = Decimal(m.group('POT'))
            if potcoll > 0:
                 hand.addCollectPot(player=m.group('PNAME'),pot=potcoll)

    def readShownCards(self,hand):
        for m in self.re_ShownCards.finditer(hand.handText):
            if m.group('CARDS') is not None:
                cards = m.group('CARDS')
                cards = cards.split(' ')
                hand.addShownCards(cards=cards, player=m.group('PNAME'))

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-i", "--input", dest="ipath", help=_("parse input hand history"), default="-")
    parser.add_option("-o", "--output", dest="opath", help=_("output translation to"), default="-")
    parser.add_option("-f", "--follow", dest="follow", help=_("follow (tail -f) the input"), action="store_true", default=False)
    parser.add_option("-q", "--quiet",
                  action="store_const", const=logging.CRITICAL, dest="verbosity", default=logging.INFO)
    parser.add_option("-v", "--verbose",
                  action="store_const", const=logging.INFO, dest="verbosity")
    parser.add_option("--vv",
                  action="store_const", const=logging.DEBUG, dest="verbosity")

    (options, args) = parser.parse_args()

    LOG_FILENAME = './logging.out'
    logging.basicConfig(filename=LOG_FILENAME,level=options.verbosity)

    e = Win2day(in_path = options.ipath, out_path = options.opath, follow = options.follow)
