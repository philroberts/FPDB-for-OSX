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
import L10n
_ = L10n.get_translation()
import Card
from decimal_wrapper import Decimal

import sys
import logging
# logging has been set up in fpdb.py or HUD_main.py, use their settings:
log = logging.getLogger("parser")

try:
    from pokereval import PokerEval
    pokereval = PokerEval()
except:
    pokereval = None
    
def _buildStatsInitializer():
    init = {}
    #Init vars that may not be used, but still need to be inserted.
    # All stud street4 need this when importing holdem
    init['effStack']    = 0
    init['played']      = 0
    init['winnings']    = 0
    init['rake']        = 0
    init['rakeDealt']   = 0
    init['rakeContributed'] = 0
    init['rakeWeighted'] = 0
    init['totalProfit'] = 0
    init['allInEV']     = 0
    init['BBwon']       = 0
    init['street4Aggr'] = False
    init['wonWhenSeenStreet1'] = False
    init['sawShowdown'] = False
    init['showed']      = False
    init['wonAtSD']     = False
    init['startCards']  = 170
    init['handString']  = None
    init['position']    = 2
    init['street0CalledRaiseChance'] = 0
    init['street0CalledRaiseDone'] = 0
    init['street0VPIChance']    = True
    init['street0VPI']          = False
    init['street0AggrChance']   = True
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
        init['street%dAggr' % i] = False
    for i in range(1,5):
        init['street%dCBChance' %i] = False
        init['street%dCBDone' %i] = False
        init['street%dCheckCallRaiseChance' %i] = False
        init['street%dCheckCallDone' %i]        = False
        init['street%dCheckRaiseDone' %i]       = False
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
    init['wonWhenSeenStreet2'] = False
    init['wonWhenSeenStreet3'] = False
    init['wonWhenSeenStreet4'] = False
    return init

_INIT_STATS = _buildStatsInitializer()

