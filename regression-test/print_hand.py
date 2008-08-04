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

#This is intended mostly for regression testing

import sys
import MySQLdb
from optparse import OptionParser
import fpdb_util_lib as ful

parser = OptionParser()
parser.add_option("-n", "--hand_number", "--hand", type="int",
				help="Number of the hand to print")
parser.add_option("-p", "--password", help="The password for the MySQL user")
parser.add_option("-s", "--site", default="PokerStars",
				help="Name of the site (as written in the history files)")

(options, sys.argv) = parser.parse_args()

if options.hand_number==None or options.site==None:
	print "please supply a hand number and site name. TODO: make this work"

db = MySQLdb.connect("localhost", "fpdb", options.password, "fpdb")
cursor = db.cursor()
print "Connected to MySQL on localhost. Print Hand Utility"

cursor.execute("SELECT id FROM sites WHERE name=%s", (options.site,))
site_id=cursor.fetchone()[0]
print "options.site:",options.site,"site_id:",site_id

cursor.execute("""SELECT hands.* FROM hands INNER JOIN gametypes
ON hands.gametype_id = gametypes.id WHERE gametypes.site_id=%s AND hands.site_hand_no=%s""",
(site_id, options.hand_number))
hands_result=cursor.fetchone()
gametype_id=hands_result[2]
site_hand_no=options.hand_number
hand_id=hands_result[0]
hand_start=hands_result[3]
seat_count=hands_result[4]


print ""
print "From Table gametypes"
print "===================="

cursor.execute("""SELECT type, category, limit_type FROM gametypes WHERE id=%s""",
			   (gametype_id, ))
type_etc=cursor.fetchone()
type=type_etc[0]
category=type_etc[1]
limit_type=type_etc[2]
print "type:", type, "  category:", category, "  limit_type:", limit_type

gt_string=""
do_bets=False
if (category=="holdem" or category=="omahahi" or category=="omahahilo"):
	cursor.execute("SELECT small_blind FROM gametypes WHERE id=%s", (gametype_id, ))
	sb=cursor.fetchone()[0]
	cursor.execute("SELECT big_blind FROM gametypes WHERE id=%s", (gametype_id, ))
	bb=cursor.fetchone()[0]
	gt_string=("sb: "+str(sb)+"   bb: "+str(bb))
	if (limit_type=="fl"):
		do_bets=True
elif (category=="razz" or category=="studhi" or category=="studhilo"):
	do_bets=True
	
if do_bets:
	cursor.execute("SELECT small_bet FROM gametypes WHERE id=%s", (gametype_id, ))
	sbet=cursor.fetchone()[0]
	cursor.execute("SELECT big_bet FROM gametypes WHERE id=%s", (gametype_id, ))
	bbet=cursor.fetchone()[0]
	gt_string+=("   sbet: "+str(sbet)+"   bbet: "+str(bbet))
print gt_string

if type=="ring":
	pass
elif type=="tour":
	#cursor.execute("SELECT tourneys_players_id FROM hands
	cursor.execute("""SELECT DISTINCT tourneys_players.id
	FROM hands JOIN hands_players ON hands_players.hand_id=hands.id
	JOIN tourneys_players ON hands_players.tourneys_players_id=tourneys_players.id
	WHERE hands.id=%s""", (hand_id,))
	hands_players_ids=cursor.fetchall()
	print "dbg hands_players_ids:",hands_players_ids
	
	print ""
	print "From Table tourneys"
	print "==================="
	print "TODO"
	
	
	print ""
	print "From Table tourneys_players"
	print "==========================="
	print "TODO"
else:
	print "invalid type:",type
	sys.exit(1)


print ""
print "From Table hands"
print "================"

print "site_hand_no:",site_hand_no,"hand_start:",hand_start,"seat_count:",seat_count
#,"hand_id:",hand_id,"gametype_id:",gametype_id

if (category=="holdem" or category=="omahahi" or category=="omahahilo"):
	cursor.execute("""SELECT * FROM board_cards WHERE hand_id=%s""",(hand_id, ))
	bc=cursor.fetchone()
	print "Board cards:", ful.cards2String(bc[2:])


print ""
print "From Table hands_players"
print "========================"
cursor.execute("""SELECT * FROM hands_players WHERE hand_id=%s""",(hand_id, ))
hands_players=cursor.fetchall()
player_names=[]
for i in range (len(hands_players)):
	line=hands_players[i][2:]
	player_names.append(ful.id_to_player_name(cursor, line[0]))
	printstr="player_name:"+player_names[i]+" player_startcash:"+str(line[1])
	if (category=="holdem" or category=="omahahi" or category=="omahahilo"):
		printstr+=" position:"+ful.position2String(line[2])+" cards:"
		if (category=="holdem"):
			printstr+=ful.cards2String(line[4:8])
		else:
			printstr+=ful.cards2String(line[4:12])
	elif (category=="razz" or category=="studhi" or category=="studhilo"):
		printstr+=" ante:"+str(line[3])+" cards:"
		printstr+=ful.cards2String(line[4:18])
	else:
		print "TODO: raise error, print_hand.py"
		sys.exit(1)
	printstr+=" winnings:"+str(line[18])+" rake:"+str(line[19])
	print printstr
	
	
print ""
print "From Table hands_actions"
print "========================"
for i in range (len(hands_players)):
	cursor.execute("""SELECT * FROM hands_actions WHERE hand_player_id=%s""",(hands_players[i][0], ))
	hands_actions=cursor.fetchall()
	for j in range (len(hands_actions)):
		line=hands_actions[j][2:]
		printstr="player_name:"+player_names[i]+" actionCount:"+str(j)
		printstr+=" street:"+ful.street_int2String(category, line[0])+" streetActionNo:"+str(line[1])+" action:"+line[2]
		printstr+=" amount:"+str(line[3])
		print printstr
		
cursor.close()
db.close()
sys.exit(0)
