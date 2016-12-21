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
from HandHistoryConverter import *

# Class for converting Everleaf HH format.

class Everleaf(HandHistoryConverter):

    sitename = 'Everleaf'
    filetype = "text"
    codepage = ("utf-8", "cp1252")
    siteId   = 3 # Needs to match id entry in Sites database
    
    substitutions = {
                     'LEGAL_ISO' : "USD|EUR|GBP|CAD|FPP",       # legal ISO currency codes
                            'LS' : u"\$|\u20AC|\xe2\x82\xac|\x80|\u02c6|",  # legal currency symbols - Euro(cp1252, utf-8) #TODO change \x80 to \x20\x80, update all regexes accordingly
                        'PLAYERS': r'(?P<PNAME>.+?)',
                           'TAB' : u"-\u2013'\s\da-zA-Z#_()",     # legal characters for tablename
                           'NUM' : u".,\d",                     # legal characters in number format
                    }
    
    Lim_Blinds = {      '0.04': ('0.01', '0.02'),    '0.10': ('0.02', '0.05'),
                        '0.20': ('0.05', '0.10'),    '0.50': ('0.12', '0.25'),
                        '1.00': ('0.25', '0.50'),       '1': ('0.25', '0.50'),
                  }    
    
    # Static regexes
    re_Identify    = re.compile(u'\*{5}\sHand\shistory\sfor\sgame\s#\d+\s|Partouche\sPoker\s')
    re_SplitHands  = re.compile(r"\n\n\n+")
    re_TailSplitHands  = re.compile(r"(\n\n\n+)")
    re_GameInfo    = re.compile(ur"^(Blinds )? ?(?P<CURRENCY>[%(LS)s]?)(?P<SB>[%(NUM)s]+) ?/ ? ?[%(LS)s]?(?P<BB>[%(NUM)s]+) (?P<LIMIT>NL|PL|) ?(?P<GAME>(Hold\'em|Omaha|7\sCard\sStud))" % substitutions, re.MULTILINE)
    re_HandInfo    = re.compile(ur".*\n(.*#|.* partie )(?P<HID>[0-9]+).*(\n|\n\n)(Blinds )? ?(?P<CURRENCY>[%(LS)s])?(?P<SB>[%(NUM)s]+) ?/ ?(?:[%(LS)s])?(?P<BB>[%(NUM)s]+) (?P<GAMETYPE>.+?)(\s-\s(?P<MAX>\d+)\sMax)? - (?P<DATETIME>\d\d\d\d/\d\d/\d\d - \d\d:\d\d:\d\d)\nTable (?P<TABLE>.+$)" % substitutions, re.MULTILINE) 
    re_Button      = re.compile(ur"^Seat (?P<BUTTON>\d+) is the button$", re.MULTILINE)
    re_PlayerInfo  = re.compile(ur"""^Seat\s(?P<SEAT>[0-9]+):\s(?P<PNAME>.*)\s+
                                    \(
                                      \s+[%(LS)s]?\s?(?P<CASH>[%(NUM)s]+)
                                          (\s(USD|EURO|EUR|Chips|GEL)?(new\splayer|All-in)?)?
                                  \s?\)$
                                  """ % substitutions, re.MULTILINE|re.VERBOSE)
    re_Board       = re.compile(ur"\[ (?P<CARDS>.+) \]")
    re_TourneyInfoFromFilename = re.compile(ur".*TID_(?P<TOURNO>[0-9]+)-(?P<TABLE>[0-9]+).*\.txt")


    def compilePlayerRegexs(self, hand):
        players = set([player[1] for player in hand.players])
        if not players <= self.compiledPlayers: # x <= y means 'x is subset of y'
            # we need to recompile the player regexs.
            self.compiledPlayers = players
            
            self.re_PostSB          = re.compile(ur"^%(PLAYERS)s: posts small blind \[ ?[%(LS)s]? (?P<SB>[%(NUM)s]+)\s?.*\]$" % self.substitutions, re.MULTILINE)
            self.re_PostBB          = re.compile(ur"^%(PLAYERS)s: posts big blind \[ ?[%(LS)s]? (?P<BB>[%(NUM)s]+)\s?.*\]$" % self.substitutions, re.MULTILINE)
            self.re_PostBoth        = re.compile(ur"^%(PLAYERS)s: posts both blinds \[ ?[%(LS)s]? (?P<SBBB>[%(NUM)s]+)\s.*\]$" % self.substitutions, re.MULTILINE)
            self.re_Antes           = re.compile(ur"^%(PLAYERS)s: posts ante \[ ?[%(LS)s]? (?P<ANTE>[%(NUM)s]+)\s.*\]$" % self.substitutions, re.MULTILINE)
            self.re_BringIn         = re.compile(ur"^%(PLAYERS)s posts bring-in  ?[%(LS)s]?\s?(?P<BRINGIN>[%(NUM)s]+)\." % self.substitutions, re.MULTILINE)
            self.re_Completes       = re.compile(ur"^%(PLAYERS)s completes to  ?[%(LS)s]?\s?(?P<BET>[%(NUM)s]+)\." % self.substitutions, re.MULTILINE)
            self.re_HeroCards       = re.compile(ur"^Dealt to %(PLAYERS)s \[ (?P<CARDS>.*) \]$" % self.substitutions, re.MULTILINE)
            # ^%s(?P<ATYPE>: bets| checks| raises| calls| folds)(\s\[(?:\$| €|) (?P<BET>[.,\d]+) (USD|EURO|EUR|Chips)\])?
            self.re_Action          = re.compile(ur"^%(PLAYERS)s(?P<ATYPE>: bets| checks| raises| calls| folds)(\s\[(?: ?[%(LS)s]?) (?P<BET>[%(NUM)s]+)\s?(USD|EURO|EUR|Chips|GEL|)\])?" % self.substitutions, re.MULTILINE)
            self.re_ShowdownAction  = re.compile(ur"^%(PLAYERS)s (?P<SHOWED>shows|mucks) \[ (?P<CARDS>.*) \] (?P<STRING>.*)" % self.substitutions, re.MULTILINE)
            self.re_CollectPot      = re.compile(ur"^%(PLAYERS)s wins ( (high|low) )?\(?\s?[%(LS)s]?\s?(?P<POT>[%(NUM)s]+)\s?(USD|EURO|EUR|chips|GEL)?\)?" % self.substitutions, re.MULTILINE)

    def readSupportedGames(self):
        return [
                ["ring", "hold", "nl"],
                ["ring", "hold", "pl"],
                ["ring", "hold", "fl"],
                ["ring", "stud", "fl"],
                ["tour", "hold", "nl"],
                ["tour", "hold", "fl"],
                ["tour", "hold", "pl"]
               ]

    def determineGameType(self, handText):
        """return dict with keys/values:
    'type'       in ('ring', 'tour')
    'limitType'  in ('nl', 'cn', 'pl', 'cp', 'fl')
    'base'       in ('hold', 'stud', 'draw')
    'category'   in ('holdem', 'omahahi', omahahilo', 'razz', 'studhi', 'studhilo', 'fivedraw', '27_1draw', '27_3draw', 'badugi')
    'hilo'       in ('h','l','s')
    'smallBlind' int?
    'bigBlind'   int?
    'smallBet'
    'bigBet'
    'currency'  in ('USD', 'EUR', 'T$', <countrycode>)
or None if we fail to get the info """
        # Blinds $0.50/$1 PL Omaha - 2008/12/07 - 21:59:48
        # Blinds $0.05/$0.10 NL Hold'em - 2009/02/21 - 11:21:57
        # $0.25/$0.50 7 Card Stud - 2008/12/05 - 21:43:59

        # Tourney:
        # Everleaf Gaming Game #75065769
        # ***** Hand history for game #75065769 *****
        # Blinds 10/20 NL Hold'em - 2009/02/25 - 17:30:32
        # Table 2
        info = {'type':'ring'}
        
        m = self.re_GameInfo.search(handText)
        if not m:
            tmp = handText[0:200]
            log.error(_("EverleafToFpdb.determineGameType: '%s'") % tmp)
            raise FpdbParseError

        mg = m.groupdict()

        # translations from captured groups to our info strings
        limits = { 'NL':'nl', 'PL':'pl', '':'fl' }
        games = {              # base, category
                  "Hold'em" : ('hold','holdem'),
                    'Omaha' : ('hold','omahahi'),
                     'Razz' : ('stud','razz'),
              '7 Card Stud' : ('stud','studhi')
               }
        currencies = { u'ˆ':'EUR', u'€':'EUR', '$':'USD', '':'T$'}
        if 'LIMIT' in mg:
            info['limitType'] = limits[mg['LIMIT']]
        if 'GAME' in mg:
            (info['base'], info['category']) = games[mg['GAME']]
        if 'SB' in mg:
            info['sb'] = self.clearMoneyString(mg['SB'])
        if 'BB' in mg:
            info['bb'] = self.clearMoneyString(mg['BB'])
        if 'CURRENCY' in mg:
            info['currency'] = currencies[mg['CURRENCY']]
            if info['currency'] == 'T$':
                info['type'] = 'tour'
        # NB: SB, BB must be interpreted as blinds or bets depending on limit type.
        if info['limitType'] == 'fl' and info['bb'] is not None:
            if info['type'] == 'ring':
                try:
                    bb = self.clearMoneyString(mg['BB'].replace(',', ''))
                    info['sb'] = self.Lim_Blinds[bb][0]
                    info['bb'] = self.Lim_Blinds[bb][1]
                except KeyError:
                    tmp = handText[0:200]
                    log.error(_("EverleafToFpdb.determineGameType: Lim_Blinds has no lookup for '%s' - '%s'") % (mg['BB'], tmp))
                    raise FpdbParseError
            else:
                sb = self.clearMoneyString(mg['SB'].replace(',', ''))
                info['sb'] = str((Decimal(sb)/2).quantize(Decimal("0.01")))
                info['bb'] = str(Decimal(sb).quantize(Decimal("0.01")))
        return info


    def readHandInfo(self, hand):
        m = self.re_HandInfo.search(hand.handText)
        if(m == None):
            tmp = hand.handText[0:200]
            log.error(_("EverleafToFpdb.readHandInfo: '%s'") % tmp)
            raise FpdbParseError
        
        #log.debug("HID %s, Table %s" % (m.group('HID'),  m.group('TABLE')))
        hand.handid =  m.group('HID')
        hand.tablename = m.group('TABLE')
        if m.group('MAX'):
            hand.maxseats = int(m.group('MAX'))     # assume 4-max unless we have proof it's a larger/smaller game, since everleaf doesn't give seat max info
        
        currencies = { u'ˆ':'EUR', u'€':'EUR', '$':'USD', '':'T$'}
        mg = m.groupdict()
        if mg['CURRENCY'] is not None:
            hand.gametype['currency'] = currencies[mg['CURRENCY']]
        else:
            hand.gametype['currency'] = 'T$'

        t = self.re_TourneyInfoFromFilename.search(self.in_path)
        if t:
            tourno = t.group('TOURNO')
            hand.tourNo = tourno
            hand.tablename = t.group('TABLE')
            hand.buyin = 0
            hand.fee = 0
            hand.buyinCurrency = 'NA'
            #TODO we should fetch info including buyincurrency, buyin and fee from URL:
            #           https://www.poker4ever.com/tourney/%TOURNEY_NUMBER%

        # Believe Everleaf time is GMT/UTC, no transation necessary
        hand.startTime = datetime.datetime.strptime(m.group('DATETIME'), "%Y/%m/%d - %H:%M:%S")
        return

    def readPlayerStacks(self, hand):
        m = self.re_PlayerInfo.finditer(hand.handText)
        for a in m:
            seatnum = int(a.group('SEAT'))
            hand.addPlayer(seatnum, a.group('PNAME'), a.group('CASH'))
            if seatnum > 8:
                hand.maxseats = 10 # they added 8-seat games now
            elif seatnum > 6:
                hand.maxseats = 8 # everleaf currently does 2/6/10 games, so if seats > 6 are in use, it must be 10-max.
                # TODO: implement lookup list by table-name to determine maxes, then fall back to 6 default/10 here, if there's no entry in the list?
            elif seatnum > 4:
                hand.maxseats = 6 # they added 4-seat games too!


    def markStreets(self, hand):
        if hand.gametype['base'] == 'hold':
            m =  re.search(r"\*\* Dealing down cards \*\*(?P<PREFLOP>.+(?=\*\* Dealing Flop \*\*)|.+)"
                       r"(\*\* Dealing Flop \*\*(?P<FLOP> \[ \S\S, \S\S, \S\S \].+(?=\*\* Dealing Turn \*\*)|.+))?"
                       r"(\*\* Dealing Turn \*\*(?P<TURN> \[ \S\S \].+(?=\*\* Dealing River \*\*)|.+))?"
                       r"(\*\* Dealing River \*\*(?P<RIVER> \[ \S\S \].+))?", hand.handText,re.DOTALL)
        elif hand.gametype['base'] == 'stud':
            m =     re.search(r"(?P<ANTES>.+(?=\*\* Dealing down cards \*\*)|.+)"
                           r"(\*\* Dealing down cards \*\*(?P<THIRD>.+(?=\*\*\*\* dealing 4th street \*\*\*\*)|.+))?"
                           r"(\*\*\*\* dealing 4th street \*\*\*\*(?P<FOURTH>.+(?=\*\*\*\* dealing 5th street \*\*\*\*)|.+))?"
                           r"(\*\*\*\* dealing 5th street \*\*\*\*(?P<FIFTH>.+(?=\*\*\*\* dealing 6th street \*\*\*\*)|.+))?"
                           r"(\*\*\*\* dealing 6th street \*\*\*\*(?P<SIXTH>.+(?=\*\*\*\* dealing river \*\*\*\*)|.+))?"
                           r"(\*\*\*\* dealing river \*\*\*\*(?P<SEVENTH>.+))?", hand.handText,re.DOTALL)
        hand.addStreets(m)

    def readCommunityCards(self, hand, street): # street has been matched by markStreets, so exists in this hand
        # If this has been called, street is a street which gets dealt community cards by type hand
        # but it might be worth checking somehow.
