#!/usr/bin/python

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

import datetime

PS=1
FTP=2

class DuplicateError(Exception):
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr(self.value)

class FpdbError(Exception):
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr(self.value)

#returns an array of the total money paid. intending to add rebuys/addons here
def calcPayin(count, buyin, fee):
	result=[]
	for i in range(count):
		result.append (buyin+fee)
	return result
#end def calcPayin

def checkPositions(positions):
	"""verifies that these positions are valid"""
	for i in range (len(positions)):
		pos=positions[i]
		try:#todo: use type recognition instead of error
			if (len(pos)!=1):
				raise FpdbError("invalid position found in checkPositions. i: "+str(i)+"   position: "+pos) #dont need to str() here
		except TypeError:#->not string->is int->fine
			pass
		
		if (pos!="B" and pos!="S" and pos!=0 and pos!=1 and pos!=2 and pos!=3 and pos!=4 and pos!=5 and pos!=6 and pos!=7):
			raise FpdbError("invalid position found in checkPositions. i: "+str(i)+"   position: "+str(pos))
#end def fpdb_simple.checkPositions

#classifies each line for further processing in later code. Manipulates the passed arrays.
def classifyLines(hand, category, lineTypes, lineStreets):
	currentStreet="predeal"
	done=False #set this to true once we reach the last relevant line (the summary, except rake, is all repeats)
	for i in range (len(hand)):
		if (done):
			if (hand[i].find("[")==-1 or hand[i].find("mucked [")==-1):
				lineTypes.append("ignore")
			else: #it's storing a mucked card
				lineTypes.append("cards")
		elif (hand[i].startswith("Dealt to")):
			lineTypes.append("cards")
		elif (i==0):
			lineTypes.append("header")
		elif (hand[i].startswith("Seat ") and ((hand[i].find("in chips")!=-1) or (hand[i].find("($")!=-1))):
			lineTypes.append("name")
		elif (isActionLine(hand[i])):
			lineTypes.append("action")
			if (hand[i].find(" posts ")!=-1 or hand[i].find(" posts the ")!=-1):#need to set this here so the "action" of posting blinds is registered properly
				currentStreet="preflop"
		elif (isWinLine(hand[i])):
			lineTypes.append("win")
		elif (hand[i].startswith("Total pot ") and hand[i].find("Rake")!=-1):
			lineTypes.append("rake")
			done=True
		elif (hand[i]=="*** SHOW DOWN ***" or hand[i]=="*** SUMMARY ***"):
			lineTypes.append("ignore")
			#print "in classifyLine, showdown or summary"
		elif (hand[i].find(" antes ")!=-1 or hand[i].find(" posts the ante ")!=-1):
			lineTypes.append("ante")
		elif (hand[i].startswith("*** FLOP *** [")):
			lineTypes.append("cards")
			currentStreet="flop"
		elif (hand[i].startswith("*** TURN *** [")):
			lineTypes.append("cards")
			currentStreet="turn"
		elif (hand[i].startswith("*** RIVER *** [")):
			lineTypes.append("cards")
			currentStreet="river"
		elif (hand[i].startswith("*** 3")):
			lineTypes.append("ignore")
			currentStreet=0
		elif (hand[i].startswith("*** 4")):
			lineTypes.append("ignore")
			currentStreet=1
		elif (hand[i].startswith("*** 5")):
			lineTypes.append("ignore")
			currentStreet=2
		elif (hand[i].startswith("*** 6")):
			lineTypes.append("ignore")
			currentStreet=3
		elif (hand[i].startswith("*** 7") or hand[i]=="*** RIVER ***"):
			lineTypes.append("ignore")
			currentStreet=4
		elif (hand[i].find(" shows [")!=-1):
			lineTypes.append("cards")
		elif (hand[i].startswith("Table '")):
			lineTypes.append("table")
		else:
			raise FpdbError("unrecognised linetype in:"+hand[i])
		lineStreets.append(currentStreet)
#end def classifyLines

def convert3B4B(site, category, limit_type, actionTypes, actionAmounts):
	"""calculates the actual bet amounts in the given amount array and changes it accordingly."""
	for i in range (len(actionTypes)):
		for j in range (len(actionTypes[i])):
			bets=[]
			for k in range (len(actionTypes[i][j])):
				if (actionTypes[i][j][k]=="bet"):
					bets.append((i,j,k))
					if (len(bets)==2):
						#print "len(bets) 2 or higher, need to correct it. bets:",bets,"len:",len(bets)
						amount2=actionAmounts[bets[1][0]][bets[1][1]][bets[1][2]]
						amount1=actionAmounts[bets[0][0]][bets[0][1]][bets[0][2]]
						actionAmounts[bets[1][0]][bets[1][1]][bets[1][2]]=amount2-amount1
					elif (len(bets)>2):
						fail=True
						#todo: run correction for below
						if (site=="ps" and category=="holdem" and limit_type=="nl" and len(bets)==3):
							fail=False
						if (site=="ftp" and category=="omahahi" and limit_type=="pl" and len(bets)==3):
							fail=False
						
						if fail:
							print "len(bets)>2 in convert3B4B, i didnt think this is possible. i:",i,"j:",j,"k:",k
							print "actionTypes:",actionTypes
							raise FpdbError ("too many bets in convert3B4B")
	#print "actionAmounts postConvert",actionAmounts
#end def convert3B4B(actionTypes, actionAmounts)

#Corrects the bet amount if the player had to pay blinds
def convertBlindBet(actionTypes, actionAmounts):
	i=0#setting street to pre-flop
	for j in range (len(actionTypes[i])):#playerloop
		blinds=[]
		bets=[]
		for k in range (len(actionTypes[i][j])):
			if (actionTypes[i][j][k]=="blind"):
				blinds.append((i,j,k))
			
			if (len(blinds)>0 and actionTypes[i][j][k]=="bet"):
				bets.append((i,j,k))
				if (len(bets)==1):
					blind_amount=actionAmounts[blinds[0][0]][blinds[0][1]][blinds[0][2]]
					bet_amount=actionAmounts[bets[0][0]][bets[0][1]][bets[0][2]]
					actionAmounts[bets[0][0]][bets[0][1]][bets[0][2]]=bet_amount-blind_amount
#end def convertBlindBet

#converts the strings in the given array to ints (changes the passed array, no returning). see table design for conversion details
#todo: make this use convertCardValuesBoard
def convertCardValues(arr):
	for i in range (len(arr)):
		for j in range (len(arr[i])):
			if (arr[i][j]=="A"):
				arr[i][j]=14
			elif (arr[i][j]=="K"):
				arr[i][j]=13
			elif (arr[i][j]=="Q"):
				arr[i][j]=12
			elif (arr[i][j]=="J"):
				arr[i][j]=11
			elif (arr[i][j]=="T"):
				arr[i][j]=10
			else:
				arr[i][j]=int(arr[i][j])
#end def convertCardValues

#converts the strings in the given array to ints (changes the passed array, no returning). see table design for conversion details
def convertCardValuesBoard(arr):
	for i in range (len(arr)):
		if (arr[i]=="A"):
			arr[i]=14
		elif (arr[i]=="K"):
			arr[i]=13
		elif (arr[i]=="Q"):
			arr[i]=12
		elif (arr[i]=="J"):
			arr[i]=11
		elif (arr[i]=="T"):
			arr[i]=10
		else:
			arr[i]=int(arr[i])
#end def convertCardValuesBoard

#this creates the 2D/3D arrays. manipulates the passed arrays instead of returning.
def createArrays(category, seats, card_values, card_suits, antes, winnings, rakes, action_types, action_amounts, actionNos, actionTypeByNo):
	for i in range(seats):#create second dimension arrays
		tmp=[]
		card_values.append(tmp)
		tmp=[]
		card_suits.append(tmp)
		antes.append(0)
		winnings.append(0)
		rakes.append(0)
	
	if (category=="holdem" or category=="omahahi" or category=="omahahilo"):
		streetCount=4
	else:
		streetCount=5
	
	for i in range(streetCount): #build the first dimension array, for streets 
		tmp=[]
		action_types.append(tmp)
		tmp=[]
		action_amounts.append(tmp)
		tmp=[]
		actionNos.append(tmp)
		tmp=[]
		actionTypeByNo.append(tmp)
		for j in range (seats): #second dimension arrays: players
			tmp=[]
			action_types[i].append(tmp)
			tmp=[]
			action_amounts[i].append(tmp)
			tmp=[]
			actionNos[i].append(tmp)
	if (category=="holdem" or category=="omahahi" or category=="omahahilo"):
		pass
	elif (category=="razz" or category=="studhi" or category=="studhilo"):#need to fill card arrays.
		for i in range(seats):
			for j in range (7):
				card_values[i].append(0)
				card_suits[i].append("x")
	else:
		raise FpdbError("invalid category")
#end def createArrays

def fill_board_cards(board_values, board_suits):
#fill up the two board card arrays
	while (len(board_values)<5):
		board_values.append(0)
		board_suits.append("x")
#end def fill_board_cards

