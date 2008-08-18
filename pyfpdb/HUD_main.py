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
#    to do kill a hud
#    to do no hud window for hero
#    to do single click to display detailed stats
#    to do things to add to config.xml
#    to do     font and size

#    Standard Library modules
import sys
import os

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
    
def process_new_hand(source, condition):
#    there is a new hand_id to be processed
#    read the hand_id from stdin and strip whitespace
    new_hand_id = sys.stdin.readline()
    new_hand_id = new_hand_id.rstrip()
    db_connection = Database.Database(config, 'fpdb', 'holdem')

    (table_name, max, poker_game) = db_connection.get_table_name(new_hand_id)
#    if a hud for this table exists, just update it
    if hud_dict.has_key(table_name):
        hud_dict[table_name].update(new_hand_id, db_connection, config)
#    otherwise create a new hud
    else:
        table_windows = Tables.discover(config)
        for t in table_windows.keys():
            if table_windows[t].name == table_name:
                hud_dict[table_name] = Hud.Hud(table_windows[t], max, poker_game, config, db_connection)
                hud_dict[table_name].create(new_hand_id, config)
                hud_dict[table_name].update(new_hand_id, db_connection, config)
                break
#        print "table name \"%s\" not identified, no hud created" % (table_name)
    return(1)

if __name__== "__main__":
    
    if not os.name == 'posix':
        print "This version of the HUD only works with Linux or compatible.\nHUD exiting."
        sys.exit()

    main_window = gtk.Window()
    main_window.connect("destroy", destroy)
    label = gtk.Label('Fake main window, blah blah, blah\nblah, blah')
    main_window.add(label)
    main_window.show_all()
    
    config = Configuration.Config()
    
    db_connection = Database.Database(config, 'fpdb', 'holdem')
    
    s_id = gobject.io_add_watch(sys.stdin, gobject.IO_IN, process_new_hand)

    gtk.main()
