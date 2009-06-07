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

import re
import sys
import traceback
import logging
import os
import os.path
from decimal import Decimal
import operator
import time,datetime
from copy import deepcopy
from Exceptions import *
import DerivedStats
import Card

class Hand:
    UPS = {'a':'A', 't':'T', 'j':'J', 'q':'Q', 'k':'K', 'S':'s', 'C':'c', 'H':'h', 'D':'d'}
    LCS = {'H':'h', 'D':'d', 'C':'c', 'S':'s'}
    def __init__(self, sitename, gametype, handText, builtFrom = "HHC"):
        self.sitename = sitename
        self.stats = DerivedStats.DerivedStats(self)
        self.gametype = gametype
        self.handText = handText
        self.handid = 0
        self.tablename = "Slartibartfast"
        self.hero = "Hiro"
        self.maxseats = 10
        self.counted_seats = 0
        self.buttonpos = 0
        self.seating = []
        self.players = []
        self.posted = []
        self.involved = True

        # Collections indexed by street names
        self.bets = {}
        self.lastBet = {}
        self.streets = {}
        self.actions = {} # [['mct','bets','$10'],['mika','folds'],['carlg','raises','$20']]
        self.board = {} # dict from street names to community cards
        for street in self.streetList:
            self.streets[street] = "" # portions of the handText, filled by markStreets()
            self.bets[street] = {}
            self.lastBet[street] = 0
            self.actions[street] = []
            self.board[street] = []
        
        # Collections indexed by player names
        self.holecards = {} # dict from player names to dicts by street ... of tuples ... of holecards
        self.discards = {} # dict from player names to dicts by street ... of tuples ... of discarded holecards
        self.stacks = {}
        self.collected = [] #list of ?
        self.collectees = {} # dict from player names to amounts collected (?)

        # Sets of players
        self.shown = set()
        self.folded = set()

