#!/usr/bin/python

#Copyright 2008 Carl Gherardi
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU Affero General Public License as published by
#the Free Software Foundation, version 3 of the License.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU Affero General Public License
#along with this program. If not, see <http://www.gnu.org/licenses/>.
#In the "official" distribution you can find the license in
#agpl-3.0.txt in the docs folder of the package.

import Configuration
import FpdbRegex
import re
import sys
import traceback
import os
import os.path
import xml.dom.minidom
import codecs
from decimal import Decimal
import operator
from xml.dom.minidom import Node
from pokereval import PokerEval
from time import time
#from pokerengine.pokercards import *
# provides letter2name{}, letter2names{}, visible_card(), not_visible_card(), is_visible(), card_value(), class PokerCards
# but it's probably not installed so here are the ones we may want:
letter2name = {
    'A': 'Ace',
    'K': 'King',
    'Q': 'Queen',
    'J': 'Jack',
    'T': 'Ten',
    '9': 'Nine',
    '8': 'Eight',
    '7': 'Seven',
    '6': 'Six',
    '5': 'Five',
    '4': 'Four',
    '3': 'Trey',
    '2': 'Deuce'
    }

letter2names = {
    'A': 'Aces',
    'K': 'Kings',
    'Q': 'Queens',
    'J': 'Jacks',
    'T': 'Tens',
    '9': 'Nines',
    '8': 'Eights',
    '7': 'Sevens',
    '6': 'Sixes',
    '5': 'Fives',
    '4': 'Fours',
    '3': 'Treys',
    '2': 'Deuces'
    }

class HandHistoryConverter:
    eval = PokerEval()
    def __init__(self, config, file, sitename):
        print "HandHistory init called"
        self.c         = config
        self.sitename  = sitename
        self.obs       = ""             # One big string
        self.filetype  = "text"
        self.codepage  = "utf8"
        self.doc       = None     # For XML based HH files
        self.file      = file
        self.hhbase    = self.c.get_import_parameters().get("hhArchiveBase")
        self.hhbase    = os.path.expanduser(self.hhbase)
        self.hhdir     = os.path.join(self.hhbase,sitename)
        self.gametype  = []
#		self.ofile     = os.path.join(self.hhdir,file)
        self.rexx      = FpdbRegex.FpdbRegex()

    def __str__(self):
        tmp = "HandHistoryConverter: '%s'\n" % (self.sitename)
        tmp = tmp + "\thhbase:     '%s'\n" % (self.hhbase)
        tmp = tmp + "\thhdir:      '%s'\n" % (self.hhdir)
        tmp = tmp + "\tfiletype:   '%s'\n" % (self.filetype)
        tmp = tmp + "\tinfile:     '%s'\n" % (self.file)