def fillCardArrays(player_count, base, category, card_values, card_suits):
	"""fills up the two card arrays"""
	if (category=="holdem"):
		cardCount=2
	elif (category=="omahahi" or category=="omahahilo"):
		cardCount=4
	elif base=="stud":
		cardCount=7
	else:
		raise fpdb_simple.FpdbError ("invalid category:", category)
	
	for i in range (player_count):
		while (len(card_values[i])<cardCount):
			card_values[i].append(0)
			card_suits[i].append("x")
#end def fillCardArrays

#filters out a player that folded before paying ante or blinds. This should be called
#before calling the actual hand parser. manipulates hand, no return.
def filterAnteBlindFold(site,hand):
	#todo: this'll only get rid of one ante folder, not multiple ones
	#todo: in tourneys this should not be removed but 
	#print "start of filterAnteBlindFold"
	pre3rd=[]
	for i in range (len(hand)):
		if (hand[i].startswith("*** 3") or hand[i].startswith("*** HOLE")):
			pre3rd=hand[0:i]
	
	foldeeName=None
	for i in range (len(pre3rd)):
		if (pre3rd[i].endswith("folds") or pre3rd[i].endswith("is sitting out") or pre3rd[i].endswith(" stands up")): #found ante fold or timeout
			pos=pre3rd[i].find (" folds")
			foldeeName=pre3rd[i][0:pos]
			if pos==-1 and pre3rd[i].find(" in chips)")==-1:
				pos=pre3rd[i].find (" is sitting out")
				foldeeName=pre3rd[i][0:pos]
			if pos==-1:
				pos=pre3rd[i].find (" stands up")
				foldeeName=pre3rd[i][0:pos]
			if pos==-1:#this one is for PS tourney
				pos1=pre3rd[i].find (": ")+2
				pos2=pre3rd[i].find (" (")
				foldeeName=pre3rd[i][pos1:pos2]

	if foldeeName!=None:
		#print "filterAnteBlindFold, foldeeName:",foldeeName
		toRemove=[]
		for i in range (len(hand)): #using hand again to filter from all streets, just in case.
			#todo: this will break it if sittin out BB wins a hand
			if (hand[i].find(foldeeName)!=-1):
				toRemove.append(hand[i])
			
		for i in range (len(toRemove)):
			hand.remove(toRemove[i])
#end def filterAnteFold

#removes useless lines as well as trailing spaces
def filterCrap(site, hand, isTourney):
	#remove one trailing space at end of line
	for i in range (len(hand)):
		if (hand[i][-1]==' '):
			hand[i]=hand[i][:-1]
			
	#print "hand after trailing space removal in filterCrap:",hand
	#general variable position word filter/string filter
	toRemove=[]
	for i in range (len(hand)):
		if (hand[i].startswith("Board [")):
			toRemove.append(hand[i])
		elif (hand[i].find(" out of hand ")!=-1):
			hand[i]=hand[i][:-56]
		elif (hand[i]=="*** HOLE CARDS ***"):
			toRemove.append(hand[i])
		elif (hand[i].endswith("has been disconnected")):
			toRemove.append(hand[i])
		elif (hand[i].endswith("has requested TIME")):
			toRemove.append(hand[i])
		elif (hand[i].endswith("has returned")):
			toRemove.append(hand[i])
		elif (hand[i].endswith("will be allowed to play after the button")):
			toRemove.append(hand[i])
		elif (hand[i].endswith("has timed out")):
			toRemove.append(hand[i])
		elif (hand[i].endswith("has timed out while disconnected")):
			toRemove.append(hand[i])
		elif (hand[i].endswith("has timed out while being disconnected")):
			toRemove.append(hand[i])
		elif (hand[i].endswith("is connected")):
			toRemove.append(hand[i])
		elif (hand[i].endswith("is disconnected")):
			toRemove.append(hand[i])
		elif (hand[i].endswith(" is feeling angry")):
			toRemove.append(hand[i])
		elif (hand[i].endswith(" is feeling confused")):
			toRemove.append(hand[i])
		elif (hand[i].endswith(" is feeling happy")):
			toRemove.append(hand[i])
		elif (hand[i].endswith(" is feeling normal")):
			toRemove.append(hand[i])
		elif (hand[i].find(" is low with [")!=-1):
			toRemove.append(hand[i])
		#elif (hand[i].find("-max Seat #")!=-1 and hand[i].find(" is the button")!=-1):
		#	toRemove.append(hand[i])
		elif (hand[i].endswith(" mucks")):
			toRemove.append(hand[i])
		elif (hand[i].endswith(": mucks hand")):
			toRemove.append(hand[i])
		elif (hand[i]=="No low hand qualified"):
			toRemove.append(hand[i])
		elif (hand[i]=="Pair on board - a double bet is allowed"):
			toRemove.append(hand[i])
		elif (hand[i].find(" shows ")!=-1 and hand[i].find("[")==-1):
			toRemove.append(hand[i])
		#elif (hand[i].startswith("Table '") and hand[i].endswith("-max")):
		#	toRemove.append(hand[i])
		elif (hand[i].startswith("The button is in seat #")):
			toRemove.append(hand[i])
		#above is alphabetic, reorder below if bored
		elif (hand[i].startswith("Time has expired")):
			toRemove.append(hand[i])
		elif (hand[i].endswith("has reconnected")):
			toRemove.append(hand[i])
		elif (hand[i].endswith("seconds left to act")):
			toRemove.append(hand[i])
		elif (hand[i].endswith("seconds to reconnect")):
			toRemove.append(hand[i])
		elif (hand[i].endswith("was removed from the table for failing to post")):
			toRemove.append(hand[i])
		elif (hand[i].find("joins the table at seat ")!=-1):
			toRemove.append(hand[i])
		elif (hand[i].endswith(" sits down")):
			toRemove.append(hand[i])
		elif (hand[i].endswith("leaves the table")):
			toRemove.append(hand[i])
		elif (hand[i].endswith(" stands up")):
			toRemove.append(hand[i])
		elif (hand[i].find("is high with ")!=-1):
			toRemove.append(hand[i])
		elif (hand[i].endswith("doesn't show hand")):
			toRemove.append(hand[i])
		elif (hand[i].endswith("is being treated as all-in")):
			toRemove.append(hand[i])
		elif (hand[i].find(" adds $")!=-1):
			toRemove.append(hand[i])
		elif (hand[i]=="Betting is capped"):
			toRemove.append(hand[i])
		#site specific variable position filter
		elif (hand[i].find(" said, \"")!=-1):
			toRemove.append(hand[i])
		elif (hand[i].find(": ")!=-1 and site=="ftp" and hand[i].find("Seat ")==-1 and hand[i].find(": Table")==-1): #filter ftp chat
			toRemove.append(hand[i])
		if isTourney:
			if (hand[i].endswith(" is sitting out") and (not hand[i].startswith("Seat "))):
				toRemove.append(hand[i])
		else:
			if (hand[i].endswith(": sits out")):
				toRemove.append(hand[i])
			elif (hand[i].endswith(" is sitting out")):
				toRemove.append(hand[i])

	
	for i in range (len(toRemove)):
		#print "removing in filterCr:",toRemove[i]
		hand.remove(toRemove[i])
	
	#print "done with filterCrap, hand:", hand
	return hand
#end filterCrap

#takes a poker float (including , for thousand seperator and converts it to an int
def float2int (string):
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

#returns boolean whether the passed line is an action line
def isActionLine(line):
	if (line.endswith("folds")):
		return True
	elif (line.endswith("checks")):
		return True
	elif (line.find("calls $")!=-1 or line.find(": calls ")!=-1):
		return True
	elif (line.find("brings in for")!=-1):
		return True
	elif (line.find("completes it to")!=-1):
		return True
	elif (line.find("posts small blind")!=-1):
		return True
	elif (line.find("posts the small blind")!=-1):
		return True
	elif (line.find("posts big blind")!=-1):
		return True
	elif (line.find("posts the big blind")!=-1):
		return True
	elif (line.find("posts small & big blinds")!=-1):
		return True
	elif (line.find(" posts $")!=-1): #this reads voluntary blind pay in FTP Holdem
		return True
	elif (line.find(" posts a dead ")!=-1): #this reads voluntary blind pay in FTP Holdem
		return True
	elif (line.find("bets $")!=-1 or line.find(": bets ")!=-1):
		return True
	elif (line.find("raises")!=-1):
		return True
	elif (line.startswith("Uncalled bet")):
		return True
	else:
		return False
#end def isActionLine

#returns whether this is a duplicate
def isAlreadyInDB(cursor, gametypeID, siteHandNo):
	cursor.execute ("SELECT id FROM Hands WHERE gametypeId=%s AND siteHandNo=%s", (gametypeID, siteHandNo))
	result=cursor.fetchall()
	if (len(result)>=1):
		raise DuplicateError ("dupl")
#end isAlreadyInDB

def isRebuyOrAddon(topline):
	"""isRebuyOrAddon not implemented yet"""
	return False
#end def isRebuyOrAddon

#returns whether the passed topline indicates a tournament or not
def isTourney(topline):
	if (topline.find("Tournament")!=-1):
		return True
	else:
		return False
#end def isTourney

