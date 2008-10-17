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
import Queue

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

def process_new_hand(new_hand_id, db_name):
#    there is a new hand_id to be processed
#    read the hand_id from stdin and strip whitespace
    global hud_dict

    for h in hud_dict.keys():
        if hud_dict[h].deleted:
            del(hud_dict[h])

    db_connection = Database.Database(config, db_name, 'temp')
    (table_name, max, poker_game) = db_connection.get_table_name(new_hand_id)
#    if a hud for this table exists, just update it
    if hud_dict.has_key(table_name):
        hud_dict[table_name].update(new_hand_id, db_connection, config)
#    otherwise create a new hud
    else:
        table_windows = Tables.discover(config)
        for t in table_windows.keys():
            if table_windows[t].name == table_name:
                hud_dict[table_name] = Hud.Hud(table_windows[t], max, poker_game, config, db_name)
                hud_dict[table_name].create(new_hand_id, config)
                hud_dict[table_name].update(new_hand_id, db_connection, config)
                break
#        print "table name \"%s\" not identified, no hud created" % (table_name)
    db_connection.close_connection()
    return(1)  

def check_stdin(db_name):
    try:
        hand_no = dataQueue.get(block=False)
        process_new_hand(hand_no, db_name)
    except:
        pass
    return True

def read_stdin(source, condition, db_name):
    new_hand_id = sys.stdin.readline()
    if new_hand_id == "":
        destroy()
    process_new_hand(new_hand_id, db_name)
    return True

def producer():            # This is the thread function
    while True:
        hand_no = sys.stdin.readline()  # reads stdin
        if hand_no == "":
            destroy()
        dataQueue.put(hand_no)          # and puts result on the queue

if __name__== "__main__":
    sys.stderr.write("HUD_main starting\n")

    try:
        db_name = sys.argv[1]
    except:
        db_name = 'fpdb'
    sys.stderr.write("Using db name = %s\n" % (db_name))

    config = Configuration.Config()
#    db_connection = Database.Database(config, 'fpdb', 'holdem')

    if os.name == 'posix':
        s_id = gobject.io_add_watch(sys.stdin, gobject.IO_IN, read_stdin, db_name)
    elif os.name == 'nt':
        dataQueue = Queue.Queue()             # shared global. infinite size
        gobject.threads_init()                # this is required
        thread.start_new_thread(producer, ()) # starts the thread
        gobject.timeout_add(1000, check_stdin, db_name)
    else:
        print "Sorry your operating system is not supported."
        sys.exit()

    main_window = gtk.Window()
    main_window.connect("destroy", destroy)
    label = gtk.Label('Closing this window will exit from the HUD.')
    main_window.add(label)
    main_window.set_title("HUD Main Window")
    main_window.show_all()
    
    gtk.main()
