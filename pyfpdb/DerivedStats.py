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

#fpdb modules
import Card
from decimal import Decimal

DEBUG = False

if DEBUG:
    import pprint
    pp = pprint.PrettyPrinter(indent=4)


class DerivedStats():
    def __init__(self, hand):
        self.hand = hand

        self.hands = {}
        self.handsplayers = {}

    def getStats(self, hand):
        
        for player in hand.players:
            self.handsplayers[player[1]] = {}
            #Init vars that may not be used, but still need to be inserted.
            # All stud street4 need this when importing holdem
            self.handsplayers[player[1]]['winnings']    = 0
            self.handsplayers[player[1]]['rake']        = 0
            self.handsplayers[player[1]]['totalProfit'] = 0
            self.handsplayers[player[1]]['street4Seen'] = False
            self.handsplayers[player[1]]['street4Aggr'] = False
            self.handsplayers[player[1]]['wonWhenSeenStreet1'] = 0.0
            self.handsplayers[player[1]]['sawShowdown'] = False
            self.handsplayers[player[1]]['wonAtSD']     = 0.0
            for i in range(5): 
                self.handsplayers[player[1]]['street%dCalls' % i] = 0
                self.handsplayers[player[1]]['street%dBets' % i] = 0
            for i in range(1,5):
                self.handsplayers[player[1]]['street%dCBChance' %i] = False
                self.handsplayers[player[1]]['street%dCBDone' %i] = False

            #FIXME - Everything below this point is incomplete.
            self.handsplayers[player[1]]['position']            = 2
            self.handsplayers[player[1]]['tourneyTypeId']       = 1
            self.handsplayers[player[1]]['startCards']          = 0
            self.handsplayers[player[1]]['street0_3BChance']    = False
            self.handsplayers[player[1]]['street0_3BDone']      = False
            self.handsplayers[player[1]]['stealAttemptChance']  = False
            self.handsplayers[player[1]]['stealAttempted']      = False
            self.handsplayers[player[1]]['foldBbToStealChance'] = False
            self.handsplayers[player[1]]['foldBbToStealChance'] = False
            self.handsplayers[player[1]]['foldSbToStealChance'] = False
            self.handsplayers[player[1]]['foldedSbToSteal']     = False
            self.handsplayers[player[1]]['foldedBbToSteal']     = False
            for i in range(1,5):
                self.handsplayers[player[1]]['otherRaisedStreet%d' %i]          = False
                self.handsplayers[player[1]]['foldToOtherRaisedStreet%d' %i]    = False
                self.handsplayers[player[1]]['foldToStreet%dCBChance' %i]       = False
                self.handsplayers[player[1]]['foldToStreet%dCBDone' %i]         = False
                self.handsplayers[player[1]]['street%dCheckCallRaiseChance' %i] = False
                self.handsplayers[player[1]]['street%dCheckCallRaiseDone' %i]   = False

        self.assembleHands(self.hand)
        self.assembleHandsPlayers(self.hand)


        if DEBUG:
            print "Hands:"
            pp.pprint(self.hands)
            print "HandsPlayers:"
            pp.pprint(self.handsplayers)

    def getHands(self):
        return self.hands

    def getHandsPlayers(self):
        return self.handsplayers

    def assembleHands(self, hand):
        self.hands['tableName']  = hand.tablename
        self.hands['siteHandNo'] = hand.handid
        self.hands['gametypeId'] = None                     # Leave None, handled later after checking db
        self.hands['handStart']  = hand.starttime           # format this!
        self.hands['importTime'] = None
        self.hands['seats']      = self.countPlayers(hand) 
        self.hands['maxSeats']   = hand.maxseats
        self.hands['texture']    = None                     # No calculation done for this yet.

        # This (i think...) is correct for both stud and flop games, as hand.board['street'] disappears, and
        # those values remain default in stud.
        boardcards = []
        for street in hand.communityStreets:
            boardcards += hand.board[street]
        boardcards += [u'0x', u'0x', u'0x', u'0x', u'0x']
        cards = [Card.encodeCard(c) for c in boardcards[0:5]]
        self.hands['boardcard1'] = cards[0]
        self.hands['boardcard2'] = cards[1]
        self.hands['boardcard3'] = cards[2]
        self.hands['boardcard4'] = cards[3]
        self.hands['boardcard5'] = cards[4]

        #print "DEBUG: self.getStreetTotals = (%s, %s, %s, %s, %s)" %  hand.getStreetTotals()
        totals = hand.getStreetTotals()
        totals = [int(100*i) for i in totals]
        self.hands['street1Pot']  = totals[0]
        self.hands['street2Pot']  = totals[1]
        self.hands['street3Pot']  = totals[2]
        self.hands['street4Pot']  = totals[3]
        self.hands['showdownPot'] = totals[4]

        self.vpip(hand) # Gives playersVpi (num of players vpip)
        #print "DEBUG: vpip: %s" %(self.hands['playersVpi'])
        self.playersAtStreetX(hand) # Gives playersAtStreet1..4 and Showdown
        #print "DEBUG: playersAtStreet 1:'%s' 2:'%s' 3:'%s' 4:'%s'" %(self.hands['playersAtStreet1'],self.hands['playersAtStreet2'],self.hands['playersAtStreet3'],self.hands['playersAtStreet4'])
        self.streetXRaises(hand) # Empty function currently

    def assembleHandsPlayers(self, hand):
        #street0VPI/vpip already called in Hand
        # sawShowdown is calculated in playersAtStreetX, as that calculation gives us a convenient list of names

        #hand.players = [[seat, name, chips],[seat, name, chips]]
        for player in hand.players:
            self.handsplayers[player[1]]['seatNo'] = player[0]
            self.handsplayers[player[1]]['startCash'] = int(100 * Decimal(player[2]))

        for i, street in enumerate(hand.actionStreets[2:]):
            self.seen(self.hand, i+1)

        for i, street in enumerate(hand.actionStreets[1:]):
            self.aggr(self.hand, i)
            self.calls(self.hand, i)
            self.bets(self.hand, i)

        # Winnings is a non-negative value of money collected from the pot, which already includes the
        # rake taken out. hand.collectees is Decimal, database requires cents
        for player in hand.collectees:
            self.handsplayers[player]['winnings'] = int(100 * hand.collectees[player])
            #FIXME: This is pretty dodgy, rake = hand.rake/#collectees
            # You can really only pay rake when you collect money, but
            # different sites calculate rake differently.
            # Should be fine for split-pots, but won't be accurate for multi-way pots
            self.handsplayers[player]['rake'] = int(100* hand.rake)/len(hand.collectees)
            if self.handsplayers[player]['street1Seen'] == True:
                self.handsplayers[player]['wonWhenSeenStreet1'] = 1.0
            if self.handsplayers[player]['sawShowdown'] == True:
                self.handsplayers[player]['wonAtSD'] = 1.0

        for player in hand.pot.committed:
            self.handsplayers[player]['totalProfit'] = int(self.handsplayers[player]['winnings'] - (100*hand.pot.committed[player]))

        self.calcCBets(hand)

        for player in hand.players:
            hcs = hand.join_holecards(player[1], asList=True)
            hcs = hcs + [u'0x', u'0x', u'0x', u'0x', u'0x']
            #for i, card in enumerate(hcs[:7], 1): #Python 2.6 syntax
            #    self.handsplayers[player[1]]['card%s' % i] = Card.encodeCard(card)
            for i, card in enumerate(hcs[:7]):
                self.handsplayers[player[1]]['card%s' % (i+1)] = Card.encodeCard(card)


        # position,
            #Stud 3rd street card test
            # denny501: brings in for $0.02
            # s0rrow: calls $0.02
            # TomSludge: folds
            # Soroka69: calls $0.02
            # rdiezchang: calls $0.02           (Seat 8)
            # u.pressure: folds                 (Seat 1)
            # 123smoothie: calls $0.02
            # gashpor: calls $0.02

        # Additional stats
        # 3betSB, 3betBB
        # Squeeze, Ratchet?


    def getPosition(hand, seat):
        """Returns position value like 'B', 'S', 0, 1, ..."""
        # Flop/Draw games with blinds
        # Need a better system???
        # -2 BB - B (all)
        # -1 SB - S (all)
        #  0 Button 
        #  1 Cutoff
        #  2 Hijack

    def assembleHudCache(self, hand):
        pass

    def vpip(self, hand):
        vpipers = set()
        for act in hand.actions[hand.actionStreets[1]]:
            if act[1] in ('calls','bets', 'raises'):
                vpipers.add(act[0])

        self.hands['playersVpi'] = len(vpipers)

        for player in hand.players:
            if player[1] in vpipers:
                self.handsplayers[player[1]]['street0VPI'] = True
            else:
                self.handsplayers[player[1]]['street0VPI'] = False

    def playersAtStreetX(self, hand):
        """ playersAtStreet1 SMALLINT NOT NULL,   /* num of players seeing flop/street4/draw1 */"""
        # self.actions[street] is a list of all actions in a tuple, contining the player name first
        # [ (player, action, ....), (player2, action, ...) ]
        # The number of unique players in the list per street gives the value for playersAtStreetXXX

        # FIXME?? - This isn't couting people that are all in - at least showdown needs to reflect this

        self.hands['playersAtStreet1']  = 0
        self.hands['playersAtStreet2']  = 0
        self.hands['playersAtStreet3']  = 0
        self.hands['playersAtStreet4']  = 0
        self.hands['playersAtShowdown'] = 0

        alliners = set()
        for (i, street) in enumerate(hand.actionStreets[2:]):
            actors = set()
            for action in hand.actions[street]:
                if len(action) > 2 and action[-1]: # allin
                    alliners.add(action[0])
                actors.add(action[0])
            if len(actors)==0 and len(alliners)<2:
                alliners = set()
            self.hands['playersAtStreet%d' % (i+1)] = len(set.union(alliners, actors))

        actions = hand.actions[hand.actionStreets[-1]]
        pas = set.union(self.pfba(actions) - self.pfba(actions, l=('folds',)),  alliners)
        self.hands['playersAtShowdown'] = len(pas)

        if self.hands['playersAtShowdown'] > 1:
            for player in pas:
                self.handsplayers[player]['sawShowdown'] = True

    def streetXRaises(self, hand):
        # self.actions[street] is a list of all actions in a tuple, contining the action as the second element
        # [ (player, action, ....), (player2, action, ...) ]
        # No idea what this value is actually supposed to be
        # In theory its "num small bets paid to see flop/street4, including blind" which makes sense for limit. Not so useful for nl
        # Leaving empty for the moment,

        for i in range(5): self.hands['street%dRaises' % i] = 0

        for (i, street) in enumerate(hand.actionStreets[1:]):
            self.hands['street%dRaises' % i] = len(filter( lambda action: action[1] in ('raises','bets'), hand.actions[street]))

    def calcCBets(self, hand):
        # Continuation Bet chance, action:
        # Had the last bet (initiative) on previous street, got called, close street action
        #   Then no bets before the player with initiatives first action on current street
        # ie. if player on street-1 had initiative
        #                and no donkbets occurred

        # XXX: enumerate(list, start=x) is python 2.6 syntax; 'start'
        # came there
        #for i, street in enumerate(hand.actionStreets[2:], start=1):
        for i, street in enumerate(hand.actionStreets[2:]):
            name = self.lastBetOrRaiser(hand.actionStreets[i+1])
            if name:
                chance = self.noBetsBefore(hand.actionStreets[i+2], name)
                self.handsplayers[name]['street%dCBChance' % (i+1)] = True
                if chance == True:
                    self.handsplayers[name]['street%dCBDone' % (i+1)] = self.betStreet(hand.actionStreets[i+2], name)

    def seen(self, hand, i):
        pas = set()
        for act in hand.actions[hand.actionStreets[i+1]]:
            pas.add(act[0])

        for player in hand.players:
            if player[1] in pas:
                self.handsplayers[player[1]]['street%sSeen' % i] = True
            else:
                self.handsplayers[player[1]]['street%sSeen' % i] = False

    def aggr(self, hand, i):
        aggrers = set()
        for act in hand.actions[hand.actionStreets[i]]:
            if act[1] in ('completes', 'raises'):
                aggrers.add(act[0])

        for player in hand.players:
            if player[1] in aggrers:
                self.handsplayers[player[1]]['street%sAggr' % i] = True
            else:
                self.handsplayers[player[1]]['street%sAggr' % i] = False

    def calls(self, hand, i):
        callers = []
        for act in hand.actions[hand.actionStreets[i+1]]:
            if act[1] in ('calls'):
                self.handsplayers[act[0]]['street%sCalls' % i] = 1 + self.handsplayers[act[0]]['street%sCalls' % i]

    # CG - I'm sure this stat is wrong
    # Best guess is that raise = 2 bets
    def bets(self, hand, i):
        betters = []
        for act in hand.actions[hand.actionStreets[i+1]]:
            if act[1] in ('bets'):
                self.handsplayers[act[0]]['street%sBets' % i] = 1 + self.handsplayers[act[0]]['street%sBets' % i]

    def countPlayers(self, hand):
        pass

    def pfba(self, actions, f=None, l=None):
        """Helper method. Returns set of PlayersFilteredByActions

        f - forbidden actions
        l - limited to actions
        """
        players = set()
        for action in actions:
            if l is not None and action[1] not in l: continue
            if f is not None and action[1] in f: continue
            players.add(action[0])
        return players

    def noBetsBefore(self, street, player):
        """Returns true if there were no bets before the specified players turn, false otherwise"""
        betOrRaise = False
        for act in self.hand.actions[street]:
            #Must test for player first in case UTG
            if act[0] == player:
                betOrRaise = True
                break
            if act[1] in ('bets', 'raises'):
                break
        return betOrRaise

    def betStreet(self, street, player):
        """Returns true if player bet/raised the street as their first action"""
        betOrRaise = False
        for act in self.hand.actions[street]:
            if act[0] == player and act[1] in ('bets', 'raises'):
                betOrRaise = True
            else:
                break
        return betOrRaise


    def lastBetOrRaiser(self, street):
        """Returns player name that placed the last bet or raise for that street.
            None if there were no bets or raises on that street"""
        lastbet = None
        for act in self.hand.actions[street]:
            if act[1] in ('bets', 'raises'):
                lastbet = act[0]
        return lastbet
