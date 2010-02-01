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

(options, argv) = Options.fpdb_options()

if not options.errorsToConsole:
    print "Note: error output is being logged. Any major error will be reported there _only_."

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

log = Configuration.get_logger("logging.conf", config = 'hud')
log.debug("%s logger initialized." % "hud")


import Database
from HandHistoryConverter import getTableTitleRe
#    get the correct module for the current os
if os.name == 'posix':
    import XTables as Tables
elif os.name == 'nt':
    import WinTables as Tables
#import Tables
import Hud


class HUD_main(object):
    """A main() object to own both the read_stdin thread and the gui."""
#    This class mainly provides state for controlling the multiple HUDs.

    def __init__(self, db_name = 'fpdb'):
        try:
            print "HUD_main: starting ..."
            self.db_name = db_name
            self.config = Configuration.Config(file=options.config, dbname=options.dbname)
            log = Configuration.get_logger("logging.conf", "hud", log_dir=self.config.dir_log)
            log.debug("starting ...")
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
        except:
            log.debug("commit "+str(i)+" failed: info=" + str(sys.exc_info())
                          + " value=" + str(sys.exc_value))


    def destroy(self, *args):             # call back for terminating the main eventloop
        log.info("Terminating normally.")
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
            try:
                table.gdkhandle = gtk.gdk.window_foreign_new(table.number)
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
            except:
                print "*** Exception in HUD_main::idle_func() *** "
                traceback.print_stack()
            finally:
                gtk.gdk.threads_leave()
                return False

        self.hud_dict[table_name] = Hud.Hud(self, table, max, poker_game, self.config, self.db_connection)
        self.hud_dict[table_name].table_name = table_name
        self.hud_dict[table_name].stat_dict = stat_dict
        self.hud_dict[table_name].cards = cards

        # set agg_bb_mult so that aggregate_tour and aggregate_ring can be ignored,
        # agg_bb_mult == 1 means no aggregation after these if statements:
        if type == "tour" and self.hud_params['aggregate_tour'] == False:
            self.hud_dict[table_name].hud_params['agg_bb_mult'] = 1
        elif type == "ring" and self.hud_params['aggregate_ring'] == False:
            self.hud_dict[table_name].hud_params['agg_bb_mult'] = 1
        if type == "tour" and self.hud_params['h_aggregate_tour'] == False:
            self.hud_dict[table_name].hud_params['h_agg_bb_mult'] = 1
        elif type == "ring" and self.hud_params['h_aggregate_ring'] == False:
            self.hud_dict[table_name].hud_params['h_agg_bb_mult'] = 1
        # sqlcoder: I forget why these are set to true (aren't they ignored from now on?)
        # but I think it's needed:
        self.hud_params['aggregate_ring'] = True
        self.hud_params['h_aggregate_ring'] = True
        # so maybe the tour ones should be set as well? does this fix the bug I see mentioned?
        self.hud_params['aggregate_tour'] = True
        self.hud_params['h_aggregate_tour'] = True

        [aw.update_data(new_hand_id, self.db_connection) for aw in self.hud_dict[table_name].aux_windows]
        gobject.idle_add(idle_func)

    def update_HUD(self, new_hand_id, table_name, config):
        """Update a HUD gui from inside the non-gui read_stdin thread."""
#    This is written so that only 1 thread can touch the gui--mainly
#    for compatibility with Windows. This method dispatches the
#    function idle_func() to be run by the gui thread, at its leisure.
        def idle_func():
            gtk.gdk.threads_enter()
            try:
                self.hud_dict[table_name].update(new_hand_id, config)
            # The HUD could get destroyed in the above call ^^, which leaves us with a KeyError here vv
            # if we ever get an error we need to expect ^^ then we need to handle it vv - Eric
                [aw.update_gui(new_hand_id) for aw in self.hud_dict[table_name].aux_windows]
            except KeyError:
                pass
            finally:
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
            t0 = time.time()
            t1 = t2 = t3 = t4 = t5 = t6 = t0
            new_hand_id = string.rstrip(new_hand_id)
            log.debug("Received hand no %s" % new_hand_id)
            if new_hand_id == "":           # blank line means quit
                self.destroy()
                break # this thread is not always killed immediately with gtk.main_quit()

