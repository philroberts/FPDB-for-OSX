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


############################################################################
#
#    File for Regression Testing fpdb
#

import os
import sys

import datetime
import Configuration
import fpdb_db
import fpdb_import
import fpdb_simple
import FpdbSQLQueries
import EverleafToFpdb
import Tables

import unittest

class TestSequenceFunctions(unittest.TestCase):

    def setUp(self):
        """Configure MySQL settings/database and establish connection"""
        self.c = Configuration.Config()
        self.mysql_settings={ 'db-host':"localhost", 
                    'db-backend':2, 
                    'db-databaseName':"fpdbtest", 
                    'db-user':"fpdb", 
                    'db-password':"fpdb"}
        self.mysql_db = fpdb_db.fpdb_db()
        self.mysql_db.connect(self.mysql_settings['db-backend'], self.mysql_settings['db-host'],
                    self.mysql_settings['db-databaseName'], self.mysql_settings['db-user'],
                    self.mysql_settings['db-password'])
        self.mysqldict = FpdbSQLQueries.FpdbSQLQueries('MySQL InnoDB')
        self.mysqlimporter = fpdb_import.Importer(self, self.mysql_settings, self.c)
        self.mysqlimporter.setCallHud(False)

        self.everleaf = EverleafToFpdb.Everleaf(self.c, "Nofile")

#        """Configure Postgres settings/database and establish connection"""
#        self.pg_settings={ 'db-host':"localhost", 'db-backend':3, 'db-databaseName':"fpdbtest", 'db-user':"fpdb", 'db-password':"fpdb"}
#        self.pg_db = fpdb_db.fpdb_db()
#        self.pg_db.connect(self.pg_settings['db-backend'], self.pg_settings['db-host'],
#                    self.pg_settings['db-databaseName'], self.pg_settings['db-user'],
#                    self.pg_settings['db-password'])
#        self.pgdict = FpdbSQLQueries.FpdbSQLQueries('PostgreSQL')


    def testDatabaseConnection(self):
        """Test all supported DBs"""
        self.result = self.mysql_db.cursor.execute(self.mysqldict.query['list_tables'])
        self.failUnless(self.result==13, "Number of tables in database incorrect. Expected 13 got " + str(self.result))

#        self.result = self.pg_db.cursor.execute(self.pgdict.query['list_tables'])
#        self.failUnless(self.result==13, "Number of tables in database incorrect. Expected 13 got " + str(self.result))

    def testMySQLRecreateTables(self):
        """Test droping then recreating fpdb table schema"""
        self.mysql_db.recreate_tables()
        self.result = self.mysql_db.cursor.execute("SHOW TABLES")
        self.failUnless(self.result==13, "Number of tables in database incorrect. Expected 13 got " + str(self.result))

    def testPokerStarsHHDate(self):
        latest = "PokerStars Game #21969660557:  Hold'em No Limit ($0.50/$1.00) - 2008/11/12 10:00:48 CET [2008/11/12 4:00:48 ET]"
        previous = "PokerStars Game #21969660557:  Hold'em No Limit ($0.50/$1.00) - 2008/08/17 - 01:14:43 (ET)"
        older1 = "PokerStars Game #21969660557:  Hold'em No Limit ($0.50/$1.00) - 2008/09/07 06:23:14 ET"

        result = fpdb_simple.parseHandStartTime(older1, "ps")
        self.failUnless(result==datetime.datetime(2008,9,7,11,23,14),
                        "Date incorrect, expected: 2008-09-07 11:23:14 got: " + str(result))
        result = fpdb_simple.parseHandStartTime(latest, "ps")
        self.failUnless(result==datetime.datetime(2008,11,12,15,00,48), 
                        "Date incorrect, expected: 2008-11-12 15:00:48 got: " + str(result))
        result = fpdb_simple.parseHandStartTime(previous, "ps")
        self.failUnless(result==datetime.datetime(2008,8,17,6,14,43),
                        "Date incorrect, expected: 2008-08-17 01:14:43 got: " + str(result))

    def testFullTiltHHDate(self):
        sitngo1 = "Full Tilt Poker Game #10311865543: $1 + $0.25 Sit & Go (78057629), Table 1 - 25/50 - No Limit Hold'em - 0:07:45 ET - 2009/01/29"
        cash1 = "Full Tilt Poker Game #9403951181: Table CR - tay - $0.05/$0.10 - No Limit Hold'em - 9:40:20 ET - 2008/12/09"
        cash2 = "Full Tilt Poker Game #9468383505: Table Bike (deep 6) - $0.05/$0.10 - No Limit Hold'em - 5:09:36 ET - 2008/12/13"

        result = fpdb_simple.parseHandStartTime(sitngo1,"ftp")
        self.failUnless(result==datetime.datetime(2009,1,29,05,07,45),
                        "Date incorrect, expected: 2009-01-29 05:07:45 got: " + str(result))
        result = fpdb_simple.parseHandStartTime(cash1,"ftp")
        self.failUnless(result==datetime.datetime(2008,12,9,14,40,20),
                        "Date incorrect, expected: 2008-12-09 14:40:20 got: " + str(result))
        result = fpdb_simple.parseHandStartTime(cash2,"ftp")
        self.failUnless(result==datetime.datetime(2008,12,13,10,9,36),
                        "Date incorrect, expected: 2008-12-13 10:09:36 got: " + str(result))

    def testTableDetection(self):
        result = Tables.clean_title("French (deep)")
        self.failUnless(result == "French", "French (deep) parsed incorrectly. Expected 'French' got: " + str(result))
