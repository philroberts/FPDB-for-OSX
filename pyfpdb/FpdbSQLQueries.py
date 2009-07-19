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
#    File for DB queries used in fpdb
#

import sys
import os

class FpdbSQLQueries:

    def __init__(self, db):
        self.query = {}
        self.dbname = db

        ################################
        # List tables
        ################################
        if(self.dbname == 'MySQL InnoDB'):
            self.query['list_tables'] = """SHOW TABLES"""
        elif(self.dbname == 'PostgreSQL'):
            self.query['list_tables'] = """SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"""
        elif(self.dbname == 'SQLite'):
            self.query['list_tables'] = """SELECT name FROM sqlite_master
            WHERE type='table'
            ORDER BY name;"""

        ##################################################################
        # Drop Tables - MySQL, PostgreSQL and SQLite all share same syntax
        ##################################################################

        if(self.dbname == 'MySQL InnoDB') or (self.dbname == 'PostgreSQL') or (self.dbname == 'SQLite'):
            self.query['drop_table'] = """DROP TABLE IF EXISTS """


        ################################
        # Create Tables
        ################################

        ################################
        # Create Settings
        ################################
        if(self.dbname == 'MySQL InnoDB'):
            self.query['createSettingsTable'] = """CREATE TABLE Settings (
                                        version SMALLINT NOT NULL)
                                ENGINE=INNODB""" 
        elif(self.dbname == 'PostgreSQL'):
            self.query['createSettingsTable'] =  """CREATE TABLE Settings (version SMALLINT)"""

        elif(self.dbname == 'SQLite'):
            self.query['createSettingsTable'] = """CREATE TABLE Settings
            (version INTEGER) """


        ################################
        # Create Sites
        ################################

        if(self.dbname == 'MySQL InnoDB'):
            self.query['createSitesTable'] = """CREATE TABLE Sites (
                        id SMALLINT UNSIGNED AUTO_INCREMENT NOT NULL, PRIMARY KEY (id),
                        name varchar(32) NOT NULL,
                        currency char(3) NOT NULL)
                        ENGINE=INNODB""" 
        elif(self.dbname == 'PostgreSQL'):
            self.query['createSitesTable'] = """CREATE TABLE Sites (
                        id SERIAL, PRIMARY KEY (id),
                        name varchar(32),
                        currency char(3))"""
        elif(self.dbname == 'SQLite'):
            self.query['createSitesTable'] = """CREATE TABLE Sites (
                        id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL,
                        currency TEXT NOT NULL)"""


        ################################
        # Create Gametypes
        ################################

        if(self.dbname == 'MySQL InnoDB'):
            self.query['createGametypesTable'] = """CREATE TABLE Gametypes (
                        id SMALLINT UNSIGNED AUTO_INCREMENT NOT NULL, PRIMARY KEY (id),
                        siteId SMALLINT UNSIGNED NOT NULL, FOREIGN KEY (siteId) REFERENCES Sites(id),
                        type char(4) NOT NULL,
                        base char(4) NOT NULL,
                        category varchar(9) NOT NULL,
                        limitType char(2) NOT NULL,
                        hiLo char(1) NOT NULL,
                        smallBlind int,
                        bigBlind int,
                        smallBet int NOT NULL,
                        bigBet int NOT NULL)
                        ENGINE=INNODB""" 
        elif(self.dbname == 'PostgreSQL'):
            self.query['createGametypesTable'] = """CREATE TABLE Gametypes (
                        id SERIAL, PRIMARY KEY (id),
                        siteId INTEGER, FOREIGN KEY (siteId) REFERENCES Sites(id),
                        type char(4),
                        base char(4),
                        category varchar(9),
                        limitType char(2),
                        hiLo char(1),
                        smallBlind int,
                        bigBlind int,
                        smallBet int,
                        bigBet int)"""
        elif(self.dbname == 'SQLite'):
            self.query['createGametypesTable'] = """CREATE TABLE GameTypes (
                        id INTEGER PRIMARY KEY,
                        siteId INTEGER,
                        type TEXT,
                        base TEXT,
                        category TEXT,
                        limitType TEXT,
                        hiLo TEXT,
                        smallBlind INTEGER,
                        bigBlind INTEGER,
                        smallBet INTEGER,
                        bigBet INTEGER,
                        FOREIGN KEY(siteId) REFERENCES Sites(id) ON DELETE CASCADE)"""


        ################################
        # Create Players
        ################################

        if(self.dbname == 'MySQL InnoDB'):
            self.query['createPlayersTable'] = """CREATE TABLE Players (
                            id INT UNSIGNED AUTO_INCREMENT NOT NULL, PRIMARY KEY (id),
                            name VARCHAR(32) CHARACTER SET utf8 NOT NULL,
                            siteId SMALLINT UNSIGNED NOT NULL, FOREIGN KEY (siteId) REFERENCES Sites(id),
                            comment text,
                            commentTs DATETIME)
                        ENGINE=INNODB""" 
        elif(self.dbname == 'PostgreSQL'):
            self.query['createPlayersTable'] = """CREATE TABLE Players (
                        id SERIAL, PRIMARY KEY (id),
                        name VARCHAR(32),
                        siteId INTEGER, FOREIGN KEY (siteId) REFERENCES Sites(id),
                        comment text,
                        commentTs timestamp without time zone)"""
        elif(self.dbname == 'SQLite'):
            self.query['createPlayersTable'] = """CREATE TABLE Players (
                        id INTEGER PRIMARY KEY,
                        name TEXT,
                        siteId INTEGER,
                        comment TEXT,
                        commentTs BLOB,
                        FOREIGN KEY(siteId) REFERENCES Sites(id) ON DELETE CASCADE)"""


        ################################
        # Create Autorates
        ################################

        if(self.dbname == 'MySQL InnoDB'):
            self.query['createAutoratesTable'] = """CREATE TABLE Autorates (
                            id BIGINT UNSIGNED AUTO_INCREMENT NOT NULL, PRIMARY KEY (id),
                            playerId INT UNSIGNED NOT NULL, FOREIGN KEY (playerId) REFERENCES Players(id),
                            gametypeId SMALLINT UNSIGNED NOT NULL, FOREIGN KEY (gametypeId) REFERENCES Gametypes(id),
                            description varchar(50) NOT NULL,
                            shortDesc char(8) NOT NULL,
                            ratingTime DATETIME NOT NULL,
                            handCount int NOT NULL)
                        ENGINE=INNODB""" 
        elif(self.dbname == 'PostgreSQL'):
            self.query['createAutoratesTable'] = """CREATE TABLE Autorates (
                            id BIGSERIAL, PRIMARY KEY (id),
                            playerId INT, FOREIGN KEY (playerId) REFERENCES Players(id),
                            gametypeId INT, FOREIGN KEY (gametypeId) REFERENCES Gametypes(id),
                            description varchar(50),
                            shortDesc char(8),
                            ratingTime timestamp without time zone,
                        handCount int)"""
        elif(self.dbname == 'SQLite'):
            self.query['createAutoratesTable'] = """ """


        ################################
        # Create Hands
        ################################

        if(self.dbname == 'MySQL InnoDB'):
            self.query['createHandsTable'] = """CREATE TABLE Hands (
                            id BIGINT UNSIGNED AUTO_INCREMENT NOT NULL, PRIMARY KEY (id),
                            tableName VARCHAR(20) NOT NULL,
                            siteHandNo BIGINT NOT NULL,
                            gametypeId SMALLINT UNSIGNED NOT NULL, FOREIGN KEY (gametypeId) REFERENCES Gametypes(id),
                            handStart DATETIME NOT NULL,
                            importTime DATETIME NOT NULL,
                            seats TINYINT NOT NULL,
                            maxSeats TINYINT NOT NULL,
                            boardcard1 smallint,  /* 0=none, 1-13=2-Ah 14-26=2-Ad 27-39=2-Ac 40-52=2-As */
                            boardcard2 smallint,
                            boardcard3 smallint,
                            boardcard4 smallint,
                            boardcard5 smallint,
                            texture smallint,
                            playersVpi SMALLINT NOT NULL,         /* num of players vpi */
                            playersAtStreet1 SMALLINT NOT NULL,   /* num of players seeing flop/street4 */
                            playersAtStreet2 SMALLINT NOT NULL,
                            playersAtStreet3 SMALLINT NOT NULL,
                            playersAtStreet4 SMALLINT NOT NULL,
                            playersAtShowdown SMALLINT NOT NULL,
                            street0Raises TINYINT NOT NULL, /* num small bets paid to see flop/street4, including blind */
                            street1Raises TINYINT NOT NULL, /* num small bets paid to see turn/street5 */
                            street2Raises TINYINT NOT NULL, /* num big bets paid to see river/street6 */
                            street3Raises TINYINT NOT NULL, /* num big bets paid to see sd/street7 */
                            street4Raises TINYINT NOT NULL, /* num big bets paid to see showdown */
                            street1Pot INT,                  /* pot size at flop/street4 */
                            street2Pot INT,                  /* pot size at turn/street5 */
                            street3Pot INT,                  /* pot size at river/street6 */
                            street4Pot INT,                  /* pot size at sd/street7 */
                            showdownPot INT,                 /* pot size at sd/street7 */
                            comment TEXT,
                            commentTs DATETIME)
                        ENGINE=INNODB""" 
        elif(self.dbname == 'PostgreSQL'):
            self.query['createHandsTable'] = """CREATE TABLE Hands (
                            id BIGSERIAL, PRIMARY KEY (id),
                            tableName VARCHAR(20) NOT NULL,
                            siteHandNo BIGINT NOT NULL,
                            gametypeId INT NOT NULL, FOREIGN KEY (gametypeId) REFERENCES Gametypes(id),
                            handStart timestamp without time zone NOT NULL,
                            importTime timestamp without time zone NOT NULL,
                            seats SMALLINT NOT NULL,
                            maxSeats SMALLINT NOT NULL,
                            boardcard1 smallint,  /* 0=none, 1-13=2-Ah 14-26=2-Ad 27-39=2-Ac 40-52=2-As */
                            boardcard2 smallint,
                            boardcard3 smallint,
                            boardcard4 smallint,
                            boardcard5 smallint,
                            texture smallint,
                            playersVpi SMALLINT NOT NULL,         /* num of players vpi */
                            playersAtStreet1 SMALLINT NOT NULL,   /* num of players seeing flop/street4 */
                            playersAtStreet2 SMALLINT NOT NULL,
                            playersAtStreet3 SMALLINT NOT NULL,
                            playersAtStreet4 SMALLINT NOT NULL,
                            playersAtShowdown SMALLINT NOT NULL,
                            street0Raises SMALLINT NOT NULL, /* num small bets paid to see flop/street4, including blind */
                            street1Raises SMALLINT NOT NULL, /* num small bets paid to see turn/street5 */
                            street2Raises SMALLINT NOT NULL, /* num big bets paid to see river/street6 */
                            street3Raises SMALLINT NOT NULL, /* num big bets paid to see sd/street7 */
                            street4Raises SMALLINT NOT NULL, /* num big bets paid to see showdown */
                            street1Pot INT,                 /* pot size at flop/street4 */
                            street2Pot INT,                 /* pot size at turn/street5 */
                            street3Pot INT,                 /* pot size at river/street6 */
                            street4Pot INT,                 /* pot size at sd/street7 */
                            showdownPot INT,                /* pot size at sd/street7 */
                            comment TEXT,
                            commentTs timestamp without time zone)"""
        elif(self.dbname == 'SQLite'):
            self.query['createHandsTable'] = """CREATE TABLE Hands (
                            id INTEGER PRIMARY KEY,
                            tableName TEXT(20),
                            siteHandNo INTEGER,
                            gametypeId INTEGER,
                            handStart BLOB,
                            importTime BLOB,
                            seats INTEGER,
                            maxSeats INTEGER,
                            comment TEXT,
                            commentTs BLOB,
                            FOREIGN KEY(gametypeId) REFERENCES Gametypes(id) ON DELETE CASCADE)"""


        ################################
        # Create TourneyTypes
        ################################

        if(self.dbname == 'MySQL InnoDB'):
            self.query['createTourneyTypesTable'] = """CREATE TABLE TourneyTypes (
                            id SMALLINT UNSIGNED AUTO_INCREMENT NOT NULL, PRIMARY KEY (id),
                            siteId SMALLINT UNSIGNED NOT NULL, FOREIGN KEY (siteId) REFERENCES Sites(id),
                            buyin INT NOT NULL,
                            fee INT NOT NULL,
                            knockout INT NOT NULL,
                            rebuyOrAddon BOOLEAN NOT NULL)
                        ENGINE=INNODB""" 
        elif(self.dbname == 'PostgreSQL'):
            self.query['createTourneyTypesTable'] = """CREATE TABLE TourneyTypes (
                        id SERIAL, PRIMARY KEY (id),
                        siteId INT, FOREIGN KEY (siteId) REFERENCES Sites(id),
                        buyin INT,
                        fee INT,
                        knockout INT,
                        rebuyOrAddon BOOLEAN)"""
        elif(self.dbname == 'SQLite'):
            self.query['createTourneyTypesTable'] = """ """


        ################################
        # Create Tourneys
        ################################

        if(self.dbname == 'MySQL InnoDB'):
            self.query['createTourneysTable'] = """CREATE TABLE Tourneys (
                        id INT UNSIGNED AUTO_INCREMENT NOT NULL, PRIMARY KEY (id),
                        tourneyTypeId SMALLINT UNSIGNED NOT NULL, FOREIGN KEY (tourneyTypeId) REFERENCES TourneyTypes(id),
                        siteTourneyNo BIGINT NOT NULL,
                        entries INT NOT NULL,
                        prizepool INT NOT NULL,
                        startTime DATETIME NOT NULL,
                        comment TEXT,
                        commentTs DATETIME)
                        ENGINE=INNODB"""
        elif(self.dbname == 'PostgreSQL'):
            self.query['createTourneysTable'] = """CREATE TABLE Tourneys (
                        id SERIAL, PRIMARY KEY (id),
                        tourneyTypeId INT, FOREIGN KEY (tourneyTypeId) REFERENCES TourneyTypes(id),
                        siteTourneyNo BIGINT,
                        entries INT,
                        prizepool INT,
                        startTime timestamp without time zone,
                        comment TEXT,
                        commentTs timestamp without time zone)"""
        elif(self.dbname == 'SQLite'):
            self.query['createTourneysTable'] = """CREATE TABLE TourneyTypes (
                        id INTEGER PRIMARY KEY,
                        siteId INTEGER,
                        buyin INTEGER,
                        fee INTEGER,
                        knockout INTEGER,
                        rebuyOrAddon BOOL,
                        FOREIGN KEY(siteId) REFERENCES Sites(id) ON DELETE CASCADE)"""

        ################################
        # Create HandsPlayers
        ################################

        if(self.dbname == 'MySQL InnoDB'):
            self.query['createHandsPlayersTable'] = """CREATE TABLE HandsPlayers (
                        id BIGINT UNSIGNED AUTO_INCREMENT NOT NULL, PRIMARY KEY (id),
                        handId BIGINT UNSIGNED NOT NULL, FOREIGN KEY (handId) REFERENCES Hands(id),
                        playerId INT UNSIGNED NOT NULL, FOREIGN KEY (playerId) REFERENCES Players(id),
                        startCash INT NOT NULL,
                        position CHAR(1),
                        seatNo SMALLINT NOT NULL,
                    
                        card1 smallint NOT NULL,  /* 0=none, 1-13=2-Ah 14-26=2-Ad 27-39=2-Ac 40-52=2-As */
                        card2 smallint NOT NULL,
                        card3 smallint,
                        card4 smallint,
                        card5 smallint,
                        card6 smallint,
                        card7 smallint,
                        startCards smallint,
                    
                        ante INT,
                        winnings int NOT NULL,
                        rake int NOT NULL,
                        totalProfit INT NOT NULL,
                        comment text,
                        commentTs DATETIME,
                        tourneysPlayersId BIGINT UNSIGNED, 
                        tourneyTypeId SMALLINT UNSIGNED NOT NULL, FOREIGN KEY (tourneyTypeId) REFERENCES TourneyTypes(id),

                        wonWhenSeenStreet1 FLOAT NOT NULL,
                        wonWhenSeenStreet2 FLOAT,
                        wonWhenSeenStreet3 FLOAT,
                        wonWhenSeenStreet4 FLOAT,
                        wonAtSD FLOAT NOT NULL,

                        street0VPI BOOLEAN NOT NULL,
                        street0Aggr BOOLEAN NOT NULL,
                        street0_3BChance BOOLEAN NOT NULL,
                        street0_3BDone BOOLEAN NOT NULL,
                        street0_4BChance BOOLEAN,
                        street0_4BDone BOOLEAN,
                        other3BStreet0 BOOLEAN,
                        other4BStreet0 BOOLEAN,

                        street1Seen BOOLEAN NOT NULL,
                        street2Seen BOOLEAN NOT NULL,
                        street3Seen BOOLEAN NOT NULL,
                        street4Seen BOOLEAN NOT NULL,
                        sawShowdown BOOLEAN NOT NULL,

                        street1Aggr BOOLEAN NOT NULL,
                        street2Aggr BOOLEAN NOT NULL,
                        street3Aggr BOOLEAN NOT NULL,
                        street4Aggr BOOLEAN NOT NULL,

                        otherRaisedStreet0 BOOLEAN,
                        otherRaisedStreet1 BOOLEAN NOT NULL,
                        otherRaisedStreet2 BOOLEAN NOT NULL,
                        otherRaisedStreet3 BOOLEAN NOT NULL,
                        otherRaisedStreet4 BOOLEAN NOT NULL,
                        foldToOtherRaisedStreet0 BOOLEAN,
                        foldToOtherRaisedStreet1 BOOLEAN NOT NULL,
                        foldToOtherRaisedStreet2 BOOLEAN NOT NULL,
                        foldToOtherRaisedStreet3 BOOLEAN NOT NULL,
                        foldToOtherRaisedStreet4 BOOLEAN NOT NULL,

                        stealAttemptChance BOOLEAN NOT NULL,
                        stealAttempted BOOLEAN NOT NULL,
                        foldBbToStealChance BOOLEAN NOT NULL,
                        foldedBbToSteal BOOLEAN NOT NULL,
                        foldSbToStealChance BOOLEAN NOT NULL,
                        foldedSbToSteal BOOLEAN NOT NULL,

                        street1CBChance BOOLEAN NOT NULL,
                        street1CBDone BOOLEAN NOT NULL,
                        street2CBChance BOOLEAN NOT NULL,
                        street2CBDone BOOLEAN NOT NULL,
                        street3CBChance BOOLEAN NOT NULL,
                        street3CBDone BOOLEAN NOT NULL,
                        street4CBChance BOOLEAN NOT NULL,
                        street4CBDone BOOLEAN NOT NULL,

                        foldToStreet1CBChance BOOLEAN NOT NULL,
                        foldToStreet1CBDone BOOLEAN NOT NULL,
                        foldToStreet2CBChance BOOLEAN NOT NULL,
                        foldToStreet2CBDone BOOLEAN NOT NULL,
                        foldToStreet3CBChance BOOLEAN NOT NULL,
                        foldToStreet3CBDone BOOLEAN NOT NULL,
                        foldToStreet4CBChance BOOLEAN NOT NULL,
                        foldToStreet4CBDone BOOLEAN NOT NULL,

                        street1CheckCallRaiseChance BOOLEAN NOT NULL,
                        street1CheckCallRaiseDone BOOLEAN NOT NULL,
                        street2CheckCallRaiseChance BOOLEAN NOT NULL,
                        street2CheckCallRaiseDone BOOLEAN NOT NULL,
                        street3CheckCallRaiseChance BOOLEAN NOT NULL,
                        street3CheckCallRaiseDone BOOLEAN NOT NULL,
                        street4CheckCallRaiseChance BOOLEAN NOT NULL,
                        street4CheckCallRaiseDone BOOLEAN NOT NULL,

                        street0Calls TINYINT,
                        street1Calls TINYINT,
                        street2Calls TINYINT,
                        street3Calls TINYINT,
                        street4Calls TINYINT,
                        street0Bets TINYINT,
                        street1Bets TINYINT,
                        street2Bets TINYINT,
                        street3Bets TINYINT,
                        street4Bets TINYINT,
                        street0Raises TINYINT,
                        street1Raises TINYINT,
                        street2Raises TINYINT,
                        street3Raises TINYINT,
                        street4Raises TINYINT,

                        actionString VARCHAR(15),

                        FOREIGN KEY (tourneysPlayersId) REFERENCES TourneysPlayers(id))
                        ENGINE=INNODB"""
        elif(self.dbname == 'PostgreSQL'):
            self.query['createHandsPlayersTable'] = """CREATE TABLE HandsPlayers (
                        id BIGSERIAL, PRIMARY KEY (id),
                        handId BIGINT NOT NULL, FOREIGN KEY (handId) REFERENCES Hands(id),
                        playerId INT NOT NULL, FOREIGN KEY (playerId) REFERENCES Players(id),
                        startCash INT NOT NULL,
                        position CHAR(1),
                        seatNo SMALLINT NOT NULL,

                        card1 smallint NOT NULL,  /* 0=none, 1-13=2-Ah 14-26=2-Ad 27-39=2-Ac 40-52=2-As */
                        card2 smallint NOT NULL,
                        card3 smallint,
                        card4 smallint,
                        card5 smallint,
                        card6 smallint,
                        card7 smallint,
                        startCards smallint,

                        ante INT,
                        winnings int NOT NULL,
                        rake int NOT NULL,
                        totalProfit INT NOT NULL,
                        comment text,
                        commentTs timestamp without time zone,
                        tourneysPlayersId BIGINT, 
                        tourneyTypeId INT NOT NULL, FOREIGN KEY (tourneyTypeId) REFERENCES TourneyTypes(id),

                        wonWhenSeenStreet1 FLOAT NOT NULL,
                        wonWhenSeenStreet2 FLOAT,
                        wonWhenSeenStreet3 FLOAT,
                        wonWhenSeenStreet4 FLOAT,
                        wonAtSD FLOAT NOT NULL,

                        street0VPI BOOLEAN NOT NULL,
                        street0Aggr BOOLEAN NOT NULL,
                        street0_3BChance BOOLEAN NOT NULL,
                        street0_3BDone BOOLEAN NOT NULL,
                        street0_4BChance BOOLEAN,
                        street0_4BDone BOOLEAN,
                        other3BStreet0 BOOLEAN,
                        other4BStreet0 BOOLEAN,

                        street1Seen BOOLEAN NOT NULL,
                        street2Seen BOOLEAN NOT NULL,
                        street3Seen BOOLEAN NOT NULL,
                        street4Seen BOOLEAN NOT NULL,
                        sawShowdown BOOLEAN NOT NULL,

                        street1Aggr BOOLEAN NOT NULL,
                        street2Aggr BOOLEAN NOT NULL,
                        street3Aggr BOOLEAN NOT NULL,
                        street4Aggr BOOLEAN NOT NULL,

                        otherRaisedStreet0 BOOLEAN,
                        otherRaisedStreet1 BOOLEAN NOT NULL,
                        otherRaisedStreet2 BOOLEAN NOT NULL,
                        otherRaisedStreet3 BOOLEAN NOT NULL,
                        otherRaisedStreet4 BOOLEAN NOT NULL,
                        foldToOtherRaisedStreet0 BOOLEAN,
                        foldToOtherRaisedStreet1 BOOLEAN NOT NULL,
                        foldToOtherRaisedStreet2 BOOLEAN NOT NULL,
                        foldToOtherRaisedStreet3 BOOLEAN NOT NULL,
                        foldToOtherRaisedStreet4 BOOLEAN NOT NULL,

                        stealAttemptChance BOOLEAN NOT NULL,
                        stealAttempted BOOLEAN NOT NULL,
                        foldBbToStealChance BOOLEAN NOT NULL,
                        foldedBbToSteal BOOLEAN NOT NULL,
                        foldSbToStealChance BOOLEAN NOT NULL,
                        foldedSbToSteal BOOLEAN NOT NULL,

                        street1CBChance BOOLEAN NOT NULL,
                        street1CBDone BOOLEAN NOT NULL,
                        street2CBChance BOOLEAN NOT NULL,
                        street2CBDone BOOLEAN NOT NULL,
                        street3CBChance BOOLEAN NOT NULL,
                        street3CBDone BOOLEAN NOT NULL,
                        street4CBChance BOOLEAN NOT NULL,
                        street4CBDone BOOLEAN NOT NULL,

                        foldToStreet1CBChance BOOLEAN NOT NULL,
                        foldToStreet1CBDone BOOLEAN NOT NULL,
                        foldToStreet2CBChance BOOLEAN NOT NULL,
                        foldToStreet2CBDone BOOLEAN NOT NULL,
                        foldToStreet3CBChance BOOLEAN NOT NULL,
                        foldToStreet3CBDone BOOLEAN NOT NULL,
                        foldToStreet4CBChance BOOLEAN NOT NULL,
                        foldToStreet4CBDone BOOLEAN NOT NULL,

                        street1CheckCallRaiseChance BOOLEAN NOT NULL,
                        street1CheckCallRaiseDone BOOLEAN NOT NULL,
                        street2CheckCallRaiseChance BOOLEAN NOT NULL,
                        street2CheckCallRaiseDone BOOLEAN NOT NULL,
                        street3CheckCallRaiseChance BOOLEAN NOT NULL,
                        street3CheckCallRaiseDone BOOLEAN NOT NULL,
                        street4CheckCallRaiseChance BOOLEAN NOT NULL,
                        street4CheckCallRaiseDone BOOLEAN NOT NULL,

                        street0Calls SMALLINT,
                        street1Calls SMALLINT,
                        street2Calls SMALLINT,
                        street3Calls SMALLINT,
                        street4Calls SMALLINT,
                        street0Bets SMALLINT,
                        street1Bets SMALLINT,
                        street2Bets SMALLINT,
                        street3Bets SMALLINT,
                        street4Bets SMALLINT,
                        street0Raises SMALLINT,
                        street1Raises SMALLINT,
                        street2Raises SMALLINT,
                        street3Raises SMALLINT,
                        street4Raises SMALLINT,

                        actionString VARCHAR(15),

                        FOREIGN KEY (tourneysPlayersId) REFERENCES TourneysPlayers(id))"""
        elif(self.dbname == 'SQLite'):
            self.query['createHandsPlayersTable'] = """ """


        ################################
        # Create TourneysPlayers
        ################################

        if(self.dbname == 'MySQL InnoDB'):
            self.query['createTourneysPlayersTable'] = """CREATE TABLE TourneysPlayers (
                        id BIGINT UNSIGNED AUTO_INCREMENT NOT NULL, PRIMARY KEY (id),
                        tourneyId INT UNSIGNED NOT NULL, FOREIGN KEY (tourneyId) REFERENCES Tourneys(id),
                        playerId INT UNSIGNED NOT NULL, FOREIGN KEY (playerId) REFERENCES Players(id),
                        payinAmount INT NOT NULL,
                        rank INT NOT NULL,
                        winnings INT NOT NULL,
                        comment TEXT,
                        commentTs DATETIME)
                        ENGINE=INNODB"""
        elif(self.dbname == 'PostgreSQL'):
            self.query['createTourneysPlayersTable'] = """CREATE TABLE TourneysPlayers (
                        id BIGSERIAL, PRIMARY KEY (id),
                        tourneyId INT, FOREIGN KEY (tourneyId) REFERENCES Tourneys(id),
                        playerId INT, FOREIGN KEY (playerId) REFERENCES Players(id),
                        payinAmount INT,
                        rank INT,
                        winnings INT,
                        comment TEXT,
                        commentTs timestamp without time zone)"""
        elif(self.dbname == 'SQLite'):
            self.query['createTourneysPlayersTable'] = """ """


        ################################
        # Create HandsActions
        ################################

        if(self.dbname == 'MySQL InnoDB'):
            self.query['createHandsActionsTable'] = """CREATE TABLE HandsActions (
                        id BIGINT UNSIGNED AUTO_INCREMENT NOT NULL, PRIMARY KEY (id),
                        handsPlayerId BIGINT UNSIGNED NOT NULL, FOREIGN KEY (handsPlayerId) REFERENCES HandsPlayers(id),
                        street SMALLINT NOT NULL,
                        actionNo SMALLINT NOT NULL,
                        action CHAR(5) NOT NULL,
                        allIn BOOLEAN NOT NULL,
                        amount INT NOT NULL,
                        comment TEXT,
                        commentTs DATETIME)
                        ENGINE=INNODB"""
        elif(self.dbname == 'PostgreSQL'):
            self.query['createHandsActionsTable'] = """CREATE TABLE HandsActions (
                        id BIGSERIAL, PRIMARY KEY (id),
                        handsPlayerId BIGINT, FOREIGN KEY (handsPlayerId) REFERENCES HandsPlayers(id),
                        street SMALLINT,
                        actionNo SMALLINT,
                        action CHAR(5),
                        allIn BOOLEAN,
                        amount INT,
                        comment TEXT,
                        commentTs timestamp without time zone)"""
        elif(self.dbname == 'SQLite'):
            self.query['createHandsActionsTable'] = """ """


        ################################
        # Create HudCache
        ################################

        if(self.dbname == 'MySQL InnoDB'):
            self.query['createHudCacheTable'] = """CREATE TABLE HudCache (
                        id BIGINT UNSIGNED AUTO_INCREMENT NOT NULL, PRIMARY KEY (id),
                        gametypeId SMALLINT UNSIGNED NOT NULL, FOREIGN KEY (gametypeId) REFERENCES Gametypes(id),
                        playerId INT UNSIGNED NOT NULL, FOREIGN KEY (playerId) REFERENCES Players(id),
                        activeSeats SMALLINT NOT NULL,
                        position CHAR(1),
                        tourneyTypeId SMALLINT UNSIGNED NOT NULL, FOREIGN KEY (tourneyTypeId) REFERENCES TourneyTypes(id),
                        styleKey CHAR(7) NOT NULL,  /* 1st char is style (A/T/H/S), other 6 are the key */
                        HDs INT NOT NULL,

                        wonWhenSeenStreet1 FLOAT NOT NULL,
                        wonWhenSeenStreet2 FLOAT,
                        wonWhenSeenStreet3 FLOAT,
                        wonWhenSeenStreet4 FLOAT,
                        wonAtSD FLOAT NOT NULL,

                        street0VPI INT NOT NULL,
                        street0Aggr INT NOT NULL,
                        street0_3BChance INT NOT NULL,
                        street0_3BDone INT NOT NULL,
                        street0_4BChance INT,
                        street0_4BDone INT,
                        other3BStreet0 INT,
                        other4BStreet0 INT,

                        street1Seen INT NOT NULL,
                        street2Seen INT NOT NULL,
                        street3Seen INT NOT NULL,
                        street4Seen INT NOT NULL,
                        sawShowdown INT NOT NULL,
                        
                        street1Aggr INT NOT NULL,
                        street2Aggr INT NOT NULL,
                        street3Aggr INT NOT NULL,
                        street4Aggr INT NOT NULL,

                        otherRaisedStreet0 INT,
                        otherRaisedStreet1 INT NOT NULL,
                        otherRaisedStreet2 INT NOT NULL,
                        otherRaisedStreet3 INT NOT NULL,
                        otherRaisedStreet4 INT NOT NULL,
                        foldToOtherRaisedStreet0 INT,
                        foldToOtherRaisedStreet1 INT NOT NULL,
                        foldToOtherRaisedStreet2 INT NOT NULL,
                        foldToOtherRaisedStreet3 INT NOT NULL,
                        foldToOtherRaisedStreet4 INT NOT NULL,
                        
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
                        street4CheckCallRaiseDone INT NOT NULL,

                        street0Calls INT,
                        street1Calls INT,
                        street2Calls INT,
                        street3Calls INT,
                        street4Calls INT,
                        street0Bets INT,
                        street1Bets INT,
                        street2Bets INT,
                        street3Bets INT,
                        street4Bets INT,
                        street0Raises INT,
                        street1Raises INT,
                        street2Raises INT,
                        street3Raises INT,
                        street4Raises INT)

                        ENGINE=INNODB"""
        elif(self.dbname == 'PostgreSQL'):
            self.query['createHudCacheTable'] = """CREATE TABLE HudCache (
                        id BIGSERIAL, PRIMARY KEY (id),
                        gametypeId INT, FOREIGN KEY (gametypeId) REFERENCES Gametypes(id),
                        playerId INT, FOREIGN KEY (playerId) REFERENCES Players(id),
                        activeSeats SMALLINT,
                        position CHAR(1),
                        tourneyTypeId INT, FOREIGN KEY (tourneyTypeId) REFERENCES TourneyTypes(id),
                        styleKey CHAR(7) NOT NULL,  /* 1st char is style (A/T/H/S), other 6 are the key */
                        HDs INT,

                        wonWhenSeenStreet1 FLOAT NOT NULL,
                        wonWhenSeenStreet2 FLOAT,
                        wonWhenSeenStreet3 FLOAT,
                        wonWhenSeenStreet4 FLOAT,
                        wonAtSD FLOAT NOT NULL,

                        street0VPI INT NOT NULL,
                        street0Aggr INT,
                        street0_3BChance INT NOT NULL,
                        street0_3BDone INT NOT NULL,
                        street0_4BChance INT,
                        street0_4BDone INT,
                        other3BStreet0 INT,
                        other4BStreet0 INT,

                        street1Seen INT,
                        street2Seen INT,
                        street3Seen INT,
                        street4Seen INT,
                        sawShowdown INT,
                        street1Aggr INT,
                        street2Aggr INT,
                        street3Aggr INT,
                        street4Aggr INT,

                        otherRaisedStreet0 INT,
                        otherRaisedStreet1 INT,
                        otherRaisedStreet2 INT,
                        otherRaisedStreet3 INT,
                        otherRaisedStreet4 INT,
                        foldToOtherRaisedStreet0 INT,
                        foldToOtherRaisedStreet1 INT,
                        foldToOtherRaisedStreet2 INT,
                        foldToOtherRaisedStreet3 INT,
                        foldToOtherRaisedStreet4 INT,

                        stealAttemptChance INT,
                        stealAttempted INT,
                        foldBbToStealChance INT,
                        foldedBbToSteal INT,
                        foldSbToStealChance INT,
                        foldedSbToSteal INT,

                        street1CBChance INT,
                        street1CBDone INT,
                        street2CBChance INT,
                        street2CBDone INT,
                        street3CBChance INT,
                        street3CBDone INT,
                        street4CBChance INT,
                        street4CBDone INT,

                        foldToStreet1CBChance INT,
                        foldToStreet1CBDone INT,
                        foldToStreet2CBChance INT,
                        foldToStreet2CBDone INT,
                        foldToStreet3CBChance INT,
                        foldToStreet3CBDone INT,
                        foldToStreet4CBChance INT,
                        foldToStreet4CBDone INT,

                        totalProfit INT,

                        street1CheckCallRaiseChance INT,
                        street1CheckCallRaiseDone INT,
                        street2CheckCallRaiseChance INT,
                        street2CheckCallRaiseDone INT,
                        street3CheckCallRaiseChance INT,
                        street3CheckCallRaiseDone INT,
                        street4CheckCallRaiseChance INT,
                        street4CheckCallRaiseDone INT,

                        street0Calls INT,
                        street1Calls INT,
                        street2Calls INT,
                        street3Calls INT,
                        street4Calls INT,
                        street0Bets INT,
                        street1Bets INT,
                        street2Bets INT,
                        street3Bets INT,
                        street4Bets INT,
                        street0Raises INT,
                        street1Raises INT,
                        street2Raises INT,
                        street3Raises INT,
                        street4Raises INT)
                        """
        elif(self.dbname == 'SQLite'):
            self.query['createHudCacheTable'] = """ """

        if(self.dbname == 'MySQL InnoDB'):
            self.query['addTourneyIndex'] = """ALTER TABLE Tourneys ADD INDEX siteTourneyNo(siteTourneyNo)"""
        elif(self.dbname == 'PostgreSQL'):
            self.query['addTourneyIndex'] = """CREATE INDEX siteTourneyNo ON Tourneys (siteTourneyNo)"""
        elif(self.dbname == 'SQLite'):
            self.query['addHandsIndex'] = """ """

        if(self.dbname == 'MySQL InnoDB'):
            self.query['addHandsIndex'] = """ALTER TABLE Hands ADD INDEX siteHandNo(siteHandNo)"""
        elif(self.dbname == 'PostgreSQL'):
            self.query['addHandsIndex'] = """CREATE INDEX siteHandNo ON Hands (siteHandNo)"""
        elif(self.dbname == 'SQLite'):
            self.query['addHandsIndex'] = """ """

        if(self.dbname == 'MySQL InnoDB'):
            self.query['addPlayersIndex'] = """ALTER TABLE Players ADD INDEX name(name)"""
        elif(self.dbname == 'PostgreSQL'):
            self.query['addPlayersIndex'] = """CREATE INDEX name ON Players (name)"""
        elif(self.dbname == 'SQLite'):
            self.query['addPlayersIndex'] = """ """


        if(self.dbname == 'MySQL InnoDB' or self.dbname == 'PostgreSQL'):
            self.query['set tx level'] = """SET SESSION TRANSACTION
            ISOLATION LEVEL READ COMMITTED"""
        elif(self.dbname == 'SQLite'):
            self.query['set tx level'] = """ """

        ################################
        # Queries used in GuiGraphViewer
        ################################


        if(self.dbname == 'MySQL InnoDB') or (self.dbname == 'PostgreSQL'):
            self.query['getPlayerId'] = """SELECT id from Players where name = %s"""
        elif(self.dbname == 'SQLite'):
            self.query['getPlayerId'] = """SELECT id from Players where name = %s"""

        if(self.dbname == 'MySQL InnoDB') or (self.dbname == 'PostgreSQL'):
            self.query['getSiteId'] = """SELECT id from Sites where name = %s"""
        elif(self.dbname == 'SQLite'):
            self.query['getSiteId'] = """SELECT id from Sites where name = %s"""

        if(self.dbname == 'MySQL InnoDB') or (self.dbname == 'PostgreSQL') or (self.dbname == 'SQLite'):
            self.query['getRingProfitAllHandsPlayerIdSite'] = """
                SELECT hp.handId, hp.totalProfit, hp.totalProfit, hp.totalProfit
                FROM HandsPlayers hp
                INNER JOIN Players pl      ON hp.playerId     = pl.id
                INNER JOIN Hands h         ON h.id            = hp.handId
                INNER JOIN Gametypes g     ON h.gametypeId    = g.id
                where pl.id in <player_test>
                AND   pl.siteId in <site_test>
                AND   h.handStart > '<startdate_test>'
                AND   h.handStart < '<enddate_test>'
                AND   g.bigBlind in <limit_test>
                AND   hp.tourneysPlayersId IS NULL
                GROUP BY h.handStart, hp.handId, hp.totalProfit
                ORDER BY h.handStart"""

        if(self.dbname == 'MySQL InnoDB') or (self.dbname == 'PostgreSQL')  or (self.dbname == 'SQLite'):
            self.query['getGames'] = """SELECT DISTINCT category from Gametypes"""
        
        if(self.dbname == 'MySQL InnoDB') or (self.dbname == 'PostgreSQL')  or (self.dbname == 'SQLite'):
            self.query['getLimits'] = """SELECT DISTINCT bigBlind from Gametypes ORDER by bigBlind DESC"""


        ####################################
        # Queries to rebuild/modify hudcache
        ####################################
        
        if(self.dbname == 'MySQL InnoDB') or (self.dbname == 'PostgreSQL')  or (self.dbname == 'SQLite'):
            self.query['clearHudCache'] = """DELETE FROM HudCache"""
        
        if(self.dbname == 'MySQL InnoDB') or (self.dbname == 'PostgreSQL')  or (self.dbname == 'SQLite'):
            self.query['rebuildHudCache'] = """
                INSERT INTO HudCache
                (gametypeId
                ,playerId
                ,activeSeats
                ,position
                ,tourneyTypeId
                ,styleKey
                ,HDs
                ,wonWhenSeenStreet1
                ,wonAtSD
                ,street0VPI
                ,street0Aggr
                ,street0_3BChance
                ,street0_3BDone
                ,street1Seen
                ,street2Seen
                ,street3Seen
                ,street4Seen
                ,sawShowdown
                ,street1Aggr
                ,street2Aggr
                ,street3Aggr
                ,street4Aggr
                ,otherRaisedStreet1
                ,otherRaisedStreet2
                ,otherRaisedStreet3
                ,otherRaisedStreet4
                ,foldToOtherRaisedStreet1
                ,foldToOtherRaisedStreet2
                ,foldToOtherRaisedStreet3
                ,foldToOtherRaisedStreet4
                ,stealAttemptChance
                ,stealAttempted
                ,foldBbToStealChance
                ,foldedBbToSteal
                ,foldSbToStealChance
                ,foldedSbToSteal
                ,street1CBChance
                ,street1CBDone
                ,street2CBChance
                ,street2CBDone
                ,street3CBChance
                ,street3CBDone
                ,street4CBChance
                ,street4CBDone
                ,foldToStreet1CBChance
                ,foldToStreet1CBDone
                ,foldToStreet2CBChance
                ,foldToStreet2CBDone
                ,foldToStreet3CBChance
                ,foldToStreet3CBDone
                ,foldToStreet4CBChance
                ,foldToStreet4CBDone
                ,totalProfit
                ,street1CheckCallRaiseChance
                ,street1CheckCallRaiseDone
                ,street2CheckCallRaiseChance
                ,street2CheckCallRaiseDone
                ,street3CheckCallRaiseChance
                ,street3CheckCallRaiseDone
                ,street4CheckCallRaiseChance
                ,street4CheckCallRaiseDone
                )
                SELECT h.gametypeId
                      ,hp.playerId
                      ,h.seats
                      ,case when hp.position = 'B' then 'B'
                            when hp.position = 'S' then 'S'
                            when hp.position = '0' then 'D'
                            when hp.position = '1' then 'C'
                            when hp.position = '2' then 'M'
                            when hp.position = '3' then 'M'
                            when hp.position = '4' then 'M'
                            when hp.position = '5' then 'E'
                            when hp.position = '6' then 'E'
                            when hp.position = '7' then 'E'
                            when hp.position = '8' then 'E'
                            when hp.position = '9' then 'E'
                            else 'E'
                       end                                            AS hc_position
                      ,hp.tourneyTypeId
                      ,date_format(h.handStart, 'd%y%m%d')
                      ,count(1)
                      ,sum(wonWhenSeenStreet1)
                      ,sum(wonAtSD)
                      ,sum(CAST(street0VPI as integer)) 
                      ,sum(CAST(street0Aggr as integer)) 
                      ,sum(CAST(street0_3BChance as integer)) 
                      ,sum(CAST(street0_3BDone as integer)) 
                      ,sum(CAST(street1Seen as integer)) 
                      ,sum(CAST(street2Seen as integer)) 
                      ,sum(CAST(street3Seen as integer)) 
                      ,sum(CAST(street4Seen as integer)) 
                      ,sum(CAST(sawShowdown as integer)) 
                      ,sum(CAST(street1Aggr as integer)) 
                      ,sum(CAST(street2Aggr as integer)) 
                      ,sum(CAST(street3Aggr as integer)) 
                      ,sum(CAST(street4Aggr as integer)) 
                      ,sum(CAST(otherRaisedStreet1 as integer)) 
                      ,sum(CAST(otherRaisedStreet2 as integer)) 
                      ,sum(CAST(otherRaisedStreet3 as integer)) 
                      ,sum(CAST(otherRaisedStreet4 as integer)) 
                      ,sum(CAST(foldToOtherRaisedStreet1 as integer)) 
                      ,sum(CAST(foldToOtherRaisedStreet2 as integer)) 
                      ,sum(CAST(foldToOtherRaisedStreet3 as integer)) 
                      ,sum(CAST(foldToOtherRaisedStreet4 as integer)) 
                      ,sum(CAST(stealAttemptChance as integer)) 
                      ,sum(CAST(stealAttempted as integer)) 
                      ,sum(CAST(foldBbToStealChance as integer)) 
                      ,sum(CAST(foldedBbToSteal as integer)) 
                      ,sum(CAST(foldSbToStealChance as integer)) 
                      ,sum(CAST(foldedSbToSteal as integer)) 
                      ,sum(CAST(street1CBChance as integer)) 
                      ,sum(CAST(street1CBDone as integer)) 
                      ,sum(CAST(street2CBChance as integer)) 
                      ,sum(CAST(street2CBDone as integer)) 
                      ,sum(CAST(street3CBChance as integer)) 
                      ,sum(CAST(street3CBDone as integer)) 
                      ,sum(CAST(street4CBChance as integer)) 
                      ,sum(CAST(street4CBDone as integer)) 
                      ,sum(CAST(foldToStreet1CBChance as integer)) 
                      ,sum(CAST(foldToStreet1CBDone as integer)) 
                      ,sum(CAST(foldToStreet2CBChance as integer)) 
                      ,sum(CAST(foldToStreet2CBDone as integer)) 
                      ,sum(CAST(foldToStreet3CBChance as integer)) 
                      ,sum(CAST(foldToStreet3CBDone as integer)) 
                      ,sum(CAST(foldToStreet4CBChance as integer)) 
                      ,sum(CAST(foldToStreet4CBDone as integer)) 
                      ,sum(CAST(totalProfit as integer)) 
                      ,sum(CAST(street1CheckCallRaiseChance as integer)) 
                      ,sum(CAST(street1CheckCallRaiseDone as integer)) 
                      ,sum(CAST(street2CheckCallRaiseChance as integer)) 
                      ,sum(CAST(street2CheckCallRaiseDone as integer)) 
                      ,sum(CAST(street3CheckCallRaiseChance as integer)) 
                      ,sum(CAST(street3CheckCallRaiseDone as integer)) 
                      ,sum(CAST(street4CheckCallRaiseChance as integer)) 
                      ,sum(CAST(street4CheckCallRaiseDone as integer)) 
                FROM HandsPlayers hp
                INNER JOIN Hands h ON (h.id = hp.handId)
                GROUP BY h.gametypeId
                        ,hp.playerId
                        ,h.seats
                        ,hc_position
                        ,hp.tourneyTypeId
                        ,date_format(h.handStart, 'd%y%m%d')
"""
        elif (self.dbname == 'PostgreSQL')  or (self.dbname == 'SQLite'):
            self.query['rebuildHudCache'] = """
                INSERT INTO HudCache
                (gametypeId
                ,playerId
                ,activeSeats
                ,position
                ,tourneyTypeId
                ,styleKey
                ,HDs
                ,wonWhenSeenStreet1
                ,wonAtSD
                ,street0VPI
                ,street0Aggr
                ,street0_3BChance
                ,street0_3BDone
                ,street1Seen
                ,street2Seen
                ,street3Seen
                ,street4Seen
                ,sawShowdown
                ,street1Aggr
                ,street2Aggr
                ,street3Aggr
                ,street4Aggr
                ,otherRaisedStreet1
                ,otherRaisedStreet2
                ,otherRaisedStreet3
                ,otherRaisedStreet4
                ,foldToOtherRaisedStreet1
                ,foldToOtherRaisedStreet2
                ,foldToOtherRaisedStreet3
                ,foldToOtherRaisedStreet4
                ,stealAttemptChance
                ,stealAttempted
                ,foldBbToStealChance
                ,foldedBbToSteal
                ,foldSbToStealChance
                ,foldedSbToSteal
                ,street1CBChance
                ,street1CBDone
                ,street2CBChance
                ,street2CBDone
                ,street3CBChance
                ,street3CBDone
                ,street4CBChance
                ,street4CBDone
                ,foldToStreet1CBChance
                ,foldToStreet1CBDone
                ,foldToStreet2CBChance
                ,foldToStreet2CBDone
                ,foldToStreet3CBChance
                ,foldToStreet3CBDone
                ,foldToStreet4CBChance
                ,foldToStreet4CBDone
                ,totalProfit
                ,street1CheckCallRaiseChance
                ,street1CheckCallRaiseDone
                ,street2CheckCallRaiseChance
                ,street2CheckCallRaiseDone
                ,street3CheckCallRaiseChance
                ,street3CheckCallRaiseDone
                ,street4CheckCallRaiseChance
                ,street4CheckCallRaiseDone
                )
                SELECT h.gametypeId
                      ,hp.playerId
                      ,h.seats
                      ,case when hp.position = 'B' then 'B'
                            when hp.position = 'S' then 'S'
                            when hp.position = '0' then 'D'
                            when hp.position = '1' then 'C'
                            when hp.position = '2' then 'M'
                            when hp.position = '3' then 'M'
                            when hp.position = '4' then 'M'
                            when hp.position = '5' then 'E'
                            when hp.position = '6' then 'E'
                            when hp.position = '7' then 'E'
                            when hp.position = '8' then 'E'
                            when hp.position = '9' then 'E'
                            else 'E'
                       end                                            AS hc_position
                      ,hp.tourneyTypeId
                      ,'d' || to_char(h.handStart, 'YYMMDD')
                      ,count(1)
                      ,sum(wonWhenSeenStreet1)
                      ,sum(wonAtSD)
                      ,sum(CAST(street0VPI as integer)) 
                      ,sum(CAST(street0Aggr as integer)) 
                      ,sum(CAST(street0_3BChance as integer)) 
                      ,sum(CAST(street0_3BDone as integer)) 
                      ,sum(CAST(street1Seen as integer)) 
                      ,sum(CAST(street2Seen as integer)) 
                      ,sum(CAST(street3Seen as integer)) 
                      ,sum(CAST(street4Seen as integer)) 
                      ,sum(CAST(sawShowdown as integer)) 
                      ,sum(CAST(street1Aggr as integer)) 
                      ,sum(CAST(street2Aggr as integer)) 
                      ,sum(CAST(street3Aggr as integer)) 
                      ,sum(CAST(street4Aggr as integer)) 
                      ,sum(CAST(otherRaisedStreet1 as integer)) 
                      ,sum(CAST(otherRaisedStreet2 as integer)) 
                      ,sum(CAST(otherRaisedStreet3 as integer)) 
                      ,sum(CAST(otherRaisedStreet4 as integer)) 
                      ,sum(CAST(foldToOtherRaisedStreet1 as integer)) 
                      ,sum(CAST(foldToOtherRaisedStreet2 as integer)) 
                      ,sum(CAST(foldToOtherRaisedStreet3 as integer)) 
                      ,sum(CAST(foldToOtherRaisedStreet4 as integer)) 
                      ,sum(CAST(stealAttemptChance as integer)) 
                      ,sum(CAST(stealAttempted as integer)) 
                      ,sum(CAST(foldBbToStealChance as integer)) 
                      ,sum(CAST(foldedBbToSteal as integer)) 
                      ,sum(CAST(foldSbToStealChance as integer)) 
                      ,sum(CAST(foldedSbToSteal as integer)) 
                      ,sum(CAST(street1CBChance as integer)) 
                      ,sum(CAST(street1CBDone as integer)) 
                      ,sum(CAST(street2CBChance as integer)) 
                      ,sum(CAST(street2CBDone as integer)) 
                      ,sum(CAST(street3CBChance as integer)) 
                      ,sum(CAST(street3CBDone as integer)) 
                      ,sum(CAST(street4CBChance as integer)) 
                      ,sum(CAST(street4CBDone as integer)) 
                      ,sum(CAST(foldToStreet1CBChance as integer)) 
                      ,sum(CAST(foldToStreet1CBDone as integer)) 
                      ,sum(CAST(foldToStreet2CBChance as integer)) 
                      ,sum(CAST(foldToStreet2CBDone as integer)) 
                      ,sum(CAST(foldToStreet3CBChance as integer)) 
                      ,sum(CAST(foldToStreet3CBDone as integer)) 
                      ,sum(CAST(foldToStreet4CBChance as integer)) 
                      ,sum(CAST(foldToStreet4CBDone as integer)) 
                      ,sum(CAST(totalProfit as integer)) 
                      ,sum(CAST(street1CheckCallRaiseChance as integer)) 
                      ,sum(CAST(street1CheckCallRaiseDone as integer)) 
                      ,sum(CAST(street2CheckCallRaiseChance as integer)) 
                      ,sum(CAST(street2CheckCallRaiseDone as integer)) 
                      ,sum(CAST(street3CheckCallRaiseChance as integer)) 
                      ,sum(CAST(street3CheckCallRaiseDone as integer)) 
                      ,sum(CAST(street4CheckCallRaiseChance as integer)) 
                      ,sum(CAST(street4CheckCallRaiseDone as integer)) 
                FROM HandsPlayers hp
                INNER JOIN Hands h ON (h.id = hp.handId)
                GROUP BY h.gametypeId
                        ,hp.playerId
                        ,h.seats
                        ,hc_position
                        ,hp.tourneyTypeId
                        ,to_char(h.handStart, 'YYMMDD')
"""


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
