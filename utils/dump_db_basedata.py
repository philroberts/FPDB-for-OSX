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
print "Connected to MySQL on localhost. Printing dev-supplied base data:"

cursor.execute("SELECT * FROM sites")
print "Sites"
print "====="
print cursor.fetchall()

cursor.execute("SELECT * FROM gametypes")
print "Gametypes"
print "========="
result=cursor.fetchall()
for i in range (len(result)):
    print result[i]

cursor.close()
db.close()
