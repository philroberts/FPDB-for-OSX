#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Copyright 2008, Carl Gherardi
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

import sys
from HandHistoryConverter import *

# PokerStars HH Format

#PokerStars Game #20461877044:  Hold'em No Limit ($1/$2) - 2008/09/16 18:58:01 ET
#Table 'Gianfar IV' 6-max Seat #1 is the button
#Seat 1: ZeKGB ($224 in chips)
#Seat 2: quimboavida ($107.75 in chips)
#Seat 3: tropical100 ($190 in chips)
#Seat 4: jackhama33 ($54.95 in chips)
#Seat 5: Olubanu ($196 in chips)
#Seat 6: LSgambler ($205.35 in chips)
#quimboavida: posts small blind $1
#tropical100: posts big blind $2
#*** HOLE CARDS ***
#jackhama33: folds
#Olubanu: folds
#LSgambler: folds
#ZeKGB: folds
#quimboavida: calls $1
#tropical100: raises $5 to $7
#quimboavida: calls $5
#*** FLOP *** [3d Qs Kd]
#quimboavida: bets $10
#tropical100: calls $10
#*** TURN *** [3d Qs Kd] [Ah]
#quimboavida: checks
#tropical100: checks
#*** RIVER *** [3d Qs Kd Ah] [7c]
#quimboavida: bets $30
#tropical100: folds
#quimboavida collected $32.35 from pot
#*** SUMMARY ***
#Total pot $34 | Rake $1.65
#Board [3d Qs Kd Ah 7c]
#Seat 1: ZeKGB (button) folded before Flop (didn't bet)
#Seat 2: quimboavida (small blind) collected ($32.35)
#Seat 3: tropical100 (big blind) folded on the River
#Seat 4: jackhama33 folded before Flop (didn't bet)
#Seat 5: Olubanu folded before Flop (didn't bet)
#Seat 6: LSgambler folded before Flop (didn't bet)


#PokerStars Game #25381215423:  HORSE (Razz Limit, $0.10/$0.20) - 2009/02/26 15:20:19 ET
#Table 'Natalie V' 8-max


class PokerStars(HandHistoryConverter):
    
    # Static regexes
    re_GameInfo     = re.compile('PokerStars Game #(?P<HID>[0-9]+):\s+(HORSE)? \(?(?P<GAME>Hold\'em|Razz|7 Card Stud|Omaha Hi/Lo) (?P<LIMIT>No Limit|Limit|Pot Limit),? \(?(?P<CURRENCY>\$|)?(?P<SB>[.0-9]+)/\$?(?P<BB>[.0-9]+)\) - (?P<DATETIME>.*$)', re.MULTILINE)
    re_SplitHands   = re.compile('\n\n+')
    re_HandInfo     = re.compile("^Table \'(?P<TABLE>[- a-zA-Z]+)\'(?P<TABLEATTRIBUTES>.+?$)?", re.MULTILINE)
    re_Button       = re.compile('Seat #(?P<BUTTON>\d+) is the button', re.MULTILINE)
    re_PlayerInfo   = re.compile('^Seat (?P<SEAT>[0-9]+): (?P<PNAME>.*) \(\$?(?P<CASH>[.0-9]+) in chips\)', re.MULTILINE)
    re_Board        = re.compile(r"\[(?P<CARDS>.+)\]")
