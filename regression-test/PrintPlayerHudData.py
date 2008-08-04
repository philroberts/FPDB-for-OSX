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
parser.add_option("-b", "--bigblind", default="2", type="int", help="big blinds in cent")
parser.add_option("-c", "--cat", "--category", default="holdem", help="Category, e.g. holdem or studhilo")
parser.add_option("-e", "--seats", default="7", type="int", help="number of active seats")
parser.add_option("-g", "--gameType", default="ring", help="Whether its a ringgame (ring) or a tournament (tour)")
parser.add_option("-l", "--limit", "--limitType", default="fl", help="Limit Type, one of: nl, pl, fl, cn, cp")
parser.add_option("-n", "--name", "--playername", default="Player_1", help="Name of the player to print")
parser.add_option("-p", "--password", help="The password for the MySQL user")
parser.add_option("-s", "--site", default="PokerStars", help="Name of the site (as written in the history files)")

(options, sys.argv) = parser.parse_args()

db = MySQLdb.connect("localhost", "fpdb", options.password, "fpdb")
cursor = db.cursor()
print "Connected to MySQL on localhost. Print Player Flags Utility"

print ""
print "Basic Data"
print "=========="
print "bigblind:",options.bigblind, "category:",options.cat, "limitType:", options.limit, "name:", options.name, "gameType:", options.gameType, "site:", options.site

cursor.execute("SELECT id FROM sites WHERE name=%s", (options.site,))
siteId=cursor.fetchone()[0]

cursor.execute("SELECT id FROM gametypes WHERE big_blind=%s AND category=%s AND site_id=%s AND limit_type=%s AND type=%s", (options.bigblind, options.cat, siteId, options.limit, options.gameType))
gametypeId=cursor.fetchone()[0]

cursor.execute("SELECT id FROM players WHERE name=%s", (options.name,))
playerId=cursor.fetchone()[0]

cursor.execute("SELECT id FROM HudDataHoldemOmaha WHERE gametypeId=%s AND playerId=%s AND activeSeats=%s",(gametypeId, playerId, options.seats))
hudDataId=cursor.fetchone()[0]

print "siteId:", siteId, "gametypeId:", gametypeId, "playerId:", playerId, "hudDataId:", hudDataId

print ""
print "HUD Raw Hand Counts"
print "==================="

cursor.execute ("SELECT HDs, VPIP, PFR, PF3B4BChance, PF3B4B FROM HudDataHoldemOmaha WHERE id=%s", (hudDataId,))
fields=cursor.fetchone()
print "HDs:",fields[0]
print "VPIP:",fields[1]
print "PFR:",fields[2]
print "PF3B4BChance:",fields[3]
print "PF3B4B:",fields[4]
print ""

cursor.execute ("SELECT sawFlop, sawTurn, sawRiver, sawShowdown FROM HudDataHoldemOmaha WHERE id=%s", (hudDataId,))
fields=cursor.fetchone()
print "sawFlop:",fields[0]
print "sawTurn:",fields[1]
print "sawRiver:",fields[2]
print "sawShowdown:",fields[3]
print ""

cursor.execute ("SELECT raisedFlop, raisedTurn, raisedRiver FROM HudDataHoldemOmaha WHERE id=%s", (hudDataId,))
fields=cursor.fetchone()
print "raisedFlop:",fields[0]
print "raisedTurn:",fields[1]
print "raisedRiver:",fields[2]
print ""

cursor.execute ("SELECT otherRaisedFlop, otherRaisedFlopFold, otherRaisedTurn, otherRaisedTurnFold, otherRaisedRiver, otherRaisedRiverFold FROM HudDataHoldemOmaha WHERE id=%s", (hudDataId,))
fields=cursor.fetchone()
print "otherRaisedFlop:",fields[0]
print "otherRaisedFlopFold:",fields[1]
print "otherRaisedTurn:",fields[2]
print "otherRaisedTurnFold:",fields[3]
print "otherRaisedRiver:",fields[4]
print "otherRaisedRiverFold:",fields[5]


cursor.close()
db.close()
sys.exit(0)
