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


class Pkr(HandHistoryConverter):

    # Class Variables

    sitename = "PKR"
    filetype = "text"
    codepage = ("utf8", "cp1252")
    siteId   = 12 # Needs to match id entry in Sites database

    mixes = { 'HORSE': 'horse', '8-Game': '8game', 'HOSE': 'hose'} # Legal mixed games
    sym = {'USD': "\$"}         # ADD Euro, Sterling, etc HERE
    substitutions = {
                     'LEGAL_ISO' : "USD",    # legal ISO currency codes
                            'LS' : "\$|"        # legal currency symbols - Euro(cp1252, utf-8)
                    }

    limits = { 'NO LIMIT':'nl', 'POT LIMIT':'pl', 'LIMIT':'fl' }
    games = {                          # base, category
                              "HOLD'EM" : ('hold','holdem'),
                           'FIXMEOmaha' : ('hold','omahahi'),
                     'FIXMEOmaha Hi/Lo' : ('hold','omahahilo'),
                     'FIXME5 Card Draw' : ('draw','fivedraw')
               }
    currencies = { u'€':'EUR', '$':'USD', '':'T$' }

    # Static regexes
    re_GameInfo     = re.compile(u"""
          Table\s\#\d+\s\-\s(?P<TABLE>[a-zA-Z\ \d]+)\s
          Starting\sHand\s\#(?P<HID>[0-9]+)\s
          Start\stime\sof\shand:\s(?P<DATETIME>.*)\s
          Last\sHand\s\#[0-9]+\s
          Game\sType:\s(?P<GAME>HOLD'EM|5\sCard\sDraw)\s
          Limit\sType:\s(?P<LIMIT>NO\sLIMIT|LIMIT|POT\sLIMIT)\s
          Table\sType\:\sRING\s
          Money\sType:\sREAL\sMONEY\s
          Blinds\sare\snow\s(?P<CURRENCY>%(LS)s|)?
          (?P<SB>[.0-9]+)/(%(LS)s)?
          (?P<BB>[.0-9]+)
          """ % substitutions, re.MULTILINE|re.VERBOSE)

    re_PlayerInfo   = re.compile(u"""
              ^Seat\s(?P<SEAT>[0-9]+):\s
              (?P<PNAME>.*)\s-\s
              (%(LS)s)?(?P<CASH>[.0-9]+)
            """ % substitutions, re.MULTILINE|re.VERBOSE)

    re_HandInfo     = re.compile("""
          ^Table\s\'(?P<TABLE>[-\ a-zA-Z\d]+)\'\s
          ((?P<MAX>\d+)-max\s)?
          (?P<PLAY>\(Play\sMoney\)\s)?
          (Seat\s\#(?P<BUTTON>\d+)\sis\sthe\sbutton)?""", 
          re.MULTILINE|re.VERBOSE)

    re_SplitHands   = re.compile('\n\n+')
    re_TailSplitHands   = re.compile('(\n\n\n+)')
    re_Button       = re.compile('Seat #(?P<BUTTON>\d+) is the button', re.MULTILINE)
    re_Board        = re.compile(r"\[(?P<CARDS>.+)\]")