#        self.action = []
        # Things to do with money
        self.pot = Pot()
        self.totalpot = None
        self.totalcollected = None
        self.rake = None


    def insert(self, db):
        """ Function to insert Hand into database
Should not commit, and do minimal selects. Callers may want to cache commits
db: a connected fpdb_db object"""
        # TODO:
        # Players - base playerid and siteid tuple
        # HudCache data to come from DerivedStats class
        # HandsActions - all actions for all players for all streets - self.actions
        # BoardCards - ?
        # Hands - Summary information of hand indexed by handId - gameinfo
        # HandsPlayers - ? ... Do we fix winnings?
        # Tourneys ?
        # TourneysPlayers

        pass

    def select(self, handId):
        """ Function to create Hand object from database """
        
        


    def addPlayer(self, seat, name, chips):
        """\
Adds a player to the hand, and initialises data structures indexed by player.
seat    (int) indicating the seat
name    (string) player name
chips   (string) the chips the player has at the start of the hand (can be None)
If a player has None chips he won't be added."""
        logging.debug("addPlayer: %s %s (%s)" % (seat, name, chips))
        if chips is not None:
            self.players.append([seat, name, chips])
            self.stacks[name] = Decimal(chips)
            self.holecards[name] = []
            self.discards[name] = []
            self.pot.addPlayer(name)
            for street in self.streetList:
                self.bets[street][name] = []
                self.holecards[name] = {} # dict from street names.
                self.discards[name] = {} # dict from street names.


    def addStreets(self, match):
        # go through m and initialise actions to empty list for each street.
        if match:
            self.streets.update(match.groupdict())
            logging.debug("markStreets:\n"+ str(self.streets))
        else:
            logging.error("markstreets didn't match")

    def checkPlayerExists(self,player):
        if player not in [p[1] for p in self.players]:
            print "checkPlayerExists", player, "fail"
            raise FpdbParseError



    def setCommunityCards(self, street, cards):
        logging.debug("setCommunityCards %s %s" %(street,  cards))
        self.board[street] = [self.card(c) for c in cards]

    def card(self,c):
        """upper case the ranks but not suits, 'atjqk' => 'ATJQK'"""
        for k,v in self.UPS.items():
            c = c.replace(k,v)
        return c

    def addAnte(self, player, ante):
        logging.debug("%s %s antes %s" % ('ANTES', player, ante))
        if player is not None:
            self.bets['ANTES'][player].append(Decimal(ante))
            self.stacks[player] -= Decimal(ante)
            act = (player, 'posts', "ante", ante, self.stacks[player]==0)
            self.actions['ANTES'].append(act)
            #~ self.lastBet['ANTES'] = Decimal(ante)   
            self.pot.addMoney(player, Decimal(ante))

    def addBlind(self, player, blindtype, amount):
        # if player is None, it's a missing small blind.
        # The situation we need to cover are:
        # Player in small blind posts
        #   - this is a bet of 1 sb, as yet uncalled.
        # Player in the big blind posts
        #   - this is a call of 1 sb and a raise to 1 bb
        #

        logging.debug("addBlind: %s posts %s, %s" % (player, blindtype, amount))
        if player is not None:
            self.bets['PREFLOP'][player].append(Decimal(amount))
            self.stacks[player] -= Decimal(amount)
            #print "DEBUG %s posts, stack %s" % (player, self.stacks[player])
            act = (player, 'posts', blindtype, amount, self.stacks[player]==0)
            self.actions['BLINDSANTES'].append(act)
            self.pot.addMoney(player, Decimal(amount))
            if blindtype == 'big blind':
                self.lastBet['PREFLOP'] = Decimal(amount)
            elif blindtype == 'both':
                # extra small blind is 'dead'
                self.lastBet['PREFLOP'] = Decimal(self.bb)
            self.posted = self.posted + [[player,blindtype]]
        #print "DEBUG: self.posted: %s" %(self.posted)



    def addCall(self, street, player=None, amount=None):
        logging.debug("%s %s calls %s" %(street, player, amount))
        # Potentially calculate the amount of the call if not supplied
        # corner cases include if player would be all in
        if amount is not None:
            self.bets[street][player].append(Decimal(amount))
            #self.lastBet[street] = Decimal(amount)
            self.stacks[player] -= Decimal(amount)
            #print "DEBUG %s calls %s, stack %s" % (player, amount, self.stacks[player])
            act = (player, 'calls', amount, self.stacks[player]==0)
            self.actions[street].append(act)
            self.pot.addMoney(player, Decimal(amount))
            
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
        
        self._addRaise(street, player, C, Rb, Rt)
        #~ self.bets[street][player].append(C + Rb)
        #~ self.stacks[player] -= (C + Rb)
        #~ self.actions[street] += [(player, 'raises', Rb, Rt, C, self.stacks[player]==0)]
        #~ self.lastBet[street] = Rt

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

    def addRaiseTo(self, street, player, amountTo):
        """\
Add a raise on [street] by [player] to [amountTo]
"""
        #CG - No idea if this function has been test/verified
        self.checkPlayerExists(player)
        Bp = self.lastBet[street]
        Bc = reduce(operator.add, self.bets[street][player], 0)
        Rt = Decimal(amountTo)
        C = Bp - Bc
        Rb = Rt - C
        self._addRaise(street, player, C, Rb, Rt)

    def _addRaise(self, street, player, C, Rb, Rt):
        logging.debug("%s %s raise %s" %(street, player, Rt))
        self.bets[street][player].append(C + Rb)
        self.stacks[player] -= (C + Rb)
        act = (player, 'raises', Rb, Rt, C, self.stacks[player]==0)
        self.actions[street].append(act)
        self.lastBet[street] = Rt # TODO check this is correct
        self.pot.addMoney(player, C+Rb)
    
        
        
    def addBet(self, street, player, amount):
        logging.debug("%s %s bets %s" %(street, player, amount))
        self.checkPlayerExists(player)
        self.bets[street][player].append(Decimal(amount))
        self.stacks[player] -= Decimal(amount)
        #print "DEBUG %s bets %s, stack %s" % (player, amount, self.stacks[player])
        act = (player, 'bets', amount, self.stacks[player]==0)
        self.actions[street].append(act)
        self.lastBet[street] = Decimal(amount)
        self.pot.addMoney(player, Decimal(amount))


    def addStandsPat(self, street, player):
        self.checkPlayerExists(player)
        act = (player, 'stands pat')
        self.actions[street].append(act)
        

    def addFold(self, street, player):
        logging.debug("%s %s folds" % (street, player))
        self.checkPlayerExists(player)
        self.folded.add(player)
        self.pot.addFold(player)
        self.actions[street].append((player, 'folds'))
        

    def addCheck(self, street, player):
        #print "DEBUG: %s %s checked" % (street, player)
        self.checkPlayerExists(player)
        self.actions[street].append((player, 'checks'))


    def addCollectPot(self,player, pot):
        logging.debug("%s collected %s" % (player, pot))
        self.checkPlayerExists(player)
        self.collected = self.collected + [[player, pot]]
        if player not in self.collectees:
            self.collectees[player] = Decimal(pot)
        else:
            self.collectees[player] += Decimal(pot)


    def totalPot(self):
        """If all bets and blinds have been added, totals up the total pot size"""
        
        # This gives us the total amount put in the pot
        if self.totalpot is None:
            self.pot.end()
            self.totalpot = self.pot.total

        # This gives us the amount collected, i.e. after rake
        if self.totalcollected is None:
            self.totalcollected = 0;
            #self.collected looks like [[p1,amount][px,amount]]
            for entry in self.collected:
                self.totalcollected += Decimal(entry[1])




    def getGameTypeAsString(self):
        """\
Map the tuple self.gametype onto the pokerstars string describing it
"""
        # currently it appears to be something like ["ring", "hold", "nl", sb, bb]:
        gs = {"holdem"       : "Hold'em",
              "omahahi"    : "Omaha",
              "omahahilo"  : "Omaha Hi/Lo",
              "razz"       : "Razz",
              "studhi"     : "7 Card Stud",
              "studhilo"   : "FIXME",
              "fivedraw"   : "5 Card Draw",
              "27_1draw"   : "FIXME",
              "27_3draw"   : "Triple Draw 2-7 Lowball",
              "badugi"     : "Badugi"
             }
        ls = {"nl"  : "No Limit",
              "pl"  : "Pot Limit",
              "fl"  : "Limit",
              "cn"  : "Cap No Limit",
              "cp"  : "Cap Pot Limit"
             }

        logging.debug("gametype: %s" %(self.gametype))
        retstring = "%s %s" %(gs[self.gametype['category']], ls[self.gametype['limitType']])
            
        return retstring


    def writeHand(self, fh=sys.__stdout__):
        print >>fh, "Override me"

    def printHand(self):
        self.writeHand(sys.stdout)

    def printActionLine(self, act, fh):
        if act[1] == 'folds':
            print >>fh, ("%s: folds " %(act[0]))
        elif act[1] == 'checks':
            print >>fh, ("%s: checks " %(act[0]))
        elif act[1] == 'calls':
            print >>fh, ("%s: calls $%s%s" %(act[0], act[2], ' and is all-in' if act[3] else ''))
        elif act[1] == 'bets':
            print >>fh, ("%s: bets $%s%s" %(act[0], act[2], ' and is all-in' if act[3] else ''))
        elif act[1] == 'raises':
            print >>fh, ("%s: raises $%s to $%s%s" %(act[0], act[2], act[3], ' and is all-in' if act[5] else ''))
        elif act[1] == 'completea':
            print >>fh, ("%s: completes to $%s%s" %(act[0], act[2], ' and is all-in' if act[3] else ''))
        elif act[1] == 'posts':
            if(act[2] == "small blind"):
                print >>fh, ("%s: posts small blind $%s%s" %(act[0], act[3], ' and is all-in' if act[4] else ''))
            elif(act[2] == "big blind"):
                print >>fh, ("%s: posts big blind $%s%s" %(act[0], act[3], ' and is all-in' if act[4] else ''))
            elif(act[2] == "both"):
                print >>fh, ("%s: posts small & big blinds $%s%s" %(act[0], act[3], ' and is all-in' if act[4] else ''))
        elif act[1] == 'bringin':
            print >>fh, ("%s: brings in for $%s%s" %(act[0], act[2], ' and is all-in' if act[3] else ''))
        elif act[1] == 'discards':
            print >>fh, ("%s: discards %s %s%s" %(act[0], act[2], 'card' if act[2] == 1 else 'cards' , " [" + " ".join(self.discards[act[0]]['DRAWONE']) + "]" if self.hero == act[0] else ''))
        elif act[1] == 'stands pat':
            print >>fh, ("%s: stands pat" %(act[0]))


