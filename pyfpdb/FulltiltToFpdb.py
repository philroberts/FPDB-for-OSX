#!/usr/bin/env python
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

# FullTilt HH Format converter

class FullTilt(HandHistoryConverter):
    
    # Static regexes
    re_GameInfo     = re.compile('- \$?(?P<SB>[.0-9]+)/\$?(?P<BB>[.0-9]+) (Ante \$(?P<ANTE>[.0-9]+) )?- (?P<LTYPE>(No|Pot)? )?Limit (?P<GAME>(Hold\'em|Omaha|Razz))')
    re_SplitHands   = re.compile(r"\n\n+")
    re_HandInfo     = re.compile('.*#(?P<HID>[0-9]+): Table (?P<TABLE>[- a-zA-Z]+) (\((?P<TABLEATTRIBUTES>.+)\) )?- \$?(?P<SB>[.0-9]+)/\$?(?P<BB>[.0-9]+) (Ante \$(?P<ANTE>[.0-9]+) )?- (?P<GAMETYPE>[a-zA-Z\' ]+) - (?P<DATETIME>.*)')
    re_Button       = re.compile('^The button is in seat #(?P<BUTTON>\d+)', re.MULTILINE)
    re_PlayerInfo   = re.compile('Seat (?P<SEAT>[0-9]+): (?P<PNAME>.*) \(\$(?P<CASH>[.0-9]+)\)\n')
    re_Board        = re.compile(r"\[(?P<CARDS>.+)\]")
    
    def __init__(self, in_path = '-', out_path = '-', follow = False, autostart=True):
        """\
in_path   (default '-' = sys.stdin)
out_path  (default '-' = sys.stdout)
follow :  whether to tail -f the input"""
        HandHistoryConverter.__init__(self, in_path, out_path, sitename="FullTilt", follow=follow)
        logging.info("Initialising FullTilt converter class")
        self.filetype = "text"
        self.codepage = "cp1252"
        if autostart:
            self.start()


    def compilePlayerRegexs(self,  players):
        if not players <= self.compiledPlayers: # x <= y means 'x is subset of y'
            # we need to recompile the player regexs.
            self.compiledPlayers = players
            player_re = "(?P<PNAME>" + "|".join(map(re.escape, players)) + ")"
            logging.debug("player_re: " + player_re)
            self.re_PostSB           = re.compile(r"^%s posts the small blind of \$?(?P<SB>[.0-9]+)" %  player_re, re.MULTILINE)
            self.re_PostBB           = re.compile(r"^%s posts (the big blind of )?\$?(?P<BB>[.0-9]+)" % player_re, re.MULTILINE)
            self.re_Antes            = re.compile(r"^%s antes \$?(?P<ANTE>[.0-9]+)" % player_re, re.MULTILINE)
            self.re_BringIn          = re.compile(r"^%s brings in for \$?(?P<BRINGIN>[.0-9]+)" % player_re, re.MULTILINE)
            self.re_PostBoth         = re.compile(r"^%s posts small \& big blinds \[\$? (?P<SBBB>[.0-9]+)" % player_re, re.MULTILINE)
            self.re_HeroCards        = re.compile(r"^Dealt to %s(?: \[(?P<OLDCARDS>.+?)\])?( \[(?P<NEWCARDS>.+?)\])" % player_re, re.MULTILINE)
            self.re_Action           = re.compile(r"^%s(?P<ATYPE> bets| checks| raises to| calls| folds)(\s\$(?P<BET>[.\d]+))?" % player_re, re.MULTILINE)
            self.re_ShowdownAction   = re.compile(r"^%s shows \[(?P<CARDS>.*)\]" % player_re, re.MULTILINE)
            self.re_CollectPot       = re.compile(r"^Seat (?P<SEAT>[0-9]+): %s (\(button\) |\(small blind\) |\(big blind\) )?(collected|showed \[.*\] and won) \(\$(?P<POT>[.\d]+)\)(, mucked| with.*)" % player_re, re.MULTILINE)
            self.re_SitsOut          = re.compile(r"^%s sits out" % player_re, re.MULTILINE)
            self.re_ShownCards       = re.compile(r"^Seat (?P<SEAT>[0-9]+): %s \(.*\) showed \[(?P<CARDS>.*)\].*" % player_re, re.MULTILINE)


    def readSupportedGames(self):
        return [["ring", "hold", "nl"], 
                ["ring", "hold", "pl"],
                ["ring", "razz", "fl"],
                ["ring", "omaha", "pl"]
               ]

    def determineGameType(self, handText):
        # Cheating with this regex, only support nlhe at the moment
        # Full Tilt Poker Game #10777181585: Table Deerfly (deep 6) - $0.01/$0.02 - Pot Limit Omaha Hi - 2:24:44 ET - 2009/02/22
        # Full Tilt Poker Game #10773265574: Table Butte (6 max) - $0.01/$0.02 - Pot Limit Hold'em - 21:33:46 ET - 2009/02/21
        # Full Tilt Poker Game #9403951181: Table CR - tay - $0.05/$0.10 - No Limit Hold'em - 9:40:20 ET - 2008/12/09
        # Full Tilt Poker Game #10809877615: Table Danville - $0.50/$1 Ante $0.10 - Limit Razz - 21:47:27 ET - 2009/02/23
        structure = "" # nl, pl, cn, cp, fl
        game      = ""


        m = self.re_GameInfo.search(handText)
        if m.group('LTYPE') == "No ":
            structure = "nl"
        elif m.group('LTYPE') == "Pot ":
            structure = "pl"
        elif m.group('LTYPE') == None:
            structure = "fl"

        if m.group('GAME') == "Hold\'em":
            game = "hold"
        elif m.group('GAME') == "Omaha":
            game = "omahahi"
        elif m.group('GAME') == "Razz":
            game = "razz"

        logging.debug("HandInfo: %s", m.groupdict())

        gametype = ["ring", game, structure, m.group('SB'), m.group('BB')]
        
        return gametype

    def readHandInfo(self, hand):
        m =  self.re_HandInfo.search(hand.handText,re.DOTALL)
        #print m.groups()
        hand.handid = m.group('HID')
        hand.tablename = m.group('TABLE')
        hand.starttime = time.strptime(m.group('DATETIME'), "%H:%M:%S ET - %Y/%m/%d")
