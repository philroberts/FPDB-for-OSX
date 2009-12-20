#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

#Copyright 2008 Steffen Jobbagy-Felso
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

#This file contains simple functions for fpdb

#Aiming to eventually remove this module, functions will move to, eg:
#fpdb_db      db create/re-create/management/etc
#Hands        or related files for saving hands to db, etc

import datetime
import time
import re
import sys
from Exceptions import *
import locale

import Card

PS  = 1
FTP = 2

# TODO: these constants are also used in fpdb_save_to_db and others, is there a way to do like C #define, and #include ?
# answer - yes. These are defined in fpdb_db so are accessible through that class.
MYSQL_INNODB    = 2
PGSQL           = 3
SQLITE          = 4

LOCALE_ENCODING = locale.getdefaultlocale()[1]

#returns an array of the total money paid. intending to add rebuys/addons here
def calcPayin(count, buyin, fee):
    return [buyin + fee for i in xrange(count)]
#end def calcPayin

def checkPositions(positions):
    """ verify positions are valid """
    if any(not (p == "B" or p == "S" or (p >= 0 and p <= 9)) for p in positions):
        raise FpdbError("invalid position '"+p+"' found in checkPositions")
    ### RHH modified to allow for "position 9" here (pos==9 is when you're a dead hand before the BB
    ### eric - position 8 could be valid - if only one blind is posted, but there's still 10 people, ie a sitout is present, and the small is dead...

def classifyLines(hand, category, lineTypes, lineStreets):
    """ makes a list of classifications for each line for further processing
        manipulates passed arrays """
    currentStreet = "predeal"
    done = False #set this to true once we reach the last relevant line (the summary, except rake, is all repeats)
    for i, line in enumerate(hand):
        if done:
            if "[" not in line or "mucked [" not in line:
                lineTypes.append("ignore")
            else:
                lineTypes.append("cards")
        elif line.startswith("Dealt to"):
            lineTypes.append("cards")
        elif i == 0:
            lineTypes.append("header")
        elif line.startswith("Table '"):
            lineTypes.append("table")
        elif line.startswith("Seat ") and ( ("in chips" in line) or "($" in line):
            lineTypes.append("name")
        elif isActionLine(line):
            lineTypes.append("action")
            if " posts " in line or " posts the " in line:
                currentStreet="preflop"
        elif " antes " in line or " posts the ante " in line:
            lineTypes.append("ante")
        elif line.startswith("*** FLOP *** ["):
            lineTypes.append("cards")
            currentStreet="flop"
        elif line.startswith("*** TURN *** ["):
            lineTypes.append("cards")
            currentStreet="turn"
        elif line.startswith("*** RIVER *** ["):
            lineTypes.append("cards")
            currentStreet="river"
        elif line.startswith("*** 3"):
            lineTypes.append("ignore")
            currentStreet=0
        elif line.startswith("*** 4"):
            lineTypes.append("ignore")
            currentStreet=1
        elif line.startswith("*** 5"):
            lineTypes.append("ignore")
            currentStreet=2
        elif line.startswith("*** 6"):
            lineTypes.append("ignore")
            currentStreet=3
        elif line.startswith("*** 7") or line == "*** RIVER ***":
            lineTypes.append("ignore")
            currentStreet=4
        elif isWinLine(line):
            lineTypes.append("win")
        elif line.startswith("Total pot ") and "Rake" in line:
            lineTypes.append("rake")
            done=True
        elif "*** SHOW DOWN ***" in line or "*** SUMMARY ***" in line:
            lineTypes.append("ignore")
            #print "in classifyLine, showdown or summary"
        elif " shows [" in line:
            lineTypes.append("cards")
        else:
            raise FpdbError("unrecognised linetype in:"+hand[i])
        lineStreets.append(currentStreet)

def convert3B4B(category, limit_type, actionTypes, actionAmounts):
    """calculates the actual bet amounts in the given amount array and changes it accordingly."""
    for i in xrange(len(actionTypes)):
        for j in xrange(len(actionTypes[i])):
            bets = []
            for k in xrange(len(actionTypes[i][j])):
                if (actionTypes[i][j][k] == "bet"):
                    bets.append((i,j,k))
            if (len(bets)>=2):
                #print "len(bets) 2 or higher, need to correct it. bets:",bets,"len:",len(bets)
                for betNo in reversed(xrange (1,len(bets))):
                    amount2 = actionAmounts[bets[betNo][0]][bets[betNo][1]][bets[betNo][2]]
                    amount1 = actionAmounts[bets[betNo-1][0]][bets[betNo-1][1]][bets[betNo-1][2]]
                    actionAmounts[bets[betNo][0]][bets[betNo][1]][bets[betNo][2]] = amount2 - amount1

def convertBlindBet(actionTypes, actionAmounts):
    """ Corrects the bet amount if the player had to pay blinds """
    i = 0#setting street to pre-flop
    for j in xrange(len(actionTypes[i])):#playerloop
        blinds = []
        bets = []
        for k in xrange(len(actionTypes[i][j])):
            if actionTypes[i][j][k] == "blind":
                blinds.append((i,j,k))

            if blinds and actionTypes[i][j][k] == "bet":
                bets.append((i,j,k))
                if len(bets) == 1:
                    blind_amount=actionAmounts[blinds[0][0]][blinds[0][1]][blinds[0][2]]
                    bet_amount=actionAmounts[bets[0][0]][bets[0][1]][bets[0][2]]
                    actionAmounts[bets[0][0]][bets[0][1]][bets[0][2]] = bet_amount - blind_amount

#converts the strings in the given array to ints (changes the passed array, no returning). see table design for conversion details
#todo: make this use convertCardValuesBoard
def convertCardValues(arr):
    map(convertCardValuesBoard, arr)

# a 0-card is one in a stud game that we did not see or was not shown
card_map = { 0: 0, "2": 2, "3" : 3, "4" : 4, "5" : 5, "6" : 6, "7" : 7, "8" : 8,
            "9" : 9, "T" : 10, "J" : 11, "Q" : 12, "K" : 13, "A" : 14}

def convertCardValuesBoard(arr):
    """ converts the strings in the given array to ints
        (changes the passed array, no returning). see table design for
        conversion details """
    for i in xrange(len(arr)):
        arr[i] = card_map[arr[i]]

def createArrays(category, seats, card_values, card_suits, antes, winnings,
                 rakes, action_types, allIns, action_amounts, actionNos,
                 actionTypeByNo):
    """ this creates the 2D/3D arrays. manipulates the passed arrays instead of returning.    """
    for i in xrange(seats):#create second dimension arrays
        card_values.append( [] )
        card_suits.append( [] )
        antes.append(0)
        winnings.append(0)
        rakes.append(0)

    streetCount = 4 if (category == "holdem" or category == "omahahi" or
                        category == "omahahilo") else 5

    for i in xrange(streetCount): #build the first dimension array, for streets
        action_types.append([])
        allIns.append([])
        action_amounts.append([])
        actionNos.append([])
        actionTypeByNo.append([])
        for j in xrange(seats): # second dimension arrays: players
            action_types[i].append([])
            allIns[i].append([])
            action_amounts[i].append([])
            actionNos[i].append([])
#    if (category=="holdem" or category=="omahahi" or category=="omahahilo"):
#        pass
    if category == "razz" or category == "studhi" or category == "studhilo": #need to fill card arrays.
        for i in xrange(seats):
            for j in xrange(7):
                card_values[i].append(0)
                card_suits[i].append("x")
#    else:
#        raise FpdbError("invalid category")
#end def createArrays

def fill_board_cards(board_values, board_suits):
    """ fill up the two board card arrays """
    while len(board_values) < 5:
        board_values.append(0)
        board_suits.append("x")

def fillCardArrays(player_count, base, category, card_values, card_suits):
    """fills up the two card arrays"""
    if category == "holdem":
        cardCount = 2
    elif category == "omahahi" or category == "omahahilo":
        cardCount = 4
    elif base == "stud":
        cardCount = 7
    else:
        raise FpdbError("invalid category:", category)

    for i in xrange(player_count):
        while len(card_values[i]) < cardCount:
            card_values[i].append(0)
            card_suits[i].append("x")
#end def fillCardArrays

