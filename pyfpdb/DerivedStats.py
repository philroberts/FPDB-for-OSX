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
        #FIXME: Pot size still in decimal, needs to be converted to cents
        (self.hands['street1Pot'],
         self.hands['street2Pot'],
         self.hands['street3Pot'],
         self.hands['street4Pot'],
         self.hands['showdownPot']) = hand.getStreetTotals()

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

        for i, street in enumerate(hand.actionStreets[2:]):
            self.seen(self.hand, i+1)

        for i, street in enumerate(hand.actionStreets[1:]):
            self.aggr(self.hand, i)


    def assembleHudCache(self, hand):
#       # def generateHudCacheData(player_ids, base, category, action_types, allIns, actionTypeByNo
#       #                 ,winnings, totalWinnings, positions, actionTypes, actionAmounts, antes):
#       #"""calculates data for the HUD during import. IMPORTANT: if you change this method make
#       #   sure to also change the following storage method and table_viewer.prepare_data if necessary
#       #"""
#            #print "generateHudCacheData, len(player_ids)=", len(player_ids)
#            #setup subarrays of the result dictionary.
#            street0VPI=[]
#            street0Aggr=[]
#            street0_3BChance=[]
#            street0_3BDone=[]
#            street1Seen=[]
#            street2Seen=[]
#            street3Seen=[]
#            street4Seen=[]
#            sawShowdown=[]
#            street1Aggr=[]
#            street2Aggr=[]
#            street3Aggr=[]
#            street4Aggr=[]
#            otherRaisedStreet1=[]
#            otherRaisedStreet2=[]
#            otherRaisedStreet3=[]
#            otherRaisedStreet4=[]
#            foldToOtherRaisedStreet1=[]
#            foldToOtherRaisedStreet2=[]
#            foldToOtherRaisedStreet3=[]
#            foldToOtherRaisedStreet4=[]
#            wonWhenSeenStreet1=[]
#
#            wonAtSD=[]
#            stealAttemptChance=[]
#            stealAttempted=[]
#            hudDataPositions=[]
#
#            street0Calls=[]
#            street1Calls=[]
#            street2Calls=[]
#            street3Calls=[]
#            street4Calls=[]
#            street0Bets=[]
#            street1Bets=[]
#            street2Bets=[]
#            street3Bets=[]
#            street4Bets=[]
#            #street0Raises=[]
#            #street1Raises=[]
#            #street2Raises=[]
#            #street3Raises=[]
#            #street4Raises=[]
#
#            # Summary figures for hand table:
#            result={}
#            result['playersVpi']=0
#            result['playersAtStreet1']=0
#            result['playersAtStreet2']=0
#            result['playersAtStreet3']=0
#            result['playersAtStreet4']=0
#            result['playersAtShowdown']=0
#            result['street0Raises']=0
#            result['street1Raises']=0
#            result['street2Raises']=0
#            result['street3Raises']=0
#            result['street4Raises']=0
#            result['street1Pot']=0
#            result['street2Pot']=0
#            result['street3Pot']=0
#            result['street4Pot']=0
#            result['showdownPot']=0
#
#            firstPfRaiseByNo=-1
#            firstPfRaiserId=-1
#            firstPfRaiserNo=-1
#            firstPfCallByNo=-1
#            firstPfCallerId=-1
#
#            for i, action in enumerate(actionTypeByNo[0]):
#                if action[1] == "bet":
#                    firstPfRaiseByNo = i
#                    firstPfRaiserId = action[0]
#                    for j, pid in enumerate(player_ids):
#                        if pid == firstPfRaiserId:
#                            firstPfRaiserNo = j
#                            break
#                    break
#            for i, action in enumerate(actionTypeByNo[0]):
#                if action[1] == "call":
#                    firstPfCallByNo = i
#                    firstPfCallerId = action[0]
#                    break
#            firstPlayId = firstPfCallerId
#            if firstPfRaiseByNo <> -1:
#                if firstPfRaiseByNo < firstPfCallByNo or firstPfCallByNo == -1:
#                    firstPlayId = firstPfRaiserId
#
#
#            cutoffId=-1
#            buttonId=-1
#            sbId=-1
#            bbId=-1
#            if base=="hold":
#                for player, pos in enumerate(positions):
#                    if pos == 1:
#                        cutoffId = player_ids[player]
#                    if pos == 0:
#                        buttonId = player_ids[player]
#                    if pos == 'S':
#                        sbId = player_ids[player]
#                    if pos == 'B':
#                        bbId = player_ids[player]
#
#            someoneStole=False
#
#            #run a loop for each player preparing the actual values that will be commited to SQL
#            for player in xrange(len(player_ids)):
#                #set default values
#                myStreet0VPI=False
#                myStreet0Aggr=False
#                myStreet0_3BChance=False
#                myStreet0_3BDone=False
#                myStreet1Seen=False
#                myStreet2Seen=False
#                myStreet3Seen=False
#                myStreet4Seen=False
#                mySawShowdown=False
#                myStreet1Aggr=False
#                myStreet2Aggr=False
#                myStreet3Aggr=False
#                myStreet4Aggr=False
#                myOtherRaisedStreet1=False
#                myOtherRaisedStreet2=False
#                myOtherRaisedStreet3=False
#                myOtherRaisedStreet4=False
#                myFoldToOtherRaisedStreet1=False
#                myFoldToOtherRaisedStreet2=False
#                myFoldToOtherRaisedStreet3=False
#                myFoldToOtherRaisedStreet4=False
#                myWonWhenSeenStreet1=0.0
#                myWonAtSD=0.0
#                myStealAttemptChance=False
#                myStealAttempted=False
#                myStreet0Calls=0
#                myStreet1Calls=0
#                myStreet2Calls=0
#                myStreet3Calls=0
#                myStreet4Calls=0
#                myStreet0Bets=0
#                myStreet1Bets=0
#                myStreet2Bets=0
#                myStreet3Bets=0
#                myStreet4Bets=0
#                #myStreet0Raises=0
#                #myStreet1Raises=0
#                #myStreet2Raises=0
#                #myStreet3Raises=0
#                #myStreet4Raises=0
#
#                #calculate VPIP and PFR
#                street=0
#                heroPfRaiseCount=0
#                for currentAction in action_types[street][player]: # finally individual actions
#                    if currentAction == "bet":
#                        myStreet0Aggr = True
#                    if currentAction == "bet" or currentAction == "call":
#                        myStreet0VPI = True
#
#                if myStreet0VPI:
#                    result['playersVpi'] += 1
#                myStreet0Calls = action_types[street][player].count('call')
#                myStreet0Bets = action_types[street][player].count('bet')
#                # street0Raises = action_types[street][player].count('raise')  bet count includes raises for now
#                result['street0Raises'] += myStreet0Bets
#
#                #PF3BChance and PF3B
#                pfFold=-1
#                pfRaise=-1
#                if firstPfRaiseByNo != -1:
#                    for i, actionType in enumerate(actionTypeByNo[0]):
#                        if actionType[0] == player_ids[player]:
#                            if actionType[1] == "bet" and pfRaise == -1 and i > firstPfRaiseByNo:
#                                pfRaise = i
#                            if actionType[1] == "fold" and pfFold == -1:
#                                pfFold = i
#                    if pfFold == -1 or pfFold > firstPfRaiseByNo:
#                        myStreet0_3BChance = True
#                        if pfRaise > firstPfRaiseByNo:
#                            myStreet0_3BDone = True
#
#                #steal calculations
#                if base=="hold":
#                    if len(player_ids)>=3: # no point otherwise  # was 5, use 3 to match pokertracker definition
#                        if positions[player]==1:
#                            if      firstPfRaiserId==player_ids[player] \
#                               and (firstPfCallByNo==-1 or firstPfCallByNo>firstPfRaiseByNo):
#                                myStealAttempted=True
#                                myStealAttemptChance=True
#                            if firstPlayId==cutoffId or firstPlayId==buttonId or firstPlayId==sbId or firstPlayId==bbId or firstPlayId==-1:
#                                myStealAttemptChance=True
#                        if positions[player]==0:
#                            if      firstPfRaiserId==player_ids[player] \
#                               and (firstPfCallByNo==-1 or firstPfCallByNo>firstPfRaiseByNo):
#                                myStealAttempted=True
#                                myStealAttemptChance=True
#                            if firstPlayId==buttonId or firstPlayId==sbId or firstPlayId==bbId or firstPlayId==-1:
#                                myStealAttemptChance=True
#                        if positions[player]=='S':
#                            if      firstPfRaiserId==player_ids[player] \
#                               and (firstPfCallByNo==-1 or firstPfCallByNo>firstPfRaiseByNo):
#                                myStealAttempted=True
#                                myStealAttemptChance=True
#                            if firstPlayId==sbId or firstPlayId==bbId or firstPlayId==-1:
#                                myStealAttemptChance=True
#                        if positions[player]=='B':
#                            pass
#
#                        if myStealAttempted:
#                            someoneStole=True
#
#
#                #calculate saw* values
#                isAllIn = False
#                if any(i for i in allIns[0][player]):
#                    isAllIn = True
#                if (len(action_types[1][player])>0 or isAllIn):
#                    myStreet1Seen = True
#
#                    if any(i for i in allIns[1][player]):
#                        isAllIn = True
#                    if (len(action_types[2][player])>0 or isAllIn):
#                        myStreet2Seen = True
#
#                        if any(i for i in allIns[2][player]):
#                            isAllIn = True
#                        if (len(action_types[3][player])>0 or isAllIn):
#                            myStreet3Seen = True
#
#                            #print "base:", base
#                            if base=="hold":
#                                mySawShowdown = True
#                                if any(actiontype == "fold" for actiontype in action_types[3][player]):
#                                    mySawShowdown = False
#                            else:
#                                #print "in else"
#                                if any(i for i in allIns[3][player]):
#                                    isAllIn = True
#                                if (len(action_types[4][player])>0 or isAllIn):
#                                    #print "in if"
#                                    myStreet4Seen = True
#
#                                    mySawShowdown = True
#                                    if any(actiontype == "fold" for actiontype in action_types[4][player]):
#                                        mySawShowdown = False
#
#                if myStreet1Seen:
#                    result['playersAtStreet1'] += 1
#                if myStreet2Seen:
#                    result['playersAtStreet2'] += 1
#                if myStreet3Seen:
#                    result['playersAtStreet3'] += 1
#                if myStreet4Seen:
#                    result['playersAtStreet4'] += 1
#                if mySawShowdown:
#                    result['playersAtShowdown'] += 1
#
#                #flop stuff
#                street=1
#                if myStreet1Seen:
#                    if any(actiontype == "bet" for actiontype in action_types[street][player]):
#                        myStreet1Aggr = True
#
#                    myStreet1Calls = action_types[street][player].count('call')
#                    myStreet1Bets = action_types[street][player].count('bet')
#                    # street1Raises = action_types[street][player].count('raise')  bet count includes raises for now
#                    result['street1Raises'] += myStreet1Bets
#
#                    for otherPlayer in xrange(len(player_ids)):
#                        if player==otherPlayer:
#                            pass
#                        else:
#                            for countOther in xrange(len(action_types[street][otherPlayer])):
#                                if action_types[street][otherPlayer][countOther]=="bet":
#                                    myOtherRaisedStreet1=True
#                                    for countOtherFold in xrange(len(action_types[street][player])):
#                                        if action_types[street][player][countOtherFold]=="fold":
#                                            myFoldToOtherRaisedStreet1=True
#
#                #turn stuff - copy of flop with different vars
#                street=2
#                if myStreet2Seen:
#                    if any(actiontype == "bet" for actiontype in action_types[street][player]):
#                        myStreet2Aggr = True
#
#                    myStreet2Calls = action_types[street][player].count('call')
#                    myStreet2Bets = action_types[street][player].count('bet')
#                    # street2Raises = action_types[street][player].count('raise')  bet count includes raises for now
#                    result['street2Raises'] += myStreet2Bets
#
#                    for otherPlayer in xrange(len(player_ids)):
#                        if player==otherPlayer:
#                            pass
#                        else:
#                            for countOther in xrange(len(action_types[street][otherPlayer])):
#                                if action_types[street][otherPlayer][countOther]=="bet":
#                                    myOtherRaisedStreet2=True
#                                    for countOtherFold in xrange(len(action_types[street][player])):
#                                        if action_types[street][player][countOtherFold]=="fold":
#                                            myFoldToOtherRaisedStreet2=True
#
#                #river stuff - copy of flop with different vars
#                street=3
#                if myStreet3Seen:
#                    if any(actiontype == "bet" for actiontype in action_types[street][player]):
#                            myStreet3Aggr = True
#
#                    myStreet3Calls = action_types[street][player].count('call')
#                    myStreet3Bets = action_types[street][player].count('bet')
#                    # street3Raises = action_types[street][player].count('raise')  bet count includes raises for now
#                    result['street3Raises'] += myStreet3Bets
#
#                    for otherPlayer in xrange(len(player_ids)):
#                        if player==otherPlayer:
#                            pass
#                        else:
#                            for countOther in xrange(len(action_types[street][otherPlayer])):
#                                if action_types[street][otherPlayer][countOther]=="bet":
#                                    myOtherRaisedStreet3=True
#                                    for countOtherFold in xrange(len(action_types[street][player])):
#                                        if action_types[street][player][countOtherFold]=="fold":
#                                            myFoldToOtherRaisedStreet3=True
#
#                #stud river stuff - copy of flop with different vars
#                street=4
#                if myStreet4Seen:
#                    if any(actiontype == "bet" for actiontype in action_types[street][player]):
#                        myStreet4Aggr=True
#
#                    myStreet4Calls = action_types[street][player].count('call')
#                    myStreet4Bets = action_types[street][player].count('bet')
#                    # street4Raises = action_types[street][player].count('raise')  bet count includes raises for now
#                    result['street4Raises'] += myStreet4Bets
#
#                    for otherPlayer in xrange(len(player_ids)):
#                        if player==otherPlayer:
#                            pass
#                        else:
#                            for countOther in xrange(len(action_types[street][otherPlayer])):
#                                if action_types[street][otherPlayer][countOther]=="bet":
#                                    myOtherRaisedStreet4=True
#                                    for countOtherFold in xrange(len(action_types[street][player])):
#                                        if action_types[street][player][countOtherFold]=="fold":
#                                            myFoldToOtherRaisedStreet4=True
#
#                if winnings[player] != 0:
#                    if myStreet1Seen:
#                        myWonWhenSeenStreet1 = winnings[player] / float(totalWinnings)
#                        if mySawShowdown:
#                            myWonAtSD=myWonWhenSeenStreet1
#
#                #add each value to the appropriate array
#                street0VPI.append(myStreet0VPI)
#                street0Aggr.append(myStreet0Aggr)
#                street0_3BChance.append(myStreet0_3BChance)
#                street0_3BDone.append(myStreet0_3BDone)
#                street1Seen.append(myStreet1Seen)
#                street2Seen.append(myStreet2Seen)
#                street3Seen.append(myStreet3Seen)
#                street4Seen.append(myStreet4Seen)
#                sawShowdown.append(mySawShowdown)
#                street1Aggr.append(myStreet1Aggr)
#                street2Aggr.append(myStreet2Aggr)
#                street3Aggr.append(myStreet3Aggr)
#                street4Aggr.append(myStreet4Aggr)
#                otherRaisedStreet1.append(myOtherRaisedStreet1)
#                otherRaisedStreet2.append(myOtherRaisedStreet2)
#                otherRaisedStreet3.append(myOtherRaisedStreet3)
#                otherRaisedStreet4.append(myOtherRaisedStreet4)
#                foldToOtherRaisedStreet1.append(myFoldToOtherRaisedStreet1)
#                foldToOtherRaisedStreet2.append(myFoldToOtherRaisedStreet2)
#                foldToOtherRaisedStreet3.append(myFoldToOtherRaisedStreet3)
#                foldToOtherRaisedStreet4.append(myFoldToOtherRaisedStreet4)
#                wonWhenSeenStreet1.append(myWonWhenSeenStreet1)
#                wonAtSD.append(myWonAtSD)
#                stealAttemptChance.append(myStealAttemptChance)
#                stealAttempted.append(myStealAttempted)
#                if base=="hold":
#                    pos=positions[player]
#                    if pos=='B':
#                        hudDataPositions.append('B')
#                    elif pos=='S':
#                        hudDataPositions.append('S')
#                    elif pos==0:
#                        hudDataPositions.append('D')
#                    elif pos==1:
#                        hudDataPositions.append('C')
#                    elif pos>=2 and pos<=4:
#                        hudDataPositions.append('M')
#                    elif pos>=5 and pos<=8:
#                        hudDataPositions.append('E')
#                    ### RHH Added this elif to handle being a dead hand before the BB (pos==9)
#                    elif pos==9:
#                        hudDataPositions.append('X')
#                    else:
#                        raise FpdbError("invalid position")
#                elif base=="stud":
#                    #todo: stud positions and steals
#                    pass
#
#                street0Calls.append(myStreet0Calls)
#                street1Calls.append(myStreet1Calls)
#                street2Calls.append(myStreet2Calls)
#                street3Calls.append(myStreet3Calls)
#                street4Calls.append(myStreet4Calls)
#                street0Bets.append(myStreet0Bets)
#                street1Bets.append(myStreet1Bets)
#                street2Bets.append(myStreet2Bets)
#                street3Bets.append(myStreet3Bets)
#                street4Bets.append(myStreet4Bets)
#                #street0Raises.append(myStreet0Raises)
#                #street1Raises.append(myStreet1Raises)
#                #street2Raises.append(myStreet2Raises)
#                #street3Raises.append(myStreet3Raises)
#                #street4Raises.append(myStreet4Raises)
#
#            #add each array to the to-be-returned dictionary
#            result['street0VPI']=street0VPI
#            result['street0Aggr']=street0Aggr
#            result['street0_3BChance']=street0_3BChance
#            result['street0_3BDone']=street0_3BDone
#            result['street1Seen']=street1Seen
#            result['street2Seen']=street2Seen
#            result['street3Seen']=street3Seen
#            result['street4Seen']=street4Seen
#            result['sawShowdown']=sawShowdown
#
#            result['street1Aggr']=street1Aggr
#            result['otherRaisedStreet1']=otherRaisedStreet1
#            result['foldToOtherRaisedStreet1']=foldToOtherRaisedStreet1
#            result['street2Aggr']=street2Aggr
#            result['otherRaisedStreet2']=otherRaisedStreet2
#            result['foldToOtherRaisedStreet2']=foldToOtherRaisedStreet2
#            result['street3Aggr']=street3Aggr
#            result['otherRaisedStreet3']=otherRaisedStreet3
#            result['foldToOtherRaisedStreet3']=foldToOtherRaisedStreet3
#            result['street4Aggr']=street4Aggr
#            result['otherRaisedStreet4']=otherRaisedStreet4
#            result['foldToOtherRaisedStreet4']=foldToOtherRaisedStreet4
#            result['wonWhenSeenStreet1']=wonWhenSeenStreet1
#            result['wonAtSD']=wonAtSD
#            result['stealAttemptChance']=stealAttemptChance
#            result['stealAttempted']=stealAttempted
#            result['street0Calls']=street0Calls
#            result['street1Calls']=street1Calls
#            result['street2Calls']=street2Calls
#            result['street3Calls']=street3Calls
#            result['street4Calls']=street4Calls
#            result['street0Bets']=street0Bets
#            result['street1Bets']=street1Bets
#            result['street2Bets']=street2Bets
#            result['street3Bets']=street3Bets
#            result['street4Bets']=street4Bets
#            #result['street0Raises']=street0Raises
#            #result['street1Raises']=street1Raises
#            #result['street2Raises']=street2Raises
#            #result['street3Raises']=street3Raises
#            #result['street4Raises']=street4Raises
#
#            #now the various steal values
#            foldBbToStealChance=[]
#            foldedBbToSteal=[]
#            foldSbToStealChance=[]
#            foldedSbToSteal=[]
#            for player in xrange(len(player_ids)):
#                myFoldBbToStealChance=False
#                myFoldedBbToSteal=False
#                myFoldSbToStealChance=False
#                myFoldedSbToSteal=False
#
#                if base=="hold":
#                    if someoneStole and (positions[player]=='B' or positions[player]=='S') and firstPfRaiserId!=player_ids[player]:
#                        street=0
#                        for count in xrange(len(action_types[street][player])):#individual actions
#                            if positions[player]=='B':
#                                myFoldBbToStealChance=True
#                                if action_types[street][player][count]=="fold":
#                                    myFoldedBbToSteal=True
#                            if positions[player]=='S':
#                                myFoldSbToStealChance=True
#                                if action_types[street][player][count]=="fold":
#                                    myFoldedSbToSteal=True
#
#
#                foldBbToStealChance.append(myFoldBbToStealChance)
#                foldedBbToSteal.append(myFoldedBbToSteal)
#                foldSbToStealChance.append(myFoldSbToStealChance)
#                foldedSbToSteal.append(myFoldedSbToSteal)
#            result['foldBbToStealChance']=foldBbToStealChance
#            result['foldedBbToSteal']=foldedBbToSteal
#            result['foldSbToStealChance']=foldSbToStealChance
#            result['foldedSbToSteal']=foldedSbToSteal
#
#            #now CB
#            street1CBChance=[]
#            street1CBDone=[]
#            didStreet1CB=[]
#            for player in xrange(len(player_ids)):
#                myStreet1CBChance=False
#                myStreet1CBDone=False
#
#                if street0VPI[player]:
#                    myStreet1CBChance=True
#                    if street1Aggr[player]:
#                        myStreet1CBDone=True
#                        didStreet1CB.append(player_ids[player])
#
#                street1CBChance.append(myStreet1CBChance)
#                street1CBDone.append(myStreet1CBDone)
#            result['street1CBChance']=street1CBChance
#            result['street1CBDone']=street1CBDone
#
#            #now 2B
#            street2CBChance=[]
#            street2CBDone=[]
#            didStreet2CB=[]
#            for player in xrange(len(player_ids)):
#                myStreet2CBChance=False
#                myStreet2CBDone=False
#
#                if street1CBDone[player]:
#                    myStreet2CBChance=True
#                    if street2Aggr[player]:
#                        myStreet2CBDone=True
#                        didStreet2CB.append(player_ids[player])
#
#                street2CBChance.append(myStreet2CBChance)
#                street2CBDone.append(myStreet2CBDone)
#            result['street2CBChance']=street2CBChance
#            result['street2CBDone']=street2CBDone
#
#            #now 3B
#            street3CBChance=[]
#            street3CBDone=[]
#            didStreet3CB=[]
#            for player in xrange(len(player_ids)):
#                myStreet3CBChance=False
#                myStreet3CBDone=False
#
#                if street2CBDone[player]:
#                    myStreet3CBChance=True
#                    if street3Aggr[player]:
#                        myStreet3CBDone=True
#                        didStreet3CB.append(player_ids[player])
#
#                street3CBChance.append(myStreet3CBChance)
#                street3CBDone.append(myStreet3CBDone)
#            result['street3CBChance']=street3CBChance
#            result['street3CBDone']=street3CBDone
#
#            #and 4B
#            street4CBChance=[]
#            street4CBDone=[]
#            didStreet4CB=[]
#            for player in xrange(len(player_ids)):
#                myStreet4CBChance=False
#                myStreet4CBDone=False
#
#                if street3CBDone[player]:
#                    myStreet4CBChance=True
#                    if street4Aggr[player]:
#                        myStreet4CBDone=True
#                        didStreet4CB.append(player_ids[player])
#
#                street4CBChance.append(myStreet4CBChance)
#                street4CBDone.append(myStreet4CBDone)
#            result['street4CBChance']=street4CBChance
#            result['street4CBDone']=street4CBDone
#
#
#            result['position']=hudDataPositions
#
#            foldToStreet1CBChance=[]
#            foldToStreet1CBDone=[]
#            foldToStreet2CBChance=[]
#            foldToStreet2CBDone=[]
#            foldToStreet3CBChance=[]
#            foldToStreet3CBDone=[]
#            foldToStreet4CBChance=[]
#            foldToStreet4CBDone=[]
#
#            for player in xrange(len(player_ids)):
#                myFoldToStreet1CBChance=False
#                myFoldToStreet1CBDone=False
#                foldToStreet1CBChance.append(myFoldToStreet1CBChance)
#                foldToStreet1CBDone.append(myFoldToStreet1CBDone)
#
#                myFoldToStreet2CBChance=False
#                myFoldToStreet2CBDone=False
#                foldToStreet2CBChance.append(myFoldToStreet2CBChance)
#                foldToStreet2CBDone.append(myFoldToStreet2CBDone)
#
#                myFoldToStreet3CBChance=False
#                myFoldToStreet3CBDone=False
#                foldToStreet3CBChance.append(myFoldToStreet3CBChance)
#                foldToStreet3CBDone.append(myFoldToStreet3CBDone)
#
#                myFoldToStreet4CBChance=False
#                myFoldToStreet4CBDone=False
#                foldToStreet4CBChance.append(myFoldToStreet4CBChance)
#                foldToStreet4CBDone.append(myFoldToStreet4CBDone)
#
#            if len(didStreet1CB)>=1:
#                generateFoldToCB(1, player_ids, didStreet1CB, street1CBDone, foldToStreet1CBChance, foldToStreet1CBDone, actionTypeByNo)
#
#                if len(didStreet2CB)>=1:
#                    generateFoldToCB(2, player_ids, didStreet2CB, street2CBDone, foldToStreet2CBChance, foldToStreet2CBDone, actionTypeByNo)
#
#                    if len(didStreet3CB)>=1:
#                        generateFoldToCB(3, player_ids, didStreet3CB, street3CBDone, foldToStreet3CBChance, foldToStreet3CBDone, actionTypeByNo)
#
#                        if len(didStreet4CB)>=1:
#                            generateFoldToCB(4, player_ids, didStreet4CB, street4CBDone, foldToStreet4CBChance, foldToStreet4CBDone, actionTypeByNo)
#
#            result['foldToStreet1CBChance']=foldToStreet1CBChance
#            result['foldToStreet1CBDone']=foldToStreet1CBDone
#            result['foldToStreet2CBChance']=foldToStreet2CBChance
#            result['foldToStreet2CBDone']=foldToStreet2CBDone
#            result['foldToStreet3CBChance']=foldToStreet3CBChance
#            result['foldToStreet3CBDone']=foldToStreet3CBDone
#            result['foldToStreet4CBChance']=foldToStreet4CBChance
#            result['foldToStreet4CBDone']=foldToStreet4CBDone
#
#
#            totalProfit=[]
#
#            street1CheckCallRaiseChance=[]
#            street1CheckCallRaiseDone=[]
#            street2CheckCallRaiseChance=[]
#            street2CheckCallRaiseDone=[]
#            street3CheckCallRaiseChance=[]
#            street3CheckCallRaiseDone=[]
#            street4CheckCallRaiseChance=[]
#            street4CheckCallRaiseDone=[]
#            #print "b4 totprof calc, len(playerIds)=", len(player_ids)
#            for pl in xrange(len(player_ids)):
#                #print "pl=", pl
#                myTotalProfit=winnings[pl]  # still need to deduct other costs
#                if antes:
#                    myTotalProfit=winnings[pl] - antes[pl]
#                for i in xrange(len(actionTypes)): #iterate through streets
#                    #for j in xrange(len(actionTypes[i])): #iterate through names (using pl loop above)
#                        for k in xrange(len(actionTypes[i][pl])): #iterate through individual actions of that player on that street
#                            myTotalProfit -= actionAmounts[i][pl][k]
#
#                myStreet1CheckCallRaiseChance=False
#                myStreet1CheckCallRaiseDone=False
#                myStreet2CheckCallRaiseChance=False
#                myStreet2CheckCallRaiseDone=False
#                myStreet3CheckCallRaiseChance=False
#                myStreet3CheckCallRaiseDone=False
#                myStreet4CheckCallRaiseChance=False
#                myStreet4CheckCallRaiseDone=False
#
#                #print "myTotalProfit=", myTotalProfit
#                totalProfit.append(myTotalProfit)
#                #print "totalProfit[]=", totalProfit
#
#                street1CheckCallRaiseChance.append(myStreet1CheckCallRaiseChance)
#                street1CheckCallRaiseDone.append(myStreet1CheckCallRaiseDone)
#                street2CheckCallRaiseChance.append(myStreet2CheckCallRaiseChance)
#                street2CheckCallRaiseDone.append(myStreet2CheckCallRaiseDone)
#                street3CheckCallRaiseChance.append(myStreet3CheckCallRaiseChance)
#                street3CheckCallRaiseDone.append(myStreet3CheckCallRaiseDone)
#                street4CheckCallRaiseChance.append(myStreet4CheckCallRaiseChance)
#                street4CheckCallRaiseDone.append(myStreet4CheckCallRaiseDone)
#
#            result['totalProfit']=totalProfit
#            #print "res[totalProfit]=", result['totalProfit']
#
#            result['street1CheckCallRaiseChance']=street1CheckCallRaiseChance
#            result['street1CheckCallRaiseDone']=street1CheckCallRaiseDone
#            result['street2CheckCallRaiseChance']=street2CheckCallRaiseChance
#            result['street2CheckCallRaiseDone']=street2CheckCallRaiseDone
#            result['street3CheckCallRaiseChance']=street3CheckCallRaiseChance
#            result['street3CheckCallRaiseDone']=street3CheckCallRaiseDone
#            result['street4CheckCallRaiseChance']=street4CheckCallRaiseChance
#            result['street4CheckCallRaiseDone']=street4CheckCallRaiseDone
#            return result
#        #end def generateHudCacheData
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

        for (i, street) in enumerate(hand.actionStreets[2:]):
            actors = {}
            for act in hand.actions[street]:
                actors[act[0]] = 1
            self.hands['playersAtStreet%s' % str(i+1)] = len(actors.keys())

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
