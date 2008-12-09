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
from decimal import Decimal
import operator
from xml.dom.minidom import Node
from pokereval import PokerEval

class HandHistoryConverter:
    eval = PokerEval()
    def __init__(self, config, file, sitename):
        print "HandHistory init called"

        self.c         = config
        self.sitename  = sitename
        self.obs       = ""             # One big string
        self.filetype  = "text"
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
        if not self.sanityCheck():
            print "Cowardly refusing to continue after failed sanity check"
            return
        self.readFile(self.file)
        self.gametype = self.determineGameType()
        self.hands = self.splitFileIntoHands()
        for hand in self.hands:
            self.readHandInfo(hand)
            self.readPlayerStacks(hand)
            self.markStreets(hand)
            self.readBlinds(hand)
            self.readHeroCards(hand) # want to generalise to draw games
            self.readCommunityCards(hand) # read community cards
            self.readShowdownActions(hand)
            # Read action (Note: no guarantee this is in hand order.
            for street in hand.streets.groupdict():
                self.readAction(hand, street)

            self.readCollectPot(hand)

            # finalise it (total the pot)
            hand.totalPot()
            self.getRake(hand)
            
            if(hand.involved == True):
                #self.writeHand("output file", hand)
                hand.printHand()
            else:
                pass #Don't write out observed hands

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
    def setFileType(self, filetype = "text"):
        self.filetype = filetype

    def splitFileIntoHands(self):
        hands = []
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
            infile=open(filename, "rU")
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
    
        self.streets = None # A MatchObject using a groupnames to identify streets.
        self.streetList = ['BLINDS','PREFLOP','FLOP','TURN','RIVER'] # a list of the observed street names in order
        self.actions = {}
    
        self.handid = 0
        self.sb = gametype[3]
        self.bb = gametype[4]
        self.tablename = "Slartibartfast"
        self.maxseats = 10
        self.counted_seats = 0
        self.buttonpos = 0
        self.seating = []
        self.players = []
        self.posted = []
        self.involved = True
        
        self.hero = "Hiro"
        self.holecards = {} # dict from player names to lists of hole cards
        self.board = {}     # dict from street names to community cards
        self.collected = {} # dict from player names to amounts collected
        
        self.action = []
        self.totalpot = None
        self.rake = None
        
        self.bets = {}
        self.lastBet = {}
        for street in self.streetList:
            self.bets[street] = {}
            self.lastBet[street] = 0
            
    def addPlayer(self, seat, name, chips):
        """seat, an int indicating the seat
        name, the player name
        chips, the chips the player has at the start of the hand"""
        #self.players.append(name)
        self.players.append([seat, name, chips])
        self.holecards[name] = []
        #self.startChips[name] = chips
        #self.endChips[name] = chips
        #self.winners[name] = 0
        for street in self.streetList:
            self.bets[street][name] = []


    def addHoleCards(self, cards, player=None): # generalise to add hole cards for a specific seat or player
        for c in cards:
            self.holecards[player].append(self.card(c))


    def discardHoleCards(self, cards, player=None):
        if seat is None:
            #raise something
            pass
        for card in cards:
            try:
                self.holecards[player].remove(card)
            except ValueError:
                print "tried to discard a card player apparently didn't have"

    def setCommunityCards(self, street, cards):
        self.board[street] = [self.card(c) for c in cards]
        print self.board[street]

    def card(self,c):
        """upper case the ranks but not suits, 'atjqk' => 'ATJQK'"""
        # don't know how to make this 'static'
        for k,v in self.UPS.items():
            c = c.replace(k,v)
        return c

    def addBlind(self, player, amount):
        # if player is None, it's a missing small blind.
        if player is not None:
            self.bets['PREFLOP'][player].append(Decimal(amount))
        self.lastBet['PREFLOP'] = Decimal(amount)
        self.posted += [player]
        

    #def addFold(self, street, player=None):
        ## Called when a player folds.
        #self.bets[street][player].append(None)

    #def addCheck(self, street, player=None):
        #self.bets[street][player].append(0)

    def addCall(self, street, player=None, amount=None):
        # Potentially calculate the amount of the call if not supplied
        # corner cases include if player would be all in
        if amount is not None:
            self.bets[street][player].append(Decimal(amount))
            #self.lastBet[street] = Decimal(amount)
            self.actions[street] += [[player, 'calls', amount]]
        
    def addRaiseTo(self, street, player, amountTo):
        # Given only the amount raised to, the amount of the raise can be calculated by
        # working out how much this player has already in the pot 
        #   (which is the sum of self.bets[street][player])
        # and how much he needs to call to match the previous player 
        #   (which is tracked by self.lastBet)
        committedThisStreet = reduce(operator.add, self.bets[street][player], 0)
        amountToCall = self.lastBet[street] - committedThisStreet
        self.lastBet[street] = Decimal(amountTo)
        amountBy = Decimal(amountTo) - amountToCall
        self.bets[street][player].append(amountBy+amountToCall)
        self.actions[street] += [[player, 'raises', amountBy, amountTo]]
        
    def addBet(self, street, player=None, amount=0):
        self.bets[street][name].append(Decimal(amount))
        self.orderedBets[street].append(Decimal(amount))
        self.actions[street] += [[player, 'bets', amount]]

    def addCollectPot(self,player, pot):
        if player not in self.collected:
            self.collected[player] = pot
        else:
            # possibly lines like "p collected $ from pot" appear during the showdown
            # but they are usually unique in the summary.
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
                    


    def printHand(self):
        # PokerStars format.
        print "### DEBUG ###"
        print "%s Game #%s: %s ($%s/$%s) - %s" %(self.sitename, self.handid, "XXXXhand.gametype", self.sb, self.bb, self.starttime)
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
        print "Dealt to %s [%s %s]" %(self.hero , self.holecards[self.hero][0], self.holecards[self.hero][1])

        if 'PREFLOP' in self.actions:
            for act in self.actions['PREFLOP']:
                self.printActionLine(act)

        if 'FLOP' in self.actions:
            print "*** FLOP *** [%s %s %s]" %(self.streets.group("FLOP1"), self.streets.group("FLOP2"), self.streets.group("FLOP3"))
            for act in self.actions['FLOP']:
                self.printActionLine(act)

        if 'TURN' in self.actions:
            print "*** TURN *** [%s %s %s] [%s]" %(self.streets.group("FLOP1"), self.streets.group("FLOP2"), self.streets.group("FLOP3"), self.streets.group("TURN1"))
            for act in self.actions['TURN']:
                self.printActionLine(act)

        if 'RIVER' in self.actions:
            print "*** RIVER *** [%s %s %s %s] [%s]" %(self.streets.group("FLOP1"), self.streets.group("FLOP2"), self.streets.group("FLOP3"), self.streets.group("TURN1"), self.streets.group("RIVER1"))
            for act in self.actions['RIVER']:
                self.printActionLine(act)
                
                
        #Some sites don't have a showdown section so we have to figure out if there should be one
        # The logic for a showdown is: at the end of river action there are at least two players in the hand
        if 'SHOWDOWN' in self.actions:
            print "*** SHOW DOWN ***"
            print "what do they show"
        
        print "*** SUMMARY ***"
        print "Total pot $%s | Rake $%.2f)" % (self.totalpot, self.rake) # TODO side pots
        print "Board [%s %s %s %s %s]" % (self.streets.group("FLOP1"), self.streets.group("FLOP2"), self.streets.group("FLOP3"), self.streets.group("TURN1"), self.streets.group("RIVER1"))
        
        #print self.board
        for player in self.players:
            if player[1] in self.collected and self.holecards[player[1]]:
                print "Seat %d: %s showed [%s %s] and won ($%s)" % (player[0], player[1], self.holecards[player[1]][0], self.holecards[player[1]][1], self.collected[player[1]])
            elif player[1] in self.collected:
                print "Seat %d: %s collected ($%s)" % (player[0], player[1], self.collected[player[1]])
            elif self.holecards[player[1]]:
                print "Seat %d: %s showed [%s %s]" % (player[0], player[1], self.holecards[player[1]][0], self.holecards[player[1]][1])
            else:
                print "Seat %d: %s folded (or mucked..)" % (player[0], player[1])
            
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
        if act[1] == 'raises':
            print "%s: %s $%s to $%s" %(act[0], act[1], act[2], act[3])

    # going to use pokereval to figure out hands at some point.
    # these functions are copied from pokergame.py
    def bestHand(self, side, cards):
        #if self.variant == "omaha" or self.variant == "omaha8":
        #hand = self.serial2player[serial].hand.tolist(True)
        #board = self.board.tolist(True)
        #else:
        #hand = hand.tolist(True) + board.tolist(True)
        #board = []
        print cards
        return HandHistoryConverter.eval.best('hi', cards, [])

    # from pokergame.py
    def bestHandValue(self, side, serial):
        (value, cards) = self.bestHand(side, serial)
        return value

    # from pokergame.py
    def readableHandValueLong(self, side, value, cards):
        if value == "NoPair":
            if side == "low":
                if cards[0][0] == '5':
                    return _("The wheel")
                else:
                    return join(map(lambda card: card[0], cards), ", ")
            else:
                return _("High card %(card)s") % { 'card' : _(letter2name[cards[0][0]]) }
        elif value == "OnePair":
            return _("A pair of %(card)s") % { 'card' : _(letter2names[cards[0][0]]) } + _(", %(card)s kicker") % { 'card' : _(letter2name[cards[2][0]]) }
        elif value == "TwoPair":
            return _("Two pairs %(card1)s and %(card2)s") % { 'card1' : _(letter2names[cards[0][0]]), 'card2' : _(letter2names[cards[2][0]]) } + _(", %(card)s kicker") % { 'card' : _(letter2name[cards[4][0]]) }
        elif value == "Trips":
            return _("Three of a kind %(card)s") % { 'card' : _(letter2names[cards[0][0]]) } + _(", %(card)s kicker") % { 'card' : _(letter2name[cards[3][0]]) }
        elif value == "Straight":
            return _("Straight %(card1)s to %(card2)s") % { 'card1' : _(letter2name[cards[0][0]]), 'card2' : _(letter2name[cards[4][0]]) }
        elif value == "Flush":
            return _("Flush %(card)s high") % { 'card' : _(letter2name[cards[0][0]]) }
        elif value == "FlHouse":
            return _("%(card1)ss full of %(card2)ss") % { 'card1' : _(letter2name[cards[0][0]]), 'card2' : _(letter2name[cards[3][0]]) }
        elif value == "Quads":
            return _("Four of a kind %(card)s") % { 'card' : _(letter2names[cards[0][0]]) } + _(", %(card)s kicker") % { 'card' : _(letter2name[cards[4][0]]) }
        elif value == "StFlush":
            if letter2name[cards[0][0]] == 'Ace':
                return _("Royal flush")
            else:
                return _("Straight flush %(card)s high") % { 'card' : _(letter2name[cards[0][0]]) }
        return value