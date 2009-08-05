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
from collections import defaultdict

from HandHistoryConverter import *

# PartyPoker HH Format

class PartyPoker(HandHistoryConverter):

############################################################
#    Class Variables

    #mixes = { 'HORSE': 'horse', '8-Game': '8game', 'HOSE': 'hose'} # Legal mixed games
    sym = {'USD': "\$", }
    #sym = {'USD': "\$", 'CAD': "\$", 'T$': "", "EUR": "\x80", "GBP": "\xa3"}         # ADD Euro, Sterling, etc HERE
    substitutions = {
                     'LEGAL_ISO' : "USD|EUR|GBP|CAD",    # legal ISO currency codes
                            'LS' : "\$|\x80|\xa3"        # legal currency symbols  ADD Euro, Sterling, etc HERE
                    }

    # Static regexes
    # $5 USD NL Texas Hold'em - Saturday, July 25, 07:53:52 EDT 2009
    # NL Texas Hold'em $1 USD Buy-in Trny:45685440 Level:8  Blinds-Antes(600/1 200 -50) - Sunday, May 17, 11:25:07 MSKS 2009
    re_GameInfoRing     = re.compile("""
            (?:\$|)\s*(?P<RINGLIMIT>\d+)\s*(?P<CURRENCY>USD)?\s*
            (?P<LIMIT>(NL))\s+
            (?P<GAME>(Texas\ Hold\'em))
            \s*\-\s*
            (?P<DATETIME>.+)
            """, re.VERBOSE)
    re_GameInfoTrny     = re.compile("""
            (?P<LIMIT>(NL))\s+
            (?P<GAME>(Texas\ Hold\'em))\s+
            (?:\$|)\s*
            (?P<BUYIN>[.0-9]+)\s*(?P<CURRENCY>USD)?\s*Buy-in\s+
            Trny:\s?(?P<TOURNO>\d+)\s+
            Level:\s*(?P<LEVEL>\d+)\s+
            Blinds(?:-Antes)?\(
                (?P<SB>[.0-9 ]+)\s*
                /(?P<BB>[.0-9 ]+)
                (?:\s*-\s*(?P<ANTE>[.0-9 ]+)\$?)?
            \)
            \s*\-\s*
            (?P<DATETIME>.+)
            """, re.VERBOSE)
    re_Hid          = re.compile("^Game \#(?P<HID>\d+) starts.")
    #re_GameInfo     = re.compile("""
          #PartyPoker\sGame\s\#(?P<HID>[0-9]+):\s+
          #(Tournament\s\#                # open paren of tournament info
          #(?P<TOURNO>\d+),\s
          #(?P<BUYIN>[%(LS)s\+\d\.]+      # here's how I plan to use LS
          #\s?(?P<TOUR_ISO>%(LEGAL_ISO)s)?
          #)\s)?                          # close paren of tournament info
          #(?P<MIXED>HORSE|8\-Game|HOSE)?\s?\(?
          #(?P<GAME>Hold\'em|Razz|7\sCard\sStud|7\sCard\sStud\sHi/Lo|Omaha|Omaha\sHi/Lo|Badugi|Triple\sDraw\s2\-7\sLowball)\s
          #(?P<LIMIT>No\sLimit|Limit|Pot\sLimit)\)?,?\s
          #(-\sLevel\s(?P<LEVEL>[IVXLC]+)\s)?
          #\(?                            # open paren of the stakes
          #(?P<CURRENCY>%(LS)s|)?
          #(?P<SB>[.0-9]+)/(%(LS)s)?
          #(?P<BB>[.0-9]+)
          #\s?(?P<ISO>%(LEGAL_ISO)s)?
          #\)\s-\s                        # close paren of the stakes
          #(?P<DATETIME>.*$)""" % substitutions,
          #re.MULTILINE|re.VERBOSE)

    re_PlayerInfo   = re.compile("""
          Seat\s(?P<SEAT>\d+):\s
          (?P<PNAME>.*)\s
          \(\s*\$?(?P<CASH>[0-9,.]+)\s*(?:USD)\s*\)
          """ , 
          re.VERBOSE)
    #re_PlayerInfo   = re.compile("""
          #^Seat\s(?P<SEAT>[0-9]+):\s
          #(?P<PNAME>.*)\s
          #\((%(LS)s)?(?P<CASH>[.0-9]+)\sin\schips\)""" % substitutions, 
          #re.MULTILINE|re.VERBOSE)

    re_HandInfo     = re.compile("""
            ^Table\s+
            (?P<TTYPE>[a-zA-Z0-9 ]+)\s+
            (?: \#|\(|)(?P<TABLE>\d+)\)?\s+
            (?:[^ ]+\s+\#(?P<MTTTABLE>\d+).+)? # table number for mtt
            \((?P<PLAY>Real|Play)\s+Money\)\s+ # FIXME: check if play money is correct
            Seat\s+(?P<BUTTON>\d+)\sis\sthe\sbutton
            """, 
          re.MULTILINE|re.VERBOSE)
    #re_HandInfo     = re.compile("""
          #^Table\s\'(?P<TABLE>[-\ a-zA-Z\d]+)\'\s
          #((?P<MAX>\d+)-max\s)?
          #(?P<PLAY>\(Play\sMoney\)\s)?
          #(Seat\s\#(?P<BUTTON>\d+)\sis\sthe\sbutton)?""", 
          #re.MULTILINE|re.VERBOSE)

    re_SplitHands   = re.compile('\x00+')
    re_TailSplitHands   = re.compile('(\x00+)')
    lineSplitter    = '\n'
    re_Button       = re.compile('Seat (?P<BUTTON>\d+) is the button', re.MULTILINE)
    re_Board        = re.compile(r"\[(?P<CARDS>.+)\]")
    re_NoSmallBlind = re.compile('^There is no Small Blind in this hand as the Big Blind of the previous hand left the table')
