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
import logging
from HandHistoryConverter import *

# Fulltilt HH Format converter
# TODO: cat tourno and table to make table name for tournaments

class Fulltilt(HandHistoryConverter):
    
    # Static regexes
    re_GameInfo     = re.compile('''(?:(?P<TOURNAMENT>.+)\s\((?P<TOURNO>\d+)\),\s)?
                                    .+
                                    -\s(?P<CURRENCY>\$|)?
                                    (?P<SB>[.0-9]+)/
                                    \$?(?P<BB>[.0-9]+)\s
                                    (Ante\s\$?(?P<ANTE>[.0-9]+)\s)?-\s
                                    (?P<LIMIT>(No\sLimit|Pot\sLimit|Limit))?\s
                                    (?P<GAME>(Hold\'em|Omaha\sHi|Omaha\sH/L|7\sCard\sStud|Stud\sH/L|Razz|Stud\sHi))
                                 ''', re.VERBOSE)
    re_SplitHands   = re.compile(r"\n\n+")
    re_TailSplitHands   = re.compile(r"(\n\n+)")
    re_HandInfo     = re.compile('''.*\#(?P<HID>[0-9]+):\s
                                    (?:(?P<TOURNAMENT>.+)\s\((?P<TOURNO>\d+)\),\s)?
                                    Table\s
                                    (?P<PLAY>Play\sChip\s|PC)?
                                    (?P<TABLE>[-\s\da-zA-Z]+)\s
                                    (\((?P<TABLEATTRIBUTES>.+)\)\s)?-\s
                                    \$?(?P<SB>[.0-9]+)/\$?(?P<BB>[.0-9]+)\s(Ante\s\$?(?P<ANTE>[.0-9]+)\s)?-\s
                                    (?P<GAMETYPE>[a-zA-Z\/\'\s]+)\s-\s
                                    (?P<DATETIME>.*)
                                 ''', re.VERBOSE)
    re_Button       = re.compile('^The button is in seat #(?P<BUTTON>\d+)', re.MULTILINE)
    re_PlayerInfo   = re.compile('Seat (?P<SEAT>[0-9]+): (?P<PNAME>.*) \(\$?(?P<CASH>[,.0-9]+)\)$', re.MULTILINE)
    re_Board        = re.compile(r"\[(?P<CARDS>.+)\]")

