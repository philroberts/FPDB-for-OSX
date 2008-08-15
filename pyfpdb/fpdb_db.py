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
		try:
			self.cursor.execute("SELECT * FROM Settings")
			settings=self.cursor.fetchone()
			if settings[0]!=35:
				print "outdated database version - please recreate tables"
		except:# _mysql_exceptions.ProgrammingError:
			print "failed to read settings table - please recreate tables"
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
		#todo: run the below if current db is git34 or lower
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

		self.cursor.execute("DROP TABLE IF EXISTS Settings;")
		self.cursor.execute("DROP TABLE IF EXISTS HudDataHoldemOmaha;")
		self.cursor.execute("DROP TABLE IF EXISTS Autorates;")
		self.cursor.execute("DROP TABLE IF EXISTS BoardCards;")
		self.cursor.execute("DROP TABLE IF EXISTS HandsActions;")
		self.cursor.execute("DROP TABLE IF EXISTS HandsPlayers;")
		self.cursor.execute("DROP TABLE IF EXISTS Hands;")
		self.cursor.execute("DROP TABLE IF EXISTS TourneysPlayers;")
		self.cursor.execute("DROP TABLE IF EXISTS Tourneys;")
		self.cursor.execute("DROP TABLE IF EXISTS Players;")
		self.cursor.execute("DROP TABLE IF EXISTS Gametypes;")
		self.cursor.execute("DROP TABLE IF EXISTS Sites;")
		self.db.commit()
	#end def drop_tables
	
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
	
	def recreate_tables(self):
		"""(Re-)creates the tables of the current DB"""
		self.drop_tables()
		
		self.create_table("""Settings (
		version SMALLINT)""")
		
		self.create_table("""Sites (
		id SMALLINT UNSIGNED UNIQUE AUTO_INCREMENT, PRIMARY KEY (id),
		name varchar(32),
		currency char(3))""")
		
		self.create_table("""Gametypes (
		id SMALLINT UNSIGNED UNIQUE AUTO_INCREMENT, PRIMARY KEY (id),
		siteId SMALLINT UNSIGNED, FOREIGN KEY (siteId) REFERENCES Sites(id),
		type char(4),
		category varchar(9),
		limitType char(2),
		smallBlind int,
		bigBlind int,
		smallBet int,
		bigBet int)""")
		
		self.create_table("""Players (
		id INT UNSIGNED UNIQUE AUTO_INCREMENT, PRIMARY KEY (id),
		name VARCHAR(32) CHARACTER SET utf8,
		siteId SMALLINT UNSIGNED, FOREIGN KEY (siteId) REFERENCES Sites(id),
		comment text,
		commentTs DATETIME)""")
		
		self.create_table("""Autorates (
		id BIGINT UNSIGNED UNIQUE AUTO_INCREMENT, PRIMARY KEY (id),
		playerId INT UNSIGNED, FOREIGN KEY (playerId) REFERENCES Players(id),
		gametypeId SMALLINT UNSIGNED, FOREIGN KEY (gametypeId) REFERENCES Gametypes(id),
		description varchar(50),
		shortDesc char(8),
		ratingTime DATETIME,
		handCount int)""")

		self.create_table("""Hands (
		id BIGINT UNSIGNED UNIQUE AUTO_INCREMENT, PRIMARY KEY (id),
		siteHandNo bigint,
		gametypeId SMALLINT UNSIGNED, FOREIGN KEY (gametypeId) REFERENCES Gametypes(id),
		handStart DATETIME,
		seats smallint,
		comment text,
		commentTs DATETIME)""")

		self.create_table("""BoardCards (
		id BIGINT UNSIGNED UNIQUE AUTO_INCREMENT, PRIMARY KEY (id),
		handId BIGINT UNSIGNED, FOREIGN KEY (handId) REFERENCES Hands(id),
		card1Value smallint,
		card1Suit char(1),
		card2Value smallint,
		card2Suit char(1),
		card3Value smallint,
		card3Suit char(1),
		card4Value smallint,
		card4Suit char(1),
		card5Value smallint,
		card5Suit char(1))""")

		self.create_table("""Tourneys (
		id INT UNSIGNED UNIQUE AUTO_INCREMENT, PRIMARY KEY (id),
		siteId SMALLINT UNSIGNED, FOREIGN KEY (siteId) REFERENCES Sites(id),
		siteTourneyNo BIGINT,
		buyin INT,
		fee INT,
		knockout INT,
		entries INT,
		prizepool INT,
		startTime DATETIME,
		comment TEXT,
		commentTs DATETIME)""")

		self.create_table("""TourneysPlayers (
		id BIGINT UNSIGNED UNIQUE AUTO_INCREMENT, PRIMARY KEY (id),
		tourneyId INT UNSIGNED, FOREIGN KEY (tourneyId) REFERENCES Tourneys(id),
		playerId INT UNSIGNED, FOREIGN KEY (playerId) REFERENCES Players(id),
		payinAmount INT,
		rank INT,
		winnings INT,
		comment TEXT,
		commentTs DATETIME)""")

		self.create_table("""HandsPlayers (
		id BIGINT UNSIGNED UNIQUE AUTO_INCREMENT, PRIMARY KEY (id),
		handId BIGINT UNSIGNED, FOREIGN KEY (handId) REFERENCES Hands(id),
		playerId INT UNSIGNED, FOREIGN KEY (playerId) REFERENCES Players(id),
		startCash int,
		position char(1),
		ante int,
	
		card1Value smallint,
		card1Suit char(1),
		card2Value smallint,
		card2Suit char(1),
		card3Value smallint,
		card3Suit char(1),
		card4Value smallint,
		card4Suit char(1),
		card5Value smallint,
		card5Suit char(1),
		card6Value smallint,
		card6Suit char(1),
		card7Value smallint,
		card7Suit char(1),
	
		winnings int,
		rake int,
		comment text,
		commentTs DATETIME,
	
		tourneysPlayersId BIGINT UNSIGNED, FOREIGN KEY (tourneysPlayersId) REFERENCES TourneysPlayers(id))""")

		self.create_table("""HandsActions (
		id BIGINT UNSIGNED UNIQUE AUTO_INCREMENT, PRIMARY KEY (id),
		handPlayerId BIGINT UNSIGNED, FOREIGN KEY (handPlayerId) REFERENCES HandsPlayers(id),
		street SMALLINT,
		actionNo SMALLINT,
		action CHAR(5),
		amount INT,
		comment TEXT,
		commentTs DATETIME)""")
		
		self.create_table("""HudDataHoldemOmaha (
		id BIGINT UNSIGNED UNIQUE AUTO_INCREMENT, PRIMARY KEY (id),
		gametypeId SMALLINT UNSIGNED, FOREIGN KEY (gametypeId) REFERENCES Gametypes(id),
		playerId INT UNSIGNED, FOREIGN KEY (playerId) REFERENCES Players(id),
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
		foldedSbToSteal INT,
		
		contBetChance INT,
		contBetDone INT,
		secondBarrelChance INT,
		secondBarrelDone INT,
		thirdBarrelChance INT,
		thirdBarrelDone INT)""")
		
		self.cursor.execute("INSERT INTO Settings VALUES (35);")
		self.cursor.execute("INSERT INTO Sites VALUES (DEFAULT, \"Full Tilt Poker\", 'USD');")
		self.cursor.execute("INSERT INTO Sites VALUES (DEFAULT, \"PokerStars\", 'USD');")
		self.db.commit()
		print "finished recreating tables"
	#end def recreate_tables
#end class fpdb_db
