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

#    to do kill window on my seat
#    to do adjust for preferred seat
#    to do allow window resizing
#    to do hud to echo, but ignore non numbers
#    to do no hud window for hero
#    to do things to add to config.xml
#    to do     font and size
#    to do     bg and fg color
#    to do     opacity

#    Standard Library modules
import sys
import os
import thread
import time
import string

errorfile = open('HUD-error.txt', 'w', 0)
sys.stderr = errorfile

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

db_connection = 0;
config = 0;

def destroy(*args):             # call back for terminating the main eventloop
    gtk.main_quit()

def create_HUD(new_hand_id, table, db_name, table_name, max, poker_game, db_connection, config, stat_dict):
    global hud_dict
    def idle_func():
        global hud_dict
        gtk.gdk.threads_enter()
        try:
            hud_dict[table_name] = Hud.Hud(table, max, poker_game, config, db_name)
            hud_dict[table_name].create(new_hand_id, config)
            hud_dict[table_name].update(new_hand_id, config, stat_dict)
            return False
        finally:
            gtk.gdk.threads_leave
    gobject.idle_add(idle_func)

def update_HUD(new_hand_id, table_name, config, stat_dict):
    global hud_dict
    def idle_func():
        gtk.gdk.threads_enter()
        try:
            hud_dict[table_name].update(new_hand_id, config, stat_dict)
            return False
        finally:
            gtk.gdk.threads_leave
    gobject.idle_add(idle_func)

def read_stdin():            # This is the thread function
    global hud_dict

    while True: # wait for a new hand number on stdin
        new_hand_id = sys.stdin.readline()
        new_hand_id = string.rstrip(new_hand_id)
        if new_hand_id == "":           # blank line means quit
            destroy()

#    delete hud_dict entries for any HUD destroyed since last iteration
        for h in hud_dict.keys():
            if hud_dict[h].deleted:
                del(hud_dict[h])

#    connect to the db and get basic info about the new hand
        db_connection = Database.Database(config, db_name, 'temp')
        (table_name, max, poker_game) = db_connection.get_table_name(new_hand_id)
        stat_dict = db_connection.get_stats_from_hand(new_hand_id)
        db_connection.close_connection()

#    if a hud for this table exists, just update it
        if hud_dict.has_key(table_name):
            update_HUD(new_hand_id, table_name, config, stat_dict)
#        otherwise create a new hud
        else:
            table_windows = Tables.discover(config)
            for t in table_windows.keys():
                if table_windows[t].name == table_name:
                    create_HUD(new_hand_id, table_windows[t], db_name, table_name, max, poker_game, db_connection, config, stat_dict)
                    break

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
    label = gtk.Label('Closing this window will exit from the HUD.')
    main_window.add(label)
    main_window.set_title("HUD Main Window")
    main_window.show_all()
    
    gtk.main()
