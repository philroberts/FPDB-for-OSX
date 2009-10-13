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

class DerivedStats():
    def __init__(self, hand):
        self.hand = hand

        self.hands = {}
        self.handsplayers = {}

    def getStats(self, hand):
        
        for player in hand.players:
            self.handsplayers[player[1]] = {}

        self.assembleHands(self.hand)
        self.assembleHandsPlayers(self.hand)
        
        print "hands =", self.hands
        print "handsplayers =", self.handsplayers

    def getHands(self):
        return self.hands

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
        boardcards = hand.board['FLOP'] + hand.board['TURN'] + hand.board['RIVER'] + [u'0x', u'0x', u'0x', u'0x', u'0x']
        cards = [Card.encodeCard(c) for c in boardcards[0:5]]
        self.hands['boardcard1'] = cards[0]
        self.hands['boardcard2'] = cards[1]
        self.hands['boardcard3'] = cards[2]
        self.hands['boardcard4'] = cards[3]
        self.hands['boardcard5'] = cards[4]

        #print "DEBUG: self.getStreetTotals = (%s, %s, %s, %s, %s)" %  hand.getStreetTotals()
        #FIXME: Pot size still in decimal, needs to be converted to cents
        (self.hands['street1Pot'],
         self.hands['street2Pot'],
         self.hands['street3Pot'],
         self.hands['street4Pot'],
         self.hands['showdownPot']) = hand.getStreetTotals()

        self.vpip(hand) # Gives playersVpi (num of players vpip)
        self.playersAtStreetX(hand) # Gives playersAtStreet1..4 and Showdown

        # comment TEXT,
        # commentTs DATETIME

    def assembleHandsPlayers(self, hand):
        self.vpip(self.hand)
        for i, street in enumerate(hand.actionStreets[1:]):
            self.aggr(self.hand, i)

    def vpip(self, hand):
        vpipers = set()
        for act in hand.actions[hand.actionStreets[1]]:
            if act[1] in ('calls','bets', 'raises'):
                vpipers.add(act[0])

        for player in hand.players:
            if player[1] in vpipers:
                self.handsplayers[player[1]]['vpip'] = True
            else:
                self.handsplayers[player[1]]['vpip'] = False
        self.hands['playersVpi'] = len(vpipers)

    def playersAtStreetX(self, hand):
        """ playersAtStreet1 SMALLINT NOT NULL,   /* num of players seeing flop/street4/draw1 */"""
        # self.actions[street] is a list of all actions in a tuple, contining the player name first
        # [ (player, action, ....), (player2, action, ...) ]
        # The number of unique players in the list per street gives the value for playersAtStreetXXX

        self.hands['playersAtStreet1']  = 0
        self.hands['playersAtStreet2']  = 0
        self.hands['playersAtStreet3']  = 0
        self.hands['playersAtStreet4']  = 0
        self.hands['playersAtShowdown'] = 0

        for street in hand.actionStreets:
            actors = {}
            for act in a[street]:
                actors[act[0]] = 1
            #print "len(actors.keys(%s)): %s" % ( street, len(actors.keys()))
            if hand.gametype['base'] in ("hold"):
                if street in "FLOP": self.hands['playersAtStreet1'] = len(actors.keys())
                elif street in "TURN": self.hands['playersAtStreet2'] = len(actors.keys())
                elif street in "RIVER": self.hands['playersAtStreet3'] = len(actors.keys())
            elif hand.gametype['base'] in ("stud"):
                if street in "FOURTH": self.hands['playersAtStreet1'] = len(actors.keys())
                elif street in "FIFTH": self.hands['playersAtStreet2'] = len(actors.keys())
                elif street in "SIXTH": self.hands['playersAtStreet3'] = len(actors.keys())
                elif street in "SEVENTH": self.hands['playersAtStreet4'] = len(actors.keys())
            elif hand.gametype['base'] in ("draw"):
                if street in "DRAWONE": self.hands['playersAtStreet1'] = len(actors.keys())
                elif street in "DRAWTWO": self.hands['playersAtStreet2'] = len(actors.keys())
                elif street in "DRAWTHREE": self.hands['playersAtStreet3'] = len(actors.keys())

        #Need playersAtShowdown


    def streetXRaises(self, hand):
        # self.actions[street] is a list of all actions in a tuple, contining the action as the second element
        # [ (player, action, ....), (player2, action, ...) ]
        # No idea what this value is actually supposed to be
        # In theory its "num small bets paid to see flop/street4, including blind" which makes sense for limit. Not so useful for nl
        # Leaving empty for the moment,
        self.hands['street0Raises'] = 0 # /* num small bets paid to see flop/street4, including blind */
        self.hands['street1Raises'] = 0 # /* num small bets paid to see turn/street5 */
        self.hands['street2Raises'] = 0 # /* num big bets paid to see river/street6 */
        self.hands['street3Raises'] = 0 # /* num big bets paid to see sd/street7 */
        self.hands['street4Raises'] = 0 # /* num big bets paid to see showdown */

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