#		tmp = tmp + "\toutfile:    '%s'\n" % (self.ofile)
#		tmp = tmp + "\tgametype:   '%s'\n" % (self.gametype[0])
#		tmp = tmp + "\tgamebase:   '%s'\n" % (self.gametype[1])
#		tmp = tmp + "\tlimit:      '%s'\n" % (self.gametype[2])
#		tmp = tmp + "\tsb/bb:      '%s/%s'\n" % (self.gametype[3], self.gametype[4])
        return tmp

    def processFile(self):
        starttime = time()
        if not self.sanityCheck():
            print "Cowardly refusing to continue after failed sanity check"
            return
        self.readFile(self.file)
        self.gametype = self.determineGameType()
        self.hands = self.splitFileIntoHands()
        for hand in self.hands:
            print "\nInput:\n"+hand.string
            self.readHandInfo(hand)
            self.readPlayerStacks(hand)
            self.markStreets(hand)
            self.readBlinds(hand)
            self.readHeroCards(hand) # want to generalise to draw games
            self.readCommunityCards(hand) # read community cards
            self.readShowdownActions(hand)
            # Read action (Note: no guarantee this is in hand order.
            for street in hand.streets.groupdict():
                if hand.streets.group(street) is not None:
                    self.readAction(hand, street)

            self.readCollectPot(hand)

            # finalise it (total the pot)
            hand.totalPot()
            self.getRake(hand)

            hand.printHand()
            #if(hand.involved == True):
                #self.writeHand("output file", hand)
                #hand.printHand()
            #else:
                #pass #Don't write out observed hands

        endtime = time()
        print "Processed %d hands in %d seconds" % (len(self.hands), endtime-starttime)

    #####
    # These functions are parse actions that may be overridden by the inheriting class
    #
    
    def readSupportedGames(self): abstract

    # should return a list
    #   type  base limit
    # [ ring, hold, nl   , sb, bb ]
    # Valid types specified in docs/tabledesign.html in Gametypes
    def determineGameType(self): abstract

    # Read any of:
    # HID		HandID
    # TABLE		Table name
    # SB 		small blind
    # BB		big blind
    # GAMETYPE	gametype
    # YEAR MON DAY HR MIN SEC 	datetime
    # BUTTON	button seat number
    def readHandInfo(self, hand): abstract

    # Needs to return a list of lists in the format
    # [['seat#', 'player1name', 'stacksize'] ['seat#', 'player2name', 'stacksize'] [...]]
    def readPlayerStacks(self, hand): abstract

    # Needs to return a MatchObject with group names identifying the streets into the Hand object
    # that is, pulls the chunks of preflop, flop, turn and river text into hand.streets MatchObject.
    def markStreets(self, hand): abstract

    #Needs to return a list in the format
    # ['player1name', 'player2name', ...] where player1name is the sb and player2name is bb, 
    # addtional players are assumed to post a bb oop
    def readBlinds(self, hand): abstract
    def readHeroCards(self, hand): abstract
    def readAction(self, hand, street): abstract
    def readCollectPot(self, hand): abstract
    
    # Some sites don't report the rake. This will be called at the end of the hand after the pot total has been calculated
    # so that an inheriting class can calculate it for the specific site if need be.
    def getRake(self, hand): abstract
    
    def sanityCheck(self):
        sane = True
        base_w = False
        #Check if hhbase exists and is writable
        #Note: Will not try to create the base HH directory
        if not (os.access(self.hhbase, os.W_OK) and os.path.isdir(self.hhbase)):
            print "HH Sanity Check: Directory hhbase '" + self.hhbase + "' doesn't exist or is not writable"
        else:
            #Check if hhdir exists and is writable
            if not os.path.isdir(self.hhdir):
                # In first pass, dir may not exist. Attempt to create dir
                print "Creating directory: '%s'" % (self.hhdir)
                os.mkdir(self.hhdir)
                sane = True
            elif os.access(self.hhdir, os.W_OK):
                sane = True
            else:
                print "HH Sanity Check: Directory hhdir '" + self.hhdir + "' or its parent directory are not writable"

        return sane

    # Functions not necessary to implement in sub class
    def setFileType(self, filetype = "text", codepage='utf8'):
        self.filetype = filetype
        self.codepage = codepage

    def splitFileIntoHands(self):
        hands = []
        self.obs.strip()
        list = self.rexx.split_hand_re.split(self.obs)
        list.pop() #Last entry is empty
        for l in list:
#			print "'" + l + "'"
            hands = hands + [Hand(self.sitename, self.gametype, l)]
        return hands

    def readFile(self, filename):
        """Read file"""
        print "Reading file: '%s'" %(filename)
        if(self.filetype == "text"):
            infile=codecs.open(filename, "rU", self.codepage)
            self.obs = infile.read()
            infile.close()
        elif(self.filetype == "xml"):
            try:
                doc = xml.dom.minidom.parse(filename)
                self.doc = doc
            except:
                traceback.print_exc(file=sys.stderr)


#takes a poker float (including , for thousand seperator and converts it to an int
    def float2int (self, string):
        pos=string.find(",")
        if (pos!=-1): #remove , the thousand seperator
            string=string[0:pos]+string[pos+1:]

        pos=string.find(".")
        if (pos!=-1): #remove decimal point
            string=string[0:pos]+string[pos+1:]

        result = int(string)
        if pos==-1: #no decimal point - was in full dollars - need to multiply with 100
            result*=100
        return result
#end def float2int