#        if street in ('FLOP','TURN','RIVER'):   # a list of streets which get dealt community cards (i.e. all but PREFLOP)
        log.debug("readCommunityCards (%s)" % street)
        m = self.re_Board.search(hand.streets[street])
        cards = m.group('CARDS')
        cards = [card.strip() for card in cards.split(',')]
        hand.setCommunityCards(street=street, cards=cards)

    def readAntes(self, hand):
        log.debug(_("reading antes"))
        m = self.re_Antes.finditer(hand.handText)
        for player in m:
            log.debug("hand.addAnte(%s,%s)" %(player.group('PNAME'), player.group('ANTE')))
            hand.addAnte(player.group('PNAME'), self.clearMoneyString(player.group('ANTE')))

    def readBringIn(self, hand):
        m = self.re_BringIn.search(hand.handText,re.DOTALL)
        if m:
            log.debug("Player bringing in: %s for %s" %(m.group('PNAME'),  m.group('BRINGIN')))
            hand.addBringIn(m.group('PNAME'),  self.clearMoneyString(m.group('BRINGIN')))
        else:
            log.warning(_("No bringin found."))

    def readBlinds(self, hand):
        m = self.re_PostSB.search(hand.handText)
        if m is not None:
            hand.addBlind(m.group('PNAME'), 'small blind', self.clearMoneyString(m.group('SB')))
        else:
            log.debug(_("No small blind"))
            hand.addBlind(None, None, None)
        for a in self.re_PostBB.finditer(hand.handText):
            hand.addBlind(a.group('PNAME'), 'big blind', self.clearMoneyString(a.group('BB')))
        for a in self.re_PostBoth.finditer(hand.handText):
            hand.addBlind(a.group('PNAME'), 'both', self.clearMoneyString(a.group('SBBB')))

    def readButton(self, hand):
        hand.buttonpos = int(self.re_Button.search(hand.handText).group('BUTTON'))

    def readHoleCards(self, hand):
        m = self.re_HeroCards.search(hand.handText)
        if m:
            hand.hero = m.group('PNAME')
            # "2c, qh" -> ["2c","qc"]
            # Also works with Omaha hands.
            cards = m.group('CARDS')
            cards = [card.strip() for card in cards.split(',')]
