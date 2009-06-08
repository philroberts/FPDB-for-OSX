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
import string
from datetime import datetime, date, time, timedelta

#    pyGTK modules

#    FreePokerTools modules
import Configuration
import SQL
import Card

class Database:
    def __init__(self, c, db_name, game):
        db_params = c.get_db_parameters()
        if (string.lower(db_params['db-server']) == 'postgresql' or
            string.lower(db_params['db-server']) == 'postgres'):
            import psycopg2  #   posgres via DB-API
            import psycopg2.extensions 
            psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)

            try:
                if db_params['db-host'] == 'localhost' or db_params['db-host'] == '127.0.0.1': 
                    self.connection = psycopg2.connect(database = db_params['db-databaseName'])
                else:
                    self.connection = psycopg2.connect(host = db_params['db-host'],
                                       user = db_params['db-user'],
                                       password = db_params['db-password'],
                                       database = db_params['db-databaseName'])
            except:
                print "Error opening database connection %s.  See error log file." % (file)
                traceback.print_exc(file=sys.stderr)
                print "press enter to continue"
                sys.stdin.readline()
                sys.exit()

        elif string.lower(db_params['db-server']) == 'mysql':
            import MySQLdb  #    mysql bindings
            try:
                self.connection = MySQLdb.connect(host = db_params['db-host'],
                                       user = db_params['db-user'],
                                       passwd = db_params['db-password'],
                                       db = db_params['db-databaseName'])
                cur_iso = self.connection.cursor() 
                cur_iso.execute('SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED') 
                cur_iso.close()

            except:
                print "Error opening database connection %s.  See error log file." % (file)
                traceback.print_exc(file=sys.stderr)
                print "press enter to continue"
                sys.stdin.readline()
                sys.exit()

        else:
            print "Database = %s not recognized." % (c.supported_databases[db_name].db_server)
            sys.stderr.write("Database not recognized, exiting.\n")
            print "press enter to continue"
            sys.exit()

        self.type = db_params['db-type']
        self.db_server = c.supported_databases[db_name].db_server
        self.sql = SQL.Sql(game = game, type = self.type, db_server = self.db_server)
        self.connection.rollback()        
                                   # To add to config:
        self.hud_style = 'T'       # A=All-time 
                                   # S=Session
                                   # T=timed (last n days)
                                   # Future values may also include: 
                                   #                                 H=Hands (last n hands)
        self.hud_hands = 1000      # Max number of hands from each player to use for hud stats
        self.hud_days  = 90        # Max number of days from each player to use for hud stats
        self.hud_session_gap = 30  # Gap (minutes) between hands that indicates a change of session
                                   # (hands every 2 mins for 1 hour = one session, if followed
                                   # by a 40 minute gap and then more hands on same table that is
                                   # a new session)
        cur = self.connection.cursor()

        self.hand_1day_ago = 0
        cur.execute(self.sql.query['get_hand_1day_ago'])
        row = cur.fetchone()
        if row and row[0]:
            self.hand_1day_ago = row[0]
        #print "hand 1day ago =", self.hand_1day_ago

        d = timedelta(days=self.hud_days)
        now = datetime.utcnow() - d
        self.date_ndays_ago = "d%02d%02d%02d" % (now.year-2000, now.month, now.day)

        self.hand_nhands_ago = 0  # todo
        #cur.execute(self.sql.query['get_table_name'], (hand_id, ))
        #row = cur.fetchone()

    def close_connection(self):
        self.connection.close()
        
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
        cards = {} # dict of cards, the key is the seat number example: {1: 'AcQd9hTs5d'}
        c = self.connection.cursor()
        c.execute(self.sql.query['get_cards'], [hand])
        colnames = [desc[0] for desc in c.description]
        cardnames = ['card1', 'card2', 'card3', 'card4', 'card5', 'card6', 'card7']
        for row in c.fetchall():
            cs = ['', '', '', '', '', '', '']
            seat = -1
            for col,name in enumerate(colnames):
                if name in cardnames:
                    cs[cardnames.index(name)] = Card.valueSuitFromCard(row[col])
                elif name == 'seat_number':
                    seat = row[col]
            if seat != -1:
                cards[seat] = ''.join(cs)
        return cards

    def get_common_cards(self, hand):
        """Get and return the community cards for the specified hand."""
        cards = {}
        c = self.connection.cursor()
        c.execute(self.sql.query['get_common_cards'], (hand,))
        colnames = [desc[0] for desc in c.description]
        for row in c.fetchall():
            s_dict = {}
            for name, val in zip(colnames, row):
                s_dict[name] = val
            cards['common'] = (self.convert_cards(s_dict))
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
        c.execute(self.sql.query['get_action_from_hand'], (hand_no, ))
        for row in c.fetchall():
            street = row[0]
            act = row[1:]
            action[street].append(act)
        return action

    def get_winners_from_hand(self, hand):
        """Returns a hash of winners:amount won, given a hand number."""
        winners = {}
        c = self.connection.cursor()
        c.execute(self.sql.query['get_winners_from_hand'], (hand, ))
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
    
    hero = db_connection.get_player_id(c, 'Full Tilt Poker', 'PokerAscetic')
    print "nutOmatic is id_player = %d" % hero
    
    stat_dict = db_connection.get_stats_from_hand(h)
    for p in stat_dict.keys():
        print p, "  ", stat_dict[p]
        
#    print "nutOmatics stats:"
#    stat_dict = db_connection.get_stats_from_hand(h, hero)
#    for p in stat_dict.keys():
#        print p, "  ", stat_dict[p]

    print "cards =", db_connection.get_cards(u'1')
    db_connection.close_connection

    print "press enter to continue"
    sys.stdin.readline()
