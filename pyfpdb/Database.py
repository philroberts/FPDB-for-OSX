#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Database.py

Create and manage the database objects.
"""
#    Copyright 2008-2010, Ray E. Barker
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

import logging
# logging has been set up in fpdb.py or HUD_main.py, use their settings:
log = logging.getLogger("db")

#    FreePokerTools modules
import SQL
import Card
import Charset
from Exceptions import *
import Configuration


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


DB_VERSION = 150


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
                , {'tab':'Hands',           'col':'gametypeId',        'drop':0} # mct 22/3/09
                #, {'tab':'Hands',           'col':'siteHandNo',        'drop':0}  unique indexes not dropped
                , {'tab':'HandsActions',    'col':'handId',            'drop':1}
                , {'tab':'HandsActions',    'col':'playerId',          'drop':1}
                , {'tab':'HandsActions',    'col':'actionId',          'drop':1}
                , {'tab':'HandsPlayers',    'col':'handId',            'drop':1}
                , {'tab':'HandsPlayers',    'col':'playerId',          'drop':1}
                , {'tab':'HandsPlayers',    'col':'tourneysPlayersId', 'drop':0}
                , {'tab':'HudCache',        'col':'gametypeId',        'drop':1}
                , {'tab':'HudCache',        'col':'playerId',          'drop':0}
                , {'tab':'HudCache',        'col':'tourneyTypeId',     'drop':0}
                , {'tab':'Players',         'col':'siteId',            'drop':1}
                #, {'tab':'Players',         'col':'name',              'drop':0}  unique indexes not dropped
                , {'tab':'Tourneys',        'col':'tourneyTypeId',     'drop':1}
                #, {'tab':'Tourneys',        'col':'siteTourneyNo',     'drop':0}  unique indexes not dropped
                , {'tab':'TourneysPlayers', 'col':'playerId',          'drop':0}
                #, {'tab':'TourneysPlayers', 'col':'tourneyId',         'drop':0}  unique indexes not dropped
                , {'tab':'TourneyTypes',    'col':'siteId',            'drop':0}
                , {'tab':'Backings',        'col':'tourneysPlayersId',  'drop':0}
                , {'tab':'Backings',        'col':'playerId',          'drop':0}
                , {'tab':'RawHands',        'col':'id',                'drop':0}
                , {'tab':'RawTourneys',        'col':'id',                'drop':0}
                ]
              , [ # indexes for sqlite (list index 4)
                  {'tab':'Hands',           'col':'gametypeId',        'drop':0}
                , {'tab':'HandsPlayers',    'col':'handId',            'drop':0}
                , {'tab':'HandsPlayers',    'col':'playerId',          'drop':0}
                , {'tab':'HandsPlayers',    'col':'tourneysPlayersId', 'drop':0}
                , {'tab':'HandsActions',    'col':'handId',            'drop':0}
                , {'tab':'HandsActions',    'col':'playerId',          'drop':0}
                , {'tab':'HandsActions',    'col':'actionId',          'drop':1}
                , {'tab':'HudCache',        'col':'gametypeId',        'drop':1}
                , {'tab':'HudCache',        'col':'playerId',          'drop':0}
                , {'tab':'HudCache',        'col':'tourneyTypeId',     'drop':0}
                , {'tab':'Players',         'col':'siteId',            'drop':1}
                , {'tab':'Tourneys',        'col':'tourneyTypeId',     'drop':1}
                , {'tab':'TourneysPlayers', 'col':'playerId',          'drop':0}
                , {'tab':'TourneyTypes',    'col':'siteId',            'drop':0}
                , {'tab':'Backings',        'col':'tourneysPlayersId',  'drop':0}
                , {'tab':'Backings',        'col':'playerId',          'drop':0}
                , {'tab':'RawHands',        'col':'id',                'drop':0}
                , {'tab':'RawTourneys',     'col':'id',                'drop':0}
                ]
              ]

    foreignKeys = [
                    [ ] # no db with index 0
                  , [ ] # no db with index 1
                  , [ # foreign keys for mysql (index 2)
                      {'fktab':'Hands',        'fkcol':'gametypeId',    'rtab':'Gametypes',     'rcol':'id', 'drop':1}
                    , {'fktab':'HandsPlayers', 'fkcol':'handId',        'rtab':'Hands',         'rcol':'id', 'drop':1}
                    , {'fktab':'HandsPlayers', 'fkcol':'playerId',      'rtab':'Players',       'rcol':'id', 'drop':1}
                    , {'fktab':'HandsPlayers', 'fkcol':'tourneysPlayersId','rtab':'TourneysPlayers','rcol':'id', 'drop':1}
                    , {'fktab':'HandsActions', 'fkcol':'handId',        'rtab':'Hands',         'rcol':'id', 'drop':1}
                    , {'fktab':'HandsActions', 'fkcol':'playerId',      'rtab':'Players',       'rcol':'id', 'drop':1}
                    , {'fktab':'HandsActions', 'fkcol':'actionId',      'rtab':'Actions',       'rcol':'id', 'drop':1}
                    , {'fktab':'HudCache',     'fkcol':'gametypeId',    'rtab':'Gametypes',     'rcol':'id', 'drop':1}
                    , {'fktab':'HudCache',     'fkcol':'playerId',      'rtab':'Players',       'rcol':'id', 'drop':0}
                    , {'fktab':'HudCache',     'fkcol':'tourneyTypeId', 'rtab':'TourneyTypes',  'rcol':'id', 'drop':1}
                    ]
                  , [ # foreign keys for postgres (index 3)
                      {'fktab':'Hands',        'fkcol':'gametypeId',    'rtab':'Gametypes',     'rcol':'id', 'drop':1}
                    , {'fktab':'HandsPlayers', 'fkcol':'handId',        'rtab':'Hands',         'rcol':'id', 'drop':1}
                    , {'fktab':'HandsPlayers', 'fkcol':'playerId',      'rtab':'Players',       'rcol':'id', 'drop':1}
                    , {'fktab':'HandsActions', 'fkcol':'handId',        'rtab':'Hands',         'rcol':'id', 'drop':1}
                    , {'fktab':'HandsActions', 'fkcol':'playerId',      'rtab':'Players',       'rcol':'id', 'drop':1}
                    , {'fktab':'HandsActions', 'fkcol':'actionId',      'rtab':'Actions',       'rcol':'id', 'drop':1}
                    , {'fktab':'HudCache',     'fkcol':'gametypeId',    'rtab':'Gametypes',     'rcol':'id', 'drop':1}
                    , {'fktab':'HudCache',     'fkcol':'playerId',      'rtab':'Players',       'rcol':'id', 'drop':0}
                    , {'fktab':'HudCache',     'fkcol':'tourneyTypeId', 'rtab':'TourneyTypes',  'rcol':'id', 'drop':1}
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
        #log = Configuration.get_logger("logging.conf", "db", log_dir=c.dir_log)
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

            self.pcache      = None     # PlayerId cache
            self.cachemiss   = 0        # Delete me later - using to count player cache misses
            self.cachehit    = 0        # Delete me later - using to count player cache hits

            # config while trying out new hudcache mechanism
            self.use_date_in_hudcache = True

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
        for table in (u'Actions', u'Autorates', u'Backings', u'Gametypes', u'Hands', u'HandsActions', u'HandsPlayers', u'HudCache', u'SessionsCache', u'Players', u'RawHands', u'RawTourneys', u'Settings', u'Sites', u'TourneyTypes', u'Tourneys', u'TourneysPlayers'):
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

        if backend == Database.MYSQL_INNODB:
            import MySQLdb
            if use_pool:
                MySQLdb = pool.manage(MySQLdb, pool_size=5)
            try:
                self.connection = MySQLdb.connect(host=host, user=user, passwd=password, db=database, use_unicode=True)
                self.__connected = True
            #TODO: Add port option
            except MySQLdb.Error, ex:
                if ex.args[0] == 1045:
                    raise FpdbMySQLAccessDenied(ex.args[0], ex.args[1])
                elif ex.args[0] == 2002 or ex.args[0] == 2003: # 2002 is no unix socket, 2003 is no tcp socket
                    raise FpdbMySQLNoDatabase(ex.args[0], ex.args[1])
                else:
                    print _("*** WARNING UNKNOWN MYSQL ERROR:"), ex
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
                    self.connection = psycopg2.connect(host = host,
                                               user = user,
                                               password = password,
                                               database = database)
                    self.__connected = True
                except Exception, ex:
                    if 'Connection refused' in ex.args[0]:
                        # meaning eg. db not running
                        raise FpdbPostgresqlNoDatabase(errmsg = ex.args[0])
                    elif 'password authentication' in ex.args[0]:
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
            log.info(_("Connecting to SQLite: %(database)s") % {'database':self.db_path})
            if os.path.exists(database) or create:
                self.connection = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES )
                self.__connected = True
                sqlite3.register_converter("bool", lambda x: bool(int(x)))
                sqlite3.register_adapter(bool, lambda x: 1 if x else 0)
                self.connection.create_function("floor", 1, math.floor)
                tmp = sqlitemath()
                self.connection.create_function("mod", 2, tmp.mod)
                if use_numpy:
                    self.connection.create_aggregate("variance", 1, VARIANCE)
                else:
                    log.warning(_("Some database functions will not work without NumPy support"))
                self.cursor = self.connection.cursor()
                self.cursor.execute('PRAGMA temp_store=2')  # use memory for temp tables/indexes
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

    def add_site(self, site, site_code):
        self.cursor.execute("INSERT INTO Sites "
                            "SELECT max(id)+1, '%s', '%s' "
                            "FROM Sites " % (site, site_code) )

    def check_version(self, database, create):
        self.wrongDbVersion = False
        try:
            self.cursor.execute("SELECT * FROM Settings")
            settings = self.cursor.fetchone()
            if settings[0] != DB_VERSION:
                log.error(_("outdated or too new database version (%s) - please recreate tables")
                              % (settings[0]))
                self.wrongDbVersion = True
        except:# _mysql_exceptions.ProgrammingError:
            if database !=  ":memory:":
                if create:
                    print _("Failed to read settings table - recreating tables")
                    log.info(_("Failed to read settings table - recreating tables"))
                    self.recreate_tables()
                    self.check_version(database=database, create=False)
                else:
                    print _("Failed to read settings table - please recreate tables")
                    log.info(_("Failed to read settings table - please recreate tables"))
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

    def get_cursor(self):
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
            tour_no, tab_no = re.split(" ", row[0])
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
        # FIXME: Take site and actually fetch siteId from that
        # Fixed to Winamax atm
        q = self.sql.query['getSiteTourneyNos']
        q = q.replace('%s', self.sql.query['placeholder'])
        c.execute(q, (14,))
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

    def init_hud_stat_vars(self, hud_days, h_hud_days):
        """Initialise variables used by Hud to fetch stats:
           self.hand_1day_ago     handId of latest hand played more than a day ago
           self.date_ndays_ago    date n days ago
           self.h_date_ndays_ago  date n days ago for hero (different n)
        """

        self.hand_1day_ago = 1
        try:
            c = self.get_cursor()
            c.execute(self.sql.query['get_hand_1day_ago'])
            row = c.fetchone()
        except: # TODO: what error is a database error?!
            err = traceback.extract_tb(sys.exc_info()[2])[-1]
            print _("*** Database Error: ") + err[2] + "(" + str(err[1]) + "): " + str(sys.exc_info()[1])
        else:
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

    def init_player_hud_stat_vars(self, playerid):
        # not sure if this is workable, to be continued ...
        try:
            # self.date_nhands_ago is used for fetching stats for last n hands (hud_style = 'H')
            # This option not used yet - needs to be called for each player :-(
            self.date_nhands_ago[str(playerid)] = 'd000000'

            # should use aggregated version of query if appropriate
            c.execute(self.sql.query['get_date_nhands_ago'], (self.hud_hands, playerid))
            row = c.fetchone()
            if row and row[0]:
                self.date_nhands_ago[str(playerid)] = row[0]
            c.close()
            print _("Database: date n hands ago = ") + self.date_nhands_ago[str(playerid)] + "(playerid "+str(playerid)+")"
        except:
            err = traceback.extract_tb(sys.exc_info()[2])[-1]
            print _("*** Database Error: ")+err[2]+"("+str(err[1])+"): "+str(sys.exc_info()[1])

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
        log.info("opp seats style %s %d %d hero seats style %s %d %d"
                 % (seats_style, seats_min, seats_max
                   ,h_seats_style, h_seats_min, h_seats_max) )

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
        c = self.connection.cursor()

#       now get the stats
        c.execute(self.sql.query[query], subs)
        #for row in c.fetchall():   # needs "explain query plan" in sql statement
        #    print "query plan: ", row
        colnames = [desc[0] for desc in c.description]
        for row in c.fetchall():
            playerid = row[0]
            if (playerid == hero_id and h_hud_style != 'S') or (playerid != hero_id and hud_style != 'S'):
                t_dict = {}
                for name, val in zip(colnames, row):
                    t_dict[name.lower()] = val
#                    print t_dict
                stat_dict[t_dict['player_id']] = t_dict

        return stat_dict

    # uses query on handsplayers instead of hudcache to get stats on just this session
    def get_stats_from_hand_session(self, hand, stat_dict, hero_id
                                   ,hud_style, seats_min, seats_max
                                   ,h_hud_style, h_seats_min, h_seats_max):
        """Get stats for just this session (currently defined as any play in the last 24 hours - to
           be improved at some point ...)
           h_hud_style and hud_style params indicate whether to get stats for hero and/or others
           - only fetch heros stats if h_hud_style == 'S',
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

    def resetPlayerIDs(self):
        self.pcache = None

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
        result = None
        _name = Charset.to_db_utf8(name)
        c = self.get_cursor()
        q = "SELECT name, id FROM Players WHERE siteid=%s and name=%s"
        q = q.replace('%s', self.sql.query['placeholder'])

        #NOTE/FIXME?: MySQL has ON DUPLICATE KEY UPDATE
        #Usage:
        #        INSERT INTO `tags` (`tag`, `count`)
        #         VALUES ($tag, 1)
        #           ON DUPLICATE KEY UPDATE `count`=`count`+1;


        #print "DEBUG: name: %s site: %s" %(name, site_id)

        c.execute (q, (site_id, _name))

        tmp = c.fetchone()
        if (tmp == None): #new player
            c.execute ("INSERT INTO Players (name, siteId) VALUES (%s, %s)".replace('%s',self.sql.query['placeholder'])
                      ,(_name, site_id))
            #Get last id might be faster here.
            #c.execute ("SELECT id FROM Players WHERE name=%s", (name,))
            result = self.get_last_insert_id(c)
        else:
            result = tmp[1]
        return result


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
        print _("prepare import took %s seconds" % ptime)
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
                    print _("Creating mysql index %s %s") % (idx['tab'], idx['col'])
                    try:
                        s = "alter table %s add index %s(%s)" % (idx['tab'],idx['col'],idx['col'])
                        c.execute(s)
                    except:
                        print _("Create foreign key failed: ") + str(sys.exc_info())
                elif self.backend == self.PGSQL:
    #                pass
                    # mod to use tab_col for index name?
                    print _("Creating pg index "), idx['tab'], idx['col']
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
        print (_("After import took %s seconds" % atime))
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
        self.resetPlayerIDs()
        self.create_tables()
        self.createAllIndexes()
        self.commit()
        self.get_sites()
        print _("Finished recreating tables")
        log.info(_("Finished recreating tables"))
    #end def recreate_tables

    def create_tables(self):
        #todo: should detect and fail gracefully if tables already exist.
        try:
            log.debug(self.sql.query['createSettingsTable'])
            c = self.get_cursor()
            c.execute(self.sql.query['createSettingsTable'])

            log.debug("Creating tables")
            c.execute(self.sql.query['createActionsTable'])
            c.execute(self.sql.query['createSitesTable'])
            c.execute(self.sql.query['createGametypesTable'])
            c.execute(self.sql.query['createPlayersTable'])
            c.execute(self.sql.query['createAutoratesTable'])
            c.execute(self.sql.query['createHandsTable'])
            c.execute(self.sql.query['createTourneyTypesTable'])
            c.execute(self.sql.query['createTourneysTable'])
            c.execute(self.sql.query['createTourneysPlayersTable'])
            c.execute(self.sql.query['createHandsPlayersTable'])
            c.execute(self.sql.query['createHandsActionsTable'])
            c.execute(self.sql.query['createHudCacheTable'])
            c.execute(self.sql.query['createSessionsCacheTable'])
            c.execute(self.sql.query['createBackingsTable'])
            c.execute(self.sql.query['createRawHands'])
            c.execute(self.sql.query['createRawTourneys'])

            # Create unique indexes:
            log.debug("Creating unique indexes")
            c.execute(self.sql.query['addTourneyIndex'])
            c.execute(self.sql.query['addHandsIndex'])
            c.execute(self.sql.query['addPlayersIndex'])
            c.execute(self.sql.query['addTPlayersIndex'])
            c.execute(self.sql.query['addTTypesIndex'])

            self.fillDefaultData()
            self.commit()
        except:
            #print "Error creating tables: ", str(sys.exc_value)
            err = traceback.extract_tb(sys.exc_info()[2])[-1]
            print _("***Error creating tables: ")+err[2]+"("+str(err[1])+"): "+str(sys.exc_info()[1])
            self.rollback()
            raise