class HoldemOmahaHand(Hand):
    def __init__(self, hhc, sitename, gametype, handText, builtFrom = "HHC", handid=None):
        if gametype['base'] != 'hold':
            pass # or indeed don't pass and complain instead
        logging.debug("HoldemOmahaHand")
        self.streetList = ['BLINDSANTES', 'DEAL', 'PREFLOP','FLOP','TURN','RIVER'] # a list of the observed street names in order
        self.communityStreets = ['FLOP', 'TURN', 'RIVER']
        self.actionStreets = ['PREFLOP','FLOP','TURN','RIVER']
        Hand.__init__(self, sitename, gametype, handText, builtFrom = "HHC")
        self.sb = gametype['sb']
        self.bb = gametype['bb']
        
        #Populate a HoldemOmahaHand
        #Generally, we call 'read' methods here, which get the info according to the particular filter (hhc) 
        # which then invokes a 'addXXX' callback
        if builtFrom == "HHC":
            hhc.readHandInfo(self)
            hhc.readPlayerStacks(self)
            hhc.compilePlayerRegexs(self)
            hhc.markStreets(self)
            hhc.readBlinds(self)
            hhc.readButton(self)
            hhc.readHeroCards(self)
            hhc.readShowdownActions(self)
            # Read actions in street order
            for street in self.communityStreets:
                if self.streets[street]:
                    hhc.readCommunityCards(self, street)
            for street in self.actionStreets:
                if self.streets[street]:
                    hhc.readAction(self, street)
            hhc.readCollectPot(self)
            hhc.readShownCards(self)
            self.totalPot() # finalise it (total the pot)
            hhc.getRake(self)
        elif builtFrom == "DB":
            if handid is not None:
                self.select(handid) # Will need a handId
            else:
                logging.warning("HoldemOmahaHand.__init__:Can't assemble hand from db without a handid")
        else:
            logging.warning("HoldemOmahaHand.__init__:Neither HHC nor DB+handid provided")
            pass
                

    def addHoleCards(self, cards, player, shown=False):
        """\
Assigns observed holecards to a player.
cards   list of card bigrams e.g. ['2h','Jc']
player  (string) name of player
"""
        logging.debug("addHoleCards %s %s" % (cards, player))
        try:
            self.checkPlayerExists(player)
            cardset = set(self.card(c) for c in cards)
            if shown and len(cardset) > 0:
                self.shown.add(player)
            if 'PREFLOP' in self.holecards[player]:
                self.holecards[player]['PREFLOP'].update(cardset)
            else:
                self.holecards[player]['PREFLOP'] = cardset
        except FpdbParseError, e:
            print "[ERROR] Tried to add holecards for unknown player: %s" % (player,)

    def addShownCards(self, cards, player, holeandboard=None):
        """\
For when a player shows cards for any reason (for showdown or out of choice).
Card ranks will be uppercased
"""
        logging.debug("addShownCards %s hole=%s all=%s" % (player, cards,  holeandboard))
        if cards is not None:
            self.shown.add(player)
            self.addHoleCards(cards,player)
        elif holeandboard is not None:
            holeandboard = set([self.card(c) for c in holeandboard])
            board = set([c for s in self.board.values() for c in s])
            self.addHoleCards(holeandboard.difference(board),player,shown=True)


    def writeHand(self, fh=sys.__stdout__):
        # PokerStars format.
        print >>fh, ("%s Game #%s:  %s ($%s/$%s) - %s" %("PokerStars", self.handid, self.getGameTypeAsString(), self.sb, self.bb, datetime.datetime.strftime(self.starttime,'%Y/%m/%d - %H:%M:%S ET')))
        print >>fh, ("Table '%s' %d-max Seat #%s is the button" %(self.tablename, self.maxseats, self.buttonpos))
        
        players_who_act_preflop = set(([x[0] for x in self.actions['PREFLOP']]+[x[0] for x in self.actions['BLINDSANTES']]))
        logging.debug(self.actions['PREFLOP'])
        for player in [x for x in self.players if x[1] in players_who_act_preflop]:
            #Only print stacks of players who do something preflop
            print >>fh, ("Seat %s: %s ($%s in chips) " %(player[0], player[1], player[2]))

        if self.actions['BLINDSANTES']:
            for act in self.actions['BLINDSANTES']:
                self.printActionLine(act, fh)
        
        print >>fh, ("*** HOLE CARDS ***")
        if self.involved:
            print >>fh, ("Dealt to %s [%s]" %(self.hero , " ".join(self.holecards[self.hero]['PREFLOP'])))

        if self.actions['PREFLOP']:
            for act in self.actions['PREFLOP']:
                self.printActionLine(act, fh)

        if self.board['FLOP']:
            print >>fh, ("*** FLOP *** [%s]" %( " ".join(self.board['FLOP'])))
        if self.actions['FLOP']:
            for act in self.actions['FLOP']:
                self.printActionLine(act, fh)

        if self.board['TURN']:
            print >>fh, ("*** TURN *** [%s] [%s]" %( " ".join(self.board['FLOP']), " ".join(self.board['TURN'])))
        if self.actions['TURN']:
            for act in self.actions['TURN']:
                self.printActionLine(act, fh)

        if self.board['RIVER']:
            print >>fh, ("*** RIVER *** [%s] [%s]" %(" ".join(self.board['FLOP']+self.board['TURN']), " ".join(self.board['RIVER']) ))
        if self.actions['RIVER']:
            for act in self.actions['RIVER']:
                self.printActionLine(act, fh)


        #Some sites don't have a showdown section so we have to figure out if there should be one
        # The logic for a showdown is: at the end of river action there are at least two players in the hand
        # we probably don't need a showdown section in pseudo stars format for our filtering purposes
        if self.shown:
            print >>fh, ("*** SHOW DOWN ***")
            for name in self.shown:
                # TODO: legacy importer can't handle only one holecard here, make sure there are 2 for holdem, 4 for omaha
                # TOOD: If HoldHand subclass supports more than omahahi, omahahilo, holdem, add them here
                numOfHoleCardsNeeded = None
                if self.gametype['category'] in ('omahahi','omahahilo'):
                    numOfHoleCardsNeeded = 4
                elif self.gametype['category'] in ('holdem'):
                    numOfHoleCardsNeeded = 2
                if len(self.holecards[name]['PREFLOP']) == numOfHoleCardsNeeded:
                    print >>fh, ("%s shows [%s] (a hand...)" % (name, " ".join(self.holecards[name]['PREFLOP'])))
                
        # Current PS format has the lines:
        # Uncalled bet ($111.25) returned to s0rrow
        # s0rrow collected $5.15 from side pot
        # stervels: shows [Ks Qs] (two pair, Kings and Queens)
        # stervels collected $45.35 from main pot
        # Immediately before the summary.
        # The current importer uses those lines for importing winning rather than the summary
        for name in self.pot.returned:
            print >>fh, ("Uncalled bet ($%s) returned to %s" %(self.pot.returned[name],name))
        for entry in self.collected:
            print >>fh, ("%s collected $%s from x pot" %(entry[0], entry[1]))

        print >>fh, ("*** SUMMARY ***")
        print >>fh, "%s | Rake $%.2f" % (self.pot, self.rake)

        board = []
        for s in self.board.values():
            board += s
        if board:   # sometimes hand ends preflop without a board
            print >>fh, ("Board [%s]" % (" ".join(board)))

        for player in [x for x in self.players if x[1] in players_who_act_preflop]:
            seatnum = player[0]
            name = player[1]
            if name in self.collectees and name in self.shown:
                print >>fh, ("Seat %d: %s showed [%s] and won ($%s)" % (seatnum, name, " ".join(self.holecards[name]['PREFLOP']), self.collectees[name]))
            elif name in self.collectees:
                print >>fh, ("Seat %d: %s collected ($%s)" % (seatnum, name, self.collectees[name]))
            #~ elif name in self.shown:
                #~ print >>fh, _("Seat %d: %s showed [%s]" % (seatnum, name, " ".join(self.holecards[name]['PREFLOP'])))
            elif name in self.folded:
                print >>fh, ("Seat %d: %s folded" % (seatnum, name))
            else:
                if name in self.shown:
                    print >>fh, ("Seat %d: %s showed [%s] and lost with..." % (seatnum, name, " ".join(self.holecards[name]['PREFLOP'])))
                else:
                    print >>fh, ("Seat %d: %s mucked" % (seatnum, name))

        print >>fh, "\n\n"
        
