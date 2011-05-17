#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Copyright 2009-2011 Eric Blade
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU Affero General Public License as published by
#the Free Software Foundation, version 3 of the License.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU Affero General Public License
#along with this program. If not, see <http://www.gnu.org/licenses/>.
#In the "official" distribution you can find the license in agpl-3.0.txt.

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
    sys.stderr.write(_("HUD_main starting"))

    try:
        HUD_main.db_name = sys.argv[1]
    except:
        HUD_main.db_name = 'fpdb'
    sys.stderr.write(_("Using db name = %s") % (HUD_main.db_name))

    HUD_main.config = Configuration.Config()

    gobject.threads_init()                # this is required
    hud = HUD_main.HUD_main()
    thread.start_new_thread(hud.read_stdin, ()) # starts the thread

    HUD_main.main_window = gtk.Window()
    HUD_main.main_window.connect("destroy", destroy)
    HUD_main.eb = gtk.VBox()
    label = gtk.Label(_('Closing this window will exit from the HUD.'))
    HUD_main.eb.add(label)
    HUD_main.main_window.add(HUD_main.eb)

    HUD_main.main_window.set_title(_("HUD Main Window"))
    HUD_main.main_window.show_all()
    
    gtk.main()
