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
    siteId   = 13 # Needs to match id entry in Sites database

    mixes = { 'HORSE': 'horse', '8-Game': '8game', 'HOSE': 'hose'} # Legal mixed games
    sym = {'USD': "\$", 'T$': "", "EUR": u"\u20ac", "GBP": u"\£"} # ADD Euro, Sterling, etc HERE
    substitutions = {
                     'LEGAL_ISO' : "USD|EUR|GBP",    # legal ISO currency codes
                            'LS' : u"\$|\xe2\x82\xac|\u20ac|\£|", # legal currency symbols - Euro(cp1252, utf-8)
                           'NUM' : u".,\d",
                    }

    limits = { 'NO LIMIT':'nl', 'POT LIMIT':'pl', 'LIMIT':'fl' }
    games = {                          # base, category
                              "HOLD'EM" : ('hold','holdem'),
                                'OMAHA' : ('hold','omahahi'),
                          'OMAHA HI/LO' : ('hold','omahahilo'),
                     'FIXME5 Card Draw' : ('draw','fivedraw')
               }
    currencies = { u'€':'EUR', '$':'USD', '':'T$', u'£':'GBP' }
    
    months = { 'January':1, 'Jan':1, 'February':2, 'Feb':2, 'March':3, 'Mar':3,
                 'April':4, 'Apr':4, 'May':5, 'May':5, 'June':6, 'Jun':6,
                  'July':7, 'Jul':7, 'August':8, 'Aug':8, 'September':9, 'Sep':9,
               'October':10, 'Oct':10, 'November':11, 'Nov':11, 'December':12, 'Dec':12}

    # Static regexes
    re_GameInfo     = re.compile(u"""
          Table\s\#\d+\s\-\s((Tournament|STT)\s\#\s?(?P<TOURNO>\d+)(\sTable\s\#)?)?(?P<TABLE>.+?)?\s
          Starting\sHand\s\#(?P<HID>[0-9]+)\s
          Start\stime\sof\shand:\s(?P<DATETIME>.*)\s
          Last\sHand\s(n/a|\#[0-9]+)\s
          Game\sType:\s(?P<GAME>HOLD'EM|OMAHA|OMAHA\sHI/LO)\s
          Limit\sType:\s(?P<LIMIT>NO\sLIMIT|LIMIT|POT\sLIMIT)\s
          Table\sType:\s(RING|TOURNAMENT)\s
          Money\sType:\s(?P<MONEY>PLAY\sMONEY|REAL\sMONEY|TOURNAMENT\sCHIPS|Real\smoney|Tournament\schips)\s
          Blinds\sare\snow\s(?P<CURRENCY>%(LS)s|)?
          (?P<SB>[%(NUM)s]+)\s?/\s?(%(LS)s)?
          (?P<BB>[%(NUM)s]+)
          """ % substitutions, re.MULTILINE|re.VERBOSE)

    re_PlayerInfo   = re.compile(u"""
              ^Seat\s(?P<SEAT>[0-9]+):\s
              (?P<PNAME>.+?)
              (\s\(bounty\svalue\s(%(LS)s)?[%(NUM)s]+,\sbounty\swon\s(%(LS)s)?[%(NUM)s]+\))?\s-\s
              (%(LS)s)?(?P<CASH>[%(NUM)s]+)
            """ % substitutions, re.MULTILINE|re.VERBOSE)

    re_HandInfo     = re.compile("""
          ((?P<MAX>\d+)-max\s)?
          (?P<PLAY>\(Play\sMoney\)\s)?
          Moving\sButton\sto\sseat\s(?P<BUTTON>\d+)\s""", 
          re.MULTILINE|re.VERBOSE)

    re_Identify     = re.compile(u'Starting\sHand\s\#\d+')
    re_SplitHands   = re.compile('\n\n+')
    re_TailSplitHands   = re.compile('(\n\n\n+)')
    re_Button       = re.compile('Seat #(?P<BUTTON>\d+) is the button', re.MULTILINE)
    re_Board        = re.compile(r"(?P<CARDS>\[.+\])")
    re_Cards        = re.compile(r"\[(?P<CARD>.+?)\]")
    re_Partial      = re.compile(u'Table\s\#\d+\s\-\s')