#filters out a player that folded before paying ante or blinds. This should be called
#before calling the actual hand parser. manipulates hand, no return.
def filterAnteBlindFold(hand):
    #todo: this'll only get rid of one ante folder, not multiple ones
    #todo: in tourneys this should not be removed but
    #print "start of filterAnteBlindFold"
    pre3rd = []
    for i, line in enumerate(hand):
        if line.startswith("*** 3") or line.startswith("*** HOLE"):
            pre3rd = hand[0:i]

    foldeeName = None
    for line in pre3rd:
        if line.endswith("folds") or line.endswith("is sitting out") or line.endswith(" stands up"): #found ante fold or timeout
            pos = line.find(" folds")
            foldeeName = line[0:pos]
            if pos == -1 and " in chips)" not in line:
                pos = line.find(" is sitting out")
                foldeeName = line[0:pos]
            if pos == -1:
                pos = line.find(" stands up")
                foldeeName = line[0:pos]
            if pos == -1:
                pos1 = line.find(": ") + 2
                pos2 = line.find(" (")
                foldeeName = line[pos1:pos2]

    if foldeeName is not None:
        #print "filterAnteBlindFold, foldeeName:",foldeeName
        for i, line in enumerate(hand):
            if foldeeName in line:
                hand[i] = None

    return [line for line in hand if line]

def stripEOLspaces(str):
    return str.rstrip()

def filterCrap(hand, isTourney):
    """ removes useless lines as well as trailing spaces """

    #remove trailing spaces at end of line
    hand = [line.rstrip() for line in hand]

    #general variable position word filter/string filter
    for i in xrange(len(hand)):
        if hand[i].startswith("Board ["):
            hand[i] = False
        elif hand[i].find(" out of hand ")!=-1:
            hand[i]=hand[i][:-56]
        elif "($0 in chips)" in hand[i]:
            hand[i] = False
        elif hand[i]=="*** HOLE CARDS ***":
            hand[i] = False
        elif hand[i].endswith("has been disconnected"):
            hand[i] = False
        elif hand[i].endswith("has requested TIME"):
            hand[i] = False
        elif hand[i].endswith("has returned"):
            hand[i] = False
        elif hand[i].endswith("will be allowed to play after the button"):
            hand[i] = False
        elif hand[i].endswith("has timed out"):
            hand[i] = False
        elif hand[i].endswith("has timed out while disconnected"):
            hand[i] = False
        elif hand[i].endswith("has timed out while being disconnected"):
            hand[i] = False
        elif hand[i].endswith("is connected"):
            hand[i] = False
        elif hand[i].endswith("is disconnected"):
            hand[i] = False
        elif hand[i].find(" is low with [")!=-1:
            hand[i] = False
        elif hand[i].endswith(" mucks"):
            hand[i] = False
        elif hand[i].endswith(": mucks hand"):
            hand[i] = False
        elif hand[i] == "No low hand qualified":
            hand[i] = False
        elif hand[i] == "Pair on board - a double bet is allowed":
            hand[i] = False
        elif " shows " in hand[i] and "[" not in hand[i]:
            hand[i] = False
        elif hand[i].startswith("The button is in seat #"):
            hand[i] = False
        #above is alphabetic, reorder below if bored
        elif hand[i].startswith("Time has expired"):
            hand[i] = False
        elif hand[i].endswith("has reconnected"):
            hand[i] = False
        elif hand[i].endswith("seconds left to act"):
            hand[i] = False
        elif hand[i].endswith("seconds to reconnect"):
            hand[i] = False
        elif hand[i].endswith("was removed from the table for failing to post"):
            hand[i] = False
        elif "joins the table at seat " in hand[i]:
            hand[i] = False
        elif (hand[i].endswith("leaves the table")):
            hand[i] = False
        elif "is high with " in hand[i]:
            hand[i] = False
        elif hand[i].endswith("doesn't show hand"):
            hand[i] = False
        elif hand[i].endswith("is being treated as all-in"):
            hand[i] = False
        elif " adds $" in hand[i]:
            hand[i] = False
        elif hand[i] == "Betting is capped":
            hand[i] = False
        elif (hand[i].find(" said, \"")!=-1):
            hand[i] = False

        if isTourney and not hand[i] == False:
            if (hand[i].endswith(" is sitting out") and (not hand[i].startswith("Seat "))):
                hand[i] = False
        elif hand[i]:
            if (hand[i].endswith(": sits out")):
                hand[i] = False
            elif (hand[i].endswith(" is sitting out")):
                hand[i] = False
    # python docs say this is identical to filter(None, list)
    # which removes all false items from the passed list (hand)
    hand = [line for line in hand if line]

    return hand

def float2int(string):
    """ takes a poker float (including , for thousand seperator) and
        converts it to an int """
    # Note that this automagically assumes US style currency formatters
    pos = string.find(",")
    if pos != -1: #remove , the thousand seperator
        string = "%s%s" % (string[0:pos], string[pos+1:])

    pos = string.find(".")
    if pos != -1: #remove decimal point
        string = "%s%s" % (string[0:pos], string[pos+1:])

    result = int(string)
    if pos == -1: #no decimal point - was in full dollars - need to multiply with 100
        result *= 100
    return result

ActionLines = ( "calls $", ": calls ", "brings in for", "completes it to",
               "posts small blind", "posts the small blind", "posts big blind",
               "posts the big blind", "posts small & big blinds", "posts $",
               "posts a dead", "bets $", ": bets ", " raises")

def isActionLine(line):
    if line.endswith("folds"):
        return True
    elif line.endswith("checks"):
        return True
    elif line.startswith("Uncalled bet"):
        return True

    # searches for each member of ActionLines being in line, returns true
    # on first match .. neat func
    return any(x for x in ActionLines if x in line)

def isAlreadyInDB(db, gametypeID, siteHandNo):
    c = db.get_cursor()
    c.execute(db.sql.query['isAlreadyInDB'], (gametypeID, siteHandNo))
    result = c.fetchall()
    if len(result) >= 1:
        raise DuplicateError ("dupl")

def isRebuyOrAddon(topline):
    """isRebuyOrAddon not implemented yet"""
    return False

#returns whether the passed topline indicates a tournament or not
def isTourney(topline):
    return "Tournament" in topline

WinLines = ( "wins the pot", "ties for the ", "wins side pot", "wins the low main pot", "wins the high main pot",
             "wins the low",
             "wins the high pot", "wins the high side pot", "wins the main pot", "wins the side pot", "collected" )

def isWinLine(line):
    """ returns boolean whether the passed line is a win line """
    return any(x for x in WinLines if x in line)

#returns the amount of cash/chips put into the put in the given action line
def parseActionAmount(line, atype, isTourney):
    #if (line.endswith(" and is all-in")):
    # line=line[:-14]
    #elif (line.endswith(", and is all in")):
    # line=line[:-15]

    #ideally we should recognise this as an all-in if category is capXl
    if line.endswith(", and is capped"):
        line=line[:-15]
    if line.endswith(" and is capped"):
        line=line[:-14]

    if atype == "fold" or atype == "check":
        amount = 0
    elif atype == "unbet":
        pos1 = line.find("$") + 1
        if pos1 == 0:
            pos1 = line.find("(") + 1
        pos2 = line.find(")")
        amount = float2int(line[pos1:pos2])
    elif atype == "bet" and ": raises $" in line and "to $" in line:
        pos = line.find("to $")+4
        amount = float2int(line[pos:])
    else:
        if not isTourney:
            pos = line.rfind("$")+1
            #print "parseActionAmount, line:", line, "line[pos:]:", line[pos:]
            amount = float2int(line[pos:])
        else:
            #print "line:"+line+"EOL"
            pos = line.rfind(" ")+1
            #print "pos:",pos
            #print "pos of 20:", line.find("20")
            amount = int(line[pos:])

    if atype == "unbet":
        amount *= -1
    return amount
#end def parseActionAmount

#doesnt return anything, simply changes the passed arrays action_types and
# action_amounts. For stud this expects numeric streets (3-7), for
# holdem/omaha it expects predeal, preflop, flop, turn or river
def parseActionLine(base, isTourney, line, street, playerIDs, names, action_types, allIns, action_amounts, actionNos, actionTypeByNo):
    if street == "predeal" or street == "preflop":
        street = 0
    elif street == "flop":
        street = 1
    elif street == "turn":
        street = 2
    elif street == "river":
        street = 3

    nextActionNo = 0
    for player in xrange(len(actionNos[street])):
        for count in xrange(len(actionNos[street][player])):
            if actionNos[street][player][count]>=nextActionNo:
                nextActionNo=actionNos[street][player][count]+1

    (line, allIn) = goesAllInOnThisLine(line)
    atype = parseActionType(line)
    playerno = recognisePlayerNo(line, names, atype)
    amount = parseActionAmount(line, atype, isTourney)

    action_types[street][playerno].append(atype)
    allIns[street][playerno].append(allIn)
    action_amounts[street][playerno].append(amount)
    actionNos[street][playerno].append(nextActionNo)
    tmp=(playerIDs[playerno], atype)
    actionTypeByNo[street].append(tmp)

