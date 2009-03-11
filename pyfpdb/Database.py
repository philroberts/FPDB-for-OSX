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

#    pyGTK modules

#    FreePokerTools modules
import Configuration
import SQL

class Database:
    def __init__(self, c, db_name, game):
        if   c.supported_databases[db_name].db_server == 'postgresql':
            #    psycopg2 database module for posgres via DB-API
            import psycopg2

            try:
                self.connection = psycopg2.connect(host = c.supported_databases[db_name].db_ip,
                                       user = c.supported_databases[db_name].db_user,
                                       password = c.supported_databases[db_name].db_pass,
                                       database = c.supported_databases[db_name].db_name)
            except:
                print "Error opening database connection %s.  See error log file." % (file)
                traceback.print_exc(file=sys.stderr)
                print "press enter to continue"
                sys.stdin.readline()
                sys.exit()

        elif c.supported_databases[db_name].db_server == 'mysql':
            #    mysql bindings
            import MySQLdb
            try:
                self.connection = MySQLdb.connect(host = c.supported_databases[db_name].db_ip,
                                       user = c.supported_databases[db_name].db_user,
                                       passwd = c.supported_databases[db_name].db_pass,
                                       db = c.supported_databases[db_name].db_name)
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

        self.type = c.supported_databases[db_name].db_type
        self.sql = SQL.Sql(game = game, type = self.type)
        
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
        c.execute(self.sql.query['get_cards'], hand)
        colnames = [desc[0] for desc in c.description]
        for row in c.fetchall():
            s_dict = {}
            for name, val in zip(colnames, row):
                s_dict[name] = val
            cards[s_dict['seat_number']] = (self.convert_cards(s_dict))
        return cards

    def get_common_cards(self, hand):
        """Get and return the community cards for the specified hand."""
        cards = {}
        c = self.connection.cursor()
        c.execute(self.sql.query['get_common_cards'], hand)
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
            cv = "card%dValue" % i
            if cv not in d:
                break
            elif d[cv] == 0 or d[cv] == None:
                cards = "%sxx" % cards
            else:
                cs = "card%dSuit" % i
                cards = "%s%s%s" % (cards, ranks[d[cv]], d[cs])
        return cards

    def get_action_from_hand(self, hand_no):
        action = [ [], [], [], [], [] ]
        c = self.connection.cursor()
        c.execute(self.sql.query['get_action_from_hand'], (hand_no))
        for row in c.fetchall():
            street = row[0]
            act = row[1:]
            action[street].append(act)
        return action

    def get_winners_from_hand(self, hand):
        """Returns a hash of winners:amount won, given a hand number."""
        winners = {}
        c = self.connection.cursor()
        c.execute(self.sql.query['get_winners_from_hand'], (hand))
        for row in c.fetchall():
            winners[row[0]] = row[1]
        return winners

    def get_stats_from_hand(self, hand, aggregate = False):
        c = self.connection.cursor()

        if aggregate:
            query = 'get_stats_from_hand_aggregated'
            subs = (hand, hand, hand)
        else:
            query = 'get_stats_from_hand'
            subs = (hand, hand)

#    now get the stats
        c.execute(self.sql.query[query], subs)
        colnames = [desc[0] for desc in c.description]
        stat_dict = {}
        for row in c.fetchall():
            t_dict = {}
            for name, val in zip(colnames, row):
                t_dict[name] = val
            stat_dict[t_dict['player_id']] = t_dict
        return stat_dict
            
    def get_player_id(self, config, site, player_name):
        print "site  = %s, player name = %s" % (site, player_name)
        c = self.connection.cursor()
        c.execute(self.sql.query['get_player_id'], {'player': player_name, 'site': site})
        row = c.fetchone()
        return row[0]

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
    print "nutOmatic is id_player = %d" % hero
    
    stat_dict = db_connection.get_stats_from_hand(h)
    for p in stat_dict.keys():
        print p, "  ", stat_dict[p]
        
    print "nutOmatics stats:"
    stat_dict = db_connection.get_stats_from_hand(h, hero)
    for p in stat_dict.keys():
        print p, "  ", stat_dict[p]

    print "cards =", db_connection.get_cards(73525)
    db_connection.close_connection

    print "press enter to continue"
    sys.stdin.readline()