#        self.re_setHandInfoRegex('.*#(?P<HID>[0-9]+): Table (?P<TABLE>[ a-zA-Z]+) - \$?(?P<SB>[.0-9]+)/\$?(?P<BB>[.0-9]+) - (?P<GAMETYPE>.*) - (?P<HR>[0-9]+):(?P<MIN>[0-9]+) ET - (?P<YEAR>[0-9]+)/(?P<MON>[0-9]+)/(?P<DAY>[0-9]+)Table (?P<TABLE>[ a-zA-Z]+)\nSeat (?P<BUTTON>[0-9]+)')    

    re_DateTime     = re.compile("""(?P<Y>[0-9]{4})\/(?P<M>[0-9]{2})\/(?P<D>[0-9]{2})[\- ]+(?P<H>[0-9]+):(?P<MIN>[0-9]+):(?P<S>[0-9]+)""", re.MULTILINE)
 
    def compilePlayerRegexs(self,  hand):
        players = set([player[1] for player in hand.players])
        if not players <= self.compiledPlayers: # x <= y means 'x is subset of y'
            # we need to recompile the player regexs.
            self.compiledPlayers = players
            player_re = "(?P<PNAME>" + "|".join(map(re.escape, players)) + ")"
            subst = {'PLYR': player_re, 'CUR': self.sym[hand.gametype['currency']]}
            log.debug("player_re: " + player_re)
            self.re_PostSB    = re.compile(r"^%(PLYR)s posts small blind %(CUR)s(?P<SB>[.0-9]+)" %  subst, re.MULTILINE)
            # FIXME: Sionel posts $0.04 is a second big blind in a different format.
            self.re_PostBB    = re.compile(r"^%(PLYR)s posts big blind %(CUR)s(?P<BB>[.0-9]+)" %  subst, re.MULTILINE)
            self.re_Antes     = re.compile(r"^%(PLYR)s: posts the ante %(CUR)s(?P<ANTE>[.0-9]+)" % subst, re.MULTILINE)
            self.re_BringIn   = re.compile(r"^%(PLYR)s: brings[- ]in( low|) for %(CUR)s(?P<BRINGIN>[.0-9]+)" % subst, re.MULTILINE)
            self.re_PostBoth  = re.compile(r"^%(PLYR)s: posts small \& big blinds %(CUR)s(?P<SBBB>[.0-9]+)" %  subst, re.MULTILINE)
            self.re_HeroCards = re.compile(r"^Dealing( \[(?P<OLDCARDS>.+?)\])?( \[(?P<NEWCARDS>.+?)\]) to %(PLYR)s" % subst, re.MULTILINE)
            self.re_Action    = re.compile(r"""
                        ^%(PLYR)s(?P<ATYPE>\sbets|\schecks|\sraises|\scalls|\sfolds)(\sto)?
                        (\s(%(CUR)s)?(?P<BET>[.\d]+))?
                        """ %  subst, re.MULTILINE|re.VERBOSE)
            self.re_ShowdownAction   = re.compile(r"^%(PLYR)s shows \[(?P<CARDS>.*)\]" % subst, re.MULTILINE)
            self.re_CollectPot       = re.compile(r"^%(PLYR)s wins %(CUR)s(?P<POT>[.\d]+)" %  subst, re.MULTILINE)
            self.re_sitsOut          = re.compile("^%s sits out" %  player_re, re.MULTILINE)
            self.re_ShownCards       = re.compile("^Seat (?P<SEAT>[0-9]+): %s (\(.*\) )?(?P<SHOWED>showed|mucked) \[(?P<CARDS>.*)\].*" %  player_re, re.MULTILINE)

    def readSupportedGames(self):
        return [["ring", "hold", "nl"],
                ["ring", "hold", "pl"],
                ["ring", "hold", "fl"],

                ["tour", "hold", "nl"],
                ["tour", "hold", "pl"],
                ["tour", "hold", "fl"],
               ]

    def determineGameType(self, handText):
        info = {}
        m = self.re_GameInfo.search(handText)
        if not m:
            tmp = handText[0:100]
            log.error(_("Unable to recognise gametype from: '%s'") % tmp)
            log.error(_("determineGameType: Raising FpdbParseError"))
            raise FpdbParseError(_("Unable to recognise gametype from: '%s'") % tmp)

        mg = m.groupdict()
        #print "DEBUG: %s" % mg

        info['type'] = 'ring'

        if 'LIMIT' in mg:
            info['limitType'] = self.limits[mg['LIMIT']]
        if 'GAME' in mg:
            (info['base'], info['category']) = self.games[mg['GAME']]
        if 'SB' in mg:
            info['sb'] = mg['SB']
        if 'BB' in mg:
            info['bb'] = mg['BB']
        if 'CURRENCY' in mg:
            info['currency'] = self.currencies[mg['CURRENCY']]

        if info['limitType'] == 'fl' and info['bb'] is not None and info['type'] == 'ring' and info['base'] != 'stud':
            try:
                info['sb'] = self.Lim_Blinds[mg['BB']][0]
                info['bb'] = self.Lim_Blinds[mg['BB']][1]
            except KeyError:
                log.error(_("Lim_Blinds has no lookup for '%s'") % mg['BB'])
                log.error(_("determineGameType: Raising FpdbParseError"))
                raise FpdbParseError(_("Lim_Blinds has no lookup for '%s'") % mg['BB'])

        return info

    def readHandInfo(self, hand):
        info = {}
        m = self.re_HandInfo.search(hand.handText,re.DOTALL)
        if m:
            info.update(m.groupdict())
#                hand.maxseats = int(m2.group(1))
        else:
            pass  # throw an exception here, eh?
        m = self.re_GameInfo.search(hand.handText)
        if m:
            info.update(m.groupdict())
