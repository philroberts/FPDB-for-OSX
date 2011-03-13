#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Copyright 2009-2011 Grigorij Indigirkin
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

"""@package AlchemyTables
Contains all sqlalchemy tables
"""

#TODO: gettextify if file is used again

from sqlalchemy import Table, Float, Column, Integer, String, MetaData, \
        ForeignKey, Boolean, SmallInteger, DateTime, Text, Index, CHAR, \
        PickleType, Unicode

from AlchemyFacilities import CardColumn, MoneyColumn, BigIntColumn


metadata = MetaData()


autorates_table = Table('Autorates', metadata,
    Column('id',             Integer, primary_key=True, nullable=False),
    Column('playerId',       Integer, ForeignKey("Players.id"), nullable=False), 
    Column('gametypeId',     SmallInteger, ForeignKey("Gametypes.id"), nullable=False), 
    Column('description',    String(50), nullable=False), 
    Column('shortDesc',      CHAR(8), nullable=False), 
    Column('ratingTime',     DateTime, nullable=False), 
    Column('handCount',      Integer, nullable=False), 
    mysql_charset='utf8',
    mysql_engine='InnoDB',
)


gametypes_table = Table('Gametypes', metadata,
    Column('id',            SmallInteger, primary_key=True),
    Column('siteId',        SmallInteger, ForeignKey("Sites.id"), nullable=False), # SMALLINT
    Column('currency',      String(4), nullable=False), # varchar(4) NOT NULL
    Column('type',          String(4), nullable=False), # char(4) NOT NULL
    Column('base',          String(4), nullable=False), # char(4) NOT NULL
    Column('category',      String(9), nullable=False), # varchar(9) NOT NULL
    Column('limitType',     CHAR(2), nullable=False), # char(2) NOT NULL
    Column('hiLo',          CHAR(1), nullable=False), # char(1) NOT NULL
    Column('smallBlind',    Integer(3)), # int
    Column('bigBlind',      Integer(3)), # int
    Column('smallBet',      Integer(3), nullable=False), # int NOT NULL
    Column('bigBet',        Integer(3), nullable=False), # int NOT NULL
    mysql_charset='utf8',
    mysql_engine='InnoDB',
)


hands_table = Table('Hands', metadata,
    Column('id',            BigIntColumn, primary_key=True),
    Column('tableName',     String(30), nullable=False),
    Column('siteHandNo',    BigIntColumn, nullable=False),
    Column('gametypeId',    SmallInteger, ForeignKey('Gametypes.id'), nullable=False),
    Column('startTime',     DateTime, nullable=False),
    Column('importTime',    DateTime, nullable=False),
    Column('seats',         SmallInteger, nullable=False),
    Column('maxSeats',      SmallInteger, nullable=False),

    Column('boardcard1',    CardColumn),
    Column('boardcard2',    CardColumn),
    Column('boardcard3',    CardColumn),
    Column('boardcard4',    CardColumn),
    Column('boardcard5',    CardColumn),
    Column('texture',       SmallInteger),
    Column('playersVpi',    SmallInteger, nullable=False),
    Column('playersAtStreet1', SmallInteger, nullable=False, default=0),
    Column('playersAtStreet2', SmallInteger, nullable=False, default=0),
    Column('playersAtStreet3', SmallInteger, nullable=False, default=0),
    Column('playersAtStreet4', SmallInteger, nullable=False, default=0),
    Column('playersAtShowdown',SmallInteger, nullable=False),
    Column('street0Raises', SmallInteger, nullable=False),
    Column('street1Raises', SmallInteger, nullable=False),
    Column('street2Raises', SmallInteger, nullable=False),
    Column('street3Raises', SmallInteger, nullable=False),
    Column('street4Raises', SmallInteger, nullable=False),
    Column('street1Pot',    MoneyColumn),
    Column('street2Pot',    MoneyColumn),
    Column('street3Pot',    MoneyColumn),
    Column('street4Pot',    MoneyColumn),
    Column('showdownPot',   MoneyColumn),
    Column('comment',       Text),
    Column('commentTs',     DateTime),
    mysql_charset='utf8',
    mysql_engine='InnoDB',
)
Index('siteHandNo', hands_table.c.siteHandNo, hands_table.c.gametypeId, unique=True)


