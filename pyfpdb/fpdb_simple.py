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
 
#This file contains simple functions for fpdb
 
import datetime
import time
import re
 
PS  = 1
FTP = 2

# TODO: these constants are also used in fpdb_save_to_db and others, is there a way to do like C #define, and #include ?
MYSQL_INNODB    = 2
PGSQL           = 3
SQLITE          = 4

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
          , [ # indexes for mysql (list index 2)
              {'tab':'Players',  'col':'name',          'drop':0}
            , {'tab':'Hands',    'col':'siteHandNo',    'drop':0}
            , {'tab':'Tourneys', 'col':'siteTourneyNo', 'drop':0}
            ]
          , [ # indexes for postgres (list index 3)
              {'tab':'Boardcards',      'col':'handId',            'drop':0}
            , {'tab':'Gametypes',       'col':'siteId',            'drop':0}
            , {'tab':'Hands',           'col':'gametypeId',        'drop':1}
            , {'tab':'Hands',           'col':'siteHandNo',        'drop':0}
            , {'tab':'HandsActions',    'col':'handplayerId',      'drop':0}
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

foreignKeys = [
                [ ] # no db with index 0
              , [ ] # no db with index 1
              , [ # foreign keys for mysql
                  {'fktab':'Hands',        'fkcol':'gametypeId',    'rtab':'Gametypes',     'rcol':'id', 'drop':1}
                , {'fktab':'HandsPlayers', 'fkcol':'handId',        'rtab':'Hands',         'rcol':'id', 'drop':1}
                , {'fktab':'HandsPlayers', 'fkcol':'playerId',      'rtab':'Players',       'rcol':'id', 'drop':1}
                , {'fktab':'HandsActions', 'fkcol':'handPlayerId',  'rtab':'HandsPlayers',  'rcol':'id', 'drop':1}
                , {'fktab':'HudCache',     'fkcol':'gametypeId',    'rtab':'Gametypes',     'rcol':'id', 'drop':1}
                , {'fktab':'HudCache',     'fkcol':'playerId',      'rtab':'Players',       'rcol':'id', 'drop':0}
                , {'fktab':'HudCache',     'fkcol':'tourneyTypeId', 'rtab':'TourneyTypes',  'rcol':'id', 'drop':1}
                ]
              , [ # foreign keys for postgres
                  {'fktab':'Hands',        'fkcol':'gametypeId',    'rtab':'Gametypes',     'rcol':'id', 'drop':1}
                , {'fktab':'HandsPlayers', 'fkcol':'handId',        'rtab':'Hands',         'rcol':'id', 'drop':1}
                , {'fktab':'HandsPlayers', 'fkcol':'playerId',      'rtab':'Players',       'rcol':'id', 'drop':1}
                , {'fktab':'HandsActions', 'fkcol':'handPlayerId',  'rtab':'HandsPlayers',  'rcol':'id', 'drop':1}
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

def prepareBulkImport(fdb):
    """Drop some indexes/foreign keys to prepare for bulk import. 
       Currently keeping the standalone indexes as needed to import quickly"""
    # fdb is a fpdb_db object including backend, db, cursor, sql variables
    if fdb.backend == PGSQL:
        fdb.db.set_isolation_level(0)   # allow table/index operations to work
    for fk in foreignKeys[fdb.backend]:
        if fk['drop'] == 1:
            if fdb.backend == MYSQL_INNODB:
                fdb.cursor.execute("SELECT constraint_name " +
                                   "FROM information_schema.KEY_COLUMN_USAGE " +
                                   #"WHERE REFERENCED_TABLE_SCHEMA = 'fpdb'
                                   "WHERE 1=1 " +
                                   "AND table_name = %s AND column_name = %s " + 
                                   "AND referenced_table_name = %s " +
                                   "AND referenced_column_name = %s ",
                                   (fk['fktab'], fk['fkcol'], fk['rtab'], fk['rcol']) )
                cons = fdb.cursor.fetchone()
                print "preparebulk: cons=", cons
                if cons:
                    print "dropping mysql fk", cons[0], fk['fktab'], fk['fkcol']
                    try:
                        fdb.cursor.execute("alter table " + fk['fktab'] + " drop foreign key " + cons[0])
                    except:
                        pass
            elif fdb.backend == PGSQL:
#    DON'T FORGET TO RECREATE THEM!!
                #print "dropping pg fk", fk['fktab'], fk['fkcol']
                try:
                    fdb.cursor.execute("alter table " + fk['fktab'] + " drop constraint " 
                                       + fk['fktab'] + '_' + fk['fkcol'] + '_fkey')
		    print "dropped pg fk pg fk %s_%s_fkey" % (fk['fktab'], fk['fkcol'])
                except:
                    print "! failed drop pg fk %s_%s_fkey" % (fk['fktab'], fk['fkcol'])
            else:
                print "Only MySQL and Postgres supported so far"
                return -1
    
    for idx in indexes[fdb.backend]:
        if idx['drop'] == 1:
            if fdb.backend == MYSQL_INNODB:
                print "dropping mysql index ", idx['tab'], idx['col']
                try:
                    fdb.cursor.execute( "alter table %s drop index %s", (idx['tab'],idx['col']) )
                except:
                    pass
            elif fdb.backend == PGSQL:
#    DON'T FORGET TO RECREATE THEM!!
                #print "Index dropping disabled for postgresql."
                #print "dropping pg index ", idx['tab'], idx['col']
                # mod to use tab_col for index name?
                try:
                    fdb.cursor.execute( "drop index %s_%s_idx" % (idx['tab'],idx['col']) )
		    print "drop index %s_%s_idx" % (idx['tab'],idx['col']) 
                    #print "dropped  pg index ", idx['tab'], idx['col']
                except:
		    print "! failed drop index %s_%s_idx" % (idx['tab'],idx['col']) 
            else:
                print "Only MySQL and Postgres supported so far"
                return -1

    if fdb.backend == PGSQL:
        fdb.db.set_isolation_level(1)   # go back to normal isolation level
    fdb.db.commit() # seems to clear up errors if there were any in postgres
#end def prepareBulkImport

def afterBulkImport(fdb):
    """Re-create any dropped indexes/foreign keys after bulk import"""
    # fdb is a fpdb_db object including backend, db, cursor, sql variables
    if fdb.backend == PGSQL:
        fdb.db.set_isolation_level(0)   # allow table/index operations to work
    for fk in foreignKeys[fdb.backend]:
        if fk['drop'] == 1:
            if fdb.backend == MYSQL_INNODB:
                fdb.cursor.execute("SELECT constraint_name " +
                                   "FROM information_schema.KEY_COLUMN_USAGE " +
                                   #"WHERE REFERENCED_TABLE_SCHEMA = 'fpdb'
                                   "WHERE 1=1 " +
                                   "AND table_name = %s AND column_name = %s " + 
                                   "AND referenced_table_name = %s " +
                                   "AND referenced_column_name = %s ",
                                   (fk['fktab'], fk['fkcol'], fk['rtab'], fk['rcol']) )
                cons = fdb.cursor.fetchone()
                print "afterbulk: cons=", cons
                if cons:
                    pass
                else:
                    print "creating fk ", fk['fktab'], fk['fkcol'], "->", fk['rtab'], fk['rcol']
                    try:
                        fdb.cursor.execute("alter table " + fk['fktab'] + " add foreign key (" 
                                           + fk['fkcol'] + ") references " + fk['rtab'] + "(" 
                                           + fk['rcol'] + ")")
                    except:
                        pass
            elif fdb.backend == PGSQL:
                print "creating fk ", fk['fktab'], fk['fkcol'], "->", fk['rtab'], fk['rcol']
                try:
                    fdb.cursor.execute("alter table " + fk['fktab'] + " add constraint "
                                       + fk['fktab'] + '_' + fk['fkcol'] + '_fkey'
                                       + " foreign key (" + fk['fkcol']
                                       + ") references " + fk['rtab'] + "(" + fk['rcol'] + ")")
                except:
                    pass
            else:
                print "Only MySQL and Postgres supported so far"
                return -1
    
    for idx in indexes[fdb.backend]:
        if idx['drop'] == 1:
            if fdb.backend == MYSQL_INNODB:
                print "creating mysql index ", idx['tab'], idx['col']
                try:
                    fdb.cursor.execute( "alter table %s add index %s(%s)"
                                      , (idx['tab'],idx['col'],idx['col']) )
                except:
                    pass
            elif fdb.backend == PGSQL:
#                pass
                # mod to use tab_col for index name?
                print "creating pg index ", idx['tab'], idx['col']
                try:
                    print "create index %s_%s_idx on %s(%s)" % (idx['tab'], idx['col'], idx['tab'], idx['col'])
                    fdb.cursor.execute( "create index %s_%s_idx on %s(%s)"
                                      % (idx['tab'], idx['col'], idx['tab'], idx['col']) )
                except:
                    print "   ERROR! :-("
                    pass
            else:
                print "Only MySQL and Postgres supported so far"
                return -1

    if fdb.backend == PGSQL:
        fdb.db.set_isolation_level(1)   # go back to normal isolation level
    fdb.db.commit()   # seems to clear up errors if there were any in postgres
#end def afterBulkImport

def createAllIndexes(fdb):
    """Create new indexes"""
    if fdb.backend == PGSQL:
        fdb.db.set_isolation_level(0)   # allow table/index operations to work
    for idx in indexes[fdb.backend]:
        if fdb.backend == MYSQL_INNODB:
            print "creating mysql index ", idx['tab'], idx['col']
            try:
                fdb.cursor.execute( "alter table %s add index %s(%s)"
                                  , (idx['tab'],idx['col'],idx['col']) )
            except:
                pass
        elif fdb.backend == PGSQL:
            # mod to use tab_col for index name?
            print "creating pg index ", idx['tab'], idx['col']
            try:
                print "create index %s_%s_idx on %s(%s)" % (idx['tab'], idx['col'], idx['tab'], idx['col'])
                fdb.cursor.execute( "create index %s_%s_idx on %s(%s)"
                                  % (idx['tab'], idx['col'], idx['tab'], idx['col']) )
            except:
                print "   ERROR! :-("
                pass
        else:
            print "Only MySQL and Postgres supported so far"
            return -1
    if fdb.backend == PGSQL:
        fdb.db.set_isolation_level(1)   # go back to normal isolation level
#end def createAllIndexes

def dropAllIndexes(fdb):
    """Drop all standalone indexes (i.e. not including primary keys or foreign keys)
       using list of indexes in indexes data structure"""
    # maybe upgrade to use data dictionary?? (but take care to exclude PK and FK)
    if fdb.backend == PGSQL:
        fdb.db.set_isolation_level(0)   # allow table/index operations to work
    for idx in indexes[fdb.backend]:
        if fdb.backend == MYSQL_INNODB:
            print "dropping mysql index ", idx['tab'], idx['col']
            try:
                fdb.cursor.execute( "alter table %s drop index %s"
                                  , (idx['tab'],idx['col']) )
            except:
                pass
        elif fdb.backend == PGSQL:
            print "dropping pg index ", idx['tab'], idx['col']
            # mod to use tab_col for index name?
            try:
                fdb.cursor.execute( "drop index %s_%s_idx"
                                  % (idx['tab'],idx['col']) )
            except:
                pass
        else:
            print "Only MySQL and Postgres supported so far"
            return -1
    if fdb.backend == PGSQL:
        fdb.db.set_isolation_level(1)   # go back to normal isolation level
#end def dropAllIndexes

def analyzeDB(fdb):
    """Do whatever the DB can offer to update index/table statistics"""
    if fdb.backend == PGSQL:
        fdb.db.set_isolation_level(0)   # allow vacuum to work
        try:
            fdb.cursor.execute("vacuum analyze")
        except:
            print "Error during vacuum"
        fdb.db.set_isolation_level(1)   # go back to normal isolation level
#end def analyzeDB

class DuplicateError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
 
class FpdbError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
    
# gets value for last auto-increment key generated
# returns -1 if a problem occurs
def getLastInsertId(backend, conn, cursor):
    if backend == MYSQL_INNODB:
        ret = conn.insert_id()
        if ret < 1 or ret > 999999999:
            print "getLastInsertId(): problem fetching insert_id? ret=", ret
            ret = -1
    elif backend == PGSQL:
        # some options:
        # currval(hands_id_seq) - use name of implicit seq here
        # lastval() - still needs sequences set up?
        # insert ... returning  is useful syntax (but postgres specific?)
        # see rules (fancy trigger type things)
        cursor.execute ("SELECT lastval()")
        row = cursor.fetchone()
        if not row:
            print "getLastInsertId(%s): problem fetching lastval? row=" % seq, row
            ret = -1
        else:
            ret = row[0]
    elif backend == SQLITE:
        # don't know how to do this in sqlite
        print "getLastInsertId(): not coded for sqlite yet"
        ret = -1
    else:
        print "getLastInsertId(): unknown backend ", backend
        ret = -1
    return ret
#end def getLastInsertId
 
#returns an array of the total money paid. intending to add rebuys/addons here
def calcPayin(count, buyin, fee):
    result=[]
    for i in xrange(count):
        result.append (buyin+fee)
    return result
#end def calcPayin

def checkPositions(positions):
    """ verify positions are valid """
    for p in positions:
        if not (p == "B" or p == "S" or (p >= 0 and p <= 9)):
            raise FpdbError("invalid position '" + p + "' found in checkPositions")
 
    ### RHH modified to allow for "position 9" here (pos==9 is when you're a dead hand before the BB
    ### eric - position 8 could be valid - if only one blind is posted, but there's still 10 people, ie a sitout is present, and the small is dead...
 
#classifies each line for further processing in later code. Manipulates the passed arrays.
def classifyLines(hand, category, lineTypes, lineStreets):
    currentStreet = "predeal"
    done = False #set this to true once we reach the last relevant line (the summary, except rake, is all repeats)
    for i, line in enumerate(hand):
        if done:
            if "[" not in line or "mucked [" not in line:
                lineTypes.append("ignore")
            else:
                lineTypes.append("cards")
        elif line.startswith("Dealt to"):
            lineTypes.append("cards")
        elif i == 0:
            lineTypes.append("header")
        elif line.startswith("Table '"):
            lineTypes.append("table")            
        elif line.startswith("Seat ") and ( ("in chips" in line) or "($" in line):
            lineTypes.append("name")
        elif isActionLine(line):
            lineTypes.append("action")
            if " posts " in line or " posts the " in line:
                currentStreet="preflop"
        elif " antes " in line or " posts the ante " in line:
            lineTypes.append("ante")
        elif line.startswith("*** FLOP *** ["):
            lineTypes.append("cards")
            currentStreet="flop"
        elif line.startswith("*** TURN *** ["):
            lineTypes.append("cards")
            currentStreet="turn"
        elif line.startswith("*** RIVER *** ["):            
            lineTypes.append("cards")
            currentStreet="river"
        elif line.startswith("*** 3"):
            lineTypes.append("ignore")
            currentStreet=0
        elif line.startswith("*** 4"):
            lineTypes.append("ignore")
            currentStreet=1
        elif line.startswith("*** 5"):
            lineTypes.append("ignore")
            currentStreet=2
        elif line.startswith("*** 6"):
            lineTypes.append("ignore")
            currentStreet=3
        elif line.startswith("*** 7") or line == "*** RIVER ***":
            lineTypes.append("ignore")
            currentStreet=4                
        elif isWinLine(line):
            lineTypes.append("win")
        elif line.startswith("Total pot ") and "Rake" in line:
            lineTypes.append("rake")
            done=True
        elif "*** SHOW DOWN ***" in line or "*** SUMMARY ***" in line:
            lineTypes.append("ignore")
            #print "in classifyLine, showdown or summary"
        elif " shows [" in line:
            lineTypes.append("cards")
        else:
            raise FpdbError("unrecognised linetype in:"+hand[i])
        lineStreets.append(currentStreet)
#end def classifyLines
 
def convert3B4B(site, category, limit_type, actionTypes, actionAmounts):
    """calculates the actual bet amounts in the given amount array and changes it accordingly."""
    for i in xrange(len(actionTypes)):
        for j in xrange(len(actionTypes[i])):
            bets=[]
            for k in xrange(len(actionTypes[i][j])):
                if (actionTypes[i][j][k]=="bet"):
                    bets.append((i,j,k))
                    if (len(bets)==2):
                        #print "len(bets) 2 or higher, need to correct it. bets:",bets,"len:",len(bets)
                        amount2=actionAmounts[bets[1][0]][bets[1][1]][bets[1][2]]
                        amount1=actionAmounts[bets[0][0]][bets[0][1]][bets[0][2]]
                        actionAmounts[bets[1][0]][bets[1][1]][bets[1][2]]=amount2-amount1
                    elif (len(bets)>2):
                        fail=True
                        #todo: run correction for below
                        if (site=="ps" and category=="holdem" and limit_type=="nl" and len(bets)==3):
                            fail=False
                        if (site=="ftp" and category=="omahahi" and limit_type=="pl" and len(bets)==3):
                            fail=False
                        
                        if fail:
                            print "len(bets)>2 in convert3B4B, i didnt think this is possible. i:",i,"j:",j,"k:",k
                            print "actionTypes:",actionTypes
                            raise FpdbError ("too many bets in convert3B4B")
    #print "actionAmounts postConvert",actionAmounts
#end def convert3B4B(actionTypes, actionAmounts)
 
#Corrects the bet amount if the player had to pay blinds
def convertBlindBet(actionTypes, actionAmounts):
    i=0#setting street to pre-flop
    for j in xrange(len(actionTypes[i])):#playerloop
        blinds=[]
        bets=[]
        for k in xrange(len(actionTypes[i][j])):
            if (actionTypes[i][j][k]=="blind"):
                blinds.append((i,j,k))
            
            if (len(blinds)>0 and actionTypes[i][j][k]=="bet"):
                bets.append((i,j,k))
                if (len(bets)==1):
                    blind_amount=actionAmounts[blinds[0][0]][blinds[0][1]][blinds[0][2]]
                    bet_amount=actionAmounts[bets[0][0]][bets[0][1]][bets[0][2]]
                    actionAmounts[bets[0][0]][bets[0][1]][bets[0][2]]=bet_amount-blind_amount
#end def convertBlindBet
 
#converts the strings in the given array to ints (changes the passed array, no returning). see table design for conversion details
#todo: make this use convertCardValuesBoard
def convertCardValues(arr):
    map(convertCardValuesBoard, arr)
#end def convertCardValues

card_map = { "2": 2, "3" : 3, "4" : 4, "5" : 5, "6" : 6, "7" : 7, "8" : 8, "9" : 9, "T" : 10, "J" : 11, "Q" : 12, "K" : 13, "A" : 14}
 
#converts the strings in the given array to ints (changes the passed array, no returning). see table design for conversion details
def convertCardValuesBoard(arr):
    for i in xrange(len(arr)):
        arr[i] = card_map[arr[i]]
#end def convertCardValuesBoard
 
#this creates the 2D/3D arrays. manipulates the passed arrays instead of returning.
def createArrays(category, seats, card_values, card_suits, antes, winnings, rakes, action_types, allIns, action_amounts, actionNos, actionTypeByNo):
    for i in xrange(seats):#create second dimension arrays
        card_values.append( [] )
        card_suits.append( [] )
        antes.append(0)
        winnings.append(0)
        rakes.append(0)
    
    streetCount = 4 if category == "holdem" or category == "omahahi" or category == "omahahilo" else 5
    
    for i in xrange(streetCount): #build the first dimension array, for streets
        action_types.append([])
        allIns.append([])
        action_amounts.append([])
        actionNos.append([])
        actionTypeByNo.append([])
        for j in xrange (seats): #second dimension arrays: players
            action_types[i].append([])
            allIns[i].append([])
            action_amounts[i].append([])
            actionNos[i].append([])
#    if (category=="holdem" or category=="omahahi" or category=="omahahilo"):
#        pass
    if category=="razz" or category=="studhi" or category=="studhilo":#need to fill card arrays.
        for i in xrange(seats):
            for j in xrange(7):
                card_values[i].append(0)
                card_suits[i].append("x")
#    else:
#        raise FpdbError("invalid category")
#end def createArrays
 
def fill_board_cards(board_values, board_suits):
#fill up the two board card arrays
    while (len(board_values)<5):
        board_values.append(0)
        board_suits.append("x")
#end def fill_board_cards
 
def fillCardArrays(player_count, base, category, card_values, card_suits):
    """fills up the two card arrays"""
    if (category=="holdem"):
        cardCount = 2
    elif (category=="omahahi" or category=="omahahilo"):
        cardCount = 4
    elif base=="stud":
        cardCount = 7
    else:
        raise fpdb_simple.FpdbError("invalid category:", category)
    
    for i in xrange(player_count):
        while (len(card_values[i]) < cardCount):
            card_values[i].append(0)
            card_suits[i].append("x")
#end def fillCardArrays
 
#filters out a player that folded before paying ante or blinds. This should be called
#before calling the actual hand parser. manipulates hand, no return.
def filterAnteBlindFold(site,hand):
    #todo: this'll only get rid of one ante folder, not multiple ones
    #todo: in tourneys this should not be removed but
    #print "start of filterAnteBlindFold"
    pre3rd=[]
    for i, line in enumerate(hand):
        if line.startswith("*** 3") or line.startswith("*** HOLE"):
            pre3rd = hand[0:i]
    
    foldeeName=None
    for line in pre3rd:
        if line.endswith("folds") or line.endswith("is sitting out") or line.endswith(" stands up"): #found ante fold or timeout
            pos = line.find(" folds")
            foldeeName = line[0:pos]
            if pos == -1 and " in chips)" not in line:
                pos = line.find(" is sitting out")
                foldeeName = line[0:pos]
            if pos == -1:
                pos = line.find(" stands up")
                foldeeName = line[0:pos]
            if pos == -1:
                pos1 = line.find(": ") + 2
                pos2 = line.find(" (")
                foldeeName = line[pos1:pos2]
 
    if foldeeName!=None:
        #print "filterAnteBlindFold, foldeeName:",foldeeName
        for i, line in enumerate(hand):
            if foldeeName in line:
                hand[i] = None
                
        hand = [line for line in hand if line]
#end def filterAnteFold

def stripEOLspaces(str):
    if str[-1] == ' ':
        str = str[:-1]
    if str[-1] == ' ':
        str = str[:-1]
    return str
 
#removes useless lines as well as trailing spaces
def filterCrap(site, hand, isTourney):
    #remove two trailing spaces at end of line
    hand = [stripEOLspaces(line) for line in hand]
            
    #print "hand after trailing space removal in filterCrap:",hand
    #general variable position word filter/string filter
    for i in xrange (len(hand)):
        if (hand[i].startswith("Board [")):
            hand[i] = False
        elif (hand[i].find(" out of hand ")!=-1):
            hand[i]=hand[i][:-56]
        elif (hand[i].find("($0 in chips)") != -1):
            hand[i] = False
        elif (hand[i]=="*** HOLE CARDS ***"):
            hand[i] = False
        elif (hand[i].endswith("has been disconnected")):
            hand[i] = False
        elif (hand[i].endswith("has requested TIME")):
            hand[i] = False
        elif (hand[i].endswith("has returned")):
            hand[i] = False
        elif (hand[i].endswith("will be allowed to play after the button")):
            hand[i] = False
        elif (hand[i].endswith("has timed out")):
            hand[i] = False
        elif (hand[i].endswith("has timed out while disconnected")):
            hand[i] = False
        elif (hand[i].endswith("has timed out while being disconnected")):
            hand[i] = False
        elif (hand[i].endswith("is connected")):
            hand[i] = False
        elif (hand[i].endswith("is disconnected")):
            hand[i] = False
        elif (hand[i].endswith(" is feeling angry")):
            hand[i] = False
        elif (hand[i].endswith(" is feeling confused")):
            hand[i] = False
        elif (hand[i].endswith(" is feeling happy")):
            hand[i] = False
        elif (hand[i].endswith(" is feeling normal")):
            hand[i] = False
        elif (hand[i].find(" is low with [")!=-1):
            hand[i] = False
        #elif (hand[i].find("-max Seat #")!=-1 and hand[i].find(" is the button")!=-1):
        # toRemove.append(hand[i])
        elif (hand[i].endswith(" mucks")):
            hand[i] = False
        elif (hand[i].endswith(": mucks hand")):
            hand[i] = False
        elif (hand[i]=="No low hand qualified"):
            hand[i] = False
        elif (hand[i]=="Pair on board - a double bet is allowed"):
            hand[i] = False
        elif (hand[i].find(" shows ")!=-1 and hand[i].find("[")==-1):
            hand[i] = False
        #elif (hand[i].startswith("Table '") and hand[i].endswith("-max")):
        # toRemove.append(hand[i])
        elif (hand[i].startswith("The button is in seat #")):
            hand[i] = False
        #above is alphabetic, reorder below if bored
        elif (hand[i].startswith("Time has expired")):
            hand[i] = False
        elif (hand[i].endswith("has reconnected")):
            hand[i] = False
        elif (hand[i].endswith("seconds left to act")):
            hand[i] = False
        elif (hand[i].endswith("seconds to reconnect")):
            hand[i] = False
        elif (hand[i].endswith("was removed from the table for failing to post")):
            hand[i] = False
        elif (hand[i].find("joins the table at seat ")!=-1):
            hand[i] = False
        elif (hand[i].endswith(" sits down")):
            hand[i] = False
        elif (hand[i].endswith("leaves the table")):
            hand[i] = False
        elif (hand[i].endswith(" stands up")):
            hand[i] = False
        elif (hand[i].find("is high with ")!=-1):
            hand[i] = False
        elif (hand[i].endswith("doesn't show hand")):
            hand[i] = False
        elif (hand[i].endswith("is being treated as all-in")):
            hand[i] = False
        elif (hand[i].find(" adds $")!=-1):
            hand[i] = False
        elif (hand[i]=="Betting is capped"):
            hand[i] = False
        #site specific variable position filter
        elif (hand[i].find(" said, \"")!=-1):
            hand[i] = False
        elif (hand[i].find(": ")!=-1 and site=="ftp" and hand[i].find("Seat ")==-1 and hand[i].find(": Table")==-1): #filter ftp chat
            hand[i] = False
        if isTourney and not hand[i] == False:
            if (hand[i].endswith(" is sitting out") and (not hand[i].startswith("Seat "))):
                hand[i] = False
        elif hand[i]:
            if (hand[i].endswith(": sits out")):
                hand[i] = False
            elif (hand[i].endswith(" is sitting out")):
                hand[i] = False

    hand = [line for line in hand if line]  # python docs say this is identical to filter(None, list)
        
    #print "done with filterCrap, hand:", hand
    return hand
#end filterCrap
 
#takes a poker float (including , for thousand seperator and converts it to an int
def float2int (string):
    pos=string.find(",")
    if (pos!=-1): #remove , the thousand seperator
        string = "%s%s" % (string[0:pos], string[pos+1:])
       
    pos=string.find(".")
    if (pos!=-1): #remove decimal point
        string = "%s%s" % (string[0:pos], string[pos+1:])
    
    result = int(string)
    if pos == -1: #no decimal point - was in full dollars - need to multiply with 100
        result*=100
    return result
#end def float2int

ActionLines = ( "calls $", ": calls ", "brings in for", "completes it to", "posts small blind",
                "posts the small blind", "posts big blind", "posts the big blind",
                "posts small & big blinds", "posts $", "posts a dead", "bets $",
                ": bets ", "raises")
 
#returns boolean whether the passed line is an action line
def isActionLine(line):
    if (line.endswith("folds")):
        return True
    elif (line.endswith("checks")):
        return True
    elif (line.startswith("Uncalled bet")):
        return True
    
    return len( [ x for x in ActionLines if x in line]) > 0
#        ret = any(True for searchstr in ActionLines if searchstr in line)
#        ret = len( [ x for x in ActionLines if line.find(x) > -1] ) > 0
#        ret = any(searchstr in line for searchstr in ActionLines)
#end def isActionLine
 
#returns whether this is a duplicate
def isAlreadyInDB(cursor, gametypeID, siteHandNo):
    #print "isAlreadyInDB gtid,shand:",gametypeID, siteHandNo
    cursor.execute ("SELECT id FROM Hands WHERE gametypeId=%s AND siteHandNo=%s", (gametypeID, siteHandNo))
    result=cursor.fetchall()
    if (len(result)>=1):
        raise DuplicateError ("dupl")
#end isAlreadyInDB
 
def isRebuyOrAddon(topline):
    """isRebuyOrAddon not implemented yet"""
    return False
#end def isRebuyOrAddon
 
#returns whether the passed topline indicates a tournament or not
def isTourney(topline):
    return "Tournament" in topline
#end def isTourney
 
WinLines = ( "wins the pot", "ties for the ", "wins side pot", "wins the low main pot", "wins the high main pot",
             "wins the high pot", "wins the high side pot", "wins the main pot", "wins the side pot", "collected" )
#returns boolean whether the passed line is a win line
def isWinLine(line):
    return len( [ x for x in WinLines if x in line ] ) > 0
#end def isWinLine
 
#returns the amount of cash/chips put into the put in the given action line
def parseActionAmount(line, atype, site, isTourney):
    #if (line.endswith(" and is all-in")):
    # line=line[:-14]
    #elif (line.endswith(", and is all in")):
    # line=line[:-15]
    
    if line.endswith(", and is capped"):#ideally we should recognise this as an all-in if category is capXl
        line=line[:-15]
    if line.endswith(" and is capped"):
        line=line[:-14]
 
    if atype == "fold" or atype == "check":
        amount = 0
    elif atype == "unbet":
        if site == "ftp":
            pos1 = line.find("$") + 1
            pos2 = line.find(" returned to")
            amount = float2int(line[pos1:pos2])
        elif site == "ps":
            pos1 = line.find("$") + 1
            if pos1 == 0:
                pos1 = line.find("(") + 1
            pos2 = line.find(")")
            amount = float2int(line[pos1:pos2])
    elif atype == "bet" and site == "ps" and line.find(": raises $")!=-1 and line.find("to $")!=-1:
        pos = line.find("to $")+4
        amount = float2int(line[pos:])
    else:
        if not isTourney:
            pos = line.rfind("$")+1
            #print "parseActionAmount, line:", line, "line[pos:]:", line[pos:]
            amount = float2int(line[pos:])
        else:
            #print "line:"+line+"EOL"
            pos = line.rfind(" ")+1
            #print "pos:",pos
            #print "pos of 20:", line.find("20")
            amount = int(line[pos:])
    
    if atype == "unbet":
        amount *= -1
    return amount
#end def parseActionAmount
 
#doesnt return anything, simply changes the passed arrays action_types and
# action_amounts. For stud this expects numeric streets (3-7), for
# holdem/omaha it expects predeal, preflop, flop, turn or river
def parseActionLine(site, base, isTourney, line, street, playerIDs, names, action_types, allIns, action_amounts, actionNos, actionTypeByNo):
    if street == "predeal" or street == "preflop":
        street = 0
    elif street == "flop":
        street = 1
    elif street == "turn":
        street = 2
    elif street == "river":
        street = 3
    
    nextActionNo = 0
    for player in xrange(len(actionNos[street])):
        for count in xrange(len(actionNos[street][player])):
            if actionNos[street][player][count]>=nextActionNo:
                nextActionNo=actionNos[street][player][count]+1
                
    (line, allIn) = goesAllInOnThisLine(line)
    atype = parseActionType(line)
    playerno = recognisePlayerNo(line, names, atype)
    amount = parseActionAmount(line, atype, site, isTourney)
    
    action_types[street][playerno].append(atype)
    allIns[street][playerno].append(allIn)
    action_amounts[street][playerno].append(amount)
    actionNos[street][playerno].append(nextActionNo)
    tmp=(playerIDs[playerno], atype)
    actionTypeByNo[street].append(tmp)
#end def parseActionLine
 
def goesAllInOnThisLine(line):
    """returns whether the player went all-in on this line and removes the all-in text from the line."""
    isAllIn = False
    if (line.endswith(" and is all-in")):
        line = line[:-14]
        isAllIn = True
    elif (line.endswith(", and is all in")):
        line = line[:-15]
        isAllIn = True
    return (line, isAllIn)
#end def goesAllInOnThisLine
 
#returns the action type code (see table design) of the given action line
def parseActionType(line):
    if (line.startswith("Uncalled bet")):
        return "unbet"
    elif (line.endswith("folds")):
        return "fold"
    elif (line.endswith("checks")):
        return "check"
    elif (line.find("calls")!=-1):
        return "call"
    elif (line.find("brings in for")!=-1):
        return "blind"
    elif (line.find("completes it to")!=-1):
        return "bet"
       #todo: what if someone completes instead of bringing in?
    elif (line.find(" posts $")!=-1):
        return "blind"
    elif (line.find(" posts a dead ")!=-1):
        return "blind"
    elif (line.find(": posts small blind ")!=-1):
        return "blind"
    elif (line.find(" posts the small blind of $")!=-1):
        return "blind"
    elif (line.find(": posts big blind ")!=-1):
        return "blind"
    elif (line.find(" posts the big blind of $")!=-1):
        return "blind"
    elif (line.find(": posts small & big blinds $")!=-1):
        return "blind"
    #todo: seperately record voluntary blind payments made to join table out of turn
    elif (line.find("bets")!=-1):
        return "bet"
    elif (line.find("raises")!=-1):
        return "bet"
    else:
        raise FpdbError ("failed to recognise actiontype in parseActionLine in: "+line)
#end def parseActionType
 
#parses the ante out of the given line and checks which player paid it, updates antes accordingly.
def parseAnteLine(line, site, isTourney, names, antes):
    for i, name in enumerate(names):
        if line.startswith(name.encode("latin-1")):
            pos = line.rfind("$") + 1
            if not isTourney:
                antes[i] += float2int(line[pos:])
            else:
                if "all-in" not in line:
                    pos = line.rfind(" ") + 1
                    antes[i] += int(line[pos:])
                else:
                    pos1 = line.rfind("ante") + 5
                    pos2 = line.find(" ", pos1)
                    antes[i] += int(line[pos1:pos2])
        #print "parseAnteLine line: ", line, "antes[i]", antes[i], "antes", antes
#end def parseAntes
 
#returns the buyin of a tourney in cents
def parseBuyin(topline):
    pos1 = topline.find("$")+1
    pos2 = topline.find("+")
    return float2int(topline[pos1:pos2])
#end def parseBuyin
 
#parses a card line and changes the passed arrays accordingly
#todo: reorganise this messy method
def parseCardLine(site, category, street, line, names, cardValues, cardSuits, boardValues, boardSuits):
    if line.startswith("Dealt to") or " shows [" in line or "mucked [" in line:
        playerNo = recognisePlayerNo(line, names, "card") #anything but unbet will be ok for that string
 
        pos = line.rfind("[")+1
        if category == "holdem":
            for i in (pos, pos+3):
                cardValues[playerNo].append(line[i:i+1])
                cardSuits[playerNo].append(line[i+1:i+2])
            if len(cardValues[playerNo]) !=2:
                if cardValues[playerNo][0]==cardValues[playerNo][2] and cardSuits[playerNo][1]==cardSuits[playerNo][3]: #two tests will do
                    cardValues[playerNo]=cardValues[playerNo][0:2]
                    cardSuits[playerNo]=cardSuits[playerNo][0:2]
                else:
                    print "line:",line,"cardValues[playerNo]:",cardValues[playerNo]
                    raise FpdbError("read too many/too few holecards in parseCardLine")
        elif category == "omahahi" or category == "omahahilo":
            for i in (pos, pos+3, pos+6, pos+9):
                cardValues[playerNo].append(line[i:i+1])
                cardSuits[playerNo].append(line[i+1:i+2])
            if (len(cardValues[playerNo])!=4):
                if cardValues[playerNo][0]==cardValues[playerNo][4] and cardSuits[playerNo][3]==cardSuits[playerNo][7]: #two tests will do
                    cardValues[playerNo]=cardValues[playerNo][0:4]
                    cardSuits[playerNo]=cardSuits[playerNo][0:4]
                else:
                    print "line:",line,"cardValues[playerNo]:",cardValues[playerNo]
                    raise FpdbError("read too many/too few holecards in parseCardLine")
        elif category=="razz" or category=="studhi" or category=="studhilo":
            if "shows" not in line and "mucked" not in line:
                #print "parseCardLine(in stud if), street:", street
                if line[pos+2]=="]": #-> not (hero and 3rd street)
                    cardValues[playerNo][street+2]=line[pos:pos+1]
                    cardSuits[playerNo][street+2]=line[pos+1:pos+2]
                else:
                    #print "hero card1:", line[pos:pos+2], "hero card2:", line[pos+3:pos+5], "hero card3:", line[pos+6:pos+8],
                    cardValues[playerNo][street]=line[pos:pos+1]
                    cardSuits[playerNo][street]=line[pos+1:pos+2]
                    cardValues[playerNo][street+1]=line[pos+3:pos+4]
                    cardSuits[playerNo][street+1]=line[pos+4:pos+5]
                    cardValues[playerNo][street+2]=line[pos+6:pos+7]
                    cardSuits[playerNo][street+2]=line[pos+7:pos+8]
            else:
                #print "parseCardLine(in stud else), street:", street
                cardValues[playerNo][0]=line[pos:pos+1]
                cardSuits[playerNo][0]=line[pos+1:pos+2]
                pos+=3
                cardValues[playerNo][1]=line[pos:pos+1]
                cardSuits[playerNo][1]=line[pos+1:pos+2]
                if street==4:
                    pos=pos=line.rfind("]")-2
                    cardValues[playerNo][6]=line[pos:pos+1]
                    cardSuits[playerNo][6]=line[pos+1:pos+2]
                    #print "cardValues:", cardValues
                    #print "cardSuits:", cardSuits
        else:
            print "line:",line,"street:",street
            raise FpdbError("invalid category")
        #print "end of parseCardLine/playercards, cardValues:",cardValues
    elif (line.startswith("*** FLOP ***")):
        pos=line.find("[")+1
        for i in (pos, pos+3, pos+6):
            boardValues.append(line[i:i+1])
            boardSuits.append(line[i+1:i+2])
        #print boardValues
    elif (line.startswith("*** TURN ***") or line.startswith("*** RIVER ***")):
        pos=line.find("[")+1
        pos=line.find("[", pos+1)+1
        boardValues.append(line[pos:pos+1])
        boardSuits.append(line[pos+1:pos+2])
        #print boardValues
    else:
        raise FpdbError ("unrecognised line:"+line)
#end def parseCardLine
 
def parseCashesAndSeatNos(lines, site):
    """parses the startCashes and seatNos of each player out of the given lines and returns them as a dictionary of two arrays"""
    cashes = []
    seatNos = []
    for i in xrange (len(lines)):
        pos2=lines[i].find(":")
        seatNos.append(int(lines[i][5:pos2]))
        
        pos1=lines[i].rfind("($")+2
        if pos1==1: #for tourneys - it's 1 instead of -1 due to adding 2 above
            pos1=lines[i].rfind("(")+1
        if (site=="ftp"):
            pos2=lines[i].rfind(")")
        elif (site=="ps"):
            pos2=lines[i].find(" in chips")
        cashes.append(float2int(lines[i][pos1:pos2]))
    return {'startCashes':cashes, 'seatNos':seatNos}
#end def parseCashesAndSeatNos
 
#returns the buyin of a tourney in cents
def parseFee(topline):
    pos1=topline.find("$")+1
    pos1=topline.find("$",pos1)+1
    pos2=topline.find(" ", pos1)
    return float2int(topline[pos1:pos2])
#end def parsefee
 
#returns a datetime object with the starttime indicated in the given topline
def parseHandStartTime(topline, site):
    #convert x:13:35 to 0x:13:35
    counter=0
    while (True):
        pos=topline.find(" "+str(counter)+":")
        if (pos!=-1):
            topline=topline[0:pos+1]+"0"+topline[pos+1:]
        counter+=1
        if counter==10: break
    
    isUTC=False
    if site=="ftp":
        # Full Tilt Sit'n'Go
        # Full Tilt Poker Game #10311865543: $1 + $0.25 Sit & Go (78057629), Table 1 - 25/50 - No Limit Hold'em - 0:07:45 ET - 2009/01/29
        # Cash Game:
        # Full Tilt Poker Game #9403951181: Table CR - tay - $0.05/$0.10 - No Limit Hold'em - 9:40:20 ET - 2008/12/09
        # Full Tilt Poker Game #9468383505: Table Bike (deep 6) - $0.05/$0.10 - No Limit Hold'em - 5:09:36 ET - 2008/12/13
        pos = topline.find(" ", len(topline)-26)+1
        tmp = topline[pos:]

        rexx = '(?P<HR>[0-9]+):(?P<MIN>[0-9]+):(?P<SEC>[0-9]+) ET [\- ]+(?P<YEAR>[0-9]{4})\/(?P<MON>[0-9]{2})\/(?P<DAY>[0-9]{2})'
        m = re.search(rexx,tmp)
        result = datetime.datetime(int(m.group('YEAR')), int(m.group('MON')), int(m.group('DAY')), int(m.group('HR')), int(m.group('MIN')), int(m.group('SEC')))
    elif site=="ps":
        if topline.find("UTC")!=-1:
            pos1 = topline.find("-")+2
            pos2 = topline.find("UTC")
            tmp=topline[pos1:pos2]
            isUTC=True
        else:
            tmp=topline
            #print "parsehandStartTime, tmp:", tmp
            pos = tmp.find("-")+2
            tmp = tmp[pos:]
        #Need to match either
        # 2008/09/07 06:23:14 ET or
        # 2008/08/17 - 01:14:43 (ET) or
        # 2008/11/12 9:33:31 CET [2008/11/12 3:33:31 ET]
        rexx = '(?P<YEAR>[0-9]{4})\/(?P<MON>[0-9]{2})\/(?P<DAY>[0-9]{2})[\- ]+(?P<HR>[0-9]+):(?P<MIN>[0-9]+):(?P<SEC>[0-9]+)'
        m = re.search(rexx,tmp)
        #print "year:", int(m.group('YEAR')), "month", int(m.group('MON')), "day", int(m.group('DAY')), "hour", int(m.group('HR')), "minute", int(m.group('MIN')), "second", int(m.group('SEC'))
        result = datetime.datetime(int(m.group('YEAR')), int(m.group('MON')), int(m.group('DAY')), int(m.group('HR')), int(m.group('MIN')), int(m.group('SEC')))
    else:
        raise FpdbError("invalid site in parseHandStartTime")
    
    if (site=="ftp" or site=="ps") and not isUTC: #these use US ET
        result+=datetime.timedelta(hours=5)
    
    return result
#end def parseHandStartTime
 
#parses the names out of the given lines and returns them as an array
def parseNames(lines):
    result = []
    for i in xrange (len(lines)):
        pos1=lines[i].find(":")+2
        pos2=lines[i].rfind("(")-1
        tmp=lines[i][pos1:pos2]
        #print "parseNames, tmp original:",tmp
        tmp=unicode(tmp,"latin-1")
        #print "parseNames, tmp after unicode latin-1 conversion:",tmp
        result.append(tmp)
    return result
#end def parseNames
 
def parsePositions(hand, names):
    positions = map(lambda x: -1, names)

    #find blinds
    sb,bb=-1,-1
    for i in xrange (len(hand)):
        if (sb==-1 and hand[i].find("small blind")!=-1 and hand[i].find("dead small blind")==-1):
            sb=hand[i]
            #print "sb:",sb
        if (bb==-1 and hand[i].find("big blind")!=-1 and hand[i].find("dead big blind")==-1):
            bb=hand[i]
            #print "bb:",bb

#identify blinds
#print "parsePositions before recognising sb/bb. names:",names
    sbExists=True
    if (sb!=-1):
        sb=recognisePlayerNo(sb, names, "bet")
    else:
        sbExists=False
    if (bb!=-1):
        bb=recognisePlayerNo(bb, names, "bet")
        
#	print "sb = ", sb, "bb = ", bb
    if bb == sb:
        sbExists = False
        sb = -1

    #write blinds into array
    if (sbExists):
        positions[sb]="S"
    positions[bb]="B"


    #fill up rest of array
    if (sbExists):
        arraypos=sb-1
    else:
        arraypos=bb-1
    distFromBtn=0
    while (arraypos>=0 and arraypos != bb):
        #print "parsePositions first while, arraypos:",arraypos,"positions:",positions
        positions[arraypos]=distFromBtn
        arraypos-=1
        distFromBtn+=1

    # eric - this takes into account dead seats between blinds
    if sbExists:
        i = bb - 1
        while positions[i] < 0 and i != sb:
            positions[i] = 9
            i -= 1
    ### RHH - Changed to set the null seats before BB to "9"			
    if sbExists:
        i = sb-1
    else:
        i = bb-1
    while positions[i] < 0:
        positions[i]=9
        i-=1

    arraypos=len(names)-1
    if (bb!=0 or (bb==0 and sbExists==False) or (bb == 1 and sb != arraypos) ):
        while (arraypos>bb and arraypos > sb):
            positions[arraypos]=distFromBtn
            arraypos-=1
            distFromBtn+=1

    for i in xrange (len(names)):
        if positions[i]==-1:
            print "parsePositions names:",names
            print "result:",positions
            raise FpdbError ("failed to read positions")
#	print str(positions), "\n"
    return positions
#end def parsePositions
 
#simply parses the rake amount and returns it as an int
def parseRake(line):
    pos=line.find("Rake")+6
    rake=float2int(line[pos:])
    return rake
#end def parseRake
 
def parseSiteHandNo(topline):
    """returns the hand no assigned by the poker site"""
    pos1=topline.find("#")+1
    pos2=topline.find(":")
    return topline[pos1:pos2]
#end def parseSiteHandNo
 
def parseTableLine(site, base, line):
    """returns a dictionary with maxSeats and tableName"""
    if site=="ps":
        pos1=line.find('\'')+1
        pos2=line.find('\'', pos1)
        #print "table:",line[pos1:pos2]
        pos3=pos2+2
        pos4=line.find("-max")
        #print "seats:",line[pos3:pos4]
        return {'maxSeats':int(line[pos3:pos4]), 'tableName':line[pos1:pos2]}
    elif site=="ftp":
        pos1=line.find("Table ")+6
        pos2=line.find("-")-1
        if base=="hold":
            maxSeats=9
        elif base=="stud":
            maxSeats=8
            
        if line.find("6 max")!=-1:
            maxSeats=6
        elif line.find("4 max")!=-1:
            maxSeats=4
        elif line.find("heads up")!=-1:
            maxSeats=2
            
        tableName = line[pos1:pos2]
        for pattern in [' \(6 max\)', ' \(heads up\)', ' \(deep\)',
                    ' \(deep hu\)', ' \(deep 6\)', ' \(2\)',
                    ' \(edu\)', ' \(edu, 6 max\)', ' \(6\)',
                    ' \(speed\)', 
                    ' no all-in', ' fast', ',', ' 50BB min', '\s+$']:
            tableName = re.sub(pattern, '', tableName)
        tableName = tableName.rstrip()            
        return {'maxSeats':maxSeats, 'tableName':tableName}
    else:
        raise FpdbError("invalid site ID")
#end def parseTableLine
 
#returns the hand no assigned by the poker site
def parseTourneyNo(topline):
    pos1=topline.find("Tournament #")+12
    pos2=topline.find(",", pos1)
    #print "parseTourneyNo pos1:",pos1," pos2:",pos2, " result:",topline[pos1:pos2]
    return topline[pos1:pos2]
#end def parseTourneyNo
 
#parses a win/collect line. manipulates the passed array winnings, no explicit return
def parseWinLine(line, site, names, winnings, isTourney):
    #print "parseWinLine: line:",line
    for i in xrange(len(names)):
        if (line.startswith(names[i].encode("latin-1"))): #found a winner
            if isTourney:
                pos1=line.rfind("collected ")+10
                if (site=="ftp"):
                    pos2=line.find(")", pos1)
                elif (site=="ps"):
                    pos2=line.find(" ", pos1)
                winnings[i]+=int(line[pos1:pos2])
            else:
                pos1=line.rfind("$")+1
                if (site=="ftp"):
                    pos2=line.find(")", pos1)
                elif (site=="ps"):
                    pos2=line.find(" ", pos1)
                winnings[i]+=float2int(line[pos1:pos2])
#end def parseWinLine
 
#returns the category (as per database) string for the given line
def recogniseCategory(line):
    if "Razz" in line:
        return "razz"
    elif "Hold'em" in line:
        return "holdem"
    elif "Omaha" in line:
        if "Hi/Lo" not in line and "H/L" not in line:
            return "omahahi"
        else:
            return "omahahilo"
    elif "Stud" in line:
        if "Hi/Lo" not in line and "H/L" not in line:
            return "studhi"
        else:
            return "studhilo"
    else:
        raise FpdbError("failed to recognise category, line:"+line)
#end def recogniseCategory
 
#returns the int for the gametype_id for the given line
def recogniseGametypeID(backend, db, cursor, topline, smallBlindLine, site_id, category, isTourney):#todo: this method is messy
    #if (topline.find("HORSE")!=-1):
    # raise FpdbError("recogniseGametypeID: HORSE is not yet supported.")
    
    #note: the below variable names small_bet and big_bet are misleading, in NL/PL they mean small/big blind
    if isTourney:
        type="tour"
        pos1=topline.find("(")+1
        if (topline[pos1]=="H" or topline[pos1]=="O" or topline[pos1]=="R" or topline[pos1]=="S" or topline[pos1+2]=="C"):
            pos1=topline.find("(", pos1)+1
        pos2=topline.find("/", pos1)
        small_bet=int(topline[pos1:pos2])
    else:
        type="ring"
        pos1=topline.find("$")+1
        pos2=topline.find("/$")
        small_bet=float2int(topline[pos1:pos2])
    
    pos1=pos2+2
    if isTourney:
        pos1-=1
    if (site_id==1): #ftp
        pos2=topline.find(" ", pos1)
    elif (site_id==2): #ps
        pos2=topline.find(")")
    
    if pos2<=pos1:
        pos2=topline.find(")", pos1)
    
    if isTourney:
        big_bet=int(topline[pos1:pos2])
    else:
        big_bet=float2int(topline[pos1:pos2])
    
    if (topline.find("No Limit")!=-1):
        limit_type="nl"
        if (topline.find("Cap No")!=-1):
            limit_type="cn"
    elif (topline.find("Pot Limit")!=-1):
        limit_type="pl"
        if (topline.find("Cap Pot")!=-1):
            limit_type="cp"
    else:
        limit_type="fl"
    
    #print "recogniseGametypeID small_bet/blind:",small_bet,"big bet/blind:", big_bet,"limit type:",limit_type
    if (limit_type=="fl"):
        cursor.execute ("SELECT id FROM Gametypes WHERE siteId=%s AND type=%s AND category=%s AND limitType=%s AND smallBet=%s AND bigBet=%s", (site_id, type, category, limit_type, small_bet, big_bet))
    else:
        cursor.execute ("SELECT id FROM Gametypes WHERE siteId=%s AND type=%s AND category=%s AND limitType=%s AND smallBlind=%s AND bigBlind=%s", (site_id, type, category, limit_type, small_bet, big_bet))
    result=cursor.fetchone()
    #print "recgt1 result=",result
    #ret=result[0]
    #print "recgt1 ret=",ret
    #print "tried SELECTing gametypes.id, result:",result
    
    try:
        len(result)
    except TypeError:
        if category=="holdem" or category=="omahahi" or category=="omahahilo":
            base="hold"
        else:
            base="stud"
        
        if category=="holdem" or category=="omahahi" or category=="studhi":
            hiLo='h'
        elif category=="razz":
            hiLo='l'
        else:
            hiLo='s'
        
        if (limit_type=="fl"):
            big_blind=small_bet
            if base=="hold":
                if smallBlindLine==topline:
                    raise FpdbError("invalid small blind line")
                elif isTourney:
                    pos=smallBlindLine.rfind(" ")+1
                    small_blind=int(smallBlindLine[pos:])
                else:
                    pos=smallBlindLine.rfind("$")+1
                    small_blind=float2int(smallBlindLine[pos:])
            else:
                small_blind=0
            cursor.execute( """INSERT INTO Gametypes(siteId, type, base, category, limitType
                                                    ,hiLo, smallBlind, bigBlind, smallBet, bigBet)
                               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                          , (site_id, type, base, category, limit_type, hiLo
                            ,small_blind, big_blind, small_bet, big_bet) )
            #cursor.execute ("SELECT id FROM Gametypes WHERE siteId=%s AND type=%s AND category=%s 
            #AND limitType=%s AND smallBet=%s AND bigBet=%s", (site_id, type, category, limit_type, small_bet, big_bet))
        else:
            cursor.execute( """INSERT INTO Gametypes(siteId, type, base, category, limitType
                                                    ,hiLo, smallBlind, bigBlind, smallBet, bigBet)
                               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                          , (site_id, type, base, category, limit_type
                            ,hiLo, small_bet, big_bet, 0, 0))#remember, for these bet means blind
            #cursor.execute ("SELECT id FROM Gametypes WHERE siteId=%s AND type=%s AND category=%s
            #AND limitType=%s AND smallBlind=%s AND bigBlind=%s", (site_id, type, category, limit_type, small_bet, big_bet))
 
        #result=(db.insert_id(),)
        result=(getLastInsertId(backend,db,cursor),)
    
    return result[0]
#end def recogniseGametypeID
 
def recogniseTourneyTypeId(cursor, siteId, buyin, fee, knockout, rebuyOrAddon):
    cursor.execute ("SELECT id FROM TourneyTypes WHERE siteId=%s AND buyin=%s AND fee=%s AND knockout=%s AND rebuyOrAddon=%s", (siteId, buyin, fee, knockout, rebuyOrAddon))
    result=cursor.fetchone()
    #print "tried SELECTing gametypes.id, result:",result
    
    try:
        len(result)
    except TypeError:#this means we need to create a new entry
        cursor.execute("""INSERT INTO TourneyTypes (siteId, buyin, fee, knockout, rebuyOrAddon) VALUES (%s, %s, %s, %s, %s)""", (siteId, buyin, fee, knockout, rebuyOrAddon))
        cursor.execute("SELECT id FROM TourneyTypes WHERE siteId=%s AND buyin=%s AND fee=%s AND knockout=%s AND rebuyOrAddon=%s", (siteId, buyin, fee, knockout, rebuyOrAddon))
        result=cursor.fetchone()
    return result[0]
#end def recogniseTourneyTypeId
 
#returns the SQL ids of the names given in an array
def recognisePlayerIDs(cursor, names, site_id):
    result = []
    for i in xrange(len(names)):
        cursor.execute ("SELECT id FROM Players WHERE name=%s", (names[i],))
        tmp=cursor.fetchall()
        if (len(tmp)==0): #new player
            cursor.execute ("INSERT INTO Players (name, siteId) VALUES (%s, %s)", (names[i], site_id))
            #print "Number of players rows inserted: %d" % cursor.rowcount
            cursor.execute ("SELECT id FROM Players WHERE name=%s", (names[i],))
            tmp=cursor.fetchall()
        #print "recognisePlayerIDs, names[i]:",names[i],"tmp:",tmp
        result.append(tmp[0][0])
    return result
#end def recognisePlayerIDs
 
#recognises the name in the given line and returns its array position in the given array
def recognisePlayerNo(line, names, atype):
    #print "recogniseplayerno, names:",names
    for i in xrange(len(names)):
        if (atype=="unbet"):
            if (line.endswith(names[i].encode("latin-1"))):
                return (i)
        elif (line.startswith("Dealt to ")):
            #print "recognisePlayerNo, card precut, line:",line
            tmp=line[9:]
            #print "recognisePlayerNo, card postcut, tmp:",tmp
            if (tmp.startswith(names[i].encode("latin-1"))):
                return (i)
        elif (line.startswith("Seat ")):
            if (line.startswith("Seat 10")):
                tmp=line[9:]
            else:
                tmp=line[8:]
            
            if (tmp.startswith(names[i].encode("latin-1"))):
                return (i)
        else:
            if (line.startswith(names[i].encode("latin-1"))):
                return (i)
    #if we're here we mustve failed
    raise FpdbError ("failed to recognise player in: "+line+" atype:"+atype)
#end def recognisePlayerNo
 
#returns the site abbreviation for the given site
def recogniseSite(line):
    if (line.startswith("Full Tilt Poker")):
        return "ftp"
    elif (line.startswith("PokerStars")):
        return "ps"
    else:
        raise FpdbError("failed to recognise site, line:"+line)
#end def recogniseSite
 
#returns the ID of the given site
def recogniseSiteID(cursor, site):
    if (site=="ftp"):
        return 1
        #cursor.execute("SELECT id FROM Sites WHERE name = ('Full Tilt Poker')")
    elif (site=="ps"):
        return 2
        #cursor.execute("SELECT id FROM Sites WHERE name = ('PokerStars')")
    else:
        raise FpdbError("invalid site in recogniseSiteID: "+site)
    return cursor.fetchall()[0][0]
#end def recogniseSiteID
 
#removes trailing \n from the given array
def removeTrailingEOL(arr):
    for i in xrange(len(arr)):
        if (arr[i].endswith("\n")):
            #print "arr[i] before removetrailingEOL:", arr[i]
            arr[i]=arr[i][:-1]
            #print "arr[i] after removetrailingEOL:", arr[i]
    return arr
#end def removeTrailingEOL
 
#splits the rake according to the proportion of pot won. manipulates the second passed array.
def splitRake(winnings, rakes, totalRake):
    winnercnt=0
    totalWin=0
    for i in xrange(len(winnings)):
        if winnings[i]!=0:
            winnercnt+=1
            totalWin+=winnings[i]
            firstWinner=i
    if winnercnt==1:
        rakes[firstWinner]=totalRake
    else:
        totalWin=float(totalWin)
        for i in xrange(len(winnings)):
            if winnings[i]!=0:
                winPortion=winnings[i]/totalWin
                rakes[i]=totalRake*winPortion
#end def splitRake
 
def storeActions(cursor, handsPlayersIds, actionTypes, allIns, actionAmounts, actionNos):
#stores into table hands_actions
    #print "start of storeActions, actionNos:",actionNos
    #print " action_amounts:",action_amounts
    for i in xrange(len(actionTypes)): #iterate through streets
        for j in xrange(len(actionTypes[i])): #iterate through names
            for k in xrange(len(actionTypes[i][j])): #iterate through individual actions of that player on that street
                cursor.execute ("INSERT INTO HandsActions (handPlayerId, street, actionNo, action, allIn, amount) VALUES (%s, %s, %s, %s, %s, %s)"
                               , (handsPlayersIds[j], i, actionNos[i][j][k], actionTypes[i][j][k], allIns[i][j][k], actionAmounts[i][j][k]))
#end def storeActions
 
def store_board_cards(cursor, hands_id, board_values, board_suits):
#stores into table board_cards
    cursor.execute ("""INSERT INTO BoardCards (handId, card1Value, card1Suit,
card2Value, card2Suit, card3Value, card3Suit, card4Value, card4Suit,
card5Value, card5Suit) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
    (hands_id, board_values[0], board_suits[0], board_values[1], board_suits[1],
    board_values[2], board_suits[2], board_values[3], board_suits[3],
    board_values[4], board_suits[4]))
#end def store_board_cards
 
def storeHands(backend, conn, cursor, site_hand_no, gametype_id
              ,hand_start_time, names, tableName, maxSeats):
#stores into table hands
    cursor.execute ("INSERT INTO Hands (siteHandNo, gametypeId, handStart, seats, tableName, importTime, maxSeats) VALUES (%s, %s, %s, %s, %s, %s, %s)", (site_hand_no, gametype_id, hand_start_time, len(names), tableName, datetime.datetime.today(), maxSeats))
    #todo: find a better way of doing this...
    #cursor.execute("SELECT id FROM Hands WHERE siteHandNo=%s AND gametypeId=%s", (site_hand_no, gametype_id))
    #return cursor.fetchall()[0][0]
    return getLastInsertId(backend, conn, cursor)
    #return db.insert_id() # mysql only
#end def storeHands
 
def store_hands_players_holdem_omaha(backend, conn, cursor, category, hands_id, player_ids, start_cashes
                                    ,positions, card_values, card_suits, winnings, rakes, seatNos):
    result=[]
    if (category=="holdem"):
        for i in xrange(len(player_ids)):
            cursor.execute ("""
INSERT INTO HandsPlayers
(handId, playerId, startCash, position,
card1Value, card1Suit, card2Value, card2Suit, winnings, rake, seatNo)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (hands_id, player_ids[i], start_cashes[i], positions[i],
            card_values[i][0], card_suits[i][0], card_values[i][1], card_suits[i][1],
            winnings[i], rakes[i], seatNos[i]))
            #cursor.execute("SELECT id FROM HandsPlayers WHERE handId=%s AND playerId=%s", (hands_id, player_ids[i]))
            #result.append(cursor.fetchall()[0][0])
            result.append( getLastInsertId(backend, conn, cursor) ) # mysql only
    elif (category=="omahahi" or category=="omahahilo"):
        for i in xrange(len(player_ids)):
            cursor.execute ("""INSERT INTO HandsPlayers
(handId, playerId, startCash, position,
card1Value, card1Suit, card2Value, card2Suit,
card3Value, card3Suit, card4Value, card4Suit, winnings, rake, seatNo)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (hands_id, player_ids[i], start_cashes[i], positions[i],
            card_values[i][0], card_suits[i][0], card_values[i][1], card_suits[i][1],
            card_values[i][2], card_suits[i][2], card_values[i][3], card_suits[i][3],
            winnings[i], rakes[i], seatNos[i]))
            #cursor.execute("SELECT id FROM HandsPlayers WHERE handId=%s AND playerId+0=%s", (hands_id, player_ids[i]))
            #result.append(cursor.fetchall()[0][0])
            result.append( getLastInsertId(backend, conn, cursor) ) # mysql only
    else:
        raise FpdbError("invalid category")
    return result
#end def store_hands_players_holdem_omaha
 
def store_hands_players_stud(backend, conn, cursor, hands_id, player_ids, start_cashes, antes,
                             card_values, card_suits, winnings, rakes, seatNos):
#stores hands_players rows for stud/razz games. returns an array of the resulting IDs
    result=[]
    #print "before inserts in store_hands_players_stud, antes:", antes
    for i in xrange(len(player_ids)):
        cursor.execute ("""INSERT INTO HandsPlayers
(handId, playerId, startCash, ante,
card1Value, card1Suit, card2Value, card2Suit,
card3Value, card3Suit, card4Value, card4Suit,
card5Value, card5Suit, card6Value, card6Suit,
card7Value, card7Suit, winnings, rake, seatNo)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
%s, %s, %s, %s)""",
        (hands_id, player_ids[i], start_cashes[i], antes[i],
        card_values[i][0], card_suits[i][0], card_values[i][1], card_suits[i][1],
        card_values[i][2], card_suits[i][2], card_values[i][3], card_suits[i][3],
        card_values[i][4], card_suits[i][4], card_values[i][5], card_suits[i][5],
        card_values[i][6], card_suits[i][6], winnings[i], rakes[i], seatNos[i]))
        #cursor.execute("SELECT id FROM HandsPlayers WHERE handId=%s AND playerId+0=%s", (hands_id, player_ids[i]))
        #result.append(cursor.fetchall()[0][0])
        result.append( getLastInsertId(backend, conn, cursor) ) # mysql only
    return result
#end def store_hands_players_stud
 
def store_hands_players_holdem_omaha_tourney(backend, conn, cursor, category, hands_id, player_ids
                                            ,start_cashes, positions, card_values, card_suits
                                            , winnings, rakes, seatNos, tourneys_players_ids):
    #stores hands_players for tourney holdem/omaha hands
    result=[]
    for i in xrange(len(player_ids)):
        if len(card_values[0])==2:
            cursor.execute ("""INSERT INTO HandsPlayers
(handId, playerId, startCash, position,
card1Value, card1Suit, card2Value, card2Suit,
winnings, rake, tourneysPlayersId, seatNo)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (hands_id, player_ids[i], start_cashes[i], positions[i],
            card_values[i][0], card_suits[i][0], card_values[i][1], card_suits[i][1],
            winnings[i], rakes[i], tourneys_players_ids[i], seatNos[i]))
        elif len(card_values[0])==4:
            cursor.execute ("""INSERT INTO HandsPlayers
(handId, playerId, startCash, position,
card1Value, card1Suit, card2Value, card2Suit,
card3Value, card3Suit, card4Value, card4Suit,
winnings, rake, tourneysPlayersId, seatNo)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (hands_id, player_ids[i], start_cashes[i], positions[i],
            card_values[i][0], card_suits[i][0], card_values[i][1], card_suits[i][1],
            card_values[i][2], card_suits[i][2], card_values[i][3], card_suits[i][3],
            winnings[i], rakes[i], tourneys_players_ids[i], seatNos[i]))
        else:
            raise FpdbError ("invalid card_values length:"+str(len(card_values[0])))
        #cursor.execute("SELECT id FROM HandsPlayers WHERE handId=%s AND playerId+0=%s", (hands_id, player_ids[i]))
        #result.append(cursor.fetchall()[0][0])
        result.append( getLastInsertId(backend, conn, cursor) ) # mysql only
    
    return result
#end def store_hands_players_holdem_omaha_tourney
 
def store_hands_players_stud_tourney(backend, conn, cursor, hands_id, player_ids, start_cashes,
            antes, card_values, card_suits, winnings, rakes, seatNos, tourneys_players_ids):
#stores hands_players for tourney stud/razz hands
    result=[]
    for i in xrange(len(player_ids)):
        cursor.execute ("""INSERT INTO HandsPlayers
(handId, playerId, startCash, ante,
card1Value, card1Suit, card2Value, card2Suit,
card3Value, card3Suit, card4Value, card4Suit,
card5Value, card5Suit, card6Value, card6Suit,
card7Value, card7Suit, winnings, rake, tourneysPlayersId, seatNo)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
%s, %s, %s, %s, %s, %s)""",
        (hands_id, player_ids[i], start_cashes[i], antes[i],
        card_values[i][0], card_suits[i][0], card_values[i][1], card_suits[i][1],
        card_values[i][2], card_suits[i][2], card_values[i][3], card_suits[i][3],
        card_values[i][4], card_suits[i][4], card_values[i][5], card_suits[i][5],
        card_values[i][6], card_suits[i][6], winnings[i], rakes[i], tourneys_players_ids[i], seatNos[i]))
        #cursor.execute("SELECT id FROM HandsPlayers WHERE handId=%s AND playerId+0=%s", (hands_id, player_ids[i]))
        #result.append(cursor.fetchall()[0][0])
        result.append( getLastInsertId(backend, conn, cursor) ) # mysql only
    return result
#end def store_hands_players_stud_tourney
 
def generateHudCacheData(player_ids, base, category, action_types, allIns, actionTypeByNo
                        ,winnings, totalWinnings, positions, actionTypes, actionAmounts, antes):
    """calculates data for the HUD during import. IMPORTANT: if you change this method make
sure to also change the following storage method and table_viewer.prepare_data if necessary
"""
    #print "generateHudCacheData, len(player_ids)=", len(player_ids)
    #setup subarrays of the result dictionary.
    street0VPI=[]
    street0Aggr=[]
    street0_3B4BChance=[]
    street0_3B4BDone=[]
    street1Seen=[]
    street2Seen=[]
    street3Seen=[]
    street4Seen=[]
    sawShowdown=[]
    street1Aggr=[]
    street2Aggr=[]
    street3Aggr=[]
    street4Aggr=[]
    otherRaisedStreet1=[]
    otherRaisedStreet2=[]
    otherRaisedStreet3=[]
    otherRaisedStreet4=[]
    foldToOtherRaisedStreet1=[]
    foldToOtherRaisedStreet2=[]
    foldToOtherRaisedStreet3=[]
    foldToOtherRaisedStreet4=[]
    wonWhenSeenStreet1=[]
    
    wonAtSD=[]
    stealAttemptChance=[]
    stealAttempted=[]
    hudDataPositions=[]
    
    firstPfRaiseByNo=-1
    firstPfRaiserId=-1
    firstPfRaiserNo=-1
    firstPfCallByNo=-1
    firstPfCallerId=-1
    
    for i, action in enumerate(actionTypeByNo[0]):
        if action[1] == "bet":
            firstPfRaiseByNo = i
            firstPfRaiserId = action[0]
            for j, pid in enumerate(player_ids):
                if pid == firstPfRaiserId:
                    firstPfRaiserNo = j
                    break
            break
    for i, action in enumerate(actionTypeByNo[0]):
        if action[1] == "call":
            firstPfCallByNo = i
            firstPfCallerId = action[0]
            break
    
    cutoffId=-1
    buttonId=-1
    sbId=-1
    bbId=-1
    if base=="hold":
        for player, pos in enumerate(positions):
            if pos == 1:
                cutoffId = player_ids[player]
            if pos == 0:
                buttonId = player_ids[player]
            if pos == 'S':
                sbId = player_ids[player]
            if pos == 'B':
                bbId = player_ids[player]
            
    someoneStole=False
    
    #run a loop for each player preparing the actual values that will be commited to SQL
    for player in xrange(len(player_ids)):
        #set default values
        myStreet0VPI=False
        myStreet0Aggr=False
        myStreet0_3B4BChance=False
        myStreet0_3B4BDone=False
        myStreet1Seen=False
        myStreet2Seen=False
        myStreet3Seen=False
        myStreet4Seen=False
        mySawShowdown=False
        myStreet1Aggr=False
        myStreet2Aggr=False
        myStreet3Aggr=False
        myStreet4Aggr=False
        myOtherRaisedStreet1=False
        myOtherRaisedStreet2=False
        myOtherRaisedStreet3=False
        myOtherRaisedStreet4=False
        myFoldToOtherRaisedStreet1=False
        myFoldToOtherRaisedStreet2=False
        myFoldToOtherRaisedStreet3=False
        myFoldToOtherRaisedStreet4=False
        myWonWhenSeenStreet1=0.0
        myWonAtSD=0.0
        myStealAttemptChance=False
        myStealAttempted=False
        
        #calculate VPIP and PFR
        street=0
        heroPfRaiseCount=0
        for currentAction in action_types[street][player]: # finally individual actions
            if currentAction == "bet":
                myStreet0Aggr = True
            if currentAction == "bet" or currentAction == "call":
                myStreet0VPI = True
        
        #PF3B4BChance and PF3B4B
        pfFold=-1
        pfRaise=-1
        if firstPfRaiseByNo != -1:
            for i, actionType in enumerate(actionTypeByNo[0]):
                if actionType[0] == player_ids[player]:
                    if actionType[1] == "bet" and pfRaise == -1 and i > firstPfRaiseByNo:
                        pfRaise = i
                    if actionType[1] == "fold" and pfFold == -1:
                        pfFold = i
            if pfFold == -1 or pfFold > firstPfRaiseByNo:
                myStreet0_3B4BChance = True
                if pfRaise > firstPfRaiseByNo:
                    myStreet0_3B4BDone = True
        
        #steal calculations
        if base == "hold":
            if len(player_ids)>=5: #no point otherwise
                if positions[player]==1:
                    if firstPfRaiserId==player_ids[player]:
                        myStealAttemptChance=True
                        myStealAttempted=True
                    elif firstPfRaiserId==buttonId or firstPfRaiserId==sbId or firstPfRaiserId==bbId or firstPfRaiserId==-1:
                        myStealAttemptChance=True
                if positions[player]==0:
                    if firstPfRaiserId==player_ids[player]:
                        myStealAttemptChance=True
                        myStealAttempted=True
                    elif firstPfRaiserId==sbId or firstPfRaiserId==bbId or firstPfRaiserId==-1:
                        myStealAttemptChance=True
                if positions[player]=='S':
                    if firstPfRaiserId==player_ids[player]:
                        myStealAttemptChance=True
                        myStealAttempted=True
                    elif firstPfRaiserId==bbId or firstPfRaiserId==-1:
                        myStealAttemptChance=True
                if positions[player]=='B':
                    pass
            
                if myStealAttempted:
                    someoneStole=True
        
        
        #calculate saw* values
        isAllIn = False
        if any(i for i in allIns[0][player]):
            isAllIn = True
        if (len(action_types[1][player])>0 or isAllIn):
            myStreet1Seen = True
            
            if any(i for i in allIns[1][player]):
                isAllIn = True
            if (len(action_types[2][player])>0 or isAllIn):
                myStreet2Seen = True
 
                if any(i for i in allIns[2][player]):
                    isAllIn = True
                if (len(action_types[3][player])>0 or isAllIn):
                    myStreet3Seen = True
 
                    #print "base:", base
                    if base=="hold":
                        mySawShowdown = True
                        if any(actiontype == "fold" for actiontype in action_types[3][player]):
                            mySawShowdown = False
                    else:
                        #print "in else"
                        if any(i for i in allIns[3][player]):
                            isAllIn = True
                        if (len(action_types[4][player])>0 or isAllIn):
                            #print "in if"
                            myStreet4Seen = True
 
                            mySawShowdown = True
                            if any(actiontype == "fold" for actiontype in action_types[4][player]):
                                mySawShowdown = False
                        
 
        #flop stuff
        street=1
        if myStreet1Seen:
            if any(actiontype == "bet" for actiontype in action_types[street][player]):
                myStreet1Aggr = True
            
            for otherPlayer in xrange(len(player_ids)):
                if player==otherPlayer:
                    pass
                else:
                    for countOther in xrange(len(action_types[street][otherPlayer])):
                        if action_types[street][otherPlayer][countOther]=="bet":
                            myOtherRaisedStreet1=True
                            for countOtherFold in xrange(len(action_types[street][player])):
                                if action_types[street][player][countOtherFold]=="fold":
                                    myFoldToOtherRaisedStreet1=True
        
        #turn stuff - copy of flop with different vars
        street=2
        if myStreet2Seen:
            if any(actiontype == "bet" for actiontype in action_types[street][player]):
                myStreet2Aggr = True
            
            for otherPlayer in xrange(len(player_ids)):
                if player==otherPlayer:
                    pass
                else:
                    for countOther in xrange(len(action_types[street][otherPlayer])):
                        if action_types[street][otherPlayer][countOther]=="bet":
                            myOtherRaisedStreet2=True
                            for countOtherFold in xrange(len(action_types[street][player])):
                                if action_types[street][player][countOtherFold]=="fold":
                                    myFoldToOtherRaisedStreet2=True
        
        #river stuff - copy of flop with different vars
        street=3
        if myStreet3Seen:
            if any(actiontype == "bet" for actiontype in action_types[street][player]):
                    myStreet3Aggr = True
            
            for otherPlayer in xrange(len(player_ids)):
                if player==otherPlayer:
                    pass
                else:
                    for countOther in xrange(len(action_types[street][otherPlayer])):
                        if action_types[street][otherPlayer][countOther]=="bet":
                            myOtherRaisedStreet3=True
                            for countOtherFold in xrange(len(action_types[street][player])):
                                if action_types[street][player][countOtherFold]=="fold":
                                    myFoldToOtherRaisedStreet3=True
        
        #stud river stuff - copy of flop with different vars
        street=4
        if myStreet4Seen:
            if any(actiontype == "bet" for actiontype in action_types[street][player]):
                myStreet4Aggr=True
            
            for otherPlayer in xrange(len(player_ids)):
                if player==otherPlayer:
                    pass
                else:
                    for countOther in xrange(len(action_types[street][otherPlayer])):
                        if action_types[street][otherPlayer][countOther]=="bet":
                            myOtherRaisedStreet4=True
                            for countOtherFold in xrange(len(action_types[street][player])):
                                if action_types[street][player][countOtherFold]=="fold":
                                    myFoldToOtherRaisedStreet4=True
        
        if winnings[player] != 0:
            if myStreet1Seen:
                myWonWhenSeenStreet1 = winnings[player] / float(totalWinnings)
                if mySawShowdown:
                    myWonAtSD=myWonWhenSeenStreet1
        
        #add each value to the appropriate array
        street0VPI.append(myStreet0VPI)
        street0Aggr.append(myStreet0Aggr)
        street0_3B4BChance.append(myStreet0_3B4BChance)
        street0_3B4BDone.append(myStreet0_3B4BDone)
        street1Seen.append(myStreet1Seen)
        street2Seen.append(myStreet2Seen)
        street3Seen.append(myStreet3Seen)
        street4Seen.append(myStreet4Seen)
        sawShowdown.append(mySawShowdown)
        street1Aggr.append(myStreet1Aggr)
        street2Aggr.append(myStreet2Aggr)
        street3Aggr.append(myStreet3Aggr)
        street4Aggr.append(myStreet4Aggr)
        otherRaisedStreet1.append(myOtherRaisedStreet1)
        otherRaisedStreet2.append(myOtherRaisedStreet2)
        otherRaisedStreet3.append(myOtherRaisedStreet3)
        otherRaisedStreet4.append(myOtherRaisedStreet4)
        foldToOtherRaisedStreet1.append(myFoldToOtherRaisedStreet1)
        foldToOtherRaisedStreet2.append(myFoldToOtherRaisedStreet2)
        foldToOtherRaisedStreet3.append(myFoldToOtherRaisedStreet3)
        foldToOtherRaisedStreet4.append(myFoldToOtherRaisedStreet4)
        wonWhenSeenStreet1.append(myWonWhenSeenStreet1)
        wonAtSD.append(myWonAtSD)
        stealAttemptChance.append(myStealAttemptChance)
        stealAttempted.append(myStealAttempted)
        if base=="hold":
            pos=positions[player]
            if pos=='B':
                hudDataPositions.append('B')
            elif pos=='S':
                hudDataPositions.append('S')
            elif pos==0:
                hudDataPositions.append('D')
            elif pos==1:
                hudDataPositions.append('C')
            elif pos>=2 and pos<=4:
                hudDataPositions.append('M')
            elif pos>=5 and pos<=8:
                hudDataPositions.append('E')
            ### RHH Added this elif to handle being a dead hand before the BB (pos==9)
            elif pos==9:
                hudDataPositions.append('X')
            else:
                raise FpdbError("invalid position")
        elif base=="stud":
            #todo: stud positions and steals
            pass
    
    #add each array to the to-be-returned dictionary
    result={'street0VPI':street0VPI}
    result['street0Aggr']=street0Aggr
    result['street0_3B4BChance']=street0_3B4BChance
    result['street0_3B4BDone']=street0_3B4BDone
    result['street1Seen']=street1Seen
    result['street2Seen']=street2Seen
    result['street3Seen']=street3Seen
    result['street4Seen']=street4Seen
    result['sawShowdown']=sawShowdown
    
    result['street1Aggr']=street1Aggr
    result['otherRaisedStreet1']=otherRaisedStreet1
    result['foldToOtherRaisedStreet1']=foldToOtherRaisedStreet1
    result['street2Aggr']=street2Aggr
    result['otherRaisedStreet2']=otherRaisedStreet2
    result['foldToOtherRaisedStreet2']=foldToOtherRaisedStreet2
    result['street3Aggr']=street3Aggr
    result['otherRaisedStreet3']=otherRaisedStreet3
    result['foldToOtherRaisedStreet3']=foldToOtherRaisedStreet3
    result['street4Aggr']=street4Aggr
    result['otherRaisedStreet4']=otherRaisedStreet4
    result['foldToOtherRaisedStreet4']=foldToOtherRaisedStreet4
    result['wonWhenSeenStreet1']=wonWhenSeenStreet1
    result['wonAtSD']=wonAtSD
    result['stealAttemptChance']=stealAttemptChance
    result['stealAttempted']=stealAttempted
    
    #now the various steal values
    foldBbToStealChance=[]
    foldedBbToSteal=[]
    foldSbToStealChance=[]
    foldedSbToSteal=[]
    for player in xrange(len(player_ids)):
        myFoldBbToStealChance=False
        myFoldedBbToSteal=False
        myFoldSbToStealChance=False
        myFoldedSbToSteal=False
        
        if base=="hold":
            if someoneStole and (positions[player]=='B' or positions[player]=='S') and firstPfRaiserId!=player_ids[player]:
                street=0
                for count in xrange(len(action_types[street][player])):#individual actions
                    if positions[player]=='B':
                        myFoldBbToStealChance=True
                        if action_types[street][player][count]=="fold":
                            myFoldedBbToSteal=True
                    if positions[player]=='S':
                        myFoldSbToStealChance=True
                        if action_types[street][player][count]=="fold":
                            myFoldedSbToSteal=True
                
                
        foldBbToStealChance.append(myFoldBbToStealChance)
        foldedBbToSteal.append(myFoldedBbToSteal)
        foldSbToStealChance.append(myFoldSbToStealChance)
        foldedSbToSteal.append(myFoldedSbToSteal)
    result['foldBbToStealChance']=foldBbToStealChance
    result['foldedBbToSteal']=foldedBbToSteal
    result['foldSbToStealChance']=foldSbToStealChance
    result['foldedSbToSteal']=foldedSbToSteal
    
    #now CB
    street1CBChance=[]
    street1CBDone=[]
    didStreet1CB=[]
    for player in xrange(len(player_ids)):
        myStreet1CBChance=False
        myStreet1CBDone=False
        
        if street0VPI[player]:
            myStreet1CBChance=True
            if street1Aggr[player]:
                myStreet1CBDone=True
                didStreet1CB.append(player_ids[player])
                
        street1CBChance.append(myStreet1CBChance)
        street1CBDone.append(myStreet1CBDone)
    result['street1CBChance']=street1CBChance
    result['street1CBDone']=street1CBDone
    
    #now 2B
    street2CBChance=[]
    street2CBDone=[]
    didStreet2CB=[]
    for player in xrange(len(player_ids)):
        myStreet2CBChance=False
        myStreet2CBDone=False
        
        if street1CBDone[player]:
            myStreet2CBChance=True
            if street2Aggr[player]:
                myStreet2CBDone=True
                didStreet2CB.append(player_ids[player])
 
        street2CBChance.append(myStreet2CBChance)
        street2CBDone.append(myStreet2CBDone)
    result['street2CBChance']=street2CBChance
    result['street2CBDone']=street2CBDone
    
    #now 3B
    street3CBChance=[]
    street3CBDone=[]
    didStreet3CB=[]
    for player in xrange(len(player_ids)):
        myStreet3CBChance=False
        myStreet3CBDone=False
        
        if street2CBDone[player]:
            myStreet3CBChance=True
            if street3Aggr[player]:
                myStreet3CBDone=True
                didStreet3CB.append(player_ids[player])
 
        street3CBChance.append(myStreet3CBChance)
        street3CBDone.append(myStreet3CBDone)
    result['street3CBChance']=street3CBChance
    result['street3CBDone']=street3CBDone
    
    #and 4B
    street4CBChance=[]
    street4CBDone=[]
    didStreet4CB=[]
    for player in xrange(len(player_ids)):
        myStreet4CBChance=False
        myStreet4CBDone=False
        
        if street3CBDone[player]:
            myStreet4CBChance=True
            if street4Aggr[player]:
                myStreet4CBDone=True
                didStreet4CB.append(player_ids[player])
        
        street4CBChance.append(myStreet4CBChance)
        street4CBDone.append(myStreet4CBDone)
    result['street4CBChance']=street4CBChance
    result['street4CBDone']=street4CBDone
 
 
    result['position']=hudDataPositions
    
    foldToStreet1CBChance=[]
    foldToStreet1CBDone=[]
    foldToStreet2CBChance=[]
    foldToStreet2CBDone=[]
    foldToStreet3CBChance=[]
    foldToStreet3CBDone=[]
    foldToStreet4CBChance=[]
    foldToStreet4CBDone=[]
    
    for player in xrange(len(player_ids)):
        myFoldToStreet1CBChance=False
        myFoldToStreet1CBDone=False
        foldToStreet1CBChance.append(myFoldToStreet1CBChance)
        foldToStreet1CBDone.append(myFoldToStreet1CBDone)
 
        myFoldToStreet2CBChance=False
        myFoldToStreet2CBDone=False
        foldToStreet2CBChance.append(myFoldToStreet2CBChance)
        foldToStreet2CBDone.append(myFoldToStreet2CBDone)
        
        myFoldToStreet3CBChance=False
        myFoldToStreet3CBDone=False
        foldToStreet3CBChance.append(myFoldToStreet3CBChance)
        foldToStreet3CBDone.append(myFoldToStreet3CBDone)
        
        myFoldToStreet4CBChance=False
        myFoldToStreet4CBDone=False
        foldToStreet4CBChance.append(myFoldToStreet4CBChance)
        foldToStreet4CBDone.append(myFoldToStreet4CBDone)
    
    if len(didStreet1CB)>=1:
        generateFoldToCB(1, player_ids, didStreet1CB, street1CBDone, foldToStreet1CBChance, foldToStreet1CBDone, actionTypeByNo)
        
        if len(didStreet2CB)>=1:
            generateFoldToCB(2, player_ids, didStreet2CB, street2CBDone, foldToStreet2CBChance, foldToStreet2CBDone, actionTypeByNo)
 
            if len(didStreet3CB)>=1:
                generateFoldToCB(3, player_ids, didStreet3CB, street3CBDone, foldToStreet3CBChance, foldToStreet3CBDone, actionTypeByNo)
 
                if len(didStreet4CB)>=1:
                    generateFoldToCB(4, player_ids, didStreet4CB, street4CBDone, foldToStreet4CBChance, foldToStreet4CBDone, actionTypeByNo)
            
    result['foldToStreet1CBChance']=foldToStreet1CBChance
    result['foldToStreet1CBDone']=foldToStreet1CBDone
    result['foldToStreet2CBChance']=foldToStreet2CBChance
    result['foldToStreet2CBDone']=foldToStreet2CBDone
    result['foldToStreet3CBChance']=foldToStreet3CBChance
    result['foldToStreet3CBDone']=foldToStreet3CBDone
    result['foldToStreet4CBChance']=foldToStreet4CBChance
    result['foldToStreet4CBDone']=foldToStreet4CBDone
 
 
    totalProfit=[]
    
    street1CheckCallRaiseChance=[]
    street1CheckCallRaiseDone=[]
    street2CheckCallRaiseChance=[]
    street2CheckCallRaiseDone=[]
    street3CheckCallRaiseChance=[]
    street3CheckCallRaiseDone=[]
    street4CheckCallRaiseChance=[]
    street4CheckCallRaiseDone=[]
    #print "b4 totprof calc, len(playerIds)=", len(player_ids)
    for pl in xrange(len(player_ids)):
        #print "pl=", pl
        myTotalProfit=winnings[pl]  # still need to deduct other costs
        if antes:
            myTotalProfit=winnings[pl] - antes[pl]
        for i in xrange(len(actionTypes)): #iterate through streets
            #for j in xrange(len(actionTypes[i])): #iterate through names (using pl loop above)
                for k in xrange(len(actionTypes[i][pl])): #iterate through individual actions of that player on that street
                    myTotalProfit -= actionAmounts[i][pl][k]
        
        myStreet1CheckCallRaiseChance=False
        myStreet1CheckCallRaiseDone=False
        myStreet2CheckCallRaiseChance=False
        myStreet2CheckCallRaiseDone=False
        myStreet3CheckCallRaiseChance=False
        myStreet3CheckCallRaiseDone=False
        myStreet4CheckCallRaiseChance=False
        myStreet4CheckCallRaiseDone=False
        
        #print "myTotalProfit=", myTotalProfit
        totalProfit.append(myTotalProfit)
        #print "totalProfit[]=", totalProfit
        
        street1CheckCallRaiseChance.append(myStreet1CheckCallRaiseChance)
        street1CheckCallRaiseDone.append(myStreet1CheckCallRaiseDone)
        street2CheckCallRaiseChance.append(myStreet2CheckCallRaiseChance)
        street2CheckCallRaiseDone.append(myStreet2CheckCallRaiseDone)
        street3CheckCallRaiseChance.append(myStreet3CheckCallRaiseChance)
        street3CheckCallRaiseDone.append(myStreet3CheckCallRaiseDone)
        street4CheckCallRaiseChance.append(myStreet4CheckCallRaiseChance)
        street4CheckCallRaiseDone.append(myStreet4CheckCallRaiseDone)
 
    result['totalProfit']=totalProfit
    #print "res[totalProfit]=", result['totalProfit']
 
    result['street1CheckCallRaiseChance']=street1CheckCallRaiseChance
    result['street1CheckCallRaiseDone']=street1CheckCallRaiseDone
    result['street2CheckCallRaiseChance']=street2CheckCallRaiseChance
    result['street2CheckCallRaiseDone']=street2CheckCallRaiseDone
    result['street3CheckCallRaiseChance']=street3CheckCallRaiseChance
    result['street3CheckCallRaiseDone']=street3CheckCallRaiseDone
    result['street4CheckCallRaiseChance']=street4CheckCallRaiseChance
    result['street4CheckCallRaiseDone']=street4CheckCallRaiseDone
    return result
#end def generateHudCacheData
 
def generateFoldToCB(street, playerIDs, didStreetCB, streetCBDone, foldToStreetCBChance, foldToStreetCBDone, actionTypeByNo):
    """fills the passed foldToStreetCB* arrays appropriately depending on the given street"""
    #print "beginning of generateFoldToCB, street:", street, "len(actionTypeByNo):", len(actionTypeByNo)
    #print "len(actionTypeByNo[street]):",len(actionTypeByNo[street])
    firstCBReaction=0
    for action in xrange(len(actionTypeByNo[street])):
        if actionTypeByNo[street][action][1]=="bet":
            for player in didStreetCB:
                if player==actionTypeByNo[street][action][0] and firstCBReaction==0:
                    firstCBReaction=action+1
                    break
    
    for action in actionTypeByNo[street][firstCBReaction:]:
        for player in xrange(len(playerIDs)):
            if playerIDs[player]==action[0]:
                foldToStreetCBChance[player]=True
                if action[1]=="fold":
                    foldToStreetCBDone[player]=True
#end def generateFoldToCB
 
def storeHudCache(cursor, base, category, gametypeId, playerIds, hudImportData):
# if (category=="holdem" or category=="omahahi" or category=="omahahilo"):
        
        #print "storeHudCache, len(playerIds)=", len(playerIds), " len(vpip)=" \
        #, len(hudImportData['street0VPI']), " len(totprof)=", len(hudImportData['totalProfit'])
        for player in xrange(len(playerIds)):
            if base=="hold":
                cursor.execute("SELECT * FROM HudCache WHERE gametypeId+0=%s AND playerId=%s AND activeSeats=%s AND position=%s", (gametypeId, playerIds[player], len(playerIds), hudImportData['position'][player]))
            else:
                cursor.execute("SELECT * FROM HudCache WHERE gametypeId+0=%s AND playerId=%s AND activeSeats=%s", (gametypeId, playerIds[player], len(playerIds)))
            row=cursor.fetchone()
            #print "gametypeId:", gametypeId, "playerIds[player]",playerIds[player], "len(playerIds):",len(playerIds), "row:",row
            
            try: len(row)
            except TypeError:
                row=[]
            
            if (len(row)==0):
                #print "new huddata row"
                doInsert=True
                row=[]
                row.append(0)#blank for id
                row.append(gametypeId)
                row.append(playerIds[player])
                row.append(len(playerIds))#seats
                for i in xrange(len(hudImportData)+2):
                    row.append(0)
                
            else:
                doInsert=False
                newrow=[]
                for i in xrange(len(row)):
                    newrow.append(row[i])
                row=newrow
            
            if base=="hold":
                row[4]=hudImportData['position'][player]
            else:
                row[4]=0
            row[5]=1 #tourneysGametypeId
            row[6]+=1 #HDs
            if hudImportData['street0VPI'][player]: row[7]+=1
            if hudImportData['street0Aggr'][player]: row[8]+=1
            if hudImportData['street0_3B4BChance'][player]: row[9]+=1
            if hudImportData['street0_3B4BDone'][player]: row[10]+=1
            if hudImportData['street1Seen'][player]: row[11]+=1
            if hudImportData['street2Seen'][player]: row[12]+=1
            if hudImportData['street3Seen'][player]: row[13]+=1
            if hudImportData['street4Seen'][player]: row[14]+=1
            if hudImportData['sawShowdown'][player]: row[15]+=1
            if hudImportData['street1Aggr'][player]: row[16]+=1
            if hudImportData['street2Aggr'][player]: row[17]+=1
            if hudImportData['street3Aggr'][player]: row[18]+=1
            if hudImportData['street4Aggr'][player]: row[19]+=1
            if hudImportData['otherRaisedStreet1'][player]: row[20]+=1
            if hudImportData['otherRaisedStreet2'][player]: row[21]+=1
            if hudImportData['otherRaisedStreet3'][player]: row[22]+=1
            if hudImportData['otherRaisedStreet4'][player]: row[23]+=1
            if hudImportData['foldToOtherRaisedStreet1'][player]: row[24]+=1
            if hudImportData['foldToOtherRaisedStreet2'][player]: row[25]+=1
            if hudImportData['foldToOtherRaisedStreet3'][player]: row[26]+=1
            if hudImportData['foldToOtherRaisedStreet4'][player]: row[27]+=1
            if hudImportData['wonWhenSeenStreet1'][player]!=0.0: row[28]+=hudImportData['wonWhenSeenStreet1'][player]
            if hudImportData['wonAtSD'][player]!=0.0: row[29]+=hudImportData['wonAtSD'][player]
            if hudImportData['stealAttemptChance'][player]: row[30]+=1
            if hudImportData['stealAttempted'][player]: row[31]+=1
            if hudImportData['foldBbToStealChance'][player]: row[32]+=1
            if hudImportData['foldedBbToSteal'][player]: row[33]+=1
            if hudImportData['foldSbToStealChance'][player]: row[34]+=1
            if hudImportData['foldedSbToSteal'][player]: row[35]+=1
            
            if hudImportData['street1CBChance'][player]: row[36]+=1
            if hudImportData['street1CBDone'][player]: row[37]+=1
            if hudImportData['street2CBChance'][player]: row[38]+=1
            if hudImportData['street2CBDone'][player]: row[39]+=1
            if hudImportData['street3CBChance'][player]: row[40]+=1
            if hudImportData['street3CBDone'][player]: row[41]+=1
            if hudImportData['street4CBChance'][player]: row[42]+=1
            if hudImportData['street4CBDone'][player]: row[43]+=1
            
            if hudImportData['foldToStreet1CBChance'][player]: row[44]+=1
            if hudImportData['foldToStreet1CBDone'][player]: row[45]+=1
            if hudImportData['foldToStreet2CBChance'][player]: row[46]+=1
            if hudImportData['foldToStreet2CBDone'][player]: row[47]+=1
            if hudImportData['foldToStreet3CBChance'][player]: row[48]+=1
            if hudImportData['foldToStreet3CBDone'][player]: row[49]+=1
            if hudImportData['foldToStreet4CBChance'][player]: row[50]+=1
            if hudImportData['foldToStreet4CBDone'][player]: row[51]+=1
 
            #print "player=", player
            #print "len(totalProfit)=", len(hudImportData['totalProfit'])
            if hudImportData['totalProfit'][player]:
                row[52]+=hudImportData['totalProfit'][player]
 
            if hudImportData['street1CheckCallRaiseChance'][player]: row[53]+=1
            if hudImportData['street1CheckCallRaiseDone'][player]: row[54]+=1
            if hudImportData['street2CheckCallRaiseChance'][player]: row[55]+=1
            if hudImportData['street2CheckCallRaiseDone'][player]: row[56]+=1
            if hudImportData['street3CheckCallRaiseChance'][player]: row[57]+=1
            if hudImportData['street3CheckCallRaiseDone'][player]: row[58]+=1
            if hudImportData['street4CheckCallRaiseChance'][player]: row[59]+=1
            if hudImportData['street4CheckCallRaiseDone'][player]: row[60]+=1
            
            if doInsert:
                #print "playerid before insert:",row[2]
                cursor.execute("""INSERT INTO HudCache
(gametypeId, playerId, activeSeats, position, tourneyTypeId,
HDs, street0VPI, street0Aggr, street0_3B4BChance, street0_3B4BDone,
street1Seen, street2Seen, street3Seen, street4Seen, sawShowdown,
street1Aggr, street2Aggr, street3Aggr, street4Aggr, otherRaisedStreet1,
otherRaisedStreet2, otherRaisedStreet3, otherRaisedStreet4, foldToOtherRaisedStreet1, foldToOtherRaisedStreet2,
foldToOtherRaisedStreet3, foldToOtherRaisedStreet4, wonWhenSeenStreet1, wonAtSD, stealAttemptChance,
stealAttempted, foldBbToStealChance, foldedBbToSteal, foldSbToStealChance, foldedSbToSteal,
street1CBChance, street1CBDone, street2CBChance, street2CBDone, street3CBChance,
street3CBDone, street4CBChance, street4CBDone, foldToStreet1CBChance, foldToStreet1CBDone,
foldToStreet2CBChance, foldToStreet2CBDone, foldToStreet3CBChance, foldToStreet3CBDone, foldToStreet4CBChance,
foldToStreet4CBDone, totalProfit, street1CheckCallRaiseChance, street1CheckCallRaiseDone, street2CheckCallRaiseChance,
street2CheckCallRaiseDone, street3CheckCallRaiseChance, street3CheckCallRaiseDone, street4CheckCallRaiseChance, street4CheckCallRaiseDone)
VALUES (%s, %s, %s, %s, %s,
%s, %s, %s, %s, %s,
%s, %s, %s, %s, %s,
%s, %s, %s, %s, %s,
%s, %s, %s, %s, %s,
%s, %s, %s, %s, %s,
%s, %s, %s, %s, %s,
%s, %s, %s, %s, %s,
%s, %s, %s, %s, %s,
%s, %s, %s, %s, %s,
%s, %s, %s, %s, %s,
%s, %s, %s, %s, %s)""", (row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[12], row[13], row[14], row[15], row[16], row[17], row[18], row[19], row[20], row[21], row[22], row[23], row[24], row[25], row[26], row[27], row[28], row[29], row[30], row[31], row[32], row[33], row[34], row[35], row[36], row[37], row[38], row[39], row[40], row[41], row[42], row[43], row[44], row[45], row[46], row[47], row[48], row[49], row[50], row[51], row[52], row[53], row[54], row[55], row[56], row[57], row[58], row[59], row[60]))
            else:
                #print "storing updated hud data line"
                cursor.execute("""UPDATE HudCache
SET HDs=%s, street0VPI=%s, street0Aggr=%s, street0_3B4BChance=%s, street0_3B4BDone=%s,
street1Seen=%s, street2Seen=%s, street3Seen=%s, street4Seen=%s, sawShowdown=%s,
street1Aggr=%s, street2Aggr=%s, street3Aggr=%s, street4Aggr=%s, otherRaisedStreet1=%s,
otherRaisedStreet2=%s, otherRaisedStreet3=%s, otherRaisedStreet4=%s, foldToOtherRaisedStreet1=%s, foldToOtherRaisedStreet2=%s,
foldToOtherRaisedStreet3=%s, foldToOtherRaisedStreet4=%s, wonWhenSeenStreet1=%s, wonAtSD=%s, stealAttemptChance=%s,
stealAttempted=%s, foldBbToStealChance=%s, foldedBbToSteal=%s, foldSbToStealChance=%s, foldedSbToSteal=%s,
street1CBChance=%s, street1CBDone=%s, street2CBChance=%s, street2CBDone=%s, street3CBChance=%s,
street3CBDone=%s, street4CBChance=%s, street4CBDone=%s, foldToStreet1CBChance=%s, foldToStreet1CBDone=%s,
foldToStreet2CBChance=%s, foldToStreet2CBDone=%s, foldToStreet3CBChance=%s, foldToStreet3CBDone=%s, foldToStreet4CBChance=%s,
foldToStreet4CBDone=%s, totalProfit=%s, street1CheckCallRaiseChance=%s, street1CheckCallRaiseDone=%s, street2CheckCallRaiseChance=%s,
street2CheckCallRaiseDone=%s, street3CheckCallRaiseChance=%s, street3CheckCallRaiseDone=%s, street4CheckCallRaiseChance=%s, street4CheckCallRaiseDone=%s
WHERE gametypeId=%s AND playerId=%s AND activeSeats=%s AND position=%s AND tourneyTypeId=%s""", (row[6], row[7], row[8], row[9], row[10],
                    row[11], row[12], row[13], row[14], row[15],
                    row[16], row[17], row[18], row[19], row[20],
                    row[21], row[22], row[23], row[24], row[25],
                    row[26], row[27], row[28], row[29], row[30],
                    row[31], row[32], row[33], row[34], row[35], row[36], row[37], row[38], row[39], row[40],
                    row[41], row[42], row[43], row[44], row[45], row[46], row[47], row[48], row[49], row[50],
                    row[51], row[52], row[53], row[54], row[55], row[56], row[57], row[58], row[59], row[60],
                    row[1], row[2], row[3], str(row[4]), row[5]))
# else:
# print "todo: implement storeHudCache for stud base"
#end def storeHudCache
 
def storeHudCache2(backend, cursor, base, category, gametypeId, playerIds, hudImportData):
        """Modified version aiming for more speed ..."""
# if (category=="holdem" or category=="omahahi" or category=="omahahilo"):
        
        #print "storeHudCache, len(playerIds)=", len(playerIds), " len(vpip)=" \
        #, len(hudImportData['street0VPI']), " len(totprof)=", len(hudImportData['totalProfit'])
        for player in xrange(len(playerIds)):
            
            # Set up a clean row
            row=[]
            row.append(0)#blank for id
            row.append(gametypeId)
            row.append(playerIds[player])
            row.append(len(playerIds))#seats
            for i in xrange(len(hudImportData)+2):
                row.append(0)
                
            if base=="hold":
                row[4]=hudImportData['position'][player]
            else:
                row[4]=0
            row[5]=1 #tourneysGametypeId
            row[6]+=1 #HDs
            if hudImportData['street0VPI'][player]: row[7]+=1
            if hudImportData['street0Aggr'][player]: row[8]+=1
            if hudImportData['street0_3B4BChance'][player]: row[9]+=1
            if hudImportData['street0_3B4BDone'][player]: row[10]+=1
            if hudImportData['street1Seen'][player]: row[11]+=1
            if hudImportData['street2Seen'][player]: row[12]+=1
            if hudImportData['street3Seen'][player]: row[13]+=1
            if hudImportData['street4Seen'][player]: row[14]+=1
            if hudImportData['sawShowdown'][player]: row[15]+=1
            if hudImportData['street1Aggr'][player]: row[16]+=1
            if hudImportData['street2Aggr'][player]: row[17]+=1
            if hudImportData['street3Aggr'][player]: row[18]+=1
            if hudImportData['street4Aggr'][player]: row[19]+=1
            if hudImportData['otherRaisedStreet1'][player]: row[20]+=1
            if hudImportData['otherRaisedStreet2'][player]: row[21]+=1
            if hudImportData['otherRaisedStreet3'][player]: row[22]+=1
            if hudImportData['otherRaisedStreet4'][player]: row[23]+=1
            if hudImportData['foldToOtherRaisedStreet1'][player]: row[24]+=1
            if hudImportData['foldToOtherRaisedStreet2'][player]: row[25]+=1
            if hudImportData['foldToOtherRaisedStreet3'][player]: row[26]+=1
            if hudImportData['foldToOtherRaisedStreet4'][player]: row[27]+=1
            if hudImportData['wonWhenSeenStreet1'][player]!=0.0: row[28]+=hudImportData['wonWhenSeenStreet1'][player]
            if hudImportData['wonAtSD'][player]!=0.0: row[29]+=hudImportData['wonAtSD'][player]
            if hudImportData['stealAttemptChance'][player]: row[30]+=1
            if hudImportData['stealAttempted'][player]: row[31]+=1
            if hudImportData['foldBbToStealChance'][player]: row[32]+=1
            if hudImportData['foldedBbToSteal'][player]: row[33]+=1
            if hudImportData['foldSbToStealChance'][player]: row[34]+=1
            if hudImportData['foldedSbToSteal'][player]: row[35]+=1
            
            if hudImportData['street1CBChance'][player]: row[36]+=1
            if hudImportData['street1CBDone'][player]: row[37]+=1
            if hudImportData['street2CBChance'][player]: row[38]+=1
            if hudImportData['street2CBDone'][player]: row[39]+=1
            if hudImportData['street3CBChance'][player]: row[40]+=1
            if hudImportData['street3CBDone'][player]: row[41]+=1
            if hudImportData['street4CBChance'][player]: row[42]+=1
            if hudImportData['street4CBDone'][player]: row[43]+=1
            
            if hudImportData['foldToStreet1CBChance'][player]: row[44]+=1
            if hudImportData['foldToStreet1CBDone'][player]: row[45]+=1
            if hudImportData['foldToStreet2CBChance'][player]: row[46]+=1
            if hudImportData['foldToStreet2CBDone'][player]: row[47]+=1
            if hudImportData['foldToStreet3CBChance'][player]: row[48]+=1
            if hudImportData['foldToStreet3CBDone'][player]: row[49]+=1
            if hudImportData['foldToStreet4CBChance'][player]: row[50]+=1
            if hudImportData['foldToStreet4CBDone'][player]: row[51]+=1
 
            #print "player=", player
            #print "len(totalProfit)=", len(hudImportData['totalProfit'])
            if hudImportData['totalProfit'][player]:
                row[52]+=hudImportData['totalProfit'][player]
 
            if hudImportData['street1CheckCallRaiseChance'][player]: row[53]+=1
            if hudImportData['street1CheckCallRaiseDone'][player]: row[54]+=1
            if hudImportData['street2CheckCallRaiseChance'][player]: row[55]+=1
            if hudImportData['street2CheckCallRaiseDone'][player]: row[56]+=1
            if hudImportData['street3CheckCallRaiseChance'][player]: row[57]+=1
            if hudImportData['street3CheckCallRaiseDone'][player]: row[58]+=1
            if hudImportData['street4CheckCallRaiseChance'][player]: row[59]+=1
            if hudImportData['street4CheckCallRaiseDone'][player]: row[60]+=1
            
            # Try to do the update first:
            num = cursor.execute("""UPDATE HudCache
SET HDs=HDs+%s, street0VPI=street0VPI+%s, street0Aggr=street0Aggr+%s,
    street0_3B4BChance=%s, street0_3B4BDone=%s,
    street1Seen=street1Seen+%s, street2Seen=street2Seen+%s, street3Seen=street3Seen+%s,
    street4Seen=street4Seen+%s, sawShowdown=sawShowdown+%s,
    street1Aggr=street1Aggr+%s, street2Aggr=street2Aggr+%s, street3Aggr=street3Aggr+%s,
    street4Aggr=street4Aggr+%s, otherRaisedStreet1=otherRaisedStreet1+%s,
    otherRaisedStreet2=otherRaisedStreet2+%s, otherRaisedStreet3=otherRaisedStreet3+%s,
    otherRaisedStreet4=otherRaisedStreet4+%s,
    foldToOtherRaisedStreet1=foldToOtherRaisedStreet1+%s, foldToOtherRaisedStreet2=foldToOtherRaisedStreet2+%s,
    foldToOtherRaisedStreet3=foldToOtherRaisedStreet3+%s, foldToOtherRaisedStreet4=foldToOtherRaisedStreet4+%s,
    wonWhenSeenStreet1=wonWhenSeenStreet1+%s, wonAtSD=wonAtSD+%s, stealAttemptChance=stealAttemptChance+%s,
    stealAttempted=stealAttempted+%s, foldBbToStealChance=foldBbToStealChance+%s,
    foldedBbToSteal=foldedBbToSteal+%s,
    foldSbToStealChance=foldSbToStealChance+%s, foldedSbToSteal=foldedSbToSteal+%s,
    street1CBChance=street1CBChance+%s, street1CBDone=street1CBDone+%s, street2CBChance=street2CBChance+%s,
    street2CBDone=street2CBDone+%s, street3CBChance=street3CBChance+%s,
    street3CBDone=street3CBDone+%s, street4CBChance=street4CBChance+%s, street4CBDone=street4CBDone+%s,
    foldToStreet1CBChance=foldToStreet1CBChance+%s, foldToStreet1CBDone=foldToStreet1CBDone+%s,
    foldToStreet2CBChance=foldToStreet2CBChance+%s, foldToStreet2CBDone=foldToStreet2CBDone+%s,
    foldToStreet3CBChance=foldToStreet3CBChance+%s,
    foldToStreet3CBDone=foldToStreet3CBDone+%s, foldToStreet4CBChance=foldToStreet4CBChance+%s,
    foldToStreet4CBDone=foldToStreet4CBDone+%s, totalProfit=totalProfit+%s,
    street1CheckCallRaiseChance=street1CheckCallRaiseChance+%s,
    street1CheckCallRaiseDone=street1CheckCallRaiseDone+%s, street2CheckCallRaiseChance=street2CheckCallRaiseChance+%s,
    street2CheckCallRaiseDone=street2CheckCallRaiseDone+%s, street3CheckCallRaiseChance=street3CheckCallRaiseChance+%s,
    street3CheckCallRaiseDone=street3CheckCallRaiseDone+%s, street4CheckCallRaiseChance=street4CheckCallRaiseChance+%s,
    street4CheckCallRaiseDone=street4CheckCallRaiseDone+%s
WHERE gametypeId+0=%s 
AND   playerId=%s 
AND   activeSeats=%s 
AND   position=%s 
AND   tourneyTypeId+0=%s""", (row[6], row[7], row[8], row[9], row[10],
                            row[11], row[12], row[13], row[14], row[15],
                            row[16], row[17], row[18], row[19], row[20],
                            row[21], row[22], row[23], row[24], row[25],
                            row[26], row[27], row[28], row[29], row[30],
                            row[31], row[32], row[33], row[34], row[35],
                            row[36], row[37], row[38], row[39], row[40],
                            row[41], row[42], row[43], row[44], row[45],
                            row[46], row[47], row[48], row[49], row[50],
                            row[51], row[52], row[53], row[54], row[55],
                            row[56], row[57], row[58], row[59], row[60],
                            row[1], row[2], row[3], str(row[4]), row[5]))
            # Test statusmessage to see if update worked, do insert if not
            #print "storehud2, upd num =", num
            if (   (backend == PGSQL and cursor.statusmessage != "UPDATE 1")
                or (backend == MYSQL_INNODB and num == 0) ):
                #print "playerid before insert:",row[2]," num = ", num
                cursor.execute("""INSERT INTO HudCache
(gametypeId, playerId, activeSeats, position, tourneyTypeId,
HDs, street0VPI, street0Aggr, street0_3B4BChance, street0_3B4BDone,
street1Seen, street2Seen, street3Seen, street4Seen, sawShowdown,
street1Aggr, street2Aggr, street3Aggr, street4Aggr, otherRaisedStreet1,
otherRaisedStreet2, otherRaisedStreet3, otherRaisedStreet4, foldToOtherRaisedStreet1, foldToOtherRaisedStreet2,
foldToOtherRaisedStreet3, foldToOtherRaisedStreet4, wonWhenSeenStreet1, wonAtSD, stealAttemptChance,
stealAttempted, foldBbToStealChance, foldedBbToSteal, foldSbToStealChance, foldedSbToSteal,
street1CBChance, street1CBDone, street2CBChance, street2CBDone, street3CBChance,
street3CBDone, street4CBChance, street4CBDone, foldToStreet1CBChance, foldToStreet1CBDone,
foldToStreet2CBChance, foldToStreet2CBDone, foldToStreet3CBChance, foldToStreet3CBDone, foldToStreet4CBChance,
foldToStreet4CBDone, totalProfit, street1CheckCallRaiseChance, street1CheckCallRaiseDone, street2CheckCallRaiseChance,
street2CheckCallRaiseDone, street3CheckCallRaiseChance, street3CheckCallRaiseDone, street4CheckCallRaiseChance, street4CheckCallRaiseDone)
VALUES (%s, %s, %s, %s, %s,
%s, %s, %s, %s, %s,
%s, %s, %s, %s, %s,
%s, %s, %s, %s, %s,
%s, %s, %s, %s, %s,
%s, %s, %s, %s, %s,
%s, %s, %s, %s, %s,
%s, %s, %s, %s, %s,
%s, %s, %s, %s, %s,
%s, %s, %s, %s, %s,
%s, %s, %s, %s, %s,
%s, %s, %s, %s, %s)""", (row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[12], row[13], row[14], row[15], row[16], row[17], row[18], row[19], row[20], row[21], row[22], row[23], row[24], row[25], row[26], row[27], row[28], row[29], row[30], row[31], row[32], row[33], row[34], row[35], row[36], row[37], row[38], row[39], row[40], row[41], row[42], row[43], row[44], row[45], row[46], row[47], row[48], row[49], row[50], row[51], row[52], row[53], row[54], row[55], row[56], row[57], row[58], row[59], row[60]))
                #print "hopefully inserted hud data line: ", cursor.statusmessage
                # message seems to be "INSERT 0 1"
            else:
                #print "updated(2) hud data line"
                pass
# else:
# print "todo: implement storeHudCache for stud base"
#end def storeHudCache2
 
def store_tourneys(cursor, tourneyTypeId, siteTourneyNo, entries, prizepool, startTime):
    cursor.execute("SELECT id FROM Tourneys WHERE siteTourneyNo=%s AND tourneyTypeId+0=%s", (siteTourneyNo, tourneyTypeId))
    tmp=cursor.fetchone()
    #print "tried SELECTing tourneys.id, result:",tmp
    
    try:
        len(tmp)
    except TypeError:#means we have to create new one
        cursor.execute("""INSERT INTO Tourneys
(tourneyTypeId, siteTourneyNo, entries, prizepool, startTime)
VALUES (%s, %s, %s, %s, %s)""", (tourneyTypeId, siteTourneyNo, entries, prizepool, startTime))
        cursor.execute("SELECT id FROM Tourneys WHERE siteTourneyNo=%s AND tourneyTypeId+0=%s", (siteTourneyNo, tourneyTypeId))
        tmp=cursor.fetchone()
        #print "created new tourneys.id:",tmp
    return tmp[0]
#end def store_tourneys
 
def store_tourneys_players(cursor, tourney_id, player_ids, payin_amounts, ranks, winnings):
    result=[]
    #print "in store_tourneys_players. tourney_id:",tourney_id
    #print "player_ids:",player_ids
    #print "payin_amounts:",payin_amounts
    #print "ranks:",ranks
    #print "winnings:",winnings
    for i in xrange(len(player_ids)):
        cursor.execute("SELECT id FROM TourneysPlayers WHERE tourneyId=%s AND playerId+0=%s", (tourney_id, player_ids[i]))
        tmp=cursor.fetchone()
        #print "tried SELECTing tourneys_players.id:",tmp
        
        try:
            len(tmp)
        except TypeError:
            cursor.execute("""INSERT INTO TourneysPlayers
(tourneyId, playerId, payinAmount, rank, winnings) VALUES (%s, %s, %s, %s, %s)""",
            (tourney_id, player_ids[i], payin_amounts[i], ranks[i], winnings[i]))
            
            cursor.execute("SELECT id FROM TourneysPlayers WHERE tourneyId=%s AND playerId+0=%s",
                           (tourney_id, player_ids[i]))
            tmp=cursor.fetchone()
            #print "created new tourneys_players.id:",tmp
        result.append(tmp[0])
    return result
#end def store_tourneys_players