#returns boolean whether the passed line is a win line
def isWinLine(line):
	if (line.find("wins the pot")!=-1):
		return True
	elif (line.find("ties for the high pot")!=-1):
		return True
	elif (line.find("ties for the high main pot")!=-1):
		return True
	elif (line.find("ties for the high side pot")!=-1):
		return True
	elif (line.find("ties for the low pot")!=-1):
		return True
	elif (line.find("ties for the low main pot")!=-1):
		return True
	elif (line.find("ties for the low side pot")!=-1):
		return True
	elif (line.find("ties for the main pot")!=-1): #for ftp tied main pot of split pot
		return True
	elif (line.find("ties for the pot")!=-1): #for ftp tie
		return True
	elif (line.find("ties for the side pot")!=-1): #for ftp tied split pots
		return True
	elif (line.find("wins side pot #")!=-1): #for ftp multi split pots
		return True
	elif (line.find("wins the low main pot")!=-1):
		return True
	elif (line.find("wins the low pot")!=-1):
		return True
	elif (line.find("wins the low side pot")!=-1):
		return True
	elif (line.find("wins the high main pot")!=-1):
		return True
	elif (line.find("wins the high pot")!=-1):
		return True
	elif (line.find("wins the high side pot")!=-1):
		return True
	elif (line.find("wins the main pot")!=-1):
		return True
	elif (line.find("wins the side pot")!=-1): #for ftp split pots
		return True
	elif (line.find("collected")!=-1):
		return True
	else:
		return False #not raising error here, any unknown line wouldve been detected in isActionLine already
#end def isWinLine

#returns the amount of cash/chips put into the put in the given action line
def parseActionAmount(line, atype, site):
	if (line.endswith(" and is all-in")):
		line=line[:-14]
	elif (line.endswith(", and is all in")):
		line=line[:-15]
	
	if line.endswith(", and is capped"):#ideally we should recognise this as an all-in if category is capXl
		line=line[:-15]
	if line.endswith(" and is capped"):
		line=line[:-14]

	
	if (atype=="fold"):
		amount=0
	elif (atype=="check"):
		amount=0
	elif (atype=="unbet" and site=="ftp"):
		pos1=line.find("$")+1
		pos2=line.find(" returned to")
		amount=float2int(line[pos1:pos2])
	elif (atype=="unbet" and site=="ps"):
		#print "ps unbet, line:",line
		pos1=line.find("$")+1
		if pos1==0:
			pos1=line.find("(")+1
		pos2=line.find(")")
		amount=float2int(line[pos1:pos2])
	elif (atype=="bet" and site=="ps" and line.find(": raises $")!=-1 and line.find("to $")!=-1):
		pos=line.find("to $")+4
		amount=float2int(line[pos:])
	else:
		pos=line.rfind("$")+1
		if pos!=0:
			amount=float2int(line[pos:])
		else:
			#print "line:"+line+"EOL"
			pos=line.rfind(" ")+1
			#print "pos:",pos
			#print "pos of 20:", line.find("20")
			amount=int(line[pos:])
	return amount
#end def parseActionAmount

#doesnt return anything, simply changes the passed arrays action_types and
#	action_amounts. For stud this expects numeric streets (3-7), for
#	holdem/omaha it expects predeal, preflop, flop, turn or river
def parseActionLine(site, base, line, street, playerIDs, names, action_types, action_amounts, actionNos, actionTypeByNo):
	if (street=="predeal" or street=="preflop"):
		street=0
	elif (street=="flop"):
		street=1
	elif (street=="turn"):
		street=2
	elif (street=="river"):
		street=3
	
	nextActionNo=0
	for player in range(len(actionNos[street])):
		for count in range(len(actionNos[street][player])):
			if actionNos[street][player][count]>=nextActionNo:
				nextActionNo=actionNos[street][player][count]+1
		
	atype=parseActionType(line)
	playerno=recognisePlayerNo(line, names, atype)
	amount=parseActionAmount(line, atype, site)
	
	action_types[street][playerno].append(atype)
	action_amounts[street][playerno].append(amount)
	actionNos[street][playerno].append(nextActionNo)
	tmp=(playerIDs[playerno], atype)
	actionTypeByNo[street].append(tmp)
#end def parseActionLine

#returns the action type code (see table design) of the given action line
def parseActionType(line):
	if (line.startswith("Uncalled bet")):
		return "unbet"
	elif (line.endswith("folds")):
		return "fold"
	elif (line.endswith("checks")):
		return "check"
	elif (line.find("calls")!=-1):
		return "call"
	elif (line.find("brings in for")!=-1):
		return "blind"
	elif (line.find("completes it to")!=-1):
		return "bet"
	   #todo: what if someone completes instead of bringing in?
	elif (line.find(" posts $")!=-1):
		return "blind"
	elif (line.find(" posts a dead ")!=-1):
		return "blind"
	elif (line.find(": posts small blind ")!=-1):
		return "blind"
	elif (line.find(" posts the small blind of $")!=-1):
		return "blind"
	elif (line.find(": posts big blind ")!=-1):
		return "blind"
	elif (line.find(" posts the big blind of $")!=-1):
		return "blind"
	elif (line.find(": posts small & big blinds $")!=-1):
		return "blind"
	#todo: seperately record voluntary blind payments made to join table out of turn
	elif (line.find("bets")!=-1):
		return "bet"
	elif (line.find("raises")!=-1):
		return "bet"
	else:
		raise FpdbError ("failed to recognise actiontype in parseActionLine in: "+line)
#end def parseActionType

#parses the ante out of the given line and checks which player paid it, updates antes accordingly.
def parseAnteLine(line, site, names, antes):
	for i in range(len(names)):
		if (line.startswith(names[i].encode("latin-1"))): #found the ante'er
			pos=line.rfind("$")+1
			if pos!=0: #found $, so must be ring
				antes[i]+=float2int(line[pos:])
			else:
				pos=line.rfind(" ")+1
				antes[i]+=int(line[pos:])
#end def parseAntes

#returns the buyin of a tourney in cents
def parseBuyin(topline):
	pos1=topline.find("$")+1
	pos2=topline.find("+")
	return float2int(topline[pos1:pos2])
#end def parseBuyin

#parses a card line and changes the passed arrays accordingly
#todo: reorganise this messy method
def parseCardLine(site, category, street, line, names, cardValues, cardSuits, boardValues, boardSuits):
	if (line.startswith("Dealt to ") or line.find(" shows [")!=-1 or line.find("mucked [")!=-1):
		playerNo=recognisePlayerNo(line, names, "card") #anything but unbet will be ok for that string

		pos=line.rfind("[")+1
		if (category=="holdem"):
			for i in (pos, pos+3):
				cardValues[playerNo].append(line[i:i+1])
				cardSuits[playerNo].append(line[i+1:i+2])
			if (len(cardValues[playerNo])!=2):
				if cardValues[playerNo][0]==cardValues[playerNo][2] and cardSuits[playerNo][1]==cardSuits[playerNo][3]: #two tests will do
					cardValues[playerNo]=cardValues[playerNo][0:2]
					cardSuits[playerNo]=cardSuits[playerNo][0:2]
				else:
					print "line:",line,"cardValues[playerNo]:",cardValues[playerNo]
					raise FpdbError("read too many/too few holecards in parseCardLine")
		elif (category=="omahahi" or category=="omahahilo"):
			for i in (pos, pos+3, pos+6, pos+9):
				cardValues[playerNo].append(line[i:i+1])
				cardSuits[playerNo].append(line[i+1:i+2])
			if (len(cardValues[playerNo])!=4):
				if cardValues[playerNo][0]==cardValues[playerNo][4] and cardSuits[playerNo][3]==cardSuits[playerNo][7]: #two tests will do
					cardValues[playerNo]=cardValues[playerNo][0:4]
					cardSuits[playerNo]=cardSuits[playerNo][0:4]
				else:
					print "line:",line,"cardValues[playerNo]:",cardValues[playerNo]
					raise FpdbError("read too many/too few holecards in parseCardLine")
		elif (category=="razz" or category=="studhi" or category=="studhilo"):
			if (line.find("shows")==-1):
				cardValues[playerNo][street-1]=line[pos:pos+1]
				cardSuits[playerNo][street-1]=line[pos+1:pos+2]
			else:
				cardValues[playerNo][0]=line[pos:pos+1]
				cardSuits[playerNo][0]=line[pos+1:pos+2]
				pos+=3
				cardValues[playerNo][1]=line[pos:pos+1]
				cardSuits[playerNo][1]=line[pos+1:pos+2]
				if street==7:
					pos+=15
					cardValues[playerNo][6]=line[pos:pos+1]
					cardSuits[playerNo][6]=line[pos+1:pos+2]
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
#end def parseCardLine

def parseCashesAndSeatNos(lines, site):
	"""parses the startCashes and seatNos of each player out of the given lines and returns them as a dictionary of two arrays"""
	cashes = []
	seatNos = []
	for i in range (len(lines)):
		pos2=lines[i].find(":")
		seatNos.append(int(lines[i][5:pos2]))
		
		pos1=lines[i].rfind("($")+2
		if pos1==1: #for tourneys - it's 1 instead of -1 due to adding 2 above
			pos1=lines[i].rfind("(")+1
		if (site=="ftp"):
			pos2=lines[i].rfind(")")
		elif (site=="ps"):
			pos2=lines[i].find(" in chips")
		cashes.append(float2int(lines[i][pos1:pos2]))
	return {'startCashes':cashes, 'seatNos':seatNos}