#        result = ("French (deep) - $0.25/$0.50 - No Limit Hold'em - Logged In As xxxx")

    def testEverleafGameInfoRegex(self):
        cash_nlhe = """Everleaf Gaming Game #55198191
***** Hand history for game #55198191 *****
Blinds $0.50/$1 NL Hold'em - 2008/09/01 - 10:02:11
Table Speed Kuala
Seat 8 is the button
Total number of players: 10"""
        cash_plo = """Everleaf Gaming Game #65295370
***** Hand history for game #65295370 *****
Blinds $0.50/$1 PL Omaha - 2008/12/07 - 21:59:48
Table Guanajuato
Seat 5 is the button
Total number of players: 6"""
        cash_flhe = """Everleaf Gaming Game #55809022
***** Hand history for game #55809022 *****
$1/$2 Hold'em - 2008/09/07 - 08:04:36
Table Jeonju
Seat 4 is the button
Total number of players: 5
"""
        #NLHE
        m = self.everleaf.re_GameInfo.search(cash_nlhe)
        sb = m.group('SB')
        bb = m.group('BB')
        ltype = m.group('LTYPE')
        game = m.group('GAME')

        self.failUnless(sb == "0.50", "SB incorrect, expected: 0.50 got: '" + sb + "'")
        self.failUnless(bb == "1", "BB incorrect, expected: 1 got: '" + bb + "'")
        self.failUnless(ltype == "NL", "LTYPE incorrect, expected: NL got: '" + ltype + "'")
        self.failUnless(game == "Hold\'em", "GAME incorrect, expected: Hold\'em got: '" + game + "'")

        #FLHE
        m = self.everleaf.re_GameInfo.search(cash_flhe)
        sb = m.group('SB')
        bb = m.group('BB')
        ltype = m.group('LTYPE')
        game = m.group('GAME')
        print m.groups()

        self.failUnless(sb == "1", "SB incorrect, expected: 1 got: '" + sb + "'")
        self.failUnless(bb == "2", "BB incorrect, expected: 2 got: '" + bb + "'")
        self.failUnless(ltype == None, "LTYPE incorrect, expected: NL got: '%s'" %(ltype))
        self.failUnless(game == "Hold\'em", "GAME incorrect, expected: Hold\'em got: '" + game + "'")

#    def testImportHandHistoryFiles(self):
#        """Test import of single HH file"""
#        self.mysqlimporter.addImportFile("regression-test-files/hand-histories/ps-lhe-ring-3hands.txt")
#        self.mysqlimporter.runImport()
#        self.mysqlimporter.addImportDirectory("regression-test-files/hand-histories")
#        self.mysqlimporter.runImport()

#    def testPostgresSQLRecreateTables(self):
#        """Test droping then recreating fpdb table schema"""
#        self.pg_db.recreate_tables()
#        self.result = self.pg_db.cursor.execute(self.pgdict.query['list_tables'])
#        self.failUnless(self.result==13, "Number of tables in database incorrect. Expected 13 got " + str(self.result))

if __name__ == '__main__':
        unittest.main()

