#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Copyright 2008-2010 Steffen Schaumburg
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
parser.add_option("-b", "--bigBet", default="4", type="int", help="big bet in cent")
parser.add_option("-c", "--cat", "--category", default="holdem", help="Category, e.g. holdem or studhilo")
parser.add_option("-e", "--seats", default="7", type="int", help="number of active seats")
parser.add_option("-g", "--gameType", default="ring", help="Whether its a ringgame (ring) or a tournament (tour)")
parser.add_option("-l", "--limit", "--limitType", default="fl", help="Limit Type, one of: nl, pl, fl, cn, cp")
parser.add_option("-n", "--name", "--playername", default="Player_1", help="Name of the player to print")
parser.add_option("-o", "--position", default="B", help="Position, can be B, S, D, C, M or E (see tabledesign.html)")
parser.add_option("-p", "--password", help="The password for the MySQL user")
parser.add_option("-s", "--site", default="PokerStars", help="Name of the site (as written in the history files)")

(options, sys.argv) = parser.parse_args()

db = MySQLdb.connect("localhost", "fpdb", options.password, "fpdb")
cursor = db.cursor()
print "Connected to MySQL on localhost. Print Player Flags Utility"

print ""
print "Basic Data"
print "=========="
print "bigBet:",options.bigBet, "category:",options.cat, "limitType:", options.limit, "name:", options.name, "gameType:", options.gameType, "site:", options.site

cursor.execute("SELECT id FROM Sites WHERE name=%s", (options.site,))
siteId=cursor.fetchone()[0]

cursor.execute("SELECT id FROM Gametypes WHERE bigBet=%s AND category=%s AND siteId=%s AND limitType=%s AND type=%s", (options.bigBet, options.cat, siteId, options.limit, options.gameType))
gametypeId=cursor.fetchone()[0]

cursor.execute("SELECT id FROM Players WHERE name=%s", (options.name,))
playerId=cursor.fetchone()[0]

#print "debug: gametypeId:", gametypeId, "playerId:", playerId, "options.seats:", options.seats, "options.position:", options.position
cursor.execute("SELECT id FROM HudCache WHERE gametypeId=%s AND playerId=%s AND activeSeats=%s AND position=%s",(gametypeId, playerId, options.seats, options.position))
hudDataId=cursor.fetchone()[0]

print "siteId:", siteId, "gametypeId:", gametypeId, "playerId:", playerId, "hudDataId:", hudDataId

print ""
print "HUD Raw Hand Counts"
print "==================="

cursor.execute ("SELECT HDs, street0VPI, street0Aggr, street0_3B4BChance, street0_3B4BDone FROM HudCache WHERE id=%s", (hudDataId,))
fields=cursor.fetchone()
print "HDs:",fields[0]
print "street0VPI:",fields[1]
print "street0Aggr:",fields[2]
print "street0_3B4BChance:",fields[3]
print "street0_3B4BDone:",fields[4]
print ""

cursor.execute ("SELECT street1Seen, street2Seen, street3Seen, street4Seen, sawShowdown FROM HudCache WHERE id=%s", (hudDataId,))
fields=cursor.fetchone()
print "street1Seen:",fields[0]
print "street2Seen:",fields[1]
print "street3Seen:",fields[2]
print "street4Seen:",fields[3]
print "sawShowdown:",fields[4]
print ""

cursor.execute ("SELECT street1Aggr, street2Aggr, street3Aggr, street4Aggr FROM HudCache WHERE id=%s", (hudDataId,))
fields=cursor.fetchone()
print "street1Aggr:",fields[0]
print "street2Aggr:",fields[1]
print "street3Aggr:",fields[2]
print "street4Aggr:",fields[3]
print ""