#end def parseCashesAndSeatNos

#returns the buyin of a tourney in cents
def parseFee(topline):
	pos1=topline.find("$")+1
	pos1=topline.find("$",pos1)+1
	pos2=topline.find(" ", pos1)
	return float2int(topline[pos1:pos2])
#end def parsefee

#returns a datetime object with the starttime indicated in the given topline
def parseHandStartTime(topline, site):
	#convert x:13:35 to 0x:13:35
	counter=0
	while (True): 
		pos=topline.find(" "+str(counter)+":")
		if (pos!=-1): 
			topline=topline[0:pos+1]+"0"+topline[pos+1:]
		counter+=1
		if counter==10: break

	if site=="ftp":
		pos = topline.find(" ", len(topline)-26)+1
		tmp = topline[pos:]
		#print "year:", tmp[14:18], "month", tmp[19:21], "day", tmp[22:24], "hour", tmp[0:2], "minute", tmp[3:5], "second", tmp[6:8]
		result = datetime.datetime(int(tmp[14:18]), int(tmp[19:21]), int(tmp[22:24]), int(tmp[0:2]), int(tmp[3:5]), int(tmp[6:8]))
	elif site=="ps":
		tmp=topline[-30:]
		#print "parsehandStartTime, tmp:", tmp
		pos = tmp.find("-")+2
		tmp = tmp[pos:]
		#print "year:", tmp[0:4], "month", tmp[5:7], "day", tmp[8:10], "hour", tmp[13:15], "minute", tmp[16:18], "second", tmp[19:21]
		result = datetime.datetime(int(tmp[0:4]), int(tmp[5:7]), int(tmp[8:10]), int(tmp[13:15]), int(tmp[16:18]), int(tmp[19:21]))
	else:
		raise FpdbError("invalid site in parseHandStartTime")
	
	if site=="ftp" or site=="ps": #these use US ET
		result+=datetime.timedelta(hours=5)
	
	return result
#end def parseHandStartTime

#parses the names out of the given lines and returns them as an array
def parseNames(lines):
	result = []
	for i in range (len(lines)):
		pos1=lines[i].find(":")+2
		pos2=lines[i].rfind("(")-1
		tmp=lines[i][pos1:pos2]
		#print "parseNames, tmp original:",tmp
		tmp=unicode(tmp,"latin-1")
		#print "parseNames, tmp after unicode latin-1 conversion:",tmp
		result.append(tmp)
	return result
#end def parseNames

#returns an array with the positions of the respective players
def parsePositions (hand, names):
	#prep array
	positions=[]
	for i in range(len(names)):
		positions.append(-1)
	
	#find blinds
	sb,bb=-1,-1
	for i in range (len(hand)):
		if (sb==-1 and hand[i].find("small blind")!=-1 and hand[i].find("dead small blind")==-1):
			sb=hand[i]
			#print "sb:",sb
		if (bb==-1 and hand[i].find("big blind")!=-1 and hand[i].find("dead big blind")==-1):
			bb=hand[i]
			#print "bb:",bb

	#identify blinds
	#print "parsePositions before recognising sb/bb. names:",names
	sbExists=True
	if (sb!=-1):
		sb=recognisePlayerNo(sb, names, "bet")
	else:
		sbExists=False
	if (bb!=-1):
		bb=recognisePlayerNo(bb, names, "bet")
	
	#write blinds into array
	if (sbExists):
		positions[sb]="S"
	positions[bb]="B"
	
	#fill up rest of array
	if (sbExists):
		arraypos=sb-1
	else:
		arraypos=bb-1
	distFromBtn=0
	while (arraypos>=0 and arraypos != bb):
		#print "parsePositions first while, arraypos:",arraypos,"positions:",positions
		positions[arraypos]=distFromBtn
		arraypos-=1
		distFromBtn+=1
	
	arraypos=len(names)-1
	if (bb!=0 or (bb==0 and sbExists==False)):
		while (arraypos>bb):
			positions[arraypos]=distFromBtn
			arraypos-=1
			distFromBtn+=1
			
	for i in range (len(names)):
		if positions[i]==-1:
			print "parsePositions names:",names
			print "result:",positions
			raise FpdbError ("failed to read positions")
	return positions
#end def parsePositions

#simply parses the rake amount and returns it as an int
def parseRake(line):
	pos=line.find("Rake")+6
	rake=float2int(line[pos:])
	return rake
#end def parseRake

def parseSiteHandNo(topline):
	"""returns the hand no assigned by the poker site"""
	pos1=topline.find("#")+1
	pos2=topline.find(":")
	return topline[pos1:pos2]
#end def parseSiteHandNo

def parseTableLine(site, line):
	"""returns a dictionary with maxSeats and tableName"""
	if site=="ps":
		pos1=line.find('\'')+1
		pos2=line.find('\'', pos1)
		#print "table:",line[pos1:pos2]
		pos3=pos2+2
		pos4=line.find("-max")
		#print "seats:",line[pos3:pos4]
		return {'maxSeats':int(line[pos3:pos4]), 'tableName':line[pos1:pos2]}
	elif site=="ftp":
		pos1=line.find("Table ")+6
		pos2=line.find("-")-1
		#print "table:",line[pos1:pos2]+"end"
		return {'maxSeats':9, 'tableName':line[pos1:pos2]}
	else:
		raise FpdbError("invalid site ID")
#end def parseTableLine

#returns the hand no assigned by the poker site
def parseTourneyNo(topline):
	pos1=topline.find("Tournament #")+12
	pos2=topline.find(",", pos1)
	#print "parseTourneyNo pos1:",pos1,"  pos2:",pos2, "  result:",topline[pos1:pos2]
	return topline[pos1:pos2]
#end def parseTourneyNo

#parses a win/collect line. manipulates the passed array winnings, no explicit return
def parseWinLine(line, site, names, winnings, isTourney):
	#print "parseWinLine: line:",line
	for i in range(len(names)):
		if (line.startswith(names[i].encode("latin-1"))): #found a winner
			if isTourney:
				pos1=line.rfind("collected ")+11
				if (site=="ftp"):
					pos2=line.find(")", pos1)
				elif (site=="ps"):
					pos2=line.find(" ", pos1)
				winnings[i]+=int(line[pos1:pos2])
			else:
				pos1=line.rfind("$")+1
				if (site=="ftp"):
					pos2=line.find(")", pos1)
				elif (site=="ps"):
					pos2=line.find(" ", pos1)
				winnings[i]+=float2int(line[pos1:pos2])
#end def parseWinLine

#returns the category (as per database) string for the given line
def recogniseCategory(line):
	if (line.find("Razz")!=-1):
		return "razz"
	elif (line.find("Hold'em")!=-1):
		return "holdem"
	elif (line.find("Omaha")!=-1 and line.find("Hi/Lo")==-1 and line.find("H/L")==-1):
		return "omahahi"
	elif (line.find("Omaha")!=-1 and (line.find("Hi/Lo")!=-1 or line.find("H/L")!=-1)):
		return "omahahilo"
	elif (line.find("Stud")!=-1 and line.find("Hi/Lo")==-1 and line.find("H/L")==-1):
		return "studhi"
	elif (line.find("Stud")!=-1 and (line.find("Hi/Lo")!=-1 or line.find("H/L")!=-1)):
		return "studhilo"
	else:
		raise FpdbError("failed to recognise category, line:"+line)
#end def recogniseCategory

#returns the int for the gametype_id for the given line
def recogniseGametypeID(cursor, topline, site_id, category, isTourney):#todo: this method is messy
	#if (topline.find("HORSE")!=-1):
	#	raise FpdbError("recogniseGametypeID: HORSE is not yet supported.")
	
	#note: the below variable names small_bet and big_bet are misleading, in NL/PL they mean small/big blind
	if isTourney:
		type="tour"
		pos1=topline.find("(")+1
		if (topline[pos1]=="H" or topline[pos1]=="O" or topline[pos1]=="R" or topline[pos1]=="S" or topline[pos1+2]=="C"):
			pos1=topline.find("(", pos1)+1
		pos2=topline.find("/", pos1)
		small_bet=int(topline[pos1:pos2])
	else:
		type="ring"
		pos1=topline.find("$")+1
		pos2=topline.find("/$")
		small_bet=float2int(topline[pos1:pos2])
	
	pos1=pos2+2
	if isTourney:
		pos1-=1	
	if (site_id==1): #ftp
		pos2=topline.find(" ", pos1)
	elif (site_id==2): #ps
		pos2=topline.find(")")
	
	if pos2<=pos1:
		pos2=topline.find(")", pos1)

	
	if isTourney:
		big_bet=int(topline[pos1:pos2])
	else:
		big_bet=float2int(topline[pos1:pos2])
	
	if (topline.find("No Limit")!=-1):
		limit_type="nl"
		if (topline.find("Cap No")!=-1):
			limit_type="cn"
	elif (topline.find("Pot Limit")!=-1):
		limit_type="pl"
		if (topline.find("Cap Pot")!=-1):
			limit_type="cp"
	else:
		limit_type="fl"
	
	#print "recogniseGametypeID small_bet/blind:",small_bet,"big bet/blind:", big_bet,"limit type:",limit_type
	if (limit_type=="fl"):
		cursor.execute ("SELECT id FROM Gametypes WHERE siteId=%s AND type=%s AND category=%s AND limitType=%s AND smallBet=%s AND bigBet=%s", (site_id, type, category, limit_type, small_bet, big_bet))
	else:
		cursor.execute ("SELECT id FROM Gametypes WHERE siteId=%s AND type=%s AND category=%s AND limitType=%s AND smallBlind=%s AND bigBlind=%s", (site_id, type, category, limit_type, small_bet, big_bet))
	result=cursor.fetchone()
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
			big_blind=small_bet #todo: read this
			small_blind=big_blind/2 #todo: read this
			cursor.execute("""INSERT INTO Gametypes
			(siteId, type, base, category, limitType, hiLo, smallBlind, bigBlind, smallBet, bigBet)
			VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""", (site_id, type, base, category, limit_type, hiLo, small_blind, big_blind, small_bet, big_bet))
			cursor.execute ("SELECT id FROM Gametypes WHERE siteId=%s AND type=%s AND category=%s AND limitType=%s AND smallBet=%s AND bigBet=%s", (site_id, type, category, limit_type, small_bet, big_bet))
		else:
			cursor.execute("""INSERT INTO Gametypes
			(siteId, type, base, category, limitType, hiLo, smallBlind, bigBlind, smallBet, bigBet)
			VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""", (site_id, type, base, category, limit_type, hiLo, small_bet, big_bet, 0, 0))#remember, for these bet means blind
			cursor.execute ("SELECT id FROM Gametypes WHERE siteId=%s AND type=%s AND category=%s AND limitType=%s AND smallBlind=%s AND bigBlind=%s", (site_id, type, category, limit_type, small_bet, big_bet))

		result=cursor.fetchone()
		#print "created new gametypes.id:",result
	
	return result[0]