hands_actions_table = Table('HandsActions', metadata,
    Column('id',            BigIntColumn, primary_key=True, nullable=False),
    Column('handId',        BigIntColumn, ForeignKey("Hands.id"), nullable=False),
    Column('actions',       PickleType, nullable=False),
    mysql_charset='utf8',
    mysql_engine='InnoDB',
)


hands_players_table = Table('HandsPlayers', metadata,
    Column('id',                BigIntColumn, primary_key=True),
    Column('handId',            BigIntColumn, ForeignKey("Hands.id"), nullable=False),
    Column('playerId',          Integer, ForeignKey("Players.id"), nullable=False),
    Column('startCash',         MoneyColumn),
    Column('position',          CHAR(1)), #CHAR(1)
    Column('seatNo',            SmallInteger, nullable=False), #SMALLINT NOT NULL
        
    Column('card1',             CardColumn), #smallint NOT NULL,
    Column('card2',             CardColumn), #smallint NOT NULL
    Column('card3',             CardColumn), #smallint
    Column('card4',             CardColumn), #smallint
    Column('card5',             CardColumn), #smallint
    Column('card6',             CardColumn), #smallint
    Column('card7',             CardColumn), #smallint
    Column('startCards',        SmallInteger), #smallint
        
    Column('m_factor',          Integer), # null for ring games
    Column('ante',              MoneyColumn), #INT
    Column('winnings',          MoneyColumn, nullable=False, default=0), #int NOT NULL
    Column('rake',              MoneyColumn, nullable=False, default=0), #int NOT NULL
    Column('totalProfit',       MoneyColumn), #INT
    Column('comment',           Text), #text
    Column('commentTs',         DateTime), #DATETIME
    Column('tourneysPlayersId', BigIntColumn, ForeignKey("TourneysPlayers.id"),), #BIGINT UNSIGNED
    Column('tourneyTypeId',     Integer, ForeignKey("TourneyTypes.id"),), #SMALLINT UNSIGNED

    Column('wonWhenSeenStreet1',Float), #FLOAT
    Column('wonWhenSeenStreet2',Float), #FLOAT
    Column('wonWhenSeenStreet3',Float), #FLOAT
    Column('wonWhenSeenStreet4',Float), #FLOAT
    Column('wonAtSD',           Float), #FLOAT

    Column('street0VPI',        Boolean), #BOOLEAN
    Column('street0Aggr',       Boolean), #BOOLEAN
    Column('street0_3BChance',  Boolean), #BOOLEAN
    Column('street0_3BDone',    Boolean), #BOOLEAN
    Column('street0_4BChance',  Boolean), #BOOLEAN
    Column('street0_4BDone',    Boolean), #BOOLEAN
    Column('other3BStreet0',    Boolean), #BOOLEAN
    Column('other4BStreet0',    Boolean), #BOOLEAN

    Column('street1Seen',       Boolean), #BOOLEAN
    Column('street2Seen',       Boolean), #BOOLEAN
    Column('street3Seen',       Boolean), #BOOLEAN
    Column('street4Seen',       Boolean), #BOOLEAN
    Column('sawShowdown',       Boolean), #BOOLEAN

    Column('street1Aggr',       Boolean), #BOOLEAN
    Column('street2Aggr',       Boolean), #BOOLEAN
    Column('street3Aggr',       Boolean), #BOOLEAN
    Column('street4Aggr',       Boolean), #BOOLEAN

    Column('otherRaisedStreet0',Boolean), #BOOLEAN
    Column('otherRaisedStreet1',Boolean), #BOOLEAN
    Column('otherRaisedStreet2',Boolean), #BOOLEAN
    Column('otherRaisedStreet3',Boolean), #BOOLEAN
    Column('otherRaisedStreet4',Boolean), #BOOLEAN
    Column('foldToOtherRaisedStreet0',   Boolean), #BOOLEAN
    Column('foldToOtherRaisedStreet1',   Boolean), #BOOLEAN
    Column('foldToOtherRaisedStreet2',   Boolean), #BOOLEAN
    Column('foldToOtherRaisedStreet3',   Boolean), #BOOLEAN
    Column('foldToOtherRaisedStreet4',   Boolean), #BOOLEAN

    Column('stealAttemptChance',         Boolean), #BOOLEAN
    Column('stealAttempted',             Boolean), #BOOLEAN
    Column('foldBbToStealChance',        Boolean), #BOOLEAN
    Column('foldedBbToSteal',            Boolean), #BOOLEAN
    Column('foldSbToStealChance',        Boolean), #BOOLEAN
    Column('foldedSbToSteal',            Boolean), #BOOLEAN

    Column('street1CBChance',            Boolean), #BOOLEAN
    Column('street1CBDone',              Boolean), #BOOLEAN
    Column('street2CBChance',            Boolean), #BOOLEAN
    Column('street2CBDone',              Boolean), #BOOLEAN
    Column('street3CBChance',            Boolean), #BOOLEAN
    Column('street3CBDone',              Boolean), #BOOLEAN
    Column('street4CBChance',            Boolean), #BOOLEAN
    Column('street4CBDone',              Boolean), #BOOLEAN

    Column('foldToStreet1CBChance',      Boolean), #BOOLEAN
    Column('foldToStreet1CBDone',        Boolean), #BOOLEAN
    Column('foldToStreet2CBChance',      Boolean), #BOOLEAN
    Column('foldToStreet2CBDone',        Boolean), #BOOLEAN
    Column('foldToStreet3CBChance',      Boolean), #BOOLEAN
    Column('foldToStreet3CBDone',        Boolean), #BOOLEAN
    Column('foldToStreet4CBChance',      Boolean), #BOOLEAN
    Column('foldToStreet4CBDone',        Boolean), #BOOLEAN

    Column('street1CheckCallRaiseChance',Boolean), #BOOLEAN
    Column('street1CheckCallRaiseDone',  Boolean), #BOOLEAN
    Column('street2CheckCallRaiseChance',Boolean), #BOOLEAN
    Column('street2CheckCallRaiseDone',  Boolean), #BOOLEAN
    Column('street3CheckCallRaiseChance',Boolean), #BOOLEAN
    Column('street3CheckCallRaiseDone',  Boolean), #BOOLEAN
    Column('street4CheckCallRaiseChance',Boolean), #BOOLEAN
    Column('street4CheckCallRaiseDone',  Boolean), #BOOLEAN

    Column('street0Calls',               SmallInteger), #TINYINT
    Column('street1Calls',               SmallInteger), #TINYINT
    Column('street2Calls',               SmallInteger), #TINYINT
    Column('street3Calls',               SmallInteger), #TINYINT
    Column('street4Calls',               SmallInteger), #TINYINT
    Column('street0Bets',                SmallInteger), #TINYINT
    Column('street1Bets',                SmallInteger), #TINYINT
    Column('street2Bets',                SmallInteger), #TINYINT
    Column('street3Bets',                SmallInteger), #TINYINT
    Column('street4Bets',                SmallInteger), #TINYINT
    Column('street0Raises',              SmallInteger), #TINYINT
    Column('street1Raises',              SmallInteger), #TINYINT
    Column('street2Raises',              SmallInteger), #TINYINT
    Column('street3Raises',              SmallInteger), #TINYINT
    Column('street4Raises',              SmallInteger), #TINYINT

    Column('actionString',               String(15)), #VARCHAR(15)
    mysql_charset='utf8',
    mysql_engine='InnoDB',
)


