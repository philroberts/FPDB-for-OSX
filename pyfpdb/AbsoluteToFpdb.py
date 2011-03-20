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

#Note that this filter also supports UltimateBet, they are both owned by the same company and form the Cereus Network

import L10n
_ = L10n.get_translation()

# TODO: I have no idea if AP has multi-currency options, i just copied the regex out of Everleaf converter for the currency symbols.. weeeeee - Eric
import sys
import logging
from HandHistoryConverter import *

# Class for converting Absolute HH format.

class Absolute(HandHistoryConverter):

    # Class Variables
    sitename = "Absolute"
    filetype = "text"
    codepage = "cp1252"
    siteid   = 8
    HORSEHand = False

    # Static regexes
    re_SplitHands  = re.compile(r"\n\n+")
    re_TailSplitHands  = re.compile(r"(\nn\n+)")
    #Stage #1571362962: Holdem  No Limit $0.02 - 2009-08-05 15:24:06 (ET)
    #Table: TORONTO AVE (Real Money) Seat #6 is the dealer
    #Seat 6 - FETS63 ($0.75 in chips)
    #Board [10s 5d Kh Qh 8c]

    re_GameInfo = re.compile( ur"""
              ^Stage\s+\#C?(?P<HID>[0-9]+):?\s+
              (?:Tourney\ ID\ (?P<TRNY_ID>\d+)\s+)?
              (?P<GAME>Holdem|Seven\ Card\ Hi\/L|HORSE)\s+
              (?P<TRNY_TYPE>\(1\son\s1\)|Single\ Tournament|Multi\ Normal\ Tournament|)\s*
              (?P<LIMIT>No\ Limit|Pot\ Limit|Normal|)\s?
              (?P<CURRENCY>\$|\s€|)
              (?P<SB>[.,0-9]+)/?(?:\$|\s€|)(?P<BB>[.,0-9]+)?
              \s+
              ((?P<TTYPE>(Turbo))\s+)?-\s+
              ((?P<DATETIME>\d\d\d\d-\d\d-\d\d\ \d\d:\d\d:\d\d)(\.\d+)?)\s+
              (?: \( (?P<TZ>[A-Z]+) \)\s+ )?
              .*?
              (Table:\ (?P<TABLE>.*?)\ \(Real\ Money\))?
        """, re.MULTILINE|re.VERBOSE|re.DOTALL)

    re_HorseGameInfo = re.compile(
            ur"^Game Type: (?P<LIMIT>Limit) (?P<GAME>Holdem)",
            re.MULTILINE)

    re_HandInfo = re_GameInfo

    # on HORSE STUD games, the table name isn't in the hand info!
    re_RingInfoFromFilename = re.compile(ur".*IHH([0-9]+) (?P<TABLE>.*) -")
    re_TrnyInfoFromFilename = re.compile(
            ur"IHH\s?([0-9]+) (?P<TRNY_NAME>.*) "\
            ur"ID (?P<TRNY_ID>\d+)\s?(\((?P<TABLE>\d+)\))? .* "\
            ur"(?:\$|\s€|)(?P<BUYIN>[0-9.]+)\s*\+\s*(?:\$|\s€|)(?P<FEE>[0-9.]+)"
            )

    # TODO: that's not the right way to match for "dead" dealer is it?
    re_Button = re.compile(ur"Seat #(?P<BUTTON>[0-9]) is the ?[dead]* dealer$", re.MULTILINE)

    re_PlayerInfo = re.compile(
            ur"^Seat (?P<SEAT>[0-9]) - (?P<PNAME>.*) "\
            ur"\((?:\$| €|)(?P<CASH>[0-9]*[.,0-9]+) in chips\)",
            re.MULTILINE)

    re_Board = re.compile(ur"\[(?P<CARDS>[^\]]*)\]? *$", re.MULTILINE)


    def compilePlayerRegexs(self, hand):
        players = set([player[1] for player in hand.players])
        if not players <= self.compiledPlayers: # x <= y means 'x is subset of y'
            # we need to recompile the player regexs.
            self.compiledPlayers = players
            player_re = "(?P<PNAME>" + "|".join(map(re.escape, players)) + ")"
            logging.debug("player_re: "+ player_re)
            #(?P<CURRENCY>\$| €|)(?P<BB>[0-9]*[.0-9]+)
            self.re_PostSB          = re.compile(ur"^%s - Posts small blind (?:\$| €|)(?P<SB>[,.0-9]+)" % player_re, re.MULTILINE)
            self.re_PostBB          = re.compile(ur"^%s - Posts big blind (?:\$| €|)(?P<BB>[.,0-9]+)" % player_re, re.MULTILINE)
            # TODO: Absolute posting when coming in new: %s - Posts $0.02 .. should that be a new Post line? where do we need to add support for that? *confused*
            self.re_PostBoth        = re.compile(ur"^%s - Posts dead (?:\$| €|)(?P<SBBB>[,.0-9]+)" % player_re, re.MULTILINE)
            self.re_Action          = re.compile(ur"^%s - (?P<ATYPE>Bets |Raises |All-In |All-In\(Raise\) |Calls |Folds|Checks)?\$?(?P<BET>[,.0-9]+)?" % player_re, re.MULTILINE)
            self.re_ShowdownAction  = re.compile(ur"^%s - Shows \[(?P<CARDS>.*)\]" % player_re, re.MULTILINE)
            self.re_CollectPot      = re.compile(ur"^Seat [0-9]: %s(?: \(dealer\)|)(?: \(big blind\)| \(small blind\)|) (?:won|collected) Total \((?:\$| €|)(?P<POT>[,.0-9]+)\)" % player_re, re.MULTILINE)
            self.re_Antes           = re.compile(ur"^%s - Ante \[(?:\$| €|)(?P<ANTE>[,.0-9]+)" % player_re, re.MULTILINE)
            #self.re_BringIn         = re.compile(ur"^%s posts bring-in (?:\$| €|)(?P<BRINGIN>[.0-9]+)\." % player_re, re.MULTILINE)
            self.re_HeroCards       = re.compile(ur"^Dealt to %s \[(?P<CARDS>.*)\]" % player_re, re.MULTILINE)

    def readSupportedGames(self):
        return [["ring", "hold", "nl"],
                ["ring", "hold", "pl"],
                ["ring", "hold", "fl"],
                ["ring", "studhi", "fl"],
                ["ring", "omahahi", "pl"],
                ["tour", "hold", "nl"],
               ]

    def determineGameType(self, handText):
        """return dict with keys/values:
        'type'       in ('ring', 'tour')
        'limitType'  in ('nl', 'cn', 'pl', 'cp', 'fl')
        'base'       in ('hold', 'stud', 'draw')
        'category'   in ('holdem', 'omahahi', omahahilo', 'razz',
                         'studhi', 'studhilo', 'fivedraw', '27_1draw',
                         '27_3draw', 'badugi')
        'hilo'       in ('h','l','s')
        'smallBlind' int?
        'bigBlind'   int?
        'smallBet'
        'bigBet'
        'currency'  in ('USD', 'EUR', 'T$', <countrycode>)

        or None if we fail to get the info """
        info = {'type':'ring'}

        m = self.re_GameInfo.search(handText)
        if not m:
            tmp = handText[0:100]
            log.error(_("Unable to recognise gametype from: '%s'") % tmp)
            log.error(_("determineGameType: Raising FpdbParseError"))
            raise FpdbParseError(_("Unable to recognise gametype from: '%s'") % tmp)


        mg = m.groupdict()
        #print "DEBUG: mg: %s" % mg

        # translations from captured groups to our info strings
        limits = { 'No Limit':'nl', 'Pot Limit':'pl', 'Normal':'fl', 'Limit':'fl'}
        games = {              # base, category
                   "Holdem" : ('hold','holdem'),
                    'Omaha' : ('hold','omahahi'),
                     'Razz' : ('stud','razz'),
          'Seven Card Hi/L' : ('stud','studhilo'),
              '7 Card Stud' : ('stud','studhi')
               }
        currencies = { u' €':'EUR', '$':'USD', '':'T$' }
        if 'GAME' in mg and mg['GAME'] == "HORSE": # if we're a HORSE game, the game type is on the next line
            self.HORSEHand = True
            m = self.re_HorseGameInfo.search(handText)
            if not m:
                return None # it's a HORSE game and we don't understand the game type
            temp = m.groupdict()
            #print "AP HORSE processing"
            if 'GAME' not in temp or 'LIMIT' not in temp:
                return None # sort of understood it but not really
            #print "temp=", temp
            mg['GAME'] = temp['GAME']
            mg['LIMIT'] = temp['LIMIT']
        if 'GAME' in mg:
            (info['base'], info['category']) = games[mg['GAME']]
        if 'LIMIT' in mg:
            info['limitType'] = limits[mg['LIMIT']]
        if 'CURRENCY' in mg:
            info['currency'] = currencies[mg['CURRENCY']]
            if info['currency'] == 'T$':
                info['type'] = 'tour'
        if 'SB' in mg:
            mg['SB'] = mg['SB'].replace(',', '')
            info['sb'] = mg['SB']
        if 'BB' in mg:
            info['bb'] = mg['BB']
        # NB: SB, BB must be interpreted as blinds or bets depending on limit type.
        if info['bb'] is None:
            mg['SB'] = mg['SB'].replace(',', '')
            info['bb'] = mg['SB']
            info['sb'] = str(float(mg['SB']) * 0.5) # TODO: AP does provide Small BET for Limit .. I think? at least 1-on-1 limit they do.. sigh

        return info


    def readHandInfo(self, hand):
        is_trny = hand.gametype['type']=='tour'

        m = self.re_HandInfo.search(hand.handText)
        fname_re = self.re_TrnyInfoFromFilename if is_trny \
                   else self.re_RingInfoFromFilename
        fname_info = fname_re.search(self.in_path)

        #print "DEBUG: fname_info.groupdict(): %s" %(fname_info.groupdict())

        if m is None or fname_info is None:
            if m is None:
                tmp = hand.handText[0:100]
                logging.error(_("No match in readHandInfo: '%s'") % tmp)
                raise FpdbParseError("Absolute: " + _("No match in readHandInfo: '%s'") % tmp)
            elif fname_info is None:
                logging.error(_("File name didn't match re_*InfoFromFilename"))
                logging.error(_("File name: %s") % self.in_path)
                raise FpdbParseError("Absolute: " + _("Didn't match re_*InfoFromFilename: '%s'") % self.in_path)

        logging.debug("HID %s, Table %s" % (m.group('HID'),  m.group('TABLE')))
        hand.handid =  m.group('HID')
        if m.group('TABLE'):
            hand.tablename = m.group('TABLE')
        else:
            hand.tablename = fname_info.group('TABLE')

        hand.startTime = datetime.datetime.strptime(m.group('DATETIME'), "%Y-%m-%d %H:%M:%S")

        if is_trny:
            hand.fee = fname_info.group('FEE')
            hand.buyin = fname_info.group('BUYIN')
            hand.tourNo = m.group('TRNY_ID')
            hand.tourneyComment = fname_info.group('TRNY_NAME')

        # assume 6-max unless we have proof it's a larger/smaller game, 
        #since absolute doesn't give seat max info
        # TODO: (1-on-1) does have that info in the game type line
        hand.maxseats = 6

        if self.HORSEHand:
            hand.maxseats = 8  # todo : unless it's heads up!!?
        return

    def readPlayerStacks(self, hand):
        m = self.re_PlayerInfo.finditer(hand.handText)
        for a in m:
            seatnum = int(a.group('SEAT'))
            hand.addPlayer(seatnum, a.group('PNAME'), a.group('CASH'))
            if seatnum > 6:
                hand.maxseats = 9 # absolute does 2/4/6/9 games
                # TODO: implement lookup list by table-name to determine maxes, 
                # then fall back to 6 default/10 here, if there's no entry in the list?


    def markStreets(self, hand):
        # PREFLOP = ** Dealing down cards **
        # This re fails if,  say, river is missing; then we don't get the ** that starts the river.
        #m = re.search('(\*\* Dealing down cards \*\*\n)(?P<PREFLOP>.*?\n\*\*)?( Dealing Flop \*\* \[ (?P<FLOP1>\S\S), (?P<FLOP2>\S\S), (?P<FLOP3>\S\S) \])?(?P<FLOP>.*?\*\*)?( Dealing Turn \*\* \[ (?P<TURN1>\S\S) \])?(?P<TURN>.*?\*\*)?( Dealing River \*\* \[ (?P<RIVER1>\S\S) \])?(?P<RIVER>.*)', hand.handText,re.DOTALL)
        if hand.gametype['base'] == 'hold':
            m = re.search(r"\*\*\* POCKET CARDS \*\*\*(?P<PREFLOP>.+(?=\*\*\* FLOP \*\*\*)|.+)"
                    r"(\*\*\* FLOP \*\*\*(?P<FLOP>.+(?=\*\*\* TURN \*\*\*)|.+))?"
                    r"(\*\*\* TURN \*\*\*(?P<TURN>.+(?=\*\*\* RIVER \*\*\*)|.+))?"
                    r"(\*\*\* RIVER \*\*\*(?P<RIVER>.+))?", hand.handText, re.DOTALL)

        elif hand.gametype['base'] == 'stud': # TODO: Not implemented yet
            m =     re.search(r"(?P<ANTES>.+(?=\*\* Dealing down cards \*\*)|.+)"
                           r"(\*\* Dealing down cards \*\*(?P<THIRD>.+(?=\*\*\*\* dealing 4th street \*\*\*\*)|.+))?"
                           r"(\*\*\*\* dealing 4th street \*\*\*\*(?P<FOURTH>.+(?=\*\*\*\* dealing 5th street \*\*\*\*)|.+))?"
                           r"(\*\*\*\* dealing 5th street \*\*\*\*(?P<FIFTH>.+(?=\*\*\*\* dealing 6th street \*\*\*\*)|.+))?"
                           r"(\*\*\*\* dealing 6th street \*\*\*\*(?P<SIXTH>.+(?=\*\*\*\* dealing river \*\*\*\*)|.+))?"
                           r"(\*\*\*\* dealing river \*\*\*\*(?P<SEVENTH>.+))?", hand.handText,re.DOTALL)
        hand.addStreets(m)

    def readCommunityCards(self, hand, street):
        # street has been matched by markStreets, so exists in this hand
        # If this has been called, street is a street which gets dealt
        # community cards by type hand but it might be worth checking somehow.
        # if street in ('FLOP','TURN','RIVER'):
        #    a list of streets which get dealt community cards (i.e. all but PREFLOP)
        logging.debug("readCommunityCards (%s)" % street)
        m = self.re_Board.search(hand.streets[street])
        cards = m.group('CARDS')
        cards = [validCard(card) for card in cards.split(' ')]
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
            logging.debug(_("Player bringing in: %s for %s") % (m.group('PNAME'),  m.group('BRINGIN')))
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
            cards = [validCard(card) for card in cards.split(' ')]
