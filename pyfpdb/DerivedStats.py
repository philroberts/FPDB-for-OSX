#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Copyright 2008-2011 Carl Gherardi
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
#In the "official" distribution you can find the license in agpl-3.0.txt.

#fpdb modules
import Card
from decimal_wrapper import Decimal

import logging
# logging has been set up in fpdb.py or HUD_main.py, use their settings:
log = logging.getLogger("parser")

class DerivedStats():
    def __init__(self, hand):
        self.hand = hand

        self.hands        = {}
        self.handsplayers = {}
        self.handsactions = {}
        self._initStats = DerivedStats._buildStatsInitializer()

    @staticmethod
    def _buildStatsInitializer():
        init = {}
        #Init vars that may not be used, but still need to be inserted.
        # All stud street4 need this when importing holdem
        init['winnings']    = 0
        init['rake']        = 0
        init['totalProfit'] = 0
        init['street4Aggr'] = False
        init['wonWhenSeenStreet1'] = 0.0
        init['sawShowdown'] = False
        init['wonAtSD']     = 0.0
        init['startCards']  = 0
        init['position']            = 2
        init['street0_3BChance']    = False
        init['street0_3BDone']      = False
        init['street0_4BChance']    = False
        init['street0_4BDone']      = False
        init['street0_C4BChance']   = False
        init['street0_C4BDone']     = False
        init['street0_FoldTo3BChance']= False
        init['street0_FoldTo3BDone']= False
        init['street0_FoldTo4BChance']= False
        init['street0_FoldTo4BDone']= False
        init['street0_SqueezeChance']= False
        init['street0_SqueezeDone'] = False
        init['success_Steal']       = False
        init['raiseToStealChance']  = False
        init['raiseToStealDone']  = False
        init['raiseFirstInChance']  = False
        init['raisedFirstIn']       = False
        init['foldBbToStealChance'] = False
        init['foldSbToStealChance'] = False
        init['foldedSbToSteal']     = False
        init['foldedBbToSteal']     = False
        init['tourneyTypeId']       = None
        init['street1Seen']         = False
        init['street2Seen']         = False
        init['street3Seen']         = False
        init['street4Seen']         = False


        for i in range(5):
            init['street%dCalls' % i] = 0
            init['street%dBets' % i] = 0
            init['street%dRaises' % i] = 0
        for i in range(1,5):
            init['street%dCBChance' %i] = False
            init['street%dCBDone' %i] = False
            init['street%dCheckCallRaiseChance' %i] = False
            init['street%dCheckCallRaiseDone' %i]   = False
            init['otherRaisedStreet%d' %i]          = False
            init['foldToOtherRaisedStreet%d' %i]    = False

        #FIXME - Everything below this point is incomplete.
        init['other3BStreet0']              = False
        init['other4BStreet0']              = False
        init['otherRaisedStreet0']          = False
        init['foldToOtherRaisedStreet0']    = False
        for i in range(1,5):
            init['foldToStreet%dCBChance' %i]       = False
            init['foldToStreet%dCBDone' %i]         = False
        init['wonWhenSeenStreet2'] = 0.0
        init['wonWhenSeenStreet3'] = 0.0
        init['wonWhenSeenStreet4'] = 0.0
        return init

    def getStats(self, hand):
        for player in hand.players:
            self.handsplayers[player[1]] = self._initStats.copy()

        self.assembleHands(self.hand)
        self.assembleHandsPlayers(self.hand)

        if self.hand.saveActions:
            self.assembleHandsActions(self.hand)

    def getHands(self):
        return self.hands

    def getHandsPlayers(self):
        return self.handsplayers

    def getHandsActions(self):
        return self.handsactions

    def assembleHands(self, hand):
        self.hands['tableName']     = hand.tablename
        self.hands['siteHandNo']    = hand.handid
        self.hands['gametypeId']    = None                    # Leave None, handled later after checking db
        self.hands['sessionId']     = None                    # Leave None, added later if caching sessions
        self.hands['gameSessionId'] = None                    # Leave None, added later if caching sessions
        self.hands['startTime']     = hand.startTime          # format this!
        self.hands['importTime']    = None
        self.hands['seats']         = self.countPlayers(hand) 
        self.hands['maxSeats']      = hand.maxseats
        self.hands['texture']       = None                    # No calculation done for this yet.
        self.hands['tourneyId']     = hand.tourneyId

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
        self.streetXRaises(hand)

    def assembleHandsPlayers(self, hand):
        #street0VPI/vpip already called in Hand
        # sawShowdown is calculated in playersAtStreetX, as that calculation gives us a convenient list of names

        #hand.players = [[seat, name, chips],[seat, name, chips]]
        for player in hand.players:
            self.handsplayers[player[1]]['seatNo'] = player[0]
            self.handsplayers[player[1]]['startCash'] = int(100 * Decimal(player[2]))
            self.handsplayers[player[1]]['sitout'] = False #TODO: implement actual sitout detection
            if hand.gametype["type"]=="tour":
                self.handsplayers[player[1]]['tourneyTypeId']=hand.tourneyTypeId
                self.handsplayers[player[1]]['tourneysPlayersIds'] = hand.tourneysPlayersIds[player[1]]
            else:
                self.handsplayers[player[1]]['tourneysPlayersIds'] = None

        #### seen now processed in playersAtStreetX()
        # XXX: enumerate(list, start=x) is python 2.6 syntax; 'start'
        #for i, street in enumerate(hand.actionStreets[2:], start=1):
        #for i, street in enumerate(hand.actionStreets[2:]):
        #    self.seen(self.hand, i+1)

        for i, street in enumerate(hand.actionStreets[1:]):
            self.aggr(self.hand, i)
            self.calls(self.hand, i)
            self.bets(self.hand, i)
            if i>0:
                self.folds(self.hand, i)

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
            if self.handsplayers[player]['street2Seen'] == True:
                self.handsplayers[player]['wonWhenSeenStreet2'] = 1.0
            if self.handsplayers[player]['street3Seen'] == True:
                self.handsplayers[player]['wonWhenSeenStreet3'] = 1.0
            if self.handsplayers[player]['street4Seen'] == True:
                self.handsplayers[player]['wonWhenSeenStreet4'] = 1.0
            if self.handsplayers[player]['sawShowdown'] == True:
                self.handsplayers[player]['wonAtSD'] = 1.0

        for player in hand.pot.committed:
            self.handsplayers[player]['totalProfit'] = int(self.handsplayers[player]['winnings'] - (100*hand.pot.committed[player])- (100*hand.pot.common[player]))

        self.calcCBets(hand)

        for player in hand.players:
            hcs = hand.join_holecards(player[1], asList=True)
            hcs = hcs + [u'0x']*18
            #for i, card in enumerate(hcs[:20, 1): #Python 2.6 syntax
            #    self.handsplayers[player[1]]['card%s' % i] = Card.encodeCard(card)
            for i, card in enumerate(hcs[:20]):
                self.handsplayers[player[1]]['card%s' % (i+1)] = Card.encodeCard(card)
            self.handsplayers[player[1]]['startCards'] = Card.calcStartCards(hand, player[1])

        self.setPositions(hand)
        self.calcCheckCallRaise(hand)
        self.calc34BetStreet0(hand)
        self.calcSteals(hand)
        # Additional stats
        # 3betSB, 3betBB
        # Squeeze, Ratchet?

    def assembleHandsActions(self, hand):
        k = 0
        for i, street in enumerate(hand.actionStreets):
            for j, act in enumerate(hand.actions[street]):
                k += 1
                self.handsactions[k] = {}
                #default values
                self.handsactions[k]['amount'] = 0
                self.handsactions[k]['raiseTo'] = 0
                self.handsactions[k]['amountCalled'] = 0
                self.handsactions[k]['numDiscarded'] = 0
                self.handsactions[k]['cardsDiscarded'] = None
                self.handsactions[k]['allIn'] = False
                #Insert values from hand.actions
                self.handsactions[k]['player'] = act[0]
                self.handsactions[k]['street'] = i-1
                self.handsactions[k]['actionNo'] = k
                self.handsactions[k]['streetActionNo'] = (j+1)
                self.handsactions[k]['actionId'] = hand.ACTION[act[1]]
                if act[1] not in ('discards') and len(act) > 2:
                    self.handsactions[k]['amount'] = int(100 * act[2])
                if act[1] in ('raises', 'completes'):
                    self.handsactions[k]['raiseTo'] = int(100 * act[3])
                    self.handsactions[k]['amountCalled'] = int(100 * act[4])
                if act[1] in ('discards'):
                    self.handsactions[k]['numDiscarded'] = int(act[2])
                if act[1] in ('discards') and len(act) > 3:
                    self.handsactions[k]['cardsDiscarded'] = act[3]
                if len(act) > 3 and act[1] not in ('discards'):
                    self.handsactions[k]['allIn'] = act[-1]

    def setPositions(self, hand):
        """Sets the position for each player in HandsPlayers
            any blinds are negative values, and the last person to act on the
            first betting round is 0
            NOTE: HU, both values are negative for non-stud games
            NOTE2: I've never seen a HU stud match"""
        actions = hand.actions[hand.holeStreets[0]]
        # Note:  pfbao list may not include big blind if all others folded
        players = self.pfbao(actions)

        # set blinds first, then others from pfbao list, avoids problem if bb
        # is missing from pfbao list or if there is no small blind
        sb, bb, bi = False, False, False
        if hand.gametype['base'] == 'stud':
            # Stud position is determined after cards are dealt
            bi = [x[0] for x in hand.actions[hand.actionStreets[1]] if x[1] == 'bringin']
        else:
            bb = [x[0] for x in hand.actions[hand.actionStreets[0]] if x[1] == 'big blind']
            sb = [x[0] for x in hand.actions[hand.actionStreets[0]] if x[1] == 'small blind']

        # if there are > 1 sb or bb only the first is used!
        if bb:
            self.handsplayers[bb[0]]['position'] = 'B'
            if bb[0] in players:  players.remove(bb[0])
        if sb:
            self.handsplayers[sb[0]]['position'] = 'S'
            if sb[0] in players:  players.remove(sb[0])
        if bi:
            self.handsplayers[bi[0]]['position'] = 'S'
            if bi[0] in players:  players.remove(bi[0])

        #print "DEBUG: bb: '%s' sb: '%s' bi: '%s' plyrs: '%s'" %(bb, sb, bi, players)
        for i,player in enumerate(reversed(players)):
            self.handsplayers[player]['position'] = i

    def assembleHudCache(self, hand):
        # No real work to be done - HandsPlayers data already contains the correct info
        pass

    def vpip(self, hand):
        vpipers = set()
        for act in hand.actions[hand.actionStreets[1]]:
            if act[1] in ('calls','bets', 'raises', 'completes'):
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
        #     ... new code below hopefully fixes this
        # partly fixed, allins are now set as seeing streets because they never do a fold action

        self.hands['playersAtStreet1']  = 0
        self.hands['playersAtStreet2']  = 0
        self.hands['playersAtStreet3']  = 0
        self.hands['playersAtStreet4']  = 0
        self.hands['playersAtShowdown'] = 0

