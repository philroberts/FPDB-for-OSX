#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tables_Demo.py

Main program module to test/demo the Tables subclasses.
"""
#    Copyright 2008-2011, Ray E. Barker

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

#    pyGTK modules
import pygtk
import gtk
import gobject

#    fpdb/free poker tools modules
import Configuration
import L10n
_ = L10n.get_translation()

#    get the correct module for the current os
if sys.platform[0:5] == 'linux':
    import XTables as Tables
elif sys.platform == 'darwin':
    import OSXTables as Tables
else: # This is bad--figure out the values for the various windows flavors
    import WinTables as Tables

if __name__ == "__main__":
    Configuration.set_logfile("fpdb-log.txt")
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
            self.main_window.set_title(_("Fake HUD Main Window"))
            self.main_window.move(table.x + dx, table.y + dy)
            self.main_window.show_all()
            table.topify(self.main_window)
            
#    These are the currently defined signals. Do this in the HUD.
            self.main_window.connect("client_moved", self.client_moved)
            self.main_window.connect("client_resized", self.client_resized)
            self.main_window.connect("client_destroyed", self.client_destroyed)
            self.main_window.connect("game_changed", self.game_changed)
            self.main_window.connect("table_changed", self.table_changed)

#    And these of the handlers that go with those signals.
#    These would live inside the HUD code.
        def client_moved(self, widget, hud):
            self.main_window.move(self.table.x + self.dx, self.table.y + self.dy)

        def client_resized(self, *args):
            print "Client resized"

        def client_destroyed(self, *args): # call back for terminating the main eventloop
            print "Client destroyed."
            gtk.main_quit()

        def game_changed(self, *args):
            print "Game Changed."

        def table_changed(self, *args):
            print "Table Changed."

    print _("enter table name to find: "),
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

    table = Tables.Table(config, "Full Tilt Poker", **table_kwargs)
    table.gdkhandle = gtk.gdk.window_foreign_new(table.number)
    print table

    fake = fake_hud(table)
    fake.parent = fake

    gobject.timeout_add(1000, table.check_game, fake)
    gobject.timeout_add(100, table.check_table, fake)
    print "calling main"
    gtk.main()