#        get basic info about the new hand from the db
#        if there is a db error, complain, skip hand, and proceed
            log.info("HUD_main.read_stdin: hand processing starting ...")
            try:
                (table_name, max, poker_game, type, site_id, site_name, num_seats, tour_number, tab_number) = \
                                self.db_connection.get_table_info(new_hand_id)
            except Exception, err:
                log.error("db error: skipping %s" % new_hand_id)
                continue
            t1 = time.time()

            if type == "tour":   # hand is from a tournament
                temp_key = tour_number
            else:
                temp_key = table_name

#        Update an existing HUD
            if temp_key in self.hud_dict:
                # get stats using hud's specific params and get cards
                self.db_connection.init_hud_stat_vars( self.hud_dict[temp_key].hud_params['hud_days']
                                                     , self.hud_dict[temp_key].hud_params['h_hud_days'])
                t2 = time.time()
                stat_dict = self.db_connection.get_stats_from_hand(new_hand_id, type, self.hud_dict[temp_key].hud_params
                                                                  ,self.hero_ids[site_id], num_seats)
                t3 = time.time()
                try:
                    self.db_connection.init_hud_stat_vars( self.hud_dict[temp_key].hud_params['hud_days']
                                                     , self.hud_dict[temp_key].hud_params['h_hud_days'])
                    t4 = time.time()
                    stat_dict = self.db_connection.get_stats_from_hand(new_hand_id, type, self.hud_dict[temp_key].hud_params, self.hero_ids[site_id])
                    self.hud_dict[temp_key].stat_dict = stat_dict
                except KeyError:    # HUD instance has been killed off, key is stale
                    sys.stderr.write('hud_dict[%s] was not found\n' % temp_key)
                    sys.stderr.write('will not send hand\n')
                    # Unlocks table, copied from end of function
                    self.db_connection.connection.rollback()
                    return
                t5 = time.time()
                cards      = self.db_connection.get_cards(new_hand_id)
                comm_cards = self.db_connection.get_common_cards(new_hand_id)
                if comm_cards != {}: # stud!
                    cards['common'] = comm_cards['common']
                self.hud_dict[temp_key].cards = cards
                [aw.update_data(new_hand_id, self.db_connection) for aw in self.hud_dict[temp_key].aux_windows]
                self.update_HUD(new_hand_id, temp_key, self.config)

#        Or create a new HUD
            else:
                # get stats using default params--also get cards
                self.db_connection.init_hud_stat_vars( self.hud_params['hud_days'], self.hud_params['h_hud_days'] )
                stat_dict = self.db_connection.get_stats_from_hand(new_hand_id, type, self.hud_params
                                                                  ,self.hero_ids[site_id], num_seats)
                cards      = self.db_connection.get_cards(new_hand_id)
                comm_cards = self.db_connection.get_common_cards(new_hand_id)
                if comm_cards != {}: # stud!
                    cards['common'] = comm_cards['common']

                table_kwargs = dict(table_name = table_name, tournament = tour_number, table_number = tab_number)
                search_string = getTableTitleRe(self.config, site, type, **table_kwargs)
                tablewindow = Tables.Table(search_string, **table_kwargs)

                if tablewindow is None:
#        If no client window is found on the screen, complain and continue
                    if type == "tour":
                        table_name = "%s %s" % (tour_number, tab_number)
#                    sys.stderr.write("HUD create: table name "+table_name+" not found, skipping.\n")
                    log.error("HUD create: table name %s not found, skipping." % table_name)
                else:
                    tablewindow.max = max
                    tablewindow.site = site_name
                    # Test that the table window still exists
                    if hasattr(tablewindow, 'number'):
                        self.create_HUD(new_hand_id, tablewindow, temp_key, max, poker_game, type, stat_dict, cards)
                    else:
                        sys.stderr.write('Table "%s" no longer exists\n' % table_name)

            t6 = time.time()
            log.info("HUD_main.read_stdin: hand read in %4.3f seconds (%4.3f,%4.3f,%4.3f,%4.3f,%4.3f,%4.3f)"
                     % (t6-t0,t1-t0,t2-t0,t3-t0,t4-t0,t5-t0,t6-t0))
            self.db_connection.connection.rollback()

if __name__== "__main__":

    log.info("HUD_main starting")
    log.info("Using db name = %s" % (options.dbname))

#    start the HUD_main object
    hm = HUD_main(db_name = options.dbname)

#    start the event loop
    gtk.main()