#end def recogniseGametypeID

def recogniseTourneyTypeId(cursor, siteId, buyin, fee, knockout, rebuyOrAddon):
	cursor.execute ("SELECT id FROM TourneyTypes WHERE siteId=%s AND buyin=%s AND fee=%s AND knockout=%s AND rebuyOrAddon=%s", (siteId, buyin, fee, knockout, rebuyOrAddon))
	result=cursor.fetchone()
	#print "tried SELECTing gametypes.id, result:",result
	
	try:
		len(result)
	except TypeError:#this means we need to create a new entry
		cursor.execute("""INSERT INTO TourneyTypes (siteId, buyin, fee, knockout, rebuyOrAddon) VALUES (%s, %s, %s, %s, %s)""", (siteId, buyin, fee, knockout, rebuyOrAddon))
		cursor.execute("SELECT id FROM TourneyTypes WHERE siteId=%s AND buyin=%s AND fee=%s AND knockout=%s AND rebuyOrAddon=%s", (siteId, buyin, fee, knockout, rebuyOrAddon))
		result=cursor.fetchone()
	return result[0]
#end def recogniseTourneyTypeId

#returns the SQL ids of the names given in an array
def recognisePlayerIDs(cursor, names, site_id):
	result = []
	for i in range (len(names)):
		cursor.execute ("SELECT id FROM Players WHERE name=%s", (names[i],))
		tmp=cursor.fetchall()
		if (len(tmp)==0): #new player
			cursor.execute ("INSERT INTO Players (name, siteId) VALUES (%s, %s)", (names[i], site_id))
			#print "Number of players rows inserted: %d" % cursor.rowcount
			cursor.execute ("SELECT id FROM Players WHERE name=%s", (names[i],))
			tmp=cursor.fetchall()
		#print "recognisePlayerIDs, names[i]:",names[i],"tmp:",tmp
		result.append(tmp[0][0])
	return result
#end def recognisePlayerIDs

#recognises the name in the given line and returns its array position in the given array
def recognisePlayerNo(line, names, atype):
	#print "recogniseplayerno, names:",names
	for i in range (len(names)):
		if (atype=="unbet"):
			if (line.endswith(names[i].encode("latin-1"))):
				return (i)
		elif (line.startswith("Dealt to ")):
			#print "recognisePlayerNo, card precut, line:",line
			tmp=line[9:]
			#print "recognisePlayerNo, card postcut, tmp:",tmp
			if (tmp.startswith(names[i].encode("latin-1"))):
				return (i)
		elif (line.startswith("Seat ")):
			if (line.startswith("Seat 10")):
				tmp=line[9:]
			else:
				tmp=line[8:]
			
			if (tmp.startswith(names[i].encode("latin-1"))):
				return (i)
		else:
			if (line.startswith(names[i].encode("latin-1"))):
				return (i)
	#if we're here we mustve failed
	raise FpdbError ("failed to recognise player in: "+line+" atype:"+atype)
#end def recognisePlayerNo

#returns the site abbreviation for the given site
def recogniseSite(line):
	if (line.startswith("Full Tilt Poker")):
		return "ftp"
	elif (line.startswith("PokerStars")):
		return "ps"
	else:
		raise FpdbError("failed to recognise site, line:"+line)
#end def recogniseSite

#returns the ID of the given site
def recogniseSiteID(cursor, site):
	if (site=="ftp"):
		cursor.execute("SELECT id FROM Sites WHERE name = ('Full Tilt Poker')")
	elif (site=="ps"):
		cursor.execute("SELECT id FROM Sites WHERE name = ('PokerStars')")
	return cursor.fetchall()[0][0]
#end def recogniseSiteID

#removes trailing \n from the given array
def removeTrailingEOL(arr):
	for i in range(len(arr)):
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
	for i in range(len(winnings)):
		if winnings[i]!=0:
			winnercnt+=1
			totalWin+=winnings[i]
			firstWinner=i
	if winnercnt==1:
		rakes[firstWinner]=totalRake
	else:
		totalWin=float(totalWin)
		for i in range(len(winnings)):
			if winnings[i]!=0:
				winPortion=winnings[i]/totalWin
				rakes[i]=totalRake*winPortion
#end def splitRake

def storeActions(cursor, hands_players_ids, action_types, action_amounts, actionNos):
#stores into table hands_actions
	#print "start of storeActions, actionNos:",actionNos
	#print "                  action_amounts:",action_amounts
	for i in range (len(action_types)): #iterate through streets
		for j in range (len(action_types[i])): #iterate through names
			for k in range (len(action_types[i][j])):  #iterate through individual actions of that player on that street
				cursor.execute ("INSERT INTO HandsActions (handPlayerId, street, actionNo, action, amount) VALUES (%s, %s, %s, %s, %s)", (hands_players_ids[j], i, actionNos[i][j][k], action_types[i][j][k], action_amounts[i][j][k]))
#end def storeActions