def goesAllInOnThisLine(line):
    """returns whether the player went all-in on this line and removes the all-in text from the line."""
    isAllIn = False
    if (line.endswith(" and is all-in")):
        line = line[:-14]
        isAllIn = True
    elif (line.endswith(", and is all in")):
        line = line[:-15]
        isAllIn = True
    return (line, isAllIn)

#returns the action type code (see table design) of the given action line
ActionTypes = { 'brings in for'                :"blind",
                ' posts $'                     :"blind",
                ' posts a dead '               :"blind",
                ' posts the small blind of $'  :"blind",
                ': posts big blind '           :"blind",
                ': posts small blind '         :"blind",
                ' posts the big blind of $'    :"blind",
                ': posts small & big blinds $' :"blind",
                ': posts small blind $'        :"blind",
                'calls'                        :"call",
                'completes it to'              :"bet",
                ' bets'                        :"bet",
                ' raises'                      :"bet"
               }
def parseActionType(line):
    if (line.startswith("Uncalled bet")):
        return "unbet"
    elif (line.endswith(" folds")):
        return "fold"
    elif (line.endswith(" checks")):
        return "check"
    else:
        for x in ActionTypes:
            if x in line:
                return ActionTypes[x]
    raise FpdbError ("failed to recognise actiontype in parseActionLine in: "+line)

#parses the ante out of the given line and checks which player paid it, updates antes accordingly.
def parseAnteLine(line, isTourney, names, antes):
    for i, name in enumerate(names):
        if line.startswith(name.encode(LOCALE_ENCODING)):
            pos = line.rfind("$") + 1
            if not isTourney:
                antes[i] += float2int(line[pos:])
            else:
                if "all-in" not in line:
                    pos = line.rfind(" ") + 1
                    antes[i] += int(line[pos:])
                else:
                    pos1 = line.rfind("ante") + 5
                    pos2 = line.find(" ", pos1)
                    antes[i] += int(line[pos1:pos2])

#returns the buyin of a tourney in cents
def parseBuyin(topline):
    pos1 = topline.find("$")+1
    if pos1 != 0:
        pos2 = topline.find("+")
    else:
        pos1 = topline.find("€")+3
        pos2 = topline.find("+")
    return float2int(topline[pos1:pos2])

#parses a card line and changes the passed arrays accordingly
#todo: reorganise this messy method
def parseCardLine(category, street, line, names, cardValues, cardSuits, boardValues, boardSuits):
    if line.startswith("Dealt to") or " shows [" in line or "mucked [" in line:
        playerNo = recognisePlayerNo(line, names, "card") #anything but unbet will be ok for that string

        pos = line.rfind("[")+1
        if category == "holdem":
            for i in (pos, pos+3):
                cardValues[playerNo].append(line[i:i+1])
                cardSuits[playerNo].append(line[i+1:i+2])
            if len(cardValues[playerNo]) != 2:
                if (cardValues[playerNo][0] == cardValues[playerNo][2] and
                    cardSuits[playerNo][1] == cardSuits[playerNo][3]):
                    cardValues[playerNo]=cardValues[playerNo][0:2]
                    cardSuits[playerNo]=cardSuits[playerNo][0:2]
                else:
                    print "line:",line,"cardValues[playerNo]:",cardValues[playerNo]
                    raise FpdbError("read too many/too few holecards in parseCardLine")
        elif category == "omahahi" or category == "omahahilo":
            for i in (pos, pos+3, pos+6, pos+9):
                cardValues[playerNo].append(line[i:i+1])
                cardSuits[playerNo].append(line[i+1:i+2])
            if (len(cardValues[playerNo])!=4):
                if (cardValues[playerNo][0] == cardValues[playerNo][4] and
                    cardSuits[playerNo][3] == cardSuits[playerNo][7]): #two tests will do
                    cardValues[playerNo] = cardValues[playerNo][0:4]
                    cardSuits[playerNo] = cardSuits[playerNo][0:4]
                else:
                    print "line:",line,"cardValues[playerNo]:",cardValues[playerNo]
                    raise FpdbError("read too many/too few holecards in parseCardLine")
        elif category == "razz" or category == "studhi" or category == "studhilo":
            if "shows" not in line and "mucked" not in line:
                #print "parseCardLine(in stud if), street:", street
                if line[pos+2]=="]": #-> not (hero and 3rd street)
                    cardValues[playerNo][street+2]=line[pos:pos+1]
                    cardSuits[playerNo][street+2]=line[pos+1:pos+2]
                else:
                    #print "hero card1:", line[pos:pos+2], "hero card2:", line[pos+3:pos+5], "hero card3:", line[pos+6:pos+8],
                    cardValues[playerNo][street]=line[pos:pos+1]
                    cardSuits[playerNo][street]=line[pos+1:pos+2]
                    cardValues[playerNo][street+1]=line[pos+3:pos+4]
                    cardSuits[playerNo][street+1]=line[pos+4:pos+5]
                    cardValues[playerNo][street+2]=line[pos+6:pos+7]
                    cardSuits[playerNo][street+2]=line[pos+7:pos+8]
            else:
                #print "parseCardLine(in stud else), street:", street
                cardValues[playerNo][0]=line[pos:pos+1]
                cardSuits[playerNo][0]=line[pos+1:pos+2]
                pos+=3
                cardValues[playerNo][1]=line[pos:pos+1]
                cardSuits[playerNo][1]=line[pos+1:pos+2]
                if street==4:
                    pos=pos=line.rfind("]")-2
                    cardValues[playerNo][6]=line[pos:pos+1]
                    cardSuits[playerNo][6]=line[pos+1:pos+2]
                    #print "cardValues:", cardValues
                    #print "cardSuits:", cardSuits
        else:
            print "line:",line,"street:",street
            raise FpdbError("invalid category")
        #print "end of parseCardLine/playercards, cardValues:",cardValues
    elif (line.startswith("*** FLOP ***")):
        pos=line.find("[")+1
        for i in (pos, pos+3, pos+6):
            boardValues.append(line[i:i+1])
            boardSuits.append(line[i+1:i+2])
        #print boardValues
    elif (line.startswith("*** TURN ***") or line.startswith("*** RIVER ***")):
        pos=line.find("[")+1
        pos=line.find("[", pos+1)+1
        boardValues.append(line[pos:pos+1])
        boardSuits.append(line[pos+1:pos+2])
        #print boardValues
    else:
        raise FpdbError ("unrecognised line:"+line)

def parseCashesAndSeatNos(lines):
    """parses the startCashes and seatNos of each player out of the given lines and returns them as a dictionary of two arrays"""
    cashes = []
    seatNos = []
    for i in xrange (len(lines)):
        pos2=lines[i].find(":")
        seatNos.append(int(lines[i][5:pos2]))

        pos1=lines[i].rfind("($")+2
        if pos1==1: #for tourneys - it's 1 instead of -1 due to adding 2 above
            pos1=lines[i].rfind("(")+1
        pos2=lines[i].find(" in chips")
        cashes.append(float2int(lines[i][pos1:pos2]))
    return {'startCashes':cashes, 'seatNos':seatNos}

#returns the buyin of a tourney in cents
def parseFee(topline):
    pos1 = topline.find("$")+1
    if pos1 != 0:
        pos1 = topline.find("$", pos1)+1
        pos2 = topline.find(" ", pos1)
    else:
        pos1 = topline.find("€")+3
        pos1 = topline.find("€", pos1)+3
        pos2 = topline.find(" ", pos1)
    return float2int(topline[pos1:pos2])

