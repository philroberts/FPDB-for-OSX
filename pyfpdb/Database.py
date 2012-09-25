#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Database.py

Create and manage the database objects.
"""
#    Copyright 2008-2011, Ray E. Barker
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

import L10n
_ = L10n.get_translation()

########################################################################

# TODO:  - rebuild indexes / vacuum option
#        - check speed of get_stats_from_hand() - add log info
#        - check size of db, seems big? (mysql)
#        - investigate size of mysql db (200K for just 7K hands? 2GB for 140K hands?)

# postmaster -D /var/lib/pgsql/data

#    Standard Library modules
import os
import sys
import traceback
from datetime import datetime, date, time, timedelta
from time import time, strftime, sleep
from decimal_wrapper import Decimal
import string
import re
import Queue
import codecs
import math
import pytz
import logging

#    FreePokerTools modules
import SQL
import Card
import Charset
from Exceptions import *
import Configuration

if __name__ == "__main__":
    Configuration.set_logfile("fpdb-log.txt")
# logging has been set up in fpdb.py or HUD_main.py, use their settings:
log = logging.getLogger("db")

#    Other library modules
try:
    import sqlalchemy.pool as pool
    use_pool = True
except ImportError:
    log.info(_("Not using sqlalchemy connection pool."))
    use_pool = False

try:
    from numpy import var
    use_numpy = True
except ImportError:
    log.info(_("Not using numpy to define variance in sqlite."))
    use_numpy = False


DB_VERSION = 171


# Variance created as sqlite has a bunch of undefined aggregate functions.

class VARIANCE:
    def __init__(self):
        self.store = []

    def step(self, value):
        self.store.append(value)

    def finalize(self):
        return float(var(self.store))

class sqlitemath:
    def mod(self, a, b):
        return a%b


class Database:

    MYSQL_INNODB = 2
    PGSQL = 3
    SQLITE = 4

    hero_hudstart_def = '1999-12-31'      # default for length of Hero's stats in HUD
    villain_hudstart_def = '1999-12-31'   # default for length of Villain's stats in HUD

    # Data Structures for index and foreign key creation
    # drop_code is an int with possible values:  0 - don't drop for bulk import
    #                                            1 - drop during bulk import
    # db differences:
    # - note that mysql automatically creates indexes on constrained columns when
    #   foreign keys are created, while postgres does not. Hence the much longer list
    #   of indexes is required for postgres.
    # all primary keys are left on all the time
    #
    #             table     column           drop_code

    indexes = [
                [ ] # no db with index 0
              , [ ] # no db with index 1
              , [ # indexes for mysql (list index 2) (foreign keys not here, in next data structure)
                #  {'tab':'Players',         'col':'name',              'drop':0}  unique indexes not dropped
                #  {'tab':'Hands',           'col':'siteHandNo',        'drop':0}  unique indexes not dropped
                #, {'tab':'Tourneys',        'col':'siteTourneyNo',     'drop':0}  unique indexes not dropped
                ]
              , [ # indexes for postgres (list index 3)
                  {'tab':'Gametypes',       'col':'siteId',            'drop':0}
                , {'tab':'Hands',           'col':'tourneyId',         'drop':0} # mct 22/3/09
                , {'tab':'Hands',           'col':'gametypeId',        'drop':0} # mct 22/3/09
                , {'tab':'Hands',           'col':'sessionId',         'drop':0} # mct 22/3/09
                , {'tab':'Hands',           'col':'gameId',            'drop':0} # mct 22/3/09
                , {'tab':'Hands',           'col':'fileId',            'drop':0} # mct 22/3/09
                #, {'tab':'Hands',           'col':'siteHandNo',        'drop':0}  unique indexes not dropped
                , {'tab':'HandsActions',    'col':'handId',            'drop':1}
                , {'tab':'HandsActions',    'col':'playerId',          'drop':1}
                , {'tab':'HandsActions',    'col':'actionId',          'drop':1}
                , {'tab':'HandsStove',      'col':'handId',            'drop':1}
                , {'tab':'HandsStove',      'col':'playerId',          'drop':1}
                , {'tab':'Boards',          'col':'handId',            'drop':1}
                , {'tab':'HandsPlayers',    'col':'handId',            'drop':1}
                , {'tab':'HandsPlayers',    'col':'playerId',          'drop':1}
                , {'tab':'HandsPlayers',    'col':'tourneysPlayersId', 'drop':0}
                , {'tab':'HudCache',        'col':'gametypeId',        'drop':1}
                , {'tab':'HudCache',        'col':'playerId',          'drop':0}
                , {'tab':'HudCache',        'col':'tourneyTypeId',     'drop':0}
                , {'tab':'GamesCache',      'col':'sessionId',         'drop':1}
                , {'tab':'GamesCache',      'col':'gametypeId',        'drop':1}
                , {'tab':'GamesCache',      'col':'playerId',          'drop':0}
                , {'tab':'Players',         'col':'siteId',            'drop':1}
                #, {'tab':'Players',         'col':'name',              'drop':0}  unique indexes not dropped
                , {'tab':'Tourneys',        'col':'tourneyTypeId',     'drop':1}
                , {'tab':'Tourneys',        'col':'sessionId',         'drop':1}
                #, {'tab':'Tourneys',        'col':'siteTourneyNo',     'drop':0}  unique indexes not dropped
                , {'tab':'TourneysPlayers', 'col':'playerId',          'drop':0}
                #, {'tab':'TourneysPlayers', 'col':'tourneyId',         'drop':0}  unique indexes not dropped
                , {'tab':'TourneyTypes',    'col':'siteId',            'drop':0}
                , {'tab':'Backings',        'col':'tourneysPlayersId', 'drop':0}
                , {'tab':'Backings',        'col':'playerId',          'drop':0}
                , {'tab':'RawHands',        'col':'id',                'drop':0}
                , {'tab':'RawTourneys',     'col':'id',                'drop':0}
                ]
              , [ # indexes for sqlite (list index 4)
                  {'tab':'Hands',           'col':'tourneyId',         'drop':0}
                , {'tab':'Hands',           'col':'gametypeId',        'drop':0}
                , {'tab':'Hands',           'col':'sessionId',         'drop':0}
                , {'tab':'Hands',           'col':'gameId',            'drop':0}
                , {'tab':'Hands',           'col':'fileId',            'drop':0}
                , {'tab':'Boards',          'col':'handId',            'drop':0}
                , {'tab':'Gametypes',       'col':'siteId',            'drop':0}
                , {'tab':'HandsPlayers',    'col':'handId',            'drop':0}
                , {'tab':'HandsPlayers',    'col':'playerId',          'drop':0}
                , {'tab':'HandsPlayers',    'col':'tourneysPlayersId', 'drop':0}
                , {'tab':'HandsActions',    'col':'handId',            'drop':0}
                , {'tab':'HandsActions',    'col':'playerId',          'drop':0}
                , {'tab':'HandsActions',    'col':'actionId',          'drop':1}
                , {'tab':'HandsStove',      'col':'handId',            'drop':0}
                , {'tab':'HandsStove',      'col':'playerId',          'drop':0}
                , {'tab':'HudCache',        'col':'gametypeId',        'drop':1}
                , {'tab':'HudCache',        'col':'playerId',          'drop':0}
                , {'tab':'HudCache',        'col':'tourneyTypeId',     'drop':0}
                , {'tab':'GamesCache',      'col':'sessionId',         'drop':1}
                , {'tab':'GamesCache',      'col':'gametypeId',        'drop':1}
                , {'tab':'GamesCache',      'col':'playerId',          'drop':0}
                , {'tab':'Players',         'col':'siteId',            'drop':1}
                , {'tab':'Tourneys',        'col':'tourneyTypeId',     'drop':1}
                , {'tab':'Tourneys',        'col':'sessionId',         'drop':1}
                , {'tab':'TourneysPlayers', 'col':'playerId',          'drop':0}
                , {'tab':'TourneyTypes',    'col':'siteId',            'drop':0}
                , {'tab':'Backings',        'col':'tourneysPlayersId', 'drop':0}
                , {'tab':'Backings',        'col':'playerId',          'drop':0}
                , {'tab':'RawHands',        'col':'id',                'drop':0}
                , {'tab':'RawTourneys',     'col':'id',                'drop':0}
                ]
              ]
              
    
    foreignKeys = [
                    [ ] # no db with index 0
                  , [ ] # no db with index 1
                  , [ # foreign keys for mysql (index 2)
                      {'fktab':'Hands',        'fkcol':'tourneyId',     'rtab':'Tourneys',      'rcol':'id', 'drop':1}
                    , {'fktab':'Hands',        'fkcol':'gametypeId',    'rtab':'Gametypes',     'rcol':'id', 'drop':1}
                    , {'fktab':'Hands',        'fkcol':'sessionId',     'rtab':'SessionsCache', 'rcol':'id', 'drop':1}
                    , {'fktab':'Hands',        'fkcol':'gameId',        'rtab':'GamesCache',    'rcol':'id', 'drop':1}
                    , {'fktab':'Hands',        'fkcol':'fileId',        'rtab':'Files',         'rcol':'id', 'drop':1}
                    , {'fktab':'Boards',       'fkcol':'handId',        'rtab':'Hands',         'rcol':'id', 'drop':1}
                    , {'fktab':'HandsPlayers', 'fkcol':'handId',        'rtab':'Hands',         'rcol':'id', 'drop':1}
                    , {'fktab':'HandsPlayers', 'fkcol':'playerId',      'rtab':'Players',       'rcol':'id', 'drop':1}
                    , {'fktab':'HandsPlayers', 'fkcol':'tourneysPlayersId','rtab':'TourneysPlayers','rcol':'id', 'drop':1}
                    , {'fktab':'HandsActions', 'fkcol':'handId',        'rtab':'Hands',         'rcol':'id', 'drop':1}
                    , {'fktab':'HandsActions', 'fkcol':'playerId',      'rtab':'Players',       'rcol':'id', 'drop':1}
                    , {'fktab':'HandsActions', 'fkcol':'actionId',      'rtab':'Actions',       'rcol':'id', 'drop':1}
                    , {'fktab':'HandsStove',   'fkcol':'handId',        'rtab':'Hands',         'rcol':'id', 'drop':1}
                    , {'fktab':'HandsStove',   'fkcol':'playerId',      'rtab':'Players',       'rcol':'id', 'drop':1}
                    , {'fktab':'HudCache',     'fkcol':'gametypeId',    'rtab':'Gametypes',     'rcol':'id', 'drop':1}
                    , {'fktab':'HudCache',     'fkcol':'playerId',      'rtab':'Players',       'rcol':'id', 'drop':0}
                    , {'fktab':'HudCache',     'fkcol':'tourneyTypeId', 'rtab':'TourneyTypes',  'rcol':'id', 'drop':1}
                    , {'fktab':'GamesCache',   'fkcol':'sessionId',     'rtab':'SessionsCache', 'rcol':'id', 'drop':1}
                    , {'fktab':'GamesCache',   'fkcol':'gametypeId',    'rtab':'Gametypes',     'rcol':'id', 'drop':1}
                    , {'fktab':'GamesCache',   'fkcol':'playerId',      'rtab':'Players',       'rcol':'id', 'drop':0}
                    , {'fktab':'Tourneys',     'fkcol':'tourneyTypeId', 'rtab':'TourneyTypes',  'rcol':'id', 'drop':1}
                    , {'fktab':'Tourneys',     'fkcol':'sessionId',     'rtab':'SessionsCache', 'rcol':'id', 'drop':1}
                    ]
                  , [ # foreign keys for postgres (index 3)
                      {'fktab':'Hands',        'fkcol':'tourneyId',     'rtab':'Tourneys',      'rcol':'id', 'drop':1}
                    , {'fktab':'Hands',        'fkcol':'gametypeId',    'rtab':'Gametypes',     'rcol':'id', 'drop':1}
                    , {'fktab':'Hands',        'fkcol':'sessionId',     'rtab':'SessionsCache', 'rcol':'id', 'drop':1}
                    , {'fktab':'Hands',        'fkcol':'gameId',        'rtab':'GamesCache',    'rcol':'id', 'drop':1}
                    , {'fktab':'Hands',        'fkcol':'fileId',        'rtab':'Files',         'rcol':'id', 'drop':1}
                    , {'fktab':'Boards',       'fkcol':'handId',        'rtab':'Hands',         'rcol':'id', 'drop':1}
                    , {'fktab':'HandsPlayers', 'fkcol':'handId',        'rtab':'Hands',         'rcol':'id', 'drop':1}
                    , {'fktab':'HandsPlayers', 'fkcol':'playerId',      'rtab':'Players',       'rcol':'id', 'drop':1}
                    , {'fktab':'HandsPlayers', 'fkcol':'tourneysPlayersId','rtab':'TourneysPlayers','rcol':'id', 'drop':1}
                    , {'fktab':'HandsActions', 'fkcol':'handId',        'rtab':'Hands',         'rcol':'id', 'drop':1}
                    , {'fktab':'HandsActions', 'fkcol':'playerId',      'rtab':'Players',       'rcol':'id', 'drop':1}
                    , {'fktab':'HandsActions', 'fkcol':'actionId',      'rtab':'Actions',       'rcol':'id', 'drop':1}
                    , {'fktab':'HandsStove',   'fkcol':'handId',        'rtab':'Hands',         'rcol':'id', 'drop':1}
                    , {'fktab':'HandsStove',   'fkcol':'playerId',      'rtab':'Players',       'rcol':'id', 'drop':1}
                    , {'fktab':'HudCache',     'fkcol':'gametypeId',    'rtab':'Gametypes',     'rcol':'id', 'drop':1}
                    , {'fktab':'HudCache',     'fkcol':'playerId',      'rtab':'Players',       'rcol':'id', 'drop':0}
                    , {'fktab':'HudCache',     'fkcol':'tourneyTypeId', 'rtab':'TourneyTypes',  'rcol':'id', 'drop':1}
                    , {'fktab':'GamesCache',   'fkcol':'sessionId',     'rtab':'SessionsCache', 'rcol':'id', 'drop':1}
                    , {'fktab':'GamesCache',   'fkcol':'gametypeId',    'rtab':'Gametypes',     'rcol':'id', 'drop':1}
                    , {'fktab':'GamesCache',   'fkcol':'playerId',      'rtab':'Players',       'rcol':'id', 'drop':0}
                    , {'fktab':'Tourneys',     'fkcol':'tourneyTypeId', 'rtab':'TourneyTypes',  'rcol':'id', 'drop':1}
                    , {'fktab':'Tourneys',     'fkcol':'sessionId',     'rtab':'SessionsCache', 'rcol':'id', 'drop':1}
                    ]
                  , [ # no foreign keys in sqlite (index 4)
                    ]
                  ]


    # MySQL Notes:
    #    "FOREIGN KEY (handId) REFERENCES Hands(id)" - requires index on Hands.id
    #                                                - creates index handId on <thistable>.handId
    # alter table t drop foreign key fk
    # alter table t add foreign key (fkcol) references tab(rcol)
    # alter table t add constraint c foreign key (fkcol) references tab(rcol)
    # (fkcol is used for foreigh key name)

    # mysql to list indexes: (CG - "LIST INDEXES" should work too)
    #   SELECT table_name, index_name, non_unique, column_name
    #   FROM INFORMATION_SCHEMA.STATISTICS
    #     WHERE table_name = 'tbl_name'
    #     AND table_schema = 'db_name'
    #   ORDER BY table_name, index_name, seq_in_index
    #
    # ALTER TABLE Tourneys ADD INDEX siteTourneyNo(siteTourneyNo)
    # ALTER TABLE tab DROP INDEX idx

    # mysql to list fks:
    #   SELECT constraint_name, table_name, column_name, referenced_table_name, referenced_column_name
    #   FROM information_schema.KEY_COLUMN_USAGE
    #   WHERE REFERENCED_TABLE_SCHEMA = (your schema name here)
    #   AND REFERENCED_TABLE_NAME is not null
    #   ORDER BY TABLE_NAME, COLUMN_NAME;

    # this may indicate missing object
    # _mysql_exceptions.OperationalError: (1025, "Error on rename of '.\\fpdb\\hands' to '.\\fpdb\\#sql2-7f0-1b' (errno: 152)")


    # PG notes:

    #  To add a foreign key constraint to a table:
    #  ALTER TABLE tab ADD CONSTRAINT c FOREIGN KEY (col) REFERENCES t2(col2) MATCH FULL;
    #  ALTER TABLE tab DROP CONSTRAINT zipchk
    #
    #  Note: index names must be unique across a schema
    #  CREATE INDEX idx ON tab(col)
    #  DROP INDEX idx
    #  SELECT * FROM PG_INDEXES

    # SQLite notes:

    # To add an index:
    # create index indexname on tablename (col);


    def __init__(self, c, sql = None, autoconnect = True):
        log.debug(_("Creating Database instance, sql = %s") % sql)
        self.config = c
        self.__connected = False
        self.settings = {}
        self.settings['os'] = "linuxmac" if os.name != "nt" else "windows"
        db_params = c.get_db_parameters()
        self.import_options = c.get_import_parameters()
        self.backend = db_params['db-backend']
        self.db_server = db_params['db-server']
        self.database = db_params['db-databaseName']
        self.host = db_params['db-host']
        self.db_path = ''
        gen = c.get_general_params()
        self.day_start = 0
        self._has_lock = False
        self.printdata = False
        self.resetCache()
        self.resetBulkCache()
        
        if 'day_start' in gen:
            self.day_start = float(gen['day_start'])
            
        self.sessionTimeout = float(self.import_options['sessionTimeout'])

        # where possible avoid creating new SQL instance by using the global one passed in
        if sql is None:
            self.sql = SQL.Sql(db_server = self.db_server)
        else:
            self.sql = sql

        if autoconnect:
            # connect to db
            self.do_connect(c)

            if self.backend == self.PGSQL:
                from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT, ISOLATION_LEVEL_READ_COMMITTED, ISOLATION_LEVEL_SERIALIZABLE
                #ISOLATION_LEVEL_AUTOCOMMIT     = 0
                #ISOLATION_LEVEL_READ_COMMITTED = 1
                #ISOLATION_LEVEL_SERIALIZABLE   = 2


            if self.backend == self.SQLITE and self.database == ':memory:' and self.wrongDbVersion and self.is_connected():
                log.info("sqlite/:memory: - creating")
                self.recreate_tables()
                self.wrongDbVersion = False
            
            self.gtcache    = None       # GameTypeId cache
            #self.ttcache    = None       # TourneyTypeId cache   
            self.tcache     = None       # TourneyId cache
            self.pcache     = None       # PlayerId cache
            self.tpcache    = None       # TourneysPlayersId cache

            # if fastStoreHudCache is true then the hudcache will be build using the limited configuration which ignores date, seats, and position
            self.build_full_hudcache = not self.import_options['fastStoreHudCache']

            #self.hud_hero_style = 'T'  # Duplicate set of vars just for hero - not used yet.
            #self.hud_hero_hands = 2000 # Idea is that you might want all-time stats for others
            #self.hud_hero_days  = 30   # but last T days or last H hands for yourself

            # vars for hand ids or dates fetched according to above config:
            self.hand_1day_ago = 0             # max hand id more than 24 hrs earlier than now
            self.date_ndays_ago = 'd000000'    # date N days ago ('d' + YYMMDD)
            self.h_date_ndays_ago = 'd000000'  # date N days ago ('d' + YYMMDD) for hero
            self.date_nhands_ago = {}          # dates N hands ago per player - not used yet

            self.saveActions = False if self.import_options['saveActions'] == False else True

            if self.is_connected():
                if not self.wrongDbVersion:
                    self.get_sites()
                self.connection.rollback()  # make sure any locks taken so far are released
    #end def __init__

    def dumpDatabase(self):
        result="fpdb database dump\nDB version=" + str(DB_VERSION)+"\n\n"

        tables=self.cursor.execute(self.sql.query['list_tables'])
        tables=self.cursor.fetchall()
        for table in (u'Actions', u'Autorates', u'Backings', u'Gametypes', u'Hands', u'Boards', u'HandsActions', u'HandsPlayers', u'HandsStove', u'Files', u'HudCache', u'SessionsCache', u'GamesCache',u'Players', u'RawHands', u'RawTourneys', u'Settings', u'Sites', u'TourneyTypes', u'Tourneys', u'TourneysPlayers'):
            print "table:", table
            result+="###################\nTable "+table+"\n###################\n"
            rows=self.cursor.execute(self.sql.query['get'+table])
            rows=self.cursor.fetchall()
            columnNames=self.cursor.description
            if not rows:
                result+="empty table\n"
            else:
                for row in rows:
                    for columnNumber in range(len(columnNames)):
                        if columnNames[columnNumber][0]=="importTime":
                            result+=("  "+columnNames[columnNumber][0]+"=ignore\n")
                        elif columnNames[columnNumber][0]=="styleKey":
                            result+=("  "+columnNames[columnNumber][0]+"=ignore\n")
                        else:
                            result+=("  "+columnNames[columnNumber][0]+"="+str(row[columnNumber])+"\n")
                    result+="\n"
            result+="\n"
        return result
    #end def dumpDatabase

    # could be used by hud to change hud style
    def set_hud_style(self, style):
        self.hud_style = style

    def do_connect(self, c):
        if c is None:
            raise FpdbError('Configuration not defined')

        db = c.get_db_parameters()
        try:
            self.connect(backend=db['db-backend'],
                         host=db['db-host'],
                         database=db['db-databaseName'],
                         user=db['db-user'],
                         password=db['db-password'])
        except:
            # error during connect
            self.__connected = False
            raise

        db_params = c.get_db_parameters()
        self.import_options = c.get_import_parameters()
        self.backend = db_params['db-backend']
        self.db_server = db_params['db-server']
        self.database = db_params['db-databaseName']
        self.host = db_params['db-host']

    def connect(self, backend=None, host=None, database=None,
                user=None, password=None, create=False):
        """Connects a database with the given parameters"""
        if backend is None:
            raise FpdbError('Database backend not defined')
        self.backend = backend
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        self.cursor     = None
        self.hand_inc   = 1

        if backend == Database.MYSQL_INNODB:
            import MySQLdb
            if use_pool:
                MySQLdb = pool.manage(MySQLdb, pool_size=5)
            try:
                self.connection = MySQLdb.connect(host=host
                                                 ,user=user
                                                 ,passwd=password
                                                 ,db=database
                                                 ,charset='utf8'
                                                 ,use_unicode=True)
                self.__connected = True
            #TODO: Add port option
            except MySQLdb.Error, ex:
                if ex.args[0] == 1045:
                    raise FpdbMySQLAccessDenied(ex.args[0], ex.args[1])
                elif ex.args[0] == 2002 or ex.args[0] == 2003: # 2002 is no unix socket, 2003 is no tcp socket
                    raise FpdbMySQLNoDatabase(ex.args[0], ex.args[1])
                else:
                    print _("*** WARNING UNKNOWN MYSQL ERROR:"), ex
            c = self.get_cursor()
            c.execute("show variables like 'auto_increment_increment'")
            self.hand_inc = int(c.fetchone()[1])
        elif backend == Database.PGSQL:
            import psycopg2
            import psycopg2.extensions
            if use_pool:
                psycopg2 = pool.manage(psycopg2, pool_size=5)
            psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
            # If DB connection is made over TCP, then the variables
            # host, user and password are required
            # For local domain-socket connections, only DB name is
            # needed, and everything else is in fact undefined and/or
            # flat out wrong
            # sqlcoder: This database only connect failed in my windows setup??
            # Modifed it to try the 4 parameter style if the first connect fails - does this work everywhere?
            self.__connected = False
            if self.host == "localhost" or self.host == "127.0.0.1":
                try:
                    self.connection = psycopg2.connect(database = database)
                    self.__connected = True
                except:
                    # direct connection failed so try user/pass/... version
                    pass
            if not self.is_connected():
                try:
                    print(host, user, password, database)
                    self.connection = psycopg2.connect(host = host,
                                               user = user,
                                               password = password,
                                               database = database)
                    self.__connected = True
                except Exception, ex:
                    if 'Connection refused' in ex.args[0] or ('database "' in ex.args[0] and '" does not exist' in ex.args[0]):
                        # meaning eg. db not running
                        raise FpdbPostgresqlNoDatabase(errmsg = ex.args[0])
                    elif 'password authentication' in ex.args[0]:
                        raise FpdbPostgresqlAccessDenied(errmsg = ex.args[0])
                    elif 'role "' in ex.args[0] and '" does not exist' in ex.args[0]: #role "fpdb" does not exist
                        raise FpdbPostgresqlAccessDenied(errmsg = ex.args[0])
                    else:
                        msg = ex.args[0]
                    print msg
                    raise FpdbError(msg)
        elif backend == Database.SQLITE:
            create = True
            import sqlite3
            if use_pool:
                sqlite3 = pool.manage(sqlite3, pool_size=1)
            #else:
            #    log.warning("SQLite won't work well without 'sqlalchemy' installed.")

            if database != ":memory:":
                if not os.path.isdir(self.config.dir_database) and create:
                    print _("Creating directory: '%s'") % (self.config.dir_database)
                    log.info(_("Creating directory: '%s'") % (self.config.dir_database))
                    os.mkdir(self.config.dir_database)
                database = os.path.join(self.config.dir_database, database)
            self.db_path = database
            log.info(_("Connecting to SQLite: %s") % self.db_path)
            if os.path.exists(database) or create:
                self.connection = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES )
                self.__connected = True
                sqlite3.register_converter("bool", lambda x: bool(int(x)))
                sqlite3.register_adapter(bool, lambda x: 1 if x else 0)
                self.connection.create_function("floor", 1, math.floor)
                self.connection.create_function("sqrt", 1, math.sqrt)
                tmp = sqlitemath()
                self.connection.create_function("mod", 2, tmp.mod)
                if use_numpy:
                    self.connection.create_aggregate("variance", 1, VARIANCE)
                else:
                    log.warning(_("Some database functions will not work without NumPy support"))
                self.cursor = self.connection.cursor()
                self.cursor.execute('PRAGMA temp_store=2')  # use memory for temp tables/indexes
                self.cursor.execute('PRAGMA journal_mode=WAL')  # use memory for temp tables/indexes
                self.cursor.execute('PRAGMA synchronous=0') # don't wait for file writes to finish
            else:
                raise FpdbError("sqlite database "+database+" does not exist")
        else:
            raise FpdbError("unrecognised database backend:"+str(backend))

        if self.is_connected():
            self.cursor = self.connection.cursor()
            self.cursor.execute(self.sql.query['set tx level'])
            self.check_version(database=database, create=create)

    def get_sites(self):
        self.cursor.execute("SELECT name,id FROM Sites")
        sites = self.cursor.fetchall()
        self.config.set_site_ids(sites)

    def check_version(self, database, create):
        self.wrongDbVersion = False
        try:
            self.cursor.execute("SELECT * FROM Settings")
            settings = self.cursor.fetchone()
            if settings[0] != DB_VERSION:
                log.error((_("Outdated or too new database version (%s).") % (settings[0])) + " " + _("Please recreate tables."))
                self.wrongDbVersion = True
        except:# _mysql_exceptions.ProgrammingError:
            if database !=  ":memory:":
                if create:
                    #print (_("Failed to read settings table.") + " - " + _("Recreating tables."))
                    log.info(_("Failed to read settings table.") + " - " + _("Recreating tables."))
                    self.recreate_tables()
                    self.check_version(database=database, create=False)
                else:
                    #print (_("Failed to read settings table.") + " - " + _("Please recreate tables."))
                    log.info(_("Failed to read settings table.") + " - " + _("Please recreate tables."))
                    self.wrongDbVersion = True
            else:
                self.wrongDbVersion = True
    #end def connect

    def commit(self):
        if self.backend != self.SQLITE:
            self.connection.commit()
        else:
            # sqlite commits can fail because of shared locks on the database (SQLITE_BUSY)
            # re-try commit if it fails in case this happened
            maxtimes = 5
            pause = 1
            ok = False
            for i in xrange(maxtimes):
                try:
                    ret = self.connection.commit()
                    #log.debug(_("commit finished ok, i = ")+str(i))
                    ok = True
                except:
                    log.debug(_("commit %s failed: info=%s value=%s") % (str(i), str(sys.exc_info()), str(sys.exc_value)))
                    sleep(pause)
                if ok: break
            if not ok:
                log.debug(_("commit failed"))
                raise FpdbError('sqlite commit failed')

    def rollback(self):
        self.connection.rollback()

    def connected(self):
        """ now deprecated, use is_connected() instead """
        return self.__connected

    def is_connected(self):
        return self.__connected

    def get_cursor(self, connect=False):
        if connect and self.backend == Database.MYSQL_INNODB and os.name == 'nt':
            self.do_connect(self.config)
        return self.connection.cursor()

    def close_connection(self):
        self.connection.close()

    def disconnect(self, due_to_error=False):
        """Disconnects the DB (rolls back if param is true, otherwise commits"""
        if due_to_error:
            self.connection.rollback()
        else:
            self.connection.commit()
        self.cursor.close()
        self.connection.close()
        self.__connected = False

    def reconnect(self, due_to_error=False):
        """Reconnects the DB"""
        #print "started reconnect"
        self.disconnect(due_to_error)
        self.connect(self.backend, self.host, self.database, self.user, self.password)

    def get_backend_name(self):
        """Returns the name of the currently used backend"""
        if self.backend==2:
            return "MySQL InnoDB"
        elif self.backend==3:
            return "PostgreSQL"
        elif self.backend==4:
            return "SQLite"
        else:
            raise FpdbError("invalid backend")

    def get_db_info(self):
        return (self.host, self.database, self.user, self.password)

    def get_table_name(self, hand_id):
        c = self.connection.cursor()
        c.execute(self.sql.query['get_table_name'], (hand_id, ))
        row = c.fetchone()
        return row

    def get_table_info(self, hand_id):
        c = self.connection.cursor()
        c.execute(self.sql.query['get_table_name'], (hand_id, ))
        row = c.fetchone()
        l = list(row)
        if row[3] == "ring":   # cash game
            l.append(None)
            l.append(None)
            return l
        else:    # tournament
            tour_no, tab_no = re.split(" ", row[0], 1)
            l.append(tour_no)
            l.append(tab_no)
            return l

    def get_last_hand(self):
        c = self.connection.cursor()
        c.execute(self.sql.query['get_last_hand'])
        row = c.fetchone()
        return row[0]

    def get_xml(self, hand_id):
        c = self.connection.cursor()
        c.execute(self.sql.query['get_xml'], (hand_id))
        row = c.fetchone()
        return row[0]

    def get_recent_hands(self, last_hand):
        c = self.connection.cursor()
        c.execute(self.sql.query['get_recent_hands'], {'last_hand': last_hand})
        return c.fetchall()

    def get_hand_info(self, new_hand_id):
        c = self.connection.cursor()
        c.execute(self.sql.query['get_hand_info'], new_hand_id)
        return c.fetchall()

    def getHandCount(self):
        c = self.connection.cursor()
        c.execute(self.sql.query['getHandCount'])
        return c.fetchone()[0]
    #end def getHandCount

    def getTourneyCount(self):
        c = self.connection.cursor()
        c.execute(self.sql.query['getTourneyCount'])
        return c.fetchone()[0]
    #end def getTourneyCount

    def getTourneyTypeCount(self):
        c = self.connection.cursor()
        c.execute(self.sql.query['getTourneyTypeCount'])
        return c.fetchone()[0]
    #end def getTourneyCount

    def getSiteTourneyNos(self, site):
        c = self.connection.cursor()
        q = self.sql.query['getSiteId']
        q = q.replace('%s', self.sql.query['placeholder'])
        c.execute(q, (site,))
        siteid = c.fetchone()[0]
        q = self.sql.query['getSiteTourneyNos']
        q = q.replace('%s', self.sql.query['placeholder'])
        c.execute(q, (siteid,))
        alist = []
        for row in c.fetchall():
            alist.append(row)
        return alist

    def get_actual_seat(self, hand_id, name):
        c = self.connection.cursor()
        c.execute(self.sql.query['get_actual_seat'], (hand_id, name))
        row = c.fetchone()
        return row[0]

    def get_cards(self, hand):
        """Get and return the cards for each player in the hand."""
        cards = {} # dict of cards, the key is the seat number,
                   # the value is a tuple of the players cards
                   # example: {1: (0, 0, 20, 21, 22, 0 , 0)}
        c = self.connection.cursor()
        c.execute(self.sql.query['get_cards'], [hand])
        for row in c.fetchall():
            cards[row[0]] = row[1:]
        return cards

    def get_common_cards(self, hand):
        """Get and return the community cards for the specified hand."""
        cards = {}
        c = self.connection.cursor()
        c.execute(self.sql.query['get_common_cards'], [hand])
#        row = c.fetchone()
        cards['common'] = c.fetchone()
        return cards

    def get_action_from_hand(self, hand_no):
        action = [ [], [], [], [], [] ]
        c = self.connection.cursor()
        c.execute(self.sql.query['get_action_from_hand'], (hand_no,))
        for row in c.fetchall():
            street = row[0]
            act = row[1:]
            action[street].append(act)
        return action

    def get_winners_from_hand(self, hand):
        """Returns a hash of winners:amount won, given a hand number."""
        winners = {}
        c = self.connection.cursor()
        c.execute(self.sql.query['get_winners_from_hand'], (hand,))
        for row in c.fetchall():
            winners[row[0]] = row[1]
        return winners

    def set_printdata(self, val):
        self.printdata = val

    def init_hud_stat_vars(self, hud_days, h_hud_days):
        """Initialise variables used by Hud to fetch stats:
           self.hand_1day_ago     handId of latest hand played more than a day ago
           self.date_ndays_ago    date n days ago
           self.h_date_ndays_ago  date n days ago for hero (different n)
        """

        self.hand_1day_ago = 1
        c = self.get_cursor()
        c.execute(self.sql.query['get_hand_1day_ago'])
        row = c.fetchone()
        if row and row[0]:
            self.hand_1day_ago = int(row[0])
                
        tz = datetime.utcnow() - datetime.today()
        tz_offset = tz.seconds/3600
        tz_day_start_offset = self.day_start + tz_offset
        
        d = timedelta(days=hud_days, hours=tz_day_start_offset)
        now = datetime.utcnow() - d
        self.date_ndays_ago = "d%02d%02d%02d" % (now.year - 2000, now.month, now.day)
        
        d = timedelta(days=h_hud_days, hours=tz_day_start_offset)
        now = datetime.utcnow() - d
        self.h_date_ndays_ago = "d%02d%02d%02d" % (now.year - 2000, now.month, now.day)

    # is get_stats_from_hand slow?
    def get_stats_from_hand( self, hand, type   # type is "ring" or "tour"
                           , hud_params = {'hud_style':'A', 'agg_bb_mult':1000
                                          ,'seats_style':'A', 'seats_cust_nums':['n/a', 'n/a', (2,2), (3,4), (3,5), (4,6), (5,7), (6,8), (7,9), (8,10), (8,10)]
                                          ,'h_hud_style':'S', 'h_agg_bb_mult':1000
                                          ,'h_seats_style':'A', 'h_seats_cust_nums':['n/a', 'n/a', (2,2), (3,4), (3,5), (4,6), (5,7), (6,8), (7,9), (8,10), (8,10)]
                                          }
                           , hero_id = -1
                           , num_seats = 6
                           ):
        hud_style   = hud_params['hud_style']
        agg_bb_mult = hud_params['agg_bb_mult']
        seats_style = hud_params['seats_style']
        seats_cust_nums = hud_params['seats_cust_nums']
        h_hud_style   = hud_params['h_hud_style']
        h_agg_bb_mult = hud_params['h_agg_bb_mult']
        h_seats_style = hud_params['h_seats_style']
        h_seats_cust_nums = hud_params['h_seats_cust_nums']

        stat_dict = {}

        if seats_style == 'A':
            seats_min, seats_max = 0, 10
        elif seats_style == 'C':
            seats_min, seats_max = seats_cust_nums[num_seats][0], seats_cust_nums[num_seats][1]
        elif seats_style == 'E':
            seats_min, seats_max = num_seats, num_seats
        else:
            seats_min, seats_max = 0, 10
            print "bad seats_style value:", seats_style

        if h_seats_style == 'A':
            h_seats_min, h_seats_max = 0, 10
        elif h_seats_style == 'C':
            h_seats_min, h_seats_max = h_seats_cust_nums[num_seats][0], h_seats_cust_nums[num_seats][1]
        elif h_seats_style == 'E':
            h_seats_min, h_seats_max = num_seats, num_seats
        else:
            h_seats_min, h_seats_max = 0, 10
            print "bad h_seats_style value:", h_seats_style
        #log.info("opp seats style %s %d %d hero seats style %s %d %d"
        #         % (seats_style, seats_min, seats_max
        #           ,h_seats_style, h_seats_min, h_seats_max) )

        if hud_style == 'S' or h_hud_style == 'S':
            self.get_stats_from_hand_session(hand, stat_dict, hero_id
                                            ,hud_style, seats_min, seats_max
                                            ,h_hud_style, h_seats_min, h_seats_max)

            if hud_style == 'S' and h_hud_style == 'S':
                return stat_dict

        if hud_style == 'T':
            stylekey = self.date_ndays_ago
        elif hud_style == 'A':
            stylekey = '0000000'  # all stylekey values should be higher than this
        elif hud_style == 'S':
            stylekey = 'zzzzzzz'  # all stylekey values should be lower than this
        else:
            stylekey = '0000000'
            log.info('hud_style: %s' % hud_style)

        #elif hud_style == 'H':
        #    stylekey = date_nhands_ago  needs array by player here ...

        if h_hud_style == 'T':
            h_stylekey = self.h_date_ndays_ago
        elif h_hud_style == 'A':
            h_stylekey = '0000000'  # all stylekey values should be higher than this
        elif h_hud_style == 'S':
            h_stylekey = 'zzzzzzz'  # all stylekey values should be lower than this
        else:
            h_stylekey = '00000000'
            log.info('h_hud_style: %s' % h_hud_style)

        #elif h_hud_style == 'H':
        #    h_stylekey = date_nhands_ago  needs array by player here ...

        query = 'get_stats_from_hand_aggregated'
        subs = (hand
               ,hero_id, stylekey, agg_bb_mult, agg_bb_mult, seats_min, seats_max  # hero params
               ,hero_id, h_stylekey, h_agg_bb_mult, h_agg_bb_mult, h_seats_min, h_seats_max)    # villain params

        #print "get stats: hud style =", hud_style, "query =", query, "subs =", subs
        stime = time()
        c = self.connection.cursor()

        # Now get the stats
        c.execute(self.sql.query[query], subs)
        ptime = time() - stime
        log.info("HudCache query get_stats_from_hand_aggregated took %.3f seconds" % ptime)
        colnames = [desc[0] for desc in c.description]
        for row in c.fetchall():
            playerid = row[0]
            if (playerid == hero_id and h_hud_style != 'S') or (playerid != hero_id and hud_style != 'S'):
                t_dict = {}
                for name, val in zip(colnames, row):
                    t_dict[name.lower()] = val
                stat_dict[t_dict['player_id']] = t_dict

        return stat_dict

    # uses query on handsplayers instead of hudcache to get stats on just this session
    def get_stats_from_hand_session(self, hand, stat_dict, hero_id
                                   ,hud_style, seats_min, seats_max
                                   ,h_hud_style, h_seats_min, h_seats_max):
        """Get stats for just this session (currently defined as any play in the last 24 hours - to
           be improved at some point ...)
           h_hud_style and hud_style params indicate whether to get stats for hero and/or others
           - only fetch heroes stats if h_hud_style == 'S',
             and only fetch others stats if hud_style == 'S'
           seats_min/max params give seats limits, only include stats if between these values
        """

        query = self.sql.query['get_stats_from_hand_session']
        if self.db_server == 'mysql':
            query = query.replace("<signed>", 'signed ')
        else:
            query = query.replace("<signed>", '')

        subs = (self.hand_1day_ago, hand, hero_id, seats_min, seats_max
                                        , hero_id, h_seats_min, h_seats_max)
        c = self.get_cursor()

        # now get the stats
        #print "sess_stats: subs =", subs, "subs[0] =", subs[0]
        c.execute(query, subs)
        colnames = [desc[0] for desc in c.description]
        n = 0

        row = c.fetchone()
        if colnames[0].lower() == 'player_id':

            # Loop through stats adding them to appropriate stat_dict:
            while row:
                playerid = row[0]
                seats = row[1]
                if (playerid == hero_id and h_hud_style == 'S') or (playerid != hero_id and hud_style == 'S'):
                    for name, val in zip(colnames, row):
                        if not playerid in stat_dict:
                            stat_dict[playerid] = {}
                            stat_dict[playerid][name.lower()] = val
                        elif not name.lower() in stat_dict[playerid]:
                            stat_dict[playerid][name.lower()] = val
                        elif name.lower() not in ('hand_id', 'player_id', 'seat', 'screen_name', 'seats'):
                            #print "DEBUG: stat_dict[%s][%s]: %s" %(playerid, name.lower(), val)
                            stat_dict[playerid][name.lower()] += val
                    n += 1
                    if n >= 10000: break  # todo: don't think this is needed so set nice and high
                                          # prevents infinite loop so leave for now - comment out or remove?
                row = c.fetchone()
        else:
            log.error(_("ERROR: query %s result does not have player_id as first column") % (query,))

        #print "   %d rows fetched, len(stat_dict) = %d" % (n, len(stat_dict))

        #print "session stat_dict =", stat_dict
        #return stat_dict

    def get_player_id(self, config, siteName, playerName):
        c = self.connection.cursor()
        siteNameUtf = Charset.to_utf8(siteName)
        playerNameUtf = unicode(playerName)
        #print "db.get_player_id siteName",siteName,"playerName",playerName
        c.execute(self.sql.query['get_player_id'], (playerNameUtf, siteNameUtf))
        row = c.fetchone()
        if row:
            return row[0]
        else:
            return None

    def get_player_names(self, config, site_id=None, like_player_name="%"):
        """Fetch player names from players. Use site_id and like_player_name if provided"""

        if site_id is None:
            site_id = -1
        c = self.get_cursor()
        p_name = Charset.to_utf8(like_player_name)
        c.execute(self.sql.query['get_player_names'], (p_name, site_id, site_id))
        rows = c.fetchall()
        return rows

    def get_site_id(self, site):
        c = self.get_cursor()
        c.execute(self.sql.query['getSiteId'], (site,))
        result = c.fetchall()
        return result

    def resetCache(self):
        self.ttclean    = set()      # TourneyType clean
        self.gtcache    = None       # GameTypeId cache
        #self.ttcache    = None       # TourneyTypeId cache   
        self.tcache     = None       # TourneyId cache
        self.pcache     = None       # PlayerId cache
        self.tpcache    = None       # TourneysPlayersId cache

    def get_last_insert_id(self, cursor=None):
        ret = None
        try:
            if self.backend == self.MYSQL_INNODB:
                ret = self.connection.insert_id()
                if ret < 1 or ret > 999999999:
                    log.warning(_("getLastInsertId(): problem fetching insert_id? ret=%d") % ret)
                    ret = -1
            elif self.backend == self.PGSQL:
                # some options:
                # currval(hands_id_seq) - use name of implicit seq here
                # lastval() - still needs sequences set up?
                # insert ... returning  is useful syntax (but postgres specific?)
                # see rules (fancy trigger type things)
                c = self.get_cursor()
                ret = c.execute ("SELECT lastval()")
                row = c.fetchone()
                if not row:
                    log.warning(_("getLastInsertId(%s): problem fetching lastval? row=%d") % (seq, row))
                    ret = -1
                else:
                    ret = row[0]
            elif self.backend == self.SQLITE:
                ret = cursor.lastrowid
            else:
                log.error(_("getLastInsertId(): unknown backend: %d") % self.backend)
                ret = -1
        except:
            ret = -1
            err = traceback.extract_tb(sys.exc_info()[2])
            print _("*** Database get_last_insert_id error: ") + str(sys.exc_info()[1])
            print "\n".join( [e[0]+':'+str(e[1])+" "+e[2] for e in err] )
            raise
        return ret
    
    def prepareBulkImport(self):
        """Drop some indexes/foreign keys to prepare for bulk import.
           Currently keeping the standalone indexes as needed to import quickly"""
        stime = time()
        c = self.get_cursor()
        # sc: don't think autocommit=0 is needed, should already be in that mode
        if self.backend == self.MYSQL_INNODB:
            c.execute("SET foreign_key_checks=0")
            c.execute("SET autocommit=0")
            return
        if self.backend == self.PGSQL:
            self.connection.set_isolation_level(0)   # allow table/index operations to work
        for fk in self.foreignKeys[self.backend]:
            if fk['drop'] == 1:
                if self.backend == self.MYSQL_INNODB:
                    c.execute("SELECT constraint_name " +
                              "FROM information_schema.KEY_COLUMN_USAGE " +
                              #"WHERE REFERENCED_TABLE_SCHEMA = 'fpdb'
                              "WHERE 1=1 " +
                              "AND table_name = %s AND column_name = %s " +
                              "AND referenced_table_name = %s " +
                              "AND referenced_column_name = %s ",
                              (fk['fktab'], fk['fkcol'], fk['rtab'], fk['rcol']) )
                    cons = c.fetchone()
                    #print "preparebulk find fk: cons=", cons
                    if cons:
                        print "dropping mysql fk", cons[0], fk['fktab'], fk['fkcol']
                        try:
                            c.execute("alter table " + fk['fktab'] + " drop foreign key " + cons[0])
                        except:
                            print "    drop failed: " + str(sys.exc_info())
                elif self.backend == self.PGSQL:
    #    DON'T FORGET TO RECREATE THEM!!
                    print "dropping pg fk", fk['fktab'], fk['fkcol']
                    try:
                        # try to lock table to see if index drop will work:
                        # hmmm, tested by commenting out rollback in grapher. lock seems to work but
                        # then drop still hangs :-(  does work in some tests though??
                        # will leave code here for now pending further tests/enhancement ...
                        c.execute("BEGIN TRANSACTION")
                        c.execute( "lock table %s in exclusive mode nowait" % (fk['fktab'],) )
                        #print "after lock, status:", c.statusmessage
                        #print "alter table %s drop constraint %s_%s_fkey" % (fk['fktab'], fk['fktab'], fk['fkcol'])
                        try:
                            c.execute("alter table %s drop constraint %s_%s_fkey" % (fk['fktab'], fk['fktab'], fk['fkcol']))
                            print "dropped pg fk pg fk %s_%s_fkey, continuing ..." % (fk['fktab'], fk['fkcol'])
                        except:
                            if "does not exist" not in str(sys.exc_value):
                                print _("warning: drop pg fk %s_%s_fkey failed: %s, continuing ...") \
                                      % (fk['fktab'], fk['fkcol'], str(sys.exc_value).rstrip('\n') )
                        c.execute("END TRANSACTION")
                    except:
                        print _("warning: constraint %s_%s_fkey not dropped: %s, continuing ...") \
                              % (fk['fktab'],fk['fkcol'], str(sys.exc_value).rstrip('\n'))
                else:
                    return -1

        for idx in self.indexes[self.backend]:
            if idx['drop'] == 1:
                if self.backend == self.MYSQL_INNODB:
                    print _("dropping mysql index "), idx['tab'], idx['col']
                    try:
                        # apparently nowait is not implemented in mysql so this just hangs if there are locks
                        # preventing the index drop :-(
                        c.execute( "alter table %s drop index %s;", (idx['tab'],idx['col']) )
                    except:
                        print _("    drop index failed: ") + str(sys.exc_info())
                            # ALTER TABLE `fpdb`.`handsplayers` DROP INDEX `playerId`;
                            # using: 'HandsPlayers' drop index 'playerId'
                elif self.backend == self.PGSQL:
    #    DON'T FORGET TO RECREATE THEM!!
                    print _("dropping pg index "), idx['tab'], idx['col']
                    try:
                        # try to lock table to see if index drop will work:
                        c.execute("BEGIN TRANSACTION")
                        c.execute( "lock table %s in exclusive mode nowait" % (idx['tab'],) )
                        #print "after lock, status:", c.statusmessage
                        try:
                            # table locked ok so index drop should work:
                            #print "drop index %s_%s_idx" % (idx['tab'],idx['col'])
                            c.execute( "drop index if exists %s_%s_idx" % (idx['tab'],idx['col']) )
                            #print "dropped  pg index ", idx['tab'], idx['col']
                        except:
                            if "does not exist" not in str(sys.exc_value):
                                print _("warning: drop index %s_%s_idx failed: %s, continuing ...") \
                                      % (idx['tab'],idx['col'], str(sys.exc_value).rstrip('\n'))
                        c.execute("END TRANSACTION")
                    except:
                        print _("warning: index %s_%s_idx not dropped %s, continuing ...") \
                              % (idx['tab'],idx['col'], str(sys.exc_value).rstrip('\n'))
                else:
                    return -1

        if self.backend == self.PGSQL:
            self.connection.set_isolation_level(1)   # go back to normal isolation level
        self.commit() # seems to clear up errors if there were any in postgres
        ptime = time() - stime
        print (_("prepare import took %s seconds") % ptime)
    #end def prepareBulkImport

    def afterBulkImport(self):
        """Re-create any dropped indexes/foreign keys after bulk import"""
        stime = time()

        c = self.get_cursor()
        if self.backend == self.MYSQL_INNODB:
            c.execute("SET foreign_key_checks=1")
            c.execute("SET autocommit=1")
            return

        if self.backend == self.PGSQL:
            self.connection.set_isolation_level(0)   # allow table/index operations to work
        for fk in self.foreignKeys[self.backend]:
            if fk['drop'] == 1:
                if self.backend == self.MYSQL_INNODB:
                    c.execute("SELECT constraint_name " +
                              "FROM information_schema.KEY_COLUMN_USAGE " +
                              #"WHERE REFERENCED_TABLE_SCHEMA = 'fpdb'
                              "WHERE 1=1 " +
                              "AND table_name = %s AND column_name = %s " +
                              "AND referenced_table_name = %s " +
                              "AND referenced_column_name = %s ",
                              (fk['fktab'], fk['fkcol'], fk['rtab'], fk['rcol']) )
                    cons = c.fetchone()
                    #print "afterbulk: cons=", cons
                    if cons:
                        pass
                    else:
                        print _("Creating foreign key "), fk['fktab'], fk['fkcol'], "->", fk['rtab'], fk['rcol']
                        try:
                            c.execute("alter table " + fk['fktab'] + " add foreign key ("
                                      + fk['fkcol'] + ") references " + fk['rtab'] + "("
                                      + fk['rcol'] + ")")
                        except:
                            print _("Create foreign key failed: ") + str(sys.exc_info())
                elif self.backend == self.PGSQL:
                    print _("Creating foreign key "), fk['fktab'], fk['fkcol'], "->", fk['rtab'], fk['rcol']
                    try:
                        c.execute("alter table " + fk['fktab'] + " add constraint "
                                  + fk['fktab'] + '_' + fk['fkcol'] + '_fkey'
                                  + " foreign key (" + fk['fkcol']
                                  + ") references " + fk['rtab'] + "(" + fk['rcol'] + ")")
                    except:
                        print _("Create foreign key failed: ") + str(sys.exc_info())
                else:
                    return -1

        for idx in self.indexes[self.backend]:
            if idx['drop'] == 1:
                if self.backend == self.MYSQL_INNODB:
                    print _("Creating MySQL index %s %s") % (idx['tab'], idx['col'])
                    try:
                        s = "alter table %s add index %s(%s)" % (idx['tab'],idx['col'],idx['col'])
                        c.execute(s)
                    except:
                        print _("Create foreign key failed: ") + str(sys.exc_info())
                elif self.backend == self.PGSQL:
    #                pass
                    # mod to use tab_col for index name?
                    print _("Creating PostgreSQL index "), idx['tab'], idx['col']
                    try:
                        s = "create index %s_%s_idx on %s(%s)" % (idx['tab'], idx['col'], idx['tab'], idx['col'])
                        c.execute(s)
                    except:
                        print _("Create index failed: ") + str(sys.exc_info())
                else:
                    return -1

        if self.backend == self.PGSQL:
            self.connection.set_isolation_level(1)   # go back to normal isolation level
        self.commit()   # seems to clear up errors if there were any in postgres
        atime = time() - stime
        print (_("After import took %s seconds") % atime)
    #end def afterBulkImport

    def drop_referential_integrity(self):
        """Update all tables to remove foreign keys"""

        c = self.get_cursor()
        c.execute(self.sql.query['list_tables'])
        result = c.fetchall()

        for i in range(len(result)):
            c.execute("SHOW CREATE TABLE " + result[i][0])
            inner = c.fetchall()

            for j in range(len(inner)):
            # result[i][0] - Table name
            # result[i][1] - CREATE TABLE parameters
            #Searching for CONSTRAINT `tablename_ibfk_1`
                for m in re.finditer('(ibfk_[0-9]+)', inner[j][1]):
                    key = "`" + inner[j][0] + "_" + m.group() + "`"
                    c.execute("ALTER TABLE " + inner[j][0] + " DROP FOREIGN KEY " + key)
                self.commit()
    #end drop_referential_inegrity

    def recreate_tables(self):
        """(Re-)creates the tables of the current DB"""

        self.drop_tables()
        self.resetCache()
        self.resetBulkCache()
        self.create_tables()
        self.createAllIndexes()
        self.commit()
        self.get_sites()
        log.info(_("Finished recreating tables"))
    #end def recreate_tables

    def create_tables(self):
        log.debug(self.sql.query['createSettingsTable'])
        c = self.get_cursor()
        c.execute(self.sql.query['createSettingsTable'])

        log.debug("Creating tables")
        c.execute(self.sql.query['createActionsTable'])
        c.execute(self.sql.query['createSitesTable'])
        c.execute(self.sql.query['createGametypesTable'])
        c.execute(self.sql.query['createFilesTable'])
        c.execute(self.sql.query['createPlayersTable'])
        c.execute(self.sql.query['createAutoratesTable'])
        c.execute(self.sql.query['createSessionsCacheTable'])
        c.execute(self.sql.query['createTourneyTypesTable'])
        c.execute(self.sql.query['createTourneysTable'])
        c.execute(self.sql.query['createTourneysPlayersTable'])
        c.execute(self.sql.query['createGamesCacheTable'])
        c.execute(self.sql.query['createHandsTable'])
        c.execute(self.sql.query['createHandsPlayersTable'])
        c.execute(self.sql.query['createHandsActionsTable'])
        c.execute(self.sql.query['createHandsStoveTable'])
        c.execute(self.sql.query['createHudCacheTable'])
        c.execute(self.sql.query['createCardsCacheTable'])
        c.execute(self.sql.query['createPositionsCacheTable'])
        c.execute(self.sql.query['createBoardsTable'])
        c.execute(self.sql.query['createBackingsTable'])
        c.execute(self.sql.query['createRawHands'])
        c.execute(self.sql.query['createRawTourneys'])

        # Create unique indexes:
        log.debug("Creating unique indexes")
        c.execute(self.sql.query['addTourneyIndex'])
        c.execute(self.sql.query['addHandsIndex'])
        c.execute(self.sql.query['addPlayersIndex'])
        c.execute(self.sql.query['addTPlayersIndex'])

        c.execute(self.sql.query['addHudCacheCompundIndex'])
        c.execute(self.sql.query['addCardsCacheCompundIndex'])
        c.execute(self.sql.query['addPositionsCacheCompundIndex'])

        self.fillDefaultData()
        self.commit()

    def drop_tables(self):
        """Drops the fpdb tables from the current db"""
        c = self.get_cursor()

        backend = self.get_backend_name()
        if backend == 'MySQL InnoDB': # what happens if someone is using MyISAM?
            try:
                self.drop_referential_integrity() # needed to drop tables with foreign keys
                c.execute(self.sql.query['list_tables'])
                tables = c.fetchall()
                for table in tables:
                    c.execute(self.sql.query['drop_table'] + table[0])
            except:
                err = traceback.extract_tb(sys.exc_info()[2])[-1]
                print _("***Error dropping tables:"), +err[2]+"("+str(err[1])+"): "+str(sys.exc_info()[1])
                self.rollback()
        elif backend == 'PostgreSQL':
            try:
                self.commit()
                c.execute(self.sql.query['list_tables'])
                tables = c.fetchall()
                for table in tables:
                    c.execute(self.sql.query['drop_table'] + table[0] + ' cascade')
            except:
                err = traceback.extract_tb(sys.exc_info()[2])[-1]
                print _("***Error dropping tables:"), err[2]+"("+str(err[1])+"): "+str(sys.exc_info()[1])
                self.rollback()
        elif backend == 'SQLite':
            c.execute(self.sql.query['list_tables'])
            for table in c.fetchall():
                if table[0] != 'sqlite_stat1':
                    log.info("%s '%s'" % (self.sql.query['drop_table'], table[0]))
                    c.execute(self.sql.query['drop_table'] + table[0])
        self.commit()
    #end def drop_tables

    def createAllIndexes(self):
        """Create new indexes"""

        if self.backend == self.PGSQL:
            self.connection.set_isolation_level(0)   # allow table/index operations to work
        c = self.get_cursor()
        for idx in self.indexes[self.backend]:
            log.info(_("Creating index %s %s") %(idx['tab'], idx['col']))
            if self.backend == self.MYSQL_INNODB:
                s = "CREATE INDEX %s ON %s(%s)" % (idx['col'],idx['tab'],idx['col'])
                c.execute(s)
            elif self.backend == self.PGSQL or self.backend == self.SQLITE:
                s = "CREATE INDEX %s_%s_idx ON %s(%s)" % (idx['tab'], idx['col'], idx['tab'], idx['col'])
                c.execute(s)

        if self.backend == self.PGSQL:
            self.connection.set_isolation_level(1)   # go back to normal isolation level
    #end def createAllIndexes

    def dropAllIndexes(self):
        """Drop all standalone indexes (i.e. not including primary keys or foreign keys)
           using list of indexes in indexes data structure"""
        # maybe upgrade to use data dictionary?? (but take care to exclude PK and FK)
        if self.backend == self.PGSQL:
            self.connection.set_isolation_level(0)   # allow table/index operations to work
        for idx in self.indexes[self.backend]:
            if self.backend == self.MYSQL_INNODB:
                print (_("Dropping index:"), idx['tab'], idx['col'])
                try:
                    self.get_cursor().execute( "alter table %s drop index %s"
                                             , (idx['tab'], idx['col']) )
                except:
                    print _("Drop index failed:"), str(sys.exc_info())
            elif self.backend == self.PGSQL:
                print (_("Dropping index:"), idx['tab'], idx['col'])
                # mod to use tab_col for index name?
                try:
                    self.get_cursor().execute( "drop index %s_%s_idx"
                                               % (idx['tab'],idx['col']) )
                except:
                    print (_("Drop index failed:"), str(sys.exc_info()))
            elif self.backend == self.SQLITE:
                print (_("Dropping index:"), idx['tab'], idx['col'])
                try:
                    self.get_cursor().execute( "drop index %s_%s_idx"
                                               % (idx['tab'],idx['col']) )
                except:
                    print _("Drop index failed:"), str(sys.exc_info())
            else:
                return -1
        if self.backend == self.PGSQL:
            self.connection.set_isolation_level(1)   # go back to normal isolation level
    #end def dropAllIndexes

    def createAllForeignKeys(self):
        """Create foreign keys"""

        try:
            if self.backend == self.PGSQL:
                self.connection.set_isolation_level(0)   # allow table/index operations to work
            c = self.get_cursor()
        except:
            print _("set_isolation_level failed:"), str(sys.exc_info())

        for fk in self.foreignKeys[self.backend]:
            if self.backend == self.MYSQL_INNODB:
                c.execute("SELECT constraint_name " +
                          "FROM information_schema.KEY_COLUMN_USAGE " +
                          #"WHERE REFERENCED_TABLE_SCHEMA = 'fpdb'
                          "WHERE 1=1 " +
                          "AND table_name = %s AND column_name = %s " +
                          "AND referenced_table_name = %s " +
                          "AND referenced_column_name = %s ",
                          (fk['fktab'], fk['fkcol'], fk['rtab'], fk['rcol']) )
                cons = c.fetchone()
                #print "afterbulk: cons=", cons
                if cons:
                    pass
                else:
                    print _("Creating foreign key:"), fk['fktab'], fk['fkcol'], "->", fk['rtab'], fk['rcol']
                    try:
                        c.execute("alter table " + fk['fktab'] + " add foreign key ("
                                  + fk['fkcol'] + ") references " + fk['rtab'] + "("
                                  + fk['rcol'] + ")")
                    except:
                        print _("Create foreign key failed:"), str(sys.exc_info())
            elif self.backend == self.PGSQL:
                print _("Creating foreign key:"), fk['fktab'], fk['fkcol'], "->", fk['rtab'], fk['rcol']
                try:
                    c.execute("alter table " + fk['fktab'] + " add constraint "
                              + fk['fktab'] + '_' + fk['fkcol'] + '_fkey'
                              + " foreign key (" + fk['fkcol']
                              + ") references " + fk['rtab'] + "(" + fk['rcol'] + ")")
                except:
                    print _("Create foreign key failed:"), str(sys.exc_info())
            else:
                pass

        try:
            if self.backend == self.PGSQL:
                self.connection.set_isolation_level(1)   # go back to normal isolation level
        except:
            print _("set_isolation_level failed:"), str(sys.exc_info())
    #end def createAllForeignKeys

    def dropAllForeignKeys(self):
        """Drop all standalone indexes (i.e. not including primary keys or foreign keys)
           using list of indexes in indexes data structure"""
        # maybe upgrade to use data dictionary?? (but take care to exclude PK and FK)
        if self.backend == self.PGSQL:
            self.connection.set_isolation_level(0)   # allow table/index operations to work
        c = self.get_cursor()

        for fk in self.foreignKeys[self.backend]:
            if self.backend == self.MYSQL_INNODB:
                c.execute("SELECT constraint_name " +
                          "FROM information_schema.KEY_COLUMN_USAGE " +
                          #"WHERE REFERENCED_TABLE_SCHEMA = 'fpdb'
                          "WHERE 1=1 " +
                          "AND table_name = %s AND column_name = %s " +
                          "AND referenced_table_name = %s " +
                          "AND referenced_column_name = %s ",
                          (fk['fktab'], fk['fkcol'], fk['rtab'], fk['rcol']) )
                cons = c.fetchone()
                #print "preparebulk find fk: cons=", cons
                if cons:
                    print _("Dropping foreign key:"), cons[0], fk['fktab'], fk['fkcol']
                    try:
                        c.execute("alter table " + fk['fktab'] + " drop foreign key " + cons[0])
                    except:
                        print _("Warning:"), _("Drop foreign key %s_%s_fkey failed: %s, continuing ...") \
                                  % (fk['fktab'], fk['fkcol'], str(sys.exc_value).rstrip('\n') )
            elif self.backend == self.PGSQL:
#    DON'T FORGET TO RECREATE THEM!!
                print _("Dropping foreign key:"), fk['fktab'], fk['fkcol']
                try:
                    # try to lock table to see if index drop will work:
                    # hmmm, tested by commenting out rollback in grapher. lock seems to work but
                    # then drop still hangs :-(  does work in some tests though??
                    # will leave code here for now pending further tests/enhancement ...
                    c.execute("BEGIN TRANSACTION")
                    c.execute( "lock table %s in exclusive mode nowait" % (fk['fktab'],) )
                    #print "after lock, status:", c.statusmessage
                    #print "alter table %s drop constraint %s_%s_fkey" % (fk['fktab'], fk['fktab'], fk['fkcol'])
                    try:
                        c.execute("alter table %s drop constraint %s_%s_fkey" % (fk['fktab'], fk['fktab'], fk['fkcol']))
                        print _("dropped foreign key %s_%s_fkey, continuing ...") % (fk['fktab'], fk['fkcol'])
                    except:
                        if "does not exist" not in str(sys.exc_value):
                            print _("Warning:"), _("Drop foreign key %s_%s_fkey failed: %s, continuing ...") \
                                  % (fk['fktab'], fk['fkcol'], str(sys.exc_value).rstrip('\n') )
                    c.execute("END TRANSACTION")
                except:
                    print _("Warning:"), _("constraint %s_%s_fkey not dropped: %s, continuing ...") \
                          % (fk['fktab'],fk['fkcol'], str(sys.exc_value).rstrip('\n'))
            else:
                #print _("Only MySQL and Postgres supported so far")
                pass

        if self.backend == self.PGSQL:
            self.connection.set_isolation_level(1)   # go back to normal isolation level
    #end def dropAllForeignKeys


    def fillDefaultData(self):
        c = self.get_cursor()
        c.execute("INSERT INTO Settings (version) VALUES (%s);" % (DB_VERSION))
        #Fill Sites
        c.execute("INSERT INTO Sites (id,name,code) VALUES ('1', 'Full Tilt Poker', 'FT')")
        c.execute("INSERT INTO Sites (id,name,code) VALUES ('2', 'PokerStars', 'PS')")
        c.execute("INSERT INTO Sites (id,name,code) VALUES ('3', 'Everleaf', 'EV')")
        c.execute("INSERT INTO Sites (id,name,code) VALUES ('4', 'Boss', 'BM')")
        c.execute("INSERT INTO Sites (id,name,code) VALUES ('5', 'OnGame', 'OG')")
        c.execute("INSERT INTO Sites (id,name,code) VALUES ('6', 'UltimateBet', 'UB')")
        c.execute("INSERT INTO Sites (id,name,code) VALUES ('7', 'Betfair', 'BF')")
        c.execute("INSERT INTO Sites (id,name,code) VALUES ('8', 'Absolute', 'AB')")
        c.execute("INSERT INTO Sites (id,name,code) VALUES ('9', 'PartyPoker', 'PP')")
        c.execute("INSERT INTO Sites (id,name,code) VALUES ('10', 'PacificPoker', 'P8')")
        c.execute("INSERT INTO Sites (id,name,code) VALUES ('11', 'Partouche', 'PA')")
        c.execute("INSERT INTO Sites (id,name,code) VALUES ('12', 'Merge', 'MN')")
        c.execute("INSERT INTO Sites (id,name,code) VALUES ('13', 'PKR', 'PK')")
        c.execute("INSERT INTO Sites (id,name,code) VALUES ('14', 'iPoker', 'IP')")
        c.execute("INSERT INTO Sites (id,name,code) VALUES ('15', 'Winamax', 'WM')")
        c.execute("INSERT INTO Sites (id,name,code) VALUES ('16', 'Everest', 'EP')")
        c.execute("INSERT INTO Sites (id,name,code) VALUES ('17', 'Cake', 'CK')")
        c.execute("INSERT INTO Sites (id,name,code) VALUES ('18', 'Entraction', 'TR')")
        c.execute("INSERT INTO Sites (id,name,code) VALUES ('19', 'BetOnline', 'BO')")
        c.execute("INSERT INTO Sites (id,name,code) VALUES ('20', 'Microgaming', 'MG')")
        #Fill Actions
        c.execute("INSERT INTO Actions (id,name,code) VALUES ('1', 'ante', 'A')")
        c.execute("INSERT INTO Actions (id,name,code) VALUES ('2', 'small blind', 'SB')")
        c.execute("INSERT INTO Actions (id,name,code) VALUES ('3', 'secondsb', 'SSB')")
        c.execute("INSERT INTO Actions (id,name,code) VALUES ('4', 'big blind', 'BB')")
        c.execute("INSERT INTO Actions (id,name,code) VALUES ('5', 'both', 'SBBB')")
        c.execute("INSERT INTO Actions (id,name,code) VALUES ('6', 'calls', 'C')")
        c.execute("INSERT INTO Actions (id,name,code) VALUES ('7', 'raises', 'R')")
        c.execute("INSERT INTO Actions (id,name,code) VALUES ('8', 'bets', 'B')")
        c.execute("INSERT INTO Actions (id,name,code) VALUES ('9', 'stands pat', 'S')")
        c.execute("INSERT INTO Actions (id,name,code) VALUES ('10', 'folds', 'F')")
        c.execute("INSERT INTO Actions (id,name,code) VALUES ('11', 'checks', 'K')")
        c.execute("INSERT INTO Actions (id,name,code) VALUES ('12', 'discards', 'D')")
        c.execute("INSERT INTO Actions (id,name,code) VALUES ('13', 'bringin', 'I')")
        c.execute("INSERT INTO Actions (id,name,code) VALUES ('14', 'completes', 'P')")

    #end def fillDefaultData

    def rebuild_indexes(self, start=None):
        self.dropAllIndexes()
        self.createAllIndexes()
        self.dropAllForeignKeys()
        self.createAllForeignKeys()
    #end def rebuild_indexes
    
    def replace_statscache(self, query):
        if self.build_full_hudcache:
            query = query.replace('<seat_num>', "h.seats as seat_num")
            query = query.replace('<hc_position>', """case when hp.position = 'B' then 'B'
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
                   end                                            as hc_position""")
            if self.backend == self.PGSQL:
                query = query.replace('<styleKey>', "'d' || to_char(h.startTime, 'YYMMDD')")
                query = query.replace('<styleKeyGroup>', ",to_char(h.startTime, 'YYMMDD')")
            elif self.backend == self.SQLITE:
                query = query.replace('<styleKey>', "'d' || substr(strftime('%Y%m%d', h.startTime),3,7)")
                query = query.replace('<styleKeyGroup>', ",substr(strftime('%Y%m%d', h.startTime),3,7)")
            elif self.backend == self.MYSQL_INNODB:
                query = query.replace('<styleKey>', "date_format(h.startTime, 'd%y%m%d')")
                query = query.replace('<styleKeyGroup>', ",date_format(h.startTime, 'd%y%m%d')")
        else:
            query = query.replace('<seat_num>', "'0' as seat_num")
            query = query.replace('<hc_position>', "'0' as hc_position")
            query = query.replace('<styleKey>', "'A000000' as styleKey")
            query = query.replace('<styleKeyGroup>', ',styleKey')
        return query

    def rebuild_hudcache(self, h_start=None, v_start=None, ttid = None):
        """clears hudcache and rebuilds from the individual handsplayers records"""
        stime = time()
        # derive list of program owner's player ids
        self.hero = {}                               # name of program owner indexed by site id
        self.hero_ids = {'dummy':-53, 'dummy2':-52}  # playerid of owner indexed by site id
                                                     # make sure at least two values in list
                                                     # so that tuple generation creates doesn't use
                                                     # () or (1,) style
        for site in self.config.get_supported_sites():
            result = self.get_site_id(site)
            if result:
                site_id = result[0][0]
                self.hero[site_id] = self.config.supported_sites[site].screen_name
                p_id = self.get_player_id(self.config, site, self.hero[site_id])
                if p_id:
                    self.hero_ids[site_id] = int(p_id)

        if h_start is None:
            h_start = self.hero_hudstart_def
        if v_start is None:
            v_start = self.villain_hudstart_def

        if self.hero_ids == {}:
            where = "WHERE hp.tourneysPlayersId IS NULL"
        else:
            where =   "where (((    hp.playerId not in " + str(tuple(self.hero_ids.values())) \
                    + "       and h.startTime > '" + v_start + "')" \
                    + "   or (    hp.playerId in " + str(tuple(self.hero_ids.values())) \
                    + "       and h.startTime > '" + h_start + "'))" \
                    + "   AND hp.tourneysPlayersId IS NULL)"
        rebuild_sql_cash = self.sql.query['rebuildHudCache'].replace('<tourney_insert_clause>', "")
        rebuild_sql_cash = rebuild_sql_cash.replace('<tourney_select_clause>', "")
        rebuild_sql_cash = rebuild_sql_cash.replace('<tourney_join_clause>', "")
        rebuild_sql_cash = rebuild_sql_cash.replace('<tourney_group_clause>', "")
        rebuild_sql_cash = rebuild_sql_cash.replace('<where_clause>', where)
        rebuild_sql_cash = self.replace_statscache(rebuild_sql_cash)
        if not ttid:
            self.get_cursor().execute(self.sql.query['clearHudCache'])
            self.get_cursor().execute(rebuild_sql_cash)
            #print _("Rebuild hudcache(cash) took %.1f seconds") % (time() - stime,)

        if self.hero_ids == {}:
            where = "WHERE hp.tourneysPlayersId >= 0"
        elif ttid:
            where = "WHERE t.tourneyTypeId = %s" % ttid
        else:
            where =   "where (((    hp.playerId not in " + str(tuple(self.hero_ids.values())) \
                    + "       and h.startTime > '" + v_start + "')" \
                    + "   or (    hp.playerId in " + str(tuple(self.hero_ids.values())) \
                    + "       and h.startTime > '" + h_start + "'))" \
                    + "   AND hp.tourneysPlayersId >= 0)"
        rebuild_sql_tourney = self.sql.query['rebuildHudCache'].replace('<tourney_insert_clause>', ",tourneyTypeId")
        rebuild_sql_tourney = rebuild_sql_tourney.replace('<tourney_select_clause>', ",t.tourneyTypeId")
        rebuild_sql_tourney = rebuild_sql_tourney.replace('<tourney_join_clause>', """INNER JOIN TourneysPlayers tp ON (tp.id = hp.tourneysPlayersId)
            INNER JOIN Tourneys t ON (t.id = tp.tourneyId)""")
        rebuild_sql_tourney = rebuild_sql_tourney.replace('<tourney_group_clause>', ",t.tourneyTypeId")
        rebuild_sql_tourney = rebuild_sql_tourney.replace('<where_clause>', where)
        rebuild_sql_tourney = self.replace_statscache(rebuild_sql_tourney)
        self.get_cursor().execute(rebuild_sql_tourney)
        self.commit()
        #print _("Rebuild hudcache took %.1f seconds") % (time() - stime,)
    #end def rebuild_hudcache
    
    def rebuild_sessionscache(self, tz_name = None):
        """clears sessionscache and rebuilds from the individual records"""
        heroes, hero, = [], {}
        c = self.get_cursor()
        c.execute("SELECT playerId FROM GamesCache GROUP BY playerId")
        herorecords_cash = c.fetchall()
        for h in herorecords_cash:
            heroes += h
        c.execute("SELECT playerId FROM TourneysPlayers WHERE startTime is not NULL GROUP BY playerId")
        herorecords_tour = c.fetchall()
        for h in herorecords_tour:
            if h not in heroes:
                heroes += h
        if not heroes:
            for site in self.config.get_supported_sites():
                result = self.get_site_id(site)
                if result:
                    site_id = result[0][0]
                    hero[site_id] = self.config.supported_sites[site].screen_name
                    p_id = self.get_player_id(self.config, site, hero[site_id])
                    if p_id:
                        heroes.append(int(p_id))
                                
        rebuildSessionsCache    = self.sql.query['rebuildSessionsCache']
        if len(heroes) == 0:
            where         = '0'
            where_summary = '0'
        elif len(heroes) > 0:
            where         = str(heroes[0])
            where_summary = str(heroes[0])
            if len(heroes) > 1:
                for i in heroes:
                    if i != heroes[0]:
                        where = where + ' OR HandsPlayers.playerId = %s' % str(i)
        rebuildSessionsCache     = rebuildSessionsCache.replace('<where_clause>', where)
        rebuildSessionsCacheRing = rebuildSessionsCache.replace('<tourney_join_clause>','')
        rebuildSessionsCacheRing = rebuildSessionsCacheRing.replace('<tourney_type_clause>','NULL,')
        rebuildSessionsCacheTour = rebuildSessionsCache.replace('<tourney_join_clause>',"""INNER JOIN Tourneys ON (Tourneys.id = Hands.tourneyId)""")
        rebuildSessionsCacheTour = rebuildSessionsCacheTour.replace('<tourney_type_clause>','HandsPlayers.tourneysPlayersId,')
        rebuildSessionsCacheRing = rebuildSessionsCacheRing.replace('%s', self.sql.query['placeholder'])
        rebuildSessionsCacheTour = rebuildSessionsCacheTour.replace('%s', self.sql.query['placeholder'])

        max, queries, type = [], [rebuildSessionsCacheTour, rebuildSessionsCacheRing], ['tour', 'ring']
        c = self.get_cursor()
        c.execute("SELECT count(H.id) FROM Hands H INNER JOIN Gametypes G ON (G.id = H.gametypeId) WHERE G.type='tour'")
        max.append(c.fetchone()[0])
        c.execute("SELECT count(H.id) FROM Hands H INNER JOIN Gametypes G ON (G.id = H.gametypeId) WHERE G.type='ring'")
        max.append(c.fetchone()[0])
        c.execute(self.sql.query['clear_GC_H'])
        c.execute(self.sql.query['clear_SC_H'])
        c.execute(self.sql.query['clear_SC_T'])
        c.execute(self.sql.query['clear_SC_GC'])
        c.execute(self.sql.query['clear_SC_TP'])
        c.execute(self.sql.query['clearGamesCache'])
        c.execute(self.sql.query['clearSessionsCache'])
        self.commit()
        
        for k in range(2):
            start, limit =  0, 5000
            while start < max[k]:
                hid = {}
                self.resetBulkCache()
                c.execute(queries[k], (type[k], limit, start))
                tmp = c.fetchone()
                while tmp:
                    pids, game, pdata = {}, {}, {}
                    pdata['pname'] = {}
                    id                                    = tmp[0]
                    startTime                             = tmp[1]
                    pids['pname']                         = tmp[2]
                    tid                                   = tmp[3]
                    gtid                                  = tmp[4]
                    game['type']                          = tmp[5]
                    pdata['pname']['tourneysPlayersIds']  = tmp[6]
                    pdata['pname']['totalProfit']         = tmp[7]
                    pdata['pname']['rake']                = tmp[8]
                    pdata['pname']['allInEV']             = tmp[9]
                    pdata['pname']['street0VPI']          = tmp[10]
                    pdata['pname']['street1Seen']         = tmp[11]
                    pdata['pname']['sawShowdown']         = tmp[12]
                    tmp = c.fetchone()
                    hid[id] = tid
                    self.storeSessionsCache (id, pids, startTime, heroes, tmp == None)
                    self.storeGamesCache(id, pids, startTime, gtid, game, pdata, tz_name, heroes, tmp == None)
                    self.updateTourneysPlayersSessions(pids, tid, startTime, pdata, heroes, tmp == None)
                    if tmp == None:
                        for i, id in self.sc.iteritems():
                            if i!='bk':
                                sid =  id['id']
                                if hid[i]: 
                                    self.tbulk[hid[i]] = sid
                                    gid = None
                                else: gid = self.gc[i]['id']
                                q = self.sql.query['update_RSC_H']
                                q = q.replace('%s', self.sql.query['placeholder'])
                                c.execute(q, (sid, gid, i))
                        self.updateTourneysSessions()
                        self.commit()
                        break
                start += limit
            self.commit()
        self.commit()        

    def get_hero_hudcache_start(self):
        """fetches earliest stylekey from hudcache for one of hero's player ids"""

        try:
            # derive list of program owner's player ids
            self.hero = {}                               # name of program owner indexed by site id
            self.hero_ids = {'dummy':-53, 'dummy2':-52}  # playerid of owner indexed by site id
                                                         # make sure at least two values in list
                                                         # so that tuple generation creates doesn't use
                                                         # () or (1,) style
            for site in self.config.get_supported_sites():
                result = self.get_site_id(site)
                if result:
                    site_id = result[0][0]
                    self.hero[site_id] = self.config.supported_sites[site].screen_name
                    p_id = self.get_player_id(self.config, site, self.hero[site_id])
                    if p_id:
                        self.hero_ids[site_id] = int(p_id)

            q = self.sql.query['get_hero_hudcache_start'].replace("<playerid_list>", str(tuple(self.hero_ids.values())))
            c = self.get_cursor()
            c.execute(q)
            tmp = c.fetchone()
            if tmp == (None,):
                return self.hero_hudstart_def
            else:
                return "20"+tmp[0][1:3] + "-" + tmp[0][3:5] + "-" + tmp[0][5:7]
        except:
            err = traceback.extract_tb(sys.exc_info()[2])[-1]
            print _("Error rebuilding hudcache:"), str(sys.exc_value)
            print err
    #end def get_hero_hudcache_start


    def analyzeDB(self):
        """Do whatever the DB can offer to update index/table statistics"""
        stime = time()
        if self.backend == self.MYSQL_INNODB or self.backend == self.SQLITE:
            try:
                self.get_cursor().execute(self.sql.query['analyze'])
            except:
                print _("Error during analyze:"), str(sys.exc_value)
        elif self.backend == self.PGSQL:
            self.connection.set_isolation_level(0)   # allow analyze to work
            try:
                self.get_cursor().execute(self.sql.query['analyze'])
            except:
                print _("Error during analyze:"), str(sys.exc_value)
            self.connection.set_isolation_level(1)   # go back to normal isolation level
        self.commit()
        atime = time() - stime
        log.info(_("Analyze took %.1f seconds") % (atime,))
    #end def analyzeDB

    def vacuumDB(self):
        """Do whatever the DB can offer to update index/table statistics"""
        stime = time()
        if self.backend == self.MYSQL_INNODB or self.backend == self.SQLITE:
            try:
                self.get_cursor().execute(self.sql.query['vacuum'])
            except:
                print _("Error during vacuum:"), str(sys.exc_value)
        elif self.backend == self.PGSQL:
            self.connection.set_isolation_level(0)   # allow vacuum to work
            try:
                self.get_cursor().execute(self.sql.query['vacuum'])
            except:
                print _("Error during vacuum:"), str(sys.exc_value)
            self.connection.set_isolation_level(1)   # go back to normal isolation level
        self.commit()
        atime = time() - stime
        print _("Vacuum took %.1f seconds") % (atime,)
    #end def analyzeDB

# Start of Hand Writing routines. Idea is to provide a mixture of routines to store Hand data
# however the calling prog requires. Main aims:
# - existing static routines from fpdb_simple just modified

    def setThreadId(self, threadid):
        self.threadId = threadid
                
    def acquireLock(self, wait=True, retry_time=.01):
        while not self._has_lock:
            cursor = self.get_cursor()
            num = cursor.execute(self.sql.query['switchLockOn'], (True, self.threadId))
            self.commit()
            if (self.backend == self.MYSQL_INNODB and num == 0):
                if not wait:
                    return False
                sleep(retry_time)
            else:
                self._has_lock = True
                return True
    
    def releaseLock(self):
        if self._has_lock:
            cursor = self.get_cursor()
            num = cursor.execute(self.sql.query['switchLockOff'], (False, self.threadId))
            self.commit()
            self._has_lock = False

    def lock_for_insert(self):
        """Lock tables in MySQL to try to speed inserts up"""
        try:
            self.get_cursor().execute(self.sql.query['lockForInsert'])
        except:
            print _("Error during lock_for_insert:"), str(sys.exc_value)
    #end def lock_for_insert
    
    def resetBulkCache(self, reconnect=False):
        self.siteHandNos = []         # cache of siteHandNo
        self.hbulk       = []         # Hands bulk inserts
        self.bbulk       = []         # Boards bulk inserts
        self.hpbulk      = []         # HandsPlayers bulk inserts
        self.habulk      = []         # HandsActions bulk inserts
        self.hcbulk      = {}         # HudCache bulk inserts
        self.dcbulk      = {}
        self.pcbulk      = {}
        self.hsbulk      = []         # HandsStove bulk inserts
        self.tbulk       = {}         # Tourneys bulk updates
        self.tpbulk      = []         # TourneysPlayers bulk updates
        self.sc          = {'bk': []} # SessionsCache bulk updates
        self.gc          = {'bk': []} # GamesCache bulk updates
        self.tc          = {}         # TourneysPlayers bulk updates
        if reconnect: self.do_connect(self.config)
        
    def executemany(self, c, q, values):
        batch_size=20000 #experiment to find optimal batch_size for your data
        while values: # repeat until all records in values have been inserted ''
            batch, values = values[:batch_size], values[batch_size:] #split values into the current batch and the remaining records
            c.executemany(q, batch ) #insert current batch ''

    def storeHand(self, hdata, doinsert = False, printdata = False):
        if printdata:
            print ("######## Hands ##########")
            import pprint
            pp = pprint.PrettyPrinter(indent=4)
            pp.pprint(hdata)
            print ("###### End Hands ########")
            
        # Tablename can have odd charachers
        hdata['tableName'] = Charset.to_db_utf8(hdata['tableName'])
        
        self.hbulk.append( [ hdata['tableName'],
                             hdata['siteHandNo'],
                             hdata['tourneyId'],
                             hdata['gametypeId'],
                             hdata['sessionId'],
                             hdata['gameId'],
                             hdata['fileId'],
                             hdata['startTime'],                
                             datetime.utcnow(), #importtime
                             hdata['seats'],
                             hdata['texture'],
                             hdata['playersVpi'],
                             hdata['boardcard1'],
                             hdata['boardcard2'],
                             hdata['boardcard3'],
                             hdata['boardcard4'],
                             hdata['boardcard5'],
                             hdata['runItTwice'],
                             hdata['playersAtStreet1'],
                             hdata['playersAtStreet2'],
                             hdata['playersAtStreet3'],
                             hdata['playersAtStreet4'],
                             hdata['playersAtShowdown'],
                             hdata['street0Raises'],
                             hdata['street1Raises'],
                             hdata['street2Raises'],
                             hdata['street3Raises'],
                             hdata['street4Raises'],
                             hdata['street1Pot'],
                             hdata['street2Pot'],
                             hdata['street3Pot'],
                             hdata['street4Pot'],
                             hdata['showdownPot'],
                             hdata['id']
                             ])

        if doinsert:
            self.appendSessionIds()
            self.updateTourneysSessions()
            self.hbulk = [tuple([x for x in h[:-1]]) for h in self.hbulk]
            q = self.sql.query['store_hand']
            q = q.replace('%s', self.sql.query['placeholder'])
            c = self.get_cursor()
            self.executemany(c, q, self.hbulk) #c.executemany(q, self.hbulk)
            self.commit()
    
    def storeBoards(self, id, boards, doinsert):
        if boards: 
            for b in boards:
                self.bbulk += [[id] + b]
        if doinsert and self.bbulk:
            q = self.sql.query['store_boards']
            q = q.replace('%s', self.sql.query['placeholder'])
            c = self.get_cursor()
            self.executemany(c, q, self.bbulk) #c.executemany(q, self.bbulk)
    
    def updateTourneysSessions(self):
        if self.tbulk:
            q_update_sessions  = self.sql.query['updateTourneysSessions'].replace('%s', self.sql.query['placeholder'])
            c = self.get_cursor()
            for t, sid in self.tbulk.iteritems():
                c.execute(q_update_sessions,  (sid, t))
                self.commit()
    
    def updateTourneysPlayersSessions(self, pids, tid, startTime, pdata, heroes, doinsert):
        for p, id in pids.iteritems():
            if id in heroes and tid:
                if tid not in self.tc:
                    self.tc[tid] =   {'tpid' : None,
                                    'played' : 0,
                                     'hands' : 0,
                                 'startTime' : None,
                                   'endTime' : None}
                self.tc[tid]['tpid'] = pdata[p]['tourneysPlayersIds']
                if pdata[p]['street0VPI'] or pdata[p]['street1Seen']:
                    self.tc[tid]['played'] += 1
                self.tc[tid]['hands'] += 1
                if not self.tc[tid]['startTime'] or startTime < self.tc[tid]['startTime']:
                    self.tc[tid]['startTime']  = startTime
                if not self.tc[tid]['endTime'] or startTime > self.tc[tid]['endTime']:
                    self.tc[tid]['endTime']    = startTime
                
        if doinsert:
            q_select           = self.sql.query['selectTourneysPlayersStartEnd'].replace('%s', self.sql.query['placeholder'])
            q_update_start_end = self.sql.query['updateTourneysPlayersStartEnd'].replace('%s', self.sql.query['placeholder'])
            q_update_start     = self.sql.query['updateTourneysPlayersStart'].replace('%s', self.sql.query['placeholder'])
            q_update_end       = self.sql.query['updateTourneysPlayersEnd'].replace('%s', self.sql.query['placeholder'])
            q_update           = self.sql.query['updateTourneysPlayers'].replace('%s', self.sql.query['placeholder'])
            c = self.get_cursor()
            for t, d in self.tc.iteritems():
                if self.backend == self.SQLITE:
                    d['startTime'] = datetime.strptime(d['startTime'], '%Y-%m-%d %H:%M:%S')
                    d['endTime']   = datetime.strptime(d['endTime'], '%Y-%m-%d %H:%M:%S')
                else:
                    d['startTime'] = d['startTime'].replace(tzinfo=None)
                    d['endTime']   = d['endTime'].replace(tzinfo=None)
                c.execute(q_select, d['tpid'])
                start, end = c.fetchone()
                update = not start or not end
                if (update or (d['startTime']<start and d['endTime']>end)):
                    c.execute(q_update_start_end, (d['startTime'], d['endTime'], d['played'], d['hands'], d['tpid']))
                elif d['startTime']<start:
                    c.execute(q_update_start,(d['startTime'], d['played'], d['hands'], d['tpid']))
                elif d['endTime']>end:
                    c.execute(q_update_end,(d['endTime'], d['played'], d['hands'], d['tpid']))
                else:
                    c.execute(q_update,(d['played'], d['hands'], d['tpid']))
                self.commit()

    def storeHandsPlayers(self, hid, pids, pdata, doinsert = False, printdata = False):
        #print "DEBUG: %s %s %s" %(hid, pids, pdata)
        if printdata:
            import pprint
            pp = pprint.PrettyPrinter(indent=4)
            pp.pprint(pdata)

        for p in pdata:
            self.hpbulk.append( ( hid,
                                  pids[p],
                                  pdata[p]['startCash'],
                                  pdata[p]['seatNo'],
                                  pdata[p]['sitout'],
                                  pdata[p]['card1'],
                                  pdata[p]['card2'],
                                  pdata[p]['card3'],
                                  pdata[p]['card4'],
                                  pdata[p]['card5'],
                                  pdata[p]['card6'],
                                  pdata[p]['card7'],
                                  pdata[p]['card8'],
                                  pdata[p]['card9'],
                                  pdata[p]['card10'],
                                  pdata[p]['card11'],
                                  pdata[p]['card12'],
                                  pdata[p]['card13'],
                                  pdata[p]['card14'],
                                  pdata[p]['card15'],
                                  pdata[p]['card16'],
                                  pdata[p]['card17'],
                                  pdata[p]['card18'],
                                  pdata[p]['card19'],
                                  pdata[p]['card20'],
                                  pdata[p]['winnings'],
                                  pdata[p]['rake'],
                                  pdata[p]['totalProfit'],
                                  pdata[p]['allInEV'],
                                  pdata[p]['street0VPI'],
                                  pdata[p]['street1Seen'],
                                  pdata[p]['street2Seen'],
                                  pdata[p]['street3Seen'],
                                  pdata[p]['street4Seen'],
                                  pdata[p]['sawShowdown'],
                                  pdata[p]['showed'],
                                  pdata[p]['wonAtSD'],
                                  pdata[p]['street0Aggr'],
                                  pdata[p]['street1Aggr'],
                                  pdata[p]['street2Aggr'],
                                  pdata[p]['street3Aggr'],
                                  pdata[p]['street4Aggr'],
                                  pdata[p]['street1CBChance'],
                                  pdata[p]['street2CBChance'],
                                  pdata[p]['street3CBChance'],
                                  pdata[p]['street4CBChance'],
                                  pdata[p]['street1CBDone'],
                                  pdata[p]['street2CBDone'],
                                  pdata[p]['street3CBDone'],
                                  pdata[p]['street4CBDone'],
                                  pdata[p]['wonWhenSeenStreet1'],
                                  pdata[p]['wonWhenSeenStreet2'],
                                  pdata[p]['wonWhenSeenStreet3'],
                                  pdata[p]['wonWhenSeenStreet4'],
                                  pdata[p]['street0Calls'],
                                  pdata[p]['street1Calls'],
                                  pdata[p]['street2Calls'],
                                  pdata[p]['street3Calls'],
                                  pdata[p]['street4Calls'],
                                  pdata[p]['street0Bets'],
                                  pdata[p]['street1Bets'],
                                  pdata[p]['street2Bets'],
                                  pdata[p]['street3Bets'],
                                  pdata[p]['street4Bets'],
                                  pdata[p]['position'],
                                  pdata[p]['tourneysPlayersIds'],
                                  pdata[p]['startCards'],
                                  pdata[p]['street0CalledRaiseChance'],
                                  pdata[p]['street0CalledRaiseDone'],
                                  pdata[p]['street0_3BChance'],
                                  pdata[p]['street0_3BDone'],
                                  pdata[p]['street0_4BChance'],
                                  pdata[p]['street0_4BDone'],
                                  pdata[p]['street0_C4BChance'],
                                  pdata[p]['street0_C4BDone'],
                                  pdata[p]['street0_FoldTo3BChance'],
                                  pdata[p]['street0_FoldTo3BDone'],
                                  pdata[p]['street0_FoldTo4BChance'],
                                  pdata[p]['street0_FoldTo4BDone'],
                                  pdata[p]['street0_SqueezeChance'],
                                  pdata[p]['street0_SqueezeDone'],
                                  pdata[p]['raiseToStealChance'],
                                  pdata[p]['raiseToStealDone'],
                                  pdata[p]['success_Steal'],
                                  pdata[p]['otherRaisedStreet0'],
                                  pdata[p]['otherRaisedStreet1'],
                                  pdata[p]['otherRaisedStreet2'],
                                  pdata[p]['otherRaisedStreet3'],
                                  pdata[p]['otherRaisedStreet4'],
                                  pdata[p]['foldToOtherRaisedStreet0'],
                                  pdata[p]['foldToOtherRaisedStreet1'],
                                  pdata[p]['foldToOtherRaisedStreet2'],
                                  pdata[p]['foldToOtherRaisedStreet3'],
                                  pdata[p]['foldToOtherRaisedStreet4'],
                                  pdata[p]['raiseFirstInChance'],
                                  pdata[p]['raisedFirstIn'],
                                  pdata[p]['foldBbToStealChance'],
                                  pdata[p]['foldedBbToSteal'],
                                  pdata[p]['foldSbToStealChance'],
                                  pdata[p]['foldedSbToSteal'],
                                  pdata[p]['foldToStreet1CBChance'],
                                  pdata[p]['foldToStreet1CBDone'],
                                  pdata[p]['foldToStreet2CBChance'],
                                  pdata[p]['foldToStreet2CBDone'],
                                  pdata[p]['foldToStreet3CBChance'],
                                  pdata[p]['foldToStreet3CBDone'],
                                  pdata[p]['foldToStreet4CBChance'],
                                  pdata[p]['foldToStreet4CBDone'],
                                  pdata[p]['street1CheckCallRaiseChance'],
                                  pdata[p]['street1CheckCallRaiseDone'],
                                  pdata[p]['street2CheckCallRaiseChance'],
                                  pdata[p]['street2CheckCallRaiseDone'],
                                  pdata[p]['street3CheckCallRaiseChance'],
                                  pdata[p]['street3CheckCallRaiseDone'],
                                  pdata[p]['street4CheckCallRaiseChance'],
                                  pdata[p]['street4CheckCallRaiseDone'],
                                  pdata[p]['street0Raises'],
                                  pdata[p]['street1Raises'],
                                  pdata[p]['street2Raises'],
                                  pdata[p]['street3Raises'],
                                  pdata[p]['street4Raises']
                            ) )

        if doinsert:
            q = self.sql.query['store_hands_players']
            q = q.replace('%s', self.sql.query['placeholder'])
            c = self.get_cursor(True)
            self.executemany(c, q, self.hpbulk) #c.executemany(q, self.hpbulk)

    def storeHandsActions(self, hid, pids, adata, doinsert = False, printdata = False):
        #print "DEBUG: %s %s %s" %(hid, pids, adata)

        # This can be used to generate test data. Currently unused
        #if printdata:
        #    import pprint
        #    pp = pprint.PrettyPrinter(indent=4)
        #    pp.pprint(adata)
        
        for a in adata:
            self.habulk.append( (hid,
                                 pids[adata[a]['player']],
                                 adata[a]['street'],
                                 adata[a]['actionNo'],
                                 adata[a]['streetActionNo'],
                                 adata[a]['actionId'],
                                 adata[a]['amount'],
                                 adata[a]['raiseTo'],
                                 adata[a]['amountCalled'],
                                 adata[a]['numDiscarded'],
                                 adata[a]['cardsDiscarded'],
                                 adata[a]['allIn']
                               ) )
            
        if doinsert:
            q = self.sql.query['store_hands_actions']
            q = q.replace('%s', self.sql.query['placeholder'])
            c = self.get_cursor()
            self.executemany(c, q, self.habulk) #c.executemany(q, self.habulk)
    
    def storeHandsStove(self, sdata, doinsert):
        #print sdata
        self.hsbulk += sdata
        if doinsert and self.hsbulk:
            q = self.sql.query['store_hands_stove']
            q = q.replace('%s', self.sql.query['placeholder'])
            c = self.get_cursor()
            self.executemany(c, q, self.hsbulk) #c.executemany(q, self.hsbulk)
            
    def appendStats(self, pdata, p):
        #NOTE: Insert new stats at right place because SQL needs strict order
        line = []
        line.append(1)  # HDs
        line.append(pdata[p]['street0VPI'])
        line.append(pdata[p]['street0Aggr'])  
        line.append(pdata[p]['street0CalledRaiseChance'])
        line.append(pdata[p]['street0CalledRaiseDone'])
        line.append(pdata[p]['street0_3BChance'])            
        line.append(pdata[p]['street0_3BDone'])              
        line.append(pdata[p]['street0_4BChance'])            
        line.append(pdata[p]['street0_4BDone'])              
        line.append(pdata[p]['street0_C4BChance'])              
        line.append(pdata[p]['street0_C4BDone'])              
        line.append(pdata[p]['street0_FoldTo3BChance'])      
        line.append(pdata[p]['street0_FoldTo3BDone'])        
        line.append(pdata[p]['street0_FoldTo4BChance'])      
        line.append(pdata[p]['street0_FoldTo4BDone'])        
        line.append(pdata[p]['street0_SqueezeChance'])        
        line.append(pdata[p]['street0_SqueezeDone'])        
        line.append(pdata[p]['raiseToStealChance'])        
        line.append(pdata[p]['raiseToStealDone'])        
        line.append(pdata[p]['success_Steal'])        
        line.append(pdata[p]['street1Seen'])                 
        line.append(pdata[p]['street2Seen'])                 
        line.append(pdata[p]['street3Seen'])                 
        line.append(pdata[p]['street4Seen'])                 
        line.append(pdata[p]['sawShowdown'])                 
        line.append(pdata[p]['street1Aggr'])                 
        line.append(pdata[p]['street2Aggr'])                 
        line.append(pdata[p]['street3Aggr'])                 
        line.append(pdata[p]['street4Aggr'])                 
        line.append(pdata[p]['otherRaisedStreet0'])          
        line.append(pdata[p]['otherRaisedStreet1'])          
        line.append(pdata[p]['otherRaisedStreet2'])          
        line.append(pdata[p]['otherRaisedStreet3'])          
        line.append(pdata[p]['otherRaisedStreet4'])          
        line.append(pdata[p]['foldToOtherRaisedStreet0'])    
        line.append(pdata[p]['foldToOtherRaisedStreet1'])    
        line.append(pdata[p]['foldToOtherRaisedStreet2'])    
        line.append(pdata[p]['foldToOtherRaisedStreet3'])    
        line.append(pdata[p]['foldToOtherRaisedStreet4'])    
        line.append(pdata[p]['wonWhenSeenStreet1'])
        line.append(pdata[p]['wonWhenSeenStreet2'])
        line.append(pdata[p]['wonWhenSeenStreet3'])
        line.append(pdata[p]['wonWhenSeenStreet4'])
        line.append(pdata[p]['wonAtSD'])
        line.append(pdata[p]['raiseFirstInChance'])          
        line.append(pdata[p]['raisedFirstIn'])               
        line.append(pdata[p]['foldBbToStealChance'])         
        line.append(pdata[p]['foldedBbToSteal'])             
        line.append(pdata[p]['foldSbToStealChance'])         
        line.append(pdata[p]['foldedSbToSteal'])             
        line.append(pdata[p]['street1CBChance'])             
        line.append(pdata[p]['street1CBDone'])               
        line.append(pdata[p]['street2CBChance'])             
        line.append(pdata[p]['street2CBDone'])               
        line.append(pdata[p]['street3CBChance'])             
        line.append(pdata[p]['street3CBDone'])               
        line.append(pdata[p]['street4CBChance'])             
        line.append(pdata[p]['street4CBDone'])               
        line.append(pdata[p]['foldToStreet1CBChance'])       
        line.append(pdata[p]['foldToStreet1CBDone'])         
        line.append(pdata[p]['foldToStreet2CBChance'])       
        line.append(pdata[p]['foldToStreet2CBDone'])         
        line.append(pdata[p]['foldToStreet3CBChance'])       
        line.append(pdata[p]['foldToStreet3CBDone'])         
        line.append(pdata[p]['foldToStreet4CBChance'])       
        line.append(pdata[p]['foldToStreet4CBDone'])         
        line.append(pdata[p]['totalProfit'])
        line.append(pdata[p]['rake'])
        line.append(pdata[p]['street1CheckCallRaiseChance']) 
        line.append(pdata[p]['street1CheckCallRaiseDone'])   
        line.append(pdata[p]['street2CheckCallRaiseChance']) 
        line.append(pdata[p]['street2CheckCallRaiseDone'])   
        line.append(pdata[p]['street3CheckCallRaiseChance']) 
        line.append(pdata[p]['street3CheckCallRaiseDone'])   
        line.append(pdata[p]['street4CheckCallRaiseChance']) 
        line.append(pdata[p]['street4CheckCallRaiseDone'])   
        line.append(pdata[p]['street0Calls'])                
        line.append(pdata[p]['street1Calls'])                
        line.append(pdata[p]['street2Calls'])                
        line.append(pdata[p]['street3Calls'])                
        line.append(pdata[p]['street4Calls'])                
        line.append(pdata[p]['street0Bets'])                 
        line.append(pdata[p]['street1Bets'])                 
        line.append(pdata[p]['street2Bets'])                 
        line.append(pdata[p]['street3Bets'])                 
        line.append(pdata[p]['street4Bets'])                 
        line.append(pdata[p]['street0Raises'])               
        line.append(pdata[p]['street1Raises'])               
        line.append(pdata[p]['street2Raises'])               
        line.append(pdata[p]['street3Raises'])               
        line.append(pdata[p]['street4Raises'])               
        
        for i in range(len(line)):
            if line[i]==True:  line[i] = 1
            if line[i]==False: line[i] = 0
            
        return line
            
    def storeHudCache(self, gid, pids, starttime, pdata, doinsert=False):
        update_hudcache = self.sql.query['update_hudcache']
        update_hudcache = update_hudcache.replace('%s', self.sql.query['placeholder'])
        insert_hudcache = self.sql.query['insert_hudcache']
        insert_hudcache = insert_hudcache.replace('%s', self.sql.query['placeholder'])
            
        if pdata:   
            # hard-code styleKey as 'A000000' (all-time cache, no key) for now
            seats = '0'
            position = '0'
            styleKey = 'A000000'
    
            if self.build_full_hudcache:
                tz = datetime.utcnow() - datetime.today()
                tz_offset = tz.seconds/3600
                tz_day_start_offset = self.day_start + tz_offset
                
                d = timedelta(hours=tz_day_start_offset)
                starttime_offset = starttime - d
                styleKey = datetime.strftime(starttime_offset, 'd%y%m%d')
                seats = len(pids)

        for p in pdata:
            line = self.appendStats(pdata, p)
            if self.build_full_hudcache:
                pos = {'B':'B', 'S':'S', 0:'D', 1:'C', 2:'M', 3:'M', 4:'M', 5:'E', 6:'E', 7:'E', 8:'E', 9:'E' }
                position = pos[pdata[p]['position']]
            k   = (gid
                  ,pids[p]
                  ,seats
                  ,position
                  ,pdata[p]['tourneyTypeId']
                  ,styleKey
                  )
            
            if k in self.hcbulk:
                self.hcbulk[k] = [sum(l) for l in zip(self.hcbulk[k], line)]
            else:
                self.hcbulk[k] = line
                
        if doinsert:
            inserts = []
            c = self.get_cursor()
            for k, line in self.hcbulk.iteritems():
                row = line + [k[0], k[1], k[2], k[3], k[4], k[5]]
                num = c.execute(update_hudcache, row)
                # Try to do the update first. Do insert it did not work
                if ((self.backend == self.PGSQL and c.statusmessage != "UPDATE 1")
                        or (self.backend == self.MYSQL_INNODB and num == 0)
                        or (self.backend == self.SQLITE and num.rowcount == 0)):
                    inserts.append([k[0], k[1], k[2], k[3], k[4], k[5]] + line)
                    #print "DEBUG: Successfully(?: %s) updated HudCacho using INSERT" % num
                else:
                    #print "DEBUG: Successfully updated HudCacho using UPDATE"
                    pass
            if inserts:
                self.executemany(c, insert_hudcache, inserts) #c.executemany(insert_hudcache, inserts)
            self.commit()
            
    def storeCardsCache(self, gametype, pids, heroes, pdata, doinsert):
        """Update cached statistics. If update fails because no record exists, do an insert."""
        update_cardscache = self.sql.query['update_cardscache']
        update_cardscache = update_cardscache.replace('%s', self.sql.query['placeholder'])
        insert_cardscache = self.sql.query['insert_cardscache']
        insert_cardscache = insert_cardscache.replace('%s', self.sql.query['placeholder'])
            
        for p in pdata:
            if pids[p] in heroes:
                line = self.appendStats(pdata, p)
                k =   (gametype['type']
                      ,gametype['category']
                      ,gametype['currency']
                      ,pids[p]
                      ,pdata[p]['startCards']
                      )
                if k in self.dcbulk:
                    self.dcbulk[k] = [sum(l) for l in zip(self.dcbulk[k], line)]
                else:
                    self.dcbulk[k] = line
                #id = self.dccache[(k,line)]
                
        if doinsert:
            inserts = []
            c = self.get_cursor()
            for k, line in self.dcbulk.iteritems():
                row = line + [k[0], k[1], k[2], k[3], k[4]]
                num = c.execute(update_cardscache, row)
                # Try to do the update first. Do insert it did not work
                if ((self.backend == self.PGSQL and c.statusmessage != "UPDATE 1")
                        or (self.backend == self.MYSQL_INNODB and num == 0)
                        or (self.backend == self.SQLITE and num.rowcount == 0)):
                    inserts.append([k[0], k[1], k[2], k[3], k[4]] + line)
                    #print "DEBUG: Successfully(?: %s) updated HudCacho using INSERT" % num
                else:
                    #print "DEBUG: Successfully updated HudCacho using UPDATE"
                    pass
            if inserts:
                c.executemany(insert_cardscache, inserts)
            self.commit()

    def storePositionsCache(self, gametype, pids, heroes, pdata, doinsert):
        """Update cached statistics. If update fails because no record exists, do an insert."""
        update_positionscache = self.sql.query['update_positionscache']
        update_positionscache = update_positionscache.replace('%s', self.sql.query['placeholder'])
        insert_positionscache = self.sql.query['insert_positionscache']
        insert_positionscache = insert_positionscache.replace('%s', self.sql.query['placeholder'])
            
        for p in pdata:
            if pids[p] in heroes:
                line = self.appendStats(pdata, p)
                k =   (gametype['type']
                      ,gametype['base']
                      ,gametype['category']
                      ,gametype['currency']
                      ,gametype['maxSeats']
                      ,pids[p]
                      ,len(pids)
                      ,str(pdata[p]['position'])[0]
                      )
                #id = self.pccache[(k,line)]
                if k in self.pcbulk:
                    self.pcbulk[k] = [sum(l) for l in zip(self.pcbulk[k], line)]
                else:
                    self.pcbulk[k] = line
                #id = self.dccache[(k,line)]
                
        if doinsert:
            inserts = []
            c = self.get_cursor()
            for k, line in self.pcbulk.iteritems():
                row = line + [k[0], k[1], k[2], k[3], k[4], k[5], k[6], k[7]]
                num = c.execute(update_positionscache, row)
                # Try to do the update first. Do insert it did not work
                if ((self.backend == self.PGSQL and c.statusmessage != "UPDATE 1")
                        or (self.backend == self.MYSQL_INNODB and num == 0)
                        or (self.backend == self.SQLITE and num.rowcount == 0)):
                    inserts.append([k[0], k[1], k[2], k[3], k[4], k[5], k[6], k[7]] + line)
                    #print "DEBUG: Successfully(?: %s) updated HudCacho using INSERT" % num
                else:
                    #print "DEBUG: Successfully updated HudCacho using UPDATE"
                    pass
            if inserts:
                c.executemany(insert_positionscache, inserts)
            self.commit()
            
    def storeSessionsCache(self, hid, pids, startTime, heroes, doinsert = False):
        """Update cached sessions. If no record exists, do an insert"""
        THRESHOLD = timedelta(seconds=int(self.sessionTimeout * 60))
        
        select_SC     = self.sql.query['select_SC'].replace('%s', self.sql.query['placeholder'])
        update_SC     = self.sql.query['update_SC'].replace('%s', self.sql.query['placeholder'])
        insert_SC     = self.sql.query['insert_SC'].replace('%s', self.sql.query['placeholder'])
        update_SC_GC  = self.sql.query['update_SC_GC'].replace('%s', self.sql.query['placeholder'])
        update_SC_T   = self.sql.query['update_SC_T'].replace('%s', self.sql.query['placeholder'])
        update_SC_H   = self.sql.query['update_SC_H'].replace('%s', self.sql.query['placeholder'])
        delete_SC     = self.sql.query['delete_SC'].replace('%s', self.sql.query['placeholder'])
        
        #print "DEBUG: %s %s %s" %(hid, pids, pdata)
        hand = {}
        for p, id in pids.iteritems():
            if id in heroes:
                if self.backend == self.SQLITE:
                    hand['startTime'] = datetime.strptime(startTime, '%Y-%m-%d %H:%M:%S')
                else:
                    hand['startTime'] = startTime.replace(tzinfo=None)
                hand['ids'] = []
        
        if hand:
            id = []
            lower = hand['startTime']-THRESHOLD
            upper = hand['startTime']+THRESHOLD
            for i in range(len(self.sc['bk'])):
                if ((lower  <= self.sc['bk'][i]['sessionEnd'])
                and (upper  >= self.sc['bk'][i]['sessionStart'])):
                    if ((hand['startTime'] <= self.sc['bk'][i]['sessionEnd']) 
                    and (hand['startTime'] >= self.sc['bk'][i]['sessionStart'])):
                         id.append(i)
                    elif hand['startTime'] < self.sc['bk'][i]['sessionStart']:
                         self.sc['bk'][i]['sessionStart'] = hand['startTime']
                         id.append(i)
                    elif hand['startTime'] > self.sc['bk'][i]['sessionEnd']:
                         self.sc['bk'][i]['sessionEnd'] = hand['startTime']
                         id.append(i)
            if len(id) == 1:
                id = id[0]
                self.sc['bk'][id]['ids'].append(hid)
            elif len(id) == 2:
                if  self.sc['bk'][id[0]]['sessionStart'] < self.sc['bk'][id[1]]['sessionStart']:
                    self.sc['bk'][id[0]]['sessionEnd']   = self.sc['bk'][id[1]]['sessionEnd']
                else:
                    self.sc['bk'][id[0]]['sessionStart'] = self.sc['bk'][id[1]]['sessionStart']
                sh = self.sc['bk'].pop(id[1])
                id = id[0]
                self.sc['bk'][id]['ids'].append(hid)
                self.sc['bk'][id]['ids'] += sh['ids']
            elif len(id) == 0:
                hand['id'] = None
                hand['sessionStart'] = hand['startTime']
                hand['sessionEnd']   = hand['startTime']
                id = len(self.sc['bk'])
                hand['ids'].append(hid)
                self.sc['bk'].append(hand)
        
        if doinsert:
            c = self.get_cursor()
            for i in range(len(self.sc['bk'])):
                lower = self.sc['bk'][i]['sessionStart'] - THRESHOLD
                upper = self.sc['bk'][i]['sessionEnd']   + THRESHOLD
                c.execute(select_SC, (lower, upper))
                r = self.fetchallDict(c)
                num = len(r)
                if (num == 1):
                    start, end, update = r[0]['sessionStart'], r[0]['sessionEnd'], False
                    if self.sc['bk'][i]['sessionStart'] < start:
                        start, update = self.sc['bk'][i]['sessionStart'], True
                    if self.sc['bk'][i]['sessionEnd'] > end:
                        end, update = self.sc['bk'][i]['sessionEnd'], True
                    if update: 
                        c.execute(update_SC, [start, end, r[0]['id']])
                    for h in  self.sc['bk'][i]['ids']:
                        self.sc[h] = {'id': r[0]['id'], 'data': [start, end]}
                elif (num > 1):
                    start, end, merge = None, None, []
                    for n in r: merge.append(n['id'])
                    merge.sort()
                    r.append(self.sc['bk'][i])
                    for n in r:                      
                        if start: 
                            if  start > n['sessionStart']: 
                                start = n['sessionStart']
                        else:   start = n['sessionStart']
                        if end: 
                            if  end < n['sessionEnd']: 
                                end = n['sessionEnd']
                        else:   end = n['sessionEnd']
                    row = [start, end]
                    c.execute(insert_SC, row)
                    sid = self.get_last_insert_id(c)
                    for h in self.sc['bk'][i]['ids']: self.sc[h] = {'id': sid}
                    for m in merge:
                        for h, n in self.sc.iteritems():
                            if h!='bk':
                                if n['id'] == m:
                                    self.sc[h] = {'id': sid}
                        c.execute(update_SC_GC,(sid, m))
                        c.execute(update_SC_T, (sid, m))
                        c.execute(update_SC_H, (sid, m))
                        c.execute(delete_SC, m)
                elif (num == 0):
                    start =  self.sc['bk'][i]['sessionStart']
                    end   =  self.sc['bk'][i]['sessionEnd']
                    row = [start, end]
                    c.execute(insert_SC, row)
                    sid = self.get_last_insert_id(c)
                    for h in self.sc['bk'][i]['ids']: self.sc[h] = {'id': sid}
            self.commit()
    
    def storeGamesCache(self, hid, pids, startTime, gtid, game, pdata, tz_name, heroes, doinsert = False):
        """Update cached sessions. If no record exists, do an insert"""
        utc = pytz.utc
        if tz_name in pytz.common_timezones:
            if self.backend == self.SQLITE:
                naive = datetime.strptime(startTime, '%Y-%m-%d %H:%M:%S')
            else:
                naive = startTime.replace(tzinfo=None)
            utc_start = utc.localize(naive)
            tz = pytz.timezone(tz_name)
            loc_tz = utc_start.astimezone(tz).strftime('%z')
            local = naive + timedelta(hours=int(loc_tz[:-2]), minutes=int(loc_tz[0]+loc_tz[-2:]))
        else:
            if strftime('%Z') == 'UTC':
                local = startTime
                loc_tz = '0'
            else:
                tz_dt = datetime.today() - datetime.utcnow()
                loc_tz = tz_dt.seconds/3600 - 24
                local = startTime + timedelta(hours=int(loc_tz))
                loc_tz = str(loc_tz)
        date = "d%02d%02d%02d" % (local.year - 2000, local.month, local.day)
        THRESHOLD = timedelta(seconds=int(self.sessionTimeout * 60))
        
        select_GC   = self.sql.query['select_GC'].replace('%s', self.sql.query['placeholder'])
        update_GC   = self.sql.query['update_GC'].replace('%s', self.sql.query['placeholder'])
        insert_GC   = self.sql.query['insert_GC'].replace('%s', self.sql.query['placeholder'])
        update_GC_H = self.sql.query['update_GC_H'].replace('%s', self.sql.query['placeholder'])
        delete_GC   = self.sql.query['delete_GC'].replace('%s', self.sql.query['placeholder'])

        hand = {}
        for p, pid in pids.iteritems():
            if pid in heroes and game['type']=='ring':
                hand['playerId']      = pid
                hand['gametypeId']    = None
                hand['date']          = date
                if self.backend == self.SQLITE:
                    hand['startTime'] = datetime.strptime(startTime, '%Y-%m-%d %H:%M:%S')
                else:
                    hand['startTime'] = startTime.replace(tzinfo=None)
                hand['hid']           = hid
                hand['hands']         = 1
                
                hand['ids']           = []
                hand['gametypeId'] = gtid
                if pdata[p]['street0VPI'] or pdata[p]['street1Seen']:
                    hand['played'] = 1
                else:
                    hand['played'] = 0
                hand['totalProfit'] = pdata[p]['totalProfit']
                hand['rake']        = pdata[p]['rake']
                if pdata[p]['sawShowdown']:
                    hand['showdownWinnings']    = pdata[p]['totalProfit']
                    hand['nonShowdownWinnings'] = 0
                else:
                    hand['showdownWinnings'] = 0
                    hand['nonShowdownWinnings'] = pdata[p]['totalProfit']
                hand['allInEV'] = pdata[p]['allInEV']
                
        if hand:
            id = []
            lower = hand['startTime']-THRESHOLD
            upper = hand['startTime']+THRESHOLD
            for i in range(len(self.gc['bk'])):
                if ((hand['gametypeId'] == self.gc['bk'][i]['gametypeId'])
                and (hand['playerId']   == self.gc['bk'][i]['playerId'])
                and (lower <= self.gc['bk'][i]['gameEnd'])
                and (upper >= self.gc['bk'][i]['gameStart'])):
                    if len(id)==0:
                        self.gc['bk'][i]['played']              += hand['played']
                        self.gc['bk'][i]['hands']               += hand['hands']
                        self.gc['bk'][i]['totalProfit']         += hand['totalProfit']
                        self.gc['bk'][i]['rake']                += hand['rake']
                        self.gc['bk'][i]['showdownWinnings']    += hand['showdownWinnings']
                        self.gc['bk'][i]['nonShowdownWinnings'] += hand['nonShowdownWinnings']
                        self.gc['bk'][i]['allInEV']             += hand['allInEV']
                    if ((hand['startTime'] <= self.gc['bk'][i]['gameEnd']) 
                    and (hand['startTime'] >= self.gc['bk'][i]['gameStart'])):
                        id.append(i)
                    elif hand['startTime']  <  self.gc['bk'][i]['gameStart']:
                        self.gc['bk'][i]['gameStart']      = hand['startTime']
                        id.append(i)
                    elif hand['startTime']  >  self.gc['bk'][i]['gameEnd']:
                        self.gc['bk'][i]['gameEnd']        = hand['startTime']
                        id.append(i)
            if len(id) == 1:
                self.gc['bk'][id[0]]['ids'].append(hid)
            elif len(id) == 2:
                if    self.gc['bk'][id[0]]['gameStart'] < self.gc['bk'][id[1]]['gameStart']:
                      self.gc['bk'][id[0]]['gameEnd']   = self.gc['bk'][id[1]]['gameEnd']
                else: self.gc['bk'][id[0]]['gameStart'] = self.gc['bk'][id[1]]['gameStart']
                self.gc['bk'][id[0]]['played']              += self.gc['bk'][id[1]]['played']
                self.gc['bk'][id[0]]['hands']               += self.gc['bk'][id[1]]['hands']
                self.gc['bk'][id[0]]['totalProfit']         += self.gc['bk'][id[1]]['totalProfit']
                self.gc['bk'][id[0]]['rake']                += self.gc['bk'][id[1]]['rake']
                self.gc['bk'][id[0]]['showdownWinnings']    += self.gc['bk'][id[1]]['showdownWinnings']
                self.gc['bk'][id[0]]['nonShowdownWinnings'] += self.gc['bk'][id[1]]['nonShowdownWinnings']
                self.gc['bk'][id[0]]['allInEV']             += self.gc['bk'][id[1]]['allInEV']
                gh = self.gc['bk'].pop(id[1])
                self.gc['bk'][id[0]]['ids'].append(hid)
                self.gc['bk'][id[0]]['ids'] += gh['ids']
            elif len(id) == 0:
                hand['gameStart'] = hand['startTime']
                hand['gameEnd']   = hand['startTime']
                id = len(self.gc['bk'])
                hand['ids'].append(hid)
                self.gc['bk'].append(hand)
        
        if doinsert:
            c = self.get_cursor()
            for i in range(len(self.gc['bk'])):
                hid = self.gc['bk'][i]['hid']
                sid = self.sc[hid]['id']
                lower = self.gc['bk'][i]['gameStart'] - THRESHOLD
                upper = self.gc['bk'][i]['gameEnd']   + THRESHOLD
                game = [self.gc['bk'][i]['date']
                       ,self.gc['bk'][i]['gametypeId']
                       ,self.gc['bk'][i]['playerId']]
                row = [lower, upper] + game
                c.execute(select_GC, row)
                r = self.fetchallDict(c)
                num = len(r)
                if (num == 1):
                    start, end = r[0]['gameStart'], r[0]['gameEnd']
                    if self.gc['bk'][i]['gameStart'] < start:
                        start = self.gc['bk'][i]['gameStart']
                    if self.gc['bk'][i]['gameEnd']   > end:
                        end = self.gc['bk'][i]['gameEnd']
                    row = [start, end
                          ,self.gc['bk'][i]['played']
                          ,self.gc['bk'][i]['hands']
                          ,self.gc['bk'][i]['totalProfit']
                          ,self.gc['bk'][i]['rake']
                          ,self.gc['bk'][i]['showdownWinnings']
                          ,self.gc['bk'][i]['nonShowdownWinnings']
                          ,self.gc['bk'][i]['allInEV']
                          ,r[0]['id']]
                    c.execute(update_GC, row)
                    for h in self.gc['bk'][i]['ids']: self.gc[h] = {'id': r[0]['id']} 
                elif (num > 1):
                    start, end, merge = None, None, []
                    played, hands, totalProfit, rake, showdownWinnings, nonShowdownWinnings, allInEV = 0, 0, 0, 0, 0, 0, 0
                    for n in r: merge.append(n['id'])
                    merge.sort()
                    r.append(self.gc['bk'][i])
                    for n in r:
                        if start:
                            if  start > n['gameStart']: 
                                start = n['gameStart']
                        else:   start = n['gameStart']
                        if end: 
                            if  end < n['gameEnd']: 
                                end = n['gameEnd']
                        else:   end = n['gameEnd']
                        played              += n['played']
                        hands               += n['hands']
                        totalProfit         += n['totalProfit']
                        rake                += n['rake']
                        showdownWinnings    += n['showdownWinnings']
                        nonShowdownWinnings += n['nonShowdownWinnings']
                        allInEV             += n['allInEV']
                    row = [sid, start, end] + game + [played, hands, totalProfit, rake, showdownWinnings, nonShowdownWinnings, allInEV]
                    c.execute(insert_GC, row)
                    gid = self.get_last_insert_id(c)
                    for h in self.gc['bk'][i]['ids']: self.gc[h] = {'id': gid}
                    for m in merge:
                        for h, n in self.gc.iteritems():
                            if h!='bk':
                                if n['id'] == m:
                                    self.gc[h] = {'id': gid}
                        c.execute(update_GC_H, (gid, m))
                        c.execute(delete_GC, m)
                elif (num == 0):
                    start               = self.gc['bk'][i]['gameStart']
                    end                 = self.gc['bk'][i]['gameEnd']
                    played              = self.gc['bk'][i]['played']
                    hands               = self.gc['bk'][i]['hands']
                    totalProfit         = self.gc['bk'][i]['totalProfit']
                    rake                = self.gc['bk'][i]['rake']
                    showdownWinnings    = self.gc['bk'][i]['showdownWinnings']
                    nonShowdownWinnings = self.gc['bk'][i]['nonShowdownWinnings']
                    allInEV             = self.gc['bk'][i]['allInEV']
                    row = [sid, start, end] + game + [played, hands, totalProfit, rake, showdownWinnings, nonShowdownWinnings, allInEV]
                    c.execute(insert_GC, row)
                    gid = self.get_last_insert_id(c)
                    for h in self.gc['bk'][i]['ids']: self.gc[h] = {'id': gid}
            self.commit()
    
    def appendSessionIds(self):
        for h in self.hbulk:
            id  = h[-1]
            tid = h[2]
            if id in self.sc:
                h[4] = self.sc[id]['id']
                if tid: self.tbulk[tid] = h[4]
            if id in self.gc:
                h[5] = self.gc[id]['id']                

    def storeFile(self, fdata):
        q = self.sql.query['store_file']
        q = q.replace('%s', self.sql.query['placeholder'])
        c = self.get_cursor()
        c.execute(q, fdata)
        id = self.get_last_insert_id(c)
        return id
        
    def updateFile(self, fdata):
        q = self.sql.query['update_file']
        q = q.replace('%s', self.sql.query['placeholder'])
        c = self.get_cursor()
        c.execute(q, fdata)

    def getHeroIds(self, pids, sitename):
        #Grab playerIds using hero names in HUD_Config.xml
        try:
            # derive list of program owner's player ids
            hero = {}                               # name of program owner indexed by site id
            hero_ids = []
                                                         # make sure at least two values in list
                                                         # so that tuple generation creates doesn't use
                                                         # () or (1,) style
            for site in self.config.get_supported_sites():
                hero = self.config.supported_sites[site].screen_name
                for n, v in pids.iteritems():
                    if n == hero and sitename == site:
                        hero_ids.append(v)
                        
        except:
            err = traceback.extract_tb(sys.exc_info()[2])[-1]
            #print _("Error aquiring hero ids:"), str(sys.exc_value)
        return hero_ids
    
    def fetchallDict(self, cursor):
        data = cursor.fetchall()
        if not data: return []
        desc = cursor.description
        results = [0]*len(data)
        for i in range(len(data)):
            results[i] = {}
            for n in range(len(desc)):
                name = desc[n][0]
                results[i][name] = data[i][n]
        return results
    
    def nextHandId(self):
        c = self.get_cursor(True)
        c.execute("SELECT max(id) FROM Hands")
        id = c.fetchone()[0]
        if not id: id = 0
        id += self.hand_inc
        return id

    def isDuplicate(self, gametypeID, siteHandNo):
        if (gametypeID, siteHandNo) in self.siteHandNos:
            return True
        c = self.get_cursor()
        c.execute(self.sql.query['isAlreadyInDB'], (gametypeID, siteHandNo))
        result = c.fetchall()
        if len(result) > 0:
            return True
        self.siteHandNos.append((gametypeID, siteHandNo))
        return False
    
    def getSqlPlayerIDs(self, pnames, siteid):
        result = {}
        if(self.pcache == None):
            self.pcache = LambdaDict(lambda  key:self.insertPlayer(key[0], key[1]))

        for player in pnames:
            result[player] = self.pcache[(player,siteid)]
            # NOTE: Using the LambdaDict does the same thing as:
            #if player in self.pcache:
            #    #print "DEBUG: cachehit"
            #    pass
            #else:
            #    self.pcache[player] = self.insertPlayer(player, siteid)
            #result[player] = self.pcache[player]

        return result
    
    def insertPlayer(self, name, site_id):
        insert_player = "INSERT INTO Players (name, siteId) VALUES (%s, %s)"
        insert_player = insert_player.replace('%s', self.sql.query['placeholder'])
        _name = Charset.to_db_utf8(name)
        key = (_name, site_id)
        
        #NOTE/FIXME?: MySQL has ON DUPLICATE KEY UPDATE
        #Usage:
        #        INSERT INTO `tags` (`tag`, `count`)
        #         VALUES ($tag, 1)
        #           ON DUPLICATE KEY UPDATE `count`=`count`+1;


        #print "DEBUG: name: %s site: %s" %(name, site_id)
        result = None
        c = self.get_cursor()
        q = "SELECT id, name FROM Players WHERE name=%s and siteid=%s"
        q = q.replace('%s', self.sql.query['placeholder'])
        result = self.insertOrUpdate(c, key, q, insert_player)
        return result
    
    def insertOrUpdate(self, cursor, key, select, insert):
        cursor.execute (select, key)
        tmp = cursor.fetchone()
        if (tmp == None):
            cursor.execute (insert, key)
            result = self.get_last_insert_id(cursor)
        else:
            result = tmp[0]
        return result
    
    def getSqlGameTypeId(self, siteid, game, printdata = False):
        if(self.gtcache == None):
            self.gtcache = LambdaDict(lambda  key:self.insertGameTypes(key[0], key[1]))
            
        self.gtprintdata = printdata
        hilo = "h"
        if game['category'] in ['studhilo', 'omahahilo']:
            hilo = "s"
        elif game['category'] in ['razz','27_3draw','badugi', '27_1draw']:
            hilo = "l"
            
        gtinfo = (siteid, game['type'], game['category'], game['limitType'], game['currency'],
                  game['mix'], int(Decimal(game['sb'])*100), int(Decimal(game['bb'])*100),
                  game['maxSeats'], int(game['ante']*100))
        
        gtinsert = (siteid, game['currency'], game['type'], game['base'], game['category'], game['limitType'], hilo,
                    game['mix'], int(Decimal(game['sb'])*100), int(Decimal(game['bb'])*100),
                    int(Decimal(game['bb'])*100), int(Decimal(game['bb'])*200), game['maxSeats'], int(game['ante']*100))
        
        result = self.gtcache[(gtinfo, gtinsert)]
        # NOTE: Using the LambdaDict does the same thing as:
        #if player in self.pcache:
        #    #print "DEBUG: cachehit"
        #    pass
        #else:
        #    self.pcache[player] = self.insertPlayer(player, siteid)
        #result[player] = self.pcache[player]

        return result

    def insertGameTypes(self, gtinfo, gtinsert):
        result = None
        c = self.get_cursor()
        q = self.sql.query['getGametypeNL']
        q = q.replace('%s', self.sql.query['placeholder'])
        c.execute(q, gtinfo)
        tmp = c.fetchone()
        if (tmp == None):
                
            if self.gtprintdata:
                print ("######## Gametype ##########")
                import pprint
                pp = pprint.PrettyPrinter(indent=4)
                pp.pprint(gtinsert)
                print ("###### End Gametype ########")
                
            c.execute(self.sql.query['insertGameTypes'], gtinsert)
            result = self.get_last_insert_id(c)
        else:
            result = tmp[0]
        return result
    
    def getTourneyInfo(self, siteName, tourneyNo):
        c = self.get_cursor()
        c.execute(self.sql.query['getTourneyInfo'], (siteName, tourneyNo))
        columnNames=c.description

        names=[]
        for column in columnNames:
            names.append(column[0])

        data=c.fetchone()
        return (names,data)
    #end def getTourneyInfo

    def getTourneyTypesIds(self):
        c = self.connection.cursor()
        c.execute(self.sql.query['getTourneyTypesIds'])
        result = c.fetchall()
        return result
    #end def getTourneyTypesIds
    
    def getSqlTourneyTypeIDs(self, hand):
        #if(self.ttcache == None):
        #    self.ttcache = LambdaDict(lambda  key:self.insertTourneyType(key[0], key[1], key[2]))
            
        #tourneydata =   (hand.siteId, hand.buyinCurrency, hand.buyin, hand.fee, hand.gametype['category'],
        #                 hand.gametype['limitType'], hand.maxseats, hand.isSng, hand.isKO, hand.koBounty,
        #                 hand.isRebuy, hand.rebuyCost, hand.isAddOn, hand.addOnCost, hand.speed, hand.isShootout, hand.isMatrix)
        
        result = self.createOrUpdateTourneyType(hand) #self.ttcache[(hand.tourNo, hand.siteId, tourneydata)]

        return result
    
    def createOrUpdateTourneyType(self, obj):
        ttid, _ttid, updateDb = None, None, False
        cursor = self.get_cursor()
        q = self.sql.query['getTourneyTypeIdByTourneyNo'].replace('%s', self.sql.query['placeholder'])
        cursor.execute(q, (obj.tourNo, obj.siteId))
        result=cursor.fetchone()
        
        if result != None:
            columnNames=[desc[0] for desc in cursor.description]
            if self.backend == self.PGSQL:
                expectedValues = (('buyin', 'buyin'), ('fee', 'fee'), ('buyinCurrency', 'currency'),('isSng', 'sng'), ('maxseats', 'maxseats')
                             , ('isKO', 'knockout'), ('koBounty', 'kobounty'), ('isRebuy', 'rebuy'), ('rebuyCost', 'rebuycost')
                             , ('isAddOn', 'addon'), ('addOnCost','addoncost'), ('speed', 'speed'), ('isShootout', 'shootout'), ('isMatrix', 'matrix'))
            else:
                expectedValues = (('buyin', 'buyin'), ('fee', 'fee'), ('buyinCurrency', 'currency'),('isSng', 'sng'), ('maxseats', 'maxSeats')
                             , ('isKO', 'knockout'), ('koBounty', 'koBounty'), ('isRebuy', 'rebuy'), ('rebuyCost', 'rebuyCost')
                             , ('isAddOn', 'addOn'), ('addOnCost','addOnCost'), ('speed', 'speed'), ('isShootout', 'shootout'), ('isMatrix', 'matrix'))
            resultDict = dict(zip(columnNames, result))
            ttid = resultDict["id"]
            for ev in expectedValues:
                if not getattr(obj, ev[0]) and resultDict[ev[1]]:#DB has this value but object doesnt, so update object
                    setattr(obj, ev[0], resultDict[ev[1]])
                elif getattr(obj, ev[0]) and (resultDict[ev[1]] != getattr(obj, ev[0])):#object has this value but DB doesnt, so update DB
                    updateDb=True
                    _ttid = ttid
        if not result or updateDb:
            if obj.gametype['mix']!='none':
                category = obj.gametype['mix']
            else:
                category = obj.gametype['category']
            row = (obj.siteId, obj.buyinCurrency, obj.buyin, obj.fee, category,
                   obj.gametype['limitType'], obj.maxseats, obj.isSng, obj.isKO, obj.koBounty,
                   obj.isRebuy, obj.rebuyCost, obj.isAddOn, obj.addOnCost, obj.speed, obj.isShootout, obj.isMatrix)
            cursor.execute (self.sql.query['getTourneyTypeId'].replace('%s', self.sql.query['placeholder']), row)
            tmp=cursor.fetchone()
            try:
                ttid = tmp[0]
            except TypeError: #this means we need to create a new entry
                if self.printdata:
                    print ("######## Tourneys ##########")
                    import pprint
                    pp = pprint.PrettyPrinter(indent=4)
                    pp.pprint(row)
                    print ("###### End Tourneys ########")
                cursor.execute (self.sql.query['insertTourneyType'].replace('%s', self.sql.query['placeholder']), row)
                ttid = self.get_last_insert_id(cursor)
            if updateDb:
                #print 'DEBUG createOrUpdateTourneyType:', 'old', _ttid, 'new', ttid, row
                q = self.sql.query['updateTourneyTypeId'].replace('%s', self.sql.query['placeholder'])
                cursor.execute(q, (ttid, obj.tourNo))
                self.ttclean.add(_ttid)
        return ttid
    
    def cleanUpTourneyTypes(self):
        clear  = self.sql.query['clearHudCacheTourneyType'].replace('%s', self.sql.query['placeholder'])
        select = self.sql.query['selectTourneyWithTypeId'].replace('%s', self.sql.query['placeholder'])
        delete = self.sql.query['deleteTourneyTypeId'].replace('%s', self.sql.query['placeholder'])
        fetch  = self.sql.query['fetchNewTourneyTypeIds'].replace('%s', self.sql.query['placeholder'])
        cursor = self.get_cursor()
        for ttid in self.ttclean:
            cursor.execute(clear, (ttid,))
            self.commit()
            cursor.execute(select, (ttid,))
            result=cursor.fetchone()
            if not result:
                cursor.execute(delete, (ttid,))
                self.commit()
        if self.ttclean:
            cursor.execute(fetch)
            for id in cursor.fetchall():
                self.rebuild_hudcache(None, None, id[0])
                
    def resetttclean(self):
        self.ttclean = set()
    
    def getSqlTourneyIDs(self, hand):
        if(self.tcache == None):
            self.tcache = LambdaDict(lambda  key:self.insertTourney(key[0], key[1], key[2]))

        result = self.tcache[(hand.siteId, hand.tourNo, hand.tourneyTypeId)]

        return result
    
    def insertTourney(self, siteId, tourNo, tourneyTypeId):
        result = None
        c = self.get_cursor()
        q = self.sql.query['getTourneyByTourneyNo']
        q = q.replace('%s', self.sql.query['placeholder'])

        c.execute (q, (siteId, tourNo))

        tmp = c.fetchone()
        if (tmp == None): 
            c.execute (self.sql.query['insertTourney'].replace('%s', self.sql.query['placeholder']),
                        (tourneyTypeId, None, tourNo, None, None,
                         None, None, None, None, None, None))
            result = self.get_last_insert_id(c)
        else:
            result = tmp[0]
        return result
    
    def createOrUpdateTourney(self, summary):
        cursor = self.get_cursor()
        q = self.sql.query['getTourneyByTourneyNo'].replace('%s', self.sql.query['placeholder'])
        cursor.execute(q, (summary.siteId, summary.tourNo))

        columnNames=[desc[0] for desc in cursor.description]
        result=cursor.fetchone()

        if result != None:
            if self.backend == self.PGSQL:
                expectedValues = (('comment','comment'), ('tourneyName','tourneyname'), ('matrixIdProcessed','matrixidprocessed')
                        ,('totalRebuyCount','totalrebuycount'), ('totalAddOnCount','totaladdoncount')
                        ,('prizepool','prizepool'), ('startTime','starttime'), ('entries','entries')
                        ,('commentTs','commentts'), ('endTime','endtime'))
            else:
                expectedValues = (('comment','comment'), ('tourneyName','tourneyName'), ('matrixIdProcessed','matrixIdProcessed')
                        ,('totalRebuyCount','totalRebuyCount'), ('totalAddOnCount','totalAddOnCount')
                        ,('prizepool','prizepool'), ('startTime','startTime'), ('entries','entries')
                        ,('commentTs','commentTs'), ('endTime','endTime'))
            updateDb=False
            resultDict = dict(zip(columnNames, result))

            tourneyId = resultDict["id"]
            for ev in expectedValues :
                if getattr(summary, ev[0])==None and resultDict[ev[1]]!=None:#DB has this value but object doesnt, so update object
                    setattr(summary, ev[0], resultDict[ev[1]])
                elif getattr(summary, ev[0])!=None and not resultDict[ev[1]]:#object has this value but DB doesnt, so update DB
                    updateDb=True
                #elif ev=="startTime":
                #    if (resultDict[ev] < summary.startTime):
                #        summary.startTime=resultDict[ev]
            if updateDb:
                q = self.sql.query['updateTourney'].replace('%s', self.sql.query['placeholder'])
                row = (summary.entries, summary.prizepool, summary.startTime, summary.endTime, summary.tourneyName,
                       summary.matrixIdProcessed, summary.totalRebuyCount, summary.totalAddOnCount, summary.comment,
                       summary.commentTs, tourneyId
                      )
                cursor.execute(q, row)
        else:
            row = (summary.tourneyTypeId, None, summary.tourNo, summary.entries, summary.prizepool, summary.startTime,
                   summary.endTime, summary.tourneyName, summary.matrixIdProcessed, summary.totalRebuyCount, 
                   summary.totalAddOnCount)
            if self.printdata:
                print ("######## Tourneys ##########")
                import pprint
                pp = pprint.PrettyPrinter(indent=4)
                pp.pprint(row)
                print ("###### End Tourneys ########")
            cursor.execute (self.sql.query['insertTourney'].replace('%s', self.sql.query['placeholder']), row)
            tourneyId = self.get_last_insert_id(cursor)
        return tourneyId
    #end def createOrUpdateTourney

    def getTourneyPlayerInfo(self, siteName, tourneyNo, playerName):
        c = self.get_cursor()
        c.execute(self.sql.query['getTourneyPlayerInfo'], (siteName, tourneyNo, playerName))
        columnNames=c.description

        names=[]
        for column in columnNames:
            names.append(column[0])

        data=c.fetchone()
        return (names,data)
    #end def getTourneyPlayerInfo  
    
    def getSqlTourneysPlayersIDs(self, hand):
        result = {}
        if(self.tpcache == None):
            self.tpcache = LambdaDict(lambda  key:self.insertTourneysPlayers(key[0], key[1]))

        for player in hand.players:
            playerId = hand.dbid_pids[player[1]]
            result[player[1]] = self.tpcache[(playerId,hand.tourneyId)]

        return result
    
    def insertTourneysPlayers(self, playerId, tourneyId):
        result = None
        c = self.get_cursor()
        q = self.sql.query['getTourneysPlayersByIds']
        q = q.replace('%s', self.sql.query['placeholder'])

        c.execute (q, (tourneyId, playerId))

        tmp = c.fetchone()
        if (tmp == None): #new player
            c.execute (self.sql.query['insertTourneysPlayer'].replace('%s',self.sql.query['placeholder'])
                      ,(tourneyId, playerId, None, None, None, None, None, None, None, None, 0, 0))
            #Get last id might be faster here.
            #c.execute ("SELECT id FROM Players WHERE name=%s", (name,))
            result = self.get_last_insert_id(c)
        else:
            result = tmp[0]
        return result
    
    def createOrUpdateTourneysPlayers(self, summary):
        tplayers = []
        tourneysPlayersIds={}
        cursor = self.get_cursor()
        cursor.execute (self.sql.query['getTourneysPlayersByTourney'].replace('%s', self.sql.query['placeholder']),
                            (summary.tourneyId,))
        result=cursor.fetchall()
        if result: tplayers += [i[0] for i in result]
        for player in summary.players:
            playerId = summary.dbid_pids[player]
            if playerId in tplayers:
                cursor.execute (self.sql.query['getTourneysPlayersByIds'].replace('%s', self.sql.query['placeholder']),
                                (summary.tourneyId, playerId))
                columnNames=[desc[0] for desc in cursor.description]
                result=cursor.fetchone()
                if self.backend == self.PGSQL:
                    expectedValues = (('rank','rank'), ('winnings', 'winnings')
                            ,('winningsCurrency','winningscurrency'), ('rebuyCount','rebuycount')
                            ,('addOnCount','addoncount'), ('koCount','kocount'))
                else:
                    expectedValues = (('rank','rank'), ('winnings', 'winnings')
                            ,('winningsCurrency','winningsCurrency'), ('rebuyCount','rebuyCount')
                            ,('addOnCount','addOnCount'), ('koCount','koCount'))
                updateDb=False
                resultDict = dict(zip(columnNames, result))
                tourneysPlayersIds[player[1]]=result[0]
                for ev in expectedValues :
                    summaryAttribute=ev[0]
                    if ev[0]!="winnings" and ev[0]!="winningsCurrency":
                        summaryAttribute+="s"
                    summaryDict = getattr(summary, summaryAttribute)
                    if summaryDict[player]==None and resultDict[ev[1]]!=None:#DB has this value but object doesnt, so update object 
                        summaryDict[player] = resultDict[ev[1]]
                        setattr(summary, summaryAttribute, summaryDict)
                    elif summaryDict!=None and resultDict[ev[1]]==None:#object has this value but DB doesnt, so update DB
                        updateDb=True
                if updateDb:
                    q = self.sql.query['updateTourneysPlayer'].replace('%s', self.sql.query['placeholder'])
                    inputs = (summary.ranks[player],
                              summary.winnings[player],
                              summary.winningsCurrency[player],
                              summary.rebuyCounts[player],
                              summary.addOnCounts[player],
                              summary.koCounts[player],
                              tourneysPlayersIds[player[1]]
                             )
                    #print q
                    #pp = pprint.PrettyPrinter(indent=4)
                    #pp.pprint(inputs)
                    cursor.execute(q, inputs)
            else:
                #print "all values: tourneyId",summary.tourneyId, "playerId",playerId, "rank",summary.ranks[player], "winnings",summary.winnings[player], "winCurr",summary.winningsCurrency[player], summary.rebuyCounts[player], summary.addOnCounts[player], summary.koCounts[player]
                if summary.ranks[player]:
                    self.tpbulk.append((summary.tourneyId, playerId, None, None, int(summary.ranks[player]), int(summary.winnings[player]), summary.winningsCurrency[player],
                                        summary.rebuyCounts[player], summary.addOnCounts[player], summary.koCounts[player], 0, 0))
                else:
                    self.tpbulk.append((summary.tourneyId, playerId, None, None, None, None, None,
                                         summary.rebuyCounts[player], summary.addOnCounts[player], summary.koCounts[player], 0, 0))
        cursor.executemany(self.sql.query['insertTourneysPlayer'].replace('%s', self.sql.query['placeholder']),self.tpbulk)
    
#end class Database

if __name__=="__main__":
    c = Configuration.Config()
    sql = SQL.Sql(db_server = 'sqlite')

    db_connection = Database(c) # mysql fpdb holdem
#    db_connection = Database(c, 'fpdb-p', 'test') # mysql fpdb holdem
#    db_connection = Database(c, 'PTrackSv2', 'razz') # mysql razz
#    db_connection = Database(c, 'ptracks', 'razz') # postgres
    print "database connection object = ", db_connection.connection
    # db_connection.recreate_tables()
    db_connection.dropAllIndexes()
    db_connection.createAllIndexes()

    h = db_connection.get_last_hand()
    print "last hand = ", h

    hero = db_connection.get_player_id(c, 'PokerStars', 'nutOmatic')
    if hero:
        print "nutOmatic player_id", hero

    # example of displaying query plan in sqlite:
    if db_connection.backend == 4:
        print
        c = db_connection.get_cursor()
        c.execute('explain query plan '+sql.query['get_table_name'], (h, ))
        for row in c.fetchall():
            print "Query plan:", row
        print

    t0 = time()
    stat_dict = db_connection.get_stats_from_hand(h, "ring")
    t1 = time()
    for p in stat_dict.keys():
        print p, "  ", stat_dict[p]

    print _("cards ="), db_connection.get_cards(u'1')
    db_connection.close_connection

    print _("get_stats took: %4.3f seconds") % (t1-t0)

    print _("Press ENTER to continue.")
    sys.stdin.readline()

#Code borrowed from http://push.cx/2008/caching-dictionaries-in-python-vs-ruby
class LambdaDict(dict):
    def __init__(self, l):
        super(LambdaDict, self).__init__()
        self.l = l

    def __getitem__(self, key):
        if key in self:
            return self.get(key)
        else:
            self.__setitem__(key, self.l(key))
            return self.get(key)