class DrawHand(Hand):
    def __init__(self, hhc, sitename, gametype, handText, builtFrom = "HHC"):
        if gametype['base'] != 'draw':
            pass # or indeed don't pass and complain instead
        self.streetList = ['BLINDSANTES', 'DEAL', 'DRAWONE', 'DRAWTWO', 'DRAWTHREE']
        self.holeStreets = ['DEAL', 'DRAWONE', 'DRAWTWO', 'DRAWTHREE']
        self.actionStreets =  ['PREDEAL', 'DEAL', 'DRAWONE', 'DRAWTWO', 'DRAWTHREE']
        Hand.__init__(self, sitename, gametype, handText)
        self.sb = gametype['sb']
        self.bb = gametype['bb']
        # Populate the draw hand.
        if builtFrom == "HHC":
            hhc.readHandInfo(self)
            hhc.readPlayerStacks(self)
            hhc.compilePlayerRegexs(self)
            hhc.markStreets(self)
            hhc.readBlinds(self)
            hhc.readButton(self)
            hhc.readShowdownActions(self)
            # Read actions in street order
            for street in self.streetList:
                if self.streets[street]:
                    # hhc.readCommunityCards(self, street)
                    hhc.readDrawCards(self, street)
                    hhc.readAction(self, street)
            hhc.readCollectPot(self)
            hhc.readShownCards(self)
            self.totalPot() # finalise it (total the pot)
            hhc.getRake(self)
        elif builtFrom == "DB":
            self.select("dummy") # Will need a handId

    # Draw games (at least Badugi has blinds - override default Holdem addBlind
    def addBlind(self, player, blindtype, amount):
        # if player is None, it's a missing small blind.
        # The situation we need to cover are:
        # Player in small blind posts
        #   - this is a bet of 1 sb, as yet uncalled.
        # Player in the big blind posts
        #   - this is a call of 1 sb and a raise to 1 bb
        # 
        
        logging.debug("addBlind: %s posts %s, %s" % (player, blindtype, amount))
        if player is not None:
            self.bets['DEAL'][player].append(Decimal(amount))
            self.stacks[player] -= Decimal(amount)
            #print "DEBUG %s posts, stack %s" % (player, self.stacks[player])
            act = (player, 'posts', blindtype, amount, self.stacks[player]==0)
            self.actions['BLINDSANTES'].append(act)
            self.pot.addMoney(player, Decimal(amount))
            if blindtype == 'big blind':
                self.lastBet['DEAL'] = Decimal(amount)            
            elif blindtype == 'both':
                # extra small blind is 'dead'
                self.lastBet['DEAL'] = Decimal(self.bb)
        self.posted = self.posted + [[player,blindtype]]
        #print "DEBUG: self.posted: %s" %(self.posted)



    def addDrawHoleCards(self, newcards, oldcards, player, street, shown=False):
        """\
Assigns observed holecards to a player.
cards   list of card bigrams e.g. ['2h','Jc']
player  (string) name of player
"""
        try:
            self.checkPlayerExists(player)