#returns a datetime object with the starttime indicated in the given topline
def parseHandStartTime(topline):
    #convert x:13:35 to 0x:13:35
    counter=0
    while counter < 10:
        pos = topline.find(" %d:" % counter)
        if pos != -1:
            topline = "%s0%s" % (topline[0:pos+1], topline[pos+1:])
            break
        counter += 1

    isUTC=False
    if topline.find("UTC")!=-1:
        pos1 = topline.find("-")+2
        pos2 = topline.find("UTC")
        tmp=topline[pos1:pos2]
        isUTC=True
    else:
        tmp=topline
        #print "parsehandStartTime, tmp:", tmp
        pos = tmp.find("-")+2
        tmp = tmp[pos:]
    #Need to match either
    # 2008/09/07 06:23:14 ET or
    # 2008/08/17 - 01:14:43 (ET) or
    # 2008/11/12 9:33:31 CET [2008/11/12 3:33:31 ET]
    rexx = '(?P<YEAR>[0-9]{4})\/(?P<MON>[0-9]{2})\/(?P<DAY>[0-9]{2})[\- ]+(?P<HR>[0-9]+):(?P<MIN>[0-9]+):(?P<SEC>[0-9]+)'
    m = re.search(rexx,tmp)
    result = datetime.datetime(int(m.group('YEAR')), int(m.group('MON')), int(m.group('DAY')), int(m.group('HR')), int(m.group('MIN')), int(m.group('SEC')))

    if not isUTC: #these use US ET
        result += datetime.timedelta(hours=5)

    return result

#parses the names out of the given lines and returns them as an array
def findName(line):
    pos1 = line.find(":") + 2
    pos2 = line.rfind("(") - 1
    return unicode(line[pos1:pos2], LOCALE_ENCODING)

def parseNames(lines):
    return [findName(line) for line in lines]

def parsePositions(hand, names):
    positions = [-1 for i in names]
    sb, bb = -1, -1

    for line in hand:
        if sb == -1 and "small blind" in line and "dead small blind" not in line:
            sb = line
        if bb == -1 and "big blind" in line and "dead big blind" not in line:
            bb = line

#identify blinds
#print "parsePositions before recognising sb/bb. names:",names
    sbExists = True
    if sb != -1:
        sb = recognisePlayerNo(sb, names, "bet")
    else:
        sbExists = False
    if bb != -1:
        bb = recognisePlayerNo(bb, names, "bet")

#	print "sb = ", sb, "bb = ", bb
    if bb == sb: # if big and small are same, then don't duplicate the small
        sbExists = False
        sb = -1

    #write blinds into array
    if sbExists:
        positions[sb]="S"
    positions[bb]="B"

    #fill up rest of array
    arraypos = sb - 1 if sbExists else bb - 1

    distFromBtn=0
    while arraypos >= 0 and arraypos != bb:
        #print "parsePositions first while, arraypos:",arraypos,"positions:",positions
        positions[arraypos] = distFromBtn
        arraypos -= 1
        distFromBtn += 1

    # eric - this takes into account dead seats between blinds
    if sbExists:
        i = bb - 1
        while positions[i] < 0 and i != sb:
            positions[i] = 9
            i -= 1
    ### RHH - Changed to set the null seats before BB to "9"
    i = sb - 1 if sbExists else bb - 1

    while positions[i] < 0:
        positions[i]=9
        i-=1

    arraypos=len(names)-1
    if (bb!=0 or (bb==0 and sbExists==False) or (bb == 1 and sb != arraypos) ):
        while (arraypos > bb and arraypos > sb):
            positions[arraypos] = distFromBtn
            arraypos -= 1
            distFromBtn += 1

    if any(p == -1 for p in positions):
        print "parsePositions names:",names
        print "result:",positions
        raise FpdbError ("failed to read positions")
#	print str(positions), "\n"
    return positions

#simply parses the rake amount and returns it as an int
def parseRake(line):
    pos = line.find("Rake")+6
    rake = float2int(line[pos:])
    return rake

def parseSiteHandNo(topline):
    """returns the hand no assigned by the poker site"""
    pos1 = topline.find("#")+1
    pos2 = topline.find(":")
    return topline[pos1:pos2]

def parseTableLine(base, line):
    """returns a dictionary with maxSeats and tableName"""
    pos1=line.find('\'')+1
    pos2=line.find('\'', pos1)
    #print "table:",line[pos1:pos2]
    pos3=pos2+2
    pos4=line.find("-max")
    #print "seats:",line[pos3:pos4]
    return {'maxSeats':int(line[pos3:pos4]), 'tableName':line[pos1:pos2]}
#end def parseTableLine

#returns the hand no assigned by the poker site
def parseTourneyNo(topline):
    pos1 = topline.find("Tournament #")+12
    pos2 = topline.find(",", pos1)
    #print "parseTourneyNo pos1:",pos1," pos2:",pos2, " result:",topline[pos1:pos2]
    return topline[pos1:pos2]

#parses a win/collect line. manipulates the passed array winnings, no explicit return
def parseWinLine(line, names, winnings, isTourney):
    #print "parseWinLine: line:",line
    for i,n in enumerate(names):
        n = n.encode(LOCALE_ENCODING)
        if line.startswith(n):
            if isTourney:
                pos1 = line.rfind("collected ") + 10
                pos2 = line.find(" ", pos1)
                winnings[i] += int(line[pos1:pos2])
            else:
                pos1 = line.rfind("$") + 1
                pos2 = line.find(" ", pos1)
                winnings[i] += float2int(line[pos1:pos2])

#returns the category (as per database) string for the given line
def recogniseCategory(line):
    if "Razz" in line:
        return "razz"
    elif "Hold'em" in line:
        return "holdem"
    elif "Omaha" in line:
        if "Hi/Lo" not in line and "H/L" not in line:
            return "omahahi"
        else:
            return "omahahilo"
    elif "Stud" in line:
        if "Hi/Lo" not in line and "H/L" not in line:
            return "studhi"
        else:
            return "studhilo"
    else:
        raise FpdbError("failed to recognise category, line:"+line)

#returns the int for the gametype_id for the given line
def recogniseGametypeID(backend, db, cursor, topline, smallBlindLine, site_id, category, isTourney):#todo: this method is messy
    #if (topline.find("HORSE")!=-1):
    # raise FpdbError("recogniseGametypeID: HORSE is not yet supported.")

    #note: the below variable names small_bet and big_bet are misleading, in NL/PL they mean small/big blind
    if isTourney:
        type = "tour"
        pos1 = topline.find("(")+1
        if(topline[pos1] == "H" or topline[pos1] == "O" or
           topline[pos1] == "R" or topline[pos1]=="S" or
           topline[pos1+2] == "C"):
            pos1 = topline.find("(", pos1)+1
        pos2 = topline.find("/", pos1)
        small_bet = int(topline[pos1:pos2])
    else:
        type = "ring"
        pos1 = topline.find("$")+1
        pos2 = topline.find("/$")
        small_bet = float2int(topline[pos1:pos2])

    pos1 = pos2+2
    if isTourney:
        pos1 -= 1
    pos2 = topline.find(")")

    if pos2 <= pos1:
        pos2 = topline.find(")", pos1)

    if isTourney:
        big_bet = int(topline[pos1:pos2])
    else:
        big_bet = float2int(topline[pos1:pos2])

    if 'No Limit' in topline:
        limit_type = "nl" if 'Cap No' not in topline else "cn"
    elif 'Pot Limit' in topline:
        limit_type = "pl" if 'Cap Pot' not in topline else "cp"
    else:
        limit_type = "fl"

    #print "recogniseGametypeID small_bet/blind:",small_bet,"big bet/blind:", big_bet,"limit type:",limit_type
    if limit_type == "fl":
        cursor.execute(db.sql.query['getGametypeFL'], (site_id, type, category,
                                                       limit_type, small_bet,
                                                       big_bet))
    else:
        cursor.execute(db.sql.query['getGametypeNL'], (site_id, type, category,
                                                       limit_type, small_bet,
                                                       big_bet))
    result = cursor.fetchone()
    #print "recgt1 result=",result
    #ret=result[0]
    #print "recgt1 ret=",ret
    #print "tried SELECTing gametypes.id, result:",result

    try:
        len(result)
    except TypeError:
        if category=="holdem" or category=="omahahi" or category=="omahahilo":
            base="hold"
        else:
            base="stud"

        if category=="holdem" or category=="omahahi" or category=="studhi":
            hiLo='h'
        elif category=="razz":
            hiLo='l'
        else:
            hiLo='s'

        if (limit_type=="fl"):
            big_blind=small_bet
            if base=="hold":
                if smallBlindLine==topline:
                    raise FpdbError("invalid small blind line")
                elif isTourney:
                    pos=smallBlindLine.rfind(" ")+1
                    small_blind=int(smallBlindLine[pos:])
                else:
                    pos=smallBlindLine.rfind("$")+1
                    small_blind=float2int(smallBlindLine[pos:])
            else:
                small_blind=0
            result = db.insertGameTypes( (site_id, type, base, category, limit_type, hiLo
                                         ,small_blind, big_blind, small_bet, big_bet) )
            #cursor.execute ("SELECT id FROM Gametypes WHERE siteId=%s AND type=%s AND category=%s
            #AND limitType=%s AND smallBet=%s AND bigBet=%s", (site_id, type, category, limit_type, small_bet, big_bet))
        else:
            result = db.insertGameTypes( (site_id, type, base, category, limit_type, hiLo
                                         ,small_bet, big_bet, 0, 0) )#remember, for these bet means blind
            #cursor.execute ("SELECT id FROM Gametypes WHERE siteId=%s AND type=%s AND category=%s
            #AND limitType=%s AND smallBlind=%s AND bigBlind=%s", (site_id, type, category, limit_type, small_bet, big_bet))

    return result[0]
