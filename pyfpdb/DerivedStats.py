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

        self.activeSeats                     = 0
        self.position                        = 0
        self.tourneyTypeId                   = 0

        self.HDs                             = 0
        self.street0VPI                      = 0
        self.street0Aggr                     = 0
        self.street0_3BChance                = 0
        self.street0_3BDone                  = 0
        self.street0_4BChance                = 0
        self.street0_4BDone                  = 0

        self.street1Seen                     = 0
        self.street2Seen                     = 0
        self.street3Seen                     = 0
        self.street4Seen                     = 0
        self.sawShowdown                     = 0

        self.street1Aggr                     = 0
        self.street2Aggr                     = 0
        self.street3Aggr                     = 0
        self.street4Aggr                     = 0

        self.otherRaisedStreet1              = 0
        self.otherRaisedStreet2              = 0
        self.otherRaisedStreet3              = 0
        self.otherRaisedStreet4              = 0
        self.foldToOtherRaisedStreet1        = 0
        self.foldToOtherRaisedStreet2        = 0
        self.foldToOtherRaisedStreet3        = 0
        self.foldToOtherRaisedStreet4        = 0
        self.wonWhenSeenStreet1              = 0
        self.wonAtSD                         = 0

        self.stealAttemptChance              = 0
        self.stealAttempted                  = 0
        self.foldBbToStealChance             = 0
        self.foldedBbToSteal                 = 0
        self.foldSbToStealChance             = 0
        self.foldedSbToSteal                 = 0

        self.street1CBChance                 = 0
        self.street1CBDone                   = 0
        self.street2CBChance                 = 0
        self.street2CBDone                   = 0
        self.street3CBChance                 = 0
        self.street3CBDone                   = 0
        self.street4CBChance                 = 0
        self.street4CBDone                   = 0

        self.foldToStreet1CBChance           = 0
        self.foldToStreet1CBDone             = 0
        self.foldToStreet2CBChance           = 0
        self.foldToStreet2CBDone             = 0
        self.foldToStreet3CBChance           = 0
        self.foldToStreet3CBDone             = 0
        self.foldToStreet4CBChance           = 0
        self.foldToStreet4CBDone             = 0

        self.totalProfit                     = 0

        self.street1CheckCallRaiseChance     = 0
        self.street1CheckCallRaiseDone       = 0
        self.street2CheckCallRaiseChance     = 0
        self.street2CheckCallRaiseDone       = 0
        self.street3CheckCallRaiseChance     = 0
        self.street3CheckCallRaiseDone       = 0
        self.street4CheckCallRaiseChance     = 0
        self.street4CheckCallRaiseDone       = 0
        
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
             # texture smallint,
             # playersAtStreet1 SMALLINT NOT NULL,   /* num of players seeing flop/street4 */
                # Needs to be recorded
             # playersAtStreet2 SMALLINT NOT NULL,
                # Needs to be recorded
             # playersAtStreet3 SMALLINT NOT NULL,
                # Needs to be recorded
             # playersAtStreet4 SMALLINT NOT NULL,
                # Needs to be recorded
             # playersAtShowdown SMALLINT NOT NULL,
                # Needs to be recorded
             # street0Raises TINYINT NOT NULL, /* num small bets paid to see flop/street4, including blind */
                # Needs to be recorded
             # street1Raises TINYINT NOT NULL, /* num small bets paid to see turn/street5 */
                # Needs to be recorded
             # street2Raises TINYINT NOT NULL, /* num big bets paid to see river/street6 */
                # Needs to be recorded
             # street3Raises TINYINT NOT NULL, /* num big bets paid to see sd/street7 */
                # Needs to be recorded
             # street4Raises TINYINT NOT NULL, /* num big bets paid to see showdown */
                # Needs to be recorded

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