hud_cache_table = Table('HudCache', metadata,
    Column('id',            BigIntColumn, primary_key=True),
    Column('gametypeId',    SmallInteger, ForeignKey("Gametypes.id"), nullable=False), # SMALLINT 
    Column('playerId',      Integer, ForeignKey("Players.id"), nullable=False), # SMALLINT 
    Column('activeSeats',   SmallInteger, nullable=False), # SMALLINT NOT NULL
    Column('position',      CHAR(1)), # CHAR(1)
    Column('tourneyTypeId', Integer, ForeignKey("TourneyTypes.id") ), # SMALLINT 
    Column('styleKey',      CHAR(7), nullable=False), # CHAR(7) NOT NULL
    Column('m_factor',      Integer),
    Column('HDs',           Integer, nullable=False), # INT NOT NULL

    Column('wonWhenSeenStreet1',    Float), # FLOAT
    Column('wonWhenSeenStreet2',    Float), # FLOAT
    Column('wonWhenSeenStreet3',    Float), # FLOAT
    Column('wonWhenSeenStreet4',    Float), # FLOAT
    Column('wonAtSD',               Float), # FLOAT

    Column('street0VPI',            Integer), # INT
    Column('street0Aggr',           Integer), # INT
    Column('street0_3BChance',      Integer), # INT
    Column('street0_3BDone',        Integer), # INT
    Column('street0_4BChance',      Integer), # INT
    Column('street0_4BDone',        Integer), # INT
    Column('other3BStreet0',        Integer), # INT
    Column('other4BStreet0',        Integer), # INT

    Column('street1Seen',           Integer), # INT
    Column('street2Seen',           Integer), # INT
    Column('street3Seen',           Integer), # INT
    Column('street4Seen',           Integer), # INT
    Column('sawShowdown',           Integer), # INT

    Column('street1Aggr',           Integer), # INT
    Column('street2Aggr',           Integer), # INT
    Column('street3Aggr',           Integer), # INT
    Column('street4Aggr',           Integer), # INT

    Column('otherRaisedStreet0',        Integer), # INT
    Column('otherRaisedStreet1',        Integer), # INT
    Column('otherRaisedStreet2',        Integer), # INT
    Column('otherRaisedStreet3',        Integer), # INT
    Column('otherRaisedStreet4',        Integer), # INT
    Column('foldToOtherRaisedStreet0',  Integer), # INT
    Column('foldToOtherRaisedStreet1',  Integer), # INT
    Column('foldToOtherRaisedStreet2',  Integer), # INT
    Column('foldToOtherRaisedStreet3',  Integer), # INT
    Column('foldToOtherRaisedStreet4',  Integer), # INT

    Column('stealAttemptChance',        Integer), # INT
    Column('stealAttempted',            Integer), # INT
    Column('foldBbToStealChance',       Integer), # INT
    Column('foldedBbToSteal',           Integer), # INT
    Column('foldSbToStealChance',       Integer), # INT
    Column('foldedSbToSteal',           Integer), # INT

    Column('street1CBChance',           Integer), # INT
    Column('street1CBDone',             Integer), # INT
    Column('street2CBChance',           Integer), # INT
    Column('street2CBDone',             Integer), # INT
    Column('street3CBChance',           Integer), # INT
    Column('street3CBDone',             Integer), # INT
    Column('street4CBChance',           Integer), # INT
    Column('street4CBDone',             Integer), # INT

    Column('foldToStreet1CBChance',     Integer), # INT
    Column('foldToStreet1CBDone',       Integer), # INT
    Column('foldToStreet2CBChance',     Integer), # INT
    Column('foldToStreet2CBDone',       Integer), # INT
    Column('foldToStreet3CBChance',     Integer), # INT
    Column('foldToStreet3CBDone',       Integer), # INT
    Column('foldToStreet4CBChance',     Integer), # INT
    Column('foldToStreet4CBDone',       Integer), # INT

    Column('totalProfit',               Integer), # INT

    Column('street1CheckCallRaiseChance',   Integer), # INT
    Column('street1CheckCallRaiseDone',     Integer), # INT
    Column('street2CheckCallRaiseChance',   Integer), # INT
    Column('street2CheckCallRaiseDone',     Integer), # INT
    Column('street3CheckCallRaiseChance',   Integer), # INT
    Column('street3CheckCallRaiseDone',     Integer), # INT
    Column('street4CheckCallRaiseChance',   Integer), # INT
    Column('street4CheckCallRaiseDone',     Integer), # INT

    Column('street0Calls',          Integer), # INT
    Column('street1Calls',          Integer), # INT
    Column('street2Calls',          Integer), # INT
    Column('street3Calls',          Integer), # INT
    Column('street4Calls',          Integer), # INT
    Column('street0Bets',           Integer), # INT
    Column('street1Bets',           Integer), # INT
    Column('street2Bets',           Integer), # INT
    Column('street3Bets',           Integer), # INT
    Column('street4Bets',           Integer), # INT
    Column('street0Raises',         Integer), # INT
    Column('street1Raises',         Integer), # INT
    Column('street2Raises',         Integer), # INT
    Column('street3Raises',         Integer), # INT
    Column('street4Raises',         Integer), # INT
    mysql_charset='utf8',
    mysql_engine='InnoDB',
)