#        self.re_setHandInfoRegex('.*#(?P<HID>[0-9]+): Table (?P<TABLE>[ a-zA-Z]+) - \$?(?P<SB>[.0-9]+)/\$?(?P<BB>[.0-9]+) - (?P<GAMETYPE>.*) - (?P<HR>[0-9]+):(?P<MIN>[0-9]+) ET - (?P<YEAR>[0-9]+)/(?P<MON>[0-9]+)/(?P<DAY>[0-9]+)Table (?P<TABLE>[ a-zA-Z]+)\nSeat (?P<BUTTON>[0-9]+)')    


    def __init__(self, in_path = '-', out_path = '-', follow = False, autostart=True, index=0):
        """\
in_path   (default '-' = sys.stdin)
out_path  (default '-' = sys.stdout)
follow :  whether to tail -f the input"""
        HandHistoryConverter.__init__(self, in_path, out_path, sitename="PartyPoker", follow=follow, index=index)
        logging.info("Initialising PartyPoker converter class")
        self.filetype = "text"
        self.codepage = "cp1252" # FIXME: wtf?
        self.siteId   = 2 # Needs to match id entry in Sites database
        self._gameType = None # cached reg-parse result
        if autostart: 
            self.start()

    def allHandsAsList(self):
        list = HandHistoryConverter.allHandsAsList(self)
        return filter(lambda text: len(text.strip()), list)

    def compilePlayerRegexs(self,  hand):
        players = set([player[1] for player in hand.players])
        if not players <= self.compiledPlayers: # x <= y means 'x is subset of y'
            # we need to recompile the player regexs.