#            hand.addHoleCards(cards, m.group('PNAME'))
            hand.addHoleCards('PREFLOP', hand.hero, closed=cards, shown=False, mucked=False, dealt=True)

        else:
            #Not involved in hand
            hand.involved = False


    def readStudPlayerCards(self, hand, street):
        log.warning(_("%s cannot read all stud/razz hands yet.") % hand.sitename)


    def readAction(self, hand, street):
        log.debug("readAction (%s)" % street)
        if street=='THIRD':
            m = self.re_Completes.finditer(hand.streets[street])
            for action in m:
                hand.addComplete( street, action.group('PNAME'), action.group('BET'))
        m = self.re_Action.finditer(hand.streets[street])
        for action in m:
            log.debug("%s %s" % (action.group('ATYPE'), action.groupdict()))
            if action.group('ATYPE') == ' folds':
                hand.addFold( street, action.group('PNAME'))
            elif action.group('ATYPE') == ' checks':
                hand.addCheck( street, action.group('PNAME'))
            elif action.group('ATYPE') == ' calls':
                hand.addCall( street, action.group('PNAME'), action.group('BET') )
            elif action.group('ATYPE') == ' raises':
                hand.addCallandRaise( street, action.group('PNAME'), action.group('BET') )
            elif action.group('ATYPE') == ': bets':
                hand.addBet( street, action.group('PNAME'), action.group('BET') )
            elif action.group('ATYPE') == ' complete to':
                hand.addComplete( street, action.group('PNAME'), action.group('BET'))
            else:
                log.debug(_("Unimplemented %s: '%s' '%s'") % ("readAction", action.group('PNAME'), action.group('ATYPE')))

    def readShowdownActions(self, hand):
        """Reads lines where holecards are reported in a showdown"""
        log.debug("readShowdownActions")
        for shows in self.re_ShowdownAction.finditer(hand.handText):
            cards = shows.group('CARDS')
            cards = cards.split(', ')
            log.debug("readShowdownActions %s %s" % (cards, shows.group('PNAME')))
            hand.addShownCards(cards, shows.group('PNAME'))


    def readCollectPot(self,hand):
        for m in self.re_CollectPot.finditer(hand.handText):
            hand.addCollectPot(player=m.group('PNAME'),pot=m.group('POT'))

    def readShownCards(self,hand):
        """Reads lines where hole & board cards are mixed to form a hand (summary lines)"""
        for m in self.re_ShowdownAction.finditer(hand.handText):
            if m.group('CARDS') is not None:
                cards = m.group('CARDS')
                cards = cards.split(', ')
                string = m.group('STRING')
                player = m.group('PNAME')

                (shown, mucked) = (False, False)
                if m.group('SHOWED') == "showed": shown = True
                elif m.group('SHOWED') == "mucked": mucked = True
                
                log.debug("readShownCards %s cards=%s" % (player, cards))
#                hand.addShownCards(cards=None, player=m.group('PNAME'), holeandboard=cards)
                hand.addShownCards(cards=cards, player=player, shown=shown, mucked=mucked, string=string)

    @staticmethod
    def getTableTitleRe(type, table_name=None, tournament = None, table_number=None):
        if tournament:
            return re.escape("%s - Tournament ID: %s - " % (table_number, tournament))
        return "%s (\(\d+\) )?-" % (re.escape(table_name))
