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
		oldDbVersion=0
		try:
			self.cursor.execute("SELECT * FROM settings") #for alpha1
			oldDbVersion=self.cursor.fetchone()[0]
		except:# _mysql_exceptions.ProgrammingError:
			pass
		try:
			self.cursor.execute("SELECT * FROM Settings")
			oldDbVersion=self.cursor.fetchone()[0]
		except:# _mysql_exceptions.ProgrammingError:
			pass
		
		if oldDbVersion<=34:
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
		
		if oldDbVersion>34 and oldDbVersion<=45:
			self.cursor.execute("DROP TABLE IF EXISTS HudDataHoldemOmaha;")
		
		self.cursor.execute("DROP TABLE IF EXISTS Settings;")
		self.cursor.execute("DROP TABLE IF EXISTS HudCache;")
		self.cursor.execute("DROP TABLE IF EXISTS Autorates;")
		self.cursor.execute("DROP TABLE IF EXISTS BoardCards;")
		self.cursor.execute("DROP TABLE IF EXISTS HandsActions;")
		self.cursor.execute("DROP TABLE IF EXISTS HandsPlayers;")
		self.cursor.execute("DROP TABLE IF EXISTS Hands;")
		self.cursor.execute("DROP TABLE IF EXISTS TourneysPlayers;")
		self.cursor.execute("DROP TABLE IF EXISTS Tourneys;")
		self.cursor.execute("DROP TABLE IF EXISTS Players;")
		self.cursor.execute("DROP TABLE IF EXISTS Gametypes;")
		if oldDbVersion>45 and oldDbVersion<=51:
			self.cursor.execute("DROP TABLE IF EXISTS TourneysGametypes;")		
		self.cursor.execute("DROP TABLE IF EXISTS TourneyTypes;")
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
	
	def fillDefaultData(self):
		self.cursor.execute("INSERT INTO Settings VALUES (118);")
		self.cursor.execute("INSERT INTO Sites VALUES (DEFAULT, \"Full Tilt Poker\", 'USD');")
		self.cursor.execute("INSERT INTO Sites VALUES (DEFAULT, \"PokerStars\", 'USD');")
		self.cursor.execute("INSERT INTO TourneyTypes VALUES (DEFAULT, 1, 0, 0, 0, False);")
	#end def fillDefaultData
	
	def recreate_tables(self):
		"""(Re-)creates the tables of the current DB"""
		
		if self.backend == 3:
#	postgresql
			print "recreating tables in postgres db"
			schema_file = open('schema.postgres.sql', 'r')
			schema = schema_file.read()
			schema_file.close()
			curse = self.db.cursor()