# TODO: should probably rename re_HeroCards and corresponding method,
#    since they are used to find all cards on lines starting with "Dealt to:"
#    They still identify the hero.
            self.compiledPlayers = players
            player_re = "(?P<PNAME>" + "|".join(map(re.escape, players)) + ")"
            subst = {'PLYR': player_re, 'CUR': hand.gametype['currency']}
            logging.debug("player_re: " + subst['PLYR'])
            logging.debug("CUR: " + subst['CUR'])
            self.re_PostSB = re.compile(
                r"^%(PLYR)s posts small blind \[[^.0-9]?(?P<SB>[.0-9]+) ?%(CUR)s\]\." %  subst, 
                re.MULTILINE)
            self.re_PostBB = re.compile(
                r"^%(PLYR)s posts big blind \[[^.0-9]?(?P<BB>[.0-9]+) ?%(CUR)s\]\." %  subst, 
                re.MULTILINE)
            self.re_Antes = re.compile(
                r"^%(PLYR)s posts ante \[[^.,0-9]?(?P<ANTE>[.0-9]+) ?%(CUR)s\]\." %  subst,
                re.MULTILINE)
            #self.re_BringIn = re.compile(
                #r"^%(PLYR)s: brings[- ]in( low|) for %(CUR)s(?P<BRINGIN>[.0-9]+)" % subst,
                #re.MULTILINE)
            #self.re_PostBoth = re.compile(
                #r"^%(PLYR)s: posts small \& big blinds \[%(CUR)s (?P<SBBB>[.0-9]+)" %  subst,
                #re.MULTILINE)
            self.re_HeroCards = re.compile(
                r"^Dealt to %(PLYR)s \[\s*(?P<NEWCARDS>.+)\s*\]" % subst,
                re.MULTILINE)
            self.re_Action = re.compile(r"""
                ^%(PLYR)s\s+(?P<ATYPE>bets|checks|raises|calls|folds|is\sall-In)
                (?:\s+\[[^.,0-9]?(?P<BET>[.,\d]+)\s+%(CUR)s\])?
                """ %  subst, 
                re.MULTILINE|re.VERBOSE)
            self.re_ShownCards = re.compile(
                r"^%s (?P<SHOWED>(?:doesn\'t )?shows?) "  %  player_re + 
                r"\[ *(?P<CARDS>.+) *\](?P<COMBINATION>.+)\.", 
                re.MULTILINE)
            self.re_CollectPot = re.compile(
                r""""^%(PLYR)s \s+ wins \s+
                [^.,0-9]?(?P<POT>[.\d]+)\s*%(CUR)s""" %  subst, 
                re.MULTILINE|re.VERBOSE)
            #self.re_sitsOut    = re.compile("^%s sits out" %  player_re, re.MULTILINE)
            #self.re_ShownCards = re.compile(
                #"^Seat (?P<SEAT>[0-9]+): %s (\(.*\) )?
                #(?P<SHOWED>showed|mucked) \[(?P<CARDS>.*)\].*" %  player_re, 
                #re.MULTILINE)

    def readSupportedGames(self):
        return [["ring", "hold", "nl"],
                #["ring", "hold", "pl"],
                #["ring", "hold", "fl"],

                #["ring", "stud", "fl"],

                #["ring", "draw", "fl"],

                ["tour", "hold", "nl"],
                #["tour", "hold", "pl"],
                #["tour", "hold", "fl"],

                #["tour", "stud", "fl"],
               ]

    def _getGameType(self, handText):
        if self._gameType is None:
            # let's determine whether hand is trny
            # and whether 5-th line contains head line
            headLine = handText.split(self.lineSplitter)[4]
            #print headLine
            #sys.exit(1)
            for headLineContainer in headLine, handText:
                for regexp in self.re_GameInfoTrny, self.re_GameInfoRing:
                    m = regexp.search(headLineContainer)
                    if m is not None:
                        self._gameType = m
                        return self._gameType
        return self._gameType
    
    def determineGameType(self, handText):
#    inspect the handText and return the gametype dict
#    gametype dict is:
#    {'limitType': xxx, 'base': xxx, 'category': xxx}
        
        info = {}
        
        m = self._getGameType(handText)
        if m is None:
            return None
        

        mg = m.groupdict()
        # translations from captured groups to fpdb info strings
        limits = { 'NL':'nl', 
#            'Pot Limit':'pl', 'Limit':'fl' 
            }
        games = {                          # base, category
                         "Texas Hold'em" : ('hold','holdem'), 
                                #'Omaha' : ('hold','omahahi'),
                          #'Omaha Hi/Lo' : ('hold','omahahilo'),
                                 #'Razz' : ('stud','razz'), 
                          #'7 Card Stud' : ('stud','studhi'),
                    #'7 Card Stud Hi/Lo' : ('stud','studhilo'),
                               #'Badugi' : ('draw','badugi'),
              #'Triple Draw 2-7 Lowball' : ('draw','27_3draw'),
               }
        #currencies = { '$':'USD', '':'T$' }