#end def disconnect

    def drop_tables(self):
        """Drops the fpdb tables from the current db"""
        try:
            c = self.get_cursor()
        except:
            print _("*** Error unable to get databasecursor")
        else:
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
                    print _("***Error dropping tables: ")+err[2]+"("+str(err[1])+"): "+str(sys.exc_info()[1])
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
                    print _("***Error dropping tables: ")+err[2]+"("+str(err[1])+"): "+str(sys.exc_info()[1])
                    self.rollback()
            elif backend == 'SQLite':
                try:
                    c.execute(self.sql.query['list_tables'])
                    for table in c.fetchall():
                        log.debug(self.sql.query['drop_table'] + table[0])
                        c.execute(self.sql.query['drop_table'] + table[0])
                except:
                    err = traceback.extract_tb(sys.exc_info()[2])[-1]
                    print _("***Error dropping tables: ")+err[2]+"("+str(err[1])+"): "+str(sys.exc_info()[1])
                    self.rollback()
            try:
                self.commit()
            except:
                print _("*** Error in committing table drop")
                err = traceback.extract_tb(sys.exc_info()[2])[-1]
                print _("***Error dropping tables: ")+err[2]+"("+str(err[1])+"): "+str(sys.exc_info()[1])
                self.rollback()
    #end def drop_tables

    def createAllIndexes(self):
        """Create new indexes"""

        try:
            if self.backend == self.PGSQL:
                self.connection.set_isolation_level(0)   # allow table/index operations to work
            for idx in self.indexes[self.backend]:
                if self.backend == self.MYSQL_INNODB:
                    print _("Creating mysql index %s %s") %(idx['tab'], idx['col'])
                    log.debug(_("Creating mysql index %s %s") %(idx['tab'], idx['col']))
                    try:
                        s = "create index %s on %s(%s)" % (idx['col'],idx['tab'],idx['col'])
                        self.get_cursor().execute(s)
                    except:
                        print _("Create index failed: ") + str(sys.exc_info())
                elif self.backend == self.PGSQL:
                    # mod to use tab_col for index name?
                    print _("Creating pgsql index %s %s") %(idx['tab'], idx['col'])
                    log.debug(_("Creating pgsql index %s %s") %(idx['tab'], idx['col']))
                    try:
                        s = "create index %s_%s_idx on %s(%s)" % (idx['tab'], idx['col'], idx['tab'], idx['col'])
                        self.get_cursor().execute(s)
                    except:
                        print _("Create index failed: ") + str(sys.exc_info())
                elif self.backend == self.SQLITE:
                    print _("Creating sqlite index %s %s") %(idx['tab'], idx['col'])
                    log.debug(_("Creating sqlite index %s %s") %(idx['tab'], idx['col']))
                    try:
                        s = "create index %s_%s_idx on %s(%s)" % (idx['tab'], idx['col'], idx['tab'], idx['col'])
                        self.get_cursor().execute(s)
                    except:
                        log.debug(_("Create index failed: ") + str(sys.exc_info()))
                else:
                    print _("Unknown database: MySQL, Postgres and SQLite supported")
                    return -1
            if self.backend == self.PGSQL:
                self.connection.set_isolation_level(1)   # go back to normal isolation level
        except:
            print _("Error creating indexes: ") + str(sys.exc_value)
            raise FpdbError("Error creating indexes: " + str(sys.exc_value) )
    #end def createAllIndexes

    def dropAllIndexes(self):
        """Drop all standalone indexes (i.e. not including primary keys or foreign keys)
           using list of indexes in indexes data structure"""
        # maybe upgrade to use data dictionary?? (but take care to exclude PK and FK)
        if self.backend == self.PGSQL:
            self.connection.set_isolation_level(0)   # allow table/index operations to work
        for idx in self.indexes[self.backend]:
            if self.backend == self.MYSQL_INNODB:
                print _("dropping mysql index "), idx['tab'], idx['col']
                try:
                    self.get_cursor().execute( "alter table %s drop index %s"
                                             , (idx['tab'], idx['col']) )
                except:
                    print _("    drop index failed: ") + str(sys.exc_info())
            elif self.backend == self.PGSQL:
                print _("dropping pg index "), idx['tab'], idx['col']
                # mod to use tab_col for index name?
                try:
                    self.get_cursor().execute( "drop index %s_%s_idx"
                                               % (idx['tab'],idx['col']) )
                except:
                    print _("    drop index failed: ") + str(sys.exc_info())
            elif self.backend == self.SQLITE:
                print _("Dropping sqlite index "), idx['tab'], idx['col']
                try:
                    self.get_cursor().execute( "drop index %s_%s_idx"
                                               % (idx['tab'],idx['col']) )
                except:
                    print _("    drop index failed: ") + str(sys.exc_info())
            else:
                print _("Fpdb only supports MySQL, Postgres and SQLITE, what are you trying to use?")
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
            print _("    set_isolation_level failed: ") + str(sys.exc_info())

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
                    print _("creating foreign key "), fk['fktab'], fk['fkcol'], "->", fk['rtab'], fk['rcol']
                    try:
                        c.execute("alter table " + fk['fktab'] + " add foreign key ("
                                  + fk['fkcol'] + ") references " + fk['rtab'] + "("
                                  + fk['rcol'] + ")")
                    except:
                        print _("    create foreign key failed: ") + str(sys.exc_info())
            elif self.backend == self.PGSQL:
                print _("creating foreign key "), fk['fktab'], fk['fkcol'], "->", fk['rtab'], fk['rcol']
                try:
                    c.execute("alter table " + fk['fktab'] + " add constraint "
                              + fk['fktab'] + '_' + fk['fkcol'] + '_fkey'
                              + " foreign key (" + fk['fkcol']
                              + ") references " + fk['rtab'] + "(" + fk['rcol'] + ")")
                except:
                    print _("   create foreign key failed: ") + str(sys.exc_info())
            else:
                print _("Only MySQL and Postgres supported so far")

        try:
            if self.backend == self.PGSQL:
                self.connection.set_isolation_level(1)   # go back to normal isolation level
        except:
            print _("    set_isolation_level failed: ") + str(sys.exc_info())
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
                    print _("dropping mysql foreign key"), cons[0], fk['fktab'], fk['fkcol']
                    try:
                        c.execute("alter table " + fk['fktab'] + " drop foreign key " + cons[0])
                    except:
                        print _("    drop failed: ") + str(sys.exc_info())
            elif self.backend == self.PGSQL:
