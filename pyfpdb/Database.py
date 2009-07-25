#!/usr/bin/env python
"""Database.py

Create and manage the database objects.
"""
#    Copyright 2008, Ray E. Barker
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

########################################################################

# postmaster -D /var/lib/pgsql/data

#    Standard Library modules
import sys
import traceback
from datetime import datetime, date, time, timedelta
from time import time, strftime
import string

#    pyGTK modules

#    FreePokerTools modules
import fpdb_db
import fpdb_simple
import Configuration
import SQL
import Card

class Database:

    MYSQL_INNODB = 2
    PGSQL = 3
    SQLITE = 4

    def __init__(self, c, db_name = None, game = None, sql = None): # db_name and game not used any more
        print "\ncreating Database instance, sql =", sql
        self.fdb = fpdb_db.fpdb_db()   # sets self.fdb.db self.fdb.cursor and self.fdb.sql
        self.fdb.do_connect(c)
        self.connection = self.fdb.db

        db_params = c.get_db_parameters()
        self.import_options = c.get_import_parameters()
        self.type = db_params['db-type']
        self.backend = db_params['db-backend']
        self.db_server = db_params['db-server']
        
        if self.backend == self.PGSQL:
            from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT, ISOLATION_LEVEL_READ_COMMITTED, ISOLATION_LEVEL_SERIALIZABLE
            #ISOLATION_LEVEL_AUTOCOMMIT     = 0
            #ISOLATION_LEVEL_READ_COMMITTED = 1 
            #ISOLATION_LEVEL_SERIALIZABLE   = 2

        # where possible avoid creating new SQL instance by using the global one passed in
        if sql == None:
            self.sql = SQL.Sql(type = self.type, db_server = db_params['db-server'])
        else:
            self.sql = sql
        
                                   # To add to config:
        self.hud_style = 'T'       # A=All-time 
                                   # S=Session
                                   # T=timed (last n days)
                                   # Future values may also include: 
                                   #                                 H=Hands (last n hands)
        self.hud_hands = 1000      # Max number of hands from each player to use for hud stats
        self.hud_days  = 30        # Max number of days from each player to use for hud stats
        self.hud_session_gap = 30  # Gap (minutes) between hands that indicates a change of session
                                   # (hands every 2 mins for 1 hour = one session, if followed
                                   # by a 40 minute gap and then more hands on same table that is
                                   # a new session)
        self.cursor = self.fdb.cursor

        if self.fdb.wrongDbVersion == False:
            # self.hand_1day_ago used to fetch stats for current session (i.e. if hud_style = 'S')
            self.hand_1day_ago = 0
            self.cursor.execute(self.sql.query['get_hand_1day_ago'])
            row = self.cursor.fetchone()
            if row and row[0]:
                self.hand_1day_ago = row[0]
            #print "hand 1day ago =", self.hand_1day_ago

            # self.date_ndays_ago used if hud_style = 'T'
            d = timedelta(days=self.hud_days)
            now = datetime.utcnow() - d
            self.date_ndays_ago = "d%02d%02d%02d" % (now.year-2000, now.month, now.day)

            # self.hand_nhands_ago is used for fetching stats for last n hands (hud_style = 'H')
            # This option not used yet
            self.hand_nhands_ago = 0
            # should use aggregated version of query if appropriate
            self.cursor.execute(self.sql.query['get_hand_nhands_ago'], (self.hud_hands,self.hud_hands))
            row = self.cursor.fetchone()
            if row and row[0]:
                self.hand_nhands_ago = row[0]
            print "hand n hands ago =", self.hand_nhands_ago

            #self.cursor.execute(self.sql.query['get_table_name'], (hand_id, ))
            #row = self.cursor.fetchone()
        else:
            print "Bailing on DB query, not sure it exists yet"

        self.saveActions = False if self.import_options['saveActions'] == False else True

        self.connection.rollback()  # make sure any locks taken so far are released

    # could be used by hud to change hud style
    def set_hud_style(self, style):
        self.hud_style = style

    def do_connect(self, c):
        self.fdb.do_connect(c)

    def commit(self):
        self.fdb.db.commit()

    def rollback(self):
        self.fdb.db.rollback()

    def get_cursor(self):
        return self.connection.cursor()

    def close_connection(self):
        self.connection.close()

    def disconnect(self, due_to_error=False):
        """Disconnects the DB (rolls back if param is true, otherwise commits"""
        self.fdb.disconnect(due_to_error)
    
    def reconnect(self, due_to_error=False):
        """Reconnects the DB"""
        self.fdb.reconnect(due_to_error=False)
    
    def get_backend_name(self):
        """Reconnects the DB"""
        return self.fdb.get_backend_name()
        

    def get_table_name(self, hand_id):
        c = self.connection.cursor()
        c.execute(self.sql.query['get_table_name'], (hand_id, ))
        row = c.fetchone()
        return row
    
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

    def convert_cards(self, d):
        ranks = ('', '', '2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A')
        cards = ""
        for i in xrange(1, 8):