#    I don't think this is doing what we think. mg will always have all 
#    the expected keys, but the ones that didn't match in the regex will
#    have a value of None. It is OK if it throws an exception when it 
#    runs across an unknown game or limit or whatever.
        if 'LIMIT' in mg:
            info['limitType'] = limits[mg['LIMIT']]
        if 'GAME' in mg:
            (info['base'], info['category']) = games[mg['GAME']]

        if 'CURRENCY' in mg:
            info['currency'] = mg['CURRENCY']

        if 'TOURNO' in mg:
            info['type'] = 'tour'
        else:
            info['type'] = 'ring'
        
        if info['type'] == 'ring':
            info['sb'], info['bb'] = ringBlinds(mg['RINGLIMIT'])
        else:
            info['sb'] = renderTrnyMoney(mg['SB'])
            info['bb'] = renderTrnyMoney(mg['BB'])
            

        # NB: SB, BB must be interpreted as blinds or bets depending on limit type.
        return info


    def readHandInfo(self, hand):
        info = {}
        m = self.re_HandInfo.search(hand.handText,re.DOTALL)
        if m:
            info.update(m.groupdict())
        else:
            print '#'*15, 'START HH', '#'*15
            print hand.handText
            print '#'*15, '  END HH', '#'*15
            raise Exception, "Cannot read hand info from hh above"
        m = self._getGameType(hand.handText)
        if m: info.update(m.groupdict())
        m = self.re_Hid.search(hand.handText)
        if m: info.update(m.groupdict())

        # FIXME: it's a hack couse party doesn't supply hand.maxseats info
        hand.maxseats = '9'
        hand.mixed = None
        
        # TODO : I rather like the idea of just having this dict as hand.info
        logging.debug("readHandInfo: %s" % info)
        for key in info:
            if key == 'DATETIME':
                #Saturday, July 25, 07:53:52 EDT 2009
                #Thursday, July 30, 21:40:41 MSKS 2009
                m2 = re.search("\w+, (?P<M>\w+) (?P<D>\d+), (?P<H>\d+):(?P<MIN>\d+):(?P<S>\d+) (?P<TZ>[A-Z]+) (?P<Y>\d+)", info[key])
                datetimestr = "%s/%s/%s %s:%s:%s" % (m2.group('Y'), m2.group('M'),m2.group('D'),m2.group('H'),m2.group('MIN'),m2.group('S'))
                hand.starttime = datetime.datetime.strptime(datetimestr, "%Y/%B/%d %H:%M:%S")
                #FIXME: it's hack
                tzShift = defaultdict(lambda:0, {'EDT': -5, 'EST': -6, 'MSKS': 3})
                hand.starttime -= datetime.timedelta(hours=tzShift[m2.group('TZ')])
                    
            if key == 'HID':
                hand.handid = info[key]
            if key == 'TABLE':
                hand.tablename = info[key]
            if key == 'BUTTON':
                hand.buttonpos = info[key]
            #if key == 'MAX':
                #hand.maxseats = int(info[key])

            #if key == 'MIXED':
                #if info[key] == None: hand.mixed = None
                #else:   hand.mixed = self.mixes[info[key]]

            if key == 'TOURNO':
                hand.tourNo = info[key]
            if key == 'BUYIN':
                hand.buyin = info[key]
            if key == 'LEVEL':
                hand.level = info[key]
            if key == 'PLAY' and info['PLAY'] != 'Real':
#                hand.currency = 'play' # overrides previously set value
                hand.gametype['currency'] = 'play'

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
            hand.addPlayer(int(a.group('SEAT')), a.group('PNAME'),
                           renderTrnyMoney(a.group('CASH')))

    def markStreets(self, hand):
        # PREFLOP = ** Dealing down cards **
        # This re fails if,  say, river is missing; then we don't get the ** that starts the river.
        assert hand.gametype['base'] == "hold", \
            "wtf! There're no %s games on party" % hand.gametype['base']
        m =  re.search(
            r"\*{2} Dealing down cards \*{2}"
            r"(?P<PREFLOP>.+?)"
            r"(?:\*{2} Dealing Flop \*{2} (?P<FLOP>\[ \S\S, \S\S, \S\S \].+?))?"
            r"(?:\*{2} Dealing Turn \*{2} (?P<TURN>\[ \S\S \].+?))?"
            r"(?:\*{2} Dealing River \*{2} (?P<RIVER>\[ \S\S \].+?))?$"
            , hand.handText,re.DOTALL)
        hand.addStreets(m)

    def readCommunityCards(self, hand, street): # street has been matched by markStreets, so exists in this hand
        if street in ('FLOP','TURN','RIVER'):   # a list of streets which get dealt community cards (i.e. all but PREFLOP)
            #print "DEBUG readCommunityCards:", street, hand.streets.group(street)
            m = self.re_Board.search(hand.streets[street])
            hand.setCommunityCards(street, m.group('CARDS').strip().split(' '))

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
        noSmallBlind = bool(self.re_NoSmallBlind.search(hand.handText))
        if hand.gametype['type'] == 'ring':
            try:
                assert noSmallBlind==False
                m = self.re_PostSB.search(hand.handText)
                hand.addBlind(m.group('PNAME'), 'small blind', m.group('SB'))
            except: # no small blind
                hand.addBlind(None, None, None)
              
            for a in self.re_PostBB.finditer(hand.handText):
                hand.addBlind(a.group('PNAME'), 'big blind', a.group('BB'))
        else: 
            # party doesn't track blinds for tournaments
            # so there're some cra^Wcaclulations
            if hand.buttonpos == 0:
                self.readButton(self, hand)
            # NOTE: code below depends on Hand's implementation
            # playersMap - dict {seat: (pname,stack)}
            playersMap = dict([(f[0], f[1:2]) for f in hand.players]) 
            maxSeat = max(playersMap)
            
            def findFirstNonEmptySeat(startSeat):
                while startSeat not in playersMap:
                    if startSeat >= maxSeat: 
                        startSeat = 0
                    startSeat += 1
                return startSeat
            smartMin = lambda A,B: A if float(A) <= float(B) else B
            
            if noSmallBlind:
                hand.addBlind(None, None, None)
            else:
                smallBlindSeat = findFirstNonEmptySeat(hand.buttonpos + 1)
                blind = smartMin(hand.sb, playersMap[smallBlindSeat][1])
                hand.addBlind(playersMap[smallBlindSeat][0], 'small blind', blind)
                    
            bigBlindSeat = findFirstNonEmptySeat(smallBlindSeat + 1)
            blind = smartMin(hand.bb, playersMap[bigBlindSeat][1])
            hand.addBlind(playersMap[bigBlindSeat][0], 'small blind', blind)
            
                

    def readHeroCards(self, hand):
