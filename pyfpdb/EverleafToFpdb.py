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
import logging
from HandHistoryConverter import *

# Class for converting Everleaf HH format.

class Everleaf(HandHistoryConverter):

    sitename = 'Everleaf'
    filetype = "text"
    codepage = "cp1252"
    siteId   = 3 # Needs to match id entry in Sites database

    # Static regexes
    re_SplitHands  = re.compile(r"\n\n\n+")
    re_TailSplitHands  = re.compile(r"(\n\n\n+)")
    re_GameInfo    = re.compile(ur"^(Blinds )?(?P<CURRENCY>[$€]?)(?P<SB>[.0-9]+)/[$€]?(?P<BB>[.0-9]+) (?P<LIMIT>NL|PL|) ?(?P<GAME>(Hold\'em|Omaha|7 Card Stud))", re.MULTILINE)
    #re.compile(ur"^(Blinds )?(?P<CURRENCY>\$| €|)(?P<SB>[.0-9]+)/(?:\$| €)?(?P<BB>[.0-9]+) (?P<LIMIT>NL|PL|) ?(?P<GAME>(Hold\'em|Omaha|7 Card Stud))", re.MULTILINE)
    re_HandInfo    = re.compile(ur".*#(?P<HID>[0-9]+)\n.*\n(Blinds )?(?P<CURRENCY>[$€])?(?P<SB>[.0-9]+)/(?:[$€])?(?P<BB>[.0-9]+) (?P<GAMETYPE>.*) - (?P<DATETIME>\d\d\d\d/\d\d/\d\d - \d\d:\d\d:\d\d)\nTable (?P<TABLE>.+$)", re.MULTILINE)
    re_Button      = re.compile(ur"^Seat (?P<BUTTON>\d+) is the button$", re.MULTILINE)
    re_PlayerInfo  = re.compile(ur"""^Seat\s(?P<SEAT>[0-9]+):\s(?P<PNAME>.*)\s+
                                    \(
                                      \s+[$€]?\s?(?P<CASH>[.0-9]+)
                                          (\s(USD|EURO|Chips)?(new\splayer|All-in)?)?
                                  \s?\)$
                                  """, re.MULTILINE|re.VERBOSE)
    re_Board       = re.compile(ur"\[ (?P<CARDS>.+) \]")
    re_TourneyInfoFromFilename = re.compile(ur".*TID_(?P<TOURNO>[0-9]+)-(?P<TABLE>[0-9]+)\.txt")


    def compilePlayerRegexs(self, hand):
        players = set([player[1] for player in hand.players])
        if not players <= self.compiledPlayers: # x <= y means 'x is subset of y'
            # we need to recompile the player regexs.
            self.compiledPlayers = players
            player_re = "(?P<PNAME>" + "|".join(map(re.escape, players)) + ")"
            logging.debug("player_re: "+ player_re)
            self.re_PostSB          = re.compile(ur"^%s: posts small blind \[[$€]? (?P<SB>[.0-9]+)\s.*\]$" % player_re, re.MULTILINE)
            self.re_PostBB          = re.compile(ur"^%s: posts big blind \[[$€]? (?P<BB>[.0-9]+)\s.*\]$" % player_re, re.MULTILINE)
            self.re_PostBoth        = re.compile(ur"^%s: posts both blinds \[[$€]? (?P<SBBB>[.0-9]+)\s.*\]$" % player_re, re.MULTILINE)
            self.re_Antes           = re.compile(ur"^%s: posts ante \[[$€]? (?P<ANTE>[.0-9]+)\s.*\]$" % player_re, re.MULTILINE)
            self.re_BringIn         = re.compile(ur"^%s posts bring-in [$€]? (?P<BRINGIN>[.0-9]+)\." % player_re, re.MULTILINE)
            self.re_HeroCards       = re.compile(ur"^Dealt to %s \[ (?P<CARDS>.*) \]$" % player_re, re.MULTILINE)
            # ^%s(?P<ATYPE>: bets| checks| raises| calls| folds)(\s\[(?:\$| €|) (?P<BET>[.,\d]+) (USD|EURO|Chips)\])?
            self.re_Action          = re.compile(ur"^%s(?P<ATYPE>: bets| checks| raises| calls| folds)(\s\[(?:[$€]?) (?P<BET>[.,\d]+)\s?(USD|EURO|Chips|)\])?" % player_re, re.MULTILINE)
            self.re_ShowdownAction  = re.compile(ur"^%s shows \[ (?P<CARDS>.*) \]" % player_re, re.MULTILINE)
            self.re_CollectPot      = re.compile(ur"^%s wins (?:[$€]?)\s?(?P<POT>[.\d]+) (USD|EURO|chips)(.*?\[ (?P<CARDS>.*?) \])?" % player_re, re.MULTILINE)
            self.re_SitsOut         = re.compile(ur"^%s sits out" % player_re, re.MULTILINE)

    def readSupportedGames(self):
        return [
                ["ring", "hold", "nl"],
                ["ring", "hold", "pl"],
                ["ring", "hold", "fl"],
                ["ring", "stud", "fl"],
                #["ring", "omahahi", "pl"],
                #["ring", "omahahilo", "pl"],
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
            tmp = handText[0:100]
            log.error(_("Unable to recognise gametype from: '%s'") % tmp)
            log.error("determineGameType: " + _("Raising FpdbParseError"))
            raise FpdbParseError(_("Unable to recognise gametype from: '%s'") % tmp)

        mg = m.groupdict()

        # translations from captured groups to our info strings
        limits = { 'NL':'nl', 'PL':'pl', '':'fl' }
        games = {              # base, category
                  "Hold'em" : ('hold','holdem'),
                    'Omaha' : ('hold','omahahi'),
                     'Razz' : ('stud','razz'),
              '7 Card Stud' : ('stud','studhi')
               }
        currencies = { u'€':'EUR', '$':'USD', '':'T$'}
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
            if info['currency'] == 'T$':
                info['type'] = 'tour'
        # NB: SB, BB must be interpreted as blinds or bets depending on limit type.

        return info


    def readHandInfo(self, hand):
        m = self.re_HandInfo.search(hand.handText)
        if(m == None):
            logging.info(_("No match in readHandInfo: '%s'") % hand.handText[0:100])
            logging.info(hand.handText)
            return None
        logging.debug("HID %s, Table %s" % (m.group('HID'),  m.group('TABLE')))
        hand.handid =  m.group('HID')
        hand.tablename = m.group('TABLE')
        hand.maxseats = 4     # assume 4-max unless we have proof it's a larger/smaller game, since everleaf doesn't give seat max info
        
        currencies = { u'€':'EUR', '$':'USD', '':'T$', None:'T$' }
        mg = m.groupdict()
        hand.gametype['currency'] = currencies[mg['CURRENCY']]


        t = self.re_TourneyInfoFromFilename.search(self.in_path)
        if t:
            tourno = t.group('TOURNO')
            hand.tourNo = tourno
            hand.tablename = t.group('TABLE')
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
        logging.debug("readCommunityCards (%s)" % street)
        m = self.re_Board.search(hand.streets[street])
        cards = m.group('CARDS')
        cards = [card.strip() for card in cards.split(',')]
        hand.setCommunityCards(street=street, cards=cards)

    def readAntes(self, hand):
        logging.debug(_("reading antes"))
        m = self.re_Antes.finditer(hand.handText)
        for player in m:
            logging.debug("hand.addAnte(%s,%s)" %(player.group('PNAME'), player.group('ANTE')))
            hand.addAnte(player.group('PNAME'), player.group('ANTE'))

    def readBringIn(self, hand):
        m = self.re_BringIn.search(hand.handText,re.DOTALL)
        if m:
            logging.debug("Player bringing in: %s for %s" %(m.group('PNAME'),  m.group('BRINGIN')))
            hand.addBringIn(m.group('PNAME'),  m.group('BRINGIN'))
        else:
            logging.warning(_("No bringin found."))

    def readBlinds(self, hand):
        m = self.re_PostSB.search(hand.handText)
        if m is not None:
            hand.addBlind(m.group('PNAME'), 'small blind', m.group('SB'))
        else:
            logging.debug(_("No small blind"))
            hand.addBlind(None, None, None)
        for a in self.re_PostBB.finditer(hand.handText):
            hand.addBlind(a.group('PNAME'), 'big blind', a.group('BB'))
        for a in self.re_PostBoth.finditer(hand.handText):
            hand.addBlind(a.group('PNAME'), 'both', a.group('SBBB'))

    def readButton(self, hand):
        hand.buttonpos = int(self.re_Button.search(hand.handText).group('BUTTON'))

    def readHeroCards(self, hand):
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
        # lol. see Plymouth.txt
        logging.warning(_("Everleaf readStudPlayerCards is only a stub."))
        #~ if street in ('THIRD', 'FOURTH',  'FIFTH',  'SIXTH'):
            #~ hand.addPlayerCards(player = player.group('PNAME'), street = street,  closed = [],  open = [])


    def readAction(self, hand, street):
        logging.debug("readAction (%s)" % street)
        m = self.re_Action.finditer(hand.streets[street])
        for action in m:
            logging.debug("%s %s" % (action.group('ATYPE'), action.groupdict()))
            if action.group('ATYPE') == ' raises':
                hand.addCallandRaise( street, action.group('PNAME'), action.group('BET') )
            elif action.group('ATYPE') == ' calls':
                hand.addCall( street, action.group('PNAME'), action.group('BET') )
            elif action.group('ATYPE') == ': bets':
                hand.addBet( street, action.group('PNAME'), action.group('BET') )
            elif action.group('ATYPE') == ' folds':
                hand.addFold( street, action.group('PNAME'))
            elif action.group('ATYPE') == ' checks':
                hand.addCheck( street, action.group('PNAME'))
            elif action.group('ATYPE') == ' complete to':
                hand.addComplete( street, action.group('PNAME'), action.group('BET'))
            else:
                logging.debug(_("Unimplemented readAction: '%s' '%s'") % (action.group('PNAME'), action.group('ATYPE')))


    def readShowdownActions(self, hand):
        """Reads lines where holecards are reported in a showdown"""
        logging.debug("readShowdownActions")
        for shows in self.re_ShowdownAction.finditer(hand.handText):
            cards = shows.group('CARDS')
            cards = cards.split(', ')
            logging.debug(_("readShowdownActions %s %s") % (cards, shows.group('PNAME')))
            hand.addShownCards(cards, shows.group('PNAME'))


    def readCollectPot(self,hand):
        for m in self.re_CollectPot.finditer(hand.handText):
            hand.addCollectPot(player=m.group('PNAME'),pot=m.group('POT'))

    def readShownCards(self,hand):
        """Reads lines where hole & board cards are mixed to form a hand (summary lines)"""
        for m in self.re_CollectPot.finditer(hand.handText):
            if m.group('CARDS') is not None:
                cards = m.group('CARDS')
                cards = cards.split(', ')
                player = m.group('PNAME')
                logging.debug("readShownCards %s cards=%s" % (player, cards))
#                hand.addShownCards(cards=None, player=m.group('PNAME'), holeandboard=cards)
                hand.addShownCards(cards=cards, player=m.group('PNAME'))

    @staticmethod
    def getTableTitleRe(type, table_name=None, tournament = None, table_number=None):
        if tournament:
            return "%s - Tournament ID: %s -" % (table_number, tournament)
        return "%s -" % (table_name)



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

    e = Everleaf(in_path = options.ipath, out_path = options.opath, follow = options.follow, autostart=True)