#        self.re_setHandInfoRegex('.*#(?P<HID>[0-9]+): Table (?P<TABLE>[ a-zA-Z]+) - \$?(?P<SB>[.0-9]+)/\$?(?P<BB>[.0-9]+) - (?P<GAMETYPE>.*) - (?P<HR>[0-9]+):(?P<MIN>[0-9]+) ET - (?P<YEAR>[0-9]+)/(?P<MON>[0-9]+)/(?P<DAY>[0-9]+)Table (?P<TABLE>[ a-zA-Z]+)\nSeat (?P<BUTTON>[0-9]+)')    
    
    def __init__(self, in_path = '-', out_path = '-', follow = False, autostart=True):
        """\
in_path   (default '-' = sys.stdin)
out_path  (default '-' = sys.stdout)
follow :  whether to tail -f the input"""
        HandHistoryConverter.__init__(self, in_path, out_path, sitename="PokerStars", follow=follow)
        logging.info("Initialising PokerStars converter class")
        self.filetype = "text"
        self.codepage = "cp1252"
        if autostart:
            self.start()

        
    def compilePlayerRegexs(self,  hand):
        players = set([player[1] for player in hand.players])
        if not players <= self.compiledPlayers: # x <= y means 'x is subset of y'
            # we need to recompile the player regexs.
            self.compiledPlayers = players
            player_re = "(?P<PNAME>" + "|".join(map(re.escape, players)) + ")"
            logging.debug("player_re: " + player_re)
            self.re_PostSB           = re.compile(r"^%s: posts small blind \$?(?P<SB>[.0-9]+)" %  player_re, re.MULTILINE)
            self.re_PostBB           = re.compile(r"^%s: posts big blind \$?(?P<BB>[.0-9]+)" %  player_re, re.MULTILINE)
            self.re_Antes            = re.compile(r"^%s: posts the ante \$?(?P<ANTE>[.0-9]+)" % player_re, re.MULTILINE)
            self.re_BringIn          = re.compile(r"^%s: brings[- ]in( low|) for \$?(?P<BRINGIN>[.0-9]+)" % player_re, re.MULTILINE)
            self.re_PostBoth         = re.compile(r"^%s: posts small \& big blinds \[\$? (?P<SBBB>[.0-9]+)" %  player_re, re.MULTILINE)
            self.re_HeroCards        = re.compile(r"^Dealt to %s(?: \[(?P<OLDCARDS>.+?)\])?( \[(?P<NEWCARDS>.+?)\])" % player_re, re.MULTILINE)
            self.re_Action           = re.compile(r"^%s:(?P<ATYPE> bets| checks| raises| calls| folds)( \$(?P<BET>[.\d]+))?( to \$(?P<BETTO>[.\d]+))?" %  player_re, re.MULTILINE)
            self.re_ShowdownAction   = re.compile(r"^%s: shows \[(?P<CARDS>.*)\]" %  player_re, re.MULTILINE)
            self.re_CollectPot       = re.compile(r"Seat (?P<SEAT>[0-9]+): %s (\(button\) |\(small blind\) |\(big blind\) )?(collected|showed \[.*\] and won) \(\$(?P<POT>[.\d]+)\)(, mucked| with.*|)" %  player_re, re.MULTILINE)
            self.re_sitsOut          = re.compile("^%s sits out" %  player_re, re.MULTILINE)
            self.re_ShownCards       = re.compile("^Seat (?P<SEAT>[0-9]+): %s \(.*\) showed \[(?P<CARDS>.*)\].*" %  player_re, re.MULTILINE)


    def readSupportedGames(self):
        return []

    def determineGameType(self, handText):
        info = {'type':'ring'}
        
        m = self.re_GameInfo.search(handText)
        if not m: 
            return None

        mg = m.groupdict()
        
        # translations from captured groups to our info strings
        limits = { 'No Limit':'nl', 'Pot Limit':'pl', 'Limit':'fl' }
        games = {              # base, category
                  "Hold'em" : ('hold','holdem'), 
                 'Omaha Hi' : ('hold','omahahi'),
              'Omaha Hi/Lo' : ('hold','omahahilo'),
                     'Razz' : ('stud','razz'), 
              '7 Card Stud' : ('stud','studhi')
               }
        currencies = { u'€':'EUR', '$':'USD', '':'T$' }
        if 'LIMIT' in mg:
            info['limitType'] = limits[mg['LIMIT']]
        if 'GAME' in mg:
            (info['base'], info['category']) = games[mg['GAME']]
        if 'SB' in mg:
            info['sb'] = mg['SB']
        if 'BB' in mg:
            info['bb'] = mg['BB']
        if 'CURRENCY' in mg:
            info['currency'] = currencies[mg['CURRENCY']]
        # NB: SB, BB must be interpreted as blinds or bets depending on limit type.
        
        return info


    def readHandInfo(self, hand):
        info = {}
        m = self.re_HandInfo.search(hand.handText,re.DOTALL)
        if m: info.update(m.groupdict())
        m = self.re_GameInfo.search(hand.handText)
        if m: info.update(m.groupdict())
        m = self.re_Button.search(hand.handText)
        if m: info.update(m.groupdict()) 
        # TODO : I rather like the idea of just having this dict as hand.info
        logging.debug("readHandInfo: %s" % info)
        for key in info:
            if key == 'DATETIME':
                datetime = info[key].replace(" - "," ") # some are like "2009/02/26 - 15:22:55 ET"
                datetime = datetime.replace(" (ET)","") # kludge for now.
                datetime = datetime.replace(" ET","") # kludge for now.
                hand.starttime = time.strptime(datetime, "%Y/%m/%d %H:%M:%S")
            if key == 'HID':
                hand.handid = info[key]
            if key == 'TABLE':
                hand.tablename = info[key]
            if key == 'BUTTON':
                hand.buttonpos = info[key]
        
    def readButton(self, hand):
        m = self.re_Button.search(hand.handText)
        if m:
            hand.buttonpos = int(m.group('BUTTON'))
        else:
            logging.info('readButton: not found')

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
            m =  re.search(r"\*\*\* HOLE CARDS \*\*\*(?P<PREFLOP>.+(?=\*\*\* FLOP \*\*\*)|.+)"
                       r"(\*\*\* FLOP \*\*\*(?P<FLOP> \[\S\S \S\S \S\S\].+(?=\*\*\* TURN \*\*\*)|.+))?"
                       r"(\*\*\* TURN \*\*\* \[\S\S \S\S \S\S] (?P<TURN>\[\S\S\].+(?=\*\*\* RIVER \*\*\*)|.+))?"
                       r"(\*\*\* RIVER \*\*\* \[\S\S \S\S \S\S \S\S] (?P<RIVER>\[\S\S\].+))?", hand.handText,re.DOTALL)
        elif hand.gametype['base'] in ("stud"):
            m =  re.search(r"(?P<ANTES>.+(?=\*\*\* 3rd STREET \*\*\*)|.+)"
                           r"(\*\*\* 3rd STREET \*\*\*(?P<THIRD>.+(?=\*\*\* 4th STREET \*\*\*)|.+))?"
                           r"(\*\*\* 4th STREET \*\*\*(?P<FOURTH>.+(?=\*\*\* 5th STREET \*\*\*)|.+))?"
                           r"(\*\*\* 5th STREET \*\*\*(?P<FIFTH>.+(?=\*\*\* 6th STREET \*\*\*)|.+))?"
                           r"(\*\*\* 6th STREET \*\*\*(?P<SIXTH>.+(?=\*\*\* RIVER \*\*\*)|.+))?"
                           r"(\*\*\* RIVER \*\*\*(?P<SEVENTH>.+))?", hand.handText,re.DOTALL)
        hand.addStreets(m)

    def readCommunityCards(self, hand, street): # street has been matched by markStreets, so exists in this hand
        if street in ('FLOP','TURN','RIVER'):   # a list of streets which get dealt community cards (i.e. all but PREFLOP)
            #print "DEBUG readCommunityCards:", street, hand.streets.group(street)
            m = self.re_Board.search(hand.streets[street])
            hand.setCommunityCards(street, m.group('CARDS').split(' '))

    def readAntes(self, hand):
        logging.debug("reading antes")
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
            hand.addBlind(a.group('PNAME'), 'small & big blinds', a.group('SBBB'))

    def readHeroCards(self, hand):
        m = self.re_HeroCards.search(hand.handText)
        if(m == None):
            #Not involved in hand
            hand.involved = False
        else:
            hand.hero = m.group('PNAME')
            # "2c, qh" -> set(["2c","qc"])
            # Also works with Omaha hands.
            cards = m.group('NEWCARDS')
            cards = set(cards.split(' '))
            hand.addHoleCards(cards, m.group('PNAME'))

    def readStudPlayerCards(self, hand, street):
        # See comments of reference implementation in FullTiltToFpdb.py
        logging.debug("readStudPlayerCards")
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
            if action.group('ATYPE') == ' raises':
                hand.addRaiseBy( street, action.group('PNAME'), action.group('BET') )
            elif action.group('ATYPE') == ' calls':
                hand.addCall( street, action.group('PNAME'), action.group('BET') )
            elif action.group('ATYPE') == ' bets':
                hand.addBet( street, action.group('PNAME'), action.group('BET') )
            elif action.group('ATYPE') == ' folds':
                hand.addFold( street, action.group('PNAME'))
            elif action.group('ATYPE') == ' checks':
                hand.addCheck( street, action.group('PNAME'))
            else:
                print "DEBUG: unimplemented readAction: %s %s" %(action.group('PNAME'),action.group('ATYPE'),)


    def readShowdownActions(self, hand):
        for shows in self.re_ShowdownAction.finditer(hand.handText):            
            cards = shows.group('CARDS')
            cards = set(cards.split(' '))
            hand.addShownCards(cards, shows.group('PNAME'))

    def readCollectPot(self,hand):
        for m in self.re_CollectPot.finditer(hand.handText):
            hand.addCollectPot(player=m.group('PNAME'),pot=m.group('POT'))

    def readShownCards(self,hand):
        for m in self.re_ShownCards.finditer(hand.handText):
            if m.group('CARDS') is not None:
                cards = m.group('CARDS')
                cards = set(cards.split(' '))
                hand.addShownCards(cards=cards, player=m.group('PNAME'))

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-i", "--input", dest="ipath", help="parse input hand history", default="regression-test-files/pokerstars/HH20090226 Natalie V - $0.10-$0.20 - HORSE.txt")
    parser.add_option("-o", "--output", dest="opath", help="output translation to", default="-")
    parser.add_option("-f", "--follow", dest="follow", help="follow (tail -f) the input", action="store_true", default=False)
    parser.add_option("-q", "--quiet",
                  action="store_const", const=logging.CRITICAL, dest="verbosity", default=logging.INFO)
    parser.add_option("-v", "--verbose",
                  action="store_const", const=logging.INFO, dest="verbosity")
    parser.add_option("--vv",
                  action="store_const", const=logging.DEBUG, dest="verbosity")

    (options, args) = parser.parse_args()

    LOG_FILENAME = './logging.out'
    logging.basicConfig(filename=LOG_FILENAME,level=options.verbosity)

    e = PokerStars(in_path = options.ipath, out_path = options.opath, follow = options.follow)
