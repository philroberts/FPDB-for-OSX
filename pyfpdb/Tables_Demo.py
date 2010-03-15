#!/usr/bin/env python
"""Tables_Demo.py

Main program module to test/demo the Tables subclasses.
"""
#    Copyright 2008 - 2009, Ray E. Barker

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

#    Standard Library modules
import sys
import os
import re

#    pyGTK modules
import pygtk
import gtk
import gobject

#    fpdb/free poker tools modules
import Configuration
from HandHistoryConverter import getTableTitleRe

#    get the correct module for the current os
if os.name == 'posix':
    import XTables as Tables
elif os.name == 'nt':
    import WinTables as Tables

config = Configuration.Config()
#   Main function used for testing
if __name__=="__main__":
#    c = Configuration.Config()

    class fake_hud(object):
        def __init__(self, table, dx = 100, dy = 100):
            self.table = table
            self.dx = dx
            self.dy = dy

            self.main_window = gtk.Window()
            self.main_window.connect("destroy", self.client_destroyed)
            self.label = gtk.Label('Fake Fake Fake Fake\nFake\nFake\nFake')
            self.main_window.add(self.label)
            self.main_window.set_title("Fake HUD Main Window")
            self.main_window.move(table.x + dx, table.y + dy)
            self.main_window.show_all()
            table.topify(self)
            self.main_window.connect("client_moved", self.client_moved)
            self.main_window.connect("client_resized", self.client_resized)
            self.main_window.connect("client_destroyed", self.client_destroyed)

        def client_moved(self, widget, hud):
            self.main_window.move(self.table.x + self.dx, self.table.y + self.dy)

        def client_resized(self, *args):
            print "client resized"

        def client_destroyed(self, *args): # call back for terminating the main eventloop
            gtk.main_quit()

    def check_on_table(table, hud):
        result = table.check_geometry()
        if result != False:
            hud.main_window.emit(result, hud)
        return True

    print "enter table name to find: ",
    table_name = sys.stdin.readline()
    if "," in table_name:  # tournament
        print "tournament"
        (tour_no, tab_no) = table_name.split(",", 1)
        tour_no = tour_no.rstrip()
        tab_no = tab_no.rstrip()
        type = "tour"
        table_kwargs = dict(tournament = tour_no, table_number = tab_no)
    else:   # not a tournament
        print "cash game"
        table_name = table_name.rstrip()
        type = "cash"
        table_kwargs = dict(table_name = table_name)

    search_string = getTableTitleRe(config, "Full Tilt Poker", type, **table_kwargs)
    table = Tables.Table(search_string, **table_kwargs)
    table.gdk_handle = gtk.gdk.window_foreign_new(table.number)

    print "table =", table
#    print "game =", table.get_game()

    fake = fake_hud(table)
    print "fake =", fake
#    gobject.timeout_add(100, check_on_table, table, fake)
    print "calling main"
    gtk.main()