players_table = Table('Players', metadata,
    Column('id',            Integer, primary_key=True),
    Column('name',          Unicode(32), nullable=False), # VARCHAR(32) CHARACTER SET utf8 NOT NULL
    Column('siteId',        SmallInteger, ForeignKey("Sites.id"), nullable=False), # SMALLINT 
    Column('comment',       Text), # text
    Column('commentTs',     DateTime), # DATETIME
    mysql_charset='utf8',
    mysql_engine='InnoDB',
)
Index('name', players_table.c.name, players_table.c.siteId, unique=True)


settings_table = Table('Settings', metadata,
    Column('version',          SmallInteger, nullable=False), 
    mysql_charset='utf8',
    mysql_engine='InnoDB',
)


sites_table = Table('Sites', metadata,
    Column('id',            SmallInteger, primary_key=True),
    Column('name',          String(32), nullable=False), # varchar(32) NOT NULL
    Column('code',          String(2), nullable=False), # char(2) NOT NULL
    mysql_charset='utf8',
    mysql_engine='InnoDB',
)


tourneys_table = Table('Tourneys', metadata,
    Column('id',            Integer, primary_key=True), 
    Column('tourneyTypeId', Integer, ForeignKey("TourneyTypes.id"), nullable=False, default=1), 
    Column('siteTourneyNo', BigIntColumn, nullable=False), # BIGINT NOT NULL
    Column('entries',       Integer), # INT NOT NULL
    Column('prizepool',     Integer), # INT NOT NULL
    Column('tourStartTime',     DateTime), # DATETIME NOT NULL
    Column('tourEndTime',       DateTime), # DATETIME
    Column('tourneyName',   String(40)), # varchar(40)
    # Mask use : 1=Positionnal Winnings|2=Match1|4=Match2|...|pow(2,n)=Matchn 
    Column('matrixIdProcessed',SmallInteger, default=0), # TINYINT UNSIGNED DEFAULT 0   
    Column('totalRebuyCount',   Integer, default=0), # INT DEFAULT 0
    Column('totalAddOnCount',   Integer, default=0), # INT DEFAULT 0
    Column('comment',       Text), # TEXT
    Column('commentTs',     DateTime), # DATETIME
    mysql_charset='utf8',
    mysql_engine='InnoDB',
)
Index('siteTourneyNo', tourneys_table.c.siteTourneyNo, tourneys_table.c.tourneyTypeId, unique=True)


