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
import logging

from PyQt5.QtGui import QWindow

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

        self.wnck_table_w = None

        for win in root.get_windows():
            w_title = win.get_name()
            if re.search(self.search_string, w_title, re.I):
                log.info('"%s" matches: "%s"', w_title, self.search_string)
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
            log.warning(_("No match in XTables for table '%s'."), self.search_string)

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
#    The idea here is to call setTransientParent on the HUD window, with the table window
#    as the argument. This should keep the HUD window on top of the table window, as if 
#    the hud window was a dialog belonging to the table.

#    X doesn't like calling the foreign_new function in XTables.
#    Nope don't know why. Moving it here seems to make X happy.
        if self.gdkhandle is None:
            self.gdkhandle = QWindow.fromWinId(int(self.number))

#   This is the gdkhandle for the HUD window
        gdkwindow = (window.windowHandle())

        gdkwindow.setTransientParent(self.gdkhandle)