#            key = 'card' + str(i) + 'Value'
#            if not d.has_key(key): continue
#            if d[key] == None:
#                break
#            elif d[key] == 0:
#                cards += "xx"
#            else:
#                cards += ranks[d['card' + str(i) + 'Value']] + d['card' +str(i) + 'Suit']
            cv = "card%dvalue" % i
            if cv not in d or d[cv] == None:
                break
            elif d[cv] == 0:
                cards += "xx"
            else:
                cs = "card%dsuit" % i
                cards = "%s%s%s" % (cards, ranks[d[cv]], d[cs])
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

    def get_stats_from_hand(self, hand, aggregate = False):
        if self.hud_style == 'S':
            return( self.get_stats_from_hand_session(hand) )
        else:   # self.hud_style == A
            if aggregate:
                query = 'get_stats_from_hand_aggregated'
            else:
                query = 'get_stats_from_hand'
        
        if self.hud_style == 'T':
            stylekey = self.date_ndays_ago
        else:  # assume A (all-time)
            stylekey = '0000000'  # all stylekey values should be higher than this

        subs = (hand, hand, stylekey)
        #print "get stats: hud style =", self.hud_style, "subs =", subs
        c = self.connection.cursor()

#       now get the stats
        c.execute(self.sql.query[query], subs)
        colnames = [desc[0] for desc in c.description]
        stat_dict = {}
        for row in c.fetchall():
            t_dict = {}
            for name, val in zip(colnames, row):
                t_dict[name.lower()] = val