#            if shown and len(cardset) > 0:
#                self.shown.add(player)
            self.holecards[player][street] = (newcards,oldcards)
        except FpdbParseError, e:
            print "[ERROR] Tried to add holecards for unknown player: %s" % (player,)


    def discardDrawHoleCards(self, cards, player, street):
        logging.debug("discardDrawHoleCards '%s' '%s' '%s'" % (cards, player, street))
        self.discards[player][street] = set([cards])


    def addDiscard(self, street, player, num, cards):
        self.checkPlayerExists(player)
        if cards:
            act = (player, 'discards', num, cards)
            self.discardDrawHoleCards(cards, player, street)
        else:
            act = (player, 'discards', num)
        self.actions[street].append(act)


    def addShownCards(self, cards, player, holeandboard=None):
        """\
For when a player shows cards for any reason (for showdown or out of choice).
Card ranks will be uppercased
"""
        logging.debug("addShownCards %s hole=%s all=%s" % (player, cards,  holeandboard))
#        if cards is not None:
#            self.shown.add(player)
#            self.addHoleCards(cards,player)
#        elif holeandboard is not None:
#            holeandboard = set([self.card(c) for c in holeandboard])
#            board = set([c for s in self.board.values() for c in s])
#            self.addHoleCards(holeandboard.difference(board),player,shown=True)


    def writeHand(self, fh=sys.__stdout__):
        # PokerStars format.
        print >>fh, _("%s Game #%s:  %s ($%s/$%s) - %s" %("PokerStars", self.handid, self.getGameTypeAsString(), self.sb, self.bb, time.strftime('%Y/%m/%d %H:%M:%S ET', self.starttime)))
        print >>fh, _("Table '%s' %d-max Seat #%s is the button" %(self.tablename, self.maxseats, self.buttonpos))

        players_who_act_ondeal = set(([x[0] for x in self.actions['DEAL']]+[x[0] for x in self.actions['BLINDSANTES']]))

        for player in [x for x in self.players if x[1] in players_who_act_ondeal]:
            #Only print stacks of players who do something on deal
            print >>fh, _("Seat %s: %s ($%s in chips) " %(player[0], player[1], player[2]))

        if 'BLINDSANTES' in self.actions:
            for act in self.actions['BLINDSANTES']:
                print >>fh, _("%s: %s %s $%s" %(act[0], act[1], act[2], act[3]))

        if 'DEAL' in self.actions:
            print >>fh, _("*** DEALING HANDS ***")
            for player in [x[1] for x in self.players if x[1] in players_who_act_ondeal]:
                if 'DEAL' in self.holecards[player]:
                    (nc,oc) = self.holecards[player]['DEAL']
                    print >>fh, _("Dealt to %s: [%s]") % (player, " ".join(nc))
            for act in self.actions['DEAL']:
                self.printActionLine(act, fh)

        if 'DRAWONE' in self.actions:
            print >>fh, _("*** FIRST DRAW ***")
            for act in self.actions['DRAWONE']:
                self.printActionLine(act, fh)
                if act[0] == self.hero and act[1] == 'discards':
                    (nc,oc) = self.holecards[act[0]]['DRAWONE']
                    dc = self.discards[act[0]]['DRAWONE']
                    kc = oc - dc
                    print >>fh, _("Dealt to %s [%s] [%s]" % (act[0], " ".join(kc), " ".join(nc)))

        if 'DRAWTWO' in self.actions:
            print >>fh, _("*** SECOND DRAW ***")
            for act in self.actions['DRAWTWO']:
                self.printActionLine(act, fh)
                if act[0] == self.hero and act[1] == 'discards':
                    (nc,oc) = self.holecards[act[0]]['DRAWTWO']
                    dc = self.discards[act[0]]['DRAWTWO']
                    kc = oc - dc
                    print >>fh, _("Dealt to %s [%s] [%s]" % (act[0], " ".join(kc), " ".join(nc)))

        if 'DRAWTHREE' in self.actions:
            print >>fh, _("*** THIRD DRAW ***")
            for act in self.actions['DRAWTHREE']:
                self.printActionLine(act, fh)
                if act[0] == self.hero and act[1] == 'discards':
                    (nc,oc) = self.holecards[act[0]]['DRAWTHREE']
                    dc = self.discards[act[0]]['DRAWTHREE']
                    kc = oc - dc
                    print >>fh, _("Dealt to %s [%s] [%s]" % (act[0], " ".join(kc), " ".join(nc)))

        if 'SHOWDOWN' in self.actions:
            print >>fh, _("*** SHOW DOWN ***")
            #TODO: Complete SHOWDOWN

        # Current PS format has the lines:
        # Uncalled bet ($111.25) returned to s0rrow
        # s0rrow collected $5.15 from side pot
        # stervels: shows [Ks Qs] (two pair, Kings and Queens)
        # stervels collected $45.35 from main pot
        # Immediately before the summary.
        # The current importer uses those lines for importing winning rather than the summary
        for name in self.pot.returned:
            print >>fh, _("Uncalled bet ($%s) returned to %s" %(self.pot.returned[name],name))
        for entry in self.collected:
            print >>fh, _("%s collected $%s from x pot" %(entry[0], entry[1]))

        print >>fh, _("*** SUMMARY ***")
        print >>fh, "%s | Rake $%.2f" % (self.pot, self.rake)
        print >>fh, "\n\n"