#        m = self.re_Button.search(hand.handText)
#        if m: info.update(m.groupdict()) 
        # TODO : I rather like the idea of just having this dict as hand.info
        log.debug("readHandInfo: %s" % info)
        for key in info:
            if key == 'DATETIME':
                #2008/11/12 10:00:48 CET [2008/11/12 4:00:48 ET]
                #2008/08/17 - 01:14:43 (ET)
                #2008/09/07 06:23:14 ET
                m1 = self.re_DateTime.finditer(info[key])
                datetimestr = "2000/01/01 00:00:00"  # default used if time not found
                for a in m1:
                    datetimestr = "%s/%s/%s %s:%s:%s" % (a.group('Y'), a.group('M'),a.group('D'),a.group('H'),a.group('MIN'),a.group('S'))
                hand.startTime = datetime.datetime.strptime(datetimestr, "%Y/%m/%d %H:%M:%S")
            if key == 'HID':
                hand.handid = info[key]
            if key == 'TOURNO':
                hand.tourNo = info[key]
            if key == 'BUYIN':
                if info[key] == 'Freeroll':
                    hand.buyin = '$0+$0'
                else:
                    #FIXME: The key looks like: '€0.82+€0.18 EUR'
                    #       This should be parsed properly and used
                    hand.buyin = info[key]
            if key == 'LEVEL':
                hand.level = info[key]

            if key == 'TABLE':
                if hand.tourNo != None:
                    hand.tablename = re.split(" ", info[key])[1]
                else:
                    hand.tablename = info[key]
            if key == 'BUTTON':
                hand.buttonpos = info[key]
            if key == 'MAX':
                hand.maxseats = int(info[key])

            if key == 'MIXED':
                hand.mixed = self.mixes[info[key]] if info[key] is not None else None
            if key == 'PLAY' and info['PLAY'] is not None:
