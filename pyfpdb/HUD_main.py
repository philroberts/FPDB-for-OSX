#!/usr/bin/env python

"""Hud_main.py

Main for FreePokerTools HUD.
"""
#    Copyright 2008, 2009,  Ray E. Barker
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

#    to do allow window resizing
#    to do hud to echo, but ignore non numbers
#    to do no stat window for hero
#    to do things to add to config.xml

#    Standard Library modules
import sys
import os
import Options
import traceback

(options, sys.argv) = Options.fpdb_options()

if not options.errorsToConsole:
    print "Note: error output is being diverted to fpdb-error-log.txt and HUD-error.txt. Any major error will be reported there _only_."
    errorFile = open('HUD-error.txt', 'w', 0)
    sys.stderr = errorFile

import thread
import time
import string
import re

#    pyGTK modules
import pygtk
import gtk
import gobject

#    FreePokerTools modules
import Configuration
import Database
import Tables
import Hud


# HUD params:
# - Set aggregate_ring and/or aggregate_tour to True is you want to include stats from other blind levels in the HUD display
# - If aggregation is used, the value of agg_bb_mult determines what levels are included. If
#   agg_bb_mult is M and current blind level is L, blinds between L/M and L*M are included. e.g.
#   if agg_bb_mult is 100, almost all levels are included in all HUD displays
#   if agg_bb_mult is 2, levels from half to double the current blind level are included in the HUD
#   if agg_bb_mult is 1 only the current level is included
# - Set hud_style to A to see stats for all-time
#   Set hud_style to S to only see stats for current session (currently this shows stats for the last 24 hours)
#   Set hud_style to T to only see stats for the last N days (uses value in hud_days)
# - Set hud_days to N to see stats for the last N days in the HUD (only applies if hud_style is T)
def_hud_params = { # Settings for all players apart from program owner ('hero')
                   'aggregate_ring' : False
                 , 'aggregate_tour' : True
                 , 'hud_style'      : 'A'
                 , 'hud_days'       : 90
                 , 'agg_bb_mult'    : 10000                 # 1 means no aggregation
                 # , 'hud_session_gap' : 30             not currently used
                   # Second set of variables for hero - these settings only apply to the program owner
                 , 'h_aggregate_ring' : False
                 , 'h_aggregate_tour' : True
                 , 'h_hud_style'      : 'S'             # A(ll) / S(ession) / T(ime in days)
                 , 'h_hud_days'       : 60
                 , 'h_agg_bb_mult'    : 10000               # 1 means no aggregation
                 # , 'h_hud_session_gap' : 30           not currently used
                 }


class HUD_main(object):
    """A main() object to own both the read_stdin thread and the gui."""
#    This class mainly provides state for controlling the multiple HUDs.

    def __init__(self, db_name = 'fpdb'):
        self.db_name = db_name
        self.config = Configuration.Config(file=options.config, dbname=options.dbname)
        self.hud_dict = {}
        self.hud_params = self.config.get_hud_ui_parameters()

#    a thread to read stdin
        gobject.threads_init()                       # this is required
        thread.start_new_thread(self.read_stdin, ()) # starts the thread

#    a main window
        self.main_window = gtk.Window()
        self.main_window.connect("destroy", self.destroy)
        self.vb = gtk.VBox()
        self.label = gtk.Label('Closing this window will exit from the HUD.')
        self.vb.add(self.label)
        self.main_window.add(self.vb)
        self.main_window.set_title("HUD Main Window")
        self.main_window.show_all()

    def destroy(*args):             # call back for terminating the main eventloop
        gtk.main_quit()

    def kill_hud(self, event, table):
