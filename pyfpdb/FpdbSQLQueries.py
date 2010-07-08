#!/usr/bin/python
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

############################################################################
#
#    File for DB queries used in fpdb
#

import sys
import os

class FpdbSQLQueries:

    def __init__(self, db):
        self.query = {}
        self.dbname = db


        if(self.dbname == 'MySQL InnoDB' or self.dbname == 'PostgreSQL'):
            self.query['set tx level'] = """SET SESSION TRANSACTION
            ISOLATION LEVEL READ COMMITTED"""
        elif(self.dbname == 'SQLite'):
            self.query['set tx level'] = """ """


        if(self.dbname == 'MySQL InnoDB') or (self.dbname == 'PostgreSQL'):
            self.query['getSiteId'] = """SELECT id from Sites where name = %s"""
        elif(self.dbname == 'SQLite'):
            self.query['getSiteId'] = """SELECT id from Sites where name = %s"""

        if(self.dbname == 'MySQL InnoDB') or (self.dbname == 'PostgreSQL')  or (self.dbname == 'SQLite'):
            self.query['getGames'] = """SELECT DISTINCT category from Gametypes"""
        
        if(self.dbname == 'MySQL InnoDB') or (self.dbname == 'PostgreSQL')  or (self.dbname == 'SQLite'):
            self.query['getLimits'] = """SELECT DISTINCT bigBlind from Gametypes ORDER by bigBlind DESC"""


if __name__== "__main__":
        from optparse import OptionParser

        print "FpdbSQLQueries starting from CLI"

        #process CLI parameters
        usage = "usage: %prog [options]"
        parser = OptionParser()
        parser.add_option("-t", "--type", dest="dbtype", help="Available 'MySQL InnoDB', 'PostgreSQL', 'SQLite'(default: MySQL InnoDB)", default="MySQL InnoDB")
        parser.add_option("-s", "--show", action="store_true", dest="showsql", help="Show full SQL output")
        parser.add_option("-v", "--verbose", action="store_true", dest="verbose")


        (options, args) = parser.parse_args()

        if options.verbose:
                print """No additional output available in this file"""

        obj = FpdbSQLQueries(options.dbtype)

        print "Available Queries for '" + options.dbtype + "':"

        for key in obj.query:
                print "    " + key
                if options.showsql:
                        print obj.query[key]
