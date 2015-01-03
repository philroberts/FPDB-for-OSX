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
import xcffib, xcffib.xproto

#    FPDB modules
from TableWindow import Table_Window
import Configuration

xconn = xcffib.Connection()
root = xconn.get_setup().roots[xconn.pref_screen].root

def getAtom(name):
    return xconn.core.InternAtom(False, len(name), name).reply().atom

nclatom = getAtom("_NET_CLIENT_LIST")
winatom = getAtom("WINDOW")
wnameatom = getAtom("_NET_WM_NAME")
utf8atom = getAtom("UTF8_STRING")

c = Configuration.Config()
log = logging.getLogger("hud")

class Table(Table_Window):

    def find_table_parameters(self):

#    This is called by __init__(). Find the poker table window of interest,
#    given the self.search_string. Then populate self.number, self.title, 
#    self.window, and self.parent (if required).

        wins = xconn.core.GetProperty(False, root, nclatom, winatom, 0, (2**32) - 1).reply().value.to_atoms()
        for win in wins:
            w_title = xconn.core.GetProperty(False, win, wnameatom, utf8atom, 0, (2**32) - 1).reply().value.to_string()
            if re.search(self.search_string, w_title, re.I):
                log.info('"%s" matches: "%s"', w_title, self.search_string)
                title = w_title.replace('"', '')
                if self.check_bad_words(title): continue
                self.number = win
                self.title = title
                break

        if self.number is None:
            log.warning(_("No match in XTables for table '%s'."), self.search_string)

    # This function serves a double purpose. It fetches the X geometry
    # but it also is used to track for window lifecycle. When
    # get_geometry() returns False [None is deal as False], the table is
    # assumed dead and thus the HUD instance may be killed off.
    def get_geometry(self):
        wins = xconn.core.GetProperty(False, root, nclatom, winatom, 0, (2**32) - 1).reply().value.to_atoms()
        if self.number not in wins:
            return None
        try:
            geo = xconn.core.GetGeometry(self.number).reply()
            absxy = xconn.core.TranslateCoordinates(self.number, root, geo.x, geo.y).reply()
            return {'x'        : absxy.dst_x,
                    'y'        : absxy.dst_y,
                    'width'    : geo.width,
                    'height'   : geo.height
                   }
        except xcffib.xproto.DrawableError:
            return None

    def get_window_title(self):
        return xconn.core.GetProperty(False, self.number, wnameatom, utf8atom, 0, (2**32) - 1).reply().value.to_string()


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
