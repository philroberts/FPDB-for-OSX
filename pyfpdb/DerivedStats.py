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

    def assembleHands(self, hand):
        self.hands['tableName']  = hand.tablename
        self.hands['siteHandNo'] = hand.handid
        self.hands['gametypeId'] = None                     # Leave None, handled later after checking db
        self.hands['handStart']  = hand.starttime           # format this!
        self.hands['importTime'] = None
        self.hands['seats']      = self.countPlayers(hand) 
        self.hands['maxSeats']   = hand.maxseats
        self.hands['boardcard1'] = None
        self.hands['boardcard2'] = None
        self.hands['boardcard3'] = None
        self.hands['boardcard4'] = None
        self.hands['boardcard5'] = None

        boardCard = 1
        for street in hand.communityStreets:
            for card in hand.board[street]:
                self.hands['boardcard%s' % str(boardCard)] = Card.encodeCard(card)
                boardCard += 1

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