class Hand:
#    def __init__(self, sitename, gametype, sb, bb, string):

    UPS = {'a':'A', 't':'T', 'j':'J', 'q':'Q', 'k':'K'}
    def __init__(self, sitename, gametype, string):
        self.sitename = sitename
        self.gametype = gametype
        self.string = string

        self.streetList = ['BLINDS','PREFLOP','FLOP','TURN','RIVER'] # a list of the observed street names in order

        self.handid = 0
        self.sb = gametype[3]
        self.bb = gametype[4]
        self.tablename = "Slartibartfast"
        self.hero = "Hiro"
        self.maxseats = 10
        self.counted_seats = 0
        self.buttonpos = 0
        self.seating = []
        self.players = []
        self.posted = []
        self.involved = True


        #
        # Collections indexed by street names
        #

        # A MatchObject using a groupnames to identify streets.
        # filled by markStreets()
        self.streets = None

        # dict from street names to lists of tuples, such as
        # [['mct','bets','$10'],['mika','folds'],['carlg','raises','$20']]
        # actually they're clearly lists but they probably should be tuples.
        self.actions = {}

        # dict from street names to community cards
        self.board = {}


        #
        # Collections indexed by player names
        #

        # dict from player names to lists of hole cards
        self.holecards = {}

        # dict from player names to amounts collected
        self.collected = {}

        # Sets of players
        self.shown = set()
        self.folded = set()

        self.action = []
        self.totalpot = None
        self.rake = None

        self.bets = {}
        self.lastBet = {}
        for street in self.streetList:
            self.bets[street] = {}
            self.lastBet[street] = 0

    def addPlayer(self, seat, name, chips):
        """\
Adds a player to the hand, and initialises data structures indexed by player.
seat    (int) indicating the seat
name    (string) player name
chips   (string) the chips the player has at the start of the hand (can be None)
If a player has None chips he won't be added."""
        if chips is not None:
            self.players.append([seat, name, chips])
            self.holecards[name] = []
            for street in self.streetList:
                self.bets[street][name] = []


    def addHoleCards(self, cards, player):
        """\
Assigns observed holecards to a player.
cards   list of card bigrams e.g. ['2h','jc']
player  (string) name of player
hand    
Note, will automatically uppercase the rank letter.
"""
        try:
            self.checkPlayerExists(player)
            self.holecards[player] = set([self.card(c) for c in cards])
        except FpdbParseError, e:
            print "Tried to add holecards for unknown player: %s" % (player,)

    def addShownCards(self, cards, player, holeandboard=None):
        """\
For when a player shows cards for any reason (for showdown or out of choice).
"""
        if cards is not None:
            self.shown.add(player)
            self.addHoleCards(cards,player)
        elif holeandboard is not None:
            board = set([c for s in self.board.values() for c in s])
            #print board
            #print holeandboard
            #print holeandboard.difference(board)
            self.addHoleCards(holeandboard.difference(board),player)


    def checkPlayerExists(self,player):
        if player not in [p[1] for p in self.players]:
            raise FpdbParseError

    def discardHoleCards(self, cards, player):
        try:
            self.checkPlayerExists(player)
            for card in cards:
                self.holecards[player].remove(card)
        except FpdbParseError, e:
            pass
        except ValueError:
            print "tried to discard a card %s didn't have" % (player,)

    def setCommunityCards(self, street, cards):
        self.board[street] = [self.card(c) for c in cards]

    def card(self,c):
        """upper case the ranks but not suits, 'atjqk' => 'ATJQK'"""
        for k,v in self.UPS.items():
            c = c.replace(k,v)
        return c

    def addBlind(self, player, amount):
        # if player is None, it's a missing small blind.
        if player is not None:
            self.bets['PREFLOP'][player].append(Decimal(amount))
        self.lastBet['PREFLOP'] = Decimal(amount)
        self.posted += [player]


    def addCall(self, street, player=None, amount=None):
        # Potentially calculate the amount of the call if not supplied
        # corner cases include if player would be all in
        if amount is not None:
            self.bets[street][player].append(Decimal(amount))
            #self.lastBet[street] = Decimal(amount)
            self.actions[street] += [[player, 'calls', amount]]
        
    def addRaiseTo(self, street, player, amountTo):
        """\
Add a raise on [street] by [player] to [amountTo]
"""
        #Given only the amount raised to, the amount of the raise can be calculated by
        # working out how much this player has already in the pot 
        #   (which is the sum of self.bets[street][player])
        # and how much he needs to call to match the previous player 
        #   (which is tracked by self.lastBet)
        self.checkPlayerExists(player)
        committedThisStreet = reduce(operator.add, self.bets[street][player], 0)
        amountToCall = self.lastBet[street] - committedThisStreet
        self.lastBet[street] = Decimal(amountTo)
        amountBy = Decimal(amountTo) - amountToCall
        self.bets[street][player].append(amountBy+amountToCall)
        self.actions[street] += [[player, 'raises', amountBy, amountTo]]
        
    def addBet(self, street, player, amount):
        self.checkPlayerExists(player)
        self.bets[street][player].append(Decimal(amount))
        self.actions[street] += [[player, 'bets', amount]]

    def addFold(self, street, player):
        self.checkPlayerExists(player)
        self.folded.add(player)
        self.actions[street] += [[player, 'folds']]

    def addCheck(self, street, player):
        self.checkPlayerExists(player)
        self.actions[street] += [[player, 'checks']]

    def addCollectPot(self,player, pot):
        self.checkPlayerExists(player)
        if player not in self.collected:
            self.collected[player] = pot
        else:
            # possibly lines like "p collected $ from pot" appear during the showdown
            # but they are usually unique in the summary, so it's best to try to get them from there.
            print "%s collected pot more than once; avoidable by reading winnings only from summary lines?"


    def totalPot(self):
        """If all bets and blinds have been added, totals up the total pot size
Known bug: doesn't take into account side pots"""
        if self.totalpot is None:
            self.totalpot = 0

            # player names: 
            # print [x[1] for x in self.players]
            for player in [x[1] for x in self.players]:
                for street in self.streetList:
                    #print street, self.bets[street][player]
                    self.totalpot += reduce(operator.add, self.bets[street][player], 0)

    def getGameTypeAsString(self):
        """\
Map the tuple self.gametype onto the pokerstars string describing it
"""
        # currently it appears to be something like ["ring", "hold", "nl", sb, bb]:
        return "Hold'em No Limit"

    def printHand(self):
        # PokerStars format.
        print "\n### Pseudo stars format ###"
        print "%s Game #%s: %s ($%s/$%s) - %s" %(self.sitename, self.handid, self.getGameTypeAsString(), self.sb, self.bb, self.starttime)
        print "Table '%s' %d-max Seat #%s is the button" %(self.tablename, self.maxseats, self.buttonpos)
        for player in self.players:
            print "Seat %s: %s ($%s)" %(player[0], player[1], player[2])

        if(self.posted[0] is None):
            print "No small blind posted"
        else:
            print "%s: posts small blind $%s" %(self.posted[0], self.sb)

        #May be more than 1 bb posting
        for a in self.posted[1:]:
            print "%s: posts big blind $%s" %(self.posted[1], self.bb)

        # What about big & small blinds?

        print "*** HOLE CARDS ***"
        if self.involved:
            print "Dealt to %s [%s]" %(self.hero , " ".join(self.holecards[self.hero]))

        if 'PREFLOP' in self.actions:
            for act in self.actions['PREFLOP']:
                self.printActionLine(act)

        if 'FLOP' in self.actions:
            print "*** FLOP *** [%s]" %( " ".join(self.board['Flop']))
            for act in self.actions['FLOP']:
                self.printActionLine(act)

        if 'TURN' in self.actions:
            print "*** TURN *** [%s] [%s]" %( " ".join(self.board['Flop']), " ".join(self.board['Turn']))
            for act in self.actions['TURN']:
                self.printActionLine(act)

        if 'RIVER' in self.actions:
            print "*** RIVER *** [%s] [%s]" %(" ".join(self.board['Flop']+self.board['Turn']), " ".join(self.board['River']) )
            for act in self.actions['RIVER']:
                self.printActionLine(act)


        #Some sites don't have a showdown section so we have to figure out if there should be one
        # The logic for a showdown is: at the end of river action there are at least two players in the hand
        # we probably don't need a showdown section in pseudo stars format for our filtering purposes
        if 'SHOWDOWN' in self.actions:
            print "*** SHOW DOWN ***"
            print "what do they show"

        print "*** SUMMARY ***"
        print "Total pot $%s | Rake $%.2f)" % (self.totalpot, self.rake) # TODO side pots
        board = []
        for s in self.board.values():
            board += s
        if board:   # sometimes hand ends preflop without a board
            print "Board [%s]" % (" ".join(board))


        for player in self.players:
            seatnum = player[0]
            name = player[1]
            if name in self.collected and self.holecards[name]:
                print "Seat %d: %s showed [%s] and won ($%s)" % (seatnum, name, " ".join(self.holecards[name]), self.collected[name])
            elif name in self.collected:
                print "Seat %d: %s collected ($%s)" % (seatnum, name, self.collected[name])
            elif player[1] in self.shown:
                print "Seat %d: %s showed [%s]" % (seatnum, name, " ".join(self.holecards[name]))
            elif player[1] in self.folded:
                print "Seat %d: %s folded" % (seatnum, name)
            else:
                print "Seat %d: %s mucked" % (seatnum, name)

        print
            # TODO:
            # logic for side pots
            # logic for which players get to showdown
            # I'm just not sure we need to do this so heavily.. and if we do, it's probably better to use pokerlib
            #if self.holecards[player[1]]: # empty list default is false
                #hole = self.holecards[player[1]]
                ##board = []
                ##for s in self.board.values():
                    ##board += s
                ##playerhand = self.bestHand('hi', board+hole)
                ##print "Seat %d: %s showed %s and won/lost with %s" % (player[0], player[1], hole, playerhand)
                #print "Seat %d: %s showed %s" % (player[0], player[1], hole)
            #else:
                #print "Seat %d: %s mucked or folded" % (player[0], player[1])


    def printActionLine(self, act):
        if act[1] == 'folds' or act[1] == 'checks':
            print "%s: %s " %(act[0], act[1])
        if act[1] == 'calls':
            print "%s: %s $%s" %(act[0], act[1], act[2])
        if act[1] == 'bets':
            print "%s: %s $%s" %(act[0], act[1], act[2])
        if act[1] == 'raises':
            print "%s: %s $%s to $%s" %(act[0], act[1], act[2], act[3])

    # going to use pokereval to figure out hands at some point.
    # these functions are copied from pokergame.py
    def bestHand(self, side, cards):
        return HandHistoryConverter.eval.best('hi', cards, [])

    # from pokergame.py
    def bestHandValue(self, side, serial):
        (value, cards) = self.bestHand(side, serial)
        return value

    # from pokergame.py
    # got rid of the _ for internationalisation
    def readableHandValueLong(self, side, value, cards):
        if value == "NoPair":
            if side == "low":
                if cards[0][0] == '5':
                    return ("The wheel")
                else:
                    return join(map(lambda card: card[0], cards), ", ")
            else:
                return ("High card %(card)s") % { 'card' : (letter2name[cards[0][0]]) }
        elif value == "OnePair":
            return ("A pair of %(card)s") % { 'card' : (letter2names[cards[0][0]]) } + (", %(card)s kicker") % { 'card' : (letter2name[cards[2][0]]) }
        elif value == "TwoPair":
            return ("Two pairs %(card1)s and %(card2)s") % { 'card1' : (letter2names[cards[0][0]]), 'card2' : _(letter2names[cards[2][0]]) } + (", %(card)s kicker") % { 'card' : (letter2name[cards[4][0]]) }
        elif value == "Trips":
            return ("Three of a kind %(card)s") % { 'card' : (letter2names[cards[0][0]]) } + (", %(card)s kicker") % { 'card' : (letter2name[cards[3][0]]) }
        elif value == "Straight":
            return ("Straight %(card1)s to %(card2)s") % { 'card1' : (letter2name[cards[0][0]]), 'card2' : (letter2name[cards[4][0]]) }
        elif value == "Flush":
            return ("Flush %(card)s high") % { 'card' : (letter2name[cards[0][0]]) }
        elif value == "FlHouse":
            return ("%(card1)ss full of %(card2)ss") % { 'card1' : (letter2name[cards[0][0]]), 'card2' : (letter2name[cards[3][0]]) }
        elif value == "Quads":
            return _("Four of a kind %(card)s") % { 'card' : (letter2names[cards[0][0]]) } + (", %(card)s kicker") % { 'card' : (letter2name[cards[4][0]]) }
        elif value == "StFlush":
            if letter2name[cards[0][0]] == 'Ace':
                return ("Royal flush")
            else:
                return ("Straight flush %(card)s high") % { 'card' : (letter2name[cards[0][0]]) }
        return value
        
        
class FpdbParseError(Exception): pass