#			curse.executemany(schema, [1, 2])
			for sql in schema.split(';'):
				sql = sql.rstrip()
				if sql == '':
					continue
				curse.execute(sql)
			#self.fillDefaultData()
			self.db.commit()
			curse.close()
			return
		
		self.drop_tables()
		
		self.create_table("""Settings (
		version SMALLINT NOT NULL)""")
		
		self.create_table("""Sites (
		id SMALLINT UNSIGNED UNIQUE AUTO_INCREMENT NOT NULL, PRIMARY KEY (id),
		name varchar(32) NOT NULL,
		currency char(3) NOT NULL)""")
		
		self.create_table("""Gametypes (
		id SMALLINT UNSIGNED UNIQUE AUTO_INCREMENT NOT NULL, PRIMARY KEY (id),
		siteId SMALLINT UNSIGNED NOT NULL, FOREIGN KEY (siteId) REFERENCES Sites(id),
		type char(4) NOT NULL,
		base char(4) NOT NULL,
		category varchar(9) NOT NULL,
		limitType char(2) NOT NULL,
		hiLo char(1) NOT NULL,
		smallBlind int,
		bigBlind int,
		smallBet int NOT NULL,
		bigBet int NOT NULL)""")
		#NOT NULL not set for small/bigBlind as they are not existent in all games
		
		self.create_table("""Players (
		id INT UNSIGNED UNIQUE AUTO_INCREMENT NOT NULL, PRIMARY KEY (id),
		name VARCHAR(32) CHARACTER SET utf8 NOT NULL,
		siteId SMALLINT UNSIGNED NOT NULL, FOREIGN KEY (siteId) REFERENCES Sites(id),
		comment text,
		commentTs DATETIME)""")
		
		self.create_table("""Autorates (
		id BIGINT UNSIGNED UNIQUE AUTO_INCREMENT NOT NULL, PRIMARY KEY (id),
		playerId INT UNSIGNED NOT NULL, FOREIGN KEY (playerId) REFERENCES Players(id),
		gametypeId SMALLINT UNSIGNED NOT NULL, FOREIGN KEY (gametypeId) REFERENCES Gametypes(id),
		description varchar(50) NOT NULL,
		shortDesc char(8) NOT NULL,
		ratingTime DATETIME NOT NULL,
		handCount int NOT NULL)""")

		self.create_table("""Hands (
		id BIGINT UNSIGNED UNIQUE AUTO_INCREMENT NOT NULL, PRIMARY KEY (id),
		tableName VARCHAR(20) NOT NULL,
		siteHandNo BIGINT NOT NULL,
		gametypeId SMALLINT UNSIGNED NOT NULL, FOREIGN KEY (gametypeId) REFERENCES Gametypes(id),
		handStart DATETIME NOT NULL,
		importTime DATETIME NOT NULL,
		seats SMALLINT NOT NULL,
		maxSeats SMALLINT NOT NULL,
		comment TEXT,
		commentTs DATETIME)""")

		self.create_table("""BoardCards (
		id BIGINT UNSIGNED UNIQUE AUTO_INCREMENT NOT NULL, PRIMARY KEY (id),
		handId BIGINT UNSIGNED NOT NULL, FOREIGN KEY (handId) REFERENCES Hands(id),
		card1Value smallint NOT NULL,
		card1Suit char(1) NOT NULL,
		card2Value smallint NOT NULL,
		card2Suit char(1) NOT NULL,
		card3Value smallint NOT NULL,
		card3Suit char(1) NOT NULL,
		card4Value smallint NOT NULL,
		card4Suit char(1) NOT NULL,
		card5Value smallint NOT NULL,
		card5Suit char(1) NOT NULL)""")

		self.create_table("""TourneyTypes (
		id SMALLINT UNSIGNED UNIQUE AUTO_INCREMENT NOT NULL, PRIMARY KEY (id),
		siteId SMALLINT UNSIGNED NOT NULL, FOREIGN KEY (siteId) REFERENCES Sites(id),
		buyin INT NOT NULL,
		fee INT NOT NULL,
		knockout INT NOT NULL,
		rebuyOrAddon BOOLEAN NOT NULL)""")

		self.create_table("""Tourneys (
		id INT UNSIGNED UNIQUE AUTO_INCREMENT NOT NULL, PRIMARY KEY (id),
		tourneyTypeId SMALLINT UNSIGNED NOT NULL, FOREIGN KEY (tourneyTypeId) REFERENCES TourneyTypes(id),
		siteTourneyNo BIGINT NOT NULL,
		entries INT NOT NULL,
		prizepool INT NOT NULL,
		startTime DATETIME NOT NULL,
		comment TEXT,
		commentTs DATETIME)""")

		self.create_table("""TourneysPlayers (
		id BIGINT UNSIGNED UNIQUE AUTO_INCREMENT NOT NULL, PRIMARY KEY (id),
		tourneyId INT UNSIGNED NOT NULL, FOREIGN KEY (tourneyId) REFERENCES Tourneys(id),
		playerId INT UNSIGNED NOT NULL, FOREIGN KEY (playerId) REFERENCES Players(id),
		payinAmount INT NOT NULL,
		rank INT NOT NULL,
		winnings INT NOT NULL,
		comment TEXT,
		commentTs DATETIME)""")

		self.create_table("""HandsPlayers (
		id BIGINT UNSIGNED UNIQUE AUTO_INCREMENT NOT NULL, PRIMARY KEY (id),
		handId BIGINT UNSIGNED NOT NULL, FOREIGN KEY (handId) REFERENCES Hands(id),
		playerId INT UNSIGNED NOT NULL, FOREIGN KEY (playerId) REFERENCES Players(id),
		startCash INT NOT NULL,
		position CHAR(1),
		seatNo SMALLINT NOT NULL,
		ante INT,
	
		card1Value smallint NOT NULL,
		card1Suit char(1) NOT NULL,
		card2Value smallint NOT NULL,
		card2Suit char(1) NOT NULL,
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
	
		winnings int NOT NULL,
		rake int NOT NULL,
		comment text,
		commentTs DATETIME,
	
		tourneysPlayersId BIGINT UNSIGNED, FOREIGN KEY (tourneysPlayersId) REFERENCES TourneysPlayers(id))""")
		#NOT NULL not set on cards 3-7 as they dont exist in all games

		self.create_table("""HandsActions (
		id BIGINT UNSIGNED UNIQUE AUTO_INCREMENT NOT NULL, PRIMARY KEY (id),
		handPlayerId BIGINT UNSIGNED NOT NULL, FOREIGN KEY (handPlayerId) REFERENCES HandsPlayers(id),
		street SMALLINT NOT NULL,
		actionNo SMALLINT NOT NULL,
		action CHAR(5) NOT NULL,
		allIn BOOLEAN NOT NULL,
		amount INT NOT NULL,
		comment TEXT,
		commentTs DATETIME)""")
		
		self.create_table("""HudCache (
		id BIGINT UNSIGNED UNIQUE AUTO_INCREMENT NOT NULL, PRIMARY KEY (id),
		gametypeId SMALLINT UNSIGNED NOT NULL, FOREIGN KEY (gametypeId) REFERENCES Gametypes(id),
		playerId INT UNSIGNED NOT NULL, FOREIGN KEY (playerId) REFERENCES Players(id),
		activeSeats SMALLINT NOT NULL,
		position CHAR(1),
		tourneyTypeId SMALLINT UNSIGNED NOT NULL, FOREIGN KEY (tourneyTypeId) REFERENCES TourneyTypes(id),
		
		HDs INT NOT NULL,
		street0VPI INT NOT NULL,
		street0Aggr INT NOT NULL,
		street0_3B4BChance INT NOT NULL,
		street0_3B4BDone INT NOT NULL,
		
		street1Seen INT NOT NULL,
		street2Seen INT NOT NULL,
		street3Seen INT NOT NULL,
		street4Seen INT NOT NULL,
		sawShowdown INT NOT NULL,
		
		street1Aggr INT NOT NULL,
		street2Aggr INT NOT NULL,
		street3Aggr INT NOT NULL,
		street4Aggr INT NOT NULL,
		
		otherRaisedStreet1 INT NOT NULL,
		otherRaisedStreet2 INT NOT NULL,
		otherRaisedStreet3 INT NOT NULL,
		otherRaisedStreet4 INT NOT NULL,
		foldToOtherRaisedStreet1 INT NOT NULL,
		foldToOtherRaisedStreet2 INT NOT NULL,
		foldToOtherRaisedStreet3 INT NOT NULL,
		foldToOtherRaisedStreet4 INT NOT NULL,
		wonWhenSeenStreet1 FLOAT NOT NULL,
		wonAtSD FLOAT NOT NULL,
		
		stealAttemptChance INT NOT NULL,
		stealAttempted INT NOT NULL,
		foldBbToStealChance INT NOT NULL,
		foldedBbToSteal INT NOT NULL,
		foldSbToStealChance INT NOT NULL,
		foldedSbToSteal INT NOT NULL,
		
		street1CBChance INT NOT NULL,
		street1CBDone INT NOT NULL,
		street2CBChance INT NOT NULL,
		street2CBDone INT NOT NULL,
		street3CBChance INT NOT NULL,
		street3CBDone INT NOT NULL,
		street4CBChance INT NOT NULL,
		street4CBDone INT NOT NULL,
		
		foldToStreet1CBChance INT NOT NULL,
		foldToStreet1CBDone INT NOT NULL,
		foldToStreet2CBChance INT NOT NULL,
		foldToStreet2CBDone INT NOT NULL,
		foldToStreet3CBChance INT NOT NULL,
		foldToStreet3CBDone INT NOT NULL,
		foldToStreet4CBChance INT NOT NULL,
		foldToStreet4CBDone INT NOT NULL,
		
		totalProfit INT NOT NULL,
		
		street1CheckCallRaiseChance INT NOT NULL,
		street1CheckCallRaiseDone INT NOT NULL,
		street2CheckCallRaiseChance INT NOT NULL,
		street2CheckCallRaiseDone INT NOT NULL,
		street3CheckCallRaiseChance INT NOT NULL,
		street3CheckCallRaiseDone INT NOT NULL,
		street4CheckCallRaiseChance INT NOT NULL,
		street4CheckCallRaiseDone INT NOT NULL)""")
		
		self.fillDefaultData()
		self.db.commit()
		print "finished recreating tables"
	#end def recreate_tables
#end class fpdb_db