#    DON'T FORGET TO RECREATE THEM!!
                print _("dropping pg foreign key"), fk['fktab'], fk['fkcol']
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
                        print _("dropped pg foreign key %s_%s_fkey, continuing ...") % (fk['fktab'], fk['fkcol'])
                    except:
                        if "does not exist" not in str(sys.exc_value):
                            print _("warning: drop pg fk %s_%s_fkey failed: %s, continuing ...") \
                                  % (fk['fktab'], fk['fkcol'], str(sys.exc_value).rstrip('\n') )
                    c.execute("END TRANSACTION")
                except:
                    print _("warning: constraint %s_%s_fkey not dropped: %s, continuing ...") \
                          % (fk['fktab'],fk['fkcol'], str(sys.exc_value).rstrip('\n'))
            else:
                print _("Only MySQL and Postgres supported so far")

        if self.backend == self.PGSQL:
            self.connection.set_isolation_level(1)   # go back to normal isolation level
    #end def dropAllForeignKeys


    def fillDefaultData(self):
        c = self.get_cursor()
        c.execute("INSERT INTO Settings (version) VALUES (%s);" % (DB_VERSION))
        #Fill Sites
        c.execute("INSERT INTO Sites (name,code) VALUES ('Full Tilt Poker', 'FT')")
        c.execute("INSERT INTO Sites (name,code) VALUES ('PokerStars', 'PS')")
        c.execute("INSERT INTO Sites (name,code) VALUES ('Everleaf', 'EV')")
        c.execute("INSERT INTO Sites (name,code) VALUES ('Win2day', 'W2')")
        c.execute("INSERT INTO Sites (name,code) VALUES ('OnGame', 'OG')")
        c.execute("INSERT INTO Sites (name,code) VALUES ('UltimateBet', 'UB')")
        c.execute("INSERT INTO Sites (name,code) VALUES ('Betfair', 'BF')")
        c.execute("INSERT INTO Sites (name,code) VALUES ('Absolute', 'AB')")
        c.execute("INSERT INTO Sites (name,code) VALUES ('PartyPoker', 'PP')")
        c.execute("INSERT INTO Sites (name,code) VALUES ('Partouche', 'PA')")
        c.execute("INSERT INTO Sites (name,code) VALUES ('Carbon', 'CA')")
        c.execute("INSERT INTO Sites (name,code) VALUES ('PKR', 'PK')")
        c.execute("INSERT INTO Sites (name,code) VALUES ('iPoker', 'IP')")
        c.execute("INSERT INTO Sites (name,code) VALUES ('Winamax', 'WM')")
        c.execute("INSERT INTO Sites (name,code) VALUES ('Everest', 'EP')")
        #Fill Actions
        c.execute("INSERT INTO Actions (name,code) VALUES ('ante', 'A')")
        c.execute("INSERT INTO Actions (name,code) VALUES ('small blind', 'SB')")
        c.execute("INSERT INTO Actions (name,code) VALUES ('secondsb', 'SSB')")
        c.execute("INSERT INTO Actions (name,code) VALUES ('big blind', 'BB')")
        c.execute("INSERT INTO Actions (name,code) VALUES ('both', 'SBBB')")
        c.execute("INSERT INTO Actions (name,code) VALUES ('calls', 'C')")
        c.execute("INSERT INTO Actions (name,code) VALUES ('raises', 'R')")
        c.execute("INSERT INTO Actions (name,code) VALUES ('bets', 'B')")
        c.execute("INSERT INTO Actions (name,code) VALUES ('stands pat', 'S')")
        c.execute("INSERT INTO Actions (name,code) VALUES ('folds', 'F')")
        c.execute("INSERT INTO Actions (name,code) VALUES ('checks', 'K')")
        c.execute("INSERT INTO Actions (name,code) VALUES ('discards', 'D')")
        c.execute("INSERT INTO Actions (name,code) VALUES ('bringin', 'I')")
        c.execute("INSERT INTO Actions (name,code) VALUES ('completes', 'P')")

    #end def fillDefaultData

    def rebuild_indexes(self, start=None):
        self.dropAllIndexes()
        self.createAllIndexes()
        self.dropAllForeignKeys()
        self.createAllForeignKeys()
    #end def rebuild_indexes

    def rebuild_hudcache(self, h_start=None, v_start=None):
        """clears hudcache and rebuilds from the individual handsplayers records"""

        try:
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
            #print "rebuild_sql_cash:",rebuild_sql_cash
            self.get_cursor().execute(self.sql.query['clearHudCache'])
            self.get_cursor().execute(rebuild_sql_cash)

            if self.hero_ids == {}:
                where = "WHERE hp.tourneysPlayersId >= 0"
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
            #print "rebuild_sql_tourney:",rebuild_sql_tourney

            self.get_cursor().execute(rebuild_sql_tourney)
            self.commit()
            print _("Rebuild hudcache took %.1f seconds") % (time() - stime,)
        except:
            err = traceback.extract_tb(sys.exc_info()[2])[-1]
            print _("Error rebuilding hudcache:"), str(sys.exc_value)
            print err
    #end def rebuild_hudcache
    
    def rebuild_sessionscache(self, h_start=None, v_start=None):
        """clears sessionscache and rebuilds from the individual handsplayers records"""
        #Will get to this soon
        pass

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
        if self.backend == self.MYSQL_INNODB:
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
        if self.backend == self.MYSQL_INNODB:
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

    def lock_for_insert(self):
        """Lock tables in MySQL to try to speed inserts up"""
        try:
            self.get_cursor().execute(self.sql.query['lockForInsert'])
        except:
            print _("Error during lock_for_insert:"), str(sys.exc_value)
    #end def lock_for_insert