#end def recogniseGametypeID

def recogniseTourneyTypeId(db, siteId, tourneySiteId, buyin, fee, knockout, rebuyOrAddon):
    ret = -1
    cursor = db.get_cursor()
    # First we try to find the tourney itself (by its tourneySiteId) in case it has already been inserted before (by a summary file for instance)
    # The reason is that some tourneys may not be identified correctly in the HH toplines (especially Buy-In and Fee which are used to search/create the TourneyTypeId)
    #TODO: When the summary file will be dumped to BD, if the tourney is already in, Buy-In/Fee may need an update (e.g. creation of a new type and link to the Tourney)
    cursor.execute (db.sql.query['getTourneyTypeIdByTourneyNo'].replace('%s', db.sql.query['placeholder']), (tourneySiteId, siteId))
    result = cursor.fetchone()

    try:
        len(result)
        ret = result[0]
    except:
        cursor.execute( """SELECT id FROM TourneyTypes
                           WHERE siteId=%s AND buyin=%s AND fee=%s
                           AND knockout=%s AND rebuyOrAddon=%s""".replace('%s', db.sql.query['placeholder'])
                      , (siteId, buyin, fee, knockout, rebuyOrAddon) )
        result = cursor.fetchone()
        #print "tried selecting tourneytypes.id, result:", result

        try:
            len(result)
            ret = result[0]
        except TypeError:#this means we need to create a new entry
            #print "insert new tourneytype record ..."
            try:
                cursor.execute( """INSERT INTO TourneyTypes (siteId, buyin, fee, knockout, rebuyOrAddon)
                                   VALUES (%s, %s, %s, %s, %s)""".replace('%s', db.sql.query['placeholder'])
                              , (siteId, buyin, fee, knockout, rebuyOrAddon) )
                ret = db.get_last_insert_id(cursor)
            except:
                #print "maybe tourneytype was created since select, try selecting again ..."
                cursor.execute( """SELECT id FROM TourneyTypes
                                   WHERE siteId=%s AND buyin=%s AND fee=%s
                                   AND knockout=%s AND rebuyOrAddon=%s""".replace('%s', db.sql.query['placeholder'])
                              , (siteId, buyin, fee, knockout, rebuyOrAddon) )
                result = cursor.fetchone()
                try:
                    len(result)
                    ret = result[0]
                except:
                    print "Failed to find or insert TourneyTypes record"
                    ret = -1   # failed to find or insert record
                #print "tried selecting tourneytypes.id again, result:", result

    #print "recogniseTourneyTypeId: returning", ret
    return ret
#end def recogniseTourneyTypeId


#recognises the name in the given line and returns its array position in the given array
def recognisePlayerNo(line, names, atype):
    #print "recogniseplayerno, names:",names
    for i in xrange(len(names)):
        encodedName = names[i].encode(LOCALE_ENCODING)
        if (atype=="unbet"):
            if (line.endswith(encodedName)):
                return (i)
        elif (line.startswith("Dealt to ")):
            #print "recognisePlayerNo, card precut, line:",line
            tmp=line[9:]
            #print "recognisePlayerNo, card postcut, tmp:",tmp
            if (tmp.startswith(encodedName)):
                return (i)
        elif (line.startswith("Seat ")):
            if (line.startswith("Seat 10")):
                tmp=line[9:]
            else:
                tmp=line[8:]

            if (tmp.startswith(encodedName)):
                return (i)
        else:
            if (line.startswith(encodedName)):
                return (i)
    #if we're here we mustve failed
    raise FpdbError ("failed to recognise player in: "+line+" atype:"+atype)
#end def recognisePlayerNo


#removes trailing \n from the given array
def removeTrailingEOL(arr):
    for i in xrange(len(arr)):
        if (arr[i].endswith("\n")):
            #print "arr[i] before removetrailingEOL:", arr[i]
            arr[i]=arr[i][:-1]
            #print "arr[i] after removetrailingEOL:", arr[i]
    return arr
#end def removeTrailingEOL

#splits the rake according to the proportion of pot won. manipulates the second passed array.
def splitRake(winnings, rakes, totalRake):
    winnercnt=0
    totalWin=0
    for i in xrange(len(winnings)):
        if winnings[i]!=0:
            winnercnt+=1
            totalWin+=winnings[i]
            firstWinner=i
    if winnercnt==1:
        rakes[firstWinner]=totalRake
    else:
        totalWin=float(totalWin)
        for i in xrange(len(winnings)):
            if winnings[i]!=0:
                winPortion=winnings[i]/totalWin
                rakes[i]=totalRake*winPortion
#end def splitRake