#                hand.currency = 'play' # overrides previously set value
                hand.gametype['currency'] = 'play'

    def readButton(self, hand):
        m = self.re_Button.search(hand.handText)
        if m:
            hand.buttonpos = int(m.group('BUTTON'))
        else:
            log.info('readButton: not found')

    def readPlayerStacks(self, hand):
        log.debug("readPlayerStacks")
        m = self.re_PlayerInfo.finditer(hand.handText)
        players = {} # Player Stacks are printed in the same format
                     # At the beginning and end of the hand history
                     # The hash is to cache the player names, and ignore
                     # The second round
        for a in m:
            if players.has_key(a.group('PNAME')):
                pass # Ignore
            else:
                #print "DEBUG: addPlayer(%s, %s, %s)" % (a.group('SEAT'), a.group('PNAME'), a.group('CASH'))
                hand.addPlayer(int(a.group('SEAT')), a.group('PNAME'), a.group('CASH'))
                players[a.group('PNAME')] = True

    def markStreets(self, hand):
        # PREFLOP = ** Dealing down cards **
        # This re fails if,  say, river is missing; then we don't get the ** that starts the river.
        if hand.gametype['base'] in ("hold"):
            m =  re.search(r"Dealing Cards(?P<PREFLOP>.+(?=Dealing Flop)|.+)"
                       r"(Dealing Flop(?P<FLOP> \[\S\S \S\S \S\S\].+(?=Dealing Turn)|.+))?"
                       r"(Dealing Turn (?P<TURN>\[\S\S\].+(?=Dealing River)|.+))?"
                       r"(Dealing River (?P<RIVER>\[\S\S\].+))?", hand.handText,re.DOTALL)
        elif hand.gametype['base'] in ("stud"):
            m =  re.search(r"(?P<ANTES>.+(?=\*\*\* 3rd STREET \*\*\*)|.+)"
                           r"(\*\*\* 3rd STREET \*\*\*(?P<THIRD>.+(?=\*\*\* 4th STREET \*\*\*)|.+))?"
                           r"(\*\*\* 4th STREET \*\*\*(?P<FOURTH>.+(?=\*\*\* 5th STREET \*\*\*)|.+))?"
                           r"(\*\*\* 5th STREET \*\*\*(?P<FIFTH>.+(?=\*\*\* 6th STREET \*\*\*)|.+))?"
                           r"(\*\*\* 6th STREET \*\*\*(?P<SIXTH>.+(?=\*\*\* RIVER \*\*\*)|.+))?"
                           r"(\*\*\* RIVER \*\*\*(?P<SEVENTH>.+))?", hand.handText,re.DOTALL)
        elif hand.gametype['base'] in ("draw"):
            m =  re.search(r"(?P<PREDEAL>.+(?=\*\*\* DEALING HANDS \*\*\*)|.+)"
                           r"(\*\*\* DEALING HANDS \*\*\*(?P<DEAL>.+(?=\*\*\* FIRST DRAW \*\*\*)|.+))?"
                           r"(\*\*\* FIRST DRAW \*\*\*(?P<DRAWONE>.+(?=\*\*\* SECOND DRAW \*\*\*)|.+))?"
                           r"(\*\*\* SECOND DRAW \*\*\*(?P<DRAWTWO>.+(?=\*\*\* THIRD DRAW \*\*\*)|.+))?"
                           r"(\*\*\* THIRD DRAW \*\*\*(?P<DRAWTHREE>.+))?", hand.handText,re.DOTALL)
        hand.addStreets(m)

    def readCommunityCards(self, hand, street): # street has been matched by markStreets, so exists in this hand
        if street in ('FLOP','TURN','RIVER'):   # a list of streets which get dealt community cards (i.e. all but PREFLOP)
            #print "DEBUG readCommunityCards:", street, hand.streets.group(street)
            m = self.re_Board.search(hand.streets[street])
            hand.setCommunityCards(street, m.group('CARDS').split(' '))

    def readAntes(self, hand):
        log.debug("reading antes")
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
                if found.group('NEWCARDS') is None:
                    newcards = []
                else:
                    newcards = found.group('NEWCARDS').split(' ')
                if found.group('OLDCARDS') is None:
                    oldcards = []
                else:
                    oldcards = found.group('OLDCARDS').split(' ')

                if street == 'THIRD' and len(newcards) == 3: # hero in stud game
                    hand.hero = player
                    hand.dealt.add(player) # need this for stud??
                    hand.addHoleCards(street, player, closed=newcards[0:2], open=[newcards[2]], shown=False, mucked=False, dealt=False)
                else:
                    hand.addHoleCards(street, player, open=newcards, closed=oldcards, shown=False, mucked=False, dealt=False)


    def readAction(self, hand, street):
        m = self.re_Action.finditer(hand.streets[street])
        for action in m:
            acts = action.groupdict()
            #print "DEBUG: readAction: acts: %s" % acts
            if action.group('ATYPE') == ' raises':
                hand.addRaiseTo( street, action.group('PNAME'), action.group('BET') )
            elif action.group('ATYPE') == ' calls':
                # Amount in hand history is not cumulative
                # ie. Player3 calls 0.08
                #     Player5 raises to 0.16
                #     Player3 calls 0.16 (Doh! he's only calling 0.08
                # TODO: Going to have to write an addCallStoopid()
                #print "DEBUG: addCall( %s, %s, None)" %(street,action.group('PNAME'))
                hand.addCall( street, action.group('PNAME'), action.group('BET') )
            elif action.group('ATYPE') == ' bets':
                hand.addBet( street, action.group('PNAME'), action.group('BET') )
            elif action.group('ATYPE') == ' folds':
                hand.addFold( street, action.group('PNAME'))
            elif action.group('ATYPE') == ' checks':
                hand.addCheck( street, action.group('PNAME'))
            elif action.group('ATYPE') == ' discards':
                hand.addDiscard(street, action.group('PNAME'), action.group('BET'), action.group('DISCARDED'))
            elif action.group('ATYPE') == ' stands pat':
                hand.addStandsPat( street, action.group('PNAME'))
            else:
                print "DEBUG: unimplemented readAction: '%s' '%s'" %(action.group('PNAME'),action.group('ATYPE'),)


    def readShowdownActions(self, hand):
        # TODO: pick up mucks also??
        for shows in self.re_ShowdownAction.finditer(hand.handText):
            cards = shows.group('CARDS').split(' ')
            #print "DEBUG: addShownCards(%s, %s)" %(cards, shows.group('PNAME'))
            hand.addShownCards(cards, shows.group('PNAME'))

    def readCollectPot(self,hand):
        for m in self.re_CollectPot.finditer(hand.handText):
            #print "DEBUG: addCollectPot(%s, %s)" %(m.group('PNAME'), m.group('POT'))
            hand.addCollectPot(player=m.group('PNAME'),pot=m.group('POT'))

    def readShownCards(self,hand):
        for m in self.re_ShownCards.finditer(hand.handText):
            if m.group('CARDS') is not None:
                cards = m.group('CARDS')
                cards = cards.split(' ') # needs to be a list, not a set--stud needs the order

                (shown, mucked) = (False, False)
                if m.group('SHOWED') == "showed": shown = True
                elif m.group('SHOWED') == "mucked": mucked = True

                hand.addShownCards(cards=cards, player=m.group('PNAME'), shown=shown, mucked=mucked)

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-i", "--input", dest="ipath", help="parse input hand history", default="regression-test-files/stars/horse/HH20090226 Natalie V - $0.10-$0.20 - HORSE.txt")
    parser.add_option("-o", "--output", dest="opath", help="output translation to", default="-")
    parser.add_option("-f", "--follow", dest="follow", help="follow (tail -f) the input", action="store_true", default=False)
    #parser.add_option("-q", "--quiet", action="store_const", const=logging.CRITICAL, dest="verbosity", default=logging.INFO)
    #parser.add_option("-v", "--verbose", action="store_const", const=logging.INFO, dest="verbosity")
    #parser.add_option("--vv", action="store_const", const=logging.DEBUG, dest="verbosity")

    (options, args) = parser.parse_args()

    e = PokerStars(in_path = options.ipath, out_path = options.opath, follow = options.follow)