class StudHand(Hand):
    def __init__(self, hhc, sitename, gametype, handText, builtFrom = "HHC"):
        if gametype['base'] != 'stud':
            pass # or indeed don't pass and complain instead
        self.streetList = ['ANTES','THIRD','FOURTH','FIFTH','SIXTH','SEVENTH'] # a list of the observed street names in order
        self.holeStreets = ['ANTES','THIRD','FOURTH','FIFTH','SIXTH','SEVENTH']
        Hand.__init__(self, sitename, gametype, handText)
        self.sb = gametype['sb']
        self.bb = gametype['bb']
        #Populate the StudHand
        #Generally, we call a 'read' method here, which gets the info according to the particular filter (hhc) 
        # which then invokes a 'addXXX' callback
        if builtFrom == "HHC":
            hhc.readHandInfo(self)
            hhc.readPlayerStacks(self)
            hhc.compilePlayerRegexs(self)
            hhc.markStreets(self)
            hhc.readAntes(self)
            hhc.readBringIn(self)
            #hhc.readShowdownActions(self) # not done yet
            # Read actions in street order
            for street in self.streetList:
                if self.streets[street]:
                    logging.debug(street)
                    logging.debug(self.streets[street])
                    hhc.readStudPlayerCards(self, street)
                    hhc.readAction(self, street)
            hhc.readCollectPot(self)
            #hhc.readShownCards(self) # not done yet
            self.totalPot() # finalise it (total the pot)
            hhc.getRake(self)
        elif builtFrom == "DB":
            self.select("dummy") # Will need a handId

    def addPlayerCards(self, player,  street,  open=[],  closed=[]):
        """\
Assigns observed cards to a player.
player  (string) name of player
street  (string) the street name (in streetList)
open  list of card bigrams e.g. ['2h','Jc'], dealt face up
closed    likewise, but known only to player
"""
        logging.debug("addPlayerCards %s, o%s x%s" % (player,  open, closed))
        try:
            self.checkPlayerExists(player)
            self.holecards[player][street] = (open, closed)