# These work, but the info is already in the Hand class - should be used for tourneys though.
#       m.group('SB')
#       m.group('BB')
#       m.group('GAMETYPE')

# Stars format (Nov 10 2008): 2008/11/07 12:38:49 CET [2008/11/07 7:38:49 ET]
# or                        : 2008/11/07 12:38:49 ET
# Not getting it in my HH files yet, so using
# 2008/11/10 3:58:52 ET
#TODO: Do conversion from GMT to ET
#TODO: Need some date functions to convert to different timezones (Date::Manip for perl rocked for this)
        #hand.starttime = "%d/%02d/%02d %d:%02d:%02d ET" %(int(m.group('YEAR')), int(m.group('MON')), int(m.group('DAY')),
                            ##int(m.group('HR')), int(m.group('MIN')), int(m.group('SEC')))
#FIXME:        hand.buttonpos = int(m.group('BUTTON'))

    def readPlayerStacks(self, hand):
        m = self.re_PlayerInfo.finditer(hand.handText)
        players = []
        for a in m:
            hand.addPlayer(int(a.group('SEAT')), a.group('PNAME'), a.group('CASH'))

    def markStreets(self, hand):
        # PREFLOP = ** Dealing down cards **
        
        if hand.gametype[1] in ("hold", "omaha"):
            m =  re.search(r"\*\*\* HOLE CARDS \*\*\*(?P<PREFLOP>.+(?=\*\*\* FLOP \*\*\*)|.+)"
                       r"(\*\*\* FLOP \*\*\*(?P<FLOP> \[\S\S \S\S \S\S\].+(?=\*\*\* TURN \*\*\*)|.+))?"
                       r"(\*\*\* TURN \*\*\* \[\S\S \S\S \S\S] (?P<TURN>\[\S\S\].+(?=\*\*\* RIVER \*\*\*)|.+))?"
                       r"(\*\*\* RIVER \*\*\* \[\S\S \S\S \S\S \S\S] (?P<RIVER>\[\S\S\].+))?", hand.handText,re.DOTALL)
        elif hand.gametype[1] == "razz":
            m =  re.search(r"(?P<ANTES>.+(?=\*\*\* 3RD STREET \*\*\*)|.+)"
                           r"(\*\*\* 3RD STREET \*\*\*(?P<THIRD>.+(?=\*\*\* 4TH STREET \*\*\*)|.+))?"
                           r"(\*\*\* 4TH STREET \*\*\*(?P<FOURTH>.+(?=\*\*\* 5TH STREET \*\*\*)|.+))?"
                           r"(\*\*\* 5TH STREET \*\*\*(?P<FIFTH>.+(?=\*\*\* 6TH STREET \*\*\*)|.+))?"
                           r"(\*\*\* 6TH STREET \*\*\*(?P<SIXTH>.+(?=\*\*\* 7TH STREET \*\*\*)|.+))?"
                           r"(\*\*\* 7TH STREET \*\*\*(?P<SEVENTH>.+))?", hand.handText,re.DOTALL)
        hand.addStreets(m)

    def readCommunityCards(self, hand, street): # street has been matched by markStreets, so exists in this hand
        if street in ('FLOP','TURN','RIVER'):   # a list of streets which get dealt community cards (i.e. all but PREFLOP)
            #print "DEBUG readCommunityCards:", street, hand.streets.group(street)
            m = self.re_Board.search(hand.streets.group(street))
            hand.setCommunityCards(street, m.group('CARDS').split(' '))


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

    def readAntes(self, hand):
        logging.debug("reading antes")
        m = self.re_Antes.finditer(hand.handText)
        for player in m:
            logging.debug("hand.addAnte(%s,%s)" %(player.group('PNAME'), player.group('ANTE')))
            hand.addAnte(player.group('PNAME'), player.group('ANTE'))

    def readBringIn(self, hand):
        m = self.re_BringIn.search(hand.handText,re.DOTALL)
        print "DEBUG: Player bringing in: %s for %s" %(m.group('PNAME'),  m.group('BRINGIN'))
        hand.addBringIn(m.group('PNAME'),  m.group('BRINGIN'))

    def readButton(self, hand):
        hand.buttonpos = int(self.re_Button.search(hand.handText).group('BUTTON'))

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
            cards = [c.strip() for c in cards.split(' ')]
            hand.addHoleCards(cards, m.group('PNAME'))

    def readStudPlayerCards(self, hand, street):
        # This could be the most tricky one to get right.
        # It looks for cards dealt in 'street',
        # which may or may not be in the section of the hand designated 'street' by markStreets earlier.
        # Here's an example at FTP of what 'THIRD' and 'FOURTH' look like to hero PokerAscetic
        #
        #"*** 3RD STREET ***
        #Dealt to BFK23 [Th]
        #Dealt to cutiepr1nnymaid [8c]
        #Dealt to PokerAscetic [7c 8s] [3h]
        #..."
        #
        #"*** 4TH STREET ***
        #Dealt to cutiepr1nnymaid [8c] [2s]
        #Dealt to PokerAscetic [7c 8s 3h] [5s]
        #..."
        #Note that hero's first two holecards are only reported at 3rd street as 'old' cards.
        logging.debug("readStudPlayerCards")
        m = self.re_HeroCards.finditer(hand.streets[street])
        for player in m:
            logging.debug(player.groupdict())
            (pname,  oldcards,  newcards) = (player.group('PNAME'), player.group('OLDCARDS'), player.group('NEWCARDS'))
            if oldcards:
                oldcards = [c.strip() for c in oldcards.split(' ')]
            if newcards:
                newcards = [c.strip() for c in newcards.split(' ')]
            # options here:
            # (1) we trust the hand will know what to do -- probably check that the old cards match what it already knows, and add the newcards to this street.
            # (2) we're the experts at this particular history format and we know how we're going to be called (once for each street in Hand.streetList)
            #     so call addPlayerCards with the appropriate information.
            # I favour (2) here but I'm afraid it is rather stud7-specific.
            # in the following, the final list of cards will be in 'newcards' whilst if the first list exists (most of the time it does) it will be in 'oldcards'
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
            if action.group('ATYPE') == ' raises to':
                hand.addRaiseTo( street, action.group('PNAME'), action.group('BET') )
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
            cards = cards.split(' ')
            hand.addShownCards(cards, shows.group('PNAME'))

    def readCollectPot(self,hand):
        for m in self.re_CollectPot.finditer(hand.handText):
            hand.addCollectPot(player=m.group('PNAME'),pot=m.group('POT'))

    def readShownCards(self,hand):
        for m in self.re_ShownCards.finditer(hand.handText):
            if m.group('CARDS') is not None:
                cards = m.group('CARDS')
                cards = cards.split(' ')
                hand.addShownCards(cards=cards, player=m.group('PNAME'))
    

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-i", "--input", dest="ipath", help="parse input hand history", default="regression-test-files/fulltilt/razz/FT20090223 Danville - $0.50-$1 Ante $0.10 - Limit Razz.txt")
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

    e = FullTilt(in_path = options.ipath, out_path = options.opath, follow = options.follow)
