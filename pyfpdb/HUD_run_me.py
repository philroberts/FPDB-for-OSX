#!/usr/bin/env python
import sys
import os
import thread
import time
import string
import re

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
import HUD_main

def destroy(*args):             # call back for terminating the main eventloop
    gtk.main_quit()


if __name__== "__main__":
    sys.stderr.write("HUD_main starting\n")

    try:
        HUD_main.db_name = sys.argv[1]
    except:
        HUD_main.db_name = 'fpdb'
    sys.stderr.write("Using db name = %s\n" % (HUD_main.db_name))

    HUD_main.config = Configuration.Config()

    gobject.threads_init()                # this is required
    hud = HUD_main.HUD_main()
    thread.start_new_thread(hud.read_stdin, ()) # starts the thread

    HUD_main.main_window = gtk.Window()
    HUD_main.main_window.connect("destroy", destroy)
    HUD_main.eb = gtk.VBox()
    label = gtk.Label('Closing this window will exit from the HUD.')
    HUD_main.eb.add(label)
    HUD_main.main_window.add(HUD_main.eb)

    HUD_main.main_window.set_title("HUD Main Window")
    HUD_main.main_window.show_all()
    
    gtk.main()
