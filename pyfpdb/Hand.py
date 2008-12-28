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
import time
from copy import deepcopy

class Hand:
#    def __init__(self, sitename, gametype, sb, bb, string):

    UPS = {'a':'A', 't':'T', 'j':'J', 'q':'Q', 'k':'K', 'S':'s', 'C':'c', 'H':'h', 'D':'d'}
    def __init__(self, sitename, gametype, string):
        self.sitename = sitename
        self.gametype = gametype
        self.string = string

        self.streetList = ['PREFLOP','FLOP','TURN','RIVER'] # a list of the observed street names in order

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
        
        self.stacks = {}

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
            self.stacks[name] = Decimal(chips)
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
        print "DEBUG: addHoleCards", cards,player
        try:
            self.checkPlayerExists(player)
            cards = set([self.card(c) for c in cards])
            self.holecards[player].update(cards)
        except FpdbParseError, e:
            print "[ERROR] Tried to add holecards for unknown player: %s" % (player,)

    def addShownCards(self, cards, player, holeandboard=None):
        """\
For when a player shows cards for any reason (for showdown or out of choice).
Card ranks will be uppercased
"""
        print "DEBUG: addShownCards", cards,player,holeandboard
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
            print "[ERROR] discardHoleCard tried to discard a card %s didn't have" % (player,)

    def setCommunityCards(self, street, cards):
        self.board[street] = [self.card(c) for c in cards]

    def card(self,c):
        """upper case the ranks but not suits, 'atjqk' => 'ATJQK'"""
        for k,v in self.UPS.items():
            c = c.replace(k,v)
        return c

    def addBlind(self, player, blindtype, amount):
        # if player is None, it's a missing small blind.
        print "DEBUG addBlind: %s posts %s, %s" % (player, blindtype, amount)
        if player is not None:
            self.bets['PREFLOP'][player].append(Decimal(amount))
            self.stacks[player] -= Decimal(amount)
            #print "DEBUG %s posts, stack %s" % (player, self.stacks[player])
            self.actions['PREFLOP'] += [(player, 'posts', blindtype, amount, self.stacks[player]==0)]
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
            self.stacks[player] -= Decimal(amount)
            print "DEBUG %s calls %s, stack %s" % (player, amount, self.stacks[player])
            self.actions[street] += [(player, 'calls', amount, self.stacks[player]==0)]
            
    def addRaiseBy(self, street, player, amountBy):
        """\
Add a raise by amountBy on [street] by [player] 
"""
        #Given only the amount raised by, the amount of the raise can be calculated by
        # working out how much this player has already in the pot 
        #   (which is the sum of self.bets[street][player])
        # and how much he needs to call to match the previous player 
        #   (which is tracked by self.lastBet)
        # let Bp = previous bet 
        #     Bc = amount player has committed so far
        #     Rb = raise by
        # then: C = Bp - Bc (amount to call)
        #      Rt = Bp + Rb (raise to)
        # 
        self.checkPlayerExists(player)
        Rb = Decimal(amountBy)
        Bp = self.lastBet[street]
        Bc = reduce(operator.add, self.bets[street][player], 0)
        C = Bp - Bc
        Rt = Bp + Rb
        
        self.bets[street][player].append(C + Rb)
        self.stacks[player] -= (C + Rb)
        self.actions[street] += [(player, 'raises', Rb, Rt, C, self.stacks[player]==0)]
        self.lastBet[street] = Rt

    def addCallandRaise(self, street, player, amount):
        """\
For sites which by "raises x" mean "calls and raises putting a total of x in the por". """
        self.checkPlayerExists(player)
        CRb = Decimal(amount)
        Bp = self.lastBet[street]
        Bc = reduce(operator.add, self.bets[street][player], 0)
        C = Bp - Bc
        Rb = CRb - C
        Rt = Bp + Rb
        
        self._addRaise(street, player, C, Rb, Rt)
        
    def _addRaise(self, street, player, C, Rb, Rt):
        self.bets[street][player].append(C + Rb)
        self.stacks[player] -= (C + Rb)
        self.actions[street] += [(player, 'raises', Rb, Rt, C, self.stacks[player]==0)]
        self.lastBet[street] = Rt
    
    def addRaiseTo(self, street, player, amountTo):
        """\
Add a raise on [street] by [player] to [amountTo]
"""
        self.checkPlayerExists(player)
        Bc = reduce(operator.add, self.bets[street][player], 0)
        Rt = Decimal(amountTo)
        C = Bp - Bc
        Rb = Rt - C
        self._addRaise(street, player, C, Rb, Rt)
        
        
    def addBet(self, street, player, amount):
        self.checkPlayerExists(player)
        self.bets[street][player].append(Decimal(amount))
        self.stacks[player] -= Decimal(amount)
        print "DEBUG %s bets %s, stack %s" % (player, amount, self.stacks[player])
        self.actions[street] += [(player, 'bets', amount, self.stacks[player]==0)]
        self.lastBet[street] = Decimal(amount)
        

    def addFold(self, street, player):
        print "DEBUG: %s %s folded" % (street, player)
        self.checkPlayerExists(player)
        self.folded.add(player)
        self.actions[street] += [(player, 'folds')]

    def addCheck(self, street, player):
        print "DEBUG: %s %s checked" % (street, player)
        self.checkPlayerExists(player)
        self.actions[street] += [(player, 'checks')]

    def addCollectPot(self,player, pot):
        print "DEBUG: %s collected %s" % (player, pot)
        self.checkPlayerExists(player)
        if player not in self.collected:
            self.collected[player] = pot
        else:
            print "[WARNING] %s collected pot more than once; avoidable by reading winnings only from summary lines?"


    def totalPot(self):
        """If all bets and blinds have been added, totals up the total pot size"""
        if self.totalpot is None:
            self.totalpot = 0

            for player in [x[1] for x in self.players]:
                for street in self.streetList:
                    self.totalpot += reduce(operator.add, self.bets[street][player], 0)

            print "DEBUG conventional totalpot:", self.totalpot
            
            
            self.totalpot = 0

            players_who_act_preflop = set([x[0] for x in self.actions['PREFLOP']])
            self.pot = Pot(players_who_act_preflop)
            
            
            # this can now be pruned substantially if Pot is working.
            #for street in self.actions:
            for street in [x for x in self.streetList if x in self.actions]:
                uncalled = 0
                calls = [0]
                for act in self.actions[street]:
                    if act[1] == 'bets': # [name, 'bets', amount]
                        self.totalpot += Decimal(act[2])
                        uncalled = Decimal(act[2])  # only the last bet or raise can be uncalled
                        calls = [0]
                        print "uncalled: ", uncalled
                        
                        self.pot.addMoney(act[0], Decimal(act[2]))
                        
                    elif act[1] == 'raises': # [name, 'raises', amountby, amountto, amountcalled]
                        print "calls %s and raises %s to %s" % (act[4],act[2],act[3])
                        self.totalpot += Decimal(act[2]) + Decimal(act[4])
                        calls = [0]
                        uncalled = Decimal(act[2])
                        print "uncalled: ", uncalled
                        
                        self.pot.addMoney(act[0], Decimal(act[2])+Decimal(act[4]))
                        
                    elif act[1] == 'calls': # [name, 'calls', amount]
                        self.totalpot += Decimal(act[2])
                        calls = calls + [Decimal(act[2])]
                        print "calls:", calls
                        
                        self.pot.addMoney(act[0], Decimal(act[2]))
                        
                    elif act[1] == 'posts':
                        self.totalpot += Decimal(act[3])
                        
                        self.pot.addMoney(act[0], Decimal(act[3]))
                        
                        if act[2] == 'big blind':
                            # the bb gets called by out-of-blinds posts; but sb+bb only calls bb
                            if uncalled == Decimal(act[3]): # a bb is already posted
                                calls = calls + [Decimal(act[3])]
                            elif 0 < uncalled < Decimal(act[3]): # a sb is already posted, btw wow python can do a<b<c.
                            # treat this as tho called & raised
                                calls = [0]
                                uncalled = Decimal(act[3]) - uncalled
                            else: # no blind yet posted.
                                uncalled = Decimal(act[3])
                        elif act[2] == 'small blind':
                            uncalled = Decimal(act[3])
                            calls = [0]
                            pass
                    elif act[1] == 'folds':
                        self.pot.addFold(act[0])
                if uncalled > 0 and max(calls+[0]) < uncalled:
                    
                    print "DEBUG returning some bet, calls:", calls
                    print "DEBUG returned: %.2f from %.2f" %  ((uncalled - max(calls)), self.totalpot,)
                    self.totalpot -= (uncalled - max(calls))
            print "DEBUG new totalpot:", self.totalpot
            print "DEBUG new Pot.total:", self.pot
            
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
        print >>fh, _("%s Game #%s: %s ($%s/$%s) - %s" %("PokerStars", self.handid, self.getGameTypeAsString(), self.sb, self.bb, time.strftime('%Y/%m/%d - %H:%M:%S (ET)', self.starttime)))
        print >>fh, _("Table '%s' %d-max Seat #%s is the button" %(self.tablename, self.maxseats, self.buttonpos))
        
        players_who_act_preflop = set([x[0] for x in self.actions['PREFLOP']])

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
            print >>fh, _("*** FLOP *** [%s]" %( " ".join(self.board['FLOP'])))
            for act in self.actions['FLOP']:
                self.printActionLine(act, fh)

        if 'TURN' in self.actions:
            print >>fh, _("*** TURN *** [%s] [%s]" %( " ".join(self.board['FLOP']), " ".join(self.board['TURN'])))
            for act in self.actions['TURN']:
                self.printActionLine(act, fh)

        if 'RIVER' in self.actions:
            print >>fh, _("*** RIVER *** [%s] [%s]" %(" ".join(self.board['FLOP']+self.board['TURN']), " ".join(self.board['RIVER']) ))
            for act in self.actions['RIVER']:
                self.printActionLine(act, fh)


        #Some sites don't have a showdown section so we have to figure out if there should be one
        # The logic for a showdown is: at the end of river action there are at least two players in the hand
        # we probably don't need a showdown section in pseudo stars format for our filtering purposes
        if 'SHOWDOWN' in self.actions:
            print >>fh, _("*** SHOW DOWN ***")
            print >>fh, "DEBUG: what do they show"

        print >>fh, _("*** SUMMARY ***")
        print >>fh, "%s | Rake $%.2f" % (self.pot, self.rake)
        #print >>fh, _("Total pot $%s | Rake $%.2f" % (self.totalpot, self.rake)) # TODO: side pots

        board = []
        for s in self.board.values():
            board += s
        if board:   # sometimes hand ends preflop without a board
            print >>fh, _("Board [%s]" % (" ".join(board)))

        for player in [x for x in self.players if x[1] in players_who_act_preflop]:
            seatnum = player[0]
            name = player[1]
            if name in self.collected and name in self.shown:
                print >>fh, _("Seat %d: %s showed [%s] and won ($%s)" % (seatnum, name, " ".join(self.holecards[name]), self.collected[name]))
            elif name in self.collected:
                print >>fh, _("Seat %d: %s collected ($%s)" % (seatnum, name, self.collected[name]))
            elif name in self.shown:
                print >>fh, _("Seat %d: %s showed [%s]" % (seatnum, name, " ".join(self.holecards[name])))
            elif name in self.folded:
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
            print >>fh, _("%s: folds " %(act[0]))
        elif act[1] == 'checks':
            print >>fh, _("%s: checks " %(act[0]))
        if act[1] == 'calls':
            print >>fh, _("%s: calls $%s%s" %(act[0], act[2], ' and is all-in' if act[3] else ''))
        if act[1] == 'bets':
            print >>fh, _("%s: bets $%s%s" %(act[0], act[2], ' and is all-in' if act[3] else ''))
        if act[1] == 'raises':
            print >>fh, _("%s: raises $%s to $%s%s" %(act[0], act[2], act[3], ' and is all-in' if act[5] else ''))

    # going to use pokereval to figure out hands at some point.
    # these functions are copied from pokergame.py
    def bestHand(self, side, cards):
        return HandHistoryConverter.eval.best('hi', cards, [])


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

