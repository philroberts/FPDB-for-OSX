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

DEBUG = True

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
            self.handsplayers[player[1]]['street4Seen'] = False
            self.handsplayers[player[1]]['street4Aggr'] = False

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

        # comment TEXT,
        # commentTs DATETIME

    def assembleHandsPlayers(self, hand):
        #street0VPI/vpip already called in Hand
        #hand.players = [[seat, name, chips],[seat, name, chips]]
        for player in hand.players:
            self.handsplayers[player[1]]['seatNo'] = player[0]
            self.handsplayers[player[1]]['startCash'] = player[2]

        # Winnings is a non-negative value of money collected from the pot, which already includes the
        # rake taken out. hand.collectees is Decimal, database requires cents
        for player in hand.collectees:
            self.handsplayers[player]['winnings'] = int(100 * hand.collectees[player])
            #FIXME: This is pretty dodgy, rake = hand.rake/#collectees
            # You can really only pay rake when you collect money, but
            # different sites calculate rake differently.
            # Should be fine for split-pots, but won't be accurate for multi-way pots
            self.handsplayers[player]['rake'] = int(100* hand.rake)/len(hand.collectees)

        for i, street in enumerate(hand.actionStreets[2:]):
            self.seen(self.hand, i+1)

        for i, street in enumerate(hand.actionStreets[1:]):
            self.aggr(self.hand, i)

        #default_holecards = ["Xx", "Xx", "Xx", "Xx"]
        #if hand.gametype['base'] == "hold":
        #    pass
        #elif hand.gametype['base'] == "stud":
        #    pass
        #else:
        #    # Flop hopefully...
        #    pass

        for street in hand.holeStreets:
            for player in hand.players:
                for i in range(1,8): self.handsplayers[player[1]]['card%d' % i] = 0
                #print "DEBUG: hand.holecards[%s]: %s" % (street, hand.holecards[street])
                if player[1] in hand.holecards[street].keys() and hand.gametype['base'] == "hold":
                    self.handsplayers[player[1]]['card1'] = Card.encodeCard(hand.holecards[street][player[1]][1][0])
                    self.handsplayers[player[1]]['card2'] = Card.encodeCard(hand.holecards[street][player[1]][1][1])
                    try:
                        self.handsplayers[player[1]]['card3'] = Card.encodeCard(hand.holecards[street][player[1]][1][2])
                        self.handsplayers[player[1]]['card4'] = Card.encodeCard(hand.holecards[street][player[1]][1][3])
                    except IndexError:
                        # Just means no player cards for that street/game - continue
                        pass 

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
        self.hands['playersAtShowdown'] = len(set.union(self.pfba(actions) - self.pfba(actions, l=('folds',)),  alliners))

    def streetXRaises(self, hand):
        # self.actions[street] is a list of all actions in a tuple, contining the action as the second element
        # [ (player, action, ....), (player2, action, ...) ]
        # No idea what this value is actually supposed to be
        # In theory its "num small bets paid to see flop/street4, including blind" which makes sense for limit. Not so useful for nl
        # Leaving empty for the moment,

        for i in range(5): self.hands['street%dRaises' % i] = 0

        for (i, street) in enumerate(hand.actionStreets[1:]):
            self.hands['street%dRaises' % i] = len(filter( lambda action: action[1] in ('raises','bets'), hand.actions[street]))

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