#    streets PREFLOP, PREDRAW, and THIRD are special cases beacause
#    we need to grab hero's cards
        for street in ('PREFLOP',):
            if street in hand.streets.keys():
                m = self.re_HeroCards.finditer(hand.streets[street])
                for found in m:
#                    if m == None:
#                        hand.involved = False
#                    else:
                    hand.hero = found.group('PNAME')
                    newcards = found.group('NEWCARDS').split(' ')
                    hand.addHoleCards(street, hand.hero, closed=newcards, shown=False, mucked=False, dealt=True)


    def readAction(self, hand, street):
        m = self.re_Action.finditer(hand.streets[street])
        for action in m:
            acts = action.groupdict()
            if action.group('ATYPE') in ('raises','is all-In'):
                hand.addRaiseBy( street, action.group('PNAME'), action.group('BET') )
            elif action.group('ATYPE') == 'calls':
                hand.addCall( street, action.group('PNAME'), action.group('BET') )
                #print action.groupdict()
                #sys.exit(1)
            elif action.group('ATYPE') == 'bets':
                hand.addBet( street, action.group('PNAME'), action.group('BET') )
            elif action.group('ATYPE') == 'folds':
                hand.addFold( street, action.group('PNAME'))
            elif action.group('ATYPE') == 'checks':
                hand.addCheck( street, action.group('PNAME'))
            else:
                print "DEBUG: unimplemented readAction: '%s' '%s'" %(action.group('PNAME'),action.group('ATYPE'),)


    def readShowdownActions(self, hand):
        # all action in readShownCards
        pass
## TODO: pick up mucks also??
        #for shows in self.re_ShowdownAction.finditer(hand.handText):            
            #cards = shows.group('CARDS').split(' ')
            #hand.addShownCards(cards, shows.group('PNAME'))

    def readCollectPot(self,hand):
        for m in self.re_CollectPot.finditer(hand.handText):
            hand.addCollectPot(player=m.group('PNAME'),pot=m.group('POT'))

    def readShownCards(self,hand):
        for m in self.re_ShownCards.finditer(hand.handText):
            if m.group('CARDS') is not None:
                cards = m.group('CARDS')
                cards = cards.split(' ') # needs to be a list, not a set--stud needs the order

                (shown, mucked) = (False, False)
                if m.group('SHOWED') == "show": shown = True
                else: mucked = True

                hand.addShownCards(cards=cards, player=m.group('PNAME'), shown=shown, mucked=mucked)
                
def ringBlinds(ringLimit):
    "Returns blinds for current limit"
    ringLimit = float(ringLimit)
    if ringLimit == 5.: ringLimit = 4.
    return ('%f' % (ringLimit/200.), '%f' % (ringLimit/100.)  )

def renderTrnyMoney(money):
    "renders 'numbers' like '1 200' and '2,000'"
    return money.replace(' ', '').replace(',', '')

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-i", "--input", dest="ipath", help="parse input hand history", default="regression-test-files/stars/horse/HH20090226 Natalie V - $0.10-$0.20 - HORSE.txt")
    parser.add_option("-o", "--output", dest="opath", help="output translation to", default="-")
    parser.add_option("-f", "--follow", dest="follow", help="follow (tail -f) the input", action="store_true", default=False)
    parser.add_option("-q", "--quiet",
                  action="store_const", const=logging.CRITICAL, dest="verbosity", default=logging.INFO)
    parser.add_option("-v", "--verbose",
                  action="store_const", const=logging.INFO, dest="verbosity")
    parser.add_option("--vv",
                  action="store_const", const=logging.DEBUG, dest="verbosity")

    (options, args) = parser.parse_args()

    #LOG_FILENAME = './logging.out'
    logging.basicConfig(level=options.verbosity)

    e = PartyPoker(in_path = options.ipath, out_path = options.opath, follow = options.follow)