#    called by an event in the HUD, to kill this specific HUD
        if table in self.hud_dict:
            self.hud_dict[table].kill()
            self.hud_dict[table].main_window.destroy()
            self.vb.remove(self.hud_dict[table].tablehudlabel)
            del(self.hud_dict[table])
        self.main_window.resize(1,1)

    def create_HUD(self, new_hand_id, table, table_name, max, poker_game, type, stat_dict, cards):
        """type is "ring" or "tour" used to set hud_params"""
        
        def idle_func():
            
            gtk.gdk.threads_enter()
            try: # TODO: seriously need to decrease the scope of this block.. what are we expecting to error?
                 # TODO: The purpose of this try/finally block is to make darn sure that threads_leave()
                 # TODO: gets called. If there is an exception and threads_leave() doesn't get called we 
                 # TODO: lock up.  REB
                newlabel = gtk.Label("%s - %s" % (table.site, table_name))
                self.vb.add(newlabel)
                newlabel.show()
                self.main_window.resize_children()
    
                self.hud_dict[table_name].tablehudlabel = newlabel
                self.hud_dict[table_name].create(new_hand_id, self.config, stat_dict, cards)
                for m in self.hud_dict[table_name].aux_windows:
                    m.create()
                    m.update_gui(new_hand_id)
                self.hud_dict[table_name].update(new_hand_id, self.config)
                self.hud_dict[table_name].reposition_windows()
                return False
            finally:
                gtk.gdk.threads_leave()

        self.hud_dict[table_name] = Hud.Hud(self, table, max, poker_game, self.config, self.db_connection)
        self.hud_dict[table_name].table_name = table_name
        self.hud_dict[table_name].stat_dict = stat_dict
        self.hud_dict[table_name].cards = cards

        if type == "tour" and self.hud_params['aggregate_tour'] == False:
            self.hud_dict[table_name].hud_params['agg_bb_mult'] = 1
        elif type == "ring" and self.hud_params['aggregate_ring'] == False:
            self.hud_dict[table_name].hud_params['agg_bb_mult'] = 1
        if type == "tour" and self.hud_params['h_aggregate_tour'] == False:
            self.hud_dict[table_name].hud_params['h_agg_bb_mult'] = 1
        elif type == "ring" and self.hud_params['h_aggregate_ring'] == False:
            self.hud_dict[table_name].hud_params['h_agg_bb_mult'] = 1
        self.hud_params['aggregate_ring'] == True
        self.hud_params['h_aggregate_ring'] == True

        [aw.update_data(new_hand_id, self.db_connection) for aw in self.hud_dict[table_name].aux_windows]
        gobject.idle_add(idle_func)
    
    def update_HUD(self, new_hand_id, table_name, config):
        """Update a HUD gui from inside the non-gui read_stdin thread."""
#    This is written so that only 1 thread can touch the gui--mainly
#    for compatibility with Windows. This method dispatches the 
#    function idle_func() to be run by the gui thread, at its leisure.
        def idle_func():
            gtk.gdk.threads_enter()
#            try: 
            self.hud_dict[table_name].update(new_hand_id, config)
            [aw.update_gui(new_hand_id) for aw in self.hud_dict[table_name].aux_windows]
#            finally:
            gtk.gdk.threads_leave()
            return False
                
        gobject.idle_add(idle_func)
     
    def read_stdin(self):            # This is the thread function
        """Do all the non-gui heavy lifting for the HUD program."""

#    This db connection is for the read_stdin thread only. It should not
#    be passed to HUDs for use in the gui thread. HUD objects should not
#    need their own access to the database, but should open their own
#    if it is required.
        self.db_connection = Database.Database(self.config)
        tourny_finder = re.compile('(\d+) (\d+)')
        
#       get hero's screen names and player ids
        self.hero, self.hero_ids = {}, {}
        for site in self.config.get_supported_sites():
            result = self.db_connection.get_site_id(site)
            if result:
                site_id = result[0][0]
                self.hero[site_id] = self.config.supported_sites[site].screen_name
                self.hero_ids[site_id] = self.db_connection.get_player_id(self.config, site, self.hero[site_id])
    
        while 1: # wait for a new hand number on stdin
            new_hand_id = sys.stdin.readline()
            new_hand_id = string.rstrip(new_hand_id)
            if new_hand_id == "":           # blank line means quit
                self.destroy()
                break # this thread is not always killed immediately with gtk.main_quit()