class DerivedStats():
    def __init__(self):
        self.hands        = {}
        self.handsplayers = {}
        self.handsactions = {}
        self.handsstove   = []
        self.handspots    = []

    def getStats(self, hand):
        for player in hand.players:
            self.handsplayers[player[1]] = _INIT_STATS.copy()
        
        self.assembleHands(hand)
        self.assembleHandsPlayers(hand)

        if hand.saveActions:
            self.assembleHandsActions(hand)
        
        if pokereval:
            if hand.gametype['category'] in Card.games:
                self.assembleHandsStove(hand)
                self.assembleHandsPots(hand)

    def getHands(self):
        return self.hands

    def getHandsPlayers(self):
        return self.handsplayers

    def getHandsActions(self):
        return self.handsactions
    
    def getHandsStove(self):
        return self.handsstove
    
    def getHandsPots(self):
        return self.handspots

    def assembleHands(self, hand):
        self.hands['tableName']     = hand.tablename
        self.hands['siteHandNo']    = hand.handid
        self.hands['gametypeId']    = None                    # Leave None, handled later after checking db
        self.hands['sessionId']     = None                    # Leave None, added later if caching sessions
        self.hands['gameId']        = None                    # Leave None, added later if caching sessions
        self.hands['startTime']     = hand.startTime          # format this!
        self.hands['importTime']    = None
        self.hands['seats']         = self.countPlayers(hand) 
        #self.hands['maxSeats']      = hand.maxseats
        self.hands['texture']       = None                    # No calculation done for this yet.
        self.hands['tourneyId']     = hand.tourneyId
        
        self.hands['heroSeat']      = 0
        for player in hand.players:
            if hand.hero==player[1]:
                self.hands['heroSeat'] = player[0]
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
        
        #print "cards: ",cards
        
        self.hands['boards']     = []
        self.hands['runItTwice']      = False           
        for i in range(hand.runItTimes):
            self.hands['runItTwice']  = True
            boardcards = []
            for street in hand.communityStreets:
                boardId = i+1
                street_i = street + str(boardId)
                if street_i in hand.board:
                    boardcards += hand.board[street_i]
            boardcards = [u'0x', u'0x', u'0x', u'0x', u'0x'] + boardcards
            cards = [Card.encodeCard(c) for c in boardcards[-5:]]
            self.hands['boards'] += [[boardId] + cards]

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
            player_name = player[1]
            player_stats = self.handsplayers.get(player_name)
            player_stats['seatNo'] = player[0]
            player_stats['startCash'] = int(100 * Decimal(player[2]))
            if player_name in hand.sitout:
                player_stats['sitout'] = True
            else:
                player_stats['sitout'] = False
            if hand.gametype["type"]=="tour":
                player_stats['tourneyTypeId']=hand.tourneyTypeId
                player_stats['tourneysPlayersIds'] = hand.tourneysPlayersIds[player[1]]
            else:
                player_stats['tourneysPlayersIds'] = None
            if player_name in hand.shown:
                player_stats['showed'] = True

        #### seen now processed in playersAtStreetX()
        # XXX: enumerate(list, start=x) is python 2.6 syntax; 'start'
        #for i, street in enumerate(hand.actionStreets[2:], start=1):
        #for i, street in enumerate(hand.actionStreets[2:]):
        #    self.seen(self.hand, i+1)

        for i, street in enumerate(hand.actionStreets[1:]):
            self.aggr(hand, i)
            self.calls(hand, i)
            self.bets(hand, i)
            if i>0:
                self.folds(hand, i)

        # Winnings is a non-negative value of money collected from the pot, which already includes the
        # rake taken out. hand.collectees is Decimal, database requires cents
        num_collectees = len(hand.collectees)
        for player, winnings in hand.collectees.iteritems():
            collectee_stats = self.handsplayers.get(player)
            collectee_stats['winnings'] = int(100 * winnings)
            #FIXME: This is pretty dodgy, rake = hand.rake/#collectees
            # You can really only pay rake when you collect money, but
            # different sites calculate rake differently.
            # Should be fine for split-pots, but won't be accurate for multi-way pots
            collectee_stats['rake'] = int(100 * hand.rake)/num_collectees
            if collectee_stats['street1Seen'] == True:
                collectee_stats['wonWhenSeenStreet1'] = True
            if collectee_stats['street2Seen'] == True:
                collectee_stats['wonWhenSeenStreet2'] = True
            if collectee_stats['street3Seen'] == True:
                collectee_stats['wonWhenSeenStreet3'] = True
            if collectee_stats['street4Seen'] == True:
                collectee_stats['wonWhenSeenStreet4'] = True
            if collectee_stats['sawShowdown'] == True:
                collectee_stats['wonAtSD'] = True
        
        contributed = []
        for player, money_committed in hand.pot.committed.iteritems():
            committed_player_stats = self.handsplayers.get(player)
            paid = (100 * money_committed) + (100*hand.pot.common[player])
            committed_player_stats['totalProfit'] = int(committed_player_stats['winnings'] - paid)
            committed_player_stats['allInEV'] = committed_player_stats['totalProfit']
            committed_player_stats['rakeDealt'] = int(100* hand.rake)/len(hand.players)
            if paid > 0: contributed.append(player)
            if hand.totalpot>0:
                committed_player_stats['rakeWeighted'] = int((100* hand.rake) * (paid/(100*hand.totalpot)))
            else:
                committed_player_stats['rakeWeighted'] = 0
            
        for player in contributed:
            self.handsplayers[player]['rakeContributed'] = int(100* hand.rake)/len(contributed)
            
        for player in hand.players:
            player_name = player[1]
            player_stats = self.handsplayers.get(player_name)
            if int(Decimal(hand.gametype['bb']))>0:
                player_stats['BBwon'] = player_stats['totalProfit'] / int(Decimal(hand.gametype['bb'])*2)
            if player_stats['street0VPI'] or player_stats['street1Seen']:
                player_stats['played'] = 1
            if player_stats['sawShowdown']:
                player_stats['showdownWinnings'] = player_stats['totalProfit']
                player_stats['nonShowdownWinnings'] = 0
            else:
                player_stats['showdownWinnings']    = 0
                player_stats['nonShowdownWinnings'] = player_stats['totalProfit']
            if player_name!=hand.hero and hand.hero:
                hero_stats = self.handsplayers.get(hand.hero)
                if player_stats['totalProfit']>0 and 0>hero_stats['totalProfit']:
                    player_stats['vsHero'] = - int(hero_stats['totalProfit'] * Decimal(player_stats['winnings'])/(hand.totalpot*100))
                elif hero_stats['totalProfit']>0 and 0>player_stats['totalProfit']:
                    player_stats['vsHero'] = int(player_stats['totalProfit'] * Decimal(hero_stats['winnings'])/(hand.totalpot*100))
                else:
                    player_stats['vsHero'] = 0
            else:
                player_stats['vsHero'] = 0

        self.calcCBets(hand)
        
        # More inner-loop speed hackery.
        encodeCard = Card.encodeCard
        calcStartCards = Card.calcStartCards
        for player in hand.players:
            player_name = player[1]
            hcs = hand.join_holecards(player_name, asList=True)
            hcs = hcs + [u'0x']*18
            #for i, card in enumerate(hcs[:20, 1): #Python 2.6 syntax
            #    self.handsplayers[player[1]]['card%s' % i] = Card.encodeCard(card)
            player_stats = self.handsplayers.get(player_name)
            for i, card in enumerate(hcs[:20]):
                player_stats['card%d' % (i+1)] = encodeCard(card)
            player_stats['startCards'] = calcStartCards(hand, player_name)

        self.setPositions(hand)
        self.calcEffectiveStack(hand)
        self.calcCheckCallRaise(hand)
        self.calc34BetStreet0(hand)
        self.calcSteals(hand)
        self.calcCalledRaiseStreet0(hand)
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
    
    def assembleHandsStove(self, hand):
        category = hand.gametype['category']
        holecards, holeplayers, allInStreets = {}, [], hand.allStreets[1:]
        base, evalgame, hilo, streets, last, hrange = Card.games[category]
        hiLoKey = {'h': [('h', 'hi')], 'l': [('l', 'low')], 's': [('h', 'hi'),('l', 'low')], 'r': [('l', 'hi')]}
        boards = self.getBoardsDict(hand, base, streets) 
        for player in hand.players:
            hole, cards, bcards = [], [], []
            pname = player[1]
            hp = self.handsplayers.get(pname)
            if evalgame:
                hcs = hand.join_holecards(pname, asList=True)
                hole = hcs[hrange[-1][0]:hrange[-1][1]]                            
                holecards[pname] = {}
                holecards[pname]['hole'] = [str(c) for c in hole]
                holecards[pname]['cards'] = []
                holecards[pname]['eq'] = 0
                holecards[pname]['committed'] = 0
                holeplayers.append(pname)
                for street, board in boards.iteritems():
                    streetId = streets[street]
                    if streetId > 0:
                        streetSeen = hp['street%sSeen' % str(streetId)]
                    else: streetSeen = True
                    if ((pname==hand.hero and streetSeen) or (hp['showed'] and streetSeen) or hp['sawShowdown']):
                        boardId, hl, rankId, value, _cards = 0, 'n', 1, 0, None
                        for n in range(len(board['board'])):
                            if len(board['board']) > 1: 
                                boardId = n + 1
                            else: boardId = n
                            if base!='hold':
                                hole = hcs[hrange[streetId][0]:hrange[streetId][1]]  
                            cards = [str(c) for c in hole if Card.encodeCardList.get(c)!=None or c=='0x']
                            if board['board'][n]: bcards = [str(b) for b in board['board'][n]]
                            else                : bcards = []
                            if 'omaha' not in evalgame:
                                if board['board'][n]:
                                    cards = hole + board['board'][n]
                                    cards  = [str(c) for c in cards]
                                    bcards = []
                            if base=='hold':
                                holecards[pname]['cards'] += [cards]
                            
                            notnull  = ('0x' not in cards)
                            postflop = (base=='hold' and len(board['board'][n])>=3)
                            maxcards = (base!='hold' and len(cards)>=5)
                            #print pname, street, streetId, cards, notnull, postflop, maxcards
                            if notnull and (postflop or maxcards):
                                for hl, side in hiLoKey[hilo]:
                                    value, rank = pokereval.best(side, cards, bcards)
                                    rankId = Card.hands[rank[0]][0]
                                    if rank!=None and rank[0] != 'Nothing':
                                        _cards = ''.join([pokereval.card2string(i)[0] for i in rank[1:]])
                                    else:
                                        _cards = None
                                    self.handsstove.append( [hand.dbid_hands, hand.dbid_pids[pname], streetId, boardId, hl, rankId, value, _cards, 0] )
                            else:
                                self.handsstove.append( [hand.dbid_hands, hand.dbid_pids[pname], streetId, boardId, 'n', 1, 0, None, 0] )
            else:
                hl, streetId = hiLoKey[hilo][0][0], 0
                if (hp['sawShowdown'] or hp['showed']):
                    hp['handString'] = hand.showdownStrings.get(pname)
                    streetId = streets[last]
                self.handsstove.append( [hand.dbid_hands, hand.dbid_pids[player[1]], streetId, 0, hl, 1, 0, None, 0] )
        
        if base=='hold' and evalgame:
            self.getAllInEV(hand, evalgame, holeplayers, boards, streets, holecards)
                
    def getAllInEV(self, hand, evalgame, holeplayers, boards, streets, holecards):
        startstreet, potId, allInStreets = None, 0, hand.allStreets[1:]
        for pot, players in hand.pot.pots:
            if potId ==0: pot += sum(hand.pot.common.values())
            potId+=1
            players = [p for p in players]
            for street in allInStreets:
                board = boards[street]
                streetId = streets[street]
                for n in range(len(board['board'])):
                    if len(board['board']) > 1: 
                        boardId = n + 1
                    else: boardId = n
                    if board['allin'] and len([p for p in players if p in holecards and u'0x' not in holecards[p]['cards'][n]]) > 0:
                        if not startstreet: startstreet = street
                        bcards = [str(b) for b in board['board'][n]]
                        b = bcards + (5 - len(board['board'][n])) * ['__']
                        holeshow = [holecards[p]['hole'] for p in players if self.handsplayers[p]['sawShowdown'] and u'0x' not in holecards[p]['cards'][n]]
                        if len(holeshow)> 1:
                            evs = pokereval.poker_eval(game = evalgame, iterations = Card.iter[streetId] ,pockets = holeshow ,dead = [], board = b)
                            equities = [e['ev'] for e in evs['eval']]
                        else:
                            equities = [1000]
                        for i in range(len(equities)):
                            p = players[i]
                            pid = hand.dbid_pids[p]
                            if street == startstreet:
                                rake = (hand.rake * (pot/hand.totalpot))
                                holecards[p]['eq'] += int(((100*pot - 100*rake) * Decimal(equities[i])/1000))
                                holecards[p]['committed'] = int(((100*hand.pot.committed[p]) + (100*hand.pot.common[p])))
                            for j in self.handsstove:
                                if [pid, streetId, boardId] == j[1:4] and len(players) == len(hand.pot.contenders):
                                    j[-1] = equities[i]
        for p in holeplayers:
            if holecards[p]['committed'] != 0: 
                self.handsplayers[p]['allInEV'] = holecards[p]['eq'] - holecards[p]['committed']
    
    def getBoardsList(self, hand):
        boards, community = [], []
        if hand.gametype['base']=='hold':
            for s in hand.communityStreets:
                community += hand.board[s]
            for i in range(hand.runItTimes):
                boardcards = []
                for street in hand.communityStreets:
                    boardId = i+1
                    street_i = street + str(boardId)
                    if street_i in hand.board:
                        boardcards += hand.board[street_i]
                cards = [str(c) for c in community + boardcards]
                boards.append(cards)
        if not boards: 
            boards = [community]
        return boards
    
    def getBoardsDict(self, hand, base, streets):
        boards, boardcards, allInStreets, showdown = {}, [], hand.allStreets[1:], False
        for player in hand.players:
            if (self.handsplayers[player[1]]['sawShowdown']):
                showdown = True
        if base == 'hold':
            for s in allInStreets:
                streetId = streets[s]
                b = [x for sublist in [hand.board[k] for k in allInStreets[:streetId+1]] for x in sublist]
                boards[s] = {'board': [b], 'allin': False}
                boardcards += hand.board[s]
                if not hand.actions[s] and showdown:
                    if streetId>0: boards[allInStreets[streetId-1]]['allin'] = True
                    boards[s]['allin'] = True
            boardStreets = [[], [], []]
            for i in range(hand.runItTimes):
                runitcards = []
                for street in hand.communityStreets:
                    street_i = street + str((i+1))
                    if street_i in hand.board:
                        runitcards += hand.board[street_i]
                        sId = len(boardcards + runitcards) - 3
                        boardStreets[sId].append(boardcards + runitcards)
            for i in range(len(boardStreets)):
                if boardStreets[i]:
                    boards[allInStreets[i+1]]['board'] = boardStreets[i]
        else:   
            for s in allInStreets:
                streetId = streets[s]
                boards[s] = {}
                boards[s]['board'] = [[]]
                boards[s]['allin'] = False
        return boards
    
    def awardPots(self, hand):
        base, evalgame, hilo, streets, last, hrange = Card.games[hand.gametype['category']]
        if pokereval and len(hand.pot.pots)>1 and evalgame:
            hand.collected = [] #list of ?
            hand.collectees = {} # dict from player names to amounts collected (?)
            rakes, totrake, potId = {}, 0, 0
            board = [str(b) for b in hand.board['FLOP'] + hand.board['TURN'] + hand.board['RIVER']]
            for pot, players in hand.pot.pots:
                if potId ==0: pot += sum(hand.pot.common.values())
                potId+=1
                holecards = []
                for p in players:
                    hcs = hand.join_holecards(p, asList=True)
                    if 'omaha' not in evalgame:
                        holes = [str(c) for c in hcs[hrange[-1][0]:hrange[-1][1]] + board]
                        bcards = []
                    else:
                        holes = [str(c) for c in hcs[hrange[-1][0]:hrange[-1][1]]]
                        bcards = [str(b) for b in board]
                    if '0x' not in hcs:
                        holecards.append(holes)
                win = pokereval.winners(game = evalgame, pockets = holecards, board = bcards)
                totalrake = hand.rakes.get('rake')
                if not totalrake:
                    totalpot = hand.rakes.get('pot')
                    if totalpot:
                        totalrake = hand.totalpot - totalpot
                    else:
                        totalrake = 0
                rake = (totalrake * (pot/hand.totalpot))
                for w in win['hi']:
                    pname = list(players)[w]
                    ppot  = str(((pot-rake)/len(win['hi'])).quantize(Decimal("0.01")))
                    hand.addCollectPot(player=pname,pot=ppot)
    
    def assembleHandsPots(self, hand):
        category, positions, playersPots, potFound, positionDict, showdown = hand.gametype['category'], [], {}, {}, {}, False
        for p in hand.players:
            playersPots[p[1]] = [0,[]]
            potFound[p[1]] = [0,0]
            positionDict[self.handsplayers[p[1]]['position']] = p[1]
            positions.append(self.handsplayers[p[1]]['position'])
            if self.handsplayers[p[1]]['sawShowdown']:
                showdown = True
        positions.sort(reverse=True)
        factor = 100
        if ((hand.gametype["type"]=="tour" or 
            (hand.gametype["type"]=="ring" and 
             (hand.gametype["currency"]=="play" and 
              (hand.sitename not in ('Winamax', 'PacificPoker'))))) and
               (not [n for (n,v) in hand.pot.pots if (n % Decimal('1.00'))!=0])):
            factor = 1  
        hiLoKey = {'h':['hi'],'l':['low'],'r':['low'],'s':['hi','low']}
        base, evalgame, hilo, streets, last, hrange = Card.games[category]
        if (evalgame and (len(hand.pot.pots)>1 or (showdown and (hilo=='s' or hand.runItTimes==2)))):
            #print 'DEBUG hand.collected', hand.collected
            #print 'DEBUG hand.collectees', hand.collectees
            rakes, totrake, potId = {}, 0, 0
            for pot, players in hand.pot.pots:
                if potId ==0: pot += sum(hand.pot.common.values())
                potId+=1
                boards, boardId, sumpot = self.getBoardsList(hand), 0, 0
                for b in boards:
                    boardId += (hand.runItTimes==2)
                    potBoard = Decimal(int(pot/len(boards)*factor))/factor
                    modBoard = pot - potBoard*len(boards)
                    if boardId==1: 
                        potBoard+=modBoard
                    holeplayers, holecards = [], []
                    for p in players:
                        hcs = hand.join_holecards(p, asList=True)
                        holes = [str(c) for c in hcs[hrange[-1][0]:hrange[-1][1]] if Card.encodeCardList.get(c)!=None or c=='0x']
                        board = [str(c) for c in b if 'omaha' in evalgame]
                        if 'omaha' not in evalgame:
                            holes = holes + [str(c) for c in b if base=='hold']
                        if '0x' not in holes and '0x' not in board:
                            holecards.append(holes)
                            holeplayers.append(p)
                    win = pokereval.winners(game = evalgame, pockets = holecards, board = board)
                    for hl in hiLoKey[hilo]:
                        if hl in win and len(win[hl])>0:
                            potHiLo = Decimal(int(potBoard/len(win)*factor))/factor
                            modHiLo = potBoard - potHiLo*len(win)
                            if len(win)==1 or hl=='hi':
                                potHiLo+=modHiLo
                            potSplit = Decimal(int(potHiLo/len(win[hl])*factor))/factor
                            modSplit = potHiLo - potSplit*len(win[hl])
                            pnames = [holeplayers[w] for w in win[hl]]
                            for n in positions:
                                if positionDict[n] in pnames:
                                    pname = positionDict[n]
                                    ppot = potSplit
                                    if modSplit>0:
                                        cent = (Decimal('0.01') * (100/factor))
                                        ppot += cent
                                        modSplit -= cent
                                    playersPots[pname][0] += ppot
                                    potFound[pname][0] += ppot
                                    data = {'potId': potId, 'boardId': boardId, 'hiLo': hl,'ppot':ppot, 'winners': [m for m in pnames if pname!=n], 'mod': ppot>potSplit}
                                    playersPots[pname][1].append(data)
        
            for p, (total, info) in playersPots.iteritems():
                if hand.collectees.get(p) and info:
                    potFound[p][1] = hand.collectees.get(p)
                    for item in info:
                        #print (str(hand.handid)," winners: ",item['winners'])
                        split = [n for n in item['winners'] if len(playersPots[n][1])==1]
                        if len(info)==1:
                            ppot = item['ppot']
                            rake = ppot - hand.collectees[p]
                            collected = hand.collectees[p]
                        elif item==info[-1]:
                            ppot, collected = potFound[p]
                            rake = ppot - collected
                        elif len(split)>0 and not item['mod']:
                            ppot = item['ppot']
                            collected = min([hand.collectees[s] for s in split] + [ppot])
                            rake = ppot - collected
                        else:
                            ppot = item['ppot']
                            totalrake = total - hand.collectees[p]
                            rake = (totalrake * (ppot/total)).quantize(Decimal("0.01"))
                            collected = ppot - rake 
                        potFound[p][0] -= ppot
                        potFound[p][1] -= collected
                        insert = [None, item['potId'], item['boardId'], item['hiLo'][0], hand.dbid_pids[p], int(item['ppot']*100), int(collected*100), int(rake*100)]   
                        self.handspots.append(insert)

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
        bb = [x[0] for x in hand.actions[hand.actionStreets[0]] if x[1] == 'big blind']
        for act in hand.actions[hand.actionStreets[1]]:
            if act[1] in ('calls','bets', 'raises', 'completes'):
                vpipers.add(act[0])

        self.hands['playersVpi'] = len(vpipers)

        for player in hand.players:
            pname = player[1]
            player_stats = self.handsplayers.get(pname)
            if pname in vpipers:
                player_stats['street0VPI'] = True
            elif pname in hand.sitout:
                player_stats['street0VPIChance'] = False
                player_stats['street0AggrChance'] = False
                
        if len(vpipers)==0 and bb:
            self.handsplayers[bb[0]]['street0VPIChance'] = False
            self.handsplayers[bb[0]]['street0AggrChance'] = False

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
        #Add in players who were allin blind
        if hand.pot.pots:
            if len(hand.pot.pots[0][1])>1: p_in = p_in.union(hand.pot.pots[0][1])

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
            player_stats = self.handsplayers.get(pname)
            if player_stats['sitout']: continue
            posn = player_stats['position']
            #print "\naction:", action[0], posn, type(posn), steal_attempt, act
            if posn == 'B':
                #NOTE: Stud games will never hit this section
                if steal_attempt:
                    player_stats['foldBbToStealChance'] = True
                    player_stats['raiseToStealChance'] = True
                    player_stats['foldedBbToSteal'] = act == 'folds'
                    player_stats['raiseToStealDone'] = act == 'raises'
                    self.handsplayers[stealer]['success_Steal'] = act == 'folds'
                break
            elif posn == 'S':
                player_stats['raiseToStealChance'] = steal_attempt
                player_stats['foldSbToStealChance'] = steal_attempt
                player_stats['foldedSbToSteal'] = steal_attempt and act == 'folds'
                player_stats['raiseToStealDone'] = steal_attempt and act == 'raises'

            if steal_attempt and act != 'folds':
                break

            if not steal_attempt and not raised and not act in ('bringin'):
                player_stats['raiseFirstInChance'] = True
                if act in ('bets', 'raises', 'completes'):
                    player_stats['raisedFirstIn'] = True
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
        squeeze_chance, raise_chance, action_cnt = False, True, {}
        p0_in = set([x[0] for x in hand.actions[hand.actionStreets[0]] if not x[-1]])
        p1_in = set([x[0] for x in hand.actions[hand.actionStreets[1]]])
        p_in = p1_in.union(p0_in)
        for p in p_in: action_cnt[p] = 0
        for action in hand.actions[hand.actionStreets[1]]:
            pname, act, aggr, allin = action[0], action[1], action[1] in ('raises', 'bets'), False
            player_stats = self.handsplayers.get(pname)
            action_cnt[pname] += 1
            if len(action) > 3 and act != 'discards':
                allin = action[-1]
            if len(p_in)==1 and action_cnt[pname]==1:
                raise_chance = False
                player_stats['street0AggrChance'] = raise_chance
            if act == 'folds' or allin or player_stats['sitout']:
                p_in.discard(pname)
                if player_stats['sitout']: continue
            if bet_level == 1:
                if aggr:
                    first_agressor = pname
                    bet_level += 1
                continue
            elif bet_level == 2:
                player_stats['street0_3BChance'] = raise_chance
                player_stats['street0_SqueezeChance'] = squeeze_chance
                if not squeeze_chance and act == 'calls':
                    squeeze_chance = True
                    continue
                if aggr:
                    player_stats['street0_3BDone'] = True
                    player_stats['street0_SqueezeDone'] = squeeze_chance
                    second_agressor = pname
                    bet_level += 1
                continue
            elif bet_level == 3:
                if pname == first_agressor:
                    player_stats['street0_4BChance'] = raise_chance
                    player_stats['street0_FoldTo3BChance'] = True
                    if aggr:
                        player_stats['street0_4BDone'] = raise_chance
                        bet_level += 1
                    elif act == 'folds':
                        player_stats['street0_FoldTo3BDone'] = True
                        break
                else:
                    player_stats['street0_C4BChance'] = raise_chance
                    if aggr:
                        player_stats['street0_C4BDone'] = raise_chance
                        bet_level += 1
                continue
            elif bet_level == 4:
                if pname != first_agressor: 
                    player_stats['street0_FoldTo4BChance'] = True
                    if act == 'folds':
                        player_stats['street0_FoldTo4BDone'] = True

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
            name = self.lastBetOrRaiser(hand.actions, hand.actionStreets[i+1]) # previous street
            if name:
                chance = self.noBetsBefore(hand.actions, hand.actionStreets[i+2], name) # this street
                if chance == True:
                    player_stats = self.handsplayers.get(name)
                    player_stats['street%dCBChance' % (i+1)] = True
                    player_stats['street%dCBDone' % (i+1)] = self.betStreet(hand.actions, hand.actionStreets[i+2], name)
                    if player_stats['street%dCBDone' % (i+1)]:
                        for pname, folds in self.foldTofirstsBetOrRaiser(hand.actions, street, name).iteritems():
                            #print "DEBUG:", hand.handid, pname.encode('utf8'), street, folds, '--', name, 'lastbet on ', hand.actionStreets[i+1]
                            self.handsplayers[pname]['foldToStreet%sCBChance' % (i+1)] = True
                            self.handsplayers[pname]['foldToStreet%sCBDone' % (i+1)] = folds

    def calcCalledRaiseStreet0(self, hand):
        """
        Fill street0CalledRaiseChance, street0CalledRaiseDone
        For flop games, go through the preflop actions:
            skip through first raise
            For each subsequent action:
                if the next action is fold :
                    player chance + 1
                if the next action is raise :
                    player chance + 1
                if the next non-fold action is call :
                    player chance + 1
                    player done + 1
                    skip through list to the next raise action
        """
        
        fast_forward = True
        for tupleread in hand.actions[hand.actionStreets[1]]:
            action = tupleread[1]
            if fast_forward:
                if action == 'raises':
                    fast_forward = False # raisefound, end fast-forward
            else:
                player = tupleread[0]
                player_stats = self.handsplayers.get(player)
                player_stats['street0CalledRaiseChance'] += 1
                if action == 'calls':
                    player_stats['street0CalledRaiseDone'] += 1
                    fast_forward = True

    def calcCheckCallRaise(self, hand):
        """Fill streetXCheckCallRaiseChance, streetXCheckCallRaiseDone

        streetXCheckCallRaiseChance = got raise/bet after check
        streetXCheckCallRaiseDone = checked. got raise/bet. didn't fold

        CG: CheckCall would be a much better name for this.
        """
        # XXX: enumerate(list, start=x) is python 2.6 syntax; 'start'
        #for i, street in enumerate(hand.actionStreets[2:], start=1):
        for i, street in enumerate(hand.actionStreets[2:]):
            actions = hand.actions[street]
            checkers = set()
            initial_raiser = None
            for action in actions:
                pname, act = action[0], action[1]
                if act in ('bets', 'raises') and initial_raiser is None:
                    initial_raiser = pname
                elif act == 'checks' and initial_raiser is None:
                    checkers.add(pname)
                elif initial_raiser is not None and pname in checkers:
                    player_stats = self.handsplayers.get(pname)
                    player_stats['street%dCheckCallRaiseChance' % (i+1)] = True
                    player_stats['street%dCheckCallDone' % (i+1)] = act=='calls'
                    player_stats['street%dCheckRaiseDone' % (i+1)] = act=='raises'

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
            if player[1] in aggrers:
                self.handsplayers[player[1]]['street%sAggr' % i] = True
                
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
                player_stats = self.handsplayers.get(act[0])
                player_stats['street%sCalls' % i] = 1 + player_stats['street%sCalls' % i]

    # CG - I'm sure this stat is wrong
    # Best guess is that raise = 2 bets
    def bets(self, hand, i):
        for act in hand.actions[hand.actionStreets[i+1]]:
            if act[1] in ('bets'):
                player_stats = self.handsplayers.get(act[0])
                player_stats['street%sBets' % i] = 1 + player_stats['street%sBets' % i]
        
    def folds(self, hand, i):
        for act in hand.actions[hand.actionStreets[i+1]]:
            if act[1] in ('folds'):
                player_stats = self.handsplayers.get(act[0])
                if player_stats['otherRaisedStreet%s' % i] == True:
                    player_stats['foldToOtherRaisedStreet%s' % i] = True
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
    
    def calcEffectiveStack(self,hand):
        """Calculates the effective stack for each player on street 1
        """
        seen = {}
        pstacks = {}
        actions = hand.actions[hand.holeStreets[0]]
        for p in hand.players: 
            if p[1] not in hand.sitout:
                if int(Decimal(hand.gametype['bb']))>0:
                    pstacks[p[1]] = int(100 * Decimal(p[2])) / int(Decimal(hand.gametype['bb']))
        for action in actions:
            if action[0] in seen: continue
            if action[0] not in pstacks: continue
            seen[action[0]] = 1
            oppstacks = [v for (k,v) in pstacks.iteritems() if k != action[0]]
            if oppstacks:
                if pstacks[action[0]] > max(oppstacks):
                    self.handsplayers[action[0]]['effStack'] = max(oppstacks)
                else:
                    self.handsplayers[action[0]]['effStack'] = pstacks[action[0]]
                if action[1] == 'folds':
                    pstacks[action[0]] = 0

    def firstsBetOrRaiser(self, actions):
        """Returns player name that placed the first bet or raise.

        None if there were no bets or raises on that street
        """
        for act in actions:
            if act[1] in ('bets', 'raises'):
                return act[0]
        return None
    
    def foldTofirstsBetOrRaiser(self, actions, street, aggressor):
        """Returns player name that placed the first bet or raise.

        None if there were no bets or raises on that street
        """
        i, players = 0, {}
        for act in actions[street]:
            if i>1: break
            if act[0] != aggressor:
                if act[1] == 'folds':
                    players[act[0]] = True
                else:
                    players[act[0]] = False
                if act[1] == 'raises': break
            elif act[1]!='discards':
                i+=1
        return players

    def lastBetOrRaiser(self, actions, street):
        """Returns player name that placed the last bet or raise for that street.
            None if there were no bets or raises on that street"""
        lastbet = None
        for act in actions[street]:
            if act[1] in ('bets', 'raises'):
                lastbet = act[0]
        return lastbet


    def noBetsBefore(self, actions, street, player):
        """Returns true if there were no bets before the specified players turn, false otherwise"""
        noBetsBefore = False
        for act in actions[street]:
            #Must test for player first in case UTG
            if act[0] == player:
                noBetsBefore = True
                break
            if act[1] in ('bets', 'raises'):
                break
        return noBetsBefore


    def betStreet(self, actions, street, player):
        """Returns true if player bet/raised the street as their first action"""
        betOrRaise = False
        for act in actions[street]:
            if act[0] == player and act[1] not in ('discards', 'stands pat'):
                if act[1] in ('bets', 'raises'):
                    betOrRaise = True
                else:
                    # player found but did not bet or raise as their first action
                    pass
                break
            #else:
                # haven't found player's first action yet
        return betOrRaise
