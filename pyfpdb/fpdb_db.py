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
import sys
from time import time, strftime

import fpdb_simple
import FpdbSQLQueries

class fpdb_db:
    def __init__(self):
        """Simple constructor, doesnt really do anything"""
        self.db             = None
        self.cursor         = None
        self.sql            = {}
        self.MYSQL_INNODB   = 2
        self.PGSQL          = 3
        self.SQLITE         = 4

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

        self.indexes = [
                         [ ] # no db with index 0
                       , [ ] # no db with index 1
                       , [ # indexes for mysql (list index 2)
                           {'tab':'Players',  'col':'name',          'drop':0}
                         , {'tab':'Hands',    'col':'siteHandNo',    'drop':0}
                         , {'tab':'Tourneys', 'col':'siteTourneyNo', 'drop':0}
                         ]
                       , [ # indexes for postgres (list index 3)
                           {'tab':'Boardcards',      'col':'handId',            'drop':0}
                         , {'tab':'Gametypes',       'col':'siteId',            'drop':0}
                         , {'tab':'Hands',           'col':'gametypeId',        'drop':0} # mct 22/3/09
                         , {'tab':'Hands',           'col':'siteHandNo',        'drop':0}
                         , {'tab':'HandsActions',    'col':'handsPlayerId',     'drop':0}
                         , {'tab':'HandsPlayers',    'col':'handId',            'drop':1}
                         , {'tab':'HandsPlayers',    'col':'playerId',          'drop':1}
                         , {'tab':'HandsPlayers',    'col':'tourneysPlayersId', 'drop':0}
                         , {'tab':'HudCache',        'col':'gametypeId',        'drop':1}
                         , {'tab':'HudCache',        'col':'playerId',          'drop':0}
                         , {'tab':'HudCache',        'col':'tourneyTypeId',     'drop':0}
                         , {'tab':'Players',         'col':'siteId',            'drop':1}
                         , {'tab':'Players',         'col':'name',              'drop':0}
                         , {'tab':'Tourneys',        'col':'tourneyTypeId',     'drop':1}
                         , {'tab':'Tourneys',        'col':'siteTourneyNo',     'drop':0}
                         , {'tab':'TourneysPlayers', 'col':'playerId',          'drop':0}
                         , {'tab':'TourneysPlayers', 'col':'tourneyId',         'drop':0}
                         , {'tab':'TourneyTypes',    'col':'siteId',            'drop':0}
                         ]
                       ]

        self.foreignKeys = [
                             [ ] # no db with index 0
                           , [ ] # no db with index 1
                           , [ # foreign keys for mysql
                               {'fktab':'Hands',        'fkcol':'gametypeId',    'rtab':'Gametypes',     'rcol':'id', 'drop':1}
                             , {'fktab':'HandsPlayers', 'fkcol':'handId',        'rtab':'Hands',         'rcol':'id', 'drop':1}
                             , {'fktab':'HandsPlayers', 'fkcol':'playerId',      'rtab':'Players',       'rcol':'id', 'drop':1}
                             , {'fktab':'HandsActions', 'fkcol':'handsPlayerId', 'rtab':'HandsPlayers',  'rcol':'id', 'drop':1}
                             , {'fktab':'HudCache',     'fkcol':'gametypeId',    'rtab':'Gametypes',     'rcol':'id', 'drop':1}
                             , {'fktab':'HudCache',     'fkcol':'playerId',      'rtab':'Players',       'rcol':'id', 'drop':0}
                             , {'fktab':'HudCache',     'fkcol':'tourneyTypeId', 'rtab':'TourneyTypes',  'rcol':'id', 'drop':1}
                             ]
                           , [ # foreign keys for postgres
                               {'fktab':'Hands',        'fkcol':'gametypeId',    'rtab':'Gametypes',     'rcol':'id', 'drop':1}
                             , {'fktab':'HandsPlayers', 'fkcol':'handId',        'rtab':'Hands',         'rcol':'id', 'drop':1}
                             , {'fktab':'HandsPlayers', 'fkcol':'playerId',      'rtab':'Players',       'rcol':'id', 'drop':1}
                             , {'fktab':'HandsActions', 'fkcol':'handsPlayerId', 'rtab':'HandsPlayers',  'rcol':'id', 'drop':1}
                             , {'fktab':'HudCache',     'fkcol':'gametypeId',    'rtab':'Gametypes',     'rcol':'id', 'drop':1}
                             , {'fktab':'HudCache',     'fkcol':'playerId',      'rtab':'Players',       'rcol':'id', 'drop':0}
                             , {'fktab':'HudCache',     'fkcol':'tourneyTypeId', 'rtab':'TourneyTypes',  'rcol':'id', 'drop':1}
                             ]
                           ]


        # MySQL Notes:
        #    "FOREIGN KEY (handId) REFERENCES Hands(id)" - requires index on Hands.id
        #                                                - creates index handId on <thistable>.handId
        # alter table t drop foreign key fk
        # alter table t add foreign key (fkcol) references tab(rcol)
        # alter table t add constraint c foreign key (fkcol) references tab(rcol)
        # (fkcol is used for foreigh key name)

        # mysql to list indexes:
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
    #end def __init__

    def do_connect(self, config=None):
        """Connects a database using information in config"""
        if config is None:
            raise FpdbError('Configuration not defined')

        self.settings = {}
        self.settings['os'] = "linuxmac" if os.name != "nt" else "windows"

        self.settings.update(config.get_db_parameters())
        self.connect(self.settings['db-backend'],
                     self.settings['db-host'],
                     self.settings['db-databaseName'],
                     self.settings['db-user'], 
                     self.settings['db-password'])
    #end def do_connect
    
    def connect(self, backend=None, host=None, database=None,
                user=None, password=None):
        """Connects a database with the given parameters"""
        if backend is None:
            raise FpdbError('Database backend not defined')
        self.backend=backend
        self.host=host
        self.user=user
        self.password=password
        self.database=database
        if backend==self.MYSQL_INNODB:
            import MySQLdb
            try:
                self.db = MySQLdb.connect(host = host, user = user, passwd = password, db = database, use_unicode=True)
            except:
                raise fpdb_simple.FpdbError("MySQL connection failed")
        elif backend==self.PGSQL:
            import psycopg2
            import psycopg2.extensions 
            psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
            # If DB connection is made over TCP, then the variables
            # host, user and password are required
            # For local domain-socket connections, only DB name is
            # needed, and everything else is in fact undefined and/or
            # flat out wrong
            # sqlcoder: This database only connect failed in my windows setup??
            # Modifed it to try the 4 parameter style if the first connect fails - does this work everywhere?
            connected = False
            if self.host == None or self.host == '' \
                    or self.host == "localhost" \
                    or self.host == "127.0.0.1":
                try:
                    self.db = psycopg2.connect(database = database)
                    connected = True
                except:
                    pass
                    #msg = "PostgreSQL direct connection to database (%s) failed, trying with user ..." % (database,)
                    #print msg
                    #raise fpdb_simple.FpdbError(msg)
            if not connected:
                try:
                    self.db = psycopg2.connect(host = host,
                                               user = user, 
                                               password = password, 
                                               database = database)
                except:
                    msg = "PostgreSQL connection to database (%s) user (%s) failed." % (database, user)
                    print msg
                    raise fpdb_simple.FpdbError(msg)
        else:
            raise fpdb_simple.FpdbError("unrecognised database backend:"+backend)
        self.cursor=self.db.cursor()
        self.cursor.execute('SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED')
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
        self.cursor.execute(self.sql.query['createTourneyTypesTable'])
        self.cursor.execute(self.sql.query['createTourneysTable'])
        self.cursor.execute(self.sql.query['createTourneysPlayersTable'])
        self.cursor.execute(self.sql.query['createHandsPlayersTable'])
        self.cursor.execute(self.sql.query['createHandsActionsTable'])
        self.cursor.execute(self.sql.query['createHudCacheTable'])
        #self.cursor.execute(self.sql.query['addTourneyIndex'])
        #self.cursor.execute(self.sql.query['addHandsIndex'])
        #self.cursor.execute(self.sql.query['addPlayersIndex'])
        self.fillDefaultData()
        self.db.commit()
