#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Base class for interacting with poker client windows.

There are currently subclasses for X, OSX, and Windows.

The class queries the poker client window for data of interest, such as
size and location. It also controls the signals to alert the HUD when the
client has been resized, destroyed, etc.
"""
#    Copyright 2008 - 2011, Ray E. Barker

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

import L10n
_ = L10n.get_translation()

#    Standard Library modules
import re
import logging
from time import sleep

#    FreePokerTools modules
import Configuration
from HandHistoryConverter import getTableTitleRe
from HandHistoryConverter import getTableNoRe

c = Configuration.Config()
log = logging.getLogger("hud")

#    Global used for figuring out the current game being played from the title.
#    The dict key is a tuple of (limit type, category) for the game. 
#    The list is the names for those games used by the supported poker sites
#    This is currently only used for mixed games, so it only needs to support those
#    games on PokerStars and Full Tilt.
nlpl_game_names = { #fpdb name      Stars Name   FTP Name (if different)
              ("nl", "holdem"    ) : ("No Limit Hold\'em"  ,                     ),
              ("pl", "holdem"    ) : ("Pot Limit Hold\'em" ,                     ),
              ("pl", "omahahi"   ) : ("Pot Limit Omaha"    ,"Pot Limit Omaha Hi" ),
             }
limit_game_names = { #fpdb name      Stars Name   FTP Name
              ("fl", "holdem"    ) : ("Limit Hold\'em"  ,          ),
              ("fl", "omahahilo" ) : ("Limit Omaha H/L" ,          ),
              ("fl", "studhilo"  ) : ("Limit Stud H/L"  ,          ),
              ("fl", "razz"      ) : ("Limit Razz"      ,          ),
              ("fl", "studhi"    ) : ("Limit Stud"      , "Stud Hi"),
              ("fl", "27_3draw"  ) : ("Limit Triple Draw 2-7 Lowball",          )
             }

#    A window title might have our table name + one of these words/
#    phrases. If it has this word in the title, it is not a table.
bad_words = ('History for table:', 'HUD:', 'Chat:', 'FPDBHUD', 'Lobby')

#    Each TableWindow object must have the following attributes correctly populated:
#    tw.name = the table name from the title bar, which must to match the table name
#              from the corresponding hand record in the db.
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
#    tournament = Tournament number for a tournament or None for a cash game.
#    table = Table number for a tournament.
#    gdkhandle = 
#    window = 
#    parent = 
#    game = 
#    search_string = 

class Table_Window(object):
    def __init__(self, config, site, table_name = None, tournament = None, table_number = None):

        self.config = config
        self.site = site
        self.hud = None   # fill in later
        self.gdkhandle = None
        self.number = None
        if tournament is not None and table_number is not None:
            self.tournament = int(tournament)
            self.table = int(table_number)
            self.name = "%s - %s" % (self.tournament, self.table)
            self.type = "tour"
            table_kwargs = dict(tournament = self.tournament, table_number = self.table)
            self.tableno_re = getTableNoRe(self.config, self.site, tournament = self.tournament)
        elif table_name is not None:
            self.name = table_name
            self.type = "cash"
            self.tournament = None
            table_kwargs = dict(table_name = table_name)

        else:
            return None

        self.search_string = getTableTitleRe(self.config, self.site, self.type, **table_kwargs)
        # make a small delay otherwise Xtables.root.get_windows()
        #  returns empty for unknown reasons
        sleep(0.1)
        
        self.find_table_parameters()
        if not self.number:
            log.error(_("Can't find table \"%s\" with search string \"%s\""), table_name, self.search_string)


        geo = self.get_geometry()
        if geo is None:  return None
        self.width  = geo['width']
        self.height = geo['height']
        self.x      = geo['x']
        self.y      = geo['y']
        self.oldx   = self.x # attn ray: remove these two lines and update Hud.py::update_table_position()
        self.oldy   = self.y

        self.game = self.get_game()

    def __str__(self):
        likely_attrs = ("number", "title", "site", "width", "height", "x", "y",
                        "tournament", "table", "gdkhandle", "window", "parent",
                        "key", "hud", "game", "search_string", "tableno_re")
        temp = 'TableWindow object\n'
        for a in likely_attrs:
            if getattr(self, a, 0):
                temp += "    %s = %s\n" % (a, getattr(self, a))
        return temp

####################################################################
#    "get" methods. These query the table and return the info to get.
#    They don't change the data in the table and are generally used
#    by the "check" methods. Most of the get methods are in the 
#    subclass because they are specific to X, Windows, etc.
    def get_game(self):
#        title = self.get_window_title()
#        if title is None:
#            return False
        title = self.title

#    check for nl and pl games first, to avoid bad matches
        for game, names in nlpl_game_names.iteritems():
            for name in names:
                if name in title:
                    return game
        for game, names in limit_game_names.iteritems():
            for name in names:
                if name in title:
                    return game
        return False

    def get_table_no(self):
        new_title = self.get_window_title()
        if new_title is None:
            return False

        try:
            mo = re.search(self.tableno_re, new_title)
        except AttributeError: #'Table' object has no attribute 'tableno_re'
            return False
              
        if mo is not None:
            return int(mo.group(1))
        return False

####################################################################
#    check_table() is meant to be called by the hud periodically to
#    determine if the client has been moved or resized. check_table()
#    also checks and signals if the client has been closed. 
    def check_table(self):
        return self.check_size() or self.check_loc()

####################################################################
#    "check" methods. They use the corresponding get method, update the
#    table object and return the name of the signal to be emitted or 
#    False if unchanged. These do not signal for destroyed
#    clients to prevent a race condition.

#    These might be called by a Window.timeout, so they must not
#    return False, or the timeout will be cancelled.
    def check_size(self):
        new_geo = self.get_geometry()
        if new_geo is None:   # window destroyed
            return "client_destroyed"

        elif  self.width  != new_geo['width'] or self.height != new_geo['height']:    # window resized
            self.oldwidth = self.width
            self.width  = new_geo['width']
            self.oldheight = self.height
            self.height = new_geo['height']
            return "client_resized"
        return False  # no change

    def check_loc(self):
        new_geo = self.get_geometry()        
        if new_geo is None:   # window destroyed
            return "client_destroyed"

        if self.x != new_geo['x'] or self.y != new_geo['y']: # window moved
            self.x      = new_geo['x']
            self.y      = new_geo['y']
            return "client_moved"
        return False  # no change

    def has_table_title_changed(self, hud):
        result = self.get_table_no()
        if result is not False and result != self.table:
            self.table = result
            if hud is not None:
                return True
        return False

    def check_bad_words(self, title):
        for word in bad_words:
            if word in title: return True
        return False