tourney_types_table = Table('TourneyTypes', metadata,
    Column('id',            Integer, primary_key=True), 
    Column('siteId',        SmallInteger, ForeignKey("Sites.id"), nullable=False), 
    Column('currency',      String(4), nullable=False), # varchar(4) NOT NULL
    Column('buyin',         Integer, nullable=False), # INT NOT NULL
    Column('fee',           Integer, nullable=False), # INT NOT NULL
    Column('buyInChips',    Integer, nullable=False), # INT NOT NULL
    Column('maxSeats',      Boolean, nullable=False, default=-1), # INT NOT NULL DEFAULT -1
    Column('rebuy',         Boolean, nullable=False, default=False), # BOOLEAN NOT NULL DEFAULT False
    Column('rebuyCost',     Integer), # INT
    Column('rebuyChips',    Integer), # INT
    Column('addOn',         Boolean, nullable=False, default=False), # BOOLEAN NOT NULL DEFAULT False
    Column('addOnCost',     Integer), # INT
    Column('addOnChips',    Integer), # INT
    Column('knockout',      Boolean, nullable=False, default=False), # BOOLEAN NOT NULL DEFAULT False
    Column('koBounty',      Integer), # INT
    Column('speed',         String(10)), # varchar(10)
    Column('shootout',      Boolean, nullable=False, default=False), # BOOLEAN NOT NULL DEFAULT False
    Column('matrix',        Boolean, nullable=False, default=False), # BOOLEAN NOT NULL DEFAULT False
    Column('sng',           Boolean, nullable=False, default=False), # BOOLEAN NOT NULL DEFAULT False
    Column('satellite',     Boolean, nullable=False, default=False), # BOOLEAN NOT NULL DEFAULT False
    Column('doubleOrNothing', Boolean, nullable=False, default=False), # BOOLEAN NOT NULL DEFAULT False
    Column('guarantee',     Integer, nullable=False, default=0), # INT NOT NULL DEFAULT 0
    mysql_charset='utf8',
    mysql_engine='InnoDB',
)
Index('tourneyTypes_all', 
    tourney_types_table.c.siteId, tourney_types_table.c.buyin, tourney_types_table.c.fee, 
    tourney_types_table.c.maxSeats, tourney_types_table.c.knockout, tourney_types_table.c.rebuy,
    tourney_types_table.c.addOn, tourney_types_table.c.speed,
    tourney_types_table.c.shootout, tourney_types_table.c.matrix, tourney_types_table.c.sng)