#        self.re_setHandInfoRegex('.*#(?P<HID>[0-9]+): Table (?P<TABLE>[ a-zA-Z]+) - \$?(?P<SB>[.0-9]+)/\$?(?P<BB>[.0-9]+) - (?P<GAMETYPE>.*) - (?P<HR>[0-9]+):(?P<MIN>[0-9]+) ET - (?P<YEAR>[0-9]+)/(?P<MON>[0-9]+)/(?P<DAY>[0-9]+)Table (?P<TABLE>[ a-zA-Z]+)\nSeat (?P<BUTTON>[0-9]+)')    

    re_DateTime     = re.compile("""(?P<D>[0-9]{2}) (?P<M>\w+) (?P<Y>[0-9]{4}) (?P<H>[0-9]+):(?P<MIN>[0-9]+):(?P<S>[0-9]+)""", re.MULTILINE)
 
    def compilePlayerRegexs(self,  hand):
        players = set([player[1] for player in hand.players])
        if not players <= self.compiledPlayers: # x <= y means 'x is subset of y'
            # we need to recompile the player regexs.
            self.compiledPlayers = players
            player_re = "(?P<PNAME>" + "|".join(map(re.escape, players)) + ")"
            subst = {'PLYR': player_re, 'CUR': self.sym[hand.gametype['currency']], 'NUM' : u".,\d",}
            self.re_PostSB    = re.compile(r"^%(PLYR)s posts small blind \(%(CUR)s(?P<SB>[%(NUM)s]+)\)" %  subst, re.MULTILINE)
            # FIXME: Sionel posts $0.04 is a second big blind in a different format.
            self.re_PostBB    = re.compile(r"^%(PLYR)s posts big blind \(%(CUR)s(?P<BB>[%(NUM)s]+)\)" %  subst, re.MULTILINE)
            self.re_Antes     = re.compile(r"^%(PLYR)s posts ante of %(CUR)s(?P<ANTE>[%(NUM)s]+)" % subst, re.MULTILINE)
            self.re_BringIn   = re.compile(r"^%(PLYR)s brings[- ]in( low|) for %(CUR)s(?P<BRINGIN>[%(NUM)s]+)" % subst, re.MULTILINE)
            self.re_Post      = re.compile(r"^%(PLYR)s posts %(CUR)s(?P<BB>[%(NUM)s]+)$" %  subst, re.MULTILINE)
            self.re_HeroCards = re.compile(r"^Dealing( (?P<OLDCARDS>\[.+\]))?( (?P<NEWCARDS>\[.+\])) to %(PLYR)s" % subst, re.MULTILINE)
            self.re_Action    = re.compile(r"""
                        ^%(PLYR)s(?P<ATYPE>\sbets|\schecks|\sraises|\scalls|\sfolds)(\sand\sshows\s\[.+\])?(\sto)?
                        (\s(%(CUR)s)?(?P<BET>[%(NUM)s]+))?(\s\(all\-in\))?\s*$
                        """ %  subst, re.MULTILINE|re.VERBOSE)
            self.re_ShowdownAction   = re.compile(r"^%(PLYR)s shows (?P<CARDS>\[.+\])" % subst, re.MULTILINE)
            self.re_CollectPot       = re.compile(r"^%(PLYR)s (ties( side pot \#\d)?, and )?(ties|wins) %(CUR)s(?P<POT>[%(NUM)s]+)" %  subst, re.MULTILINE)
            self.re_sitsOut          = re.compile("^%s sits out" %  player_re, re.MULTILINE)
            self.re_ShownCards       = re.compile("^Seat (?P<SEAT>[0-9]+): %s (\(.*\) )?(?P<SHOWED>showed|mucked) (?P<CARDS>\[.+\])" %  player_re, re.MULTILINE)

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
            m2 = self.re_Partial.search(handText)
            if not m2:
                message = 'Join in hand'
                raise FpdbHandPartial("Partial hand history: %s" % message)
            else:
                tmp = handText[0:200]
                log.error(_("PkrToFpdb.determineGameType: '%s'") % tmp)
                raise FpdbParseError

        mg = m.groupdict()
        #print "DEBUG: %s" % mg

        if 'LIMIT' in mg:
            info['limitType'] = self.limits[mg['LIMIT']]
        if 'GAME' in mg:
            (info['base'], info['category']) = self.games[mg['GAME']]
        if 'SB' in mg:
            info['sb'] = self.clearMoneyString(mg['SB'])
        if 'BB' in mg:
            info['bb'] = self.clearMoneyString(mg['BB'])
        if 'CURRENCY' in mg:
            if 'MONEY'!='PLAY MONEY':
                info['currency'] = self.currencies[mg['CURRENCY']]
            else:
                info['currency'] = 'play'
        if 'TOURNO' in mg and mg['TOURNO'] is not None:
            info['type'] = 'tour'
        else:
            info['type'] = 'ring'

        return info

    def readHandInfo(self, hand):
        info = {}
        m1 = self.re_HandInfo.search(hand.handText,re.DOTALL)
        m2 = self.re_GameInfo.search(hand.handText)
        if m1 is None or m2 is None:
            tmp = hand.handText[0:200]
            log.error(_("PkrToFpdb.readHandInfo: '%s'") % tmp)
            raise FpdbParseError

        info.update(m1.groupdict())
        info.update(m2.groupdict())
