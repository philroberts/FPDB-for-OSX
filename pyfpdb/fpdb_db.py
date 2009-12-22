#!/usr/bin/python
# -*- coding: utf-8 -*-

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
import sys
import logging
import math
from time import time, strftime
from Exceptions import *

try:
    import sqlalchemy.pool as pool
    use_pool = True
except ImportError:
    logging.info("Not using sqlalchemy connection pool.")
    use_pool = False

try:
    from numpy import var
    use_numpy = True
except ImportError:
    logging.info("Not using numpy to define variance in sqlite.")
    use_numpy = False

import FpdbSQLQueries
import Configuration

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

class fpdb_db:
    MYSQL_INNODB = 2
    PGSQL = 3
    SQLITE = 4

    def __init__(self):
        """Simple constructor, doesnt really do anything"""
        self.db             = None
        self.cursor         = None
        self.sql            = {}
    #end def __init__

    def do_connect(self, config=None):
        """Connects a database using information in config"""
        if config is None:
            raise FpdbError('Configuration not defined')

        self.settings = {}
        self.settings['os'] = "linuxmac" if os.name != "nt" else "windows"

        db = config.get_db_parameters()
        self.connect(backend=db['db-backend'],
                     host=db['db-host'],
                     database=db['db-databaseName'],
                     user=db['db-user'],
                     password=db['db-password'])
    #end def do_connect

    def connect(self, backend=None, host=None, database=None,
                user=None, password=None):
        """Connects a database with the given parameters"""
        if backend is None:
            raise FpdbError('Database backend not defined')
        self.backend = backend
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        if backend == fpdb_db.MYSQL_INNODB:
            import MySQLdb
            if use_pool:
                MySQLdb = pool.manage(MySQLdb, pool_size=5)
            try:
                self.db = MySQLdb.connect(host=host, user=user, passwd=password, db=database, use_unicode=True)
            #TODO: Add port option
            except MySQLdb.Error, ex:
                if ex.args[0] == 1045:
                    raise FpdbMySQLAccessDenied(ex.args[0], ex.args[1])
                elif ex.args[0] == 2002 or ex.args[0] == 2003: # 2002 is no unix socket, 2003 is no tcp socket
                    raise FpdbMySQLNoDatabase(ex.args[0], ex.args[1])
                else:
                    print "*** WARNING UNKNOWN MYSQL ERROR", ex
        elif backend == fpdb_db.PGSQL:
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
            connected = False
            if self.host == "localhost" or self.host == "127.0.0.1":
                try:
                    self.db = psycopg2.connect(database = database)
                    connected = True
                except:
                    # direct connection failed so try user/pass/... version
                    pass
            if not connected:
                try:
                    self.db = psycopg2.connect(host = host,
                                               user = user,
                                               password = password,
                                               database = database)
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
        elif backend == fpdb_db.SQLITE:
            logging.info("Connecting to SQLite:%(database)s" % {'database':database})
            import sqlite3
            if use_pool:
                sqlite3 = pool.manage(sqlite3, pool_size=1)
            else:
                logging.warning("SQLite won't work well without 'sqlalchemy' installed.")

            if not os.path.isdir(Configuration.DIR_DATABASES) and not database ==  ":memory:":
                print "Creating directory: '%s'" % (Configuration.DIR_DATABASES)
                os.mkdir(Configuration.DIR_DATABASES)
                database = os.path.join(Configuration.DIR_DATABASES, database)
            self.db = sqlite3.connect(database, detect_types=sqlite3.PARSE_DECLTYPES )
            sqlite3.register_converter("bool", lambda x: bool(int(x)))
            sqlite3.register_adapter(bool, lambda x: "1" if x else "0")
            self.db.create_function("floor", 1, math.floor)
            tmp = sqlitemath()
            self.db.create_function("mod", 2, tmp.mod)
            if use_numpy:
                self.db.create_aggregate("variance", 1, VARIANCE)
            else:
                logging.warning("Some database functions will not work without NumPy support")
        else:
            raise FpdbError("unrecognised database backend:"+backend)

        self.cursor = self.db.cursor()
        # Set up query dictionary as early in the connection process as we can.
        self.sql = FpdbSQLQueries.FpdbSQLQueries(self.get_backend_name())
        self.cursor.execute(self.sql.query['set tx level'])
        self.wrongDbVersion = False
        try:
            self.cursor.execute("SELECT * FROM Settings")
            settings = self.cursor.fetchone()
            if settings[0] != 118:
                print "outdated or too new database version - please recreate tables"
                self.wrongDbVersion = True
        except:# _mysql_exceptions.ProgrammingError:
            if database !=  ":memory:": print "failed to read settings table - please recreate tables"
            self.wrongDbVersion = True
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
    #end def get_backend_name

    def get_db_info(self):
        return (self.host, self.database, self.user, self.password)
    #end def get_db_info

#end class fpdb_db
