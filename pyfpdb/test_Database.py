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

import sqlite3
import Database
import math

# Should probably use our wrapper classes - creating sqlite db in memory
sqlite3.register_converter("bool", lambda x: bool(int(x)))
sqlite3.register_adapter(bool, lambda x: "1" if x else "0")

con = sqlite3.connect(":memory:")
con.isolation_level = None

#Floor function
con.create_function("floor", 1, math.floor)

#Mod function
tmp = Database.sqlitemath()
con.create_function("mod", 2, tmp.mod)

# Aggregate function VARIANCE()
con.create_aggregate("variance", 1, Database.VARIANCE)


cur = con.cursor()

def testSQLiteVarianceFunction():
    cur.execute("CREATE TABLE test(i)")
    cur.execute("INSERT INTO test(i) values (1)")
    cur.execute("INSERT INTO test(i) values (2)")
    cur.execute("INSERT INTO test(i) values (3)")
    cur.execute("SELECT variance(i) from test")
    result = cur.fetchone()[0]

    print ("DEBUG: Testing variance function")
    print ("DEBUG: result: %s expecting: 0.666666 (result-expecting ~= 0.0): %s" % (result, (result - 0.66666)))
    cur.execute("DROP TABLE test")
    assert (result - 0.66666) <= 0.0001

def testSQLiteFloorFunction():
    vars    = [0.1, 1.5, 2.6, 3.5, 4.9]
    cur.execute("CREATE TABLE test(i float)")
    for var in vars:
        cur.execute("INSERT INTO test(i) values(%f)" % var)
    cur.execute("SELECT floor(i) from test")
    result = cur.fetchall()
    print "DEBUG: result: %s" % result
    answer = 0
    for i in result:
        print "DEBUG: int(var): %s" % int(i[0])
        assert answer == int(i[0])
        answer = answer + 1
    cur.execute("DROP TABLE test")

def testSQLiteModFunction():
    vars    = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16 ,17, 18]
    cur.execute("CREATE TABLE test(i int)")
    for var in vars:
        cur.execute("INSERT INTO test(i) values(%i)" % var)
    cur.execute("SELECT mod(i,13) from test")
    result = cur.fetchall()
    idx = 0
    for i in result:
        print "DEBUG: int(var): %s" % i[0]
        assert vars[idx]%13 == int(i[0])
        idx = idx+1

    cur.execute("DROP TABLE test")