#        m = self.re_Button.search(hand.handText)
#        if m: info.update(m.groupdict()) 
        # TODO : I rather like the idea of just having this dict as hand.info
        log.debug("readHandInfo: %s" % info)
        for key in info:
            if key == 'DATETIME':
                #11 Jun 2012 21:38:10
                m3 = self.re_DateTime.finditer(info[key])
                datetimestr = "2000/01/01 00:00:00"  # default used if time not found
                for a in m3:
                    month = self.months[a.group('M')]
                    datetimestr = "%s/%s/%s %s:%s:%s" % (a.group('Y'), month,a.group('D'),a.group('H'),a.group('MIN'),a.group('S'))
                hand.startTime = datetime.datetime.strptime(datetimestr, "%Y/%m/%d %H:%M:%S")
            if key == 'HID':
                hand.handid = info[key]
            if key == 'TOURNO' and info[key] is not None:
                hand.tourNo = info[key]
                hand.buyin = 0
                hand.fee = 0
                hand.buyinCurrency = 'NA'
            if key == 'BUYIN':
                if info[key] == 'Freeroll':
                    hand.buyin = 0
                    hand.fee = 0
                    hand.buyinCurrency = 'FREE'
                else:
                    #FIXME: The key looks like: '€0.82+€0.18 EUR'
                    #       This should be parsed properly and used
                    hand.buyin = int(100*Decimal(info[key]))
            if key == 'LEVEL':
                hand.level = info[key]
            if key == 'TABLE':
                if info[key] is None:
                    hand.tablename = '1'
                else:
                    hand.tablename = info[key]
            if key == 'BUTTON':
                hand.buttonpos = int(info[key])
            if key == 'MAX' and info[key] is not None:
                hand.maxseats = int(info[key])

    def readButton(self, hand):
        if hand.buttonpos==0:
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
                hand.addPlayer(int(a.group('SEAT')), a.group('PNAME'), self.clearMoneyString(a.group('CASH')))
                players[a.group('PNAME')] = True

    def markStreets(self, hand):
        # PREFLOP = ** Dealing down cards **
        # This re fails if,  say, river is missing; then we don't get the ** that starts the river.
        if hand.gametype['base'] in ("hold"):
            m =  re.search(r"Dealing Cards(?P<PREFLOP>.+(?=Dealing Flop)|.+)"
                       r"(Dealing Flop (?P<FLOP>(\[\S\S \S\S \S\S\]|\[\S \S\]\[\S \S\]\[\S \S\]|\[\S\S\]\[\S\S\]\[\S\S\]).+(?=Dealing\sTurn)|.+))?"
                       r"(Dealing Turn (?P<TURN>(\[\S\S\]|\[\S \S\]).+(?=Dealing\sRiver)|.+))?"
                       r"(Dealing River (?P<RIVER>(\[\S\S\]|\[\S \S\]).+))?", hand.handText,re.DOTALL)
        hand.addStreets(m)

    def readCommunityCards(self, hand, street): # street has been matched by markStreets, so exists in this hand
        if street in ('FLOP','TURN','RIVER'):   # a list of streets which get dealt community cards (i.e. all but PREFLOP)
            #print "DEBUG readCommunityCards:", street, hand.streets.group(street)               
            m = self.re_Board.search(hand.streets[street])
            if street=='FLOP' and re.search(r'\[\S\S \S\S \S\S\]', hand.streets[street]):
                cards = m.group('CARDS').strip('[]').split(' ')
            else:
                m2 = self.re_Cards.finditer(m.group('CARDS'))
                cards = [c.group('CARD').replace(' ', '') for c in m2]
            hand.setCommunityCards(street, cards)

    def readAntes(self, hand):
        log.debug("reading antes")
        m = self.re_Antes.finditer(hand.handText)
        for player in m:
            #~ logging.debug("hand.addAnte(%s,%s)" %(player.group('PNAME'), player.group('ANTE')))
            hand.addAnte(player.group('PNAME'), self.clearMoneyString(player.group('ANTE')))
    
    def readBringIn(self, hand):
        pass
        
    def readBlinds(self, hand):
        try:
            m = self.re_PostSB.search(hand.handText)
            hand.addBlind(m.group('PNAME'), 'small blind', self.clearMoneyString(m.group('SB')))
        except: # no small blind
            hand.addBlind(None, None, None)
        for a in self.re_PostBB.finditer(hand.handText):
            hand.addBlind(a.group('PNAME'), 'big blind', self.clearMoneyString(a.group('BB')))
        for a in self.re_Post.finditer(hand.handText):
            bb = Decimal(self.clearMoneyString(a.group('BB')))
            subst = {'PLYR': "(?P<PNAME>" + re.escape(a.group('PNAME')) + ")", 'CUR': self.sym[hand.gametype['currency']], 'NUM' : u".,\d"}
            if not re.search(r"^%(PLYR)s posts %(CUR)s(?P<SB>[%(NUM)s]+) dead$" %  subst, hand.handText, re.MULTILINE):
                hand.addBlind(a.group('PNAME'), 'big blind', self.clearMoneyString(a.group('BB')))
            elif (bb==0):
                hand.addBlind(a.group('PNAME'), 'secondsb', str(Decimal(hand.gametype['bb'])/2))
            else:
                hand.addBlind(a.group('PNAME'), 'both', str(bb + bb/2))

    def readHoleCards(self, hand):
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
                    if re.search(r'\]\[', found.group('NEWCARDS')):
                        m2 = self.re_Cards.finditer(found.group('NEWCARDS'))
                        newcards = [c.group('CARD').replace(' ', '') for c in m2]
                    else:
                        newcards = found.group('NEWCARDS').strip('[]').split(' ')
                    hand.addHoleCards(street, hand.hero, closed=newcards, shown=False, mucked=False, dealt=True)

    def readAction(self, hand, street):
        m = self.re_Action.finditer(hand.streets[street])
        for action in m:
            acts = action.groupdict()
            #print "DEBUG: readAction: acts: %s street: %s" % (acts, street)
            if action.group('ATYPE') == ' folds':
                hand.addFold( street, action.group('PNAME'))
            elif action.group('ATYPE') == ' checks':
                hand.addCheck( street, action.group('PNAME'))
            elif action.group('ATYPE') == ' calls':
                # Amount in hand history is not cumulative
                # ie. Player3 calls 0.08
                #     Player5 raises to 0.16
                #     Player3 calls 0.16 (Doh! he's only calling 0.08
                # TODO: Going to have to write an addCallStoopid()
                #print "DEBUG: addCall( %s, %s, None)" %(street,action.group('PNAME'))
                hand.addCallTo( street, action.group('PNAME'), self.clearMoneyString(action.group('BET')))
            elif action.group('ATYPE') == ' raises':
                hand.addRaiseTo( street, action.group('PNAME'), self.clearMoneyString(action.group('BET')))
            elif action.group('ATYPE') == ' bets':
                hand.addBet( street, action.group('PNAME'), self.clearMoneyString(action.group('BET')))
            elif action.group('ATYPE') == ' discards':
                hand.addDiscard(street, action.group('PNAME'), action.group('BET'), action.group('DISCARDED'))
            elif action.group('ATYPE') == ' stands pat':
                hand.addStandsPat( street, action.group('PNAME'))
            else:
                print (_("DEBUG:") + _("Unimplemented %s: '%s' '%s'") % ("readAction", action.group('PNAME'), action.group('ATYPE')))


    def readShowdownActions(self, hand):
        # TODO: pick up mucks also??
        for shows in self.re_ShowdownAction.finditer(hand.handText):
            if re.search(r'\]\s?\[', shows.group('CARDS')):
                m2 = self.re_Cards.finditer(shows.group('CARDS'))
                cards = [c.group('CARD').replace(' ', '').replace('X', '') for c in m2]
            else:
                cards = shows.group('CARDS').strip('X[]').split(' ')
            #print "DEBUG: addShownCards(%s, %s)" %(cards, shows.group('PNAME'))
            hand.addShownCards(cards, shows.group('PNAME'))

    def readCollectPot(self,hand):
        for m in self.re_CollectPot.finditer(hand.handText):
            #print "DEBUG: addCollectPot(%s, %s)" %(m.group('PNAME'), m.group('POT'))
            hand.addCollectPot(player=m.group('PNAME'),pot=self.clearMoneyString(m.group('POT')))

    def readShownCards(self,hand):
        for m in self.re_ShownCards.finditer(hand.handText):
            if m.group('CARDS') is not None:
                if re.search(r'\]\s?\[', m.group('CARDS')):
                    m2 = self.re_Cards.finditer(m.group('CARDS'))
                    cards = [c.group('CARD').replace(' ', '').replace('X', '') for c in m2]
                else:
                    cards = m.group('CARDS').strip('X[]').split(' ')

                (shown, mucked) = (False, False)
                if m.group('SHOWED') == "showed": shown = True
                elif m.group('SHOWED') == "mucked": mucked = True
                
                hand.addShownCards(cards=cards, player=m.group('PNAME'), shown=shown, mucked=mucked)