# These regexes are for FTP only
    re_Mixed        = re.compile(r'\s\-\s(?P<MIXED>HA|HORSE|HOSE)\s\-\s', re.VERBOSE)
    re_Max          = re.compile("(?P<MAX>\d+)( max)?", re.MULTILINE)
    # NB: if we ever match "Full Tilt Poker" we should also match "FullTiltPoker", which PT Stud erroneously exports.

    mixes = { 'HORSE': 'horse', '7-Game': '7game', 'HOSE': 'hose', 'HA': 'ha'}

    def __init__(self, in_path = '-', out_path = '-', follow = False, autostart=True, index=0):
        """\
in_path   (default '-' = sys.stdin)
out_path  (default '-' = sys.stdout)
follow :  whether to tail -f the input"""
        HandHistoryConverter.__init__(self, in_path, out_path, sitename="Fulltilt", follow=follow, index=index)
        logging.info("Initialising Fulltilt converter class")
        self.filetype = "text"
        self.codepage = "cp1252"
        self.siteId   = 1 # Needs to match id entry in Sites database
        if autostart:
            self.start()


    def compilePlayerRegexs(self,  hand):
        players = set([player[1] for player in hand.players])
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
            self.re_Action           = re.compile(r"^%s(?P<ATYPE> bets| checks| raises to| completes it to| calls| folds)( \$?(?P<BET>[.,\d]+))?" % player_re, re.MULTILINE)
            self.re_ShowdownAction   = re.compile(r"^%s shows \[(?P<CARDS>.*)\]" % player_re, re.MULTILINE)
            self.re_CollectPot       = re.compile(r"^Seat (?P<SEAT>[0-9]+): %s (\(button\) |\(small blind\) |\(big blind\) )?(collected|showed \[.*\] and won) \(\$(?P<POT>[.\d]+)\)(, mucked| with.*)" % player_re, re.MULTILINE)
            self.re_SitsOut          = re.compile(r"^%s sits out" % player_re, re.MULTILINE)
            self.re_ShownCards       = re.compile(r"^Seat (?P<SEAT>[0-9]+): %s \(.*\) showed \[(?P<CARDS>.*)\].*" % player_re, re.MULTILINE)

    def readSupportedGames(self):
        return [["ring", "hold", "nl"], 
                ["ring", "hold", "pl"],
                ["ring", "hold", "fl"],

                ["ring", "stud", "fl"],

                ["tour", "hold", "nl"],
                ["tour", "hold", "pl"],
                ["tour", "hold", "fl"],

                ["tour", "stud", "fl"],
               ]

    def determineGameType(self, handText):
        # Full Tilt Poker Game #10777181585: Table Deerfly (deep 6) - $0.01/$0.02 - Pot Limit Omaha Hi - 2:24:44 ET - 2009/02/22
        # Full Tilt Poker Game #10773265574: Table Butte (6 max) - $0.01/$0.02 - Pot Limit Hold'em - 21:33:46 ET - 2009/02/21
        # Full Tilt Poker Game #9403951181: Table CR - tay - $0.05/$0.10 - No Limit Hold'em - 9:40:20 ET - 2008/12/09
        # Full Tilt Poker Game #10809877615: Table Danville - $0.50/$1 Ante $0.10 - Limit Razz - 21:47:27 ET - 2009/02/23
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
                'Omaha H/L' : ('hold','omahahilo'),
                     'Razz' : ('stud','razz'), 
                  'Stud Hi' : ('stud','studhi'), 
                 'Stud H/L' : ('stud','studhilo')
               }
        currencies = { u' €':'EUR', '$':'USD', '':'T$' }
        info['limitType'] = limits[mg['LIMIT']]
        info['sb'] = mg['SB']
        info['bb'] = mg['BB']
        if mg['GAME'] != None:
            (info['base'], info['category']) = games[mg['GAME']]
        if mg['CURRENCY'] != None:
            info['currency'] = currencies[mg['CURRENCY']]
        if mg['TOURNO'] == None:  info['type'] = "ring"
        else:                     info['type'] = "tour"
        # NB: SB, BB must be interpreted as blinds or bets depending on limit type.
        if info['type'] == "tour": return None # importer is screwed on tournies, pass on those hands so we don't interrupt other autoimporting
        return info

    #Following function is a hack, we should be dealing with this in readFile (i think correct codepage....)
    # Same function as parent class, removing the 2 end characters. - CG
    def allHandsAsList(self):
        """Return a list of handtexts in the file at self.in_path"""
        #TODO : any need for this to be generator? e.g. stars support can email one huge file of all hands in a year. Better to read bit by bit than all at once.
        self.readFile()

        # FIXME: it's a hack
        if self.obs[:2] == u'\xff\xfe':
            self.obs = self.obs[2:].replace('\x00', '')

        self.obs = self.obs.strip()
        self.obs = self.obs.replace('\r\n', '\n')
        if self.obs == "" or self.obs == None:
            logging.info("Read no hands.")
            return
        return re.split(self.re_SplitHands,  self.obs)

    def readHandInfo(self, hand):
        m =  self.re_HandInfo.search(hand.handText,re.DOTALL)
        if(m == None):
            logging.info("Didn't match re_HandInfo")
            logging.info(hand.handText)
            return None
        hand.handid = m.group('HID')
        hand.tablename = m.group('TABLE')
        hand.starttime = datetime.datetime.strptime(m.group('DATETIME'), "%H:%M:%S ET - %Y/%m/%d")
        if m.group('TABLEATTRIBUTES'):
            m2 = self.re_Max.search(m.group('TABLEATTRIBUTES'))
            if m2: hand.maxseats = int(m2.group('MAX'))

        hand.tourNo = m.group('TOURNO')
        if m.group('PLAY') != None:
            hand.gametype['currency'] = 'play'
            
        # TODO: if there's a way to figure these out, we should.. otherwise we have to stuff it with unknowns
        if hand.buyin == None:
            hand.buyin = "$0.00+$0.00"
        if hand.level == None:
            hand.level = "0"            

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

        if hand.gametype['base'] == 'hold':
            m =  re.search(r"\*\*\* HOLE CARDS \*\*\*(?P<PREFLOP>.+(?=\*\*\* FLOP \*\*\*)|.+)"
                       r"(\*\*\* FLOP \*\*\*(?P<FLOP> \[\S\S \S\S \S\S\].+(?=\*\*\* TURN \*\*\*)|.+))?"
                       r"(\*\*\* TURN \*\*\* \[\S\S \S\S \S\S] (?P<TURN>\[\S\S\].+(?=\*\*\* RIVER \*\*\*)|.+))?"
                       r"(\*\*\* RIVER \*\*\* \[\S\S \S\S \S\S \S\S] (?P<RIVER>\[\S\S\].+))?", hand.handText,re.DOTALL)
        elif hand.gametype['base'] == "stud": # or should this be gametype['category'] == 'razz'
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
            m = self.re_Board.search(hand.streets[street])
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
#            if player.group() != 
            hand.addAnte(player.group('PNAME'), player.group('ANTE'))

    def readBringIn(self, hand):
        m = self.re_BringIn.search(hand.handText,re.DOTALL)
        if m:
            logging.debug("Player bringing in: %s for %s" %(m.group('PNAME'),  m.group('BRINGIN')))
            hand.addBringIn(m.group('PNAME'),  m.group('BRINGIN'))
        else:
            logging.warning("No bringin found, handid =%s" % hand.handid)

    def readButton(self, hand):
        hand.buttonpos = int(self.re_Button.search(hand.handText).group('BUTTON'))

    def readHeroCards(self, hand):
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
                    newcards = found.group('NEWCARDS').split(' ')
                    hand.addHoleCards(street, hand.hero, closed=newcards, shown=False, mucked=False, dealt=True)

        for street, text in hand.streets.iteritems():
            if not text or street in ('PREFLOP', 'DEAL'): continue  # already done these
            m = self.re_HeroCards.finditer(hand.streets[street])
            for found in m:
                player = found.group('PNAME')
                if found.group('NEWCARDS') == None:
                    newcards = []
                else:
                    newcards = found.group('NEWCARDS').split(' ')
                if found.group('OLDCARDS') == None:
                    oldcards = []
                else:
                    oldcards = found.group('OLDCARDS').split(' ')

                if street == 'THIRD' and len(oldcards) == 2: # hero in stud game
                    hand.hero = player
                    hand.dealt.add(player) # need this for stud??
                    hand.addHoleCards(street, player, closed=oldcards, open=newcards, shown=False, mucked=False, dealt=False)
                else:
                    hand.addHoleCards(street, player, open=newcards, closed=oldcards, shown=False, mucked=False, dealt=False)


    def readAction(self, hand, street):
        m = self.re_Action.finditer(hand.streets[street])
        for action in m:
            if action.group('ATYPE') == ' raises to':
                hand.addRaiseTo( street, action.group('PNAME'), action.group('BET') )
            elif action.group('ATYPE') == ' completes it to':
                hand.addComplete( street, action.group('PNAME'), action.group('BET') )
            elif action.group('ATYPE') == ' calls':
                hand.addCall( street, action.group('PNAME'), action.group('BET') )
            elif action.group('ATYPE') == ' bets':
                hand.addBet( street, action.group('PNAME'), action.group('BET') )
            elif action.group('ATYPE') == ' folds':
                hand.addFold( street, action.group('PNAME'))
            elif action.group('ATYPE') == ' checks':
                hand.addCheck( street, action.group('PNAME'))
            else:
                print "DEBUG: unimplemented readAction: '%s' '%s'" %(action.group('PNAME'),action.group('ATYPE'),)


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

    def guessMaxSeats(self, hand):
        """Return a guess at max_seats when not specified in HH."""
        mo = self.maxOccSeat(hand)

        if mo == 10: return 10 #that was easy

        if hand.gametype['base'] == 'stud':
            if mo <= 8: return 8
            else: return mo 

        if hand.gametype['base'] == 'draw':
            if mo <= 6: return 6
            else: return mo

        if mo == 2: return 2
        if mo <= 6: return 6
        return 9

    def readOther(self, hand):
        m = self.re_Mixed.search(self.in_path)
        if m == None: hand.mixed = None
        else:
            hand.mixed = self.mixes[m.groupdict()['MIXED']]

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

    e = Fulltilt(in_path = options.ipath, out_path = options.opath, follow = options.follow)