#        get basic info about the new hand from the db
#        if there is a db error, complain, skip hand, and proceed
            try:
                (table_name, max, poker_game, type, site_id) = self.db_connection.get_table_name(new_hand_id)

                cards      = self.db_connection.get_cards(new_hand_id)
                comm_cards = self.db_connection.get_common_cards(new_hand_id)
                if comm_cards != {}: # stud!
                    cards['common'] = comm_cards['common']
            except Exception, err:
                err = traceback.extract_tb(sys.exc_info()[2])[-1]
                print "db error: skipping "+str(new_hand_id)+" "+err[2]+"("+str(err[1])+"): "+str(sys.exc_info()[1])
                if new_hand_id: # new_hand_id is none if we had an error prior to the store
                    sys.stderr.write("Database error %s in hand %d. Skipping.\n" % (err, int(new_hand_id)))
                continue

            if type == "tour":   # hand is from a tournament
                mat_obj = tourny_finder.search(table_name)
                if mat_obj:
                    (tour_number, tab_number) = mat_obj.group(1, 2)
                    temp_key = tour_number
                else:   # tourney, but can't get number and table
                    print "could not find tournament: skipping "
                    #sys.stderr.write("Could not find tournament %d in hand %d. Skipping.\n" % (int(tour_number), int(new_hand_id)))
                    continue
                    
            else:
                temp_key = table_name

#        Update an existing HUD
            if temp_key in self.hud_dict:
                try:
                    # get stats using hud's specific params
                    self.db_connection.init_hud_stat_vars( self.hud_dict[temp_key].hud_params['hud_days']
                                                         , self.hud_dict[temp_key].hud_params['h_hud_days'])
                    stat_dict = self.db_connection.get_stats_from_hand(new_hand_id, type, self.hud_dict[temp_key].hud_params, self.hero_ids[site_id])
                except:
                    err = traceback.extract_tb(sys.exc_info()[2])[-1]
                    print "db get_stats error: skipping "+str(new_hand_id)+" "+err[2]+"("+str(err[1])+"): "+str(sys.exc_info()[1])
                    if new_hand_id: # new_hand_id is none if we had an error prior to the store
                        sys.stderr.write("Database get_stats error %s in hand %d. Skipping.\n" % (err, int(new_hand_id)))
                    continue
                self.hud_dict[temp_key].stat_dict = stat_dict
                self.hud_dict[temp_key].cards = cards
                [aw.update_data(new_hand_id, self.db_connection) for aw in self.hud_dict[temp_key].aux_windows]
                self.update_HUD(new_hand_id, temp_key, self.config)
    
#        Or create a new HUD
            else:
                try:
                    # get stats using default params
                    self.db_connection.init_hud_stat_vars( self.hud_params['hud_days'], self.hud_params['h_hud_days'] )
                    stat_dict = self.db_connection.get_stats_from_hand(new_hand_id, type, self.hud_params, self.hero_ids[site_id])
                except:
                    err = traceback.extract_tb(sys.exc_info()[2])[-1]
                    print "db get_stats error: skipping "+str(new_hand_id)+" "+err[2]+"("+str(err[1])+"): "+str(sys.exc_info()[1])
                    if new_hand_id: # new_hand_id is none if we had an error prior to the store
                        sys.stderr.write("Database get_stats error %s in hand %d. Skipping.\n" % (err, int(new_hand_id)))
                    continue
                if type == "tour":
                    tablewindow = Tables.discover_tournament_table(self.config, tour_number, tab_number)
                else:
                    tablewindow = Tables.discover_table_by_name(self.config, table_name)
                if tablewindow is None:
#        If no client window is found on the screen, complain and continue
                    if type == "tour":
                        table_name = "%s %s" % (tour_number, tab_number)
                    sys.stderr.write("HUD create: table name "+table_name+" not found, skipping.\n")
                else:
                    self.create_HUD(new_hand_id, tablewindow, temp_key, max, poker_game, type, stat_dict, cards)
            self.db_connection.connection.rollback()

if __name__== "__main__":

    sys.stderr.write("HUD_main starting\n")
    sys.stderr.write("Using db name = %s\n" % (options.dbname))

#    start the HUD_main object
    hm = HUD_main(db_name = options.dbname)

#    start the event loop
    gtk.main()
