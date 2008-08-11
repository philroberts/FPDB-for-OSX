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
import fpdb_simple

class fpdb_db:
	def __init__(self):
		"""Simple constructor, doesnt really do anything"""
		self.db=None
		self.cursor=None
		self.MYSQL_INNODB=2
		self.PGSQL=3
	#end def __init__
	
	def connect(self, backend, host, database, user, password):
		"""Connects a database with the given parameters"""
		self.backend=backend
		self.host=host
		self.database=database
		self.user=user
		self.password=password
		#print "fpdb_db.connect, database:",database
		if backend==self.MYSQL_INNODB:
			import MySQLdb
			self.db=MySQLdb.connect(host = host, user = user, passwd = password, db = database)
		elif backend==self.PGSQL:
			import pgdb
			self.db = pgdb.connect(dsn=host+":"+database, user='postgres', password=password)
		else:
			raise fpdb_simple.FpdbError("unrecognised database backend:"+backend)
		self.cursor=self.db.cursor()
		#try:
		#	self.cursor.execute("SELECT * FROM settings")
		#	settings=self.cursor.fetchone()
		#	if settings[0]!=21:
		#		print "outdated database version - please recreate tables"
		#except:# _mysql_exceptions.ProgrammingError:
		#	print "failed to read settings table - please recreate tables"
	#end def connect

	def create_table(self, string):
		"""creates a table for the given string
		The string should the name of the table followed by the column list
		in brackets as if it were an SQL command. Do NOT include the "CREATE TABLES"
		bit at the beginning nor the ";" or ENGINE= at the end"""
		string="CREATE TABLE "+string
		if (self.backend==self.MYSQL_INNODB):
			string+=" ENGINE=INNODB"
		string+=";"
		#print "create_table, string:", string
		self.cursor.execute(string)
		self.db.commit()
	#end def create_table

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
	#end def disconnect
	
	def drop_tables(self):
		"""Drops the fpdb tables from the current db"""
		self.cursor.execute("DROP TABLE IF EXISTS settings;")
		
		self.cursor.execute("DROP TABLE IF EXISTS HudDataHoldemOmaha;")
		self.cursor.execute("DROP TABLE IF EXISTS autorates;")
		self.cursor.execute("DROP TABLE IF EXISTS board_cards;")
		self.cursor.execute("DROP TABLE IF EXISTS hands_actions;")
		self.cursor.execute("DROP TABLE IF EXISTS hands_players;")
		self.cursor.execute("DROP TABLE IF EXISTS hands;")
		self.cursor.execute("DROP TABLE IF EXISTS tourneys_players;")
		self.cursor.execute("DROP TABLE IF EXISTS tourneys;")
		self.cursor.execute("DROP TABLE IF EXISTS players;")
		self.cursor.execute("DROP TABLE IF EXISTS gametypes;")
		self.cursor.execute("DROP TABLE IF EXISTS sites;")
		self.db.commit()
	#end def drop_tables
	
	def get_backend_name(self):
		"""Returns the name of the currently used backend"""
		if self.backend==1:
			return "MySQL normal"
		elif self.backend==2:
			return "MySQL InnoDB"
		elif self.backend==3:
			return "PostgreSQL"
	#end def get_backend_name
	
	def get_db_info(self):
		return (self.host, self.database, self.user, self.password)
	#end def get_db_info
	
	def recreate_tables(self):
		"""(Re-)creates the tables of the current DB"""
		self.drop_tables()
		
		self.create_table("""settings (
		version SMALLINT)""")
		
		self.create_table("""sites (
		id SMALLINT UNSIGNED UNIQUE AUTO_INCREMENT, PRIMARY KEY (id),
		name varchar(32),
		currency char(3))""")
		
		self.create_table("""gametypes (
		id SMALLINT UNSIGNED UNIQUE AUTO_INCREMENT, PRIMARY KEY (id),
		site_id SMALLINT UNSIGNED, FOREIGN KEY (site_id) REFERENCES sites(id),
		type char(4),
		category varchar(9),
		limit_type char(2),
		small_blind int,
		big_blind int,
		small_bet int,
		big_bet int)""")
		
		self.create_table("""players (
		id INT UNSIGNED UNIQUE AUTO_INCREMENT, PRIMARY KEY (id),
		name VARCHAR(32) CHARACTER SET utf8,
		site_id SMALLINT UNSIGNED, FOREIGN KEY (site_id) REFERENCES sites(id),
		comment text,
		comment_ts DATETIME)""")
		
		self.create_table("""autorates (
		id BIGINT UNSIGNED UNIQUE AUTO_INCREMENT, PRIMARY KEY (id),
		player_id INT UNSIGNED, FOREIGN KEY (player_id) REFERENCES players(id),
		gametype_id SMALLINT UNSIGNED, FOREIGN KEY (gametype_id) REFERENCES gametypes(id),
		description varchar(50),
		short_desc char(8),
		rating_time DATETIME,
		hand_count int)""")

		self.create_table("""hands (
		id BIGINT UNSIGNED UNIQUE AUTO_INCREMENT, PRIMARY KEY (id),
		site_hand_no bigint,
		gametype_id SMALLINT UNSIGNED, FOREIGN KEY (gametype_id) REFERENCES gametypes(id),
		hand_start DATETIME,
		seats smallint,
		comment text,
		comment_ts DATETIME)""")

		self.create_table("""board_cards (
		id BIGINT UNSIGNED UNIQUE AUTO_INCREMENT,
		PRIMARY KEY (id),
		hand_id BIGINT UNSIGNED,
		FOREIGN KEY (hand_id) REFERENCES hands(id),
		card1_value smallint,
		card1_suit char(1),
		card2_value smallint,
		card2_suit char(1),
		card3_value smallint,
		card3_suit char(1),
		card4_value smallint,
		card4_suit char(1),
		card5_value smallint,
		card5_suit char(1))""")

		self.create_table("""tourneys (
		id INT UNSIGNED UNIQUE AUTO_INCREMENT, PRIMARY KEY (id),
		site_id SMALLINT UNSIGNED, FOREIGN KEY (site_id) REFERENCES sites(id),
		site_tourney_no BIGINT,
		buyin INT,
		fee INT,
		knockout INT,
		entries INT,
		prizepool INT,
		start_time DATETIME,
		comment TEXT,
		comment_ts DATETIME)""")

		self.create_table("""tourneys_players (
		id BIGINT UNSIGNED UNIQUE AUTO_INCREMENT, PRIMARY KEY (id),
		tourney_id INT UNSIGNED, FOREIGN KEY (tourney_id) REFERENCES tourneys(id),
		player_id INT UNSIGNED, FOREIGN KEY (player_id) REFERENCES players(id),
		payin_amount INT,
		rank INT,
		winnings INT,
		comment TEXT,
		comment_ts DATETIME)""")

		self.create_table("""hands_players (
		id BIGINT UNSIGNED UNIQUE AUTO_INCREMENT,
		PRIMARY KEY (id),
		hand_id BIGINT UNSIGNED,
		FOREIGN KEY (hand_id) REFERENCES hands(id),
		player_id INT UNSIGNED,
		FOREIGN KEY (player_id) REFERENCES players(id),
		player_startcash int,
		position char(1),
		ante int,
	
		card1_value smallint,
		card1_suit char(1),
		card2_value smallint,
		card2_suit char(1),
		card3_value smallint,
		card3_suit char(1),
		card4_value smallint,
		card4_suit char(1),
		card5_value smallint,
		card5_suit char(1),
		card6_value smallint,
		card6_suit char(1),
		card7_value smallint,
		card7_suit char(1),
	
		winnings int,
		rake int,
		comment text,
		comment_ts DATETIME,
	
		tourneys_players_id BIGINT UNSIGNED,
		FOREIGN KEY (tourneys_players_id) REFERENCES tourneys_players(id))""")

		self.create_table("""hands_actions (
		id BIGINT UNSIGNED UNIQUE AUTO_INCREMENT,
		PRIMARY KEY (id),
		hand_player_id BIGINT UNSIGNED,
		FOREIGN KEY (hand_player_id) REFERENCES hands_players(id),
		street SMALLINT,
		action_no SMALLINT,
		action CHAR(5),
		amount INT,
		comment TEXT,
		comment_ts DATETIME)""")
		
		self.create_table("""HudDataHoldemOmaha (
		id BIGINT UNSIGNED UNIQUE AUTO_INCREMENT, PRIMARY KEY (id),
		gametypeId SMALLINT UNSIGNED, FOREIGN KEY (gametypeId) REFERENCES gametypes(id),
		playerId INT UNSIGNED, FOREIGN KEY (playerId) REFERENCES players(id),
		activeSeats SMALLINT,
		HDs INT,
		VPIP INT,
		PFR INT,
		PF3B4BChance INT,
		PF3B4B INT,
		sawFlop INT,
		sawTurn INT,
		sawRiver INT,
		sawShowdown INT,
		raisedFlop INT,
		raisedTurn INT,
		raisedRiver INT,
		otherRaisedFlop INT,
		otherRaisedFlopFold INT,
		otherRaisedTurn INT,
		otherRaisedTurnFold INT,
		otherRaisedRiver INT,
		otherRaisedRiverFold INT,
		wonWhenSeenFlop FLOAT,
		wonAtSD FLOAT,
		stealAttemptChance INT,
		stealAttempted INT,
		foldBbToStealChance INT,
		foldedBbToSteal INT,
		foldSbToStealChance INT,
		foldedSbToSteal INT)""")
		
		self.cursor.execute("INSERT INTO settings VALUES (21);")
		self.cursor.execute("INSERT INTO sites VALUES (DEFAULT, \"Full Tilt Poker\", 'USD');")
		self.cursor.execute("INSERT INTO sites VALUES (DEFAULT, \"PokerStars\", 'USD');")
		self.db.commit()
		print "finished recreating tables"
	#end def recreate_tables
#end class fpdb_db
