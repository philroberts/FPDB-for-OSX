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

import fpdb_db
import FpdbSQLQueries

import unittest

class TestSequenceFunctions(unittest.TestCase):

        def setUp(self):
                """Configure MySQL settings/database and establish connection"""
                self.mysql_settings={ 'db-host':"localhost", 'db-backend':2, 'db-databaseName':"fpdbtest", 'db-user':"fpdb", 'db-password':"fpdb"}
                self.mysql_db = fpdb_db.fpdb_db()
                self.mysql_db.connect(self.mysql_settings['db-backend'], self.mysql_settings['db-host'],
                                      self.mysql_settings['db-databaseName'], self.mysql_settings['db-user'],
                                      self.mysql_settings['db-password'])
                self.mysqldict = FpdbSQLQueries.FpdbSQLQueries('MySQL InnoDB')


	def testDatabaseConnection(self):
		"""Test all supported DBs"""
		result = self.mysql_db.cursor.execute("SHOW TABLES")
                self.failUnless(result==13, "Number of tables in database incorrect. Expected 13 got " + str(result))

if __name__ == '__main__':
        unittest.main()

