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

import sys
import MySQLdb

db = MySQLdb.connect("localhost", "fpdb", sys.argv[1], "fpdb")
cursor = db.cursor()
print "Connected to MySQL on localhost. Printing summary stats:"

cursor.execute("SELECT id FROM players")
print "Players:",cursor.rowcount
cursor.execute("SELECT id FROM autorates")
print "Autorates:",cursor.rowcount

cursor.execute("SELECT id FROM sites")
print "Sites:",cursor.rowcount
cursor.execute("SELECT id FROM gametypes")
print "Gametypes:",cursor.rowcount

cursor.execute("SELECT id FROM hands")
print "Total Hands:",cursor.rowcount
cursor.execute("SELECT hands.id FROM hands INNER JOIN gametypes ON hands.gametype_id = gametypes.id WHERE gametypes.type='ring'")
print "Hands, Ring:",cursor.rowcount
cursor.execute("SELECT hands.id FROM hands INNER JOIN gametypes ON hands.gametype_id = gametypes.id WHERE gametypes.type='stt'")
print "Hands, STT:",cursor.rowcount
cursor.execute("SELECT hands.id FROM hands INNER JOIN gametypes ON hands.gametype_id = gametypes.id WHERE gametypes.type='mtt'")
print "Hands, MTT:",cursor.rowcount

print ""
print "Hands per category and type"
cursor.execute("SELECT hands.id FROM hands INNER JOIN gametypes ON hands.gametype_id = gametypes.id WHERE gametypes.limit_type='cn'")
print "Hands, Cap No Limit:",cursor.rowcount
cursor.execute("SELECT hands.id FROM hands INNER JOIN gametypes ON hands.gametype_id = gametypes.id WHERE gametypes.limit_type='cp'")
print "Hands, Cap Pot Limit:",cursor.rowcount
cursor.execute("SELECT hands.id FROM hands INNER JOIN gametypes ON hands.gametype_id = gametypes.id WHERE gametypes.category='holdem' AND gametypes.limit_type='nl'")
print "Hands, Holdem No Limit:",cursor.rowcount
cursor.execute("SELECT hands.id FROM hands INNER JOIN gametypes ON hands.gametype_id = gametypes.id WHERE gametypes.category='holdem' AND gametypes.limit_type='pl'")
print "Hands, Holdem Pot Limit:",cursor.rowcount
cursor.execute("SELECT hands.id FROM hands INNER JOIN gametypes ON hands.gametype_id = gametypes.id WHERE gametypes.category='holdem' AND gametypes.limit_type='fl'")
print "Hands, Holdem Fixed Limit:",cursor.rowcount
cursor.execute("SELECT hands.id FROM hands INNER JOIN gametypes ON hands.gametype_id = gametypes.id WHERE gametypes.category='omahahi' AND gametypes.limit_type='nl'")
print "Hands, Omaha Hi No Limit:",cursor.rowcount
cursor.execute("SELECT hands.id FROM hands INNER JOIN gametypes ON hands.gametype_id = gametypes.id WHERE gametypes.category='omahahi' AND gametypes.limit_type='pl'")
print "Hands, Omaha Hi Pot Limit:",cursor.rowcount
cursor.execute("SELECT hands.id FROM hands INNER JOIN gametypes ON hands.gametype_id = gametypes.id WHERE gametypes.category='omahahi' AND gametypes.limit_type='fl'")
print "Hands, Omaha Hi Fixed Limit:",cursor.rowcount
cursor.execute("SELECT hands.id FROM hands INNER JOIN gametypes ON hands.gametype_id = gametypes.id WHERE gametypes.category='omahahilo' AND gametypes.limit_type='nl'")
print "Hands, Omaha Hi/Lo No Limit:",cursor.rowcount
cursor.execute("SELECT hands.id FROM hands INNER JOIN gametypes ON hands.gametype_id = gametypes.id WHERE gametypes.category='omahahilo' AND gametypes.limit_type='pl'")
print "Hands, Omaha Hi/Lo Pot Limit:",cursor.rowcount
cursor.execute("SELECT hands.id FROM hands INNER JOIN gametypes ON hands.gametype_id = gametypes.id WHERE gametypes.category='omahahilo' AND gametypes.limit_type='fl'")
print "Hands, Omaha Hi/Lo Fixed Limit:",cursor.rowcount
cursor.execute("SELECT hands.id FROM hands INNER JOIN gametypes ON hands.gametype_id = gametypes.id WHERE gametypes.category='razz'")
print "Hands, Razz:",cursor.rowcount
cursor.execute("SELECT hands.id FROM hands INNER JOIN gametypes ON hands.gametype_id = gametypes.id WHERE gametypes.category='studhi'")
print "Hands, Stud Hi:",cursor.rowcount
cursor.execute("SELECT hands.id FROM hands INNER JOIN gametypes ON hands.gametype_id = gametypes.id WHERE gametypes.category='studhilo'")
print "Hands, Stud Hi/Lo:",cursor.rowcount
print ""
cursor.execute("SELECT id FROM board_cards")
print "Board_cards:",cursor.rowcount
cursor.execute("SELECT id FROM hands_players")
print "Hands_players:",cursor.rowcount
cursor.execute("SELECT id FROM hands_actions")
print "Hands_actions:",cursor.rowcount

cursor.close()
db.close()