tourneys_players_table = Table('TourneysPlayers', metadata,
    Column('id',            BigIntColumn, primary_key=True), 
    Column('tourneyId',     Integer, ForeignKey("Tourneys.id"), nullable=False), 
    Column('playerId',      Integer, ForeignKey("Players.id"), nullable=False), 
    Column('rank',          Integer), # INT NOT NULL
    Column('winnings',      Integer), # INT NOT NULL
    Column('winningsCurrency', Text), # TEXT
    Column('rebuyCount',    Integer, default=0), # INT DEFAULT 0
    Column('addOnCount',    Integer, default=0), # INT DEFAULT 0
    Column('koCount',       Integer, default=0), # INT DEFAULT 0
    Column('comment',       Text), # TEXT
    Column('commentTs',     DateTime), # DATETIME
    mysql_charset='utf8',
    mysql_engine='InnoDB',
)
Index('tourneyId', tourneys_players_table.c.tourneyId, tourneys_players_table.c.playerId, unique=True)


def sss():
    "Debug function. Returns (config, sql, db)"

    import Configuration, SQL, Database, os
    class Dummy(object):
        pass
    self = Dummy()
    self.config = Configuration.Config()
    self.settings = {}
    if (os.sep=="/"):
        self.settings['os']="linuxmac"
    else:
        self.settings['os']="windows"

    self.settings.update(self.config.get_db_parameters())
    self.settings.update(self.config.get_import_parameters())
    self.settings.update(self.config.get_default_paths())

    self.sql = SQL.Sql( db_server = self.settings['db-server'])
    self.db = Database.Database(self.config, sql = self.sql)

    return self.config, self.sql, self.db