###########################
# NEWIMPORT CODE
###########################

    def storeHand(self, p, printdata = False):
        if printdata:
            print _("######## Hands ##########")
            import pprint
            pp = pprint.PrettyPrinter(indent=4)
            pp.pprint(p)
            print _("###### End Hands ########")

        # Tablename can have odd charachers
        p['tableName'] = Charset.to_db_utf8(p['tableName'])

        #stores into table hands:
        q = self.sql.query['store_hand']

        q = q.replace('%s', self.sql.query['placeholder'])

        c = self.get_cursor()

        c.execute(q, (
                p['tableName'],
                p['siteHandNo'],
                p['tourneyId'],
                p['gametypeId'],
                p['sessionId'],                
                p['startTime'],                
                datetime.utcnow(), #importtime
                p['seats'],
                p['maxSeats'],
                p['texture'],
                p['playersVpi'],
                p['boardcard1'],
                p['boardcard2'],
                p['boardcard3'],
                p['boardcard4'],
                p['boardcard5'],
                p['playersAtStreet1'],
                p['playersAtStreet2'],
                p['playersAtStreet3'],
                p['playersAtStreet4'],
                p['playersAtShowdown'],
                p['street0Raises'],
                p['street1Raises'],
                p['street2Raises'],
                p['street3Raises'],
                p['street4Raises'],
                p['street1Pot'],
                p['street2Pot'],
                p['street3Pot'],
                p['street4Pot'],
                p['showdownPot']
        ))
        return self.get_last_insert_id(c)
    # def storeHand

    def storeHandsPlayers(self, hid, pids, pdata, hp_bulk = None, insert = False, printdata = False):
        #print "DEBUG: %s %s %s" %(hid, pids, pdata)
        if printdata:
            import pprint
            pp = pprint.PrettyPrinter(indent=4)
            pp.pprint(pdata)

        inserts = []
        for p in pdata:
            inserts.append( (hid,
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
                             pdata[p]['winnings'],
                             pdata[p]['rake'],
                             pdata[p]['totalProfit'],
                             pdata[p]['street0VPI'],
                             pdata[p]['street1Seen'],
                             pdata[p]['street2Seen'],
                             pdata[p]['street3Seen'],
                             pdata[p]['street4Seen'],
                             pdata[p]['sawShowdown'],
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

        if insert:
            hp_bulk += inserts
            q = self.sql.query['store_hands_players']
            q = q.replace('%s', self.sql.query['placeholder'])
            c = self.get_cursor()
            c.executemany(q, hp_bulk)
            
        return inserts

    def storeHandsActions(self, hid, pids, adata, ha_bulk = None, insert = False, printdata = False):
        #print "DEBUG: %s %s %s" %(hid, pids, adata)

        # This can be used to generate test data. Currently unused
        #if printdata:
        #    import pprint
        #    pp = pprint.PrettyPrinter(indent=4)
        #    pp.pprint(adata)

        inserts = []
        for a in adata:
            inserts.append( (hid,
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

        if insert:
            ha_bulk += inserts
            q = self.sql.query['store_hands_actions']
            q = q.replace('%s', self.sql.query['placeholder'])
            c = self.get_cursor()
            c.executemany(q, ha_bulk)

        return inserts

    def storeHudCache(self, gid, pids, starttime, pdata):
        """Update cached statistics. If update fails because no record exists, do an insert."""

        tz = datetime.utcnow() - datetime.today()
        tz_offset = tz.seconds/3600
        tz_day_start_offset = self.day_start + tz_offset
        
        d = timedelta(hours=tz_day_start_offset)
        starttime_offset = starttime - d
        
        if self.use_date_in_hudcache:
            styleKey = datetime.strftime(starttime_offset, 'd%y%m%d')
            #styleKey = "d%02d%02d%02d" % (hand_start_time.year-2000, hand_start_time.month, hand_start_time.day)
        else:
            # hard-code styleKey as 'A000000' (all-time cache, no key) for now
            styleKey = 'A000000'

        update_hudcache = self.sql.query['update_hudcache']
        update_hudcache = update_hudcache.replace('%s', self.sql.query['placeholder'])
        insert_hudcache = self.sql.query['insert_hudcache']
        insert_hudcache = insert_hudcache.replace('%s', self.sql.query['placeholder'])

        #print "DEBUG: %s %s %s" %(hid, pids, pdata)
        inserts = []
        for p in pdata:
            #NOTE: Insert new stats at right place because SQL needs strict order
            line = []

            line.append(1)  # HDs
            line.append(pdata[p]['street0VPI'])
            line.append(pdata[p]['street0Aggr'])                 
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

            line.append(gid)          # gametypeId
            line.append(pids[p])      # playerId
            line.append(len(pids))    # activeSeats
            pos = {'B':'B', 'S':'S', 0:'D', 1:'C', 2:'M', 3:'M', 4:'M', 5:'E', 6:'E', 7:'E', 8:'E', 9:'E' }
            line.append(pos[pdata[p]['position']])
            line.append(pdata[p]['tourneyTypeId'])
            line.append(styleKey)    # styleKey
            inserts.append(line)


        cursor = self.get_cursor()

        for row in inserts:
            # Try to do the update first:
            num = cursor.execute(update_hudcache, row)
            #print "DEBUG: values: %s" % row[-6:]
            # Test statusmessage to see if update worked, do insert if not
            # num is a cursor in sqlite
            if ((self.backend == self.PGSQL and cursor.statusmessage != "UPDATE 1")
                    or (self.backend == self.MYSQL_INNODB and num == 0)
                    or (self.backend == self.SQLITE and num.rowcount == 0)):
                #move the last 6 items in WHERE clause of row from the end of the array
                # to the beginning for the INSERT statement
                #print "DEBUG: using INSERT: %s" % num
                row = row[-6:] + row[:-6]
                num = cursor.execute(insert_hudcache, row)
                #print "DEBUG: Successfully(?: %s) updated HudCacho using INSERT" % num
            else:
                #print "DEBUG: Successfully updated HudCacho using UPDATE"
                pass
            
    def storeSessionsCache(self, pids, startTime, game, pdata):
        """Update cached sessions. If no record exists, do an insert"""
        
        THRESHOLD = timedelta(seconds=int(self.sessionTimeout * 60))
        
        select_sessionscache = self.sql.query['select_sessionscache']
        select_sessionscache = select_sessionscache.replace('%s', self.sql.query['placeholder'])
        select_sessionscache_mid = self.sql.query['select_sessionscache_mid']
        select_sessionscache_mid = select_sessionscache_mid.replace('%s', self.sql.query['placeholder'])
        select_sessionscache_start = self.sql.query['select_sessionscache_start']
        select_sessionscache_start = select_sessionscache_start.replace('%s', self.sql.query['placeholder'])
    
        update_sessionscache_mid = self.sql.query['update_sessionscache_mid']
        update_sessionscache_mid = update_sessionscache_mid.replace('%s', self.sql.query['placeholder'])
        update_sessionscache_start = self.sql.query['update_sessionscache_start']
        update_sessionscache_start = update_sessionscache_start.replace('%s', self.sql.query['placeholder'])
        update_sessionscache_end = self.sql.query['update_sessionscache_end']
        update_sessionscache_end = update_sessionscache_end.replace('%s', self.sql.query['placeholder'])
        
        insert_sessionscache = self.sql.query['insert_sessionscache']
        insert_sessionscache = insert_sessionscache.replace('%s', self.sql.query['placeholder'])
        merge_sessionscache = self.sql.query['merge_sessionscache']
        merge_sessionscache = merge_sessionscache.replace('%s', self.sql.query['placeholder'])
        delete_sessions = self.sql.query['delete_sessions']
        delete_sessions = delete_sessions.replace('%s', self.sql.query['placeholder'])
        
        update_hands_sessionid = self.sql.query['update_hands_sessionid']
        update_hands_sessionid = update_hands_sessionid.replace('%s', self.sql.query['placeholder'])
        
        #Grab playerIds using hero names in HUD_Config.xml
        try:
            # derive list of program owner's player ids
            self.hero = {}                               # name of program owner indexed by site id
            self.hero_ids = []
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
                        self.hero_ids.append(int(p_id))

        except:
            err = traceback.extract_tb(sys.exc_info()[2])[-1]
            print _("Error aquiring hero ids:"), str(sys.exc_value)
            print err

        inserts = []
        for p in pdata:
            if pids[p] in self.hero_ids:
                line = [0]*5
    
                if (game['type']=='ring'): line[0] = 1 # count ring hands
                if (game['type']=='tour'): line[1] = 1 # count tour hands
                if (game['type']=='ring' and game['currency']=='USD'): line[2] = pdata[p]['totalProfit'] #sum of ring profit in USD
                if (game['type']=='ring' and game['currency']=='EUR'): line[3] = pdata[p]['totalProfit'] #sum of ring profit in EUR
                line[4] = startTime
                inserts.append(line)

        cursor = self.get_cursor()
        id = None

        for row in inserts:
            threshold = []
            threshold.append(row[-1]-THRESHOLD)
            threshold.append(row[-1]+THRESHOLD)
            cursor.execute(select_sessionscache, threshold)
            session_records = cursor.fetchall()
            num = len(session_records)
            if (num == 1):
                id = session_records[0][0] #grab the sessionId
                # Try to do the update first:
                #print "DEBUG: found 1 record to update"
                update_mid = row + row[-1:]
                cursor.execute(select_sessionscache_mid, update_mid[-2:])
                mid = len(cursor.fetchall())
                if (mid == 0):
                    update_startend = row[-1:] + row + threshold
                    cursor.execute(select_sessionscache_start, update_startend[-3:])
                    start = len(cursor.fetchall())
                    if (start == 0):
                        #print "DEBUG:", start, " start record found. Update stats and start time"
                        cursor.execute(update_sessionscache_end, update_startend)                 
                    else:
                        #print "DEBUG: 1 end record found. Update stats and end time time"
                        cursor.execute(update_sessionscache_start, update_startend) 
                else:
                    #print "DEBUG: update stats mid-session"
                    cursor.execute(update_sessionscache_mid, update_mid)
            elif (num > 1):
                session_ids = [session_records[0][0], session_records[1][0]]
                session_ids.sort()
                # Multiple matches found - merge them into one session and update:
                # - Obtain the session start and end times for the new combined session
                cursor.execute(merge_sessionscache, session_ids)
                merge = cursor.fetchone()
                # - Delete the old records
                for id in session_ids:
                    cursor.execute(delete_sessions, id)
                # - Insert the new updated record
                cursor.execute(insert_sessionscache, merge)
                # - Obtain the new sessionId and write over the old ids in Hands
                id = self.get_last_insert_id(cursor) #grab the sessionId
                update_hands = [id] + session_ids
                cursor.execute(update_hands_sessionid, update_hands)
                # - Update the newly combined record in SessionsCache with data from this hand
                update_mid = row + row[-1:]
                cursor.execute(update_sessionscache_mid, update_mid)
            elif (num == 0):
                # No matches found, insert new session:
                insert = row + row[-1:]
                insert = insert[-2:] + insert[:-2]
                #print "DEBUG: No matches found. Insert record", insert
                cursor.execute(insert_sessionscache, insert)
                id = self.get_last_insert_id(cursor) #grab the sessionId
            else:
                # Something bad happened
                pass
        
        return id 

    def isDuplicate(self, gametypeID, siteHandNo):
        dup = False
        c = self.get_cursor()
        c.execute(self.sql.query['isAlreadyInDB'], (gametypeID, siteHandNo))
        result = c.fetchall()
        if len(result) > 0:
            dup = True
        return dup

    def getGameTypeId(self, siteid, game, printdata = False):
        c = self.get_cursor()
        #FIXME: Fixed for NL at the moment
        c.execute(self.sql.query['getGametypeNL'], (siteid, game['type'], game['category'], game['limitType'], game['currency'],
                        int(Decimal(game['sb'])*100), int(Decimal(game['bb'])*100)))
        tmp = c.fetchone()
        if (tmp == None):
            hilo = "h"
            if game['category'] in ['studhilo', 'omahahilo']:
                hilo = "s"
            elif game['category'] in ['razz','27_3draw','badugi', '27_1draw']:
                hilo = "l"
            #FIXME: recognise currency
            #TODO: this wont work for non-standard structures
            tmp  = self.insertGameTypes( (siteid, game['currency'], game['type'], game['base'], game['category'], game['limitType'], hilo,
                                    int(Decimal(game['sb'])*100), int(Decimal(game['bb'])*100),
                                    int(Decimal(game['bb'])*100), int(Decimal(game['bb'])*200)), printdata = printdata)
        return tmp[0]


    def insertGameTypes(self, row, printdata = False):
        if printdata:
            print _("######## Gametype ##########")
            import pprint
            pp = pprint.PrettyPrinter(indent=4)
            pp.pprint(row)
            print _("###### End Gametype ########")

        c = self.get_cursor()
        c.execute( self.sql.query['insertGameTypes'], row )
        return [self.get_last_insert_id(c)]



#################################
# Finish of NEWIMPORT CODE
#################################

    # read HandToWrite objects from q and insert into database
    def insert_queue_hands(self, q, maxwait=10, commitEachHand=True):
        n,fails,maxTries,firstWait = 0,0,4,0.1
        sendFinal = False
        t0 = time()
        while True:
            try:
                h = q.get(True)  # (True,maxWait) has probs if 1st part of import is all dups
            except Queue.Empty:
                # Queue.Empty exception thrown if q was empty for
                # if q.empty() also possible - no point if testing for Queue.Empty exception
                # maybe increment a counter and only break after a few times?
                # could also test threading.active_count() or look through threading.enumerate()
                # so break immediately if no threads, but count up to X exceptions if a writer
                # thread is still alive???
                print _("queue empty too long - writer stopping ...")
                break
            except:
                print _("writer stopping, error reading queue: ") + str(sys.exc_info())
                break
            #print "got hand", str(h.get_finished())

            tries,wait,again = 0,firstWait,True
            while again:
                try:
                    again = False # set this immediately to avoid infinite loops!
                    if h.get_finished():
                        # all items on queue processed
                        sendFinal = True
                    else:
                        self.store_the_hand(h)
                        # optional commit, could be every hand / every N hands / every time a
                        # commit message received?? mark flag to indicate if commits outstanding
                        if commitEachHand:
                            self.commit()
                        n = n + 1
                except:
                    #print "iqh store error", sys.exc_value # debug
                    self.rollback()
                    if re.search('deadlock', str(sys.exc_info()[1]), re.I):
                        # deadlocks only a problem if hudcache is being updated
                        tries = tries + 1
                        if tries < maxTries and wait < 5:    # wait < 5 just to make sure
                            print _("deadlock detected - trying again ...")
                            sleep(wait)
                            wait = wait + wait
                            again = True
                        else:
                            print _("too many deadlocks - failed to store hand ") + h.get_siteHandNo()
                    if not again:
                        fails = fails + 1
                        err = traceback.extract_tb(sys.exc_info()[2])[-1]
                        print _("***Error storing hand: ")+err[2]+"("+str(err[1])+"): "+str(sys.exc_info()[1])
            # finished trying to store hand

            # always reduce q count, whether or not this hand was saved ok
            q.task_done()
        # while True loop

        self.commit()
        if sendFinal:
            q.task_done()
        print _("db writer finished: stored %d hands (%d fails) in %.1f seconds") % (n, fails, time()-t0)
    # end def insert_queue_hands():


    def send_finish_msg(self, q):
        try:
            h = HandToWrite(True)
            q.put(h)
        except:
            err = traceback.extract_tb(sys.exc_info()[2])[-1]
            print _("***Error sending finish: ")+err[2]+"("+str(err[1])+"): "+str(sys.exc_info()[1])
    # end def send_finish_msg():

    def createTourneyType(self, hand):#note: this method is used on Hand and TourneySummary objects
        tourneyTypeId = 1

        # Check if Tourney exists, and if so retrieve TTypeId : in that case, check values of the ttype
        cursor = self.get_cursor()
        cursor.execute (self.sql.query['getTourneyTypeIdByTourneyNo'].replace('%s', self.sql.query['placeholder']),
                        (hand.tourNo, hand.siteId)
                        )
        result=cursor.fetchone()
        #print "result of fetching TT by number and site:",result

        if result:
            tourneyTypeId = result[0]
        else:
            # Check for an existing TTypeId that matches tourney info, if not found create it
            #print "info that we use to get TT by detail:", hand.siteId, hand.buyinCurrency, hand.buyin, hand.fee, hand.gametype['category'], hand.gametype['limitType'], hand.isKO, hand.isRebuy, hand.isAddOn, hand.speed, hand.isShootout, hand.isMatrix
            #print "the query:",self.sql.query['getTourneyTypeId'].replace('%s', self.sql.query['placeholder'])
            cursor.execute (self.sql.query['getTourneyTypeId'].replace('%s', self.sql.query['placeholder']),
                            (hand.siteId, hand.buyinCurrency, hand.buyin, hand.fee, hand.gametype['category'],
                             hand.gametype['limitType'], hand.maxseats, hand.isKO,
                             hand.isRebuy, hand.isAddOn, hand.speed, hand.isShootout, hand.isMatrix)
                            )
            result=cursor.fetchone()
            #print "result of fetching TT by details:",result

            try:
                tourneyTypeId = result[0]
            except TypeError: #this means we need to create a new entry
                cursor.execute (self.sql.query['insertTourneyType'].replace('%s', self.sql.query['placeholder']),
                                (hand.siteId, hand.buyinCurrency, hand.buyin, hand.fee, hand.gametype['category'],
                                 hand.gametype['limitType'], hand.maxseats,
                                 hand.buyInChips, hand.isKO, hand.koBounty, hand.isRebuy,
                                 hand.isAddOn, hand.speed, hand.isShootout, hand.isMatrix, hand.added, hand.addedCurrency)
                                )
                tourneyTypeId = self.get_last_insert_id(cursor)
        return tourneyTypeId
    #end def createTourneyType

    def createOrUpdateTourney(self, hand, source):#note: this method is used on Hand and TourneySummary objects
        cursor = self.get_cursor()
        cursor.execute (self.sql.query['getTourneyByTourneyNo'].replace('%s', self.sql.query['placeholder']),
                        (hand.siteId, hand.tourNo))
        columnNames=[desc[0] for desc in cursor.description]
        result=cursor.fetchone()

        if result != None:
            if self.backend == Database.PGSQL:
                expectedValues = ('comment', 'tourneyname', 'matrixIdProcessed', 'totalRebuyCount', 'totalAddOnCount',
                        'prizepool', 'startTime', 'entries', 'commentTs', 'endTime')
            else:
                expectedValues = ('comment', 'tourneyName', 'matrixIdProcessed', 'totalRebuyCount', 'totalAddOnCount',
                        'prizepool', 'startTime', 'entries', 'commentTs', 'endTime')
            updateDb=False
            resultDict = dict(zip(columnNames, result))

            tourneyId = resultDict["id"]
            if source=="TS":
                for ev in expectedValues :
                    if getattr(hand, ev)==None and resultDict[ev]!=None:#DB has this value but object doesnt, so update object
                        setattr(hand, ev, resultDict[ev])
                    elif getattr(hand, ev)!=None and resultDict[ev]==None:#object has this value but DB doesnt, so update DB
                        updateDb=True
                    #elif ev=="startTime":
                    #    if (resultDict[ev] < hand.startTime):
                    #        hand.startTime=resultDict[ev]
                if updateDb:
                    cursor.execute (self.sql.query['updateTourney'].replace('%s', self.sql.query['placeholder']),
                           (hand.entries, hand.prizepool, hand.startTime, hand.endTime, hand.tourneyName,
                            hand.matrixIdProcessed, hand.totalRebuyCount, hand.totalAddOnCount, hand.comment, hand.commentTs, tourneyId))
        else:
            if source=="HHC":
                cursor.execute (self.sql.query['insertTourney'].replace('%s', self.sql.query['placeholder']),
                        (hand.tourneyTypeId, hand.tourNo, None, None,
                         hand.startTime, None, None, None, None, None))
            elif source=="TS":
                cursor.execute (self.sql.query['insertTourney'].replace('%s', self.sql.query['placeholder']),
                        (hand.tourneyTypeId, hand.tourNo, hand.entries, hand.prizepool, hand.startTime,
                         hand.endTime, hand.tourneyName, hand.matrixIdProcessed, hand.totalRebuyCount, hand.totalAddOnCount))
            else:
                raise FpdbParseError(_("invalid source in Database.createOrUpdateTourney"))
            tourneyId = self.get_last_insert_id(cursor)
        return tourneyId
    #end def createOrUpdateTourney

    def createOrUpdateTourneysPlayers(self, hand, source):#note: this method is used on Hand and TourneySummary objects
        tourneysPlayersIds={}
        for player in hand.players:
            if source=="TS": #TODO remove this horrible hack
                playerId = hand.dbid_pids[player]
            elif source=="HHC":
                playerId = hand.dbid_pids[player[1]]
            else:
                raise FpdbParseError(_("invalid source in Database.createOrUpdateTourneysPlayers"))

            cursor = self.get_cursor()
            cursor.execute (self.sql.query['getTourneysPlayersByIds'].replace('%s', self.sql.query['placeholder']),
                            (hand.tourneyId, playerId))
            columnNames=[desc[0] for desc in cursor.description]
            result=cursor.fetchone()

            if result != None:
                expectedValues = ('rank', 'winnings', 'winningsCurrency', 'rebuyCount', 'addOnCount', 'koCount')
                updateDb=False
                resultDict = dict(zip(columnNames, result))

                tourneysPlayersIds[player[1]]=result[0]
                if source=="TS":
                    for ev in expectedValues :
                        handAttribute=ev
                        if ev!="winnings" and ev!="winningsCurrency":
                            handAttribute+="s"

                        if getattr(hand, handAttribute)[player]==None and resultDict[ev]!=None:#DB has this value but object doesnt, so update object
                            setattr(hand, handAttribute, resultDict[ev][player])
                        elif getattr(hand, handAttribute)[player]!=None and resultDict[ev]==None:#object has this value but DB doesnt, so update DB
                            updateDb=True
                    if updateDb:
                        cursor.execute (self.sql.query['updateTourneysPlayer'].replace('%s', self.sql.query['placeholder']),
                               (hand.ranks[player], hand.winnings[player], hand.winningsCurrency[player],
                                 hand.rebuyCounts[player], hand.addOnCounts[player], hand.koCounts[player], tourneysPlayersIds[player[1]]))
            else:
                if source=="HHC":
                    cursor.execute (self.sql.query['insertTourneysPlayer'].replace('%s', self.sql.query['placeholder']),
                            (hand.tourneyId, playerId, None, None, None, None, None, None))
                elif source=="TS":
                    #print "all values: tourneyId",hand.tourneyId, "playerId",playerId, "rank",hand.ranks[player], "winnings",hand.winnings[player], "winCurr",hand.winningsCurrency[player], hand.rebuyCounts[player], hand.addOnCounts[player], hand.koCounts[player]
                    if hand.ranks[player]:
                        cursor.execute (self.sql.query['insertTourneysPlayer'].replace('%s', self.sql.query['placeholder']),
                                (hand.tourneyId, playerId, int(hand.ranks[player]), int(hand.winnings[player]), hand.winningsCurrency[player],
                                 hand.rebuyCounts[player], hand.addOnCounts[player], hand.koCounts[player]))
                    else:
                        cursor.execute (self.sql.query['insertTourneysPlayer'].replace('%s', self.sql.query['placeholder']),
                                (hand.tourneyId, playerId, None, None, None,
                                 hand.rebuyCounts[player], hand.addOnCounts[player], hand.koCounts[player]))
                tourneysPlayersIds[player[1]]=self.get_last_insert_id(cursor)
        return tourneysPlayersIds
    #end def createOrUpdateTourneysPlayers

    def getTourneyTypesIds(self):
        c = self.connection.cursor()
        c.execute(self.sql.query['getTourneyTypesIds'])
        result = c.fetchall()
        return result
    #end def getTourneyTypesIds

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
#end class Database

# Class used to hold all the data needed to write a hand to the db
# mainParser() in fpdb_parse_logic.py creates one of these and then passes it to
# self.insert_queue_hands()

class HandToWrite:

    def __init__(self, finished = False): # db_name and game not used any more
        try:
            self.finished = finished
            self.config = None
            self.settings = None
            self.base = None
            self.category = None
            self.siteTourneyNo = None
            self.buyin = None
            self.fee = None
            self.knockout = None
            self.entries = None
            self.prizepool = None
            self.tourneyStartTime = None
            self.isTourney = None
            self.tourneyTypeId = None
            self.siteID = None
            self.siteHandNo = None
            self.gametypeID = None
            self.handStartTime = None
            self.names = None
            self.playerIDs = None
            self.startCashes = None
            self.positions = None
            self.antes = None
            self.cardValues = None
            self.cardSuits = None
            self.boardValues = None
            self.boardSuits = None
            self.winnings = None
            self.rakes = None
            self.actionTypes = None
            self.allIns = None
            self.actionAmounts = None
            self.actionNos = None
            self.hudImportData = None
            self.maxSeats = None
            self.tableName = None
            self.seatNos = None
        except:
            print _("HandToWrite.init error: ") + str(sys.exc_info())
            raise
    # end def __init__

    def set_all( self, config, settings, base, category, siteTourneyNo, buyin
               , fee, knockout, entries, prizepool, tourneyStartTime
               , isTourney, tourneyTypeId, siteID, siteHandNo
               , gametypeID, handStartTime, names, playerIDs, startCashes
               , positions, antes, cardValues, cardSuits, boardValues, boardSuits
               , winnings, rakes, actionTypes, allIns, actionAmounts
               , actionNos, hudImportData, maxSeats, tableName, seatNos):

        try:
            self.config = config
            self.settings = settings
            self.base = base
            self.category = category
            self.siteTourneyNo = siteTourneyNo
            self.buyin = buyin
            self.fee = fee
            self.knockout = knockout
            self.entries = entries
            self.prizepool = prizepool
            self.tourneyStartTime = tourneyStartTime
            self.isTourney = isTourney
            self.tourneyTypeId = tourneyTypeId
            self.siteID = siteID
            self.siteHandNo = siteHandNo
            self.gametypeID = gametypeID
            self.handStartTime = handStartTime
            self.names = names
            self.playerIDs = playerIDs
            self.startCashes = startCashes
            self.positions = positions
            self.antes = antes
            self.cardValues = cardValues
            self.cardSuits = cardSuits
            self.boardValues = boardValues
            self.boardSuits = boardSuits
            self.winnings = winnings
            self.rakes = rakes
            self.actionTypes = actionTypes
            self.allIns = allIns
            self.actionAmounts = actionAmounts
            self.actionNos = actionNos
            self.hudImportData = hudImportData
            self.maxSeats = maxSeats
            self.tableName = tableName
            self.seatNos = seatNos
        except:
            print _("HandToWrite.set_all error: ") + str(sys.exc_info())
            raise
    # end def set_hand

    def get_finished(self):
        return( self.finished )
    # end def get_finished

    def get_siteHandNo(self):
        return( self.siteHandNo )
    # end def get_siteHandNo


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
        print _("nutOmatic is id_player = %d") % hero

    # example of displaying query plan in sqlite:
    if db_connection.backend == 4:
        print
        c = db_connection.get_cursor()
        c.execute('explain query plan '+sql.query['get_table_name'], (h, ))
        for row in c.fetchall():
            print _("query plan: "), row
        print

    t0 = time()
    stat_dict = db_connection.get_stats_from_hand(h, "ring")
    t1 = time()
    for p in stat_dict.keys():
        print p, "  ", stat_dict[p]

    print _("cards ="), db_connection.get_cards(u'1')
    db_connection.close_connection

    print _("get_stats took:  %4.3f seconds") % (t1-t0)

    print _("press enter to continue")
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
