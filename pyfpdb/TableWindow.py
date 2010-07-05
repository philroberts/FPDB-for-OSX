#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""Discover_TableWindow.py

Inspects the currently open windows and finds those of interest to us--that is
poker table windows from supported sites.  Returns a list
of Table_Window objects representing the windows found.
"""
#    Copyright 2008-2010, Ray E. Barker

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
import os
import sys

#    pyGTK modules
import pygtk
import gtk
import gobject

#    FreePokerTools modules
import Configuration
#if os.name == "posix":
#    import XTables
#elif os.name == "nt":
#    import WinTables

#    Global used for figuring out the current game being played from the title
#    The dict key is the fpdb name for the game
#    The list is the names for those games used by the supported poker sites
#    This is currently only used for HORSE, so it only needs to support those
#    games on PokerStars and Full Tilt.
game_names = { #fpdb name      Stars Name   FTP Name
              "holdem"     : ("Hold\'em"  ,          ),
              "omahahilo"  : ("Omaha H/L" ,          ),
              "studhilo"   : ("Stud H/L"  ,          ),
              "razz"       : ("Razz"      ,          ),
              "studhi"     : ("Stud"      , "Stud Hi")
             }

#    A window title might have our table name + one of theses words/
#    phrases. If it has this word in the title, it is not a table.
bad_words = ('History for table:', 'HUD:', 'Chat:')

#    Here are the custom signals we define for allowing the 'client watcher'
#    thread to communicate with the gui thread. Any time a poker client is
#    is moved, resized, or closed on of these signals is emitted to the
#    HUD main window.
gobject.signal_new("client_moved", gtk.Window,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_PYOBJECT,))

gobject.signal_new("client_resized", gtk.Window,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_PYOBJECT,))

gobject.signal_new("client_destroyed", gtk.Window,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_PYOBJECT,))

#    Each TableWindow object must have the following attributes correctly populated:
#    tw.name = the table name from the title bar, which must to match the table name
#              from the corresponding hand history.
#    tw.site = the site name, e.g. PokerStars, FullTilt.  This must match the site
#            name specified in the config file.
#    tw.number = This is the system id number for the client table window in the
#                format that the system presents it.  This is Xid in Xwindows and
#                hwnd in Microsoft Windows.
#    tw.title = The full title from the window title bar.
#    tw.width, tw.height = The width and height of the window in pixels.  This is
#            the internal width and height, not including the title bar and
#            window borders.
#    tw.x, tw.y = The x, y (horizontal, vertical) location of the window relative
#            to the top left of the display screen.  This also does not include the
#            title bar and window borders.  To put it another way, this is the
#            screen location of (0, 0) in the working window.

class Table_Window(object):
    def __init__(self, search_string, table_name = None, tournament = None, table_number = None):

        if tournament is not None and table_number is not None:
            print "tournament %s, table %s" % (tournament, table_number)
            self.tournament = int(tournament)
            self.table = int(table_number)
            self.name = "%s - %s" % (self.tournament, self.table)
        elif table_name is not None:
            # search_string = table_name
            self.name = table_name
            self.tournament = None
        else:
            return None

        self.find_table_parameters(search_string)

    def __str__(self):
#    __str__ method for testing
        likely_attrs = ("site", "number", "title", "width", "height", "x", "y",
                        "tournament", "table", "gdkhandle")
        temp = 'TableWindow object\n'
        for a in likely_attrs:
            if getattr(self, a, 0):
                temp += "    %s = %s\n" % (a, getattr(self, a))
        return temp

    def get_game(self):
        title = self.get_window_title()
        print title
        for game, names in game_names.iteritems():
            for name in names:
                if name in title:
                    return game
        return None

    def check_geometry(self):
        new_geo = self.get_geometry()

        if new_geo is None:   # window destroyed
            return "client_destroyed"

        elif  self.x != new_geo['x'] or self.y != new_geo['y']: # window moved
            self.x      = new_geo['x']
            self.y      = new_geo['y']
            return "client_moved"

        elif  self.width  != new_geo['width'] or self.height != new_geo['height']:    # window resized
            self.width  = new_geo['width']
            self.height = new_geo['height']
            return "client_resized"

        else: return False    # window not changed

    def check_bad_words(self, title):
        for word in bad_words:
            if word in title: return True
        return False