#            cards = set([self.card(c) for c in cards])
#            self.holecards[player].update(cards)
        except FpdbParseError, e:
            print "[ERROR] Tried to add holecards for unknown player: %s" % (player,)

    # TODO: def addComplete(self, player, amount):
    def addComplete(self, street, player, amountTo):
        # assert street=='THIRD'
        #     This needs to be called instead of addRaiseTo, and it needs to take account of self.lastBet['THIRD'] to determine the raise-by size
        """\
Add a complete on [street] by [player] to [amountTo]
"""
        logging.debug("%s %s completes %s" % (street, player, amountTo))
        self.checkPlayerExists(player)
        Bp = self.lastBet['THIRD']
        Bc = reduce(operator.add, self.bets[street][player], 0)
        Rt = Decimal(amountTo)
        C = Bp - Bc
        Rb = Rt - C
        self._addRaise(street, player, C, Rb, Rt)
        #~ self.bets[street][player].append(C + Rb)
        #~ self.stacks[player] -= (C + Rb)
        #~ act = (player, 'raises', Rb, Rt, C, self.stacks[player]==0)
        #~ self.actions[street].append(act)
        #~ self.lastBet[street] = Rt # TODO check this is correct
        #~ self.pot.addMoney(player, C+Rb)
        
    def addBringIn(self, player, bringin):
        if player is not None:
            logging.debug("Bringin: %s, %s" % (player , bringin))
            self.bets['THIRD'][player].append(Decimal(bringin))
            self.stacks[player] -= Decimal(bringin)
            act = (player, 'bringin', bringin, self.stacks[player]==0)
            self.actions['THIRD'].append(act)
            self.lastBet['THIRD'] = Decimal(bringin)
            self.pot.addMoney(player, Decimal(bringin))
    
    def writeHand(self, fh=sys.__stdout__):
        # PokerStars format.
        print >>fh, _("%s Game #%s:  %s ($%s/$%s) - %s" %("PokerStars", self.handid, self.getGameTypeAsString(), self.sb, self.bb, time.strftime('%Y/%m/%d - %H:%M:%S (ET)', self.starttime)))
        print >>fh, _("Table '%s' %d-max Seat #%s is the button" %(self.tablename, self.maxseats, self.buttonpos))
        
        players_who_post_antes = set([x[0] for x in self.actions['ANTES']])

        for player in [x for x in self.players if x[1] in players_who_post_antes]:
            #Only print stacks of players who do something preflop
            print >>fh, _("Seat %s: %s ($%s)" %(player[0], player[1], player[2]))

        if 'ANTES' in self.actions:
            for act in self.actions['ANTES']:
                print >>fh, _("%s: posts the ante $%s" %(act[0], act[3]))

        if 'THIRD' in self.actions:
            dealt = 0
            #~ print >>fh, _("*** 3RD STREET ***")
            for player in [x[1] for x in self.players if x[1] in players_who_post_antes]:
                if 'THIRD' in self.holecards[player]:
                    (open,  closed) = self.holecards[player]['THIRD']
                    dealt+=1
                    if dealt==1:
                        print >>fh, _("*** 3RD STREET ***")
                    print >>fh, _("Dealt to %s:%s%s") % (player, " [" + " ".join(closed) + "] " if closed else " ", "[" + " ".join(open) + "]" if open else "")
            for act in self.actions['THIRD']:
                #FIXME: Need some logic here for bringin vs completes
                self.printActionLine(act, fh)

        if 'FOURTH' in self.actions:
            dealt = 0
            #~ print >>fh, _("*** 4TH STREET ***")
            for player in [x[1] for x in self.players if x[1] in players_who_post_antes]:
                if 'FOURTH' in self.holecards[player]:
                    old = []
                    (o,c) = self.holecards[player]['THIRD']
                    if o:old.extend(o)
                    if c:old.extend(c)
                    new = self.holecards[player]['FOURTH'][0]
                    dealt+=1
                    if dealt==1:
                        print >>fh, _("*** 4TH STREET ***")
                    print >>fh, _("Dealt to %s:%s%s") % (player, " [" + " ".join(old) + "] " if old else " ", "[" + " ".join(new) + "]" if new else "")
            for act in self.actions['FOURTH']:
                self.printActionLine(act, fh)

        if 'FIFTH' in self.actions:
            dealt = 0
            #~ print >>fh, _("*** 5TH STREET ***")
            for player in [x[1] for x in self.players if x[1] in players_who_post_antes]:
                if 'FIFTH' in self.holecards[player]:
                    old = []
                    for street in ('THIRD','FOURTH'):
                        (o,c) = self.holecards[player][street]
                        if o:old.extend(o)
                        if c:old.extend(c)
                    new = self.holecards[player]['FIFTH'][0]
                    dealt+=1
                    if dealt==1:
                        print >>fh, _("*** 5TH STREET ***")
                    print >>fh, _("Dealt to %s:%s%s") % (player, " [" + " ".join(old) + "] " if old else " ", "[" + " ".join(new) + "]" if new else "")
            for act in self.actions['FIFTH']:
                self.printActionLine(act, fh)

        if 'SIXTH' in self.actions:
            dealt = 0
            #~ print >>fh, _("*** 6TH STREET ***")
            for player in [x[1] for x in self.players if x[1] in players_who_post_antes]:
                if 'SIXTH' in self.holecards[player]:
                    old = []
                    for street in ('THIRD','FOURTH','FIFTH'):
                        (o,c) = self.holecards[player][street]
                        if o:old.extend(o)
                        if c:old.extend(c)
                    new = self.holecards[player]['SIXTH'][0]
                    dealt += 1
                    if dealt == 1:
                        print >>fh, _("*** 6TH STREET ***")
                    print >>fh, _("Dealt to %s:%s%s") % (player, " [" + " ".join(old) + "] " if old else " ", "[" + " ".join(new) + "]" if new else "")
            for act in self.actions['SIXTH']:
                self.printActionLine(act, fh)

        if 'SEVENTH' in self.actions:
            # OK. It's possible that they're all in at an earlier street, but only closed cards are dealt.
            # Then we have no 'dealt to' lines, no action lines, but still 7th street should appear.
            # The only way I can see to know whether to print this line is by knowing the state of the hand
            # i.e. are all but one players folded; is there an allin showdown; and all that.
            print >>fh, _("*** 7TH STREET ***")
            for player in [x[1] for x in self.players if x[1] in players_who_post_antes]:
                if 'SEVENTH' in self.holecards[player]:
                    old = []
                    for street in ('THIRD','FOURTH','FIFTH','SIXTH'):
                        (o,c) = self.holecards[player][street]
                        if o:old.extend(o)
                        if c:old.extend(c)
                    new = self.holecards[player]['SEVENTH'][0]
                    if new:
                        print >>fh, _("Dealt to %s:%s%s") % (player, " [" + " ".join(old) + "] " if old else " ", "[" + " ".join(new) + "]" if new else "")
            for act in self.actions['SEVENTH']:
                self.printActionLine(act, fh)

        #Some sites don't have a showdown section so we have to figure out if there should be one
        # The logic for a showdown is: at the end of river action there are at least two players in the hand
        # we probably don't need a showdown section in pseudo stars format for our filtering purposes
        if 'SHOWDOWN' in self.actions:
            print >>fh, _("*** SHOW DOWN ***")
            # TODO: print showdown lines.

        # Current PS format has the lines:
        # Uncalled bet ($111.25) returned to s0rrow
        # s0rrow collected $5.15 from side pot
        # stervels: shows [Ks Qs] (two pair, Kings and Queens)
        # stervels collected $45.35 from main pot
        # Immediately before the summary.
        # The current importer uses those lines for importing winning rather than the summary
        for name in self.pot.returned:
            print >>fh, _("Uncalled bet ($%s) returned to %s" %(self.pot.returned[name],name))
        for entry in self.collected:
            print >>fh, _("%s collected $%s from x pot" %(entry[0], entry[1]))

        print >>fh, _("*** SUMMARY ***")
        print >>fh, "%s | Rake $%.2f" % (self.pot, self.rake)
        #print >>fh, _("Total pot $%s | Rake $%.2f" % (self.totalpot, self.rake)) # TODO: side pots

        board = []
        for s in self.board.values():
            board += s
        if board:   # sometimes hand ends preflop without a board
            print >>fh, _("Board [%s]" % (" ".join(board)))

        for player in [x for x in self.players if x[1] in players_who_post_antes]:
            seatnum = player[0]
            name = player[1]
            if name in self.collectees and name in self.shown:
                print >>fh, _("Seat %d: %s showed [%s] and won ($%s)" % (seatnum, name, " ".join(self.holecards[name]), self.collectees[name]))
            elif name in self.collectees:
                print >>fh, _("Seat %d: %s collected ($%s)" % (seatnum, name, self.collectees[name]))
            elif name in self.shown:
                print >>fh, _("Seat %d: %s showed [%s]" % (seatnum, name, " ".join(self.holecards[name])))
            elif name in self.folded:
                print >>fh, _("Seat %d: %s folded" % (seatnum, name))
            else:
                print >>fh, _("Seat %d: %s mucked" % (seatnum, name))

        print >>fh, "\n\n"



