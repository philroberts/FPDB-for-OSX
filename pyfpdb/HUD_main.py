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
#    to do     font and size

#    Standard Library modules
import sys
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

#    global dict for keeping the huds
hud_dict = {}
eb = 0 # our former event-box

db_connection = 0;
config = 0;

def destroy(*args):             # call back for terminating the main eventloop
    gtk.main_quit()

def create_HUD(new_hand_id, table, db_name, table_name, max, poker_game, db_connection, config, stat_dict):
    global hud_dict, eb
    
    def idle_func():
        global hud_dict, eb
        
        gtk.gdk.threads_enter()
        try:
            newlabel = gtk.Label(table.site + " - " + table_name)
            eb.add(newlabel)
            newlabel.show()

            hud_dict[table_name] = Hud.Hud(table, max, poker_game, config, db_connection)
            hud_dict[table_name].tablehudlabel = newlabel
            hud_dict[table_name].create(new_hand_id, config)
            for m in hud_dict[table_name].aux_windows:
                m.update_data(new_hand_id, db_connection)
                m.update_gui(new_hand_id)
            hud_dict[table_name].update(new_hand_id, config, stat_dict)
            hud_dict[table_name].reposition_windows()
            return False
        finally:
            gtk.gdk.threads_leave()
    gobject.idle_add(idle_func)

def update_HUD(new_hand_id, table_name, config, stat_dict):
    global hud_dict
    def idle_func():
        gtk.gdk.threads_enter()
        try:
            hud_dict[table_name].update(new_hand_id, config, stat_dict)
            for m in hud_dict[table_name].aux_windows:
                m.update_gui(new_hand_id)
            return False
        finally:
            gtk.gdk.threads_leave()
    gobject.idle_add(idle_func)
 
def HUD_removed(tablename):
    global hud_dict, eb
    
    tablename = Tables.clean_title(tablename)
    # TODO: There's a potential problem here somewhere, that this hacks around .. the table_name as being passed to HUD_create is cleaned,
    # but the table.name as being passed here is not cleaned. I don't know why. -eric
    if tablename in hud_dict and hud_dict[tablename].deleted:
        eb.remove(hud_dict[tablename].tablehudlabel)
        del hud_dict[tablename]
        return False
    
    return True

def read_stdin():            # This is the thread function
    global hud_dict, eb

    db_connection = Database.Database(config, db_name, 'temp')
    tourny_finder = re.compile('(\d+) (\d+)')

    while True: # wait for a new hand number on stdin
        new_hand_id = sys.stdin.readline()
        new_hand_id = string.rstrip(new_hand_id)
        if new_hand_id == "":           # blank line means quit
            destroy()
            break # this thread is not always killed immediately with gtk.main_quit()

#    get basic info about the new hand from the db
        (table_name, max, poker_game) = db_connection.get_table_name(new_hand_id)

#    find out if this hand is from a tournament
        is_tournament = False
        (tour_number, tab_number) = (0, 0)
        mat_obj = tourny_finder.search(table_name)
        if mat_obj:
            is_tournament = True
            (tour_number, tab_number) = mat_obj.group(1, 2)
            
        stat_dict = db_connection.get_stats_from_hand(new_hand_id)

#    if a hud for this CASH table exists, just update it
        if table_name in hud_dict:
#    update the data for the aux_windows
            for aw in hud_dict[table_name].aux_windows:
                aw.update_data(new_hand_id, db_connection)
            update_HUD(new_hand_id, table_name, config, stat_dict)

#    if a hud for this TOURNAMENT table exists, just update it
        elif tour_number in hud_dict:
            update_HUD(new_hand_id, tour_number, config, stat_dict)

#    otherwise create a new hud
        else:
            if is_tournament:
                tablewindow = Tables.discover_tournament_table(config, tour_number, tab_number)
                if tablewindow == None:
                    sys.stderr.write("tournament %s,  table %s not found\n" % (tour_number, tab_number))
                else:
                    create_HUD(new_hand_id, tablewindow, db_name, tour_number, max, poker_game, db_connection, config, stat_dict)
            else:
                tablewindow = Tables.discover_table_by_name(config, table_name)
                if tablewindow == None:
                    sys.stderr.write("table name "+table_name+" not found\n")
                else:
                    create_HUD(new_hand_id, tablewindow, db_name, table_name, max, poker_game, db_connection, config, stat_dict)

if __name__== "__main__":
    sys.stderr.write("HUD_main starting\n")

    try:
        db_name = sys.argv[1]
    except:
        db_name = 'fpdb'
    sys.stderr.write("Using db name = %s\n" % (db_name))

    config = Configuration.Config()

    gobject.threads_init()                # this is required
    thread.start_new_thread(read_stdin, ()) # starts the thread

    main_window = gtk.Window()
    main_window.connect("destroy", destroy)
    eb = gtk.VBox()
    label = gtk.Label('Closing this window will exit from the HUD.')
    eb.add(label)
    main_window.add(eb)

    main_window.set_title("HUD Main Window")
    main_window.show_all()
    
    gtk.main()