#                print t_dict
            stat_dict[t_dict['player_id']] = t_dict

        return stat_dict

    # uses query on handsplayers instead of hudcache to get stats on just this session
    def get_stats_from_hand_session(self, hand):

        if self.hud_style == 'S':
            query = self.sql.query['get_stats_from_hand_session']
            if self.db_server == 'mysql':
                query = query.replace("<signed>", 'signed ')
            else:
                query = query.replace("<signed>", '')
        else:   # self.hud_style == A
            return None
        
        subs = (self.hand_1day_ago, hand)
        c = self.connection.cursor()

        # now get the stats
        #print "sess_stats: subs =", subs, "subs[0] =", subs[0]
        c.execute(query, subs)
        colnames = [desc[0] for desc in c.description]
        n,stat_dict = 0,{}
        row = c.fetchone()
        while row:
            if colnames[0].lower() == 'player_id':
                playerid = row[0]
            else:
                print "ERROR: query %s result does not have player_id as first column" % (query,)
                break

            for name, val in zip(colnames, row):
                if not playerid in stat_dict:
                    stat_dict[playerid] = {}
                    stat_dict[playerid][name.lower()] = val
                elif not name.lower() in stat_dict[playerid]:
                    stat_dict[playerid][name.lower()] = val
                elif name.lower() not in ('hand_id', 'player_id', 'seat', 'screen_name', 'seats'):
                    stat_dict[playerid][name.lower()] += val
            n += 1
            if n >= 4000: break  # todo: don't think this is needed so set nice and high 
                                 #       for now - comment out or remove?
            row = c.fetchone()
        #print "   %d rows fetched, len(stat_dict) = %d" % (n, len(stat_dict))

        #print "session stat_dict =", stat_dict
        return stat_dict
            
    def get_player_id(self, config, site, player_name):
        c = self.connection.cursor()
        c.execute(self.sql.query['get_player_id'], {'player': player_name, 'site': site})
        row = c.fetchone()
        if row:
            return row[0]
        else:
            return None

    def get_last_insert_id(self):
        return self.fdb.getLastInsertId()


    #stores a stud/razz hand into the database
    def ring_stud(self, config, settings, db, cursor, base, category, site_hand_no, gametype_id, hand_start_time
                 ,names, player_ids, start_cashes, antes, card_values, card_suits, winnings, rakes
                 ,action_types, allIns, action_amounts, actionNos, hudImportData, maxSeats, tableName
                 ,seatNos):

        fpdb_simple.fillCardArrays(len(names), base, category, card_values, card_suits)

        hands_id = fpdb_simple.storeHands(self.backend, db, cursor, site_hand_no, gametype_id
                                       ,hand_start_time, names, tableName, maxSeats, hudImportData
                                       ,(None, None, None, None, None), (None, None, None, None, None))

        #print "before calling store_hands_players_stud, antes:", antes
        hands_players_ids = fpdb_simple.store_hands_players_stud(self.backend, db, cursor, hands_id, player_ids
                                                              ,start_cashes, antes, card_values
                                                              ,card_suits, winnings, rakes, seatNos)

        if 'dropHudCache' not in settings or settings['dropHudCache'] != 'drop':
            fpdb_simple.storeHudCache(self.backend, cursor, base, category, gametype_id, hand_start_time, player_ids, hudImportData)

        if self.saveActions:
            fpdb_simple.storeActions(cursor, hands_players_ids, action_types
                                    ,allIns, action_amounts, actionNos)
        return hands_id
    #end def ring_stud

    def ring_holdem_omaha(self, config, settings, db, cursor, base, category, site_hand_no, gametype_id
                         ,hand_start_time, names, player_ids, start_cashes, positions, card_values
                         ,card_suits, board_values, board_suits, winnings, rakes, action_types, allIns
                         ,action_amounts, actionNos, hudImportData, maxSeats, tableName, seatNos):
        """stores a holdem/omaha hand into the database"""

        t0 = time()
        fpdb_simple.fillCardArrays(len(names), base, category, card_values, card_suits)
        t1 = time()
        fpdb_simple.fill_board_cards(board_values, board_suits)
        t2 = time()

        hands_id = fpdb_simple.storeHands(self.backend, db, cursor, site_hand_no, gametype_id
                                       ,hand_start_time, names, tableName, maxSeats,
                                       hudImportData, board_values, board_suits)
        #TEMPORARY CALL! - Just until all functions are migrated
        t3 = time()
        hands_players_ids = fpdb_simple.store_hands_players_holdem_omaha(
                                   self.backend, db, cursor, category, hands_id, player_ids, start_cashes
                                 , positions, card_values, card_suits, winnings, rakes, seatNos, hudImportData)
        t4 = time()
        #print "ring holdem, backend=%d" % backend
        if 'dropHudCache' not in settings or settings['dropHudCache'] != 'drop':
            fpdb_simple.storeHudCache(self.backend, cursor, base, category, gametype_id, hand_start_time, player_ids, hudImportData)
        t5 = time()
        t6 = time()
        if self.saveActions:
            fpdb_simple.storeActions(cursor, hands_players_ids, action_types, allIns, action_amounts, actionNos)
        t7 = time()
        #print "fills=(%4.3f) saves=(%4.3f,%4.3f,%4.3f,%4.3f)" % (t2-t0, t3-t2, t4-t3, t5-t4, t6-t5)
        return hands_id
    #end def ring_holdem_omaha

    def tourney_holdem_omaha(self, config, settings, db, cursor, base, category, siteTourneyNo, buyin, fee, knockout
                            ,entries, prizepool, tourney_start, payin_amounts, ranks, tourneyTypeId
                            ,siteId #end of tourney specific params
                            ,site_hand_no, gametype_id, hand_start_time, names, player_ids
                            ,start_cashes, positions, card_values, card_suits, board_values
                            ,board_suits, winnings, rakes, action_types, allIns, action_amounts
                            ,actionNos, hudImportData, maxSeats, tableName, seatNos):
        """stores a tourney holdem/omaha hand into the database"""

        fpdb_simple.fillCardArrays(len(names), base, category, card_values, card_suits)
        fpdb_simple.fill_board_cards(board_values, board_suits)

        tourney_id = fpdb_simple.store_tourneys(cursor, tourneyTypeId, siteTourneyNo, entries, prizepool, tourney_start)
        tourneys_players_ids = fpdb_simple.store_tourneys_players(cursor, tourney_id, player_ids, payin_amounts, ranks, winnings)

        hands_id = fpdb_simple.storeHands(self.backend, db, cursor, site_hand_no, gametype_id
                                       ,hand_start_time, names, tableName, maxSeats)

        hands_players_ids = fpdb_simple.store_hands_players_holdem_omaha_tourney(
                          self.backend, db, cursor, category, hands_id, player_ids, start_cashes, positions
                        , card_values, card_suits, winnings, rakes, seatNos, tourneys_players_ids)

        #print "tourney holdem, backend=%d" % backend
        if 'dropHudCache' not in settings or settings['dropHudCache'] != 'drop':
            fpdb_simple.storeHudCache(self.backend, cursor, base, category, gametype_id, hand_start_time, player_ids, hudImportData)

        if self.saveActions:
            fpdb_simple.storeActions(cursor, hands_players_ids, action_types, allIns, action_amounts, actionNos)
        return hands_id
    #end def tourney_holdem_omaha

    def tourney_stud(self, config, settings, db, cursor, base, category, siteTourneyNo, buyin, fee, knockout, entries
                    ,prizepool, tourneyStartTime, payin_amounts, ranks, tourneyTypeId, siteId
                    ,siteHandNo, gametypeId, handStartTime, names, playerIds, startCashes, antes
                    ,cardValues, cardSuits, winnings, rakes, actionTypes, allIns, actionAmounts
                    ,actionNos, hudImportData, maxSeats, tableName, seatNos):
        #stores a tourney stud/razz hand into the database

        fpdb_simple.fillCardArrays(len(names), base, category, cardValues, cardSuits)

        tourney_id = fpdb_simple.store_tourneys(cursor, tourneyTypeId, siteTourneyNo, entries, prizepool, tourneyStartTime)

        tourneys_players_ids = fpdb_simple.store_tourneys_players(cursor, tourney_id, playerIds, payin_amounts, ranks, winnings)

        hands_id = fpdb_simple.storeHands(self.backend, db, cursor, siteHandNo, gametypeId, handStartTime, names, tableName, maxSeats)

        hands_players_ids = fpdb_simple.store_hands_players_stud_tourney(self.backend, db, cursor, hands_id
                                                 , playerIds, startCashes, antes, cardValues, cardSuits
                                                 , winnings, rakes, seatNos, tourneys_players_ids)

        if 'dropHudCache' not in settings or settings['dropHudCache'] != 'drop':
            fpdb_simple.storeHudCache(self.backend, cursor, base, category, gametypeId, hand_start_time, playerIds, hudImportData)

        if self.saveActions:
            fpdb_simple.storeActions(cursor, hands_players_ids, actionTypes, allIns, actionAmounts, actionNos)
        return hands_id
    #end def tourney_stud

    def rebuild_hudcache(self):
        """clears hudcache and rebuilds from the individual handsplayers records"""

        stime = time()
        self.connection.cursor().execute(self.sql.query['clearHudCache'])
        self.connection.cursor().execute(self.sql.query['rebuildHudCache'])
        self.commit()
        print "Rebuild hudcache took %.1f seconds" % (time() - stime,)
    #end def rebuild_hudcache


    def analyzeDB(self):
        """Do whatever the DB can offer to update index/table statistics"""
        stime = time()
        if self.backend == self.MYSQL_INNODB:
            try:
                self.cursor.execute(self.sql.query['analyze'])
            except:
                print "Error during analyze"
        elif self.backend == self.PGSQL:
            self.connection.set_isolation_level(0)   # allow vacuum to work
            try:
                self.cursor = self.get_cursor()
                self.cursor.execute(self.sql.query['analyze'])
            except:
                print "Error during analyze:", str(sys.exc_value)
            self.connection.set_isolation_level(1)   # go back to normal isolation level
        self.commit()
        atime = time() - stime
        print "Analyze took %.1f seconds" % (atime,)
    #end def analyzeDB

if __name__=="__main__":
    c = Configuration.Config()

    db_connection = Database(c, 'fpdb', 'holdem') # mysql fpdb holdem
#    db_connection = Database(c, 'fpdb-p', 'test') # mysql fpdb holdem
#    db_connection = Database(c, 'PTrackSv2', 'razz') # mysql razz
#    db_connection = Database(c, 'ptracks', 'razz') # postgres
    print "database connection object = ", db_connection.connection
    print "database type = ", db_connection.type
    
    h = db_connection.get_last_hand()
    print "last hand = ", h
    
    hero = db_connection.get_player_id(c, 'PokerStars', 'nutOmatic')
    if hero:
        print "nutOmatic is id_player = %d" % hero
    
    stat_dict = db_connection.get_stats_from_hand(h)
    for p in stat_dict.keys():
        print p, "  ", stat_dict[p]
        
    #print "nutOmatics stats:"
    #stat_dict = db_connection.get_stats_from_hand(h, hero)
    #for p in stat_dict.keys():
    #    print p, "  ", stat_dict[p]

    print "cards =", db_connection.get_cards(u'1')
    db_connection.close_connection

    print "press enter to continue"
    sys.stdin.readline()
