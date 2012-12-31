#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""XWindows specific methods for TableWindows Class.
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
import os
import logging

#    pyGTK modules
import gtk

#    Other Library modules
import wnck

#    FPDB modules
from TableWindow import Table_Window
import Configuration

# Wnck caches the results of queries. A window once retrieved remains in
# the list of Wnck internal objects even after the window no longer
# exists. To make things worse, event callbacks for signal
# "window-closed" can only be set for the WnckScreen, not for individual
# WnckWindow objects. For this reason, we need to track the known table
# windows.
WNCK_XTABLES = set()

# Prototype for callback is 'func(WnckScreen, WnckWindow, user_data)';
# We're only interested in the XID of tables we're tracking.
def remove_wnck_win(scr, w, *args):
    _xid = w.get_xid()
    if _xid in WNCK_XTABLES:
        WNCK_XTABLES.remove(_xid)

# Connect the signal handler to the single global root (screen)
root = wnck.screen_get_default()
root.connect('window-closed', remove_wnck_win)


c = Configuration.Config()
log = logging.getLogger("hud")

class Table(Table_Window):

    def find_table_parameters(self):

#    This is called by __init__(). Find the poker table window of interest,
#    given the self.search_string. Then populate self.number, self.title, 
#    self.window, and self.parent (if required).

        self.number = None
        self.wnck_table_w = None

        # Flush GTK event loop before calling wnck.get_*
        while gtk.events_pending():
            gtk.main_iteration(False)

        for win in root.get_windows():
            w_title = win.get_name()
            if re.search(self.search_string, w_title, re.I):
                log.info('"%s" matches: "%s"' % (w_title, self.search_string))
                title = w_title.replace('"', '')
                if self.check_bad_words(title): continue
                # XXX: If we could connect to 'window-closed' here, it
                # would make things SOOO much easier... Alas, the signal
                # is not available for individual windows.
                self.wnck_table_w = win
                self.number = int(win.get_xid())
                self.title = title
                # XID is a consistent key
                WNCK_XTABLES.add(self.number)
                break

        if self.number is None:
            log.warning(_("No match in XTables for table '%s'.") % self.search_string)
            return None

#    def get_window_from_xid(self, id):
#        for outside in root.query_tree().children:
#            if outside.id == id:
#                return (outside, outside.query_tree().parent)
#            for inside in outside.query_tree().children:
#                if inside.id == id:  # GNOME, Xfce
#                    return (inside, inside.query_tree().parent)
#                for wayinside in inside.query_tree().children:
#                    if wayinside.id == id:  # KDE
#                        parent = wayinside.query_tree().parent
#                        return (wayinside, parent.query_tree().parent)
#        return (None, None)

    #def get_geometry(self):
        #try:
            #my_geo = self.window.get_geometry()
            #if self.parent is None:
                #return {'x'      : my_geo.x,
                        #'y'      : my_geo.y,
                        #'width'  : my_geo.width,
                        #'height' : my_geo.height
                       #}
            #else:
                #pa_geo = self.parent.get_geometry()
                #return {'x'      : my_geo.x + pa_geo.x,
                        #'y'      : my_geo.y + pa_geo.y,
                        #'width'  : my_geo.width,
                        #'height' : my_geo.height
                       #}
        #except:
            #return None

    # This function serves a double purpose. It fetches the X geometry
    # information from the WnckWindow, which is the normal behaviour -
    # but it also is used to track for window lifecycle. When
    # get_geometry() returns False [None is deal as False], the table is
    # assumed dead and thus the HUD instance may be killed off.
    def get_geometry(self):
        if self.number not in WNCK_XTABLES:
            return None
        (_x, _y, _w, _h) = self.wnck_table_w.get_client_window_geometry()
        return {'x'        : int(_x),
                'y'        : int(_y),
                'width'    : int(_w),
                'height'   : int(_h)
               }

    def get_window_title(self):
        return self.wnck_table_w.get_name()


    def topify(self, window):
#    The idea here is to call set_transient_for on the HUD window, with the table window
#    as the argument. This should keep the HUD window on top of the table window, as if 
#    the hud window was a dialog belonging to the table.

#    X doesn't like calling the foreign_new function in XTables.
#    Nope don't know why. Moving it here seems to make X happy.
        if self.gdkhandle is None:
            self.gdkhandle = gtk.gdk.window_foreign_new(int(self.number))

#   This is the gdkhandle for the HUD window
        gdkwindow = gtk.gdk.window_foreign_new(window.window.xid)

#    Then call set_transient_for on the gdk handle of the HUD window
#    with the gdk handle of the table window as the argument.
        gdkwindow.set_transient_for(self.gdkhandle)

