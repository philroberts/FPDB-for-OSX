#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Copyright 2008-2011 Steffen Schaumburg
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

#This is intended mostly for regression testing

import sys
import MySQLdb
from optparse import OptionParser
import fpdb_util_lib as ful

parser = OptionParser()
parser.add_option("-n", "--handNumber", "--hand", type="int",
				help="Number of the hand to print")
parser.add_option("-p", "--password", help="The password for the MySQL user")
parser.add_option("-s", "--site", default="PokerStars",
				help="Name of the site (as written in the history files)")

(options, sys.argv) = parser.parse_args()

if options.handNumber==None or options.site==None:
	print "please supply a hand number and site name. TODO: make this work"

db = MySQLdb.connect("localhost", "fpdb", options.password, "fpdb")
cursor = db.cursor()
print "Connected to MySQL on localhost. Print Hand Utility"

cursor.execute("SELECT id FROM Sites WHERE name=%s", (options.site,))
siteId=cursor.fetchone()[0]
print "options.site:",options.site,"siteId:",siteId

print ""
print "From Table Hands"
print "================"

cursor.execute("""SELECT Hands.* FROM Hands INNER JOIN Gametypes
ON Hands.gametypeId = Gametypes.id WHERE Gametypes.siteId=%s AND Hands.siteHandNo=%s""",
(siteId, options.handNumber))
handsResult=cursor.fetchone()
handId=handsResult[0]
tableName=handsResult[1]
siteHandNo=options.handNumber
gametypeId=handsResult[3]
handStart=handsResult[4]
#skip importTime
seats=handsResult[6]
maxSeats=handsResult[7]
print "handId:", handId, "  tableName:", tableName, "  siteHandNo:", siteHandNo, "  gametypeId:", gametypeId, "  handStart:", handStart, "  seats:", seats, "  maxSeats:", maxSeats


print ""
print "From Table Gametypes"
print "===================="

cursor.execute("""SELECT type, base, category, limitType, hiLo FROM Gametypes WHERE id=%s""", (gametypeId, ))
typeEtc=cursor.fetchone()
type=typeEtc[0]
base=typeEtc[1]
category=typeEtc[2]
limitType=typeEtc[3]
hiLo=typeEtc[4]
print "type:", type, "  base:", base, "  category:", category, "  limitType:", limitType, "  hiLo:", hiLo

gtString=""
doBets=False
if base=="hold":
	cursor.execute("SELECT smallBlind FROM Gametypes WHERE id=%s", (gametypeId, ))
	sb=cursor.fetchone()[0]
	cursor.execute("SELECT bigBlind FROM Gametypes WHERE id=%s", (gametypeId, ))
	bb=cursor.fetchone()[0]
	gtString=("sb: "+str(sb)+"   bb: "+str(bb))
	if (limitType=="fl"):
		doBets=True
elif base=="stud":
	doBets=True
	
if doBets:
	cursor.execute("SELECT smallBet FROM Gametypes WHERE id=%s", (gametypeId, ))
	sbet=cursor.fetchone()[0]
	cursor.execute("SELECT bigBet FROM Gametypes WHERE id=%s", (gametypeId, ))
	bbet=cursor.fetchone()[0]
	gtString+=("   sbet: "+str(sbet)+"   bbet: "+str(bbet))
print gtString

if type=="ring":
	pass
elif type=="tour":
	#cursor.execute("SELECT tourneys_players_id FROM hands
	cursor.execute("""SELECT DISTINCT TourneysPlayers.id
	FROM Hands JOIN HandsPlayers ON HandsPlayers.handId=Hands.id
	JOIN TourneysPlayers ON HandsPlayers.tourneysPlayersId=TourneysPlayers.id
	WHERE Hands.id=%s""", (hand_id,))
	handsPlayersIds=cursor.fetchall()
	print "dbg hands_players_ids:",handsPlayersIds
	
	print ""
	print "From Table Tourneys"
	print "==================="
	print "TODO"
	
	
	print ""
	print "From Table TourneysPlayers"
	print "=========================="
	print "TODO"
else:
	print "invalid type:",type
	sys.exit(1)


print ""
print "From Table BoardCards"
print "====================="

if (category=="holdem" or category=="omahahi" or category=="omahahilo"):
	cursor.execute("""SELECT * FROM BoardCards WHERE handId=%s""",(handId, ))
	bc=cursor.fetchone()
	print "Board cards:", ful.cards2String(bc[2:])


print ""
print "From Table HandsPlayers"
print "======================="
cursor.execute("""SELECT * FROM HandsPlayers WHERE handId=%s""",(handId, ))
handsPlayers=cursor.fetchall()
playerNames=[]
for i in range (len(handsPlayers)):
	line=handsPlayers[i][2:]
	playerNames.append(ful.id_to_player_name(cursor, line[0]))
	printstr="playerName:"+playerNames[i]+" playerStartcash:"+str(line[1])
	if (category=="holdem" or category=="omahahi" or category=="omahahilo"):
		printstr+=" position:"+ful.position2String(line[2])+" cards:"
		if (category=="holdem"):
			printstr+=ful.cards2String(line[5:9])
		else:
			printstr+=ful.cards2String(line[5:13])
	elif (category=="razz" or category=="studhi" or category=="studhilo"):
		printstr+=" ante:"+str(line[4])+" cards:"
		printstr+=ful.cards2String(line[5:19])
	else:
		print "TODO: raise error, print_hand.py"
		sys.exit(1)
	printstr+=" winnings:"+str(line[19])+" rake:"+str(line[20])
	print printstr
	
	
print ""
print "From Table HandsActions"
print "======================="
for i in range (len(handsPlayers)):
	cursor.execute("""SELECT * FROM HandsActions WHERE handPlayerId=%s""",(handsPlayers[i][0], ))
	handsActions=cursor.fetchall()
	for j in range (len(handsActions)):
		line=handsActions[j][2:]
		printstr="playerName:"+playerNames[i]
		printstr+=" street:"+ful.street_int2String(category, line[0])+" streetActionNo:"+str(line[1])+" action:"+line[2]
		printstr+=" amount:"+str(line[4])
		print printstr
		
cursor.close()
db.close()
sys.exit(0)