#end def disconnect
    
    def drop_tables(self):
        """Drops the fpdb tables from the current db"""

        if(self.get_backend_name() == 'MySQL InnoDB'):
            #Databases with FOREIGN KEY support need this switched of before you can drop tables
            self.drop_referential_integrity()

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

    def drop_referential_integrity(self):
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
        #end drop_referential_inegrity
    
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
        self.cursor.execute("INSERT INTO Sites VALUES (DEFAULT, 'Everleaf', 'USD');")
        self.cursor.execute("INSERT INTO TourneyTypes VALUES (DEFAULT, 1, 0, 0, 0, False);")
    #end def fillDefaultData
    
    def recreate_tables(self):
        """(Re-)creates the tables of the current DB"""
        
        self.drop_tables()
        self.create_tables()
        self.createAllIndexes()
        self.db.commit()
        print "Finished recreating tables"
    #end def recreate_tables

    def prepareBulkImport(self):
        """Drop some indexes/foreign keys to prepare for bulk import. 
           Currently keeping the standalone indexes as needed to import quickly"""
        stime = time()
        if self.backend == self.PGSQL:
            self.db.set_isolation_level(0)   # allow table/index operations to work
        for fk in self.foreignKeys[self.backend]:
            if fk['drop'] == 1:
                if self.backend == self.MYSQL_INNODB:
                    self.cursor.execute("SELECT constraint_name " +
                                       "FROM information_schema.KEY_COLUMN_USAGE " +
                                       #"WHERE REFERENCED_TABLE_SCHEMA = 'fpdb'
                                       "WHERE 1=1 " +
                                       "AND table_name = %s AND column_name = %s " + 
                                       "AND referenced_table_name = %s " +
                                       "AND referenced_column_name = %s ",
                                       (fk['fktab'], fk['fkcol'], fk['rtab'], fk['rcol']) )
                    cons = self.cursor.fetchone()
                    #print "preparebulk: cons=", cons
                    if cons:
                        print "dropping mysql fk", cons[0], fk['fktab'], fk['fkcol']
                        try:
                            self.cursor.execute("alter table " + fk['fktab'] + " drop foreign key " + cons[0])
                        except:
                            pass
                elif self.backend == self.PGSQL:
    #    DON'T FORGET TO RECREATE THEM!!
                    print "dropping pg fk", fk['fktab'], fk['fkcol']
                    try:
                        # try to lock table to see if index drop will work:
                        # hmmm, tested by commenting out rollback in grapher. lock seems to work but 
                        # then drop still hangs :-(  does work in some tests though??
                        # will leave code here for now pending further tests/enhancement ...
                        self.cursor.execute( "lock table %s in exclusive mode nowait" % (fk['fktab'],) )
                        #print "after lock, status:", self.cursor.statusmessage
                        #print "alter table %s drop constraint %s_%s_fkey" % (fk['fktab'], fk['fktab'], fk['fkcol'])
                        try:
                            self.cursor.execute("alter table %s drop constraint %s_%s_fkey" % (fk['fktab'], fk['fktab'], fk['fkcol']))
                            print "dropped pg fk pg fk %s_%s_fkey, continuing ..." % (fk['fktab'], fk['fkcol'])
                        except:
                            if "does not exist" not in str(sys.exc_value):
                                print "warning: drop pg fk %s_%s_fkey failed: %s, continuing ..." \
                                      % (fk['fktab'], fk['fkcol'], str(sys.exc_value).rstrip('\n') )
                    except:
                        print "warning: constraint %s_%s_fkey not dropped: %s, continuing ..." \
                              % (fk['fktab'],fk['fkcol'], str(sys.exc_value).rstrip('\n'))
                else:
                    print "Only MySQL and Postgres supported so far"
                    return -1
        
        for idx in self.indexes[self.backend]:
            if idx['drop'] == 1:
                if self.backend == self.MYSQL_INNODB:
                    print "dropping mysql index ", idx['tab'], idx['col']
                    try:
                        # apparently nowait is not implemented in mysql so this just hands if there are locks 
                        # preventing the index drop :-(
                        self.cursor.execute( "alter table %s drop index %s", (idx['tab'],idx['col']) )
                    except:
                        pass
                elif self.backend == self.PGSQL:
    #    DON'T FORGET TO RECREATE THEM!!
                    print "dropping pg index ", idx['tab'], idx['col']
                    try:
                        # try to lock table to see if index drop will work:
                        self.cursor.execute( "lock table %s in exclusive mode nowait" % (idx['tab'],) )
                        #print "after lock, status:", self.cursor.statusmessage
                        try:
                            # table locked ok so index drop should work:
                            #print "drop index %s_%s_idx" % (idx['tab'],idx['col']) 
                            self.cursor.execute( "drop index if exists %s_%s_idx" % (idx['tab'],idx['col']) )
                            #print "dropped  pg index ", idx['tab'], idx['col']
                        except:
                            if "does not exist" not in str(sys.exc_value):
                                print "warning: drop index %s_%s_idx failed: %s, continuing ..." \
                                      % (idx['tab'],idx['col'], str(sys.exc_value).rstrip('\n')) 
                    except:
                        print "warning: index %s_%s_idx not dropped %s, continuing ..." \
                              % (idx['tab'],idx['col'], str(sys.exc_value).rstrip('\n'))
                else:
                    print "Error: Only MySQL and Postgres supported so far"
                    return -1

        if self.backend == self.PGSQL:
            self.db.set_isolation_level(1)   # go back to normal isolation level
        self.db.commit() # seems to clear up errors if there were any in postgres
        ptime = time() - stime
        print "prepare import took", ptime, "seconds"
    #end def prepareBulkImport

    def afterBulkImport(self):
        """Re-create any dropped indexes/foreign keys after bulk import"""
        stime = time()
        if self.backend == self.PGSQL:
            self.db.set_isolation_level(0)   # allow table/index operations to work
        for fk in self.foreignKeys[self.backend]:
            if fk['drop'] == 1:
                if self.backend == self.MYSQL_INNODB:
                    self.cursor.execute("SELECT constraint_name " +
                                       "FROM information_schema.KEY_COLUMN_USAGE " +
                                       #"WHERE REFERENCED_TABLE_SCHEMA = 'fpdb'
                                       "WHERE 1=1 " +
                                       "AND table_name = %s AND column_name = %s " + 
                                       "AND referenced_table_name = %s " +
                                       "AND referenced_column_name = %s ",
                                       (fk['fktab'], fk['fkcol'], fk['rtab'], fk['rcol']) )
                    cons = self.cursor.fetchone()
                    print "afterbulk: cons=", cons
                    if cons:
                        pass
                    else:
                        print "creating fk ", fk['fktab'], fk['fkcol'], "->", fk['rtab'], fk['rcol']
                        try:
                            self.cursor.execute("alter table " + fk['fktab'] + " add foreign key (" 
                                               + fk['fkcol'] + ") references " + fk['rtab'] + "(" 
                                               + fk['rcol'] + ")")
                        except:
                            pass
                elif self.backend == self.PGSQL:
                    print "creating fk ", fk['fktab'], fk['fkcol'], "->", fk['rtab'], fk['rcol']
                    try:
                        self.cursor.execute("alter table " + fk['fktab'] + " add constraint "
                                           + fk['fktab'] + '_' + fk['fkcol'] + '_fkey'
                                           + " foreign key (" + fk['fkcol']
                                           + ") references " + fk['rtab'] + "(" + fk['rcol'] + ")")
                    except:
                        pass
                else:
                    print "Only MySQL and Postgres supported so far"
                    return -1
        
        for idx in self.indexes[self.backend]:
            if idx['drop'] == 1:
                if self.backend == self.MYSQL_INNODB:
                    print "creating mysql index ", idx['tab'], idx['col']
                    try:
                        self.cursor.execute( "alter table %s add index %s(%s)"
                                          , (idx['tab'],idx['col'],idx['col']) )
                    except:
                        pass
                elif self.backend == self.PGSQL:
    #                pass
                    # mod to use tab_col for index name?
                    print "creating pg index ", idx['tab'], idx['col']
                    try:
                        print "create index %s_%s_idx on %s(%s)" % (idx['tab'], idx['col'], idx['tab'], idx['col'])
                        self.cursor.execute( "create index %s_%s_idx on %s(%s)"
                                          % (idx['tab'], idx['col'], idx['tab'], idx['col']) )
                    except:
                        print "   ERROR! :-("
                        pass
                else:
                    print "Only MySQL and Postgres supported so far"
                    return -1

        if self.backend == self.PGSQL:
            self.db.set_isolation_level(1)   # go back to normal isolation level
        self.db.commit()   # seems to clear up errors if there were any in postgres
        atime = time() - stime
        print "after import took", atime, "seconds"
    #end def afterBulkImport

    def createAllIndexes(self):
        """Create new indexes"""
        if self.backend == self.PGSQL:
            self.db.set_isolation_level(0)   # allow table/index operations to work
        for idx in self.indexes[self.backend]:
            if self.backend == self.MYSQL_INNODB:
                print "creating mysql index ", idx['tab'], idx['col']
                try:
                    self.cursor.execute( "alter table %s add index %s(%s)"
                                      , (idx['tab'],idx['col'],idx['col']) )
                except:
                    pass
            elif self.backend == self.PGSQL:
                # mod to use tab_col for index name?
                print "creating pg index ", idx['tab'], idx['col']
                try:
                    print "create index %s_%s_idx on %s(%s)" % (idx['tab'], idx['col'], idx['tab'], idx['col'])
                    self.cursor.execute( "create index %s_%s_idx on %s(%s)"
                                      % (idx['tab'], idx['col'], idx['tab'], idx['col']) )
                except:
                    print "   ERROR! :-("
                    pass
            else:
                print "Only MySQL and Postgres supported so far"
                return -1
        if self.backend == self.PGSQL:
            self.db.set_isolation_level(1)   # go back to normal isolation level
    #end def createAllIndexes

    def dropAllIndexes(self):
        """Drop all standalone indexes (i.e. not including primary keys or foreign keys)
           using list of indexes in indexes data structure"""
        # maybe upgrade to use data dictionary?? (but take care to exclude PK and FK)
        if self.backend == self.PGSQL:
            self.db.set_isolation_level(0)   # allow table/index operations to work
        for idx in self.indexes[self.backend]:
            if self.backend == self.MYSQL_INNODB:
                print "dropping mysql index ", idx['tab'], idx['col']
                try:
                    self.cursor.execute( "alter table %s drop index %s"
                                      , (idx['tab'],idx['col']) )
                except:
                    pass
            elif self.backend == self.PGSQL:
                print "dropping pg index ", idx['tab'], idx['col']
                # mod to use tab_col for index name?
                try:
                    self.cursor.execute( "drop index %s_%s_idx"
                                      % (idx['tab'],idx['col']) )
                except:
                    pass
            else:
                print "Only MySQL and Postgres supported so far"
                return -1
        if self.backend == self.PGSQL:
            self.db.set_isolation_level(1)   # go back to normal isolation level
    #end def dropAllIndexes

    def analyzeDB(self):
        """Do whatever the DB can offer to update index/table statistics"""
        stime = time()
        if self.backend == self.PGSQL:
            self.db.set_isolation_level(0)   # allow vacuum to work
            try:
                self.cursor.execute("vacuum analyze")
            except:
                print "Error during vacuum"
            self.db.set_isolation_level(1)   # go back to normal isolation level
        self.db.commit()
        atime = time() - stime
        print "analyze took", atime, "seconds"
    #end def analyzeDB

    # Currently uses an exclusive lock on the Players table as a global lock 
    # ( Changed because Hands is used in Database.init() )
    # Return values are Unix style, 0 for success, positive integers for errors
    # 1 = generic error
    # 2 = players table does not exist (error message is suppressed)
    def get_global_lock(self):
        if self.backend == self.MYSQL_INNODB:
            try:
                self.cursor.execute( "lock tables Players write" )
            except:
                # Table 'fpdb.players' doesn't exist
                if str(sys.exc_value).find(".Players' doesn't exist") >= 0:
                    return(2)
                print "Error! failed to obtain global lock. Close all programs accessing " \
                      + "database (including fpdb) and try again (%s)." \
                      % ( str(sys.exc_value).rstrip('\n'), )
                return(1)
        elif self.backend == self.PGSQL:
            try:
                self.cursor.execute( "lock table Players in exclusive mode nowait" )
                #print "... after lock table, status =", self.cursor.statusmessage
            except:
                # relation "players" does not exist
                if str(sys.exc_value).find('relation "players" does not exist') >= 0:
                    return(2)
                print "Error! failed to obtain global lock. Close all programs accessing " \
                      + "database (including fpdb) and try again (%s)." \
                      % ( str(sys.exc_value).rstrip('\n'), )
                return(1)
        return(0)

    def getLastInsertId(self):
        if self.backend == self.MYSQL_INNODB:
            ret = self.db.insert_id()
            if ret < 1 or ret > 999999999:
                print "getLastInsertId(): problem fetching insert_id? ret=", ret
                ret = -1
        elif self.backend == self.PGSQL:
            # some options:
            # currval(hands_id_seq) - use name of implicit seq here
            # lastval() - still needs sequences set up?
            # insert ... returning  is useful syntax (but postgres specific?)
            # see rules (fancy trigger type things)
            self.cursor.execute ("SELECT lastval()")
            row = self.cursor.fetchone()
            if not row:
                print "getLastInsertId(%s): problem fetching lastval? row=" % seq, row
                ret = -1
            else:
                ret = row[0]
        elif self.backend == self.SQLITE:
            # don't know how to do this in sqlite
            print "getLastInsertId(): not coded for sqlite yet"
            ret = -1
        else:
            print "getLastInsertId(): unknown backend ", self.backend
            ret = -1
        return ret

    def storeHand(self, p):
        #stores into table hands:
        self.cursor.execute ("""INSERT INTO Hands 
             (siteHandNo, gametypeId, handStart, seats, tableName, importTime, maxSeats
              ,boardcard1, boardcard2, boardcard3, boardcard4, boardcard5
              ,playersVpi, playersAtStreet1, playersAtStreet2
              ,playersAtStreet3, playersAtStreet4, playersAtShowdown
              ,street0Raises, street1Raises, street2Raises
              ,street3Raises, street4Raises, street1Pot
              ,street2Pot, street3Pot, street4Pot
              ,showdownPot
             ) 
             VALUES 
              (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
             ,(p['siteHandNo'], gametype_id, p['handStart'], len(names), p['tableName'], datetime.datetime.today(), p['maxSeats']
               ,p['boardcard1'], ['boardcard2'], p['boardcard3'], ['boardcard4'], ['boardcard5'] 
               ,hudCache['playersVpi'], hudCache['playersAtStreet1'], hudCache['playersAtStreet2']
               ,hudCache['playersAtStreet3'], hudCache['playersAtStreet4'], hudCache['playersAtShowdown']
               ,hudCache['street0Raises'], hudCache['street1Raises'], hudCache['street2Raises']
               ,hudCache['street3Raises'], hudCache['street4Raises'], hudCache['street1Pot']
               ,hudCache['street2Pot'], hudCache['street3Pot'], hudCache['street4Pot']
               ,hudCache['showdownPot']
              )
             )
        #return getLastInsertId(backend, conn, cursor)
#end class fpdb_db