def store_board_cards(cursor, hands_id, board_values, board_suits):
#stores into table board_cards
	cursor.execute ("""INSERT INTO BoardCards (handId, card1Value, card1Suit,
	card2Value, card2Suit, card3Value, card3Suit, card4Value, card4Suit,
	card5Value, card5Suit) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
	(hands_id, board_values[0], board_suits[0], board_values[1], board_suits[1],
	board_values[2], board_suits[2], board_values[3], board_suits[3],
	board_values[4], board_suits[4]))
#end def store_board_cards

def storeHands(cursor, site_hand_no, gametype_id, hand_start_time, names, tableName, maxSeats):
#stores into table hands
	cursor.execute ("INSERT INTO Hands (siteHandNo, gametypeId, handStart, seats, tableName, importTime, maxSeats) VALUES (%s, %s, %s, %s, %s, %s, %s)", (site_hand_no, gametype_id, hand_start_time, len(names), tableName, datetime.datetime.today(), maxSeats))
	#todo: find a better way of doing this...
	cursor.execute("SELECT id FROM Hands WHERE siteHandNo=%s AND gametypeId=%s", (site_hand_no, gametype_id))
	return cursor.fetchall()[0][0]
#end def storeHands

def store_hands_players_holdem_omaha(cursor, category, hands_id, player_ids, start_cashes, positions, card_values, card_suits, winnings, rakes, seatNos):
	result=[]
	if (category=="holdem"):
		for i in range (len(player_ids)):
			cursor.execute ("""
			INSERT INTO HandsPlayers 
			(handId, playerId, startCash, position,
			card1Value, card1Suit, card2Value, card2Suit, winnings, rake, seatNo) 
			VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
			(hands_id, player_ids[i], start_cashes[i], positions[i],
			card_values[i][0], card_suits[i][0], card_values[i][1],	card_suits[i][1],
			winnings[i], rakes[i], seatNos[i]))
			cursor.execute("SELECT id FROM HandsPlayers WHERE handId=%s AND playerId=%s", (hands_id, player_ids[i]))
			result.append(cursor.fetchall()[0][0])
	elif (category=="omahahi" or category=="omahahilo"):
		for i in range (len(player_ids)):
			cursor.execute ("""INSERT INTO HandsPlayers 
			(handId, playerId, startCash,	position,
			card1Value, card1Suit, card2Value, card2Suit,
			card3Value, card3Suit, card4Value, card4Suit, winnings, rake, seatNo) 
			VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
			(hands_id, player_ids[i], start_cashes[i], positions[i],
			card_values[i][0], card_suits[i][0], card_values[i][1],	card_suits[i][1],
			card_values[i][2], card_suits[i][2], card_values[i][3],	card_suits[i][3],
			winnings[i], rakes[i], seatNo[i]))
			cursor.execute("SELECT id FROM hands_players WHERE hand_id=%s AND player_id=%s", (hands_id, player_ids[i]))
			result.append(cursor.fetchall()[0][0])
	else:
		raise FpdbError("invalid category")
	return result
#end def store_hands_players_holdem_omaha

def store_hands_players_stud(cursor, hands_id, player_ids, start_cashes, antes,
			card_values, card_suits, winnings, rakes):
#stores hands_players rows for stud/razz games. returns an array of the resulting IDs
	result=[]
	for i in range (len(player_ids)):
		cursor.execute ("""INSERT INTO HandsPlayers 
		(handId, playerId, startCash, ante,
		card1Value, card1Suit, card2Value, card2Suit,
		card3Value, card3Suit, card4Value, card4Suit,
		card5Value, card5Suit, card6Value, card6Suit,
		card7Value, card7Suit, winnings, rake) 
		VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
		%s, %s, %s, %s)""",
		(hands_id, player_ids[i], start_cashes[i], antes[i],
		card_values[i][0], card_suits[i][0], card_values[i][1],	card_suits[i][1],
		card_values[i][2], card_suits[i][2], card_values[i][3], card_suits[i][3],
		card_values[i][4], card_suits[i][4], card_values[i][5], card_suits[i][5],
		card_values[i][6], card_suits[i][6], winnings[i], rakes[i]))
		cursor.execute("SELECT id FROM HandsPlayers WHERE handId=%s AND playerId=%s", (hands_id, player_ids[i]))
		result.append(cursor.fetchall()[0][0])
	return result
#end def store_hands_players_stud

def store_hands_players_holdem_omaha_tourney(cursor, category, hands_id, player_ids, start_cashes, positions, card_values, card_suits, winnings, rakes, seatNos, tourneys_players_ids):
#stores hands_players for tourney holdem/omaha hands
	result=[]
	for i in range (len(player_ids)):
		if len(card_values[0])==2:
			cursor.execute ("""INSERT INTO HandsPlayers 
			(handId, playerId, startCash, position,
			card1Value, card1Suit, card2Value, card2Suit,
			winnings, rake, tourneysPlayersId, seatNo) 
			VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
			(hands_id, player_ids[i], start_cashes[i], positions[i],
			card_values[i][0], card_suits[i][0], card_values[i][1],	card_suits[i][1],
			winnings[i], rakes[i], tourneys_players_ids[i], seatNos[i]))
		elif len(card_values[0])==4:
			cursor.execute ("""INSERT INTO HandsPlayers 
			(handId, playerId, startCash, position,
			card1Value, card1Suit, card2Value, card2Suit,
			card3Value, card3Suit, card4Value, card4Suit,
			winnings, rake, tourneysPlayersId, seatNo) 
			VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
			(hands_id, player_ids[i], start_cashes[i], positions[i],
			card_values[i][0], card_suits[i][0], card_values[i][1],	card_suits[i][1],
			card_values[i][2], card_suits[i][2], card_values[i][3], card_suits[i][3],
			winnings[i], rakes[i], tourneys_players_ids[i], seatNos[i]))
		else:
			raise FpdbError ("invalid card_values length:"+str(len(card_values[0])))
		cursor.execute("SELECT id FROM HandsPlayers WHERE handId=%s AND playerId=%s", (hands_id, player_ids[i]))
		result.append(cursor.fetchall()[0][0])
	
	return result
#end def store_hands_players_holdem_omaha_tourney

def store_hands_players_stud_tourney(cursor, hands_id, player_ids, start_cashes,
			antes, card_values, card_suits, winnings, rakes, tourneys_players_ids):
#stores hands_players for tourney stud/razz hands
	result=[]
	for i in range (len(player_ids)):
		cursor.execute ("""INSERT INTO HandsPlayers 
		(hand_id, player_id, player_startcash,	ante,
		card1_value, card1_suit, card2_value, card2_suit,
		card3_value, card3_suit, card4_value, card4_suit,
		card5_value, card5_suit, card6_value, card6_suit,
		card7_value, card7_suit, winnings, rake, tourneys_players_id) 
		VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
		%s, %s, %s, %s, %s)""",
		(hands_id, player_ids[i], start_cashes[i], antes[i],
		card_values[i][0], card_suits[i][0], card_values[i][1],	card_suits[i][1],
		card_values[i][2], card_suits[i][2], card_values[i][3], card_suits[i][3],
		card_values[i][4], card_suits[i][4], card_values[i][5], card_suits[i][5],
		card_values[i][6], card_suits[i][6], winnings[i], rakes[i], tourneys_players_ids[i]))
		cursor.execute("SELECT id FROM hands_players WHERE hand_id=%s AND player_id=%s", (hands_id, player_ids[i]))
		result.append(cursor.fetchall()[0][0])
	return result
#end def store_hands_players_stud_tourney

def generateHudCacheData(player_ids, category, action_types, actionTypeByNo, winnings, totalWinnings, positions):
	"""calculates data for the HUD during import. IMPORTANT: if you change this method make sure to also change the following storage method and table_viewer.prepare_data if necessary"""
	#setup subarrays of the result dictionary.
	street0VPI=[]
	street0Aggr=[]
	street0_3B4BChance=[]
	street0_3B4BDone=[]
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
	
	firstPfRaiseByNo=-1
	firstPfRaiserId=-1
	firstPfRaiserNo=-1
	firstPfCallByNo=-1
	firstPfCallerId=-1
	for i in range(len(actionTypeByNo[0])):
		if actionTypeByNo[0][i][1]=="bet":
			firstPfRaiseByNo=i
			firstPfRaiserId=actionTypeByNo[0][i][0]
			for j in range(len(player_ids)):
				if player_ids[j]==firstPfRaiserId:
					firstPfRaiserNo=j
					break
			break
	for i in range(len(actionTypeByNo[0])):
		if actionTypeByNo[0][i][1]=="call":
			firstPfCallByNo=i
			firstPfCallerId=actionTypeByNo[0][i][0]
			break
	
	cutoffId=-1
	buttonId=-1
	sbId=-1
	bbId=-1
	for player in range(len(positions)):
		if positions==1:
			cutoffId=player_ids[player]
		if positions==0:
			buttonId=player_ids[player]
		if positions=='S':
			sbId=player_ids[player]
		if positions=='B':
			bbId=player_ids[player]
			
	someoneStole=False
	
	#run a loop for each player preparing the actual values that will be commited to SQL
	for player in range (len(player_ids)):
		#set default values
		myStreet0VPI=False
		myStreet0Aggr=False
		myStreet0_3B4BChance=False
		myStreet0_3B4BDone=False
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
		
		#calculate VPIP and PFR
		street=0
		heroPfRaiseCount=0
		for count in range (len(action_types[street][player])):#finally individual actions
			currentAction=action_types[street][player][count]
			if currentAction=="bet":
				myStreet0Aggr=True
			if (currentAction=="bet" or currentAction=="call"):
				myStreet0VPI=True
		
		#PF3B4BChance and PF3B4B
		pfFold=-1
		pfRaise=-1
		if firstPfRaiseByNo!=-1:
			for i in range(len(actionTypeByNo[0])):
				if actionTypeByNo[0][i][0]==player_ids[player]:
					if actionTypeByNo[0][i][1]=="bet" and pfRaise==-1 and i>firstPfRaiseByNo:
						pfRaise=i
					if actionTypeByNo[0][i][1]=="fold" and pfFold==-1:
						pfFold=i
			if pfFold==-1 or pfFold>firstPfRaiseByNo:
				myStreet0_3B4BChance=True
				if pfRaise>firstPfRaiseByNo:
					myStreet0_3B4BDone=True
		
		#steal calculations
		if len(player_ids)>=5: #no point otherwise
			if positions[player]==1:
				if firstPfRaiserId==player_ids[player]:
					myStealAttemptChance=True
					myStealAttempted=True
				elif firstPfRaiserId==buttonId or firstPfRaiserId==sbId or firstPfRaiserId==bbId or firstPfRaiserId==-1:
					myStealAttemptChance=True
			if positions[player]==0:
				if firstPfRaiserId==player_ids[player]:
					myStealAttemptChance=True
					myStealAttempted=True
				elif firstPfRaiserId==sbId or firstPfRaiserId==bbId or firstPfRaiserId==-1:
					myStealAttemptChance=True
			if positions[player]=='S':
				if firstPfRaiserId==player_ids[player]:
					myStealAttemptChance=True
					myStealAttempted=True
				elif firstPfRaiserId==bbId or firstPfRaiserId==-1:
					myStealAttemptChance=True
			if positions[player]=='B':
				pass
			
			if myStealAttempted:
				someoneStole=True

		#calculate saw* values
		if (len(action_types[1][player])>0):
			myStreet1Seen=True
			if (len(action_types[2][player])>0):
				myStreet2Seen=True
				if (len(action_types[3][player])>0):
					myStreet3Seen=True
					mySawShowdown=True
					for count in range (len(action_types[3][player])):
						if action_types[3][player][count]=="fold":
							mySawShowdown=False

		#flop stuff
		street=1
		if myStreet1Seen:
			for count in range(len(action_types[street][player])):
				if action_types[street][player][count]=="bet":
					myStreet1Aggr=True
			
			for otherPlayer in range (len(player_ids)):
				if player==otherPlayer:
					pass
				else:
					for countOther in range (len(action_types[street][otherPlayer])):
						if action_types[street][otherPlayer][countOther]=="bet":
							myOtherRaisedStreet1=True
							for countOtherFold in range (len(action_types[street][player])):
								if action_types[street][player][countOtherFold]=="fold":
									myFoldToOtherRaisedStreet1=True
		
		#turn stuff - copy of flop with different vars
		street=2
		if myStreet2Seen:
			for count in range(len(action_types[street][player])):
				if action_types[street][player][count]=="bet":
					myStreet2Aggr=True
			
			for otherPlayer in range (len(player_ids)):
				if player==otherPlayer:
					pass
				else:
					for countOther in range (len(action_types[street][otherPlayer])):
						if action_types[street][otherPlayer][countOther]=="bet":
							myOtherRaisedStreet2=True
							for countOtherFold in range (len(action_types[street][player])):
								if action_types[street][player][countOtherFold]=="fold":
									myFoldToOtherRaisedStreet2=True
		
		#river stuff - copy of flop with different vars
		street=3
		if myStreet3Seen:
			for count in range(len(action_types[street][player])):
				if action_types[street][player][count]=="bet":
					myStreet3Aggr=True
			
			for otherPlayer in range (len(player_ids)):
				if player==otherPlayer:
					pass
				else:
					for countOther in range (len(action_types[street][otherPlayer])):
						if action_types[street][otherPlayer][countOther]=="bet":
							myOtherRaisedStreet3=True
							for countOtherFold in range (len(action_types[street][player])):
								if action_types[street][player][countOtherFold]=="fold":
									myFoldToOtherRaisedStreet3=True
		
		if winnings[player]!=0:
			if myStreet1Seen:
				myWonWhenSeenStreet1=winnings[player]/float(totalWinnings)
				if mySawShowdown:
					myWonAtSD=myWonWhenSeenStreet1
		
		#add each value to the appropriate array
		street0VPI.append(myStreet0VPI)
		street0Aggr.append(myStreet0Aggr)
		street0_3B4BChance.append(myStreet0_3B4BChance)
		street0_3B4BDone.append(myStreet0_3B4BDone)
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
		elif pos>=5 and pos<=7:
			hudDataPositions.append('L')
		else:
			raise FpdbError("invalid position")
	
	#add each array to the to-be-returned dictionary
	result={'street0VPI':street0VPI}
	result['street0Aggr']=street0Aggr
	result['street0_3B4BChance']=street0_3B4BChance
	result['street0_3B4BDone']=street0_3B4BDone
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
	
	#now the various steal values
	foldBbToStealChance=[]
	foldedBbToSteal=[]
	foldSbToStealChance=[]
	foldedSbToSteal=[]
	for player in range (len(player_ids)):
		myFoldBbToStealChance=False
		myFoldedBbToSteal=False
		myFoldSbToStealChance=False
		myFoldedSbToSteal=False
		
		if someoneStole and (positions[player]=='B' or positions[player]=='S') and firstPfRaiserId!=player_ids[player]:
			street=0
			for count in range (len(action_types[street][player])):#individual actions
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
	for player in range (len(player_ids)):
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
	for player in range (len(player_ids)):
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
	for player in range (len(player_ids)):
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
	for player in range (len(player_ids)):
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
	
	for player in range (len(player_ids)):
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
	for player in range (len(player_ids)):
		myTotalProfit=0
		
		myStreet1CheckCallRaiseChance=False
		myStreet1CheckCallRaiseDone=False
		myStreet2CheckCallRaiseChance=False
		myStreet2CheckCallRaiseDone=False
		myStreet3CheckCallRaiseChance=False
		myStreet3CheckCallRaiseDone=False
		myStreet4CheckCallRaiseChance=False
		myStreet4CheckCallRaiseDone=False
		
		totalProfit.append(myTotalProfit)
		
		street1CheckCallRaiseChance.append(myStreet1CheckCallRaiseChance)
		street1CheckCallRaiseDone.append(myStreet1CheckCallRaiseDone)
		street2CheckCallRaiseChance.append(myStreet2CheckCallRaiseChance)
		street2CheckCallRaiseDone.append(myStreet2CheckCallRaiseDone)
		street3CheckCallRaiseChance.append(myStreet3CheckCallRaiseChance)
		street3CheckCallRaiseDone.append(myStreet3CheckCallRaiseDone)
		street4CheckCallRaiseChance.append(myStreet4CheckCallRaiseChance)
		street4CheckCallRaiseDone.append(myStreet4CheckCallRaiseDone)

	result['totalProfit']=totalProfit

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
	for action in range(len(actionTypeByNo[street])):
		if actionTypeByNo[street][action][1]=="bet":
			for player in didStreetCB:
				if player==actionTypeByNo[street][action][0] and firstCBReaction==0:
					firstCBReaction=action+1
					break
	
	for action in actionTypeByNo[street][firstCBReaction:]:
		for player in range(len(playerIDs)):
			if playerIDs[player]==action[0]:
				foldToStreetCBChance[player]=True
				if action[1]=="fold":
					foldToStreetCBDone[player]=True
#end def generateFoldToCB

def storeHudCache(cursor, category, gametypeId, playerIds, hudImportData):
	if (category=="holdem" or category=="omahahi" or category=="omahahilo"):
		for player in range (len(playerIds)):
			cursor.execute("SELECT * FROM HudCache WHERE gametypeId=%s AND playerId=%s AND activeSeats=%s AND position=%s", (gametypeId, playerIds[player], len(playerIds), hudImportData['position'][player]))
			row=cursor.fetchone()
			#print "gametypeId:", gametypeId, "playerIds[player]",playerIds[player], "len(playerIds):",len(playerIds), "row:",row
			
			try: len(row)
			except TypeError:
				row=[]
			
			if (len(row)==0):
				#print "new huddata row"
				doInsert=True
				row=[]
				row.append(0)#blank for id
				row.append(gametypeId)
				row.append(playerIds[player])
				row.append(len(playerIds))#seats
				for i in range(len(hudImportData)+2):
					row.append(0)
				
			else:
				doInsert=False
				newrow=[]
				for i in range(len(row)):
					newrow.append(row[i])
				row=newrow
			
			row[4]=hudImportData['position'][player]
			row[5]=1 #tourneysGametypeId
			row[6]+=1 #HDs
			if hudImportData['street0VPI'][player]: row[7]+=1
			if hudImportData['street0Aggr'][player]: row[8]+=1
			if hudImportData['street0_3B4BChance'][player]: row[9]+=1
			if hudImportData['street0_3B4BDone'][player]: row[10]+=1
			if hudImportData['street1Seen'][player]: row[11]+=1
			if hudImportData['street2Seen'][player]: row[12]+=1
			if hudImportData['street3Seen'][player]: row[13]+=1
			if hudImportData['street4Seen'][player]: row[14]+=1
			if hudImportData['sawShowdown'][player]: row[15]+=1
			if hudImportData['street1Aggr'][player]: row[16]+=1
			if hudImportData['street2Aggr'][player]: row[17]+=1
			if hudImportData['street3Aggr'][player]: row[18]+=1
			if hudImportData['street4Aggr'][player]: row[19]+=1
			if hudImportData['otherRaisedStreet1'][player]: row[20]+=1
			if hudImportData['otherRaisedStreet2'][player]: row[21]+=1
			if hudImportData['otherRaisedStreet3'][player]: row[22]+=1
			if hudImportData['otherRaisedStreet4'][player]: row[23]+=1
			if hudImportData['foldToOtherRaisedStreet1'][player]: row[24]+=1
			if hudImportData['foldToOtherRaisedStreet2'][player]: row[25]+=1
			if hudImportData['foldToOtherRaisedStreet3'][player]: row[26]+=1
			if hudImportData['foldToOtherRaisedStreet4'][player]: row[27]+=1
			if hudImportData['wonWhenSeenStreet1'][player]!=0.0: row[28]+=hudImportData['wonWhenSeenStreet1'][player]
			if hudImportData['wonAtSD'][player]!=0.0: row[29]+=hudImportData['wonAtSD'][player]
			if hudImportData['stealAttemptChance'][player]: row[30]+=1
			if hudImportData['stealAttempted'][player]: row[31]+=1
			if hudImportData['foldBbToStealChance'][player]: row[32]+=1
			if hudImportData['foldedBbToSteal'][player]: row[33]+=1
			if hudImportData['foldSbToStealChance'][player]: row[34]+=1
			if hudImportData['foldedSbToSteal'][player]: row[35]+=1
			
			if hudImportData['street1CBChance'][player]: row[36]+=1
			if hudImportData['street1CBDone'][player]: row[37]+=1
			if hudImportData['street2CBChance'][player]: row[38]+=1
			if hudImportData['street2CBDone'][player]: row[39]+=1
			if hudImportData['street3CBChance'][player]: row[40]+=1
			if hudImportData['street3CBDone'][player]: row[41]+=1
			if hudImportData['street4CBChance'][player]: row[42]+=1
			if hudImportData['street4CBDone'][player]: row[43]+=1
			
			if hudImportData['foldToStreet1CBChance'][player]: row[44]+=1
			if hudImportData['foldToStreet1CBDone'][player]: row[45]+=1
			if hudImportData['foldToStreet2CBChance'][player]: row[46]+=1
			if hudImportData['foldToStreet2CBDone'][player]: row[47]+=1
			if hudImportData['foldToStreet3CBChance'][player]: row[48]+=1
			if hudImportData['foldToStreet3CBDone'][player]: row[49]+=1
			if hudImportData['foldToStreet4CBChance'][player]: row[50]+=1
			if hudImportData['foldToStreet4CBDone'][player]: row[51]+=1

			row[52]+=hudImportData['totalProfit'][player]

			if hudImportData['street1CheckCallRaiseChance'][player]: row[53]+=1
			if hudImportData['street1CheckCallRaiseDone'][player]: row[54]+=1
			if hudImportData['street2CheckCallRaiseChance'][player]: row[55]+=1
			if hudImportData['street2CheckCallRaiseDone'][player]: row[56]+=1
			if hudImportData['street3CheckCallRaiseChance'][player]: row[57]+=1
			if hudImportData['street3CheckCallRaiseDone'][player]: row[58]+=1
			if hudImportData['street4CheckCallRaiseChance'][player]: row[59]+=1
			if hudImportData['street4CheckCallRaiseDone'][player]: row[60]+=1
			
			if doInsert:
				#print "playerid before insert:",row[2]
				cursor.execute("""INSERT INTO HudCache
					(gametypeId, playerId, activeSeats, position, tourneyTypeId, 
					HDs, street0VPI, street0Aggr, street0_3B4BChance, street0_3B4BDone,
					street1Seen, street2Seen, street3Seen, street4Seen, sawShowdown,
					street1Aggr, street2Aggr, street3Aggr, street4Aggr, otherRaisedStreet1,
					otherRaisedStreet2, otherRaisedStreet3, otherRaisedStreet4, foldToOtherRaisedStreet1, foldToOtherRaisedStreet2, 
					foldToOtherRaisedStreet3, foldToOtherRaisedStreet4, wonWhenSeenStreet1, wonAtSD, stealAttemptChance, 
					stealAttempted, foldBbToStealChance, foldedBbToSteal, foldSbToStealChance, foldedSbToSteal, 
					street1CBChance, street1CBDone, street2CBChance, street2CBDone, street3CBChance, 
					street3CBDone, street4CBChance, street4CBDone, foldToStreet1CBChance, foldToStreet1CBDone, 
					foldToStreet2CBChance, foldToStreet2CBDone, foldToStreet3CBChance, foldToStreet3CBDone, foldToStreet4CBChance, 
					foldToStreet4CBDone, totalProfit, street1CheckCallRaiseChance, street1CheckCallRaiseDone, street2CheckCallRaiseChance, 
					street2CheckCallRaiseDone, street3CheckCallRaiseChance, street3CheckCallRaiseDone, street4CheckCallRaiseChance, street4CheckCallRaiseDone)
					VALUES (%s, %s, %s, %s, %s, 
					%s, %s, %s, %s, %s, 
					%s, %s, %s, %s, %s, 
					%s, %s, %s, %s, %s, 
					%s, %s, %s, %s, %s, 
					%s, %s, %s, %s, %s, 
					%s, %s, %s, %s, %s, 
					%s, %s, %s, %s, %s, 
					%s, %s, %s, %s, %s, 
					%s, %s, %s, %s, %s, 
					%s, %s, %s, %s, %s, 
					%s, %s, %s, %s, %s)""", (row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[12], row[13], row[14], row[15], row[16], row[17], row[18], row[19], row[20], row[21], row[22], row[23], row[24], row[25], row[26], row[27], row[28], row[29], row[30], row[31], row[32], row[33], row[34], row[35], row[36], row[37], row[38], row[39], row[40], row[41], row[42], row[43], row[44], row[45], row[46], row[47], row[48], row[49], row[50], row[51], row[52], row[53], row[54], row[55], row[56], row[57], row[58], row[59], row[60]))
			else:
				#print "storing updated hud data line"
				cursor.execute("""UPDATE HudCache
					SET HDs=%s, street0VPI=%s, street0Aggr=%s, street0_3B4BChance=%s, street0_3B4BDone=%s, 
					street1Seen=%s, street2Seen=%s, street3Seen=%s, street4Seen=%s, sawShowdown=%s, 
					street1Aggr=%s, street2Aggr=%s, street3Aggr=%s, street4Aggr=%s, otherRaisedStreet1=%s, 
					otherRaisedStreet2=%s, otherRaisedStreet3=%s, otherRaisedStreet4=%s, foldToOtherRaisedStreet1=%s, foldToOtherRaisedStreet2=%s, 
					foldToOtherRaisedStreet3=%s, foldToOtherRaisedStreet4=%s, wonWhenSeenStreet1=%s, wonAtSD=%s, stealAttemptChance=%s, 
					stealAttempted=%s, foldBbToStealChance=%s, foldedBbToSteal=%s, foldSbToStealChance=%s, foldedSbToSteal=%s, 
					street1CBChance=%s, street1CBDone=%s, street2CBChance=%s, street2CBDone=%s, street3CBChance=%s, 
					street3CBDone=%s, street4CBChance=%s, street4CBDone=%s, foldToStreet1CBChance=%s, foldToStreet1CBDone=%s, 
					foldToStreet2CBChance=%s, foldToStreet2CBDone=%s, foldToStreet3CBChance=%s, foldToStreet3CBDone=%s, foldToStreet4CBChance=%s, 
					foldToStreet4CBDone=%s, totalProfit=%s, street1CheckCallRaiseChance=%s, street1CheckCallRaiseDone=%s, street2CheckCallRaiseChance=%s, 
					street2CheckCallRaiseDone=%s, street3CheckCallRaiseChance=%s, street3CheckCallRaiseDone=%s, street4CheckCallRaiseChance=%s, street4CheckCallRaiseDone=%s
					WHERE gametypeId=%s AND playerId=%s AND activeSeats=%s AND position=%s AND tourneyTypeId=%s""", (row[6], row[7], row[8], row[9], row[10], 
					row[11], row[12], row[13], row[14], row[15], 
					row[16], row[17], row[18], row[19], row[20], 
					row[21], row[22], row[23], row[24], row[25], 
					row[26], row[27], row[28], row[29], row[30], 
					row[31], row[32], row[33], row[34], row[35], row[36], row[37], row[38], row[39], row[40], 
					row[41], row[42], row[43], row[44], row[45], row[46], row[47], row[48], row[49], row[50], 
					row[51], row[52], row[53], row[54], row[55], row[56], row[57], row[58], row[59], row[60], 
					row[1], row[2], row[3], row[4], row[5]))
	else:
		print "todo: implement storeHudCache for stud base"
#end def storeHudCache

def store_tourneys(cursor, tourneyTypeId, siteTourneyNo, entries, prizepool, startTime):
	cursor.execute("SELECT id FROM Tourneys WHERE siteTourneyNo=%s AND tourneyTypeId=%s", (siteTourneyNo, tourneyTypeId))
	tmp=cursor.fetchone()
	#print "tried SELECTing tourneys.id, result:",tmp
	
	try:
		len(tmp)
	except TypeError:#means we have to create new one
		cursor.execute("""INSERT INTO Tourneys
		(tourneyTypeId, siteTourneyNo, entries, prizepool, startTime)
		VALUES (%s, %s, %s, %s, %s)""", (tourneyTypeId, siteTourneyNo, entries, prizepool, startTime))
		cursor.execute("SELECT id FROM Tourneys WHERE siteTourneyNo=%s AND tourneyTypeId=%s", (siteTourneyNo, tourneyTypeId))
		tmp=cursor.fetchone()
		#print "created new tourneys.id:",tmp
	return tmp[0]
#end def store_tourneys

def store_tourneys_players(cursor, tourney_id, player_ids, payin_amounts, ranks, winnings):
	result=[]
	#print "in store_tourneys_players. tourney_id:",tourney_id
	#print "player_ids:",player_ids
	#print "payin_amounts:",payin_amounts
	#print "ranks:",ranks
	#print "winnings:",winnings
	for i in range (len(player_ids)):
		cursor.execute("SELECT id FROM TourneysPlayers WHERE tourneyId=%s AND playerId=%s", (tourney_id, player_ids[i]))
		tmp=cursor.fetchone()
		#print "tried SELECTing tourneys_players.id:",tmp
		
		try:
			len(tmp)
		except TypeError:
			cursor.execute("""INSERT INTO TourneysPlayers
			(tourneyId, playerId, payinAmount, rank, winnings) VALUES (%s, %s, %s, %s, %s)""",
			(tourney_id, player_ids[i], payin_amounts[i], ranks[i], winnings[i]))
			
			cursor.execute("SELECT id FROM TourneysPlayers WHERE tourneyId=%s AND playerId=%s",
						   (tourney_id, player_ids[i]))
			tmp=cursor.fetchone()
			#print "created new tourneys_players.id:",tmp
		result.append(tmp[0])
	return result
#end def store_tourneys_players
