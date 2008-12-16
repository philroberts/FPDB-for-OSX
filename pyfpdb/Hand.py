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
import Hand
import re
import sys
import traceback
import os
import os.path
import xml.dom.minidom
import codecs
from decimal import Decimal
import operator
from time import time

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
        self.totalcollected = None

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
            self.holecards[name] = set()
            for street in self.streetList:
                self.bets[street][name] = []


    def addStreets(self, match):
        # go through m and initialise actions to empty list for each street.
        if match is not None:
            self.streets = match
            for street in match.groupdict():
                if match.group(street) is not None:
                    self.actions[street] = []

        else:
            print "empty markStreets match" # better to raise exception and put process hand in a try block

    def addHoleCards(self, cards, player):
        """\
Assigns observed holecards to a player.
cards   set of card bigrams e.g. set(['2h','Jc'])     
player  (string) name of player
"""
        try:
            self.checkPlayerExists(player)
            cards = set([self.card(c) for c in cards])
            self.holecards[player].update(cards)
        except FpdbParseError, e:
            print "Tried to add holecards for unknown player: %s" % (player,)

    def addShownCards(self, cards, player, holeandboard=None):
        """\
For when a player shows cards for any reason (for showdown or out of choice).
Card ranks will be uppercased
"""
        if cards is not None:
            self.shown.add(player)
            self.addHoleCards(cards,player)
        elif holeandboard is not None:
            holeandboard = set([self.card(c) for c in holeandboard])
            board = set([c for s in self.board.values() for c in s])
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

    def addBlind(self, player, blindtype, amount):
        # if player is None, it's a missing small blind.
        if player is not None:
            self.bets['PREFLOP'][player].append(Decimal(amount))
            self.actions['PREFLOP'] += [(player, 'posts', blindtype, amount)]
            if blindtype == 'big blind':
                self.lastBet['PREFLOP'] = Decimal(amount)            
            elif blindtype == 'small & big blinds':
                # extra small blind is 'dead'
                self.lastBet['PREFLOP'] = Decimal(self.bb)
        self.posted += [player]


    def addCall(self, street, player=None, amount=None):
        # Potentially calculate the amount of the call if not supplied
        # corner cases include if player would be all in
        if amount is not None:
            self.bets[street][player].append(Decimal(amount))
            #self.lastBet[street] = Decimal(amount)
            self.actions[street] += [(player, 'calls', amount)]
        
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
        self.actions[street] += [(player, 'raises', amountBy, amountTo, amountToCall)]
        
    def addBet(self, street, player, amount):
        self.checkPlayerExists(player)
        self.bets[street][player].append(Decimal(amount))
        self.actions[street] += [(player, 'bets', amount)]
        self.lastBet[street] = Decimal(amount)

    def addFold(self, street, player):
        self.checkPlayerExists(player)
        self.folded.add(player)
        self.actions[street] += [(player, 'folds')]

    def addCheck(self, street, player):
        self.checkPlayerExists(player)
        self.actions[street] += [(player, 'checks')]

    def addCollectPot(self,player, pot):
        self.checkPlayerExists(player)
        if player not in self.collected:
            self.collected[player] = pot
        else:
            print "[WARNING] %s collected pot more than once; avoidable by reading winnings only from summary lines?"


    def totalPot(self):
        """If all bets and blinds have been added, totals up the total pot size"""
        if self.totalpot is None:
            self.totalpot = 0

            # player names: 
            # print [x[1] for x in self.players]
            for player in [x[1] for x in self.players]:
                for street in self.streetList:
                    #print street, self.bets[street][player]
                    self.totalpot += reduce(operator.add, self.bets[street][player], 0)

            print "conventional totalpot:", self.totalpot
            self.totalpot = 0

            print self.actions
            for street in self.actions:
                uncalled = 0
                calls = [0]
                for act in self.actions[street]:
                    if act[1] == 'bets': # [name, 'bets', amount]
                        self.totalpot += Decimal(act[2])
                        uncalled = Decimal(act[2])  # only the last bet or raise can be uncalled
                        calls = [0]
                        print "uncalled: ", uncalled
                    elif act[1] == 'raises': # [name, 'raises', amountby, amountto, amountcalled]
                        print "calls %s and raises %s to %s" % (act[4],act[2],act[3])
                        self.totalpot += Decimal(act[2]) + Decimal(act[4])
                        calls = [0]
                        uncalled = Decimal(act[2])
                        print "uncalled: ", uncalled
                    elif act[1] == 'calls': # [name, 'calls', amount]
                        self.totalpot += Decimal(act[2])
                        calls = calls + [Decimal(act[2])]
                        print "calls:", calls
                    if act[1] == ('posts'):
                        self.totalpot += Decimal(act[3])
                        uncalled = Decimal(act[3])
                if uncalled > 0 and max(calls+[0]) < uncalled:
                    
                    print "returning some bet, calls:", calls
                    print "returned: %.2f from %.2f" %  ((uncalled - max(calls)), self.totalpot,)
                    self.totalpot -= (uncalled - max(calls))
            print "new totalpot:", self.totalpot

        if self.totalcollected is None:
            self.totalcollected = 0;
            for amount in self.collected.values():
                self.totalcollected += Decimal(amount)




    def getGameTypeAsString(self):
        """\
Map the tuple self.gametype onto the pokerstars string describing it
"""
        # currently it appears to be something like ["ring", "hold", "nl", sb, bb]:
        gs = {"hold"       : "Hold'em",
              "omahahi"    : "FIXME",
              "omahahilo"  : "FIXME",
              "razz"       : "Razz",
              "studhi"     : "FIXME",
              "studhilo"   : "FIXME",
              "fivedraw"   : "5 Card Draw",
              "27_1draw"   : "FIXME",
              "27_3draw"   : "Triple Draw 2-7 Lowball",
              "badugi"     : "FIXME"
             }
        ls = {"nl"  : "No Limit",
              "pl"  : "Pot Limit",
              "fl"  : "Limit",
              "cn"  : "Cap No Limit",
              "cp"  : "Cap Pot Limit"
             }

        string = "%s %s" %(gs[self.gametype[1]], ls[self.gametype[2]])
        
        return string

    def writeHand(self, fh=sys.__stdout__):
        # PokerStars format.
        #print "\n### Pseudo stars format ###"
        #print >>fh, _("%s Game #%s: %s ($%s/$%s) - %s" %(self.sitename, self.handid, self.getGameTypeAsString(), self.sb, self.bb, self.starttime))
        print >>fh, _("%s Game #%s: %s ($%s/$%s) - %s" %("PokerStars", self.handid, self.getGameTypeAsString(), self.sb, self.bb, self.starttime))
        print >>fh, _("Table '%s' %d-max Seat #%s is the button" %(self.tablename, self.maxseats, self.buttonpos))
        
        players_who_act_preflop = set([x[0] for x in self.actions['PREFLOP']])
        print players_who_act_preflop
        print [x[1] for x in self.players]
        print [x for x in self.players if x[1] in players_who_act_preflop]
        for player in [x for x in self.players if x[1] in players_who_act_preflop]:
            #Only print stacks of players who do something preflop
            print >>fh, _("Seat %s: %s ($%s)" %(player[0], player[1], player[2]))

        if(self.posted[0] is None):
            #print >>fh, _("No small blind posted") # PS doesn't say this
            pass
        else:
            print >>fh, _("%s: posts small blind $%s" %(self.posted[0], self.sb))

        #May be more than 1 bb posting
        for a in self.posted[1:]:
            print >>fh, _("%s: posts big blind $%s" %(self.posted[1], self.bb))

        # TODO: What about big & small blinds?

        print >>fh, _("*** HOLE CARDS ***")
        if self.involved:
            print >>fh, _("Dealt to %s [%s]" %(self.hero , " ".join(self.holecards[self.hero])))

        if 'PREFLOP' in self.actions:
            for act in self.actions['PREFLOP']:
                self.printActionLine(act, fh)

        if 'FLOP' in self.actions:
            print >>fh, _("*** FLOP *** [%s]" %( " ".join(self.board['Flop'])))
            for act in self.actions['FLOP']:
                self.printActionLine(act, fh)

        if 'TURN' in self.actions:
            print >>fh, _("*** TURN *** [%s] [%s]" %( " ".join(self.board['Flop']), " ".join(self.board['Turn'])))
            for act in self.actions['TURN']:
                self.printActionLine(act, fh)

        if 'RIVER' in self.actions:
            print >>fh, _("*** RIVER *** [%s] [%s]" %(" ".join(self.board['Flop']+self.board['Turn']), " ".join(self.board['River']) ))
            for act in self.actions['RIVER']:
                self.printActionLine(act, fh)


        #Some sites don't have a showdown section so we have to figure out if there should be one
        # The logic for a showdown is: at the end of river action there are at least two players in the hand
        # we probably don't need a showdown section in pseudo stars format for our filtering purposes
        if 'SHOWDOWN' in self.actions:
            print >>fh, _("*** SHOW DOWN ***")
            print >>fh, "DEBUG: what do they show"

        print >>fh, _("*** SUMMARY ***")
        print >>fh, _("Total pot $%s | Rake $%.2f" % (self.totalcollected, self.rake)) # TODO: side pots

        board = []
        for s in self.board.values():
            board += s
        if board:   # sometimes hand ends preflop without a board
            print >>fh, _("Board [%s]" % (" ".join(board)))


        for player in self.players:
            seatnum = player[0]
            name = player[1]
            if name in self.collected and self.holecards[name]:
                print >>fh, _("Seat %d: %s showed [%s] and won ($%s)" % (seatnum, name, " ".join(self.holecards[name]), self.collected[name]))
            elif name in self.collected:
                print >>fh, _("Seat %d: %s collected ($%s)" % (seatnum, name, self.collected[name]))
            elif player[1] in self.shown:
                print >>fh, _("Seat %d: %s showed [%s]" % (seatnum, name, " ".join(self.holecards[name])))
            elif player[1] in self.folded:
                print >>fh, _("Seat %d: %s folded" % (seatnum, name))
            else:
                print >>fh, _("Seat %d: %s mucked" % (seatnum, name))

        print >>fh, "\n\n"
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
        

    def printHand(self):
        self.writeHand(sys.stdout)

    def printActionLine(self, act, fh):
        if act[1] == 'folds':
            print >>fh, _("%s: folds" %(act[0]))
        elif act[1] == 'checks':
            print >>fh, _("%s: checks" %(act[0]))
        if act[1] == 'calls':
            print >>fh, _("%s: calls $%s" %(act[0], act[2]))
        if act[1] == 'bets':
            print >>fh, _("%s: bets $%s" %(act[0], act[2]))
        if act[1] == 'raises':
            print >>fh, _("%s: raises $%s to $%s" %(act[0], act[2], act[3]))

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