cursor.execute ("SELECT otherRaisedStreet1, otherRaisedStreet2, otherRaisedStreet3, otherRaisedStreet4, foldToOtherRaisedStreet1, foldToOtherRaisedStreet2, foldToOtherRaisedStreet3, foldToOtherRaisedStreet4 FROM HudCache WHERE id=%s", (hudDataId,))
fields=cursor.fetchone()
print "otherRaisedStreet1:",fields[0]
print "otherRaisedStreet2:",fields[1]
print "otherRaisedStreet3:",fields[2]
print "otherRaisedStreet4:",fields[3]
print "foldToOtherRaisedStreet1:",fields[4]
print "foldToOtherRaisedStreet2:",fields[5]
print "foldToOtherRaisedStreet3:",fields[6]
print "foldToOtherRaisedStreet4:",fields[7]
print ""

cursor.execute ("SELECT wonWhenSeenStreet1, wonAtSD FROM HudCache WHERE id=%s", (hudDataId,))
fields=cursor.fetchone()
print "wonWhenSeenStreet1:",fields[0]
print "wonAtSD:",fields[1]

cursor.execute ("SELECT stealAttemptChance, stealAttempted, foldBbToStealChance, foldedBbToSteal, foldSbToStealChance, foldedSbToSteal FROM HudCache WHERE id=%s", (hudDataId,))
fields=cursor.fetchone()
print "stealAttemptChance:",fields[0]
print "stealAttempted:",fields[1]
print "foldBbToStealChance:",fields[2]
print "foldedBbToSteal:",fields[3]
print "foldSbToStealChance:",fields[4]
print "foldedSbToSteal:",fields[5]

cursor.execute ("SELECT street1CBChance, street1CBDone, street2CBChance, street2CBDone, street3CBChance, street3CBDone, street4CBChance, street4CBDone FROM HudCache WHERE id=%s", (hudDataId,))
fields=cursor.fetchone()
print "street1CBChance:",fields[0]
print "street1CBDone:",fields[1]
print "street2CBChance:",fields[2]
print "street2CBDone:",fields[3]
print "street3CBChance:",fields[4]
print "street3CBDone:",fields[5]
print "street4CBChance:",fields[6]
print "street4CBDone:",fields[7]

cursor.execute ("SELECT foldToStreet1CBChance, foldToStreet1CBDone, foldToStreet2CBChance, foldToStreet2CBDone, foldToStreet3CBChance, foldToStreet3CBDone, foldToStreet4CBChance, foldToStreet4CBDone FROM HudCache WHERE id=%s", (hudDataId,))
fields=cursor.fetchone()
print "foldToStreet1CBChance:",fields[0]
print "foldToStreet1CBDone:",fields[1]
print "foldToStreet2CBChance:",fields[2]
print "foldToStreet2CBDone:",fields[3]
print "foldToStreet3CBChance:",fields[4]
print "foldToStreet3CBDone:",fields[5]
print "foldToStreet4CBChance:",fields[6]
print "foldToStreet4CBDone:",fields[7]

cursor.execute ("SELECT totalProfit FROM HudCache WHERE id=%s", (hudDataId,))
fields=cursor.fetchone()
print "totalProfit:",fields[0]

cursor.execute ("SELECT street1CheckCallRaiseChance, street1CheckCallRaiseDone, street2CheckCallRaiseChance, street2CheckCallRaiseDone, street3CheckCallRaiseChance, street3CheckCallRaiseDone, street4CheckCallRaiseChance, street4CheckCallRaiseDone FROM HudCache WHERE id=%s", (hudDataId,))
fields=cursor.fetchone()
print "street1CheckCallRaiseChance:",fields[0]
print "street1CheckCallRaiseDone:",fields[1]
print "street2CheckCallRaiseChance:",fields[2]
print "street2CheckCallRaiseDone:",fields[3]
print "street3CheckCallRaiseChance:",fields[4]
print "street3CheckCallRaiseDone:",fields[5]
print "street4CheckCallRaiseChance:",fields[6]
print "street4CheckCallRaiseDone:",fields[7]


cursor.close()
db.close()
sys.exit(0)