#        alliners = set()
#        for (i, street) in enumerate(hand.actionStreets[2:]):
#            actors = set()
#            for action in hand.actions[street]:
#                if len(action) > 2 and action[-1]: # allin
#                    alliners.add(action[0])
#                actors.add(action[0])
#            if len(actors)==0 and len(alliners)<2:
#                alliners = set()
#            self.hands['playersAtStreet%d' % (i+1)] = len(set.union(alliners, actors))
#
#        actions = hand.actions[hand.actionStreets[-1]]
#        print "p_actions:", self.pfba(actions), "p_folds:", self.pfba(actions, l=('folds',)), "alliners:", alliners
#        pas = set.union(self.pfba(actions) - self.pfba(actions, l=('folds',)),  alliners)
        
        # hand.players includes people that are sitting out on some sites for cash games
        # actionStreets[1] is 'DEAL', 'THIRD', 'PREFLOP', so any player dealt cards
        # must act on this street if dealt cards. Almost certainly broken for the 'all-in blind' case
        # and right now i don't care - CG

        p_in = set([x[0] for x in hand.actions[hand.actionStreets[1]]])

        #
        # discover who folded on each street and remove them from p_in
        #
        # i values as follows 0=BLINDSANTES 1=PREFLOP 2=FLOP 3=TURN 4=RIVER
        #   (for flop games)
        #
        # At the beginning of the loop p_in contains the players with cards
        # at the start of that street.
        # p_in is reduced each street to become a list of players still-in
        # e.g. when i=1 (preflop) all players who folded during preflop
        # are found by pfba() and eliminated from p_in.
        # Therefore at the end of the loop, p_in contains players remaining
        # at the end of the action on that street, and can therefore be set
        # as the value for the number of players who saw the next street
        #
        # note that i is 1 in advance of the actual street numbers in the db
        #
        # if p_in reduces to 1 player, we must bomb-out immediately
        # because the hand is over, this will ensure playersAtStreetx
        # is accurate.
        #
                    
        for (i, street) in enumerate(hand.actionStreets):
            if (i-1) in (1,2,3,4):
                # p_in stores players with cards at start of this street,
                # so can set streetxSeen & playersAtStreetx with this information
                # This hard-coded for i-1 =1,2,3,4 because those are the only columns
                # in the db! this code section also replaces seen() - more info log 66
                # nb i=2=flop=street1Seen, hence i-1 term needed
                self.hands['playersAtStreet%d' % (i-1)] = len(p_in)
                for player_with_cards in p_in:
                    self.handsplayers[player_with_cards]['street%sSeen' % (i-1)] = True
            #
            # find out who folded, and eliminate them from p_in
            #
            actions = hand.actions[street]
            p_in = p_in - self.pfba(actions, l=('folds',))
            #
            # if everyone folded, we are done, so exit this method immediately
            #
            if len(p_in) == 1: return None

        #
        # The remaining players in p_in reached showdown (including all-ins
        # because they never did a "fold" action in pfba() above)
        #
        self.hands['playersAtShowdown'] = len(p_in)
        for showdown_player in p_in:
            self.handsplayers[showdown_player]['sawShowdown'] = True

    def streetXRaises(self, hand):
        # self.actions[street] is a list of all actions in a tuple, contining the action as the second element
        # [ (player, action, ....), (player2, action, ...) ]
        # No idea what this value is actually supposed to be
        # In theory its "num small bets paid to see flop/street4, including blind" which makes sense for limit. Not so useful for nl
        # Leaving empty for the moment,

        for i in range(5): self.hands['street%dRaises' % i] = 0

        for (i, street) in enumerate(hand.actionStreets[1:]):
            self.hands['street%dRaises' % i] = len(filter( lambda action: action[1] in ('raises','bets'), hand.actions[street]))

    def calcSteals(self, hand):
        """Fills raiseFirstInChance|raisedFirstIn, fold(Bb|Sb)ToSteal(Chance|)

        Steal attempt - open raise on positions 1 0 S - i.e. CO, BU, SB
                        (note: I don't think PT2 counts SB steals in HU hands, maybe we shouldn't?)
        Fold to steal - folding blind after steal attemp wo any other callers or raisers
        """
        steal_attempt = False
        raised = False
        steal_positions = (1, 0, 'S')
        if hand.gametype['base'] == 'stud':
            steal_positions = (2, 1, 0)
        for action in hand.actions[hand.actionStreets[1]]:
            pname, act = action[0], action[1]
            posn = self.handsplayers[pname]['position']
            #print "\naction:", action[0], posn, type(posn), steal_attempt, act
            if posn == 'B':
                #NOTE: Stud games will never hit this section
                if steal_attempt:
                    self.handsplayers[pname]['foldBbToStealChance'] = True
                    self.handsplayers[pname]['raiseToStealChance'] = True
                    self.handsplayers[pname]['foldedBbToSteal'] = act == 'folds'
                    self.handsplayers[pname]['raiseToStealDone'] = act == 'raises'
                    self.handsplayers[stealer]['success_Steal'] = act == 'folds'
                break
            elif posn == 'S':
                self.handsplayers[pname]['raiseToStealChance'] = steal_attempt
                self.handsplayers[pname]['foldSbToStealChance'] = steal_attempt
                self.handsplayers[pname]['foldedSbToSteal'] = steal_attempt and act == 'folds'
                self.handsplayers[pname]['raiseToStealDone'] = steal_attempt and act == 'raises'

            if steal_attempt and act != 'folds':
                break

            if not steal_attempt and not raised and not act in ('bringin'):
                self.handsplayers[pname]['raiseFirstInChance'] = True
                if act in ('bets', 'raises', 'completes'):
                    self.handsplayers[pname]['raisedFirstIn'] = True
                    raised = True
                    if posn in steal_positions:
                        steal_attempt = True
                        stealer = pname
                if act == 'calls':
                    break
            
            if posn not in steal_positions and act not in ('folds', 'bringin'):
                break

    def calc34BetStreet0(self, hand):
        """Fills street0_(3|4)B(Chance|Done), other(3|4)BStreet0"""
        bet_level = 1 # bet_level after 3-bet is equal to 3
        squeeze_chance = False
        for action in hand.actions[hand.actionStreets[1]]:
            pname, act, aggr = action[0], action[1], action[1] in ('raises', 'bets')
            if bet_level == 1:
                if aggr:
                    first_agressor = pname
                    bet_level += 1
                continue
            elif bet_level == 2:
                self.handsplayers[pname]['street0_3BChance'] = True
                self.handsplayers[pname]['street0_SqueezeChance'] = squeeze_chance
                if not squeeze_chance and act == 'calls':
                    squeeze_chance = True
                    continue
                if aggr:
                    self.handsplayers[pname]['street0_3BDone'] = True
                    self.handsplayers[pname]['street0_SqueezeDone'] = squeeze_chance
                    second_agressor = pname
                    bet_level += 1
                continue
            elif bet_level == 3:
                if pname == first_agressor:
                    self.handsplayers[pname]['street0_4BChance'] = True
                    self.handsplayers[pname]['street0_FoldTo3BChance'] = True
                    if aggr:
                        self.handsplayers[pname]['street0_4BDone'] = True
                        bet_level += 1
                    elif act == 'folds':
                        self.handsplayers[pname]['street0_FoldTo3BDone'] = True
                        break
                else:
                    self.handsplayers[pname]['street0_C4BChance'] = True
                    if aggr:
                        self.handsplayers[pname]['street0_C4BDone'] = True
                        bet_level += 1
                continue
            elif bet_level == 4:
                if pname == second_agressor: 
                    self.handsplayers[pname]['street0_FoldTo4BChance'] = True
                    if act == 'folds':
                        self.handsplayers[pname]['street0_FoldTo4BDone'] = True
                    break

    def calcCBets(self, hand):
        """Fill streetXCBChance, streetXCBDone, foldToStreetXCBDone, foldToStreetXCBChance

        Continuation Bet chance, action:
        Had the last bet (initiative) on previous street, got called, close street action
        Then no bets before the player with initiatives first action on current street
        ie. if player on street-1 had initiative and no donkbets occurred
        """
        # XXX: enumerate(list, start=x) is python 2.6 syntax; 'start'
        # came there
        #for i, street in enumerate(hand.actionStreets[2:], start=1):
        for i, street in enumerate(hand.actionStreets[2:]):
            name = self.lastBetOrRaiser(hand.actionStreets[i+1])
            if name:
                chance = self.noBetsBefore(hand.actionStreets[i+2], name)
                if chance == True:
                    self.handsplayers[name]['street%dCBChance' % (i+1)] = True
                    self.handsplayers[name]['street%dCBDone' % (i+1)] = self.betStreet(hand.actionStreets[i+2], name)

    def calcCheckCallRaise(self, hand):
        """Fill streetXCheckCallRaiseChance, streetXCheckCallRaiseDone

        streetXCheckCallRaiseChance = got raise/bet after check
        streetXCheckCallRaiseDone = checked. got raise/bet. didn't fold

        CG: CheckCall would be a much better name for this.
        """
        # XXX: enumerate(list, start=x) is python 2.6 syntax; 'start'
        #for i, street in enumerate(hand.actionStreets[2:], start=1):
        for i, street in enumerate(hand.actionStreets[2:]):
            actions = hand.actions[hand.actionStreets[i+1]]
            checkers = set()
            initial_raiser = None
            for action in actions:
                pname, act = action[0], action[1]
                if act in ('bets', 'raises') and initial_raiser is None:
                    initial_raiser = pname
                elif act == 'checks' and initial_raiser is None:
                    checkers.add(pname)
                elif initial_raiser is not None and pname in checkers:
                    self.handsplayers[pname]['street%dCheckCallRaiseChance' % (i+1)] = True
                    self.handsplayers[pname]['street%dCheckCallRaiseDone' % (i+1)] = act!='folds'

    def aggr(self, hand, i):
        aggrers = set()
        others = set()
        # Growl - actionStreets contains 'BLINDSANTES', which isn't actually an action street

        firstAggrMade=False
        for act in hand.actions[hand.actionStreets[i+1]]:
            if firstAggrMade:
                others.add(act[0])
            if act[1] in ('completes', 'bets', 'raises'):
                aggrers.add(act[0])
                firstAggrMade=True

        for player in hand.players:
            #print "DEBUG: actionStreet[%s]: %s" %(hand.actionStreets[i+1], i)
            if player[1] in aggrers:
                self.handsplayers[player[1]]['street%sAggr' % i] = True
            else:
                self.handsplayers[player[1]]['street%sAggr' % i] = False
                
        if len(aggrers)>0 and i>0:
            for playername in others:
                self.handsplayers[playername]['otherRaisedStreet%s' % i] = True
                #print "otherRaised detected on handid "+str(hand.handid)+" for "+playername+" on street "+str(i)

        if i > 0 and len(aggrers) > 0:
            for playername in others:
                self.handsplayers[playername]['otherRaisedStreet%s' % i] = True
                #print "DEBUG: otherRaised detected on handid %s for %s on actionStreet[%s]: %s" 
                #                           %(hand.handid, playername, hand.actionStreets[i+1], i)

    def calls(self, hand, i):
        callers = []
        for act in hand.actions[hand.actionStreets[i+1]]:
            if act[1] in ('calls'):
                self.handsplayers[act[0]]['street%sCalls' % i] = 1 + self.handsplayers[act[0]]['street%sCalls' % i]

    # CG - I'm sure this stat is wrong
    # Best guess is that raise = 2 bets
    def bets(self, hand, i):
        for act in hand.actions[hand.actionStreets[i+1]]:
            if act[1] in ('bets'):
                self.handsplayers[act[0]]['street%sBets' % i] = 1 + self.handsplayers[act[0]]['street%sBets' % i]
        
    def folds(self, hand, i):
        for act in hand.actions[hand.actionStreets[i+1]]:
            if act[1] in ('folds'):
                if self.handsplayers[act[0]]['otherRaisedStreet%s' % i] == True:
                    self.handsplayers[act[0]]['foldToOtherRaisedStreet%s' % i] = True
                    #print "DEBUG: fold detected on handid %s for %s on actionStreet[%s]: %s"
                    #                       %(hand.handid, act[0],hand.actionStreets[i+1], i)

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

    def pfbao(self, actions, f=None, l=None, unique=True):
        """Helper method. Returns set of PlayersFilteredByActionsOrdered

        f - forbidden actions
        l - limited to actions
        """
        # Note, this is an adaptation of function 5 from:
        # http://www.peterbe.com/plog/uniqifiers-benchmark
        seen = {}
        players = []
        for action in actions:
            if l is not None and action[1] not in l: continue
            if f is not None and action[1] in f: continue
            if action[0] in seen and unique: continue
            seen[action[0]] = 1
            players.append(action[0])
        return players

    def firstsBetOrRaiser(self, actions):
        """Returns player name that placed the first bet or raise.

        None if there were no bets or raises on that street
        """
        for act in actions:
            if act[1] in ('bets', 'raises'):
                return act[0]
        return None

    def lastBetOrRaiser(self, street):
        """Returns player name that placed the last bet or raise for that street.
            None if there were no bets or raises on that street"""
        lastbet = None
        for act in self.hand.actions[street]:
            if act[1] in ('bets', 'raises'):
                lastbet = act[0]
        return lastbet


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
            if act[0] == player:
                if act[1] in ('bets', 'raises'):
                    betOrRaise = True
                else:
                    # player found but did not bet or raise as their first action
                    pass
                break
            #else:
                # haven't found player's first action yet
        return betOrRaise

