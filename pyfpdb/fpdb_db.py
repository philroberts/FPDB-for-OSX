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
import re
import fpdb_simple
import FpdbSQLQueries

class fpdb_db:
	def __init__(self):
		"""Simple constructor, doesnt really do anything"""
		self.db=None
		self.cursor=None
		self.sql = {}
		self.MYSQL_INNODB=2
		self.PGSQL=3
		self.SQLITE=4
	#end def __init__
	
	def connect(self, backend, host, database, user, password):
		"""Connects a database with the given parameters"""
		self.backend=backend
		self.host=host
		self.database=database
		self.user=user
		self.password=password
		if backend==self.MYSQL_INNODB:
			import MySQLdb
			self.db=MySQLdb.connect(host = host, user = user, passwd = password, db = database)
		elif backend==self.PGSQL:
			import psycopg2
			self.db = psycopg2.connect(host = host, user = user, password = password, database = database)
		else:
			raise fpdb_simple.FpdbError("unrecognised database backend:"+backend)
		self.cursor=self.db.cursor()
		# Set up query dictionary as early in the connection process as we can.
                self.sql = FpdbSQLQueries.FpdbSQLQueries(self.get_backend_name())
		self.wrongDbVersion=False
		try:
			self.cursor.execute("SELECT * FROM Settings")
			settings=self.cursor.fetchone()
			if settings[0]!=118:
				print "outdated or too new database version - please recreate tables"
				self.wrongDbVersion=True
		except:# _mysql_exceptions.ProgrammingError:
			print "failed to read settings table - please recreate tables"
			self.wrongDbVersion=True
	#end def connect

	def disconnect(self, due_to_error=False):
		"""Disconnects the DB"""
		if due_to_error:
			self.db.rollback()
		else:
			self.db.commit()
		self.cursor.close()
		self.db.close()
	#end def disconnect
	
	def reconnect(self, due_to_error=False):
		"""Reconnects the DB"""
		#print "started fpdb_db.reconnect"
		self.disconnect(due_to_error)
		self.connect(self.backend, self.host, self.database, self.user, self.password)

	def create_tables(self):
		#todo: should detect and fail gracefully if tables already exist.
		self.cursor.execute(self.sql.query['createSettingsTable'])
                self.cursor.execute(self.sql.query['createSitesTable'])
                self.cursor.execute(self.sql.query['createGametypesTable'])
                self.cursor.execute(self.sql.query['createPlayersTable'])
                self.cursor.execute(self.sql.query['createAutoratesTable'])
                self.cursor.execute(self.sql.query['createHandsTable'])
                self.cursor.execute(self.sql.query['createBoardCardsTable'])
                self.cursor.execute(self.sql.query['createTourneyTypesTable'])
                self.cursor.execute(self.sql.query['createTourneysTable'])
                self.cursor.execute(self.sql.query['createTourneysPlayersTable'])
                self.cursor.execute(self.sql.query['createHandsPlayersTable'])
                self.cursor.execute(self.sql.query['createHandsActionsTable'])
                self.cursor.execute(self.sql.query['createHudCacheTable'])
		self.fillDefaultData()
                self.db.commit()
#end def disconnect
	
	def drop_tables(self):
		"""Drops the fpdb tables from the current db"""

		if(self.get_backend_name() == 'MySQL InnoDB'):
			#Databases with FOREIGN KEY support need this switched of before you can drop tables
                	self.drop_referencial_integrity()

			# Query the DB to see what tables exist
			self.cursor.execute(self.sql.query['list_tables'])
	                for table in self.cursor:
                	        self.cursor.execute(self.sql.query['drop_table'] + table[0])
		elif(self.get_backend_name() == 'PostgreSQL'):
			self.db.commit()# I have no idea why this makes the query work--REB 07OCT2008
			self.cursor.execute(self.sql.query['list_tables'])
			tables = self.cursor.fetchall()
	                for table in tables:
                	        self.cursor.execute(self.sql.query['drop_table'] + table[0] + ' cascade') 
		elif(self.get_backend_name() == 'SQLite'):
			#todo: sqlite version here
			print "Empty function here"

                self.db.commit()
	#end def drop_tables

	def drop_referencial_integrity(self):
		"""Update all tables to remove foreign keys"""

		self.cursor.execute(self.sql.query['list_tables'])
		result = self.cursor.fetchall()

		for i in range(len(result)):
			self.cursor.execute("SHOW CREATE TABLE " + result[i][0])
			inner = self.cursor.fetchall()

			for j in range(len(inner)):
			# result[i][0] - Table name
			# result[i][1] - CREATE TABLE parameters
			#Searching for CONSTRAINT `tablename_ibfk_1`
				for m in re.finditer('(ibfk_[0-9]+)', inner[j][1]):
					key = "`" + inner[j][0] + "_" + m.group() + "`"
					self.cursor.execute("ALTER TABLE " + inner[j][0] + " DROP FOREIGN KEY " + key)
                self.db.commit()
        #end drop_referencial_inegrity
	
	def get_backend_name(self):
		"""Returns the name of the currently used backend"""
		if self.backend==2:
			return "MySQL InnoDB"
		elif self.backend==3:
			return "PostgreSQL"
		else:
			raise fpdb_simple.FpdbError("invalid backend")
	#end def get_backend_name
	
	def get_db_info(self):
		return (self.host, self.database, self.user, self.password)
	#end def get_db_info
	
	def fillDefaultData(self):
		self.cursor.execute("INSERT INTO Settings VALUES (118);")
		self.cursor.execute("INSERT INTO Sites VALUES (DEFAULT, 'Full Tilt Poker', 'USD');")
		self.cursor.execute("INSERT INTO Sites VALUES (DEFAULT, 'PokerStars', 'USD');")
		self.cursor.execute("INSERT INTO TourneyTypes VALUES (DEFAULT, 1, 0, 0, 0, False);")
	#end def fillDefaultData
	
	def recreate_tables(self):
		"""(Re-)creates the tables of the current DB"""
		
		self.drop_tables()
		self.create_tables()
		self.db.commit()
		print "Finished recreating tables"
	#end def recreate_tables
#end class fpdb_db