def generateHudCacheData(player_ids, base, category, action_types, allIns, actionTypeByNo
                        ,winnings, totalWinnings, positions, actionTypes, actionAmounts, antes):
    """calculates data for the HUD during import. IMPORTANT: if you change this method make
sure to also change the following storage method and table_viewer.prepare_data if necessary
"""
    #print "generateHudCacheData, len(player_ids)=", len(player_ids)
    #setup subarrays of the result dictionary.
    street0VPI=[]
    street0Aggr=[]
    street0_3BChance=[]
    street0_3BDone=[]
    street1Seen=[]
    street2Seen=[]
    street3Seen=[]
    street4Seen=[]
    sawShowdown=[]
    street1Aggr=[]
    street2Aggr=[]
    street3Aggr=[]
    street4Aggr=[]
    otherRaisedStreet1=[]
    otherRaisedStreet2=[]
    otherRaisedStreet3=[]
    otherRaisedStreet4=[]
    foldToOtherRaisedStreet1=[]
    foldToOtherRaisedStreet2=[]
    foldToOtherRaisedStreet3=[]
    foldToOtherRaisedStreet4=[]
    wonWhenSeenStreet1=[]

    wonAtSD=[]
    stealAttemptChance=[]
    stealAttempted=[]
    hudDataPositions=[]

    street0Calls=[]
    street1Calls=[]
    street2Calls=[]
    street3Calls=[]
    street4Calls=[]
    street0Bets=[]
    street1Bets=[]
    street2Bets=[]
    street3Bets=[]
    street4Bets=[]
    #street0Raises=[]
    #street1Raises=[]
    #street2Raises=[]
    #street3Raises=[]
    #street4Raises=[]

    # Summary figures for hand table:
    result={}
    result['playersVpi']=0
    result['playersAtStreet1']=0
    result['playersAtStreet2']=0
    result['playersAtStreet3']=0
    result['playersAtStreet4']=0
    result['playersAtShowdown']=0
    result['street0Raises']=0
    result['street1Raises']=0
    result['street2Raises']=0
    result['street3Raises']=0
    result['street4Raises']=0
    result['street1Pot']=0
    result['street2Pot']=0
    result['street3Pot']=0
    result['street4Pot']=0
    result['showdownPot']=0

    firstPfRaiseByNo=-1
    firstPfRaiserId=-1
    firstPfRaiserNo=-1
    firstPfCallByNo=-1
    firstPfCallerId=-1

    for i, action in enumerate(actionTypeByNo[0]):
        if action[1] == "bet":
            firstPfRaiseByNo = i
            firstPfRaiserId = action[0]
            for j, pid in enumerate(player_ids):
                if pid == firstPfRaiserId:
                    firstPfRaiserNo = j
                    break
            break
    for i, action in enumerate(actionTypeByNo[0]):
        if action[1] == "call":
            firstPfCallByNo = i
            firstPfCallerId = action[0]
            break
    firstPlayId = firstPfCallerId
    if firstPfRaiseByNo <> -1:
        if firstPfRaiseByNo < firstPfCallByNo or firstPfCallByNo == -1:
            firstPlayId = firstPfRaiserId


    cutoffId=-1
    buttonId=-1
    sbId=-1
    bbId=-1
    if base=="hold":
        for player, pos in enumerate(positions):
            if pos == 1:
                cutoffId = player_ids[player]
            if pos == 0:
                buttonId = player_ids[player]
            if pos == 'S':
                sbId = player_ids[player]
            if pos == 'B':
                bbId = player_ids[player]

    someoneStole=False

    #run a loop for each player preparing the actual values that will be commited to SQL
    for player in xrange(len(player_ids)):
        #set default values
        myStreet0VPI=False
        myStreet0Aggr=False
        myStreet0_3BChance=False
        myStreet0_3BDone=False
        myStreet1Seen=False
        myStreet2Seen=False
        myStreet3Seen=False
        myStreet4Seen=False
        mySawShowdown=False
        myStreet1Aggr=False
        myStreet2Aggr=False
        myStreet3Aggr=False
        myStreet4Aggr=False
        myOtherRaisedStreet1=False
        myOtherRaisedStreet2=False
        myOtherRaisedStreet3=False
        myOtherRaisedStreet4=False
        myFoldToOtherRaisedStreet1=False
        myFoldToOtherRaisedStreet2=False
        myFoldToOtherRaisedStreet3=False
        myFoldToOtherRaisedStreet4=False
        myWonWhenSeenStreet1=0.0
        myWonAtSD=0.0
        myStealAttemptChance=False
        myStealAttempted=False
        myStreet0Calls=0
        myStreet1Calls=0
        myStreet2Calls=0
        myStreet3Calls=0
        myStreet4Calls=0
        myStreet0Bets=0
        myStreet1Bets=0
        myStreet2Bets=0
        myStreet3Bets=0
        myStreet4Bets=0
        #myStreet0Raises=0
        #myStreet1Raises=0
        #myStreet2Raises=0
        #myStreet3Raises=0
        #myStreet4Raises=0

        #calculate VPIP and PFR
        street=0
        heroPfRaiseCount=0
        for currentAction in action_types[street][player]: # finally individual actions
            if currentAction == "bet":
                myStreet0Aggr = True
            if currentAction == "bet" or currentAction == "call":
                myStreet0VPI = True

        if myStreet0VPI:
            result['playersVpi'] += 1
        myStreet0Calls = action_types[street][player].count('call')
        myStreet0Bets = action_types[street][player].count('bet')
        # street0Raises = action_types[street][player].count('raise')  bet count includes raises for now
        result['street0Raises'] += myStreet0Bets

        #PF3BChance and PF3B
        pfFold=-1
        pfRaise=-1
        if firstPfRaiseByNo != -1:
            for i, actionType in enumerate(actionTypeByNo[0]):
                if actionType[0] == player_ids[player]:
                    if actionType[1] == "bet" and pfRaise == -1 and i > firstPfRaiseByNo:
                        pfRaise = i
                    if actionType[1] == "fold" and pfFold == -1:
                        pfFold = i
            if pfFold == -1 or pfFold > firstPfRaiseByNo:
                myStreet0_3BChance = True
                if pfRaise > firstPfRaiseByNo:
                    myStreet0_3BDone = True

        #steal calculations
        if base=="hold":
            if len(player_ids)>=3: # no point otherwise  # was 5, use 3 to match pokertracker definition
                if positions[player]==1:
                    if      firstPfRaiserId==player_ids[player] \
                       and (firstPfCallByNo==-1 or firstPfCallByNo>firstPfRaiseByNo):
                        myStealAttempted=True
                        myStealAttemptChance=True
                    if firstPlayId==cutoffId or firstPlayId==buttonId or firstPlayId==sbId or firstPlayId==bbId or firstPlayId==-1:
                        myStealAttemptChance=True
                if positions[player]==0:
                    if      firstPfRaiserId==player_ids[player] \
                       and (firstPfCallByNo==-1 or firstPfCallByNo>firstPfRaiseByNo):
                        myStealAttempted=True
                        myStealAttemptChance=True
                    if firstPlayId==buttonId or firstPlayId==sbId or firstPlayId==bbId or firstPlayId==-1:
                        myStealAttemptChance=True
                if positions[player]=='S':
                    if      firstPfRaiserId==player_ids[player] \
                       and (firstPfCallByNo==-1 or firstPfCallByNo>firstPfRaiseByNo):
                        myStealAttempted=True
                        myStealAttemptChance=True
                    if firstPlayId==sbId or firstPlayId==bbId or firstPlayId==-1:
                        myStealAttemptChance=True
                if positions[player]=='B':
                    pass

                if myStealAttempted:
                    someoneStole=True


        #calculate saw* values
        isAllIn = any(i for i in allIns[0][player])
        if isAllIn or len(action_types[1][player]) > 0:
            myStreet1Seen = True

            if not isAllIn:
                isAllIn = any(i for i in allIns[1][player])
            if isAllIn or len(action_types[2][player]) > 0:
                if all(actiontype != "fold" for actiontype in action_types[1][player]):
                    myStreet2Seen = True

                if not isAllIn:
                    isAllAin = any(i for i in allIns[2][player])
                if isAllIn or len(action_types[3][player]) > 0:
                    if all(actiontype != "fold" for actiontype in action_types[2][player]):
                        myStreet3Seen = True

                    #print "base:", base
                    if base == "hold":
                        mySawShowdown = not any(actiontype == "fold" for actiontype in action_types[3][player])
                    else:
                        #print "in else"
                        if not isAllIn:
                            isAllIn = any(i for i in allIns[3][player])
                        if isAllIn or len(action_types[4][player]) > 0:
                            #print "in if"
                            myStreet4Seen = True

                            mySawShowdown = not any(actiontype == "fold" for actiontype in action_types[4][player])

        if myStreet1Seen:
            result['playersAtStreet1'] += 1
        if myStreet2Seen:
            result['playersAtStreet2'] += 1
        if myStreet3Seen:
            result['playersAtStreet3'] += 1
        if myStreet4Seen:
            result['playersAtStreet4'] += 1
        if mySawShowdown:
            result['playersAtShowdown'] += 1

        #flop stuff
        street = 1
        if myStreet1Seen:
            myStreet1Aggr = any(actiontype == "bet" for actiontype in action_types[street][player])
            myStreet1Calls = action_types[street][player].count('call')
            myStreet1Bets = action_types[street][player].count('bet')
            # street1Raises = action_types[street][player].count('raise')  bet count includes raises for now
            result['street1Raises'] += myStreet1Bets

            for otherPlayer in xrange(len(player_ids)):
                if player == otherPlayer:
                    pass
                else:
                    for countOther in xrange(len(action_types[street][otherPlayer])):
                        if action_types[street][otherPlayer][countOther] == "bet":
                            myOtherRaisedStreet1 = True
                            for countOtherFold in xrange(len(action_types[street][player])):
                                if action_types[street][player][countOtherFold] == "fold":
                                    myFoldToOtherRaisedStreet1 = True

        #turn stuff - copy of flop with different vars
        street = 2
        if myStreet2Seen:
            myStreet2Aggr = any(actiontype == "bet" for actiontype in action_types[street][player])
            myStreet2Calls = action_types[street][player].count('call')
            myStreet2Bets = action_types[street][player].count('bet')
            # street2Raises = action_types[street][player].count('raise')  bet count includes raises for now
            result['street2Raises'] += myStreet2Bets

            for otherPlayer in xrange(len(player_ids)):
                if player == otherPlayer:
                    pass
                else:
                    for countOther in xrange(len(action_types[street][otherPlayer])):
                        if action_types[street][otherPlayer][countOther] == "bet":
                            myOtherRaisedStreet2 = True
                            for countOtherFold in xrange(len(action_types[street][player])):
                                if action_types[street][player][countOtherFold] == "fold":
                                    myFoldToOtherRaisedStreet2 = True

        #river stuff - copy of flop with different vars
        street = 3
        if myStreet3Seen:
            myStreet3Aggr = any(actiontype == "bet" for actiontype in action_types[street][player])
            myStreet3Calls = action_types[street][player].count('call')
            myStreet3Bets = action_types[street][player].count('bet')
            # street3Raises = action_types[street][player].count('raise')  bet count includes raises for now
            result['street3Raises'] += myStreet3Bets

            for otherPlayer in xrange(len(player_ids)):
                if player == otherPlayer:
                    pass
                else:
                    for countOther in xrange(len(action_types[street][otherPlayer])):
                        if action_types[street][otherPlayer][countOther] == "bet":
                            myOtherRaisedStreet3 = True
                            for countOtherFold in xrange(len(action_types[street][player])):
                                if action_types[street][player][countOtherFold] == "fold":
                                    myFoldToOtherRaisedStreet3 = True

        #stud river stuff - copy of flop with different vars
        street = 4
        if myStreet4Seen:
            myStreet4Aggr = any(actiontype == "bet" for actiontype in action_types[street][player])
            myStreet4Calls = action_types[street][player].count('call')
            myStreet4Bets = action_types[street][player].count('bet')
            # street4Raises = action_types[street][player].count('raise')  bet count includes raises for now
            result['street4Raises'] += myStreet4Bets

            for otherPlayer in xrange(len(player_ids)):
                if player == otherPlayer:
                    pass
                else:
                    for countOther in xrange(len(action_types[street][otherPlayer])):
                        if action_types[street][otherPlayer][countOther] == "bet":
                            myOtherRaisedStreet4 = True
                            for countOtherFold in xrange(len(action_types[street][player])):
                                if action_types[street][player][countOtherFold] == "fold":
                                    myFoldToOtherRaisedStreet4 = True

        if winnings[player] != 0:
            if myStreet1Seen:
                myWonWhenSeenStreet1 = winnings[player] / float(totalWinnings)
                if mySawShowdown:
                    myWonAtSD = myWonWhenSeenStreet1

        #add each value to the appropriate array
        street0VPI.append(myStreet0VPI)
        street0Aggr.append(myStreet0Aggr)
        street0_3BChance.append(myStreet0_3BChance)
        street0_3BDone.append(myStreet0_3BDone)
        street1Seen.append(myStreet1Seen)
        street2Seen.append(myStreet2Seen)
        street3Seen.append(myStreet3Seen)
        street4Seen.append(myStreet4Seen)
        sawShowdown.append(mySawShowdown)
        street1Aggr.append(myStreet1Aggr)
        street2Aggr.append(myStreet2Aggr)
        street3Aggr.append(myStreet3Aggr)
        street4Aggr.append(myStreet4Aggr)
        otherRaisedStreet1.append(myOtherRaisedStreet1)
        otherRaisedStreet2.append(myOtherRaisedStreet2)
        otherRaisedStreet3.append(myOtherRaisedStreet3)
        otherRaisedStreet4.append(myOtherRaisedStreet4)
        foldToOtherRaisedStreet1.append(myFoldToOtherRaisedStreet1)
        foldToOtherRaisedStreet2.append(myFoldToOtherRaisedStreet2)
        foldToOtherRaisedStreet3.append(myFoldToOtherRaisedStreet3)
        foldToOtherRaisedStreet4.append(myFoldToOtherRaisedStreet4)
        wonWhenSeenStreet1.append(myWonWhenSeenStreet1)
        wonAtSD.append(myWonAtSD)
        stealAttemptChance.append(myStealAttemptChance)
        stealAttempted.append(myStealAttempted)
        if base=="hold":
            pos=positions[player]
            if pos=='B':
                hudDataPositions.append('B')
            elif pos=='S':
                hudDataPositions.append('S')
            elif pos==0:
                hudDataPositions.append('D')
            elif pos==1:
                hudDataPositions.append('C')
            elif pos>=2 and pos<=4:
                hudDataPositions.append('M')
            elif pos>=5 and pos<=8:
                hudDataPositions.append('E')
            ### RHH Added this elif to handle being a dead hand before the BB (pos==9)
            elif pos==9:
                hudDataPositions.append('X')
            else:
                raise FpdbError("invalid position")
        elif base=="stud":
            #todo: stud positions and steals
            pass

        street0Calls.append(myStreet0Calls)
        street1Calls.append(myStreet1Calls)
        street2Calls.append(myStreet2Calls)
        street3Calls.append(myStreet3Calls)
        street4Calls.append(myStreet4Calls)
        street0Bets.append(myStreet0Bets)
        street1Bets.append(myStreet1Bets)
        street2Bets.append(myStreet2Bets)
        street3Bets.append(myStreet3Bets)
        street4Bets.append(myStreet4Bets)
        #street0Raises.append(myStreet0Raises)
        #street1Raises.append(myStreet1Raises)
        #street2Raises.append(myStreet2Raises)
        #street3Raises.append(myStreet3Raises)
        #street4Raises.append(myStreet4Raises)

    #add each array to the to-be-returned dictionary
    result['street0VPI']=street0VPI
    result['street0Aggr']=street0Aggr
    result['street0_3BChance']=street0_3BChance
    result['street0_3BDone']=street0_3BDone
    result['street1Seen']=street1Seen
    result['street2Seen']=street2Seen
    result['street3Seen']=street3Seen
    result['street4Seen']=street4Seen
    result['sawShowdown']=sawShowdown

    result['street1Aggr']=street1Aggr
    result['otherRaisedStreet1']=otherRaisedStreet1
    result['foldToOtherRaisedStreet1']=foldToOtherRaisedStreet1
    result['street2Aggr']=street2Aggr
    result['otherRaisedStreet2']=otherRaisedStreet2
    result['foldToOtherRaisedStreet2']=foldToOtherRaisedStreet2
    result['street3Aggr']=street3Aggr
    result['otherRaisedStreet3']=otherRaisedStreet3
    result['foldToOtherRaisedStreet3']=foldToOtherRaisedStreet3
    result['street4Aggr']=street4Aggr
    result['otherRaisedStreet4']=otherRaisedStreet4
    result['foldToOtherRaisedStreet4']=foldToOtherRaisedStreet4
    result['wonWhenSeenStreet1']=wonWhenSeenStreet1
    result['wonAtSD']=wonAtSD
    result['stealAttemptChance']=stealAttemptChance
    result['stealAttempted']=stealAttempted
    result['street0Calls']=street0Calls
    result['street1Calls']=street1Calls
    result['street2Calls']=street2Calls
    result['street3Calls']=street3Calls
    result['street4Calls']=street4Calls
    result['street0Bets']=street0Bets
    result['street1Bets']=street1Bets
    result['street2Bets']=street2Bets
    result['street3Bets']=street3Bets
    result['street4Bets']=street4Bets
    #result['street0Raises']=street0Raises
    #result['street1Raises']=street1Raises
    #result['street2Raises']=street2Raises
    #result['street3Raises']=street3Raises
    #result['street4Raises']=street4Raises

    #now the various steal values
    foldBbToStealChance=[]
    foldedBbToSteal=[]
    foldSbToStealChance=[]
    foldedSbToSteal=[]
    for player in xrange(len(player_ids)):
        myFoldBbToStealChance=False
        myFoldedBbToSteal=False
        myFoldSbToStealChance=False
        myFoldedSbToSteal=False

        if base=="hold":
            if someoneStole and (positions[player]=='B' or positions[player]=='S') and firstPfRaiserId!=player_ids[player]:
                street=0
                for count in xrange(len(action_types[street][player])):#individual actions
                    if positions[player]=='B':
                        myFoldBbToStealChance=True
                        if action_types[street][player][count]=="fold":
                            myFoldedBbToSteal=True
                    if positions[player]=='S':
                        myFoldSbToStealChance=True
                        if action_types[street][player][count]=="fold":
                            myFoldedSbToSteal=True


        foldBbToStealChance.append(myFoldBbToStealChance)
        foldedBbToSteal.append(myFoldedBbToSteal)
        foldSbToStealChance.append(myFoldSbToStealChance)
        foldedSbToSteal.append(myFoldedSbToSteal)
    result['foldBbToStealChance']=foldBbToStealChance
    result['foldedBbToSteal']=foldedBbToSteal
    result['foldSbToStealChance']=foldSbToStealChance
    result['foldedSbToSteal']=foldedSbToSteal

    #now CB
    street1CBChance=[]
    street1CBDone=[]
    didStreet1CB=[]
    for player in xrange(len(player_ids)):
        myStreet1CBChance=False
        myStreet1CBDone=False

        if street0VPI[player]:
            myStreet1CBChance=True
            if street1Aggr[player]:
                myStreet1CBDone=True
                didStreet1CB.append(player_ids[player])

        street1CBChance.append(myStreet1CBChance)
        street1CBDone.append(myStreet1CBDone)
    result['street1CBChance']=street1CBChance
    result['street1CBDone']=street1CBDone

    #now 2B
    street2CBChance=[]
    street2CBDone=[]
    didStreet2CB=[]
    for player in xrange(len(player_ids)):
        myStreet2CBChance=False
        myStreet2CBDone=False

        if street1CBDone[player]:
            myStreet2CBChance=True
            if street2Aggr[player]:
                myStreet2CBDone=True
                didStreet2CB.append(player_ids[player])

        street2CBChance.append(myStreet2CBChance)
        street2CBDone.append(myStreet2CBDone)
    result['street2CBChance']=street2CBChance
    result['street2CBDone']=street2CBDone

    #now 3B
    street3CBChance=[]
    street3CBDone=[]
    didStreet3CB=[]
    for player in xrange(len(player_ids)):
        myStreet3CBChance=False
        myStreet3CBDone=False

        if street2CBDone[player]:
            myStreet3CBChance=True
            if street3Aggr[player]:
                myStreet3CBDone=True
                didStreet3CB.append(player_ids[player])

        street3CBChance.append(myStreet3CBChance)
        street3CBDone.append(myStreet3CBDone)
    result['street3CBChance']=street3CBChance
    result['street3CBDone']=street3CBDone

    #and 4B
    street4CBChance=[]
    street4CBDone=[]
    didStreet4CB=[]
    for player in xrange(len(player_ids)):
        myStreet4CBChance=False
        myStreet4CBDone=False

        if street3CBDone[player]:
            myStreet4CBChance=True
            if street4Aggr[player]:
                myStreet4CBDone=True
                didStreet4CB.append(player_ids[player])

        street4CBChance.append(myStreet4CBChance)
        street4CBDone.append(myStreet4CBDone)
    result['street4CBChance']=street4CBChance
    result['street4CBDone']=street4CBDone


    result['position']=hudDataPositions

    foldToStreet1CBChance=[]
    foldToStreet1CBDone=[]
    foldToStreet2CBChance=[]
    foldToStreet2CBDone=[]
    foldToStreet3CBChance=[]
    foldToStreet3CBDone=[]
    foldToStreet4CBChance=[]
    foldToStreet4CBDone=[]

    for player in xrange(len(player_ids)):
        myFoldToStreet1CBChance=False
        myFoldToStreet1CBDone=False
        foldToStreet1CBChance.append(myFoldToStreet1CBChance)
        foldToStreet1CBDone.append(myFoldToStreet1CBDone)

        myFoldToStreet2CBChance=False
        myFoldToStreet2CBDone=False
        foldToStreet2CBChance.append(myFoldToStreet2CBChance)
        foldToStreet2CBDone.append(myFoldToStreet2CBDone)

        myFoldToStreet3CBChance=False
        myFoldToStreet3CBDone=False
        foldToStreet3CBChance.append(myFoldToStreet3CBChance)
        foldToStreet3CBDone.append(myFoldToStreet3CBDone)

        myFoldToStreet4CBChance=False
        myFoldToStreet4CBDone=False
        foldToStreet4CBChance.append(myFoldToStreet4CBChance)
        foldToStreet4CBDone.append(myFoldToStreet4CBDone)

    if len(didStreet1CB)>=1:
        generateFoldToCB(1, player_ids, didStreet1CB, street1CBDone, foldToStreet1CBChance, foldToStreet1CBDone, actionTypeByNo)

        if len(didStreet2CB)>=1:
            generateFoldToCB(2, player_ids, didStreet2CB, street2CBDone, foldToStreet2CBChance, foldToStreet2CBDone, actionTypeByNo)

            if len(didStreet3CB)>=1:
                generateFoldToCB(3, player_ids, didStreet3CB, street3CBDone, foldToStreet3CBChance, foldToStreet3CBDone, actionTypeByNo)

                if len(didStreet4CB)>=1:
                    generateFoldToCB(4, player_ids, didStreet4CB, street4CBDone, foldToStreet4CBChance, foldToStreet4CBDone, actionTypeByNo)

    result['foldToStreet1CBChance']=foldToStreet1CBChance
    result['foldToStreet1CBDone']=foldToStreet1CBDone
    result['foldToStreet2CBChance']=foldToStreet2CBChance
    result['foldToStreet2CBDone']=foldToStreet2CBDone
    result['foldToStreet3CBChance']=foldToStreet3CBChance
    result['foldToStreet3CBDone']=foldToStreet3CBDone
    result['foldToStreet4CBChance']=foldToStreet4CBChance
    result['foldToStreet4CBDone']=foldToStreet4CBDone


    totalProfit=[]

    street1CheckCallRaiseChance=[]
    street1CheckCallRaiseDone=[]
    street2CheckCallRaiseChance=[]
    street2CheckCallRaiseDone=[]
    street3CheckCallRaiseChance=[]
    street3CheckCallRaiseDone=[]
    street4CheckCallRaiseChance=[]
    street4CheckCallRaiseDone=[]
    #print "b4 totprof calc, len(playerIds)=", len(player_ids)
    for pl in xrange(len(player_ids)):
        #print "pl=", pl
        myTotalProfit=winnings[pl]  # still need to deduct other costs
        if antes:
            myTotalProfit=winnings[pl] - antes[pl]
        for i in xrange(len(actionTypes)): #iterate through streets
            #for j in xrange(len(actionTypes[i])): #iterate through names (using pl loop above)
                for k in xrange(len(actionTypes[i][pl])): #iterate through individual actions of that player on that street
                    myTotalProfit -= actionAmounts[i][pl][k]

        myStreet1CheckCallRaiseChance=False
        myStreet1CheckCallRaiseDone=False
        myStreet2CheckCallRaiseChance=False
        myStreet2CheckCallRaiseDone=False
        myStreet3CheckCallRaiseChance=False
        myStreet3CheckCallRaiseDone=False
        myStreet4CheckCallRaiseChance=False
        myStreet4CheckCallRaiseDone=False

        #print "myTotalProfit=", myTotalProfit
        totalProfit.append(myTotalProfit)
        #print "totalProfit[]=", totalProfit

        street1CheckCallRaiseChance.append(myStreet1CheckCallRaiseChance)
        street1CheckCallRaiseDone.append(myStreet1CheckCallRaiseDone)
        street2CheckCallRaiseChance.append(myStreet2CheckCallRaiseChance)
        street2CheckCallRaiseDone.append(myStreet2CheckCallRaiseDone)
        street3CheckCallRaiseChance.append(myStreet3CheckCallRaiseChance)
        street3CheckCallRaiseDone.append(myStreet3CheckCallRaiseDone)
        street4CheckCallRaiseChance.append(myStreet4CheckCallRaiseChance)
        street4CheckCallRaiseDone.append(myStreet4CheckCallRaiseDone)

    result['totalProfit']=totalProfit
    #print "res[totalProfit]=", result['totalProfit']

    result['street1CheckCallRaiseChance']=street1CheckCallRaiseChance
    result['street1CheckCallRaiseDone']=street1CheckCallRaiseDone
    result['street2CheckCallRaiseChance']=street2CheckCallRaiseChance
    result['street2CheckCallRaiseDone']=street2CheckCallRaiseDone
    result['street3CheckCallRaiseChance']=street3CheckCallRaiseChance
    result['street3CheckCallRaiseDone']=street3CheckCallRaiseDone
    result['street4CheckCallRaiseChance']=street4CheckCallRaiseChance
    result['street4CheckCallRaiseDone']=street4CheckCallRaiseDone
    return result
#end def generateHudCacheData

def generateFoldToCB(street, playerIDs, didStreetCB, streetCBDone, foldToStreetCBChance, foldToStreetCBDone, actionTypeByNo):
    """fills the passed foldToStreetCB* arrays appropriately depending on the given street"""
    #print "beginning of generateFoldToCB, street:", street, "len(actionTypeByNo):", len(actionTypeByNo)
    #print "len(actionTypeByNo[street]):",len(actionTypeByNo[street])
    firstCBReaction=0
    for action in xrange(len(actionTypeByNo[street])):
        if actionTypeByNo[street][action][1]=="bet":
            for player in didStreetCB:
                if player==actionTypeByNo[street][action][0] and firstCBReaction==0:
                    firstCBReaction=action+1
                    break

    for action in actionTypeByNo[street][firstCBReaction:]:
        for player in xrange(len(playerIDs)):
            if playerIDs[player]==action[0]:
                foldToStreetCBChance[player]=True
                if action[1]=="fold":
                    foldToStreetCBDone[player]=True
#end def generateFoldToCB
