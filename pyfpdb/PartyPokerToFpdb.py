#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Copyright 2009, Grigorij Indigirkin
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
    class ParsingException(Exception):
        "Usage: raise ParsingException(<msg>[, hh=<hh>])"
        def __init__(self, *args, **kwargs):
            if len(args)==0: args=[''] + list(args)
            msg, args = args[0], args[1:]
            if 'hh' in kwargs:
                msg += self.wrapHh(kwargs['hh'])
                del kwargs['hh']
            return Exception.__init__(self, msg, *args, **kwargs)
        def wrapHh(self, hh):
            return ("\n\nHand history attached below:\n"
                    "%(DELIMETER)s\n%(HH)s\n%(DELIMETER)s") % \
                    {'DELIMETER': '#'*50, 'HH': hh}
                    
############################################################
#    Class Variables

    codepage = "cp1252"
    siteId = 9 # TODO: automate; it's a class variable so shouldn't hit DB too often
    filetype = "text" # "text" or "xml". I propose we subclass HHC to HHC_Text and HHC_XML.


    sym = {'USD': "\$", }

    # Static regexes
    # $5 USD NL Texas Hold'em - Saturday, July 25, 07:53:52 EDT 2009
    # NL Texas Hold'em $1 USD Buy-in Trny:45685440 Level:8  Blinds-Antes(600/1 200 -50) - Sunday, May 17, 11:25:07 MSKS 2009
    re_GameInfoRing     = re.compile("""
            (?P<CURRENCY>\$|)\s*(?P<RINGLIMIT>\d+)\s*(?:USD)?\s*
            (?P<LIMIT>(NL))\s+
            (?P<GAME>(Texas\ Hold\'em))
            \s*\-\s*
            (?P<DATETIME>.+)
            """, re.VERBOSE)
    re_GameInfoTrny     = re.compile("""
            (?P<LIMIT>(NL))\s+
            (?P<GAME>(Texas\ Hold\'em))\s+
            (?P<BUYIN>\$?[.0-9]+)\s*(?P<BUYIN_CURRENCY>USD)?\s*Buy-in\s+
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
          \(\s*\$?(?P<CASH>[0-9,.]+)\s*(?:USD|)\s*\)
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
            subst = {'PLYR': player_re, 'CUR_SYM': hand.SYMBOL[hand.gametype['currency']],
                'CUR': hand.gametype['currency'] if hand.gametype['currency']!='T$' else ''}
            logging.debug("player_re: " + subst['PLYR'])
            logging.debug("CUR_SYM: " + subst['CUR_SYM'])
            logging.debug("CUR: " + subst['CUR'])
            self.re_PostSB = re.compile(
                r"^%(PLYR)s posts small blind \[%(CUR_SYM)s(?P<SB>[.0-9]+) ?%(CUR)s\]\." %  subst, 
                re.MULTILINE)
            self.re_PostBB = re.compile(
                r"^%(PLYR)s posts big blind \[%(CUR_SYM)s(?P<BB>[.0-9]+) ?%(CUR)s\]\." %  subst, 
                re.MULTILINE)
            self.re_Antes = re.compile(
                r"^%(PLYR)s posts ante \[%(CUR_SYM)s(?P<ANTE>[.0-9]+) ?%(CUR)s\]\." %  subst,
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
                (?:\s+\[%(CUR_SYM)s(?P<BET>[.,\d]+)\s*%(CUR)s\])?
                """ %  subst, 
                re.MULTILINE|re.VERBOSE)
            self.re_ShownCards = re.compile(
                r"^%s (?P<SHOWED>(?:doesn\'t )?shows?) "  %  player_re + 
                r"\[ *(?P<CARDS>.+) *\](?P<COMBINATION>.+)\.", 
                re.MULTILINE)
            self.re_CollectPot = re.compile(
                r""""^%(PLYR)s \s+ wins \s+
                %(CUR_SYM)s(?P<POT>[.\d]+)\s*%(CUR)s""" %  subst, 
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

                ["tour", "hold", "nl"],
                #["tour", "hold", "pl"],
                #["tour", "hold", "fl"],
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

        print self.ParsingException().wrapHh( handText )
        
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
               }
        currencies = { '$':'USD', '':'T$' }

        for expectedField in ['LIMIT', 'GAME']:
            if mg[expectedField] is None:
                raise self.ParsingException(
                    "Cannot fetch field '%s'" % expectedField,
                    hh = handText)
        try:
            info['limitType'] = limits[mg['LIMIT']]
        except:
            raise self.ParsingException(
                "Unknown limit '%s'" % mg['LIMIT'],
                hh = handText)

        try:
            (info['base'], info['category']) = games[mg['GAME']]
        except:
            raise self.ParsingException(
                "Unknown game type '%s'" % mg['GAME'],
                hh = handText)


        if 'TOURNO' in mg:
            info['type'] = 'tour'
        else:
            info['type'] = 'ring'
        
        if info['type'] == 'ring':
            info['sb'], info['bb'] = ringBlinds(mg['RINGLIMIT'])
            # FIXME: there are only $ and play money availible for cash
            info['currency'] = currencies(mg['CURRENCY'])
        else:
            info['sb'] = renderTrnyMoney(mg['SB'])
            info['bb'] = renderTrnyMoney(mg['BB'])
            info['currency'] = 'T$'
            

        # NB: SB, BB must be interpreted as blinds or bets depending on limit type.
        return info


    def readHandInfo(self, hand):
        info = {}
        m = self.re_HandInfo.search(hand.handText,re.DOTALL)
        if m:
            info.update(m.groupdict())
        else:
            raise self.ParsingException("Cannot read Handinfo for current hand", hh=hand.handText)
        m = self._getGameType(hand.handText)
        if m: info.update(m.groupdict())
        m = self.re_Hid.search(hand.handText)
        if m: info.update(m.groupdict())

        # FIXME: it's a hack cause party doesn't supply hand.maxseats info
        #hand.maxseats = '9'
        hand.mixed = None
        
        # TODO : I rather like the idea of just having this dict as hand.info
        logging.debug("readHandInfo: %s" % info)
        for key in info:
            if key == 'DATETIME':
                #Saturday, July 25, 07:53:52 EDT 2009
                #Thursday, July 30, 21:40:41 MSKS 2009
                m2 = re.search("\w+, (?P<M>\w+) (?P<D>\d+), (?P<H>\d+):(?P<MIN>\d+):(?P<S>\d+) (?P<TZ>[A-Z]+) (?P<Y>\d+)", info[key])
                # we cant use '%B' due to locale problems
                months = ['January', 'February', 'March', 'April','May', 'June',
                    'July','August','September','October','November','December']
                month = months.index(m2.group('M')) + 1
                datetimestr = "%s/%s/%s %s:%s:%s" % (m2.group('Y'), month,m2.group('D'),m2.group('H'),m2.group('MIN'),m2.group('S'))
                hand.starttime = datetime.datetime.strptime(datetimestr, "%Y/%m/%d %H:%M:%S")
                #tzShift = defaultdict(lambda:0, {'EDT': -5, 'EST': -6, 'MSKS': 3})
                #hand.starttime -= datetime.timedelta(hours=tzShift[m2.group('TZ')])
                  
            if key == 'HID':
                hand.handid = info[key]
            if key == 'TABLE':
                hand.tablename = info[key]
            if key == 'BUTTON':
                hand.buttonpos = info[key]
            if key == 'TOURNO':
                hand.tourNo = info[key]
            if key == 'BUYIN':
                #FIXME: it's dirty hack T_T
                cur = info[key][0] if info[key][0] not in '0123456789' else ''
                hand.buyin = info[key] + '+%s0' % cur
            if key == 'LEVEL':
                hand.level = info[key]
            if key == 'PLAY' and info['PLAY'] != 'Real':
                # TODO: play money wasn't tested
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

    def readCommunityCards(self, hand, street): 
        if street in ('FLOP','TURN','RIVER'):   
            m = self.re_Board.search(hand.streets[street])
            hand.setCommunityCards(street, renderCards(m.group('CARDS')))

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
                self.readButton(hand)
            # NOTE: code below depends on Hand's implementation
            # playersMap - dict {seat: (pname,stack)}
            playersMap = dict([(f[0], f[1:3]) for f in hand.players]) 
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
                smallBlindSeat = findFirstNonEmptySeat(int(hand.buttonpos) + 1)
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
                    newcards = renderCards(found.group('NEWCARDS'))
                    hand.addHoleCards(street, hand.hero, closed=newcards, shown=False, mucked=False, dealt=True)


    def readAction(self, hand, street):
        m = self.re_Action.finditer(hand.streets[street])
        for action in m:
            acts = action.groupdict()
            if action.group('ATYPE') in ('raises','is all-In'):
                #print action.groupdict()
                #sys.exit(1)
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
                cards = renderCards(m.group('CARDS'))

                (shown, mucked) = (False, False)
                if m.group('SHOWED') == "show": shown = True
                else: mucked = True

                hand.addShownCards(cards=cards, player=m.group('PNAME'), shown=shown, mucked=mucked)
                
def ringBlinds(ringLimit):
    "Returns blinds for current limit"
    ringLimit = float(ringLimit)
    if ringLimit == 5.: ringLimit = 4.
    return ('%.2f' % (ringLimit/200.), '%.2f' % (ringLimit/100.)  )

def renderTrnyMoney(money):
    "renders 'numbers' like '1 200' and '2,000'"
    return money.replace(' ', '').replace(',', '')

def renderCards(string):
    "splits strings like ' Js, 4d '"
    cards = string.strip().split(' ')
    return filter(len, map(lambda x: x.strip(' ,'), cards))
    

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