class Pot(object):


    def __init__(self):
        self.contenders = set()
        self.committed = {}
        self.total = None
        self.returned = {}
    
    def addPlayer(self,player):
        self.committed[player] = Decimal(0)
    
    def addFold(self, player):
        # addFold must be called when a player folds
        self.contenders.discard(player)
        
    def addMoney(self, player, amount):
        # addMoney must be called for any actions that put money in the pot, in the order they occur
        self.contenders.add(player)
        self.committed[player] += amount

    def end(self):
        self.total = sum(self.committed.values())
        
        # Return any uncalled bet.
        committed = sorted([ (v,k) for (k,v) in self.committed.items()])
        lastbet = committed[-1][0] - committed[-2][0]
        if lastbet > 0: # uncalled
            returnto = committed[-1][1]
            #print "DEBUG: returning %f to %s" % (lastbet, returnto)
            self.total -= lastbet
            self.committed[returnto] -= lastbet
            self.returned[returnto] = lastbet


        # Work out side pots
        commitsall = sorted([(v,k) for (k,v) in self.committed.items() if v >0])

        self.pots = []
        while len(commitsall) > 0:
            commitslive = [(v,k) for (v,k) in commitsall if k in self.contenders]
            v1 = commitslive[0][0]        
            self.pots += [sum([min(v,v1) for (v,k) in commitsall])]
            commitsall = [((v-v1),k) for (v,k) in commitsall if v-v1 >0]

        # TODO: I think rake gets taken out of the pots.
        # so it goes:
        # total pot x. main pot y, side pot z. | rake r
        # and y+z+r = x
        # for example:
        # Total pot $124.30 Main pot $98.90. Side pot $23.40. | Rake $2
        
    def __str__(self):
        if self.total is None:
            print "call Pot.end() before printing pot total"
            # NB if I'm sure end() is idempotent, call it here.
            raise FpdbParseError
        

        
        if len(self.pots) == 1: # (only use Total pot)
            return "Total pot $%.2f" % (self.total,)
        elif len(self.pots) == 2:
            return "Total pot $%.2f Main pot $%.2f. Side pot $%2.f." % (self.total, self.pots[0], self.pots[1])
        elif len(self.pots) == 3:
            return "Total pot $%.2f Main pot $%.2f. Side pot-1 $%2.2f. Side pot-2 $%.2f." % (self.total, self.pots[0], self.pots[1], self.pots[2])
        elif len(self.pots) == 0:
            # no small blind and walk in bb (hopefully)
            return "Total pot $%.2f" % (self.total,)
        else:
            return ("too many pots.. no small blind and walk in bb?. self.pots: %s" %(self.pots))
            # I don't know stars format for a walk in the bb when sb doesn't post.
            # The thing to do here is raise a Hand error like fpdb import does and file it into errors.txt






def assemble(cnxn, handid):
    c = cnxn.cursor()
    
    # We need the following for the Hand.__init__
    c.execute("""
select
    s.name,
    g.category,
    g.base,
    g.type,
    g.limitType,
    g.hilo,
    g.smallBlind / 100.0,
    g.bigBlind / 100.0 ,
    g.smallBet / 100.0,
    g.bigBet / 100.0,
    s.currency,
    (bc.card1value,bc.card1suit),
    (bc.card2value,bc.card2suit),
    (bc.card3value,bc.card3suit),
    (bc.card4value,bc.card4suit),
    (bc.card5value,bc.card5suit)
from
    hands as h,
    boardcards as bc,
    sites as s,
    gametypes as g,
    handsplayers as hp,
    players as p
where
    h.id = %(handid)s
and bc.handid = h.id
and g.id = h.gametypeid
and hp.handid = h.id
and p.id = hp.playerid
and s.id = p.siteid
limit 1""", {'handid':handid})
    #TODO: siteid should be in hands table - we took the scenic route through players here.
    res = c.fetchone()
    gametype = {'category':res[1],'base':res[2],'type':res[3],'limitType':res[4],'hilo':res[5],'sb':res[6],'bb':res[7], 'currency':res[10]}
    h = HoldemOmahaHand(hhc = None, sitename=res[0], gametype = gametype, handText=None, builtFrom = "DB", handid=handid)
    print res[11:16]
    #[Card.valueSuitFromCard(x) for x in cards]
    
    
    #TODO : doesn't look like this is in the database; don't like the way Hand requires it
    h.hero = 'mcturnbull'
    
    # HandInfo : HID, TABLE
    # BUTTON - why is this treated specially in Hand?
    # answer: it is written out in hand histories
    # still, I think we should record all the active seat positions in a seat_order array
    c.execute("""
SELECT
    h.sitehandno as hid,
    h.tablename as table,
    h.handstart as starttime
FROM
    hands as h
WHERE h.id = %(handid)s
""", {'handid':handid})
    res = c.fetchone()
    h.handid = res[0]
    h.tablename = res[1]
    h.starttime = res[2] # automatically a datetime
    
    # PlayerStacks
    c.execute("""
SELECT
    hp.seatno,
    p.name,
    round(hp.startcash / 100.0,2) as chips,
    (hp.card1,hp.card2) as hole
FROM
    handsplayers as hp,
    players as p
WHERE
    hp.handid = %(handid)s
and p.id = hp.playerid
""", {'handid':handid})
    for (seat, name, chips, cards) in c.fetchall():
        h.addPlayer(seat,name,chips)
        h.addHoleCards([Card.valueSuitFromCard(x) for x in cards],name)
    
    # actions
    c.execute("""
SELECT
    (ha.street,ha.actionno) as actnum,
    p.name,
    ha.street,
    ha.action,
    ha.allin,
    ha.amount / 100.0
FROM
    handsplayers as hp,
    handsactions as ha,
    players as p
WHERE
    hp.handid = %(handid)s
and ha.handsplayerid = hp.id
and p.id = hp.playerid
ORDER BY
    ha.street,ha.actionno
""", {'handid':handid})
    res = c.fetchall()
    for (actnum,player, streetnum, act, allin, amount) in res:
        act=act.strip()
        street = h.streetList[streetnum+2]
        if act==u'blind':
            h.addBlind(player, 'big blind', amount)
            # TODO: The type of blind is not recorded in the DB.
            # TODO: preflop street name anomalies in Hand
        elif act==u'fold':
            h.addFold(street,player)
        elif act==u'call':
            h.addCall(street,player,amount)
        elif act==u'bet':
            h.addBet(street,player,amount)
        elif act==u'check':
            h.addCheck(street,player)
        elif act==u'unbet':
            pass
        else:
            print act, player, streetnum, allin, amount
            # TODO : other actions
    #hhc.readCollectPot(self)
    #hhc.readShowdownActions(self)
    #hc.readShownCards(self)
    h.totalPot()
    h.rake = h.totalpot - h.totalcollected
    

    return h