class Pot(object):

    def __init__(self, contenders):
        self.contenders = contenders
        self.committed = dict([(player,Decimal(0)) for player in contenders])
        self.total = Decimal(0)
        
    def addFold(self, player):
        self.contenders.remove(player)
        
    def addMoney(self, player, amount):
        self.committed[player] += amount
        
    def __str__(self):
        self.total = sum(self.committed.values())
        committed = sorted([ (v,k) for (k,v) in self.committed.items()])
        lastbet = committed[-1][0] - committed[-2][0]
        if lastbet > 0: # uncalled
            returnto = committed[-1][1]
            #print "returning %f to %s" % (lastbet, returnto)
            self.total -= lastbet
            self.committed[returnto] -= lastbet
        
        
        
        # now: for those contenders still contending..
        commitsall = sorted([(v,k) for (k,v) in self.committed.items() if v >0])
        
        pots = []
        while len(commitsall) > 0:
            commitslive = [(v,k) for (v,k) in commitsall if k in self.contenders]
            v1 = commitslive[0][0]        
            pots += [sum([min(v,v1) for (v,k) in commitsall])]
            #print "all: ", commitsall
            #print "live:", commitslive
            commitsall = [((v-v1),k) for (v,k) in commitsall if v-v1 >0]

            
        #print "[**]", pots
        
        # TODO: I think rake gets taken out of the pots.
        # so it goes:
        # total pot x. main pot y, side pot z. | rake r
        # and y+z+r = x
        # for example:
        # Total pot $124.30 Main pot $98.90. Side pot $23.40. | Rake $2
        # so....... that's tricky.
        if len(pots) == 1: # (only use Total pot)
            #return "Main pot $%.2f." % pots[0]
            return "Total pot $%.2f" % (self.total,)
        elif len(pots) == 2:
            return "Total pot $%.2f Main pot $%.2f. Side pot $%2.f." % (self.total, pots[0],pots[1])
        elif len(pots) == 3:
            return "Total pot $%.2f Main pot $%.2f. Side pot-1 $%2.f. Side pot-2 $.2f." % (self.total, pots[0],pots[1],pots[2])
        else:
            return "too many pots.. fix me.", pots
            
