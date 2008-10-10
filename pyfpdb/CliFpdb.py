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

import os
import sys
import fpdb_simple
from optparse import OptionParser

try:
	import MySQLdb
except:
	diaSQLLibMissing = gtk.Dialog(title="Fatal Error - SQL interface library missing", parent=None, flags=0, buttons=(gtk.STOCK_QUIT,gtk.RESPONSE_OK))

	print "Please note that the CLI importer only works with MySQL, if you use PostgreSQL this error is expected."
	
import fpdb_import
import fpdb_db


#	def __init__(self, db, settings, debug=True):
#		"""Constructor for table_viewer"""
#		self.debug=debug
#		#print "start of table_viewer constructor"
#		self.db=db
#		self.cursor=db.cursor
#		self.settings=settings

if __name__ == "__main__":
	failOnError=False
	quiet=False

	#process CLI parameters
	parser = OptionParser()
	parser.add_option("-c", "--handCount", default="0", type="int",
					help="Number of hands to import (default 0 means unlimited)")
	parser.add_option("-d", "--database", default="fpdb", help="The MySQL database to use (default fpdb)")
	parser.add_option("-e", "--errorFile", default="failed.txt", 
					help="File to store failed hands into. (default: failed.txt) Not implemented.")
	parser.add_option("-f", "--inputFile", "--file", "--inputfile", default="stdin", 
					help="The file you want to import (remember to use quotes if necessary)")
	parser.add_option("-m", "--minPrint", "--status", default="50", type="int",
					help="How often to print a one-line status report (0 means never, default is 50)")
	parser.add_option("-p", "--password", help="The password for the MySQL user")
	parser.add_option("-q", "--quiet", action="store_true",
					help="If this is passed it doesn't print a total at the end nor the opening line. Note that this purposely does NOT change --minPrint")
	parser.add_option("-s", "--server", default="localhost",
					help="Hostname/IP of the MySQL server (default localhost)")
	parser.add_option("-u", "--user", default="fpdb", help="The MySQL username (default fpdb)")
	parser.add_option("-x", "--failOnError", action="store_true",
					help="If this option is passed it quits when it encounters any error")

	(options, sys.argv) = parser.parse_args()
	
	settings={'imp-callFpdbHud':False, 'db-backend':2}

	#self.inputFile=options.inputFile
		
	#self.server=options.server
	#self.database=options.database
	#self.user=options.user
	#self.password=options.password

	#self.quiet=False
	#self.failOnError=False
	#self.minPrint=0
	#self.handCount=0
	importer = fpdb_import.Importer()
		
	importer.import_file_dict(options, settings)