#            hand.addHoleCards(cards, m.group('PNAME'))
            hand.addHoleCards('PREFLOP', hand.hero, closed=cards, shown=False, mucked=False, dealt=True)

        else:
            #Not involved in hand
            hand.involved = False

    def readStudPlayerCards(self, hand, street):
        # lol. see Plymouth.txt
        logging.warning(_("Absolute readStudPlayerCards is only a stub."))
        #~ if street in ('THIRD', 'FOURTH',  'FIFTH',  'SIXTH'):
            #~ hand.addPlayerCards(player = player.group('PNAME'), street = street,  closed = [],  open = [])


    def readAction(self, hand, street):
        logging.debug("readAction (%s)" % street)
        m = self.re_Action.finditer(hand.streets[street])
        for action in m:
            logging.debug("%s %s" % (action.group('ATYPE'), action.groupdict()))
            if action.group('ATYPE') == 'Raises ' or action.group('ATYPE') == 'All-In(Raise) ':
                bet = action.group('BET').replace(',', '')
                hand.addCallandRaise( street, action.group('PNAME'), bet)
            elif action.group('ATYPE') == 'Calls ':
                bet = action.group('BET').replace(',', '')
                hand.addCall( street, action.group('PNAME'), bet)
            elif action.group('ATYPE') == 'Bets ' or action.group('ATYPE') == 'All-In ':
                bet = action.group('BET').replace(',', '')
                hand.addBet( street, action.group('PNAME'), bet)
            elif action.group('ATYPE') == 'Folds':
                hand.addFold( street, action.group('PNAME'))
            elif action.group('ATYPE') == 'Checks':
                hand.addCheck( street, action.group('PNAME'))
            elif action.group('ATYPE') == ' complete to': # TODO: not supported yet ?
                bet = action.group('BET').replace(',', '')
                hand.addComplete( street, action.group('PNAME'), bet)
            else:
                logging.debug(_("Unimplemented readAction: '%s' '%s'") % (action.group('PNAME'),action.group('ATYPE')))


    def readShowdownActions(self, hand):
        """Reads lines where holecards are reported in a showdown"""
        logging.debug("readShowdownActions")
        for shows in self.re_ShowdownAction.finditer(hand.handText):
            cards = shows.group('CARDS')
            cards = [validCard(card) for card in cards.split(' ')]
            logging.debug("readShowdownActions %s %s" %(cards, shows.group('PNAME')))
            hand.addShownCards(cards, shows.group('PNAME'))


    def readCollectPot(self,hand):
        for m in self.re_CollectPot.finditer(hand.handText):
            pot = m.group('POT').replace(',','')
            hand.addCollectPot(player=m.group('PNAME'),pot=pot)

    def readShownCards(self,hand):
        """Reads lines where hole & board cards are mixed to form a hand (summary lines)"""
        for m in self.re_CollectPot.finditer(hand.handText):
            try:
                if m.group('CARDS') is not None:
                    cards = m.group('CARDS')
                    cards = [validCard(card) for card in cards.split(' ')]
                    player = m.group('PNAME')
                    logging.debug("readShownCards %s cards=%s" % (player, cards))
    #                hand.addShownCards(cards=None, player=m.group('PNAME'), holeandboard=cards)
                    hand.addShownCards(cards=cards, player=m.group('PNAME'))
            except IndexError:
                pass # there's no "PLAYER - Mucks" at AP that I can see

def validCard(card):
    card = card.strip()
    if card == '10s': card = 'Ts'
    if card == '10h': card = 'Th'
    if card == '10d': card = 'Td'
    if card == '10c': card = 'Tc'
    return card

if __name__ == "__main__":
    import Configuration
    import Database
    config =  Configuration.Config(None)
    # line below this is required
    # because config.site_ids (site_name to site_id map) is required 
    # and one is stored and db.
    db = Database.Database(config)

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

    e = Absolute(config, in_path = options.ipath, out_path = options.opath, follow = options.follow, autostart=True, sitename="Absolute")

