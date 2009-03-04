#!/usr/bin/env python

"""Hud_main.py

Main for FreePokerTools HUD.
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

#    to do allow window resizing
#    to do hud to echo, but ignore non numbers
#    to do no stat window for hero
#    to do things to add to config.xml

#    Standard Library modules
import sys

#    redirect the stderr
errorfile = open('HUD-error.txt', 'w', 0)
sys.stderr = errorfile

import os
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

class HUD_main(object):
    """A main() object to own both the read_stdin thread and the gui."""
#    This class mainly provides state for controlling the multiple HUDs.

    def __init__(self, db_name = 'fpdb'):
        self.db_name = db_name
        self.config = Configuration.Config()
        self.hud_dict = {}

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
        self.hud_dict[table].kill()
        self.hud_dict[table].main_window.destroy()
        self.vb.remove(self.hud_dict[table].tablehudlabel)
        del(self.hud_dict[table])
        self.main_window.resize(1,1)

    def create_HUD(self, new_hand_id, table, table_name, max, poker_game, is_tournament, stat_dict, cards):
        
        def idle_func():
            
            gtk.gdk.threads_enter()
            try:
                newlabel = gtk.Label(table.site + " - " + table_name)
                self.vb.add(newlabel)
                newlabel.show()
                self.main_window.resize_children()
    
                self.hud_dict[table_name].tablehudlabel = newlabel
                self.hud_dict[table_name].create(new_hand_id, self.config, stat_dict, cards)
                for m in self.hud_dict[table_name].aux_windows:
                    m.update_data(new_hand_id, self.db_connection)
                    m.update_gui(new_hand_id)
                self.hud_dict[table_name].update(new_hand_id, self.config)
                self.hud_dict[table_name].reposition_windows()
                return False
            finally:
                gtk.gdk.threads_leave()

        self.hud_dict[table_name] = Hud.Hud(self, table, max, poker_game, self.config, self.db_connection)
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
                for m in self.hud_dict[table_name].aux_windows:
                    m.update_gui(new_hand_id)
                return False
            finally:
                gtk.gdk.threads_leave()
        gobject.idle_add(idle_func)
     
    def read_stdin(self):            # This is the thread function
        """Do all the non-gui heavy lifting for the HUD program."""

#    This db connection is for the read_stdin thread only. It should not
#    be passed to HUDs for use in the gui thread. HUD objects should not
#    need their own access to the database, but should open their own
#    if it is required.
        self.db_connection = Database.Database(self.config, self.db_name, 'temp')
        tourny_finder = re.compile('(\d+) (\d+)')
    
        while True: # wait for a new hand number on stdin
            new_hand_id = sys.stdin.readline()
            new_hand_id = string.rstrip(new_hand_id)
            if new_hand_id == "":           # blank line means quit
                self.destroy()
                break # this thread is not always killed immediately with gtk.main_quit()
    
#    get basic info about the new hand from the db
#    if there is a db error, complain, skip hand, and proceed
            try:
                (table_name, max, poker_game) = self.db_connection.get_table_name(new_hand_id)
                stat_dict = self.db_connection.get_stats_from_hand(new_hand_id)
                cards = self.db_connection.get_cards(new_hand_id)
            except:
                print "skipping ", new_hand_id
                sys.stderr.write("Database error in hand %d. Skipping.\n" % int(new_hand_id))
                continue

#    find out if this hand is from a tournament
            mat_obj = tourny_finder.search(table_name)
            if mat_obj:
                is_tournament = True
                (tour_number, tab_number) = mat_obj.group(1, 2)
                temp_key = tour_number
            else:
                is_tournament = False
                (tour_number, tab_number) = (0, 0)
                temp_key = table_name

#    Update an existing HUD
            if temp_key in self.hud_dict:
                self.hud_dict[temp_key].stat_dict = stat_dict
                self.hud_dict[temp_key].cards = cards
                for aw in self.hud_dict[temp_key].aux_windows:
                    aw.update_data(new_hand_id, self.db_connection)
                self.update_HUD(new_hand_id, temp_key, self.config)
    
#    Or create a new HUD
            else:
                if is_tournament:
                    tablewindow = Tables.discover_tournament_table(self.config, tour_number, tab_number)
                else:
                    tablewindow = Tables.discover_table_by_name(self.config, table_name)

                if tablewindow == None:
#    If no client window is found on the screen, complain and continue
                    if is_tournament:
                        table_name = tour_number + " " + tab_number
                    sys.stderr.write("table name "+table_name+" not found, skipping.\n")
                else:
                    self.create_HUD(new_hand_id, tablewindow, temp_key, max, poker_game, is_tournament, stat_dict, cards)

if __name__== "__main__":
    sys.stderr.write("HUD_main starting\n")

#    database name can be passed on command line
    try:
        db_name = sys.argv[1]
    except:
        db_name = 'fpdb'
    sys.stderr.write("Using db name = %s\n" % (db_name))

#    start the HUD_main object
    hm = HUD_main(db_name = db_name)

#    start the event loop
    gtk.main()
