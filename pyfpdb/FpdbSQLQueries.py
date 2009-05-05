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
            self.query['list_tables'] = """ """

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
                        #Probably doesn't work.
            self.query['createSettingsTable'] = """ """


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
            self.query['createSitesTable'] = """ """


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
            self.query['createGametypesTable'] = """ """


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
            self.query['createPlayersTable'] = """ """


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
                            seats SMALLINT NOT NULL,
                            maxSeats SMALLINT NOT NULL,
                            comment TEXT,
                            commentTs DATETIME)
                        ENGINE=INNODB""" 
        elif(self.dbname == 'PostgreSQL'):
            self.query['createHandsTable'] = """CREATE TABLE Hands (
                        id BIGSERIAL, PRIMARY KEY (id),
                        tableName VARCHAR(20),
                        siteHandNo BIGINT,
                        gametypeId INT, FOREIGN KEY (gametypeId) REFERENCES Gametypes(id),
                        handStart timestamp without time zone,
                        importTime timestamp without time zone,
                        seats SMALLINT,
                        maxSeats SMALLINT,
                        comment TEXT,
                        commentTs timestamp without time zone)"""
        elif(self.dbname == 'SQLite'):
            self.query['createHandsTable'] = """ """


        ################################
        # Create Gametypes
        ################################

        if(self.dbname == 'MySQL InnoDB'):
            self.query['createBoardCardsTable'] = """CREATE TABLE BoardCards (
                            id BIGINT UNSIGNED AUTO_INCREMENT NOT NULL, PRIMARY KEY (id),
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
                            card5Suit char(1) NOT NULL)
                        ENGINE=INNODB""" 
        elif(self.dbname == 'PostgreSQL'):
            self.query['createBoardCardsTable'] = """CREATE TABLE BoardCards (
                        id BIGSERIAL, PRIMARY KEY (id),
                        handId BIGINT, FOREIGN KEY (handId) REFERENCES Hands(id),
                        card1Value smallint,
                        card1Suit char(1),
                        card2Value smallint,
                        card2Suit char(1),
                        card3Value smallint,
                        card3Suit char(1),
                        card4Value smallint,
                        card4Suit char(1),
                        card5Value smallint,
                        card5Suit char(1))"""
        elif(self.dbname == 'SQLite'):
            self.query['createBoardCardsTable'] = """ """


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
            self.query['createTourneysTable'] = """ """

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
                    
                        tourneysPlayersId BIGINT UNSIGNED, FOREIGN KEY (tourneysPlayersId) REFERENCES TourneysPlayers(id))
                        ENGINE=INNODB"""
        elif(self.dbname == 'PostgreSQL'):
            self.query['createHandsPlayersTable'] = """CREATE TABLE HandsPlayers (
                        id BIGSERIAL, PRIMARY KEY (id),
                        handId BIGINT, FOREIGN KEY (handId) REFERENCES Hands(id),
                        playerId INT, FOREIGN KEY (playerId) REFERENCES Players(id),
                        startCash INT,
                        position CHAR(1),
                        seatNo SMALLINT,
                        ante INT,

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
                        commentTs timestamp without time zone,
                        tourneysPlayersId BIGINT, FOREIGN KEY (tourneysPlayersId) REFERENCES TourneysPlayers(id))"""
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
                        handPlayerId BIGINT UNSIGNED NOT NULL, FOREIGN KEY (handPlayerId) REFERENCES HandsPlayers(id),
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
                        handPlayerId BIGINT, FOREIGN KEY (handPlayerId) REFERENCES HandsPlayers(id),
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
                        street4CheckCallRaiseDone INT NOT NULL)
                        ENGINE=INNODB"""
        elif(self.dbname == 'PostgreSQL'):
            self.query['createHudCacheTable'] = """CREATE TABLE HudCache (
                        id BIGSERIAL, PRIMARY KEY (id),
                        gametypeId INT, FOREIGN KEY (gametypeId) REFERENCES Gametypes(id),
                        playerId INT, FOREIGN KEY (playerId) REFERENCES Players(id),
                        activeSeats SMALLINT,
                        position CHAR(1),
                        tourneyTypeId INT, FOREIGN KEY (tourneyTypeId) REFERENCES TourneyTypes(id),

                        HDs INT,
                        street0VPI INT,
                        street0Aggr INT,
                        street0_3B4BChance INT,
                        street0_3B4BDone INT,
                        street1Seen INT,
                        street2Seen INT,
                        street3Seen INT,
                        street4Seen INT,
                        sawShowdown INT,
                        street1Aggr INT,
                        street2Aggr INT,
                        street3Aggr INT,
                        street4Aggr INT,
                        otherRaisedStreet1 INT,
                        otherRaisedStreet2 INT,
                        otherRaisedStreet3 INT,
                        otherRaisedStreet4 INT,
                        foldToOtherRaisedStreet1 INT,
                        foldToOtherRaisedStreet2 INT,
                        foldToOtherRaisedStreet3 INT,
                        foldToOtherRaisedStreet4 INT,
                        wonWhenSeenStreet1 FLOAT,
                        wonAtSD FLOAT,

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
                        street4CheckCallRaiseDone INT)"""
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
                SELECT hp.handId, hp.winnings, coalesce(hp.ante,0) + SUM(ha.amount)
                     , hp.winnings - (coalesce(hp.ante,0) + SUM(ha.amount))
                FROM HandsPlayers hp
                INNER JOIN Players pl      ON hp.playerId     = pl.id
                INNER JOIN Hands h         ON h.id            = hp.handId
                INNER JOIN HandsActions ha ON ha.handPlayerId = hp.id
                INNER JOIN Gametypes g     ON h.gametypeId    = g.id
                where pl.id in <player_test>
                AND   pl.siteId in <site_test>
                AND   h.handStart > '<startdate_test>'
                AND   h.handStart < '<enddate_test>'
                AND   g.bigBlind in <limit_test>
                AND   hp.tourneysPlayersId IS NULL
                GROUP BY hp.handId, hp.winnings, h.handStart, hp.ante
                ORDER BY h.handStart"""

        if(self.dbname == 'MySQL InnoDB'):
            self.query['playerStats'] = """
                SELECT 
                      concat(upper(stats.limitType), ' '
                            ,concat(upper(substring(stats.category,1,1)),substring(stats.category,2) ), ' '
                            ,stats.name, ' $'
                            ,cast(stats.bigBlindDesc as char)
                            )                                                      AS Game
                     ,stats.n
                     ,stats.vpip
                     ,stats.pfr
                     ,stats.pf3
                     ,stats.steals
                     ,stats.saw_f
                     ,stats.sawsd
                     ,stats.wtsdwsf
                     ,stats.wmsd
                     ,stats.FlAFq
                     ,stats.TuAFq
                     ,stats.RvAFq
                     ,stats.PoFAFq
                     ,stats.Net
                     ,stats.BBper100
                     ,stats.Profitperhand
                     ,case when hprof2.variance = -999 then '-'
                           else format(hprof2.variance, 2)
                      end                                                          AS Variance
                FROM
                    (select /* stats from hudcache */
                            gt.base
                           ,gt.category
                           ,upper(gt.limitType) as limitType
                           ,s.name
                           ,<selectgt.bigBlind>                                             AS bigBlindDesc
                           ,<hcgametypeId>                                                  AS gtId
                           ,sum(HDs)                                                        AS n
                           ,format(100.0*sum(street0VPI)/sum(HDs),1)                        AS vpip
                           ,format(100.0*sum(street0Aggr)/sum(HDs),1)                       AS pfr
                           ,case when sum(street0_3b4bchance) = 0 then '0'
                                 else format(100.0*sum(street0_3b4bdone)/sum(street0_3b4bchance),1)
                            end                                                             AS pf3
                           ,case when sum(stealattemptchance) = 0 then '-'
                                 else format(100.0*sum(stealattempted)/sum(stealattemptchance),1)
                            end                                                             AS steals
                           ,format(100.0*sum(street1Seen)/sum(HDs),1)                       AS saw_f
                           ,format(100.0*sum(sawShowdown)/sum(HDs),1)                       AS sawsd
                           ,case when sum(street1Seen) = 0 then '-'
                                 else format(100.0*sum(sawShowdown)/sum(street1Seen),1)
                            end                                                             AS wtsdwsf
                           ,case when sum(sawShowdown) = 0 then '-'
                                 else format(100.0*sum(wonAtSD)/sum(sawShowdown),1)
                            end                                                             AS wmsd
                           ,case when sum(street1Seen) = 0 then '-'
                                 else format(100.0*sum(street1Aggr)/sum(street1Seen),1)
                            end                                                             AS FlAFq
                           ,case when sum(street2Seen) = 0 then '-'
                                 else format(100.0*sum(street2Aggr)/sum(street2Seen),1)
                            end                                                             AS TuAFq
                           ,case when sum(street3Seen) = 0 then '-'
                                else format(100.0*sum(street3Aggr)/sum(street3Seen),1)
                            end                                                             AS RvAFq
                           ,case when sum(street1Seen)+sum(street2Seen)+sum(street3Seen) = 0 then '-'
                                else format(100.0*(sum(street1Aggr)+sum(street2Aggr)+sum(street3Aggr))
                                         /(sum(street1Seen)+sum(street2Seen)+sum(street3Seen)),1)
                            end                                                             AS PoFAFq
                           ,format(sum(totalProfit)/100.0,2)                                AS Net
                           ,format((sum(totalProfit/(gt.bigBlind+0.0))) / (sum(HDs)/100.0),2)
                                                                                            AS BBper100
                           ,format( (sum(totalProfit)/100.0) / sum(HDs), 4)                 AS Profitperhand
                     from Gametypes gt
                          inner join Sites s on s.Id = gt.siteId
                          inner join HudCache hc on hc.gameTypeId = gt.Id
                     where hc.playerId in <player_test>
                     and   <gtbigBlind_test>
                     group by gt.base
                          ,gt.category
                          ,upper(gt.limitType)
                          ,s.name
                          <groupbygt.bigBlind>
                          ,gtId
                    ) stats
                inner join
                    ( select # profit from handsplayers/handsactions
                             hprof.gtId, sum(hprof.profit) sum_profit,
                             avg(hprof.profit/100.0) profitperhand,
                             case when hprof.gtId = -1 then -999
                                  else variance(hprof.profit/100.0)
                             end as variance
                      from
                          (select hp.handId, <hgameTypeId> as gtId, hp.winnings, SUM(ha.amount) as costs
                                , hp.winnings - SUM(ha.amount) as profit
                           from HandsPlayers hp
                           inner join Hands h        ON h.id            = hp.handId
                           left join HandsActions ha ON ha.handPlayerId = hp.id
                           where hp.playerId in <player_test>
                           and   hp.tourneysPlayersId IS NULL
                           group by hp.handId, gtId, hp.position, hp.winnings
                          ) hprof
                      group by hprof.gtId
                     ) hprof2
                    on hprof2.gtId = stats.gtId
                order by stats.category, stats.limittype, stats.bigBlindDesc"""
        elif(self.dbname == 'PostgreSQL'):
            self.query['playerStats'] = """
                SELECT upper(stats.limitType) || ' '
                       || initcap(stats.category) || ' '
                       || stats.name || ' $'
                       || stats.bigBlindDesc                                          AS Game
                      ,stats.n
                      ,stats.vpip
                      ,stats.pfr
                      ,stats.pf3
                      ,stats.steals
                      ,stats.saw_f
                      ,stats.sawsd
                      ,stats.wtsdwsf
                      ,stats.wmsd
                      ,stats.FlAFq
                      ,stats.TuAFq
                      ,stats.RvAFq
                      ,stats.PoFAFq
                      ,stats.Net
                      ,stats.BBper100
                      ,stats.Profitperhand
                      ,case when hprof2.variance = -999 then '-'
                            else to_char(hprof2.variance, '0D00')
                       end                                                          AS Variance
                FROM
                    (select gt.base
                           ,gt.category
                           ,upper(gt.limitType)                                             AS limitType
                           ,s.name
                           ,<selectgt.bigBlind>                                             AS bigBlindDesc
                           ,<hcgametypeId>                                                  AS gtId
                           ,sum(HDs) as n
                           ,to_char(100.0*sum(street0VPI)/sum(HDs),'90D0')                  AS vpip
                           ,to_char(100.0*sum(street0Aggr)/sum(HDs),'90D0')                 AS pfr
                           ,case when sum(street0_3b4bchance) = 0 then '0'
                                 else to_char(100.0*sum(street0_3b4bdone)/sum(street0_3b4bchance),'90D0')
                            end                                                             AS pf3
                           ,case when sum(stealattemptchance) = 0 then '-'
                                 else to_char(100.0*sum(stealattempted)/sum(stealattemptchance),'90D0')
                            end                                                             AS steals
                           ,to_char(100.0*sum(street1Seen)/sum(HDs),'90D0')                 AS saw_f
                           ,to_char(100.0*sum(sawShowdown)/sum(HDs),'90D0')                 AS sawsd
                           ,case when sum(street1Seen) = 0 then '-'
                                 else to_char(100.0*sum(sawShowdown)/sum(street1Seen),'90D0')
                            end                                                             AS wtsdwsf
                           ,case when sum(sawShowdown) = 0 then '-'
                                 else to_char(100.0*sum(wonAtSD)/sum(sawShowdown),'90D0')
                            end                                                             AS wmsd
                           ,case when sum(street1Seen) = 0 then '-'
                                 else to_char(100.0*sum(street1Aggr)/sum(street1Seen),'90D0')
                            end                                                             AS FlAFq
                           ,case when sum(street2Seen) = 0 then '-'
                                 else to_char(100.0*sum(street2Aggr)/sum(street2Seen),'90D0')
                            end                                                             AS TuAFq
                           ,case when sum(street3Seen) = 0 then '-'
                                else to_char(100.0*sum(street3Aggr)/sum(street3Seen),'90D0')
                            end                                                             AS RvAFq
                           ,case when sum(street1Seen)+sum(street2Seen)+sum(street3Seen) = 0 then '-'
                                else to_char(100.0*(sum(street1Aggr)+sum(street2Aggr)+sum(street3Aggr))
                                         /(sum(street1Seen)+sum(street2Seen)+sum(street3Seen)),'90D0')
                            end                                                             AS PoFAFq
                           ,round(sum(totalProfit)/100.0,2)                                 AS Net
                           ,to_char((sum(totalProfit/(gt.bigBlind+0.0))) / (sum(HDs)/100.0), '990D00')
                                                                                            AS BBper100
                           ,to_char(sum(totalProfit/100.0) / (sum(HDs)+0.0), '990D0000')    AS Profitperhand
                     from Gametypes gt
                          inner join Sites s on s.Id = gt.siteId
                          inner join HudCache hc on hc.gameTypeId = gt.Id
                     where hc.playerId in <player_test>
                     and   <gtbigBlind_test>
                     group by gt.base
                          ,gt.category
                          ,upper(gt.limitType)
                          ,s.name
                          <groupbygt.bigBlind>
                          ,gtId
                    ) stats
                inner join
                    ( select
                             hprof.gtId, sum(hprof.profit) AS sum_profit,
                             avg(hprof.profit/100.0) AS profitperhand,
                             case when hprof.gtId = -1 then -999
                                  else variance(hprof.profit/100.0)
                             end as variance
                      from
                          (select hp.handId, <hgameTypeId> as gtId, hp.winnings,
                                  SUM(ha.amount) as costs, hp.winnings - SUM(ha.amount) as profit
                           from HandsPlayers hp
                           inner join Hands h        ON (h.id            = hp.handId)
                           left join HandsActions ha ON (ha.handPlayerId = hp.id)
                           where hp.playerId in <player_test>
                           and   hp.tourneysPlayersId IS NULL
                           group by hp.handId, gtId, hp.position, hp.winnings
                          ) hprof
                      group by hprof.gtId
                     ) hprof2
                    on hprof2.gtId = stats.gtId
                order by stats.base, stats.limittype, stats.bigBlindDesc"""
        elif(self.dbname == 'SQLite'):
            self.query['playerStats'] = """ """

        if(self.dbname == 'MySQL InnoDB'):
            self.query['playerStatsByPosition'] = """
                SELECT 
                      concat(upper(stats.limitType), ' '
                            ,concat(upper(substring(stats.category,1,1)),substring(stats.category,2) ), ' '
                            ,stats.name, ' $'
                            ,cast(stats.bigBlindDesc as char)
                            )                                                      AS Game
                     ,case when stats.PlPosition = -2 then 'BB'
                           when stats.PlPosition = -1 then 'SB'
                           when stats.PlPosition =  0 then 'Btn'
                           when stats.PlPosition =  1 then 'CO'
                           when stats.PlPosition =  2 then 'MP'
                           when stats.PlPosition =  5 then 'EP'
                           else '??'
                      end                                                          AS PlPosition
                     ,stats.n
                     ,stats.vpip
                     ,stats.pfr
                     ,stats.pf3
                     ,stats.steals
                     ,stats.saw_f
                     ,stats.sawsd
                     ,stats.wtsdwsf
                     ,stats.wmsd
                     ,stats.FlAFq
                     ,stats.TuAFq
                     ,stats.RvAFq
                     ,stats.PoFAFq
                     ,stats.Net
                     ,stats.BBper100
                     ,stats.Profitperhand
                     ,case when hprof2.variance = -999 then '-'
                           else format(hprof2.variance, 2)
                      end                                                          AS Variance
                FROM
                    (select /* stats from hudcache */
                            gt.base
                           ,gt.category
                           ,upper(gt.limitType)                                             AS limitType
                           ,s.name
                           ,<selectgt.bigBlind>                                             AS bigBlindDesc
                           ,<hcgametypeId>                                                  AS gtId
                           ,case when hc.position = 'B' then -2
                                 when hc.position = 'S' then -1
                                 when hc.position = 'D' then  0
                                 when hc.position = 'C' then  1
                                 when hc.position = 'M' then  2
                                 when hc.position = 'E' then  5
                                 else 9
                            end                                                             as PlPosition
                           ,sum(HDs)                                                        AS n
                           ,format(100.0*sum(street0VPI)/sum(HDs),1)                        AS vpip
                           ,format(100.0*sum(street0Aggr)/sum(HDs),1)                       AS pfr
                           ,case when sum(street0_3b4bchance) = 0 then '0'
                                 else format(100.0*sum(street0_3b4bdone)/sum(street0_3b4bchance),1)
                            end                                                             AS pf3
                           ,case when sum(stealattemptchance) = 0 then '-'
                                 else format(100.0*sum(stealattempted)/sum(stealattemptchance),1)
                            end                                                             AS steals
                           ,format(100.0*sum(street1Seen)/sum(HDs),1)                       AS saw_f
                           ,format(100.0*sum(sawShowdown)/sum(HDs),1)                       AS sawsd
                           ,case when sum(street1Seen) = 0 then '-'
                                 else format(100.0*sum(sawShowdown)/sum(street1Seen),1)
                            end                                                             AS wtsdwsf
                           ,case when sum(sawShowdown) = 0 then '-'
                                 else format(100.0*sum(wonAtSD)/sum(sawShowdown),1)
                            end                                                             AS wmsd
                           ,case when sum(street1Seen) = 0 then '-'
                                 else format(100.0*sum(street1Aggr)/sum(street1Seen),1)
                            end                                                             AS FlAFq
                           ,case when sum(street2Seen) = 0 then '-'
                                 else format(100.0*sum(street2Aggr)/sum(street2Seen),1)
                            end                                                             AS TuAFq
                           ,case when sum(street3Seen) = 0 then '-'
                                else format(100.0*sum(street3Aggr)/sum(street3Seen),1)
                            end                                                             AS RvAFq
                           ,case when sum(street1Seen)+sum(street2Seen)+sum(street3Seen) = 0 then '-'
                                else format(100.0*(sum(street1Aggr)+sum(street2Aggr)+sum(street3Aggr))
                                         /(sum(street1Seen)+sum(street2Seen)+sum(street3Seen)),1)
                            end                                                             AS PoFAFq
                           ,format(sum(totalProfit)/100.0,2)                                AS Net
                           ,format((sum(totalProfit/(gt.bigBlind+0.0))) / (sum(HDs)/100.0),2)
                                                                                            AS BBper100
                           ,format( (sum(totalProfit)/100.0) / sum(HDs), 4)                 AS Profitperhand
                     from Gametypes gt
                          inner join Sites s on s.Id = gt.siteId
                          inner join HudCache hc on hc.gameTypeId = gt.Id
                     where hc.playerId in <player_test>
                     and   <gtbigBlind_test>
                     group by gt.base
                          ,gt.category
                          ,upper(gt.limitType)
                          ,s.name
                          <groupbygt.bigBlind>
                          ,gtId
                          ,PlPosition
                    ) stats
                inner join
                    ( select # profit from handsplayers/handsactions
                             hprof.gtId, 
                             case when hprof.position = 'B' then -2
                                  when hprof.position = 'S' then -1
                                  when hprof.position in ('3','4') then 2
                                  when hprof.position in ('6','7') then 5
                                  else hprof.position
                             end                                      as PlPosition,
                             sum(hprof.profit) as sum_profit,
                             avg(hprof.profit/100.0) as profitperhand,
                             case when hprof.gtId = -1 then -999
                                  else variance(hprof.profit/100.0)
                             end as variance
                      from
                          (select hp.handId, <hgameTypeId> as gtId, hp.position, hp.winnings
                                , SUM(ha.amount) as costs, hp.winnings - SUM(ha.amount) as profit
                           from HandsPlayers hp
                           inner join Hands h        ON h.id            = hp.handId
                           left join HandsActions ha ON ha.handPlayerId = hp.id
                           where hp.playerId in <player_test>
                           and   hp.tourneysPlayersId IS NULL
                           group by hp.handId, gtId, hp.position, hp.winnings
                          ) hprof
                      group by hprof.gtId, PlPosition
                     ) hprof2
                    on (    hprof2.gtId = stats.gtId
                        and hprof2.PlPosition = stats.PlPosition)
                order by stats.category, stats.limitType, stats.bigBlindDesc, cast(stats.PlPosition as signed)
                """
        elif(self.dbname == 'PostgreSQL'):
            self.query['playerStatsByPosition'] = """
                select /* stats from hudcache */
                       upper(stats.limitType) || ' '
                       || upper(substr(stats.category,1,1)) || substr(stats.category,2) || ' '
                       || stats.name || ' $'
                       || stats.bigBlindDesc                                        AS Game
                      ,case when stats.PlPosition = -2 then 'BB'
                            when stats.PlPosition = -1 then 'SB'
                            when stats.PlPosition =  0 then 'Btn'
                            when stats.PlPosition =  1 then 'CO'
                            when stats.PlPosition =  2 then 'MP'
                            when stats.PlPosition =  5 then 'EP'
                            else '??'
                       end                                                          AS PlPosition
                      ,stats.n
                      ,stats.vpip
                      ,stats.pfr
                      ,stats.pf3
                      ,stats.steals
                      ,stats.saw_f
                      ,stats.sawsd
                      ,stats.wtsdwsf
                      ,stats.wmsd
                      ,stats.FlAFq
                      ,stats.TuAFq
                      ,stats.RvAFq
                      ,stats.PoFAFq
                      ,stats.Net
                      ,stats.BBper100
                      ,stats.Profitperhand
                      ,case when hprof2.variance = -999 then '-'
                            else to_char(hprof2.variance, '0D00')
                       end                                                          AS Variance
                FROM
                    (select /* stats from hudcache */
                            gt.base
                           ,gt.category
                           ,upper(gt.limitType)                                             AS limitType
                           ,s.name
                           ,<selectgt.bigBlind>                                             AS bigBlindDesc
                           ,<hcgametypeId>                                                  AS gtId
                           ,case when hc.position = 'B' then -2
                                 when hc.position = 'S' then -1
                                 when hc.position = 'D' then  0
                                 when hc.position = 'C' then  1
                                 when hc.position = 'M' then  2
                                 when hc.position = 'E' then  5
                                 else 9
                            end                                                             AS PlPosition
                           ,sum(HDs)                                                        AS n
                           ,to_char(round(100.0*sum(street0VPI)/sum(HDs)),'90D0')           AS vpip
                           ,to_char(round(100.0*sum(street0Aggr)/sum(HDs)),'90D0')          AS pfr
                           ,case when sum(street0_3b4bchance) = 0 then '0'
                                 else to_char(100.0*sum(street0_3b4bdone)/sum(street0_3b4bchance),'90D0')
                            end                                                             AS pf3
                           ,case when sum(stealattemptchance) = 0 then '-'
                                 else to_char(100.0*sum(stealattempted)/sum(stealattemptchance),'90D0')
                            end                                                             AS steals
                           ,to_char(round(100.0*sum(street1Seen)/sum(HDs)),'90D0')          AS saw_f
                           ,to_char(round(100.0*sum(sawShowdown)/sum(HDs)),'90D0')          AS sawsd
                           ,case when sum(street1Seen) = 0 then '-'
                                 else to_char(round(100.0*sum(sawShowdown)/sum(street1Seen)),'90D0')
                            end                                                             AS wtsdwsf
                           ,case when sum(sawShowdown) = 0 then '-'
                                 else to_char(round(100.0*sum(wonAtSD)/sum(sawShowdown)),'90D0')
                            end                                                             AS wmsd
                           ,case when sum(street1Seen) = 0 then '-'
                                 else to_char(round(100.0*sum(street1Aggr)/sum(street1Seen)),'90D0')
                            end                                                             AS FlAFq
                           ,case when sum(street2Seen) = 0 then '-'
                                 else to_char(round(100.0*sum(street2Aggr)/sum(street2Seen)),'90D0')
                            end                                                             AS TuAFq
                           ,case when sum(street3Seen) = 0 then '-'
                                else to_char(round(100.0*sum(street3Aggr)/sum(street3Seen)),'90D0')
                            end                                                             AS RvAFq
                           ,case when sum(street1Seen)+sum(street2Seen)+sum(street3Seen) = 0 then '-'
                                else to_char(round(100.0*(sum(street1Aggr)+sum(street2Aggr)+sum(street3Aggr))
                                         /(sum(street1Seen)+sum(street2Seen)+sum(street3Seen))),'90D0')
                            end                                                             AS PoFAFq
                           ,to_char(sum(totalProfit)/100.0,'9G999G990D00')                  AS Net
                           ,case when sum(HDs) = 0 then '0'
                                 else to_char(sum(totalProfit/(gt.bigBlind+0.0)) / (sum(HDs)/100.0), '990D00')
                            end                                                             AS BBper100
                           ,case when sum(HDs) = 0 then '0'
                                 else to_char( (sum(totalProfit)/100.0) / sum(HDs), '90D0000')
                            end                                                             AS Profitperhand
                     from Gametypes gt
                          inner join Sites s     on (s.Id = gt.siteId)
                          inner join HudCache hc on (hc.gameTypeId = gt.Id)
                     where hc.playerId in <player_test>
                     and   <gtbigBlind_test>
                     group by gt.base
                          ,gt.category
                          ,upper(gt.limitType)
                          ,s.name
                          <groupbygt.bigBlind>
                          ,gtId
                          ,PlPosition
                    ) stats
                inner join
                    ( select /* profit from handsplayers/handsactions */
                             hprof.gtId, 
                             case when hprof.position = 'B' then -2
                                  when hprof.position = 'S' then -1
                                  when hprof.position in ('3','4') then 2
                                  when hprof.position in ('6','7') then 5
                                  else cast(hprof.position as smallint)
                             end                                      as PlPosition,
                             sum(hprof.profit) as sum_profit,
                             avg(hprof.profit/100.0) as profitperhand,
                             case when hprof.gtId = -1 then -999
                                  else variance(hprof.profit/100.0)
                             end as variance
                      from
                          (select hp.handId, <hgameTypeId> as gtId, hp.position, hp.winnings
                                , SUM(ha.amount) as costs, hp.winnings - SUM(ha.amount) as profit
                           from HandsPlayers hp
                           inner join Hands h        ON h.id            = hp.handId
                           left join HandsActions ha ON ha.handPlayerId = hp.id
                           where hp.playerId in <player_test>
                           and   hp.tourneysPlayersId IS NULL
                           group by hp.handId, gameTypeId, hp.position, hp.winnings
                          ) hprof
                      group by hprof.gtId, PlPosition
                    ) hprof2
                    on (    hprof2.gtId = stats.gtId
                        and hprof2.PlPosition = stats.PlPosition)
                order by stats.category, stats.limitType, stats.bigBlindDesc, cast(stats.PlPosition as smallint)
                """
        elif(self.dbname == 'SQLite'):
            self.query['playerStatsByPosition'] = """ """

        if(self.dbname == 'MySQL InnoDB'):
            self.query['playerStatsByPositionAndHoleCards'] = """
                SELECT 
                      concat(upper(stats.limitType), ' '
                            ,concat(upper(substring(stats.category,1,1)),substring(stats.category,2) ), ' '
                            ,stats.name, ' $'
                            ,cast(trim(leading ' ' from
                                  case when stats.bigBlind < 100 then format(stats.bigBlind/100.0,2)
                                      else format(stats.bigBlind/100.0,0)
                                  end ) as char)
                            )                                                      AS Game
                     ,case when stats.PlPosition = -2 then 'BB'
                           when stats.PlPosition = -1 then 'SB'
                           when stats.PlPosition =  0 then 'Btn'
                           when stats.PlPosition =  1 then 'CO'
                           when stats.PlPosition =  2 then 'MP'
                           when stats.PlPosition =  5 then 'EP'
                           else '??'
                      end                                                          AS PlPosition
                     /*,stats.n*/,hprof2.n
                     /*,stats.vpip*/,0
                     /*,stats.pfr*/,0
                     /*,stats.saw_f*/,0
                     /*,stats.sawsd*/,0
                     /*,stats.wtsdwsf*/,0
                     /*,stats.wmsd*/,0
                     /*,stats.FlAFq*/,0
                     /*,stats.TuAFq*/,0
                     /*,stats.RvAFq*/,0
                     /*,stats.PoFAFq*/,0
                     /* if you have handsactions data the next 3 fields should give same answer as
                        following 3 commented out fields */
                     /*,stats.Net
                     ,stats.BBper100
                     ,stats.Profitperhand*/
                     ,format(hprof2.sum_profit/100.0,2)                          AS Net
                       /*,format((hprof2.sum_profit/(stats.bigBlind+0.0)) / (stats.n/100.0),2)*/,0
                                                                                   AS BBlPer100
                       ,hprof2.profitperhand                                       AS Profitperhand
                     ,format(hprof2.variance,2)                                    AS Variance
                FROM
                    (select /* stats from hudcache */
                            gt.base
                           ,gt.category
                           ,upper(gt.limitType) as limitType
                           ,s.name
                           ,gt.bigBlind
                           ,hc.gametypeId
                           ,case when hc.position = 'B' then -2
                                 when hc.position = 'S' then -1
                                 when hc.position = 'D' then  0
                                 when hc.position = 'C' then  1
                                 when hc.position = 'M' then  2
                                 when hc.position = 'E' then  5
                                 else 9
                            end                                                             as PlPosition
                           ,sum(HDs)                                                        AS n
                           ,format(100.0*sum(street0VPI)/sum(HDs),1)                 AS vpip
                           ,format(100.0*sum(street0Aggr)/sum(HDs),1)                AS pfr
                           ,format(100.0*sum(street1Seen)/sum(HDs),1)                AS saw_f
                           ,format(100.0*sum(sawShowdown)/sum(HDs),1)                AS sawsd
                           ,case when sum(street1Seen) = 0 then '-'
                                else format(100.0*sum(sawShowdown)/sum(street1Seen),1)
                            end                                                             AS wtsdwsf
                           ,case when sum(sawShowdown) = 0 then '-'
                           end                                                             AS wtsdwsf
                           ,case when sum(sawShowdown) = 0 then '-'
                                 else format(100.0*sum(wonAtSD)/sum(sawShowdown),1)
                            end                                                             AS wmsd
                           ,case when sum(street1Seen) = 0 then '-'
                                 else format(100.0*sum(street1Aggr)/sum(street1Seen),1)
                            end                                                             AS FlAFq
                           ,case when sum(street2Seen) = 0 then '-'
                                 else format(100.0*sum(street2Aggr)/sum(street2Seen),1)
                            end                                                             AS TuAFq
                           ,case when sum(street3Seen) = 0 then '-'
                                else format(100.0*sum(street3Aggr)/sum(street3Seen),1)
                            end                                                             AS RvAFq
                           ,case when sum(street1Seen)+sum(street2Seen)+sum(street3Seen) = 0 then '-'
                                else format(100.0*(sum(street1Aggr)+sum(street2Aggr)+sum(street3Aggr))
                                         /(sum(street1Seen)+sum(street2Seen)+sum(street3Seen)),1)
                            end                                                             AS PoFAFq
                           ,format(sum(totalProfit)/100.0,2)                                AS Net
                           ,format((sum(totalProfit)/(gt.bigBlind+0.0)) / (sum(HDs)/100.0),2)
                                                                                            AS BBper100
                           ,format( (sum(totalProfit)/100.0) / sum(HDs), 4)                 AS Profitperhand
                     from Gametypes gt
                          inner join Sites s on s.Id = gt.siteId
                          inner join HudCache hc on hc.gameTypeId = gt.Id
                     where hc.playerId in <player_test>
                                                # use <gametype_test> here ?
                     group by gt.base
                          ,gt.category
                          ,upper(gt.limitType)
                          ,s.name
                          ,gt.bigBlind
                          ,hc.gametypeId
                          ,PlPosition
                    ) stats
                inner join
                    ( select # profit from handsplayers/handsactions
                             hprof.gameTypeId, 
                             case when hprof.position = 'B' then -2
                                  when hprof.position = 'S' then -1
                                  when hprof.position in ('3','4') then 2
                                  when hprof.position in ('6','7') then 5
                                  else hprof.position
                             end                                      as PlPosition,
                             sum(hprof.profit) as sum_profit,
                             avg(hprof.profit/100.0) as profitperhand,
                             variance(hprof.profit/100.0) as variance,
                             count(*) as n
                      from
                          (select hp.handId, h.gameTypeId, hp.position, hp.winnings, SUM(ha.amount) as costs
                                , hp.winnings - SUM(ha.amount) as profit
                          from HandsPlayers hp
                          inner join Hands h        ON h.id            = hp.handId
                          left join HandsActions ha ON ha.handPlayerId = hp.id
                          where hp.playerId in <player_test>
                                                     # use <gametype_test> here ?
                          and   hp.tourneysPlayersId IS NULL
                          and ((hp.card1Value = <first_card> and hp.card2Value = <second_card>) or (hp.card1Value = <second_card> and hp.card2Value = <first_card>))
                          group by hp.handId, h.gameTypeId, hp.position, hp.winnings
                         ) hprof
                      group by hprof.gameTypeId, PlPosition
                     ) hprof2
                    on (    hprof2.gameTypeId = stats.gameTypeId
                        and hprof2.PlPosition = stats.PlPosition)
                order by stats.category, stats.limittype, stats.bigBlind, cast(stats.PlPosition as signed)
                """
